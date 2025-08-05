from finvizfinance.screener.technical import Technical
from finvizfinance.quote import finvizfinance
import yfinance as yf
import pandas as pd
import time
import numpy as np
import requests
from bs4 import BeautifulSoup
from scipy.stats import norm
import praw
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
REDDIT_USERNAME = os.getenv('REDDIT_USERNAME')
REDDIT_PASSWORD = os.getenv('REDDIT_PASSWORD')

# Kelly Criterion Portfolio Allocation Functions
def calculate_kelly_fraction(p, g, l):
    """
    Calculate Kelly Criterion fraction for single asset allocation
    
    Parameters:
    p: probability of winning (0-1)
    g: fractional gain if win (e.g., 0.10 for 10% gain)
    l: fractional loss if lose (e.g., 0.10 for 10% loss)
    
    Returns:
    f*: optimal fraction of capital to allocate
    """
    q = 1 - p  # probability of losing
    
    # Kelly formula: f* = (bp - q) / b
    # where b = g/l (net odds)
    if l == 0:
        return 0  # Avoid division by zero
    
    b = g / l  # net odds
    kelly_fraction = (b * p - q) / b
    
    return max(0, kelly_fraction)  # Don't allow negative allocations

def calculate_portfolio_kelly(returns_matrix, risk_free_rate=0.05):
    """
    Calculate Kelly Criterion for multi-asset portfolio
    
    Parameters:
    returns_matrix: DataFrame with assets as columns and historical returns as rows
    risk_free_rate: risk-free rate (default 5%)
    
    Returns:
    weights: optimal portfolio weights
    """
    try:
        # Calculate excess returns
        excess_returns = returns_matrix - risk_free_rate
        
        # Calculate mean excess returns and covariance matrix
        mu = excess_returns.mean()
        sigma = excess_returns.cov()
        
        # Kelly portfolio weights: w* = Σ^(-1) * μ
        sigma_inv = np.linalg.inv(sigma.values)
        kelly_weights = sigma_inv @ mu.values
        
        # Normalize weights to sum to 1
        kelly_weights = kelly_weights / np.sum(np.abs(kelly_weights))
        
        return pd.Series(kelly_weights, index=returns_matrix.columns)
        
    except Exception as e:
        print(f"Error calculating portfolio Kelly: {e}")
        return None

def estimate_stock_probabilities(ticker, lookback_days=252):
    """
    Estimate win probability and gain/loss parameters for a stock
    
    Parameters:
    ticker: stock symbol
    lookback_days: number of days to look back for historical data
    
    Returns:
    dict: containing p, g, l, and Kelly fraction
    """
    try:
        yft = yf.Ticker(ticker)
        hist = yft.history(period=f'{lookback_days}d')
        
        if len(hist) < 30:  # Need at least 30 days of data
            return None
        
        # Calculate daily returns
        returns = hist['Close'].pct_change().dropna()
        
        # Estimate win probability (positive returns)
        p = (returns > 0).mean()
        
        # Calculate average gain and loss
        gains = returns[returns > 0]
        losses = returns[returns < 0]
        
        if len(gains) == 0 or len(losses) == 0:
            return None
        
        g = gains.mean()  # Average gain
        l = abs(losses.mean())  # Average loss (absolute value)
        
        # Calculate Kelly fraction
        kelly_fraction = calculate_kelly_fraction(p, g, l)
        
        # Calculate volatility
        volatility = returns.std()
        
        # Calculate Sharpe ratio
        sharpe_ratio = (returns.mean() - 0.05/252) / volatility if volatility > 0 else 0
        
        return {
            'ticker': ticker,
            'win_probability': p,
            'avg_gain': g,
            'avg_loss': l,
            'kelly_fraction': kelly_fraction,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'total_return': (hist['Close'].iloc[-1] / hist['Close'].iloc[0] - 1),
            'max_drawdown': calculate_max_drawdown(hist['Close'])
        }
        
    except Exception as e:
        print(f"Error estimating probabilities for {ticker}: {e}")
        return None

def calculate_max_drawdown(prices):
    """Calculate maximum drawdown from peak"""
    peak = prices.expanding().max()
    drawdown = (prices - peak) / peak
    return drawdown.min()

def calculate_scaled_kelly(kelly_fraction, scaling_factor=0.5):
    """
    Calculate scaled Kelly fraction to reduce volatility
    
    Parameters:
    kelly_fraction: full Kelly fraction
    scaling_factor: fraction of Kelly to use (0.5 = half Kelly)
    
    Returns:
    scaled_fraction: scaled Kelly allocation
    """
    return kelly_fraction * scaling_factor

def calculate_portfolio_allocation(stocks_data, portfolio_value=1000, scaling_factor=0.5):
    """
    Calculate optimal portfolio allocation using Kelly Criterion
    
    Parameters:
    stocks_data: list of stock analysis dictionaries
    portfolio_value: total portfolio value in dollars
    scaling_factor: Kelly scaling factor (0.5 = half Kelly)
    
    Returns:
    dict: portfolio allocation details
    """
    allocations = []
    total_allocation = 0
    
    for stock in stocks_data:
        ticker = stock['Ticker']
        
        # Get Kelly analysis
        kelly_data = estimate_stock_probabilities(ticker)
        
        if kelly_data and kelly_data['kelly_fraction'] > 0:
            # Calculate scaled Kelly allocation
            scaled_kelly = calculate_scaled_kelly(kelly_data['kelly_fraction'], scaling_factor)
            
            # Calculate dollar allocation
            dollar_allocation = scaled_kelly * portfolio_value
            
            # Don't allocate more than 20% to any single stock
            max_allocation = portfolio_value * 0.20
            dollar_allocation = min(dollar_allocation, max_allocation)
            
            if dollar_allocation > 10:  # Only include if allocation > $10
                allocations.append({
                    'ticker': ticker,
                    'current_price': stock['Current_Price'],
                    'kelly_fraction': kelly_data['kelly_fraction'],
                    'scaled_kelly': scaled_kelly,
                    'dollar_allocation': dollar_allocation,
                    'shares_to_buy': int(dollar_allocation / stock['Current_Price']),
                    'win_probability': kelly_data['win_probability'],
                    'avg_gain': kelly_data['avg_gain'],
                    'avg_loss': kelly_data['avg_loss'],
                    'volatility': kelly_data['volatility'],
                    'sharpe_ratio': kelly_data['sharpe_ratio'],
                    'doubling_score': stock['Doubling_Score'],
                    'reasons': stock['Reasons']
                })
                
                total_allocation += dollar_allocation
    
    # Sort by Kelly fraction (highest first)
    allocations.sort(key=lambda x: x['kelly_fraction'], reverse=True)
    
    return {
        'allocations': allocations,
        'total_allocated': total_allocation,
        'cash_remaining': portfolio_value - total_allocation,
        'allocation_percentage': (total_allocation / portfolio_value) * 100
    }

def calculate_risk_metrics(portfolio_allocation):
    """
    Calculate risk metrics for the portfolio allocation
    
    Parameters:
    portfolio_allocation: portfolio allocation dictionary
    
    Returns:
    dict: risk metrics
    """
    allocations = portfolio_allocation['allocations']
    
    if not allocations:
        return {}
    
    # Calculate portfolio-level metrics
    total_value = sum(alloc['dollar_allocation'] for alloc in allocations)
    
    # Weighted average metrics
    weighted_volatility = sum(
        alloc['volatility'] * (alloc['dollar_allocation'] / total_value) 
        for alloc in allocations
    )
    
    weighted_sharpe = sum(
        alloc['sharpe_ratio'] * (alloc['dollar_allocation'] / total_value) 
        for alloc in allocations
    )
    
    # Calculate expected return (simplified)
    expected_return = sum(
        alloc['win_probability'] * alloc['avg_gain'] * (alloc['dollar_allocation'] / total_value)
        for alloc in allocations
    )
    
    # Calculate maximum drawdown estimate (simplified)
    max_dd_estimate = weighted_volatility * 2  # Rough estimate
    
    return {
        'expected_return': expected_return,
        'portfolio_volatility': weighted_volatility,
        'portfolio_sharpe': weighted_sharpe,
        'max_drawdown_estimate': max_dd_estimate,
        'number_of_positions': len(allocations),
        'concentration_risk': max(alloc['dollar_allocation'] for alloc in allocations) / total_value if allocations else 0
    }

# Confidence-Weighted Kelly Criterion Functions
def calculate_confidence_interval(returns, confidence_level=0.95):
    """
    Calculate confidence interval for probability estimates
    
    Parameters:
    returns: array of historical returns
    confidence_level: confidence level (e.g., 0.95 for 95%)
    
    Returns:
    dict: confidence interval statistics
    """
    try:
        from scipy import stats
        
        # Calculate win probability
        wins = (returns > 0).sum()
        total = len(returns)
        p_hat = wins / total
        
        # Calculate standard error
        se = np.sqrt(p_hat * (1 - p_hat) / total)
        
        # Calculate confidence interval
        z_score = stats.norm.ppf((1 + confidence_level) / 2)
        margin_of_error = z_score * se
        
        lower_bound = max(0, p_hat - margin_of_error)
        upper_bound = min(1, p_hat + margin_of_error)
        
        # Calculate confidence level based on sample size
        # More data = higher confidence
        sample_confidence = min(0.95, 0.5 + (total / 1000) * 0.4)  # 50% to 95% based on sample size
        
        return {
            'point_estimate': p_hat,
            'lower_bound': lower_bound,
            'upper_bound': upper_bound,
            'margin_of_error': margin_of_error,
            'confidence_level': confidence_level,
            'sample_confidence': sample_confidence,
            'sample_size': total
        }
        
    except Exception as e:
        print(f"Error calculating confidence interval: {e}")
        return None

def calculate_confidence_weighted_kelly(p_estimate, g_estimate, l_estimate, 
                                      p_confidence, g_confidence, l_confidence,
                                      risk_aversion=1.0):
    """
    Calculate Kelly fraction weighted by confidence in estimates
    
    Parameters:
    p_estimate: point estimate of win probability
    g_estimate: point estimate of gain
    l_estimate: point estimate of loss
    p_confidence: confidence in probability estimate (0-1)
    g_confidence: confidence in gain estimate (0-1)
    l_confidence: confidence in loss estimate (0-1)
    risk_aversion: risk aversion factor (higher = more conservative)
    
    Returns:
    dict: confidence-weighted Kelly results
    """
    # Calculate base Kelly
    base_kelly = calculate_kelly_fraction(p_estimate, g_estimate, l_estimate)
    
    # Calculate confidence-weighted adjustments
    # Lower confidence = more conservative allocation
    confidence_factor = (p_confidence + g_confidence + l_confidence) / 3
    
    # Risk aversion adjustment
    risk_adjustment = 1 / (1 + risk_aversion * (1 - confidence_factor))
    
    # Calculate conservative Kelly using worst-case estimates
    # Use lower bound for gains, upper bound for losses
    conservative_p = p_estimate * p_confidence
    conservative_g = g_estimate * g_confidence
    conservative_l = l_estimate / l_confidence if l_confidence > 0 else l_estimate * 2
    
    conservative_kelly = calculate_kelly_fraction(conservative_p, conservative_g, conservative_l)
    
    # Calculate optimistic Kelly using best-case estimates
    optimistic_p = p_estimate + (1 - p_confidence) * 0.1  # Slight upward bias
    optimistic_g = g_estimate + (1 - g_confidence) * 0.05
    optimistic_l = l_estimate * (1 - (1 - l_confidence) * 0.5)
    
    optimistic_kelly = calculate_kelly_fraction(optimistic_p, optimistic_g, optimistic_l)
    
    # Final confidence-weighted Kelly
    confidence_weighted_kelly = base_kelly * confidence_factor * risk_adjustment
    
    return {
        'base_kelly': base_kelly,
        'confidence_weighted_kelly': confidence_weighted_kelly,
        'conservative_kelly': conservative_kelly,
        'optimistic_kelly': optimistic_kelly,
        'confidence_factor': confidence_factor,
        'risk_adjustment': risk_adjustment,
        'p_confidence': p_confidence,
        'g_confidence': g_confidence,
        'l_confidence': l_confidence
    }

def estimate_stock_probabilities_with_confidence(ticker, lookback_days=252, confidence_level=0.95):
    """
    Estimate stock probabilities with confidence intervals
    
    Parameters:
    ticker: stock symbol
    lookback_days: number of days to look back
    confidence_level: confidence level for intervals
    
    Returns:
    dict: probability estimates with confidence intervals
    """
    try:
        yft = yf.Ticker(ticker)
        hist = yft.history(period=f'{lookback_days}d')
        
        if len(hist) < 30:
            return None
        
        # Calculate daily returns
        returns = hist['Close'].pct_change().dropna()
        
        # Calculate probability confidence
        prob_confidence = calculate_confidence_interval(returns, confidence_level)
        
        if not prob_confidence:
            return None
        
        # Estimate win probability
        p = prob_confidence['point_estimate']
        p_confidence = prob_confidence['sample_confidence']
        
        # Calculate average gain and loss
        gains = returns[returns > 0]
        losses = returns[returns < 0]
        
        if len(gains) == 0 or len(losses) == 0:
            return None
        
        g = gains.mean()
        l = abs(losses.mean())
        
        # Estimate confidence in gain/loss estimates based on sample size
        g_confidence = min(0.95, 0.5 + (len(gains) / 500) * 0.4)
        l_confidence = min(0.95, 0.5 + (len(losses) / 500) * 0.4)
        
        # Calculate confidence-weighted Kelly
        kelly_results = calculate_confidence_weighted_kelly(
            p, g, l, p_confidence, g_confidence, l_confidence
        )
        
        # Calculate volatility
        volatility = returns.std()
        
        # Calculate Sharpe ratio
        sharpe_ratio = (returns.mean() - 0.05/252) / volatility if volatility > 0 else 0
        
        return {
            'ticker': ticker,
            'win_probability': p,
            'win_probability_confidence': p_confidence,
            'win_probability_ci': (prob_confidence['lower_bound'], prob_confidence['upper_bound']),
            'avg_gain': g,
            'avg_gain_confidence': g_confidence,
            'avg_loss': l,
            'avg_loss_confidence': l_confidence,
            'volatility': volatility,
            'kelly_results': kelly_results,
            'sharpe_ratio': sharpe_ratio,
            'total_return': (hist['Close'].iloc[-1] / hist['Close'].iloc[0] - 1),
            'max_drawdown': calculate_max_drawdown(hist['Close']),
            'sample_size': len(returns)
        }
        
    except Exception as e:
        print(f"Error estimating probabilities with confidence for {ticker}: {e}")
        return None

def calculate_confidence_weighted_portfolio_allocation(stocks_data, portfolio_value=1000, 
                                                     scaling_factor=0.5, risk_aversion=1.0):
    """
    Calculate portfolio allocation using confidence-weighted Kelly Criterion
    
    Parameters:
    stocks_data: list of stock analysis dictionaries
    portfolio_value: total portfolio value
    scaling_factor: Kelly scaling factor
    risk_aversion: risk aversion factor (higher = more conservative)
    
    Returns:
    dict: confidence-weighted portfolio allocation
    """
    allocations = []
    total_allocation = 0
    
    for stock in stocks_data:
        ticker = stock['Ticker']
        
        # Get confidence-weighted Kelly analysis
        kelly_data = estimate_stock_probabilities_with_confidence(ticker)
        
        if kelly_data and kelly_data['kelly_results']['confidence_weighted_kelly'] > 0:
            # Use confidence-weighted Kelly
            confidence_kelly = kelly_data['kelly_results']['confidence_weighted_kelly']
            
            # Apply scaling
            scaled_kelly = calculate_scaled_kelly(confidence_kelly, scaling_factor)
            
            # Calculate dollar allocation
            dollar_allocation = scaled_kelly * portfolio_value
            
            # Position limits based on confidence
            confidence_factor = kelly_data['kelly_results']['confidence_factor']
            max_allocation = portfolio_value * (0.20 * confidence_factor)  # Higher confidence = higher limit
            dollar_allocation = min(dollar_allocation, max_allocation)
            
            # Minimum allocation based on confidence
            min_allocation = 10 * confidence_factor  # Higher confidence = higher minimum
            if dollar_allocation > min_allocation:
                allocations.append({
                    'ticker': ticker,
                    'current_price': stock['Current_Price'],
                    'base_kelly': kelly_data['kelly_results']['base_kelly'],
                    'confidence_weighted_kelly': confidence_kelly,
                    'scaled_kelly': scaled_kelly,
                    'dollar_allocation': dollar_allocation,
                    'shares_to_buy': int(dollar_allocation / stock['Current_Price']),
                    'win_probability': kelly_data['win_probability'],
                    'win_probability_confidence': kelly_data['win_probability_confidence'],
                    'avg_gain': kelly_data['avg_gain'],
                    'avg_gain_confidence': kelly_data['avg_gain_confidence'],
                    'avg_loss': kelly_data['avg_loss'],
                    'avg_loss_confidence': kelly_data['avg_loss_confidence'],
                    'volatility': kelly_data['volatility'],
                    'confidence_factor': kelly_data['kelly_results']['confidence_factor'],
                    'sharpe_ratio': kelly_data['sharpe_ratio'],
                    'doubling_score': stock['Doubling_Score'],
                    'reasons': stock['Reasons'],
                    'sample_size': kelly_data['sample_size']
                })
                
                total_allocation += dollar_allocation
    
    # Sort by confidence-weighted Kelly fraction (highest first)
    allocations.sort(key=lambda x: x['confidence_weighted_kelly'], reverse=True)
    
    return {
        'allocations': allocations,
        'total_allocated': total_allocation,
        'cash_remaining': portfolio_value - total_allocation,
        'allocation_percentage': (total_allocation / portfolio_value) * 100
    }

def display_confidence_weighted_allocation(portfolio_allocation, portfolio_value=1000):
    """
    Display confidence-weighted Kelly portfolio allocation results
    
    Parameters:
    portfolio_allocation: portfolio allocation dictionary
    portfolio_value: total portfolio value
    """
    print(f"\n🎯 CONFIDENCE-WEIGHTED KELLY PORTFOLIO ALLOCATION (${portfolio_value:,})")
    print("=" * 120)
    
    allocations = portfolio_allocation['allocations']
    
    if not allocations:
        print("❌ No suitable allocations found based on confidence-weighted Kelly Criterion")
        return
    
    print(f"📊 PORTFOLIO SUMMARY:")
    print(f"   Total Allocated: ${portfolio_allocation['total_allocated']:.2f}")
    print(f"   Cash Remaining: ${portfolio_allocation['cash_remaining']:.2f}")
    print(f"   Allocation %: {portfolio_allocation['allocation_percentage']:.1f}%")
    print(f"   Number of Positions: {len(allocations)}")
    
    print(f"\n📈 CONFIDENCE-WEIGHTED ALLOCATION BREAKDOWN:")
    print("-" * 140)
    print(f"{'Rank':<4} {'Ticker':<8} {'Price':<8} {'Base%':<8} {'Conf%':<8} {'Scaled%':<8} {'Allocation':<12} {'Shares':<8} {'Win%':<6} {'Conf':<5} {'Gain%':<7} {'Conf':<5} {'Loss%':<7} {'Conf':<5} {'Sample':<6}")
    print("-" * 140)
    
    for i, alloc in enumerate(allocations, 1):
        print(f"{i:<4} {alloc['ticker']:<8} ${alloc['current_price']:<7.2f} "
              f"{alloc['base_kelly']:<7.1%} {alloc['confidence_weighted_kelly']:<7.1%} "
              f"{alloc['scaled_kelly']:<7.1%} ${alloc['dollar_allocation']:<11.2f} "
              f"{alloc['shares_to_buy']:<8} {alloc['win_probability']:<5.1%} "
              f"{alloc['win_probability_confidence']:<4.1%} {alloc['avg_gain']:<6.1%} "
              f"{alloc['avg_gain_confidence']:<4.1%} {alloc['avg_loss']:<6.1%} "
              f"{alloc['avg_loss_confidence']:<4.1%} {alloc['sample_size']:<6}")
    
    print(f"\n🎯 DETAILED CONFIDENCE ANALYSIS:")
    print("-" * 120)
    
    for i, alloc in enumerate(allocations[:5], 1):  # Show top 5
        print(f"\n🥇 #{i}: {alloc['ticker']} - Confidence-Weighted Kelly")
        print(f"   Current Price: ${alloc['current_price']:.2f}")
        print(f"   Base Kelly: {alloc['base_kelly']:.1%}")
        print(f"   Confidence-Weighted Kelly: {alloc['confidence_weighted_kelly']:.1%}")
        print(f"   Scaled Allocation: {alloc['scaled_kelly']:.1%}")
        print(f"   Dollar Allocation: ${alloc['dollar_allocation']:.2f}")
        print(f"   Shares to Buy: {alloc['shares_to_buy']}")
        print(f"   Win Probability: {alloc['win_probability']:.1%} (Confidence: {alloc['win_probability_confidence']:.1%})")
        print(f"   Average Gain: {alloc['avg_gain']:.1%} (Confidence: {alloc['avg_gain_confidence']:.1%})")
        print(f"   Average Loss: {alloc['avg_loss']:.1%} (Confidence: {alloc['avg_loss_confidence']:.1%})")
        print(f"   Volatility: {alloc['volatility']:.1%}")
        print(f"   Overall Confidence Factor: {alloc['confidence_factor']:.1%}")
        print(f"   Sample Size: {alloc['sample_size']} days")
        print(f"   Doubling Score: {alloc['doubling_score']}")
        print(f"   Reasons: {alloc['reasons']}")
    
    print(f"\n⚠️  CONFIDENCE-BASED RISK MANAGEMENT:")
    print("-" * 60)
    print("• Higher confidence = larger position sizes")
    print("• Lower confidence = smaller position sizes")
    print("• Sample size affects confidence levels")
    print("• Confidence intervals provide uncertainty bounds")
    print("• Risk aversion factor adjusts for conservative estimates")
    print("• Recalculate confidence levels monthly with new data")

def display_kelly_portfolio_allocation(portfolio_allocation, risk_metrics, portfolio_value=1000):
    """
    Display Kelly Criterion portfolio allocation results
    
    Parameters:
    portfolio_allocation: portfolio allocation dictionary
    risk_metrics: risk metrics dictionary
    portfolio_value: total portfolio value
    """
    print(f"\n🎯 KELLY CRITERION PORTFOLIO ALLOCATION (${portfolio_value:,})")
    print("=" * 100)
    
    allocations = portfolio_allocation['allocations']
    
    if not allocations:
        print("❌ No suitable allocations found based on Kelly Criterion")
        return
    
    print(f"📊 PORTFOLIO SUMMARY:")
    print(f"   Total Allocated: ${portfolio_allocation['total_allocated']:.2f}")
    print(f"   Cash Remaining: ${portfolio_allocation['cash_remaining']:.2f}")
    print(f"   Allocation %: {portfolio_allocation['allocation_percentage']:.1f}%")
    print(f"   Number of Positions: {len(allocations)}")
    
    if risk_metrics:
        print(f"   Expected Return: {risk_metrics['expected_return']:.2%}")
        print(f"   Portfolio Volatility: {risk_metrics['portfolio_volatility']:.2%}")
        print(f"   Portfolio Sharpe Ratio: {risk_metrics['portfolio_sharpe']:.2f}")
        print(f"   Max Drawdown Estimate: {risk_metrics['max_drawdown_estimate']:.2%}")
        print(f"   Concentration Risk: {risk_metrics['concentration_risk']:.2%}")
    
    print(f"\n📈 ALLOCATION BREAKDOWN:")
    print("-" * 100)
    print(f"{'Rank':<4} {'Ticker':<8} {'Price':<8} {'Kelly%':<8} {'Scaled%':<8} {'Allocation':<12} {'Shares':<8} {'Win%':<6} {'Gain%':<7} {'Loss%':<7} {'Sharpe':<7}")
    print("-" * 100)
    
    for i, alloc in enumerate(allocations, 1):
        print(f"{i:<4} {alloc['ticker']:<8} ${alloc['current_price']:<7.2f} "
              f"{alloc['kelly_fraction']:<7.1%} {alloc['scaled_kelly']:<7.1%} "
              f"${alloc['dollar_allocation']:<11.2f} {alloc['shares_to_buy']:<8} "
              f"{alloc['win_probability']:<5.1%} {alloc['avg_gain']:<6.1%} "
              f"{alloc['avg_loss']:<6.1%} {alloc['sharpe_ratio']:<6.2f}")
    
    print(f"\n🎯 DETAILED ANALYSIS:")
    print("-" * 100)
    
    for i, alloc in enumerate(allocations[:5], 1):  # Show top 5
        print(f"\n🥇 #{i}: {alloc['ticker']} - Kelly Allocation")
        print(f"   Current Price: ${alloc['current_price']:.2f}")
        print(f"   Kelly Fraction: {alloc['kelly_fraction']:.1%} (Full Kelly)")
        print(f"   Scaled Allocation: {alloc['scaled_kelly']:.1%} (Half Kelly)")
        print(f"   Dollar Allocation: ${alloc['dollar_allocation']:.2f}")
        print(f"   Shares to Buy: {alloc['shares_to_buy']}")
        print(f"   Win Probability: {alloc['win_probability']:.1%}")
        print(f"   Average Gain: {alloc['avg_gain']:.1%}")
        print(f"   Average Loss: {alloc['avg_loss']:.1%}")
        print(f"   Volatility: {alloc['volatility']:.1%}")
        print(f"   Sharpe Ratio: {alloc['sharpe_ratio']:.2f}")
        print(f"   Doubling Score: {alloc['doubling_score']}")
        print(f"   Reasons: {alloc['reasons']}")
    
    print(f"\n⚠️  RISK MANAGEMENT NOTES:")
    print("-" * 50)
    print("• Using Half-Kelly (50% scaling) to reduce volatility")
    print("• Maximum 20% allocation per position")
    print("• Minimum $10 allocation per position")
    print("• Cash remaining for opportunities and risk management")
    print("• Rebalance monthly based on updated Kelly calculations")
    print("• Monitor drawdowns and adjust scaling factor if needed")

def calculate_options_kelly_allocation(options_data, portfolio_value=1000, scaling_factor=0.25):
    """
    Calculate Kelly Criterion allocation for options
    
    Parameters:
    options_data: list of option opportunities
    portfolio_value: total portfolio value
    scaling_factor: Kelly scaling factor (more conservative for options)
    
    Returns:
    dict: options allocation details
    """
    allocations = []
    total_allocation = 0
    
    for opt in options_data:
        ticker = opt['ticker']
        
        # Estimate option probabilities based on historical data
        stock_data = estimate_stock_probabilities(ticker)
        
        if stock_data:
            # For options, we need to estimate the probability of the stock moving enough
            # to make the option profitable
            
            # Calculate probability of stock moving to different price levels
            current_price = opt['current_price']
            strike = opt['strike']
            ask = opt['ask']
            
            # Estimate probability of stock moving 25%, 50%, 100%
            # This is a simplified approach - in practice you'd use more sophisticated models
            
            # Use historical volatility to estimate move probabilities
            volatility = stock_data['volatility']
            
            # Simplified probability estimates based on normal distribution
            # Probability of stock moving up by X% in the option's time frame
            days_to_expiry = opt.get('days_to_expiry', 30)
            time_factor = np.sqrt(days_to_expiry / 252)  # Annualized to option timeframe
            
            # Calculate probabilities for different price moves
            prob_25 = 1 - norm.cdf(0.25 / (volatility * time_factor))
            prob_50 = 1 - norm.cdf(0.50 / (volatility * time_factor))
            prob_100 = 1 - norm.cdf(1.00 / (volatility * time_factor))
            
            # Use the most realistic probability for Kelly calculation
            # For penny stocks, use 25% move probability as baseline
            p = prob_25
            
            # Calculate potential gains and losses
            if current_price * 1.25 > strike:
                g = (current_price * 1.25 - strike) / ask  # Return if stock moves 25%
            else:
                g = 0.1  # Small gain if option becomes slightly profitable
            
            l = 1.0  # Maximum loss is 100% of option premium
            
            # Calculate Kelly fraction
            kelly_fraction = calculate_kelly_fraction(p, g, l)
            
            # Apply more conservative scaling for options
            scaled_kelly = calculate_scaled_kelly(kelly_fraction, scaling_factor)
            
            # Calculate dollar allocation
            dollar_allocation = scaled_kelly * portfolio_value
            
            # Very conservative limits for options
            max_allocation = portfolio_value * 0.05  # Max 5% per option
            dollar_allocation = min(dollar_allocation, max_allocation)
            
            if dollar_allocation > 5:  # Only include if allocation > $5
                contracts_to_buy = int(dollar_allocation / ask / 100)  # Options are typically 100 shares
                
                if contracts_to_buy > 0:
                    allocations.append({
                        'ticker': ticker,
                        'strike': strike,
                        'ask': ask,
                        'expiry': opt['expiry'],
                        'current_price': current_price,
                        'kelly_fraction': kelly_fraction,
                        'scaled_kelly': scaled_kelly,
                        'dollar_allocation': dollar_allocation,
                        'contracts_to_buy': contracts_to_buy,
                        'win_probability': p,
                        'potential_gain': g,
                        'max_loss': l,
                        'volatility': volatility,
                        'days_to_expiry': days_to_expiry,
                        'return_25': opt.get('return_25', 0),
                        'return_50': opt.get('return_50', 0),
                        'return_100': opt.get('return_100', 0),
                        'score': opt.get('score', 0),
                        'reasons': opt.get('reasons', [])
                    })
                    
                    total_allocation += dollar_allocation
    
    # Sort by Kelly fraction (highest first)
    allocations.sort(key=lambda x: x['kelly_fraction'], reverse=True)
    
    return {
        'allocations': allocations,
        'total_allocated': total_allocation,
        'cash_remaining': portfolio_value - total_allocation,
        'allocation_percentage': (total_allocation / portfolio_value) * 100
    }

def display_options_kelly_allocation(options_allocation, portfolio_value=1000):
    """
    Display Kelly Criterion allocation for options
    
    Parameters:
    options_allocation: options allocation dictionary
    portfolio_value: total portfolio value
    """
    print(f"\n🎯 KELLY CRITERION OPTIONS ALLOCATION (${portfolio_value:,})")
    print("=" * 100)
    
    allocations = options_allocation['allocations']
    
    if not allocations:
        print("❌ No suitable options allocations found based on Kelly Criterion")
        return
    
    print(f"📊 OPTIONS PORTFOLIO SUMMARY:")
    print(f"   Total Allocated: ${options_allocation['total_allocated']:.2f}")
    print(f"   Cash Remaining: ${options_allocation['cash_remaining']:.2f}")
    print(f"   Allocation %: {options_allocation['allocation_percentage']:.1f}%")
    print(f"   Number of Positions: {len(allocations)}")
    
    print(f"\n📈 OPTIONS ALLOCATION BREAKDOWN:")
    print("-" * 120)
    print(f"{'Rank':<4} {'Ticker':<8} {'Strike':<8} {'Cost':<8} {'Expiry':<12} {'Kelly%':<8} {'Scaled%':<8} {'Allocation':<12} {'Contracts':<10} {'Win%':<6} {'Gain%':<7} {'25%':<6} {'50%':<6} {'100%':<6}")
    print("-" * 120)
    
    for i, alloc in enumerate(allocations, 1):
        print(f"{i:<4} {alloc['ticker']:<8} ${alloc['strike']:<7.2f} ${alloc['ask']:<7.2f} "
              f"{alloc['expiry']:<12} {alloc['kelly_fraction']:<7.1%} {alloc['scaled_kelly']:<7.1%} "
              f"${alloc['dollar_allocation']:<11.2f} {alloc['contracts_to_buy']:<10} "
              f"{alloc['win_probability']:<5.1%} {alloc['potential_gain']:<6.1%} "
              f"{alloc['return_25']:<5.0f}% {alloc['return_50']:<5.0f}% {alloc['return_100']:<5.0f}%")
    
    print(f"\n🎯 DETAILED OPTIONS ANALYSIS:")
    print("-" * 100)
    
    for i, alloc in enumerate(allocations[:3], 1):  # Show top 3
        print(f"\n🥇 #{i}: {alloc['ticker']} - Options Kelly Allocation")
        print(f"   Strike: ${alloc['strike']:.2f} | Cost: ${alloc['ask']:.2f} | Expiry: {alloc['expiry']}")
        print(f"   Current Price: ${alloc['current_price']:.2f} | Days to Expiry: {alloc['days_to_expiry']}")
        print(f"   Kelly Fraction: {alloc['kelly_fraction']:.1%} (Full Kelly)")
        print(f"   Scaled Allocation: {alloc['scaled_kelly']:.1%} (Quarter Kelly)")
        print(f"   Dollar Allocation: ${alloc['dollar_allocation']:.2f}")
        print(f"   Contracts to Buy: {alloc['contracts_to_buy']}")
        print(f"   Win Probability: {alloc['win_probability']:.1%}")
        print(f"   Potential Gain: {alloc['potential_gain']:.1%}")
        print(f"   Max Loss: {alloc['max_loss']:.1%}")
        print(f"   Volatility: {alloc['volatility']:.1%}")
        print(f"   If Stock +25%: {alloc['return_25']:.0f}% return")
        print(f"   If Stock +50%: {alloc['return_50']:.0f}% return")
        print(f"   If Stock +100%: {alloc['return_100']:.0f}% return")
        print(f"   Score: {alloc['score']}")
        print(f"   Reasons: {', '.join(alloc['reasons'])}")
    
    print(f"\n⚠️  OPTIONS RISK MANAGEMENT:")
    print("-" * 50)
    print("• Using Quarter-Kelly (25% scaling) for options due to high risk")
    print("• Maximum 5% allocation per option position")
    print("• Minimum $5 allocation per position")
    print("• Options have asymmetric risk (limited upside, unlimited downside)")
    print("• Monitor time decay (theta) closely")
    print("• Consider rolling positions before expiration")
    print("• Use stop-losses or protective puts for risk management")

def analyze_stock_potential(ticker):
    """Deep analysis of a stock for doubling potential"""
    try:
        yft = yf.Ticker(ticker)
        info = yft.info
        
        hist = yft.history(period='1mo')
        if hist.empty:
            return None
            
        current_price = hist['Close'].iloc[-1]
        
        analysis = {
            'Ticker': ticker,
            'Current_Price': current_price,
            'Market_Cap': info.get('marketCap', 0),
            'Volume_Avg': info.get('averageVolume', 0),
            'Beta': info.get('beta', 0),
            'PE_Ratio': info.get('trailingPE', 0),
            'Forward_PE': info.get('forwardPE', 0),
            'PEG_Ratio': info.get('pegRatio', 0),
            'Price_to_Book': info.get('priceToBook', 0),
            'Debt_to_Equity': info.get('debtToEquity', 0),
            'ROE': info.get('returnOnEquity', 0),
            'ROA': info.get('returnOnAssets', 0),
            'Profit_Margins': info.get('profitMargins', 0),
            'Operating_Margins': info.get('operatingMargins', 0),
            'Revenue_Growth': info.get('revenueGrowth', 0),
            'Earnings_Growth': info.get('earningsGrowth', 0),
            'Analyst_Target': info.get('targetMeanPrice', 0),
            'Analyst_Recommendation': info.get('recommendationMean', 0),
            'Insider_Ownership': 0,
            'Institutional_Ownership': 0,
            'Short_Ratio': info.get('shortRatio', 0),
            'Days_To_Cover': info.get('sharesShort', 0) / info.get('averageVolume', 1) if info.get('averageVolume', 0) > 0 else 0,
            'Price_Change_1D': ((current_price - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2] * 100) if len(hist) > 1 else 0,
            'Price_Change_5D': ((current_price - hist['Close'].iloc[-6]) / hist['Close'].iloc[-6] * 100) if len(hist) > 5 else 0,
            'Price_Change_1M': ((current_price - hist['Close'].iloc[-21]) / hist['Close'].iloc[-21] * 100) if len(hist) > 21 else 0,
            'Volatility': hist['Close'].pct_change().std() * 100,
            'Volume_Spike': info.get('volume', 0) / info.get('averageVolume', 1) if info.get('averageVolume', 0) > 0 else 0,
            'Distance_from_52W_High': ((info.get('fiftyTwoWeekHigh', current_price) - current_price) / info.get('fiftyTwoWeekHigh', current_price) * 100) if info.get('fiftyTwoWeekHigh', 0) > 0 else 0,
            'Distance_from_52W_Low': ((current_price - info.get('fiftyTwoWeekLow', current_price)) / info.get('fiftyTwoWeekLow', current_price) * 100) if info.get('fiftyTwoWeekLow', 0) > 0 else 0,
        }
        
        try:
            finviz_stock = finvizfinance(ticker)
            finviz_data = finviz_stock.TickerOverview()
            analysis['Insider_Ownership'] = float(finviz_data.get('Insider Own', '0').replace('%', '')) if finviz_data.get('Insider Own') else 0
            analysis['Institutional_Ownership'] = float(finviz_data.get('Inst Own', '0').replace('%', '')) if finviz_data.get('Inst Own') else 0
            analysis['Float_Short'] = float(finviz_data.get('Short Float', '0').replace('%', '')) if finviz_data.get('Short Float') else 0
        except Exception:
            analysis['Insider_Ownership'] = 0
            analysis['Institutional_Ownership'] = 0
            analysis['Float_Short'] = 0
        
        doubling_score = 0
        reasons = []
        
        # Price-based factors
        if current_price < 5:
            doubling_score += 20
            reasons.append("Low price (<$5)")
        elif current_price < 10:
            doubling_score += 15
            reasons.append("Moderate price (<$10)")
        
        # Market cap
        if analysis['Market_Cap'] < 500_000_000:
            doubling_score += 25
            reasons.append("Micro cap (<$500M)")
        elif analysis['Market_Cap'] < 2_000_000_000:
            doubling_score += 20
            reasons.append("Small cap (<$2B)")
        
        # Volume spike
        if analysis['Volume_Spike'] > 2:
            doubling_score += 15
            reasons.append("High volume spike")
        
        # Short interest
        if analysis['Float_Short'] > 20:
            doubling_score += 20
            reasons.append("High short interest")
        elif analysis['Float_Short'] > 10:
            doubling_score += 10
            reasons.append("Moderate short interest")
        
        # Momentum
        if analysis['Price_Change_1D'] > 5:
            doubling_score += 10
            reasons.append("Strong daily momentum")
        if analysis['Price_Change_5D'] > 15:
            doubling_score += 10
            reasons.append("Strong weekly momentum")
        
        # Volatility
        if analysis['Volatility'] > 5:
            doubling_score += 10
            reasons.append("High volatility")
        
        # Analyst targets
        if analysis['Analyst_Target'] > 0 and analysis['Analyst_Target'] > current_price * 1.5:
            doubling_score += 15
            reasons.append("High analyst targets")
        
        # Growth metrics
        if analysis['Revenue_Growth'] and analysis['Revenue_Growth'] > 0.2:
            doubling_score += 10
            reasons.append("Strong revenue growth")
        if analysis['Earnings_Growth'] and analysis['Earnings_Growth'] > 0.3:
            doubling_score += 10
            reasons.append("Strong earnings growth")
        
        # Ownership
        if analysis['Insider_Ownership'] > 20:
            doubling_score += 10
            reasons.append("High insider ownership")
        if analysis['Institutional_Ownership'] < 30:
            doubling_score += 5
            reasons.append("Low institutional ownership")
        
        analysis['Doubling_Score'] = doubling_score
        analysis['Reasons'] = ', '.join(reasons)
        
        return analysis
        
    except Exception as e:
        print(f"❌ Error analyzing {ticker}: {e}")
        return None

def analyze_options(ticker_str, min_upside_ratio=0.1, min_open_interest=10, max_expiry_days=90):
    """Enhanced options analysis for finding high-reward opportunities"""
    ticker = yf.Ticker(ticker_str)
    try:
        expiries = ticker.options
        if not expiries:
            return None
        
        current_price = ticker.history(period="1d")['Close'].iloc[-1]
        today = pd.Timestamp.today()
        
        # Find multiple high-reward opportunities
        opportunities = []
        
        for expiry in expiries:
            expiry_date = pd.Timestamp(expiry)
            days_to_expiry = (expiry_date - today).days
            
            # Focus on shorter-term options for higher gamma/leverage
            if days_to_expiry > max_expiry_days:
                continue
            
            try:
                opt_chain = ticker.option_chain(expiry)
                calls = opt_chain.calls
                
                for _, row in calls.iterrows():
                    ask = row['ask']
                    bid = row['bid']
                    strike = row['strike']
                    open_interest = row.get('openInterest', 0)
                    volume = row.get('volume', 0)
                    
                    # Skip invalid options
                    if ask == 0 or pd.isna(ask) or ask < 0.01:
                        continue
                    
                    # Focus on cheaper options for higher leverage
                    if ask > current_price * 0.3:  # Skip if option costs more than 30% of stock price
                        continue
                    
                    # Calculate various metrics
                    intrinsic_value = max(0, current_price - strike)
                    time_value = ask - intrinsic_value
                    moneyness = current_price / strike if strike > 0 else 0
                    
                    # Calculate potential returns
                    # Scenario 1: Stock moves to strike (break-even)
                    breakeven_return = (strike - current_price) / ask if ask > 0 else 0
                    
                    # Scenario 2: Stock doubles (conservative)
                    double_price = current_price * 2
                    double_return = (double_price - strike) / ask if ask > 0 and double_price > strike else 0
                    
                    # Scenario 3: Stock moves 50% (more realistic)
                    fifty_percent_price = current_price * 1.5
                    fifty_percent_return = (fifty_percent_price - strike) / ask if ask > 0 and fifty_percent_price > strike else 0
                    
                    # Scenario 4: Stock moves 25% (conservative)
                    twenty_five_percent_price = current_price * 1.25
                    twenty_five_percent_return = (twenty_five_percent_price - strike) / ask if ask > 0 and twenty_five_percent_price > strike else 0
                    
                    # Scenario 3: Stock hits analyst target (if available)
                    analyst_target = ticker.info.get('targetMeanPrice', 0)
                    target_return = 0
                    if analyst_target > strike and ask > 0:
                        target_return = (analyst_target - strike) / ask
                    
                    # Calculate risk/reward ratio
                    max_loss = ask  # Maximum loss is the premium paid
                    potential_gain = max(double_return, target_return) * ask
                    risk_reward = potential_gain / max_loss if max_loss > 0 else 0
                    
                    # Scoring system for opportunities
                    score = 0
                    reasons = []
                    
                    # High leverage (low cost relative to stock price)
                    if ask < current_price * 0.05:  # Option costs less than 5% of stock price
                        score += 25
                        reasons.append("Ultra leverage")
                    elif ask < current_price * 0.1:  # Option costs less than 10% of stock price
                        score += 20
                        reasons.append("High leverage")
                    elif ask < current_price * 0.2:  # Option costs less than 20% of stock price
                        score += 15
                        reasons.append("Good leverage")
                    
                    # Near-the-money options (higher gamma)
                    if 0.8 < moneyness < 1.2:
                        score += 15
                        reasons.append("Near-the-money")
                    
                    # High potential returns (use 25% move as baseline for penny stocks)
                    if twenty_five_percent_return > 5:  # 500%+ return if stock moves 25%
                        score += 35
                        reasons.append("MASSIVE upside")
                    elif twenty_five_percent_return > 2:  # 200%+ return if stock moves 25%
                        score += 25
                        reasons.append("Massive upside")
                    elif twenty_five_percent_return > 1:  # 100%+ return if stock moves 25%
                        score += 15
                        reasons.append("High upside")
                    elif twenty_five_percent_return > 0.5:  # 50%+ return if stock moves 25%
                        score += 10
                        reasons.append("Good upside")
                    
                    # Bonus for realistic scenarios
                    if fifty_percent_return > 1:  # 100%+ return if stock moves 50%
                        score += 10
                        reasons.append("Realistic upside")
                    
                    # Good risk/reward
                    if risk_reward > 10:
                        score += 20
                        reasons.append("Excellent R/R")
                    elif risk_reward > 5:
                        score += 10
                        reasons.append("Good R/R")
                    
                    # Short time to expiry (higher gamma)
                    if days_to_expiry < 30:
                        score += 10
                        reasons.append("High gamma")
                    
                    # Some liquidity
                    if open_interest > min_open_interest or volume > 0:
                        score += 5
                        reasons.append("Some liquidity")
                    
                    # Only include high-scoring opportunities with meaningful returns
                    if score >= 30 and twenty_five_percent_return >= 0.5:  # At least 50% return if stock moves 25%
                        opportunities.append({
                            'expiry': expiry,
                            'strike': strike,
                            'ask': ask,
                            'bid': bid,
                            'current_price': current_price,
                            'moneyness': moneyness,
                            'days_to_expiry': days_to_expiry,
                            'open_interest': open_interest,
                            'volume': volume,
                            'breakeven_return': breakeven_return,
                            'double_return': double_return,
                            'fifty_percent_return': fifty_percent_return,
                            'twenty_five_percent_return': twenty_five_percent_return,
                            'target_return': target_return,
                            'risk_reward': risk_reward,
                            'score': score,
                            'reasons': reasons,
                            'symbol': ticker_str
                        })
                        
            except Exception as e:
                continue  # Skip this expiry if there's an error
        
        # Sort by score and return top opportunities
        opportunities.sort(key=lambda x: x['score'], reverse=True)
        return opportunities[:3]  # Return top 3 opportunities
        
    except Exception as e:
        return None

def calculate_greeks(S, K, T, r, sigma, option_type='call'):
    """Calculate option Greeks using Black-Scholes model"""
    try:
        # Convert time to years
        T = T / 365.0
        
        # Validate inputs to prevent invalid calculations
        if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
            return None
        
        # Calculate d1 and d2
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        if option_type == 'call':
            # Delta
            delta = norm.cdf(d1)
            
            # Gamma
            gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
            
            # Theta
            theta = (-S * norm.pdf(d1) * sigma / (2 * np.sqrt(T)) - 
                    r * K * np.exp(-r * T) * norm.cdf(d2))
            
            # Vega
            vega = S * np.sqrt(T) * norm.pdf(d1)
            
        else:  # Put
            # Delta
            delta = norm.cdf(d1) - 1
            
            # Gamma
            gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
            
            # Theta
            theta = (-S * norm.pdf(d1) * sigma / (2 * np.sqrt(T)) + 
                    r * K * np.exp(-r * T) * norm.cdf(-d2))
            
            # Vega
            vega = S * np.sqrt(T) * norm.pdf(d1)
        
        return {
            'delta': delta,
            'gamma': gamma,
            'theta': theta,
            'vega': vega
        }
    except Exception:
        return None

def analyze_options_with_greeks(ticker_str, min_upside_ratio=0.1, min_open_interest=10, max_expiry_days=90):
    """Enhanced options analysis with Greeks calculations"""
    ticker = yf.Ticker(ticker_str)
    try:
        expiries = ticker.options
        if not expiries:
            return None
        
        current_price = ticker.history(period="1d")['Close'].iloc[-1]
        today = pd.Timestamp.today()
        
        # Get volatility from historical data
        hist = ticker.history(period="30d")
        if len(hist) > 1:
            returns = hist['Close'].pct_change().dropna()
            volatility = returns.std() * np.sqrt(252)  # Annualized volatility
        else:
            volatility = 0.5  # Default 50% volatility for penny stocks
        
        # Risk-free rate (approximate)
        r = 0.05  # 5% risk-free rate
        
        opportunities = []
        
        for expiry in expiries:
            expiry_date = pd.Timestamp(expiry)
            days_to_expiry = (expiry_date - today).days
            
            if days_to_expiry > max_expiry_days:
                continue
            
            try:
                opt_chain = ticker.option_chain(expiry)
                calls = opt_chain.calls
                
                for _, row in calls.iterrows():
                    ask = row['ask']
                    bid = row['bid']
                    strike = row['strike']
                    open_interest = row.get('openInterest', 0)
                    volume = row.get('volume', 0)
                    
                    if ask == 0 or pd.isna(ask) or ask < 0.01:
                        continue
                    
                    # Calculate Greeks
                    greeks = calculate_greeks(current_price, strike, days_to_expiry, r, volatility, 'call')
                    
                    if greeks is None:
                        continue
                    
                    # Validate Greeks values
                    if (np.isnan(greeks['delta']) or np.isnan(greeks['gamma']) or 
                        np.isnan(greeks['theta']) or np.isnan(greeks['vega'])):
                        continue
                    
                    # Calculate potential returns
                    return_25 = (current_price * 1.25 - strike) / ask if current_price * 1.25 > strike else 0
                    return_50 = (current_price * 1.5 - strike) / ask if current_price * 1.5 > strike else 0
                    return_100 = (current_price * 2 - strike) / ask if current_price * 2 > strike else 0
                    
                    # Scoring based on Greeks and returns
                    score = 0
                    reasons = []
                    
                    # High Gamma (sensitive to price changes)
                    if greeks['gamma'] > 0.1:
                        score += 25
                        reasons.append("High Gamma")
                    elif greeks['gamma'] > 0.05:
                        score += 15
                        reasons.append("Good Gamma")
                    
                    # High Delta (moves with stock)
                    if greeks['delta'] > 0.7:
                        score += 20
                        reasons.append("High Delta")
                    elif greeks['delta'] > 0.5:
                        score += 15
                        reasons.append("Good Delta")
                    
                    # Low Theta (time decay)
                    if abs(greeks['theta']) < 0.01:
                        score += 15
                        reasons.append("Low Theta")
                    
                    # High Vega (volatility sensitivity)
                    if greeks['vega'] > 0.1:
                        score += 10
                        reasons.append("High Vega")
                    
                    # Return potential
                    if return_25 > 2:  # 200%+ return on 25% move
                        score += 30
                        reasons.append("Massive upside")
                    elif return_25 > 1:  # 100%+ return on 25% move
                        score += 20
                        reasons.append("High upside")
                    
                    # Leverage
                    if ask < current_price * 0.1:
                        score += 15
                        reasons.append("High leverage")
                    
                    # Only include high-scoring opportunities
                    if score >= 40 and return_25 >= 0.5:
                        opportunities.append({
                            'expiry': expiry,
                            'strike': strike,
                            'ask': ask,
                            'bid': bid,
                            'current_price': current_price,
                            'days_to_expiry': days_to_expiry,
                            'open_interest': open_interest,
                            'volume': volume,
                            'return_25': return_25,
                            'return_50': return_50,
                            'return_100': return_100,
                            'score': score,
                            'reasons': reasons,
                            'symbol': ticker_str,
                            'greeks': greeks,
                            'volatility': volatility
                        })
                        
            except Exception:
                continue
        
        opportunities.sort(key=lambda x: x['score'], reverse=True)
        return opportunities[:3]
        
    except Exception:
        return None

def find_penny_stock_options():
    """Dynamically find penny stocks with options for maximum leverage"""
    print("\n🔍 Dynamically searching for penny stock options...")
    penny_options = []
    
    # Strategy 1: Use Finviz screener to find penny stocks with options
    try:
        from finvizfinance.screener.technical import Technical
        
        # Create screener for penny stocks with high volume
        penny_filters = {
            'Price': 'Under $5',
            'Average Volume': 'Over 1M',  # Higher volume for options liquidity
            'Market Cap.': 'Any',  # Include all market caps
            'Performance': 'Today Up'  # Momentum
        }
        
        screener = Technical()
        screener.set_filter(filters_dict=penny_filters)
        penny_df = screener.screener_view(order='Volume', limit=50, ascend=False)
        
        if penny_df is not None and not penny_df.empty:
            print(f"Found {len(penny_df)} penny stocks from screener")
            
            # Test each stock for options availability
            for ticker in penny_df['Ticker'].head(20):  # Test top 20
                try:
                    yft = yf.Ticker(ticker)
                    
                    # Check if options exist
                    if not yft.options:
                        continue
                    
                    current_price = yft.history(period="1d")['Close'].iloc[-1]
                    
                    # Double-check price is under $5
                    if current_price > 5:
                        continue
                    
                    print(f"  Testing {ticker} (${current_price:.2f}) for options...")
                    
                    opportunities = analyze_options_with_greeks(ticker, min_upside_ratio=0.1, min_open_interest=5, max_expiry_days=60)
                    if opportunities:
                        for opt in opportunities:
                            opt['ticker'] = ticker
                            opt['current_price'] = current_price
                            penny_options.append(opt)
                            
                except Exception as e:
                    continue
                    
    except Exception as e:
        print(f"Error with Finviz screener: {e}")
    
    # Strategy 2: Use dynamic scraping to find trending penny stocks
    if len(penny_options) < 5:  # If we need more options
        print("Supplementing with dynamically found trending penny stocks...")
        
        try:
            trending_stocks = get_trending_penny_stocks()
            print(f"Found {len(trending_stocks)} trending stocks to test")
            
            # Add Reddit trending stocks
            reddit_stocks = get_reddit_trending_stocks()
            if reddit_stocks:
                print(f"Found {len(reddit_stocks)} Reddit trending stocks")
                trending_stocks.extend(reddit_stocks)
                trending_stocks = list(set(trending_stocks))  # Remove duplicates
            
            for ticker in trending_stocks[:15]:  # Test top 15
                try:
                    yft = yf.Ticker(ticker)
                    
                    # Check if options exist
                    if not yft.options:
                        continue
                    
                    current_price = yft.history(period="1d")['Close'].iloc[-1]
                    
                    # Only analyze penny stocks
                    if current_price > 5:
                        continue
                    
                    print(f"  Testing {ticker} (${current_price:.2f}) for options...")
                    
                    opportunities = analyze_options_with_greeks(ticker, min_upside_ratio=0.1, min_open_interest=5, max_expiry_days=60)
                    if opportunities:
                        for opt in opportunities:
                            opt['ticker'] = ticker
                            opt['current_price'] = current_price
                            penny_options.append(opt)
                            
                except Exception:
                    continue
                    
        except Exception as e:
            print(f"Error with dynamic scraping: {e}")
    
    return penny_options

def find_ultra_cheap_options():
    """Find ultra-cheap options with massive potential returns"""
    print("\n🔍 Searching for ultra-cheap options...")
    ultra_options = []
    
    # Focus on very low-priced stocks that might have cheap options
    ultra_penny_stocks = ['SNDL', 'BITF', 'HEXO', 'ACB', 'TLRY', 'CGC', 'APHA', 'CRON', 'OGI', 'VFF']
    
    for ticker in ultra_penny_stocks:
        try:
            yft = yf.Ticker(ticker)
            current_price = yft.history(period="1d")['Close'].iloc[-1]
            
            if current_price > 3 or not yft.options:  # Only very cheap stocks
                continue
            
            print(f"  Testing ultra-cheap {ticker} (${current_price:.2f})...")
            
            # Look for very cheap options
            for expiry in yft.options[:3]:  # Check first 3 expiries
                try:
                    opt_chain = yft.option_chain(expiry)
                    calls = opt_chain.calls
                    
                    for _, row in calls.iterrows():
                        ask = row['ask']
                        strike = row['strike']
                        
                        # Only ultra-cheap options
                        if ask < 0.10 and ask > 0.01:  # Between $0.01 and $0.10
                            # Calculate potential returns
                            if current_price * 1.5 > strike:  # Stock moves 50%
                                return_50 = (current_price * 1.5 - strike) / ask
                                if return_50 > 2:  # At least 200% return
                                    # Calculate Greeks for ultra-cheap options
                                    greeks = calculate_greeks(current_price, strike, days_to_expiry, 0.05, 0.8, 'call')
                                    ultra_options.append({
                                        'ticker': ticker,
                                        'current_price': current_price,
                                        'strike': strike,
                                        'ask': ask,
                                        'expiry': expiry,
                                        'return_50': return_50,
                                        'return_100': (current_price * 2 - strike) / ask if current_price * 2 > strike else 0,
                                        'greeks': greeks
                                    })
                                    
                except Exception:
                    continue
                    
        except Exception:
            continue
    
    return ultra_options

def get_trending_penny_stocks():
    """Scrape trending penny stocks from various sources"""
    trending_stocks = set()
    
    # Strategy 1: Scrape from Finviz gainers
    try:
        url = "https://finviz.com/screener.ashx?v=111&s=ta_topgainers&f=sh_price_u5,sh_avgvol_o500"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            # Find ticker symbols in the table
            ticker_links = soup.find_all('a', href=lambda x: x and 'quote.ashx' in x)
            for link in ticker_links:
                ticker = link.text.strip()
                if ticker and len(ticker) <= 5:  # Valid ticker format
                    trending_stocks.add(ticker)
                    
    except Exception as e:
        print(f"Error scraping Finviz: {e}")
    
    # Strategy 2: Get from Yahoo Finance trending
    try:
        url = "https://finance.yahoo.com/trending-tickers"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            # Look for ticker symbols
            ticker_elements = soup.find_all(string=lambda text: text and len(text.strip()) <= 5 and text.strip().isupper())
            for ticker in ticker_elements:
                if ticker.strip():
                    trending_stocks.add(ticker.strip())
                    
    except Exception as e:
        print(f"Error scraping Yahoo: {e}")
    
    # Strategy 3: Use yfinance to get some known penny stocks with options
    known_penny_options = [
        'SNDL', 'BITF', 'HEXO', 'ACB', 'TLRY', 'CGC', 'APHA', 'CRON', 'OGI', 'VFF',
        'NBEV', 'FIZZ', 'MNST', 'KO', 'PEP', 'CCEP', 'KDP', 'BUD', 'TAP', 'SAM',
        'RIOT', 'MARA', 'COIN', 'HOOD', 'PLTR', 'RBLX', 'HOOD', 'COIN', 'MSTR'
    ]
    
    for ticker in known_penny_options:
        trending_stocks.add(ticker)
    
    return list(trending_stocks)

def get_reddit_trending_stocks():
    """Get trending stocks from Reddit communities"""
    print("\n🔍 Scraping Reddit for trending stocks...")
    reddit_stocks = set()
    
    try:
        # Initialize Reddit client with environment variables
        if not all([REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USERNAME, REDDIT_PASSWORD]):
            print("  Reddit credentials not found in environment variables. Skipping Reddit scraping.")
            return []
            
        reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET, 
            user_agent="PennyStockScreener/1.0",
            username=REDDIT_USERNAME,
            password=REDDIT_PASSWORD,
        )
        
        # Subreddits to monitor for penny stocks
        subreddits = [
            "pennystocks",
            "wallstreetbets", 
            "stocks",
            "investing",
            "StockMarket"
        ]
        
        for subreddit_name in subreddits:
            try:
                subreddit = reddit.subreddit(subreddit_name)
                
                # Get hot posts from the last 24 hours
                for submission in subreddit.hot(limit=20):
                    title = submission.title.upper()
                    text = submission.selftext.upper() if submission.selftext else ""
                    
                    # Look for stock tickers (1-5 capital letters)
                    import re
                    tickers = re.findall(r'\b[A-Z]{1,5}\b', title + " " + text)
                    
                    for ticker in tickers:
                        # Filter out common words that aren't tickers
                        if ticker not in ['THE', 'AND', 'FOR', 'YOU', 'ARE', 'WAS', 'HAS', 'HAD', 'NOT', 'BUT', 'ALL', 'CAN', 'HER', 'WERE', 'SHE', 'HIS', 'ONE', 'SAID', 'THEY', 'EACH', 'WHICH', 'SHE', 'DO', 'HOW', 'THEIR', 'IF', 'WILL', 'UP', 'OTHER', 'ABOUT', 'OUT', 'MANY', 'THEN', 'THEM', 'THESE', 'SO', 'SOME', 'HER', 'WOULD', 'MAKE', 'LIKE', 'INTO', 'HIM', 'TIME', 'HAS', 'TWO', 'MORE', 'GO', 'NO', 'WAY', 'COULD', 'MY', 'THAN', 'FIRST', 'BEEN', 'CALL', 'WHO', 'ITS', 'NOW', 'FIND', 'LONG', 'DOWN', 'DAY', 'DID', 'GET', 'COME', 'MADE', 'MAY', 'PART']:
                            reddit_stocks.add(ticker)
                            
            except Exception as e:
                print(f"  Error scraping r/{subreddit_name}: {e}")
                continue
                
    except Exception as e:
        print(f"  Error initializing Reddit client: {e}")
        print("  Note: Check your Reddit API credentials in .env file")
    
    return list(reddit_stocks)

def post_results_to_reddit(results_df, options_found, portfolio_allocation=None, confidence_allocation=None):
    """Post screener results to Reddit"""
    try:
        # Check if Reddit credentials are available
        if not all([REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USERNAME, REDDIT_PASSWORD]):
            print("❌ Reddit credentials not found in environment variables. Cannot post to Reddit.")
            return
            
        # Initialize Reddit client
        reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            user_agent="PennyStockScreener/1.0", 
            username=REDDIT_USERNAME,
            password=REDDIT_PASSWORD,
        )
        
        # Create post content
        title = f"🚀 Penny Stock Screener Results - {datetime.now().strftime('%Y-%m-%d')}"
        
        text = "## 🔥 TOP DOUBLING CANDIDATES\n\n"
        
        # Add top 5 stocks
        for i, (_, row) in enumerate(results_df.head(5).iterrows(), 1):
            text += f"**#{i}: {row['Ticker']}** - Score: {row['Doubling_Score']}\n"
            text += f"- Price: ${row['Current_Price']:.2f} | Market Cap: ${row['Market_Cap']:,.0f}\n"
            text += f"- Daily Change: {row['Price_Change_1D']:+.1f}% | Volume Spike: {row['Volume_Spike']:.1f}x\n"
            if row['Analyst_Target'] > 0:
                target_potential = ((row['Analyst_Target'] - row['Current_Price']) / row['Current_Price']) * 100
                text += f"- Analyst Target: ${row['Analyst_Target']:.2f} ({target_potential:+.1f}% potential)\n"
            text += f"- Reasons: {row['Reasons']}\n\n"
        
        # Add Kelly Criterion Portfolio Allocation
        if portfolio_allocation and portfolio_allocation['allocations']:
            text += "## 🎯 KELLY CRITERION PORTFOLIO ALLOCATION ($1,000)\n\n"
            text += f"**Portfolio Summary:**\n"
            text += f"- Total Allocated: ${portfolio_allocation['total_allocated']:.0f}\n"
            text += f"- Cash Remaining: ${portfolio_allocation['cash_remaining']:.0f}\n"
            text += f"- Allocation %: {portfolio_allocation['allocation_percentage']:.1f}%\n"
            text += f"- Number of Positions: {len(portfolio_allocation['allocations'])}\n\n"
            
            text += "**Top Kelly Allocations:**\n"
            for i, alloc in enumerate(portfolio_allocation['allocations'][:5], 1):
                text += f"{i}. **{alloc['ticker']}** - ${alloc['dollar_allocation']:.0f} ({alloc['scaled_kelly']:.1%})\n"
                text += f"   - Shares: {alloc['shares_to_buy']} | Win Rate: {alloc['win_probability']:.1%}\n"
                text += f"   - Kelly Score: {alloc['kelly_fraction']:.1%} | Doubling Score: {alloc['doubling_score']}\n\n"
        
        # Add Confidence-Weighted Kelly Comparison
        if confidence_allocation and confidence_allocation['allocations']:
            text += "## 📊 CONFIDENCE-WEIGHTED KELLY ANALYSIS\n\n"
            text += f"**Confidence-Weighted Summary:**\n"
            text += f"- Total Allocated: ${confidence_allocation['total_allocated']:.0f}\n"
            text += f"- Cash Remaining: ${confidence_allocation['cash_remaining']:.0f}\n"
            text += f"- Allocation %: {confidence_allocation['allocation_percentage']:.1f}%\n"
            text += f"- Number of Positions: {len(confidence_allocation['allocations'])}\n\n"
            
            if portfolio_allocation:
                standard_allocated = portfolio_allocation['total_allocated']
                confidence_allocated = confidence_allocation['total_allocated']
                difference = confidence_allocated - standard_allocated
                percent_change = ((confidence_allocated/standard_allocated - 1)*100) if standard_allocated > 0 else 0
                
                text += f"**Comparison:**\n"
                text += f"- Standard Kelly: ${standard_allocated:.0f}\n"
                text += f"- Confidence-Weighted: ${confidence_allocated:.0f}\n"
                text += f"- Difference: ${difference:+.0f} ({percent_change:+.1f}%)\n\n"
            
            text += "**Top Confidence-Weighted Allocations:**\n"
            for i, alloc in enumerate(confidence_allocation['allocations'][:3], 1):
                text += f"{i}. **{alloc['ticker']}** - ${alloc['dollar_allocation']:.0f} ({alloc['scaled_kelly']:.1%})\n"
                text += f"   - Confidence: {alloc['confidence_factor']:.1%} | Sample Size: {alloc['sample_size']} days\n"
                text += f"   - Win Rate: {alloc['win_probability']:.1%} | Volatility: {alloc['volatility']:.1%}\n\n"
        
        # Add Kelly Criterion Insights
        text += "## 💡 KELLY CRITERION INSIGHTS\n\n"
        text += "• **Kelly Criterion** maximizes long-term geometric growth\n"
        text += "• **Confidence-weighted Kelly** adjusts for uncertainty in estimates\n"
        text += "• **Higher confidence** = larger position sizes\n"
        text += "• **Lower confidence** = smaller position sizes (more conservative)\n"
        text += "• **Half-Kelly (50%)** provides ~90% of growth with half the volatility\n"
        text += "• **Rebalance monthly** based on updated Kelly calculations\n\n"
        
        # Add detailed options analysis
        if options_found:
            text += "## 🎯 OPTIONS OPPORTUNITIES\n\n"
            text += f"Found {len(options_found)} high-reward option opportunities:\n\n"
            
            # Sort options by score
            options_found.sort(key=lambda x: x.get('score', 0), reverse=True)
            
            # Add top 3 options with key details
            for i, opt in enumerate(options_found[:3], 1):
                text += f"**#{i}: {opt['ticker']}** - Score: {opt.get('score', 'N/A')}\n"
                text += f"- Strike: ${opt['strike']:.2f} | Cost: ${opt['ask']:.2f} | Expiry: {opt['expiry']}\n"
                text += f"- Current Price: ${opt['current_price']:.2f}\n"
                
                # Add key returns
                if opt.get('return_25', 0) > 0:
                    text += f"- 25% move: {opt['return_25']:.0f}% return\n"
                if opt.get('return_50', 0) > 0:
                    text += f"- 50% move: {opt['return_50']:.0f}% return\n"
                if opt.get('return_100', 0) > 0:
                    text += f"- 100% move: {opt['return_100']:.0f}% return\n"
                
                # Add key reasons
                if opt.get('reasons'):
                    text += f"- Reasons: {', '.join(opt['reasons'][:3])}\n"  # Limit to top 3 reasons
                
                text += "\n"
        
        text += "---\n"
        text += "*Generated by Penny Stock Screener with Kelly Criterion Analysis*\n"
        text += "*Not financial advice - Always do your own research!*\n"
        text += "*Kelly Criterion optimizes position sizing for long-term growth*"
        
        # Post to subreddit
        subreddit = reddit.subreddit("cryptocurrensea")
        submission = subreddit.submit(title, selftext=text)
        print(f"✅ Posted results to Reddit: {submission.permalink}")
        
    except Exception as e:
        print(f"❌ Error posting to Reddit: {e}")
        print("  Note: Check your Reddit API credentials in .env file")

def main():
    print("🚀 POTENTIAL DOUBLING STOCKS SCREENER")
    print("=" * 60)
    print("Finding stocks with potential for significant gains...")
    
    filters = {
        'Market Cap.': 'Small ($300mln to $2bln)',  
        'Price': 'Under $10',                   
        'Average Volume': 'Over 500K',           
        'Relative Volume': 'Over 1.5',           
        'Performance': 'Today Up'                
    }
    
    print("\n📊 Applying filters:")
    for key, value in filters.items():
        print(f"  - {key}: {value}")
    
    screener = Technical()
    screener.set_filter(filters_dict=filters)
    
    df = screener.screener_view(order='Change', limit=50, ascend=False)
    
    if df is None or df.empty:
        print("❌ No stocks found matching criteria")
        return
    
    print(f"\n✅ Found {len(df)} initial candidates")
    
    print("\n🔍 Analyzing top candidates...")
    detailed_analysis = []
    
    tickers_to_analyze = df['Ticker'].head(10)
    total_tickers = len(tickers_to_analyze)
    
    for i, ticker in enumerate(tickers_to_analyze, 1):
        print(f"  [{i}/{total_tickers}] Analyzing {ticker}...")
        analysis = analyze_stock_potential(ticker)
        if analysis:
            detailed_analysis.append(analysis)
        time.sleep(0.3)
    
    if not detailed_analysis:
        print("❌ No stocks could be analyzed")
        return
    
    results_df = pd.DataFrame(detailed_analysis)
    results_df = results_df.sort_values('Doubling_Score', ascending=False)
    
    print(f"\n🔥 TOP DOUBLING CANDIDATES (Found {len(results_df)} stocks)")
    print("=" * 100)
    
    display_columns = ['Ticker', 'Current_Price', 'Market_Cap', 'Doubling_Score', 
                      'Price_Change_1D', 'Volume_Spike', 'Float_Short', 'Volatility']
    
    available_columns = [col for col in display_columns if col in results_df.columns]
    display_df = results_df[available_columns].head(10)
    
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    print(display_df.to_string(index=False, float_format='%.2f'))
    
    print(f"\n📋 DETAILED BREAKDOWN (TOP 3)")
    print("=" * 100)
    
    for i, (_, row) in enumerate(results_df.head(3).iterrows(), 1):
        print(f"\n🥇 #{i}: {row['Ticker']} | Score: {row['Doubling_Score']}")
        print(f"   Price: ${row['Current_Price']:.2f}, Market Cap: ${row['Market_Cap']:,.0f}")
        print(f"   Daily Change: {row['Price_Change_1D']:+.1f}%, Vol Spike: {row['Volume_Spike']:.1f}x")
        print(f"   Short Float: {row['Float_Short']:.1f}%, Volatility: {row['Volatility']:.1f}%")
        print(f"   Reasons: {row['Reasons']}")
        if row['Analyst_Target'] > 0:
            target_potential = ((row['Analyst_Target'] - row['Current_Price']) / row['Current_Price']) * 100
            print(f"   Analyst Target: ${row['Analyst_Target']:.2f} ({target_potential:+.1f}% potential)")
    
    # KELLY CRITERION PORTFOLIO ALLOCATION
    print(f"\n🎯 KELLY CRITERION PORTFOLIO ALLOCATION ANALYSIS")
    print("=" * 100)
    
    print("Calculating optimal portfolio allocation using Kelly Criterion...")
    print("This will determine the optimal position sizes for a $1000 portfolio.")
    
    # Convert DataFrame to list of dictionaries for Kelly analysis
    stocks_data = results_df.head(10).to_dict('records')  # Use top 10 stocks
    
    # Calculate standard Kelly portfolio allocation
    portfolio_allocation = calculate_portfolio_allocation(
        stocks_data, 
        portfolio_value=1000, 
        scaling_factor=0.5  # Half-Kelly for reduced volatility
    )
    
    # Calculate risk metrics
    risk_metrics = calculate_risk_metrics(portfolio_allocation)
    
    # Display standard Kelly allocation results
    display_kelly_portfolio_allocation(portfolio_allocation, risk_metrics, portfolio_value=1000)
    
    # CONFIDENCE-WEIGHTED KELLY CRITERION ANALYSIS
    print(f"\n🎯 CONFIDENCE-WEIGHTED KELLY CRITERION ANALYSIS")
    print("=" * 100)
    
    print("Calculating confidence-weighted portfolio allocation...")
    print("This incorporates uncertainty in probability estimates for more robust position sizing.")
    
    # Calculate confidence-weighted Kelly portfolio allocation
    confidence_portfolio_allocation = calculate_confidence_weighted_portfolio_allocation(
        stocks_data, 
        portfolio_value=1000, 
        scaling_factor=0.5,  # Half-Kelly scaling
        risk_aversion=1.0    # Moderate risk aversion
    )
    
    # Display confidence-weighted allocation results
    display_confidence_weighted_allocation(confidence_portfolio_allocation, portfolio_value=1000)
    
    # Compare standard vs confidence-weighted approaches
    print(f"\n📊 STANDARD vs CONFIDENCE-WEIGHTED KELLY COMPARISON")
    print("-" * 80)
    
    standard_allocated = portfolio_allocation['total_allocated']
    confidence_allocated = confidence_portfolio_allocation['total_allocated']
    standard_positions = len(portfolio_allocation['allocations'])
    confidence_positions = len(confidence_portfolio_allocation['allocations'])
    
    print(f"  Standard Kelly: ${standard_allocated:.0f} allocated, {standard_positions} positions")
    print(f"  Confidence-Weighted: ${confidence_allocated:.0f} allocated, {confidence_positions} positions")
    print(f"  Difference: ${confidence_allocated - standard_allocated:+.0f} ({((confidence_allocated/standard_allocated - 1)*100):+.1f}%)")
    
    if confidence_positions > 0:
        avg_confidence = sum(alloc['confidence_factor'] for alloc in confidence_portfolio_allocation['allocations']) / confidence_positions
        print(f"  Average Confidence Factor: {avg_confidence:.1%}")
    
    # Additional Kelly analysis for different scaling factors
    print(f"\n📊 KELLY SCALING COMPARISON")
    print("-" * 50)
    
    scaling_factors = [0.25, 0.5, 0.75, 1.0]  # Quarter, Half, Three-quarter, Full Kelly
    
    for scaling in scaling_factors:
        test_allocation = calculate_portfolio_allocation(stocks_data, 1000, scaling)
        if test_allocation['allocations']:
            print(f"  {scaling*100:.0f}% Kelly: ${test_allocation['total_allocated']:.0f} allocated, "
                  f"{len(test_allocation['allocations'])} positions, "
                  f"{test_allocation['cash_remaining']:.0f} cash remaining")
        else:
            print(f"  {scaling*100:.0f}% Kelly: No suitable allocations")
    
    print(f"\n💡 KELLY CRITERION INSIGHTS:")
    print("-" * 50)
    print("• Kelly Criterion maximizes long-term geometric growth")
    print("• Confidence-weighted Kelly adjusts for uncertainty in estimates")
    print("• Higher confidence = larger position sizes")
    print("• Lower confidence = smaller position sizes")
    print("• Full Kelly can be volatile - consider scaling down")
    print("• Half-Kelly (50%) provides ~90% of growth with half the volatility")
    print("• Quarter-Kelly (25%) is very conservative but still growth-optimal")
    print("• Recalculate Kelly fractions monthly as probabilities change")
    print("• Use remaining cash for new opportunities or risk management")
    
    # ENHANCED OPTIONS ANALYSIS - TOP CANDIDATES FIRST
    print(f"\n🚀 HIGH-REWARD OPTIONS OPPORTUNITIES")
    print("=" * 100)
    
    all_options = []
    
    # First, analyze options for the top candidates (they have the highest potential)
    print("🔍 Analyzing options for top candidates first...")
    for ticker in results_df['Ticker'].head(5):  # Top 5 candidates
        print(f"  Checking options for {ticker}...")
        opportunities = analyze_options_with_greeks(ticker)
        if opportunities:
            for opt in opportunities:
                opt['ticker'] = ticker
                all_options.append(opt)
                print(f"    Found option: Strike ${opt['strike']:.2f} @ ${opt['ask']:.2f} (Score: {opt['score']})")
        else:
            print(f"    No viable options found for {ticker}")
    
    # Then check remaining candidates
    print("\n🔍 Analyzing options for remaining candidates...")
    for ticker in results_df['Ticker'].iloc[5:10]:  # Candidates 6-10
        print(f"  Checking options for {ticker}...")
        opportunities = analyze_options_with_greeks(ticker)
        if opportunities:
            for opt in opportunities:
                opt['ticker'] = ticker
                all_options.append(opt)
                print(f"    Found option: Strike ${opt['strike']:.2f} @ ${opt['ask']:.2f} (Score: {opt['score']})")
        else:
            print(f"    No viable options found for {ticker}")
    
    if all_options:
        # Sort all options by score
        all_options.sort(key=lambda x: x['score'], reverse=True)
        
        print(f"\n✅ Found {len(all_options)} high-reward option opportunities:")
        print()
        
        for i, opt in enumerate(all_options[:10], 1):  # Show top 10
            print(f"🥇 #{i}: {opt['ticker']} - Score: {opt['score']}")
            print(f"   Strike: ${opt['strike']:.2f} | Cost: ${opt['ask']:.2f} | Expiry: {opt['expiry']} ({opt['days_to_expiry']} days)")
            print(f"   Current Price: ${opt['current_price']:.2f} | Volatility: {opt.get('volatility', 0):.1%}")
            print(f"   Greeks: Δ={opt['greeks']['delta']:.3f} | Γ={opt['greeks']['gamma']:.3f} | Θ={opt['greeks']['theta']:.3f} | ν={opt['greeks']['vega']:.3f}")
            print(f"   If Stock +25%: {opt['return_25']:.0f}% return")
            print(f"   If Stock +50%: {opt['return_50']:.0f}% return")
            print(f"   If Stock Doubles: {opt['return_100']:.0f}% return")
            print(f"   Reasons: {', '.join(opt['reasons'])}")
            print()
    else:
        print("No high-reward options found in screened stocks.")
    
    # SPECIAL ANALYSIS FOR TOP CANDIDATES
    print(f"\n🔍 SPECIAL ANALYSIS - ANY OPTIONS FOR TOP CANDIDATES")
    print("=" * 100)
    
    top_candidates_with_options = []
    for ticker in results_df['Ticker'].head(3):  # Top 3 candidates
        try:
            yft = yf.Ticker(ticker)
            if yft.options:
                current_price = yft.history(period="1d")['Close'].iloc[-1]
                print(f"\n📊 {ticker} (${current_price:.2f}) has options available:")
                
                # Show all available options
                for expiry in yft.options[:2]:  # First 2 expiries
                    try:
                        opt_chain = yft.option_chain(expiry)
                        calls = opt_chain.calls.head(10)  # Top 10 calls
                        
                        print(f"  Expiry: {expiry}")
                        for _, row in calls.iterrows():
                            ask = row['ask']
                            strike = row['strike']
                            if ask > 0:
                                # Calculate returns for different scenarios
                                return_25 = (current_price * 1.25 - strike) / ask if current_price * 1.25 > strike else 0
                                return_50 = (current_price * 1.5 - strike) / ask if current_price * 1.5 > strike else 0
                                return_100 = (current_price * 2 - strike) / ask if current_price * 2 > strike else 0
                                
                                # Show if it's a good opportunity
                                if return_25 > 0.5 or return_50 > 1:  # At least 50% return on 25% move or 100% on 50% move
                                    print(f"    🎯 Strike ${strike:.2f} @ ${ask:.2f} | 25% move: {return_25:.0f}% | 50% move: {return_50:.0f}% | 100% move: {return_100:.0f}%")
                                else:
                                    print(f"    Strike ${strike:.2f} @ ${ask:.2f} | 25% move: {return_25:.0f}% | 50% move: {return_50:.0f}% | 100% move: {return_100:.0f}%")
                    except Exception as e:
                        print(f"    Error: {e}")
                        continue
                        
                top_candidates_with_options.append(ticker)
            else:
                print(f"❌ {ticker} has no options available")
        except Exception as e:
            print(f"❌ Error checking {ticker}: {e}")
    
    if not top_candidates_with_options:
        print("None of the top candidates have options available.")
    
    # PENNY STOCK OPTIONS ANALYSIS
    print(f"\n💎 PENNY STOCK OPTIONS (Maximum Leverage)")
    print("=" * 100)
    
    penny_options = find_penny_stock_options()
    
    if penny_options:
        penny_options.sort(key=lambda x: x['score'], reverse=True)
        
        print(f"Found {len(penny_options)} penny stock option opportunities:")
        print()
        
        for i, opt in enumerate(penny_options[:5], 1):  # Show top 5
            print(f"💎 #{i}: {opt['ticker']} - Score: {opt['score']}")
            print(f"   Strike: ${opt['strike']:.2f} | Cost: ${opt['ask']:.2f} | Expiry: {opt['expiry']} ({opt['days_to_expiry']} days)")
            print(f"   Current Price: ${opt['current_price']:.2f}")
            if opt.get('greeks'):
                print(f"   Greeks: Δ={opt['greeks']['delta']:.3f} | Γ={opt['greeks']['gamma']:.3f} | Θ={opt['greeks']['theta']:.3f} | ν={opt['greeks']['vega']:.3f}")
            print(f"   If Stock +25%: {opt.get('return_25', 0):.0f}% return")
            print(f"   If Stock +50%: {opt.get('return_50', 0):.0f}% return")
            print(f"   If Stock Doubles: {opt.get('return_100', 0):.0f}% return")
            print(f"   Reasons: {', '.join(opt['reasons'])}")
            print()
    else:
        print("No penny stock options found. Consider:")
        print("  - Stocks with upcoming catalysts (earnings, FDA decisions)")
        print("  - Biotech stocks with FDA approval potential")
        print("  - Crypto-related stocks during bull runs")
    
    # ULTRA-CHEAP OPTIONS ANALYSIS
    print(f"\n💎 ULTRA-CHEAP OPTIONS (Maximum Leverage)")
    print("=" * 100)
    
    ultra_options = find_ultra_cheap_options()
    
    if ultra_options:
        ultra_options.sort(key=lambda x: x['return_50'], reverse=True)
        
        print(f"Found {len(ultra_options)} ultra-cheap option opportunities:")
        print()
        
        for i, opt in enumerate(ultra_options[:5], 1):  # Show top 5
            print(f"💎 #{i}: {opt['ticker']} - Ultra Cheap Option")
            print(f"   Strike: ${opt['strike']:.2f} | Cost: ${opt['ask']:.3f} | Expiry: {opt['expiry']}")
            print(f"   Current Price: ${opt['current_price']:.2f}")
            if opt.get('greeks'):
                print(f"   Greeks: Δ={opt['greeks']['delta']:.3f} | Γ={opt['greeks']['gamma']:.3f} | Θ={opt['greeks']['theta']:.3f} | ν={opt['greeks']['vega']:.3f}")
            print(f"   If Stock +50%: {opt['return_50']:.0f}% return")
            print(f"   If Stock Doubles: {opt['return_100']:.0f}% return")
            print()
    else:
        print("No ultra-cheap options found.")
        print("These are rare but can provide massive returns if found!")
    
    # KELLY CRITERION OPTIONS ALLOCATION
    print(f"\n🎯 KELLY CRITERION OPTIONS ALLOCATION ANALYSIS")
    print("=" * 100)
    
    # Collect all options for Kelly analysis
    all_options_for_kelly = []
    
    # Add regular options
    for opt in all_options:
        all_options_for_kelly.append({
            'ticker': opt['ticker'],
            'strike': opt['strike'],
            'ask': opt['ask'],
            'expiry': opt['expiry'],
            'current_price': opt['current_price'],
            'days_to_expiry': opt.get('days_to_expiry', 30),
            'return_25': opt.get('return_25', 0),
            'return_50': opt.get('return_50', 0),
            'return_100': opt.get('return_100', 0),
            'score': opt.get('score', 0),
            'reasons': opt.get('reasons', [])
        })
    
    # Add penny options
    for opt in penny_options:
        all_options_for_kelly.append({
            'ticker': opt['ticker'],
            'strike': opt['strike'],
            'ask': opt['ask'],
            'expiry': opt['expiry'],
            'current_price': opt['current_price'],
            'days_to_expiry': opt.get('days_to_expiry', 30),
            'return_25': opt.get('return_25', 0),
            'return_50': opt.get('return_50', 0),
            'return_100': opt.get('return_100', 0),
            'score': opt.get('score', 0),
            'reasons': opt.get('reasons', [])
        })
    
    # Add ultra options
    for opt in ultra_options:
        all_options_for_kelly.append({
            'ticker': opt['ticker'],
            'strike': opt['strike'],
            'ask': opt['ask'],
            'expiry': opt['expiry'],
            'current_price': opt['current_price'],
            'days_to_expiry': 30,  # Default for ultra options
            'return_25': 0,  # Will be calculated
            'return_50': opt.get('return_50', 0),
            'return_100': opt.get('return_100', 0),
            'score': 50,  # Default score for ultra options
            'reasons': ['Ultra cheap option']
        })
    
    if all_options_for_kelly:
        options_allocation = calculate_options_kelly_allocation(all_options_for_kelly, portfolio_value=1000, scaling_factor=0.25)
        display_options_kelly_allocation(options_allocation, portfolio_value=1000)
    else:
        print("No options found for Kelly Criterion analysis.")
    
    # COMBINED PORTFOLIO SUMMARY
    print(f"\n🎯 COMBINED PORTFOLIO SUMMARY (${1000:,})")
    print("=" * 100)
    
    # Calculate combined allocation
    stock_allocation = portfolio_allocation['total_allocated']
    options_allocation_total = options_allocation['total_allocated'] if 'options_allocation' in locals() else 0
    
    total_combined = stock_allocation + options_allocation_total
    cash_remaining = 1000 - total_combined
    
    print(f"📊 COMBINED ALLOCATION:")
    print(f"   Stocks Allocation: ${stock_allocation:.2f} ({stock_allocation/10:.1f}%)")
    print(f"   Options Allocation: ${options_allocation_total:.2f} ({options_allocation_total/10:.1f}%)")
    print(f"   Total Allocated: ${total_combined:.2f} ({total_combined/10:.1f}%)")
    print(f"   Cash Remaining: ${cash_remaining:.2f} ({cash_remaining/10:.1f}%)")
    
    print(f"\n💡 PORTFOLIO STRATEGY:")
    print("-" * 50)
    print("• Core positions: High-conviction stocks with Kelly-optimal sizing")
    print("• Satellite positions: High-reward options for leverage")
    print("• Cash buffer: For opportunities and risk management")
    print("• Rebalance: Monthly based on updated Kelly calculations")
    print("• Risk management: Position limits and stop-losses")
    print("• Monitoring: Track drawdowns and adjust scaling factors")

    # AUTOMATIC REDDIT POSTING
    print(f"\n📱 AUTOMATIC REDDIT POSTING")
    print("=" * 50)
    
    # Collect all options found
    all_options_found = []
    if all_options:
        all_options_found.extend(all_options)
    if penny_options:
        all_options_found.extend(penny_options)
    if ultra_options:
        all_options_found.extend(ultra_options)
    
    # Automatically post to Reddit with Kelly allocation data
    post_results_to_reddit(results_df, all_options_found, portfolio_allocation, confidence_portfolio_allocation)

if __name__ == "__main__":
    main()
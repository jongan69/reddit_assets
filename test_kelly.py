#!/usr/bin/env python3
"""
Test script for Kelly Criterion portfolio allocation
Demonstrates how to use the Kelly Criterion for a $1000 portfolio
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import (
    calculate_kelly_fraction,
    estimate_stock_probabilities,
    calculate_portfolio_allocation,
    calculate_risk_metrics,
    display_kelly_portfolio_allocation
)

def test_kelly_basics():
    """Test basic Kelly Criterion calculations"""
    print("🧮 TESTING KELLY CRITERION BASICS")
    print("=" * 50)
    
    # Test case 1: Good bet
    p1, g1, l1 = 0.6, 0.2, 0.1  # 60% win rate, 20% gain, 10% loss
    kelly1 = calculate_kelly_fraction(p1, g1, l1)
    print(f"Test 1 - Good bet: p={p1}, g={g1}, l={l1}")
    print(f"Kelly fraction: {kelly1:.1%}")
    print(f"Expected value: {p1*g1 - (1-p1)*l1:.1%}")
    print()
    
    # Test case 2: Bad bet
    p2, g2, l2 = 0.4, 0.1, 0.2  # 40% win rate, 10% gain, 20% loss
    kelly2 = calculate_kelly_fraction(p2, g2, l2)
    print(f"Test 2 - Bad bet: p={p2}, g={g2}, l={l2}")
    print(f"Kelly fraction: {kelly2:.1%}")
    print(f"Expected value: {p2*g2 - (1-p2)*l2:.1%}")
    print()
    
    # Test case 3: Coin flip with edge
    p3, g3, l3 = 0.55, 1.0, 1.0  # 55% win rate, 1:1 odds
    kelly3 = calculate_kelly_fraction(p3, g3, l3)
    print(f"Test 3 - Coin flip with edge: p={p3}, g={g3}, l={l3}")
    print(f"Kelly fraction: {kelly3:.1%}")
    print(f"Expected value: {p3*g3 - (1-p3)*l3:.1%}")
    print()

def test_stock_analysis():
    """Test stock probability estimation"""
    print("📊 TESTING STOCK PROBABILITY ESTIMATION")
    print("=" * 50)
    
    # Test with a well-known stock
    test_tickers = ['AAPL', 'TSLA', 'NVDA']
    
    for ticker in test_tickers:
        print(f"\nAnalyzing {ticker}...")
        try:
            kelly_data = estimate_stock_probabilities(ticker, lookback_days=252)
            
            if kelly_data:
                print(f"  Win Probability: {kelly_data['win_probability']:.1%}")
                print(f"  Average Gain: {kelly_data['avg_gain']:.1%}")
                print(f"  Average Loss: {kelly_data['avg_loss']:.1%}")
                print(f"  Kelly Fraction: {kelly_data['kelly_fraction']:.1%}")
                print(f"  Volatility: {kelly_data['volatility']:.1%}")
                print(f"  Sharpe Ratio: {kelly_data['sharpe_ratio']:.2f}")
                print(f"  Total Return: {kelly_data['total_return']:.1%}")
                print(f"  Max Drawdown: {kelly_data['max_drawdown']:.1%}")
            else:
                print(f"  Could not analyze {ticker}")
                
        except Exception as e:
            print(f"  Error analyzing {ticker}: {e}")

def test_portfolio_allocation():
    """Test portfolio allocation with sample data"""
    print("\n🎯 TESTING PORTFOLIO ALLOCATION")
    print("=" * 50)
    
    # Sample stock data
    sample_stocks = [
        {
            'Ticker': 'AAPL',
            'Current_Price': 150.0,
            'Doubling_Score': 75,
            'Reasons': 'Strong fundamentals, high growth'
        },
        {
            'Ticker': 'TSLA',
            'Current_Price': 250.0,
            'Doubling_Score': 85,
            'Reasons': 'High volatility, growth potential'
        },
        {
            'Ticker': 'NVDA',
            'Current_Price': 400.0,
            'Doubling_Score': 90,
            'Reasons': 'AI leader, strong momentum'
        }
    ]
    
    print("Calculating Kelly allocation for $1000 portfolio...")
    print("Note: This will take time to fetch historical data for each stock.")
    
    try:
        portfolio_allocation = calculate_portfolio_allocation(
            sample_stocks, 
            portfolio_value=1000, 
            scaling_factor=0.5
        )
        
        risk_metrics = calculate_risk_metrics(portfolio_allocation)
        
        display_kelly_portfolio_allocation(portfolio_allocation, risk_metrics, 1000)
        
    except Exception as e:
        print(f"Error in portfolio allocation: {e}")

def main():
    """Main test function"""
    print("🚀 KELLY CRITERION PORTFOLIO ALLOCATION TEST")
    print("=" * 60)
    print("This script demonstrates Kelly Criterion calculations for portfolio allocation")
    print()
    
    # Test basic Kelly calculations
    test_kelly_basics()
    
    # Test stock analysis (commented out to avoid API calls during testing)
    # test_stock_analysis()
    
    # Test portfolio allocation (commented out to avoid API calls during testing)
    # test_portfolio_allocation()
    
    print("\n✅ TEST COMPLETED")
    print("\n💡 KEY INSIGHTS:")
    print("• Kelly Criterion maximizes long-term geometric growth")
    print("• Full Kelly can be volatile - consider scaling down")
    print("• Half-Kelly (50%) provides ~90% of growth with half the volatility")
    print("• Always estimate probabilities conservatively")
    print("• Recalculate Kelly fractions regularly as probabilities change")

if __name__ == "__main__":
    main() 
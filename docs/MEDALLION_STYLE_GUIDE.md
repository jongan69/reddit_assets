# Medallion-Style Unified Risk-Reward Metric Guide

## Overview

This guide explains the implementation of a Medallion-inspired unified risk-reward metric that combines Kelly Criterion, Sortino Ratio, and Calmar Ratio principles for optimal portfolio allocation. This approach is inspired by the exceptional performance of the Medallion Fund and applies quantitative finance principles to penny stock investing.

## Why Medallion-Style Approach?

### Medallion Fund Success Principles

The Medallion Fund, with average annual returns exceeding 66% before fees, demonstrates several key principles:

1. **Position sizing optimized probabilistically** (Kelly-like)
2. **Short holding periods with asymmetric risk** (Sortino-like)
3. **Aggressive drawdown control and capital preservation** (Calmar-like)
4. **Scientific, probabilistic, and risk-managed framework**

### Benefits of Unified Approach

1. **Comprehensive Risk Assessment**: Combines multiple risk metrics
2. **Optimal Position Sizing**: Kelly Criterion for growth optimization
3. **Downside Protection**: Sortino Ratio focuses on negative volatility
4. **Drawdown Control**: Calmar Ratio emphasizes capital preservation
5. **Short-term Focus**: Designed for active trading strategies

## Mathematical Foundation

### 1. Kelly Criterion (40% Weight)

**Formula**: `f* = (bp - q) / b`

Where:
- `f*` = optimal fraction of capital to allocate
- `p` = probability of winning
- `q` = probability of losing (1 - p)
- `g` = fractional gain if you win
- `ℓ` = fractional loss if you lose
- `b` = net odds (g/ℓ)

### 2. Sortino Ratio (30% Weight)

**Formula**: `Sortino = (R_p - R_f) / σ_D`

Where:
- `R_p` = portfolio return
- `R_f` = risk-free rate
- `σ_D` = downside deviation (only negative returns)

### 3. Calmar Ratio (30% Weight)

**Formula**: `Calmar = CAGR / Max Drawdown`

Where:
- `CAGR` = Compound Annual Growth Rate
- `Max Drawdown` = Maximum observed portfolio loss from peak to trough

### 4. Unified Risk-Reward Score

**Formula**: `Unified Score = 0.4 × Kelly_Score + 0.3 × Sortino_Score + 0.3 × Calmar_Score`

Where each component is normalized to 0-1 scale.

## Implementation Features

### 1. Sortino Ratio Calculation

```python
def calculate_sortino_ratio(returns, target_return=0.0, risk_free_rate=0.05):
    """
    Calculate Sortino Ratio focusing on downside volatility only
    """
    # Convert annual risk-free rate to daily
    daily_rf = (1 + risk_free_rate) ** (1/252) - 1
    
    # Calculate excess returns
    excess_returns = returns - daily_rf
    
    # Calculate downside deviation (only negative returns)
    downside_returns = np.minimum(excess_returns - target_return, 0)
    downside_deviation = np.sqrt(np.mean(downside_returns ** 2))
    
    # Calculate average excess return
    avg_excess_return = np.mean(excess_returns)
    
    # Sortino ratio
    if downside_deviation > 0:
        sortino_ratio = avg_excess_return / downside_deviation
    else:
        sortino_ratio = 0
        
    return sortino_ratio
```

### 2. Calmar Ratio Calculation

```python
def calculate_calmar_ratio(returns, lookback_days=252):
    """
    Calculate Calmar Ratio (CAGR / Max Drawdown)
    """
    # Calculate cumulative returns
    cumulative_returns = (1 + returns).cumprod()
    
    # Calculate CAGR
    total_return = cumulative_returns.iloc[-1] - 1
    years = lookback_days / 252
    cagr = (1 + total_return) ** (1/years) - 1 if years > 0 else 0
    
    # Calculate maximum drawdown
    rolling_max = cumulative_returns.expanding().max()
    drawdown = (cumulative_returns - rolling_max) / rolling_max
    max_drawdown = abs(drawdown.min())
    
    # Calmar ratio
    if max_drawdown > 0:
        calmar_ratio = cagr / max_drawdown
    else:
        calmar_ratio = 0
        
    return calmar_ratio
```

### 3. Unified Risk-Reward Metric

```python
def calculate_unified_risk_reward_metric(ticker, lookback_days=252, risk_free_rate=0.05):
    """
    Calculate unified risk-reward metric combining Kelly, Sortino, and Calmar principles
    """
    # Get historical data
    yft = yf.Ticker(ticker)
    hist = yft.history(period=f'{lookback_days}d')
    returns = hist['Close'].pct_change().dropna()
    
    # Calculate Kelly Criterion
    kelly_data = estimate_stock_probabilities_with_confidence(ticker, lookback_days)
    
    # Calculate Sortino Ratio
    sortino_ratio = calculate_sortino_ratio(returns, 0.0, risk_free_rate)
    
    # Calculate Calmar Ratio
    calmar_ratio = calculate_calmar_ratio(returns, lookback_days)
    
    # Unified Risk-Reward Score (Medallion-inspired)
    kelly_weight = 0.4  # Position sizing importance
    sortino_weight = 0.3  # Downside risk importance
    calmar_weight = 0.3  # Drawdown control importance
    
    # Normalize ratios to 0-1 scale
    kelly_score = min(1.0, max(0.0, kelly_data['kelly_results']['confidence_weighted_kelly'] * 10))
    sortino_score = min(1.0, max(0.0, sortino_ratio / 2))  # Normalize to 0-2 range
    calmar_score = min(1.0, max(0.0, calmar_ratio / 3))    # Normalize to 0-3 range
    
    # Calculate unified score
    unified_score = (kelly_weight * kelly_score + 
                    sortino_weight * sortino_score + 
                    calmar_weight * calmar_score)
    
    # Risk-adjusted Kelly allocation
    risk_adjusted_kelly = kelly_data['kelly_results']['confidence_weighted_kelly'] * unified_score
    
    return {
        'ticker': ticker,
        'unified_score': unified_score,
        'kelly_score': kelly_score,
        'sortino_score': sortino_score,
        'calmar_score': calmar_score,
        'kelly_ratio': kelly_data['kelly_results']['confidence_weighted_kelly'],
        'sortino_ratio': sortino_ratio,
        'calmar_ratio': calmar_ratio,
        'risk_adjusted_kelly': risk_adjusted_kelly,
        # ... other metrics
    }
```

### 4. Medallion-Style Portfolio Allocation

```python
def calculate_medallion_style_portfolio_allocation(stocks_data, portfolio_value=1000, 
                                                 scaling_factor=0.5, risk_aversion=1.0):
    """
    Calculate portfolio allocation using Medallion-inspired unified risk-reward metric
    """
    allocations = []
    total_allocation = 0
    
    for stock in stocks_data:
        ticker = stock['Ticker']
        
        # Calculate unified risk-reward metric
        unified_data = calculate_unified_risk_reward_metric(ticker)
        
        if unified_data and unified_data['unified_score'] > 0.1:  # Minimum threshold
            # Use risk-adjusted Kelly for allocation
            risk_adjusted_kelly = unified_data['risk_adjusted_kelly']
            
            # Apply scaling and risk aversion
            scaled_kelly = calculate_scaled_kelly(risk_adjusted_kelly, scaling_factor)
            
            # Calculate dollar allocation
            dollar_allocation = scaled_kelly * portfolio_value
            
            # Position limits based on unified score
            max_allocation = portfolio_value * (0.20 * unified_data['unified_score'])
            dollar_allocation = min(dollar_allocation, max_allocation)
            
            # Minimum allocation based on unified score
            min_allocation = 10 * unified_data['unified_score']
            if dollar_allocation > min_allocation:
                allocations.append({
                    'ticker': ticker,
                    'unified_score': unified_data['unified_score'],
                    'kelly_score': unified_data['kelly_score'],
                    'sortino_score': unified_data['sortino_score'],
                    'calmar_score': unified_data['calmar_score'],
                    'risk_adjusted_kelly': risk_adjusted_kelly,
                    'scaled_kelly': scaled_kelly,
                    'dollar_allocation': dollar_allocation,
                    # ... other allocation data
                })
                
                total_allocation += dollar_allocation
    
    # Sort by unified score (highest first)
    allocations.sort(key=lambda x: x['unified_score'], reverse=True)
    
    return {
        'allocations': allocations,
        'total_allocated': total_allocation,
        'cash_remaining': portfolio_value - total_allocation,
        'allocation_percentage': (total_allocation / portfolio_value) * 100
    }
```

## Usage Examples

### Basic Unified Metric Calculation

```python
from main import calculate_unified_risk_reward_metric

# Calculate unified metric for a stock
unified_data = calculate_unified_risk_reward_metric('AAPL')

if unified_data:
    print(f"Unified Score: {unified_data['unified_score']:.1%}")
    print(f"Kelly Score: {unified_data['kelly_score']:.1%}")
    print(f"Sortino Score: {unified_data['sortino_score']:.1%}")
    print(f"Calmar Score: {unified_data['calmar_score']:.1%}")
    print(f"Risk-Adjusted Kelly: {unified_data['risk_adjusted_kelly']:.1%}")
```

### Medallion-Style Portfolio Allocation

```python
from main import calculate_medallion_style_portfolio_allocation, display_medallion_style_allocation

# Your screened stocks
stocks_data = [
    {'Ticker': 'AAPL', 'Current_Price': 150.0, 'Doubling_Score': 75, 'Reasons': 'Strong fundamentals'},
    {'Ticker': 'TSLA', 'Current_Price': 250.0, 'Doubling_Score': 85, 'Reasons': 'High growth potential'},
    # ... more stocks
]

# Calculate Medallion-style allocation
medallion_allocation = calculate_medallion_style_portfolio_allocation(
    stocks_data,
    portfolio_value=1000,
    scaling_factor=0.5,
    risk_aversion=1.0
)

# Display results
display_medallion_style_allocation(medallion_allocation, 1000)
```

### Comparing All Approaches

```python
from main import (
    calculate_portfolio_allocation,
    calculate_confidence_weighted_portfolio_allocation,
    calculate_medallion_style_portfolio_allocation
)

# Standard Kelly
standard_allocation = calculate_portfolio_allocation(stocks_data, 1000, 0.5)

# Confidence-weighted Kelly
confidence_allocation = calculate_confidence_weighted_portfolio_allocation(stocks_data, 1000, 0.5, 1.0)

# Medallion-style
medallion_allocation = calculate_medallion_style_portfolio_allocation(stocks_data, 1000, 0.5, 1.0)

# Compare results
print(f"Standard Kelly: ${standard_allocation['total_allocated']:.0f}")
print(f"Confidence-Weighted: ${confidence_allocation['total_allocated']:.0f}")
print(f"Medallion-Style: ${medallion_allocation['total_allocated']:.0f}")
```

## Integration with Your Screener

The Medallion-style analysis is integrated into your main screener:

1. **Standard Kelly Analysis**: Traditional Kelly allocations
2. **Confidence-Weighted Analysis**: Kelly with uncertainty adjustments
3. **Medallion-Style Analysis**: Unified risk-reward approach
4. **Comprehensive Comparison**: Side-by-side comparison of all approaches

### Running the Enhanced Screener

```bash
python main.py
```

This will now include:
- Standard Kelly Criterion allocation
- Confidence-weighted Kelly allocation
- Medallion-style unified risk-reward allocation
- Comprehensive comparison of all approaches
- Risk metrics and insights

## Key Insights

### 1. Medallion-Style Principles

- **Kelly Criterion (40%)**: Optimal position sizing for growth
- **Sortino Ratio (30%)**: Focus on downside risk only
- **Calmar Ratio (30%)**: Drawdown control and capital preservation
- **Unified Score**: Combines all three metrics for optimal allocation
- **Risk-Adjusted Kelly**: Kelly allocation weighted by unified score

### 2. Practical Considerations

- **Short-term focus**: Designed for active trading strategies
- **Risk management**: Emphasizes downside protection
- **Position sizing**: Optimized for growth while controlling risk
- **Drawdown control**: Prioritizes capital preservation

### 3. Advantages Over Standard Kelly

- **More comprehensive risk assessment**
- **Better downside protection**
- **Drawdown-aware allocation**
- **Short-term trading optimization**
- **Medallion-inspired methodology**

## Risk Management Strategies

### 1. Unified Score Thresholds

```python
# Minimum thresholds for allocation
MIN_UNIFIED_SCORE = 0.1  # 10% minimum unified score
MIN_KELLY_SCORE = 0.05   # 5% minimum Kelly score
MIN_SORTINO_SCORE = 0.1  # 10% minimum Sortino score
MIN_CALMAR_SCORE = 0.1   # 10% minimum Calmar score
```

### 2. Position Limits Based on Unified Score

```python
# Position limits based on unified score
def calculate_position_limit(unified_score, base_limit=0.20):
    return base_limit * unified_score

# Example: Higher unified score = higher position limit
position_limit = calculate_position_limit(0.8)  # 16% limit for 80% unified score
```

### 3. Dynamic Rebalancing

```python
# Rebalance when unified score changes significantly
def should_rebalance(old_unified_score, new_unified_score, threshold=0.1):
    return abs(new_unified_score - old_unified_score) > threshold
```

## Monitoring and Maintenance

### 1. Monthly Tasks

- Recalculate unified risk-reward metrics for all positions
- Update Kelly, Sortino, and Calmar ratios
- Adjust position sizes based on new unified scores
- Review and adjust thresholds

### 2. Quarterly Tasks

- Analyze performance vs. unified score predictions
- Adjust weighting factors if needed
- Review risk management parameters
- Update position limits

### 3. Annual Tasks

- Comprehensive methodology review
- Update normalization factors
- Review and adjust risk aversion parameters
- Plan unified allocation strategy

## Conclusion

The Medallion-style unified risk-reward metric provides a sophisticated approach to portfolio allocation that combines the best principles from Kelly Criterion, Sortino Ratio, and Calmar Ratio. This approach is particularly valuable for penny stock investing where risk management is crucial.

Key benefits:
- **Comprehensive risk assessment** combining multiple metrics
- **Optimal position sizing** with Kelly Criterion principles
- **Downside protection** with Sortino Ratio focus
- **Drawdown control** with Calmar Ratio emphasis
- **Short-term optimization** for active trading strategies
- **Medallion-inspired methodology** based on proven success

This implementation gives you a powerful tool for optimal portfolio allocation that balances growth optimization with comprehensive risk management, making it ideal for penny stock investing where both opportunity and risk are high. 
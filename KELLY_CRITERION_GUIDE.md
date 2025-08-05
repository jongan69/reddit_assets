# Kelly Criterion Portfolio Allocation Guide

## Overview

This guide explains how to use the Kelly Criterion for optimal portfolio allocation in your penny stock screener. The Kelly Criterion is a mathematical formula that determines the optimal fraction of capital to allocate to each investment to maximize long-term geometric growth.

## What is the Kelly Criterion?

The Kelly Criterion formula is:

**f* = (bp - q) / b**

Where:
- **f*** = optimal fraction of capital to allocate
- **p** = probability of winning
- **q** = probability of losing (1 - p)
- **g** = fractional gain if you win
- **ℓ** = fractional loss if you lose
- **b** = net odds (g/ℓ)

## Key Benefits

1. **Maximizes Long-term Growth**: Kelly Criterion maximizes the geometric growth rate of your portfolio
2. **Prevents Bankruptcy**: Always leaves some capital untouched, preventing complete loss
3. **Scale Invariant**: Works for any portfolio size
4. **Mathematically Optimal**: Based on rigorous mathematical principles

## Implementation Features

### 1. Stock Allocation Functions

#### `calculate_kelly_fraction(p, g, l)`
Calculates the Kelly fraction for a single asset.

```python
# Example: 60% win rate, 20% gain, 10% loss
kelly_fraction = calculate_kelly_fraction(0.6, 0.2, 0.1)
print(f"Kelly fraction: {kelly_fraction:.1%}")
```

#### `estimate_stock_probabilities(ticker, lookback_days=252)`
Estimates win probability and gain/loss parameters for a stock using historical data.

```python
kelly_data = estimate_stock_probabilities('AAPL')
print(f"Win probability: {kelly_data['win_probability']:.1%}")
print(f"Kelly fraction: {kelly_data['kelly_fraction']:.1%}")
```

#### `calculate_portfolio_allocation(stocks_data, portfolio_value=1000, scaling_factor=0.5)`
Calculates optimal portfolio allocation for multiple stocks.

```python
portfolio_allocation = calculate_portfolio_allocation(
    stocks_data, 
    portfolio_value=1000, 
    scaling_factor=0.5  # Half-Kelly
)
```

### 2. Options Allocation Functions

#### `calculate_options_kelly_allocation(options_data, portfolio_value=1000, scaling_factor=0.25)`
Calculates Kelly allocation for options (more conservative due to higher risk).

```python
options_allocation = calculate_options_kelly_allocation(
    options_data, 
    portfolio_value=1000, 
    scaling_factor=0.25  # Quarter-Kelly for options
)
```

### 3. Risk Management Functions

#### `calculate_scaled_kelly(kelly_fraction, scaling_factor=0.5)`
Applies scaling to reduce volatility.

```python
scaled_kelly = calculate_scaled_kelly(0.1, 0.5)  # Half-Kelly
```

#### `calculate_risk_metrics(portfolio_allocation)`
Calculates portfolio-level risk metrics.

```python
risk_metrics = calculate_risk_metrics(portfolio_allocation)
print(f"Expected return: {risk_metrics['expected_return']:.2%}")
print(f"Portfolio volatility: {risk_metrics['portfolio_volatility']:.2%}")
```

## Usage Examples

### Basic Kelly Calculation

```python
from main import calculate_kelly_fraction

# Good bet: 60% win rate, 20% gain, 10% loss
kelly = calculate_kelly_fraction(0.6, 0.2, 0.1)
print(f"Allocate {kelly:.1%} of your capital")
```

### Stock Portfolio Allocation

```python
from main import calculate_portfolio_allocation, display_kelly_portfolio_allocation

# Your screened stocks data
stocks_data = [
    {'Ticker': 'AAPL', 'Current_Price': 150.0, 'Doubling_Score': 75, 'Reasons': 'Strong fundamentals'},
    {'Ticker': 'TSLA', 'Current_Price': 250.0, 'Doubling_Score': 85, 'Reasons': 'High growth potential'},
    # ... more stocks
]

# Calculate allocation for $1000 portfolio
portfolio_allocation = calculate_portfolio_allocation(
    stocks_data, 
    portfolio_value=1000, 
    scaling_factor=0.5  # Half-Kelly
)

# Display results
display_kelly_portfolio_allocation(portfolio_allocation, risk_metrics, 1000)
```

### Options Portfolio Allocation

```python
from main import calculate_options_kelly_allocation, display_options_kelly_allocation

# Your options data
options_data = [
    {
        'ticker': 'AAPL',
        'strike': 160.0,
        'ask': 5.0,
        'expiry': '2024-01-19',
        'current_price': 150.0,
        'return_25': 2.0,  # 200% return if stock moves 25%
        # ... more data
    }
]

# Calculate options allocation
options_allocation = calculate_options_kelly_allocation(
    options_data, 
    portfolio_value=1000, 
    scaling_factor=0.25  # Quarter-Kelly for options
)

# Display results
display_options_kelly_allocation(options_allocation, 1000)
```

## Risk Management Strategies

### 1. Kelly Scaling

**Full Kelly (100%)**: Maximum growth but high volatility
**Half-Kelly (50%)**: ~90% of growth with half the volatility
**Quarter-Kelly (25%)**: Conservative but still growth-optimal

```python
# Conservative approach
scaled_kelly = calculate_scaled_kelly(kelly_fraction, 0.5)  # Half-Kelly
```

### 2. Position Limits

- **Stocks**: Maximum 20% allocation per position
- **Options**: Maximum 5% allocation per position
- **Minimum allocation**: $10 for stocks, $5 for options

### 3. Portfolio Constraints

```python
# Example constraints
max_stock_allocation = portfolio_value * 0.20  # 20% max per stock
max_options_allocation = portfolio_value * 0.05  # 5% max per option
min_allocation = 10  # $10 minimum
```

## Integration with Your Screener

The Kelly Criterion functionality is integrated into your main screener:

1. **Stock Analysis**: After finding top candidates, calculates Kelly allocations
2. **Options Analysis**: Applies Kelly to options opportunities
3. **Combined Portfolio**: Shows total allocation across stocks and options
4. **Risk Metrics**: Provides portfolio-level risk analysis

### Running the Enhanced Screener

```bash
python main.py
```

This will now include:
- Kelly Criterion stock allocation
- Kelly Criterion options allocation
- Combined portfolio summary
- Risk metrics and recommendations

## Testing the Kelly Functionality

Run the test script to see Kelly calculations in action:

```bash
python test_kelly.py
```

This demonstrates:
- Basic Kelly calculations
- Stock probability estimation
- Portfolio allocation examples

## Key Insights

### 1. Kelly Criterion Principles

- **Maximizes geometric growth**: Not just expected return
- **Prevents ruin**: Always preserves some capital
- **Scale invariant**: Works for any portfolio size
- **Requires accurate probabilities**: Garbage in, garbage out

### 2. Practical Considerations

- **Estimate conservatively**: Bias probabilities downward
- **Scale appropriately**: Use fractional Kelly for reduced volatility
- **Rebalance regularly**: Update Kelly fractions monthly
- **Monitor drawdowns**: Adjust scaling if needed

### 3. Common Mistakes to Avoid

- **Overestimating edge**: Be conservative with probability estimates
- **Using full Kelly**: Usually too volatile for most investors
- **Ignoring correlations**: Consider portfolio effects
- **Not rebalancing**: Kelly fractions change over time

## Advanced Features

### 1. Multi-Asset Kelly

For portfolios with multiple assets, use the portfolio version:

```python
from main import calculate_portfolio_kelly

# Returns matrix with assets as columns
returns_matrix = pd.DataFrame(...)
kelly_weights = calculate_portfolio_kelly(returns_matrix)
```

### 2. Dynamic Rebalancing

```python
# Recalculate monthly
monthly_kelly = calculate_portfolio_allocation(
    updated_stocks_data, 
    portfolio_value=current_portfolio_value, 
    scaling_factor=0.5
)
```

### 3. Risk-Adjusted Kelly

```python
# Adjust Kelly based on risk tolerance
risk_tolerance = 0.5  # Conservative
scaling_factor = risk_tolerance * 0.5  # Quarter-Kelly for very conservative
```

## Monitoring and Maintenance

### 1. Monthly Tasks

- Recalculate Kelly fractions for all positions
- Update probability estimates based on new data
- Adjust scaling factors if drawdowns are too high
- Review position limits and constraints

### 2. Quarterly Tasks

- Review overall portfolio performance
- Analyze Kelly vs. actual performance
- Adjust risk management parameters
- Consider new opportunities

### 3. Annual Tasks

- Comprehensive portfolio review
- Update Kelly methodology if needed
- Review and adjust scaling factors
- Plan for next year's allocation strategy

## Conclusion

The Kelly Criterion provides a mathematically sound approach to portfolio allocation that maximizes long-term growth while managing risk. By integrating it into your penny stock screener, you can make more informed allocation decisions for your $1000 portfolio.

Remember:
- **Start conservative**: Use fractional Kelly (25-50%)
- **Estimate carefully**: Be conservative with probability estimates
- **Monitor closely**: Track performance and adjust as needed
- **Stay disciplined**: Follow the Kelly allocations consistently

This implementation gives you a powerful tool for optimal portfolio allocation while maintaining the high-reward focus of your penny stock screener. 
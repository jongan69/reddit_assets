# Confidence-Weighted Kelly Criterion Guide

## Overview

The Confidence-Weighted Kelly Criterion is an advanced enhancement to the standard Kelly Criterion that incorporates uncertainty in probability estimates to provide more robust position sizing. This approach dynamically adjusts position sizes based on your confidence in the underlying probability estimates.

## Why Confidence-Weighted Kelly?

### Problems with Standard Kelly Criterion

1. **Assumes Perfect Knowledge**: Standard Kelly assumes you know the true probabilities with certainty
2. **Overconfidence Risk**: Can lead to oversized positions when estimates are uncertain
3. **Sample Size Ignorance**: Doesn't account for the amount of data used to estimate probabilities
4. **No Uncertainty Bounds**: Provides no guidance on how uncertain your estimates are

### Benefits of Confidence-Weighted Kelly

1. **Dynamic Position Sizing**: Larger positions when confident, smaller when uncertain
2. **Sample Size Awareness**: More data = higher confidence = larger positions
3. **Risk Aversion Integration**: Built-in conservative adjustments
4. **Uncertainty Quantification**: Provides confidence intervals and bounds
5. **Robust Performance**: Better handles estimation errors and market changes

## Mathematical Foundation

### Confidence Interval Calculation

For a win probability estimate based on historical data:

**Confidence Interval**: `p̂ ± z * √(p̂(1-p̂)/n)`

Where:
- `p̂` = sample proportion (win rate)
- `z` = z-score for desired confidence level
- `n` = sample size

### Confidence-Weighted Kelly Formula

**Confidence-Weighted Kelly**: `f*_cw = f*_base × confidence_factor × risk_adjustment`

Where:
- `f*_base` = standard Kelly fraction
- `confidence_factor` = average confidence across all estimates
- `risk_adjustment` = 1/(1 + risk_aversion × (1 - confidence_factor))

## Implementation Features

### 1. Confidence Interval Functions

#### `calculate_confidence_interval(returns, confidence_level=0.95)`
Calculates confidence intervals for probability estimates.

```python
# Example usage
returns = stock_returns  # Array of historical returns
confidence_data = calculate_confidence_interval(returns, 0.95)
print(f"Point estimate: {confidence_data['point_estimate']:.3f}")
print(f"Confidence interval: [{confidence_data['lower_bound']:.3f}, {confidence_data['upper_bound']:.3f}]")
print(f"Sample confidence: {confidence_data['sample_confidence']:.1%}")
```

#### `calculate_confidence_weighted_kelly(p_estimate, g_estimate, l_estimate, p_confidence, g_confidence, l_confidence, risk_aversion=1.0)`
Calculates Kelly fraction weighted by confidence in estimates.

```python
# Example usage
kelly_results = calculate_confidence_weighted_kelly(
    p_estimate=0.6,      # 60% win probability
    g_estimate=0.2,      # 20% average gain
    l_estimate=0.1,      # 10% average loss
    p_confidence=0.8,    # 80% confident in probability
    g_confidence=0.7,    # 70% confident in gain
    l_confidence=0.6,    # 60% confident in loss
    risk_aversion=1.0    # Moderate risk aversion
)

print(f"Base Kelly: {kelly_results['base_kelly']:.1%}")
print(f"Confidence-weighted Kelly: {kelly_results['confidence_weighted_kelly']:.1%}")
print(f"Confidence factor: {kelly_results['confidence_factor']:.1%}")
```

### 2. Stock Analysis with Confidence

#### `estimate_stock_probabilities_with_confidence(ticker, lookback_days=252, confidence_level=0.95)`
Estimates stock probabilities with confidence intervals and uncertainty quantification.

```python
# Example usage
kelly_data = estimate_stock_probabilities_with_confidence('AAPL', 252, 0.95)

if kelly_data:
    print(f"Win probability: {kelly_data['win_probability']:.1%}")
    print(f"Confidence: {kelly_data['win_probability_confidence']:.1%}")
    print(f"Confidence interval: {kelly_data['win_probability_ci']}")
    print(f"Sample size: {kelly_data['sample_size']} days")
    print(f"Confidence-weighted Kelly: {kelly_data['kelly_results']['confidence_weighted_kelly']:.1%}")
```

### 3. Portfolio Allocation with Confidence

#### `calculate_confidence_weighted_portfolio_allocation(stocks_data, portfolio_value=1000, scaling_factor=0.5, risk_aversion=1.0)`
Calculates portfolio allocation using confidence-weighted Kelly Criterion.

```python
# Example usage
confidence_allocation = calculate_confidence_weighted_portfolio_allocation(
    stocks_data,           # List of stock analysis dictionaries
    portfolio_value=1000,  # $1000 portfolio
    scaling_factor=0.5,    # Half-Kelly scaling
    risk_aversion=1.0      # Moderate risk aversion
)

print(f"Total allocated: ${confidence_allocation['total_allocated']:.2f}")
print(f"Number of positions: {len(confidence_allocation['allocations'])}")
```

## Confidence Factors and Their Impact

### 1. Sample Size Impact

| Sample Size | Confidence Level | Impact on Position Size |
|-------------|------------------|------------------------|
| 30 days     | ~50%            | Very small positions   |
| 60 days     | ~60%            | Small positions        |
| 125 days    | ~70%            | Medium positions       |
| 252 days    | ~80%            | Large positions        |
| 500+ days   | ~90%            | Full positions         |

### 2. Risk Aversion Levels

| Risk Aversion | Description | Position Size Impact |
|---------------|-------------|---------------------|
| 0.5           | Aggressive  | 20% larger          |
| 1.0           | Moderate    | Standard            |
| 1.5           | Conservative | 20% smaller         |
| 2.0           | Very Conservative | 40% smaller    |
| 3.0           | Ultra Conservative | 60% smaller   |

### 3. Confidence Factor Calculation

**Confidence Factor**: `(p_confidence + g_confidence + l_confidence) / 3`

This creates a weighted average of confidence across all estimates.

## Usage Examples

### Basic Confidence-Weighted Kelly

```python
from main import calculate_confidence_weighted_kelly

# High confidence scenario
high_conf = calculate_confidence_weighted_kelly(
    0.6, 0.2, 0.1,  # p, g, l
    0.9, 0.85, 0.8, # confidences
    1.0              # risk aversion
)

# Low confidence scenario
low_conf = calculate_confidence_weighted_kelly(
    0.6, 0.2, 0.1,  # p, g, l
    0.5, 0.45, 0.4, # confidences
    1.0              # risk aversion
)

print(f"High confidence Kelly: {high_conf['confidence_weighted_kelly']:.1%}")
print(f"Low confidence Kelly: {low_conf['confidence_weighted_kelly']:.1%}")
```

### Portfolio Allocation with Confidence

```python
from main import calculate_confidence_weighted_portfolio_allocation, display_confidence_weighted_allocation

# Your screened stocks
stocks_data = [
    {'Ticker': 'AAPL', 'Current_Price': 150.0, 'Doubling_Score': 75, 'Reasons': 'Strong fundamentals'},
    {'Ticker': 'TSLA', 'Current_Price': 250.0, 'Doubling_Score': 85, 'Reasons': 'High growth potential'},
    # ... more stocks
]

# Calculate confidence-weighted allocation
confidence_allocation = calculate_confidence_weighted_portfolio_allocation(
    stocks_data,
    portfolio_value=1000,
    scaling_factor=0.5,
    risk_aversion=1.0
)

# Display results
display_confidence_weighted_allocation(confidence_allocation, 1000)
```

### Comparing Standard vs Confidence-Weighted

```python
from main import calculate_portfolio_allocation, calculate_confidence_weighted_portfolio_allocation

# Standard Kelly
standard_allocation = calculate_portfolio_allocation(stocks_data, 1000, 0.5)

# Confidence-weighted Kelly
confidence_allocation = calculate_confidence_weighted_portfolio_allocation(stocks_data, 1000, 0.5, 1.0)

# Compare results
print(f"Standard Kelly: ${standard_allocation['total_allocated']:.0f} allocated")
print(f"Confidence-weighted: ${confidence_allocation['total_allocated']:.0f} allocated")
print(f"Difference: ${confidence_allocation['total_allocated'] - standard_allocation['total_allocated']:+.0f}")
```

## Integration with Your Screener

The confidence-weighted Kelly Criterion is integrated into your main screener:

1. **Standard Kelly Analysis**: Shows traditional Kelly allocations
2. **Confidence-Weighted Analysis**: Shows confidence-adjusted allocations
3. **Comparison**: Side-by-side comparison of both approaches
4. **Risk Metrics**: Portfolio-level risk analysis with confidence

### Running the Enhanced Screener

```bash
python main.py
```

This will now include:
- Standard Kelly Criterion allocation
- Confidence-weighted Kelly Criterion allocation
- Comparison between the two approaches
- Confidence statistics and risk metrics

## Testing the Confidence-Weighted Functionality

Run the test script to see confidence-weighted calculations:

```bash
python test_confidence_kelly.py
```

This demonstrates:
- Confidence interval calculations
- Confidence-weighted Kelly calculations
- Risk aversion impact
- Sample size impact on confidence
- Portfolio allocation comparisons

## Advanced Features

### 1. Dynamic Confidence Adjustment

```python
# Adjust confidence based on market conditions
def adjust_confidence_for_market_conditions(base_confidence, market_volatility):
    if market_volatility > 0.3:  # High volatility
        return base_confidence * 0.8  # Reduce confidence
    elif market_volatility < 0.1:  # Low volatility
        return base_confidence * 1.1  # Increase confidence
    else:
        return base_confidence
```

### 2. Time-Varying Confidence

```python
# Confidence decreases over time as estimates become stale
def time_decay_confidence(base_confidence, days_since_update):
    decay_factor = np.exp(-days_since_update / 30)  # 30-day half-life
    return base_confidence * decay_factor
```

### 3. Sector-Specific Confidence

```python
# Different confidence levels for different sectors
sector_confidence = {
    'Technology': 0.8,    # High confidence
    'Healthcare': 0.6,    # Medium confidence
    'Energy': 0.4,        # Low confidence
    'Finance': 0.7        # Medium-high confidence
}
```

## Risk Management Strategies

### 1. Confidence-Based Position Limits

```python
# Position limits based on confidence
def calculate_position_limit(confidence_factor, base_limit=0.20):
    return base_limit * confidence_factor

# Example: 20% limit for high confidence, 10% for low confidence
position_limit = calculate_position_limit(0.8)  # 16% limit
```

### 2. Dynamic Rebalancing

```python
# Rebalance when confidence changes significantly
def should_rebalance(old_confidence, new_confidence, threshold=0.1):
    return abs(new_confidence - old_confidence) > threshold
```

### 3. Confidence Thresholds

```python
# Minimum confidence requirements
MIN_CONFIDENCE_FOR_ALLOCATION = 0.5  # 50% minimum confidence
MIN_SAMPLE_SIZE = 60  # At least 60 days of data
```

## Monitoring and Maintenance

### 1. Monthly Tasks

- Recalculate confidence intervals for all positions
- Update confidence levels based on new data
- Adjust risk aversion factors if needed
- Review confidence thresholds

### 2. Quarterly Tasks

- Analyze confidence vs. actual performance
- Adjust confidence calculation methodology
- Review sector-specific confidence levels
- Update position limits based on confidence

### 3. Annual Tasks

- Comprehensive confidence methodology review
- Update confidence calculation parameters
- Review and adjust risk aversion factors
- Plan confidence-based allocation strategy

## Key Insights

### 1. Confidence-Weighted Principles

- **More data = higher confidence = larger positions**
- **Less data = lower confidence = smaller positions**
- **Higher uncertainty = more conservative allocation**
- **Confidence intervals provide uncertainty bounds**

### 2. Practical Considerations

- **Start with conservative confidence estimates**
- **Monitor confidence changes over time**
- **Use confidence thresholds for minimum allocations**
- **Rebalance when confidence changes significantly**

### 3. Common Mistakes to Avoid

- **Overestimating confidence**: Be conservative with confidence estimates
- **Ignoring sample size**: More data generally means higher confidence
- **Not updating confidence**: Recalculate regularly as new data arrives
- **Ignoring market conditions**: Adjust confidence for volatility

## Conclusion

The Confidence-Weighted Kelly Criterion provides a sophisticated approach to portfolio allocation that accounts for uncertainty in probability estimates. By dynamically adjusting position sizes based on confidence levels, you can achieve more robust and risk-aware portfolio management.

Key benefits:
- **Dynamic position sizing** based on confidence
- **Sample size awareness** for better estimates
- **Risk aversion integration** for conservative adjustments
- **Uncertainty quantification** with confidence intervals
- **Robust performance** in uncertain markets

This implementation gives you a powerful tool for optimal portfolio allocation that adapts to your confidence in the underlying estimates, making it particularly valuable for penny stock investing where uncertainty is often high. 
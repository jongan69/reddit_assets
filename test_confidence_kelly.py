#!/usr/bin/env python3
"""
Test script for Confidence-Weighted Kelly Criterion
Demonstrates how confidence in probability estimates affects position sizing
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import (
    calculate_kelly_fraction,
    calculate_confidence_interval,
    calculate_confidence_weighted_kelly,
    estimate_stock_probabilities_with_confidence,
    calculate_confidence_weighted_portfolio_allocation,
    display_confidence_weighted_allocation
)

def test_confidence_intervals():
    """Test confidence interval calculations"""
    print("📊 TESTING CONFIDENCE INTERVAL CALCULATIONS")
    print("=" * 60)
    
    import numpy as np
    
    # Simulate different return scenarios
    scenarios = [
        ("High win rate, large sample", np.random.choice([0.1, -0.05], 1000, p=[0.7, 0.3])),
        ("Low win rate, large sample", np.random.choice([0.1, -0.05], 1000, p=[0.3, 0.7])),
        ("High win rate, small sample", np.random.choice([0.1, -0.05], 100, p=[0.7, 0.3])),
        ("Low win rate, small sample", np.random.choice([0.1, -0.05], 100, p=[0.3, 0.7])),
    ]
    
    for name, returns in scenarios:
        print(f"\n{name}:")
        confidence_data = calculate_confidence_interval(returns, confidence_level=0.95)
        
        if confidence_data:
            print(f"  Point estimate: {confidence_data['point_estimate']:.3f}")
            print(f"  Confidence interval: [{confidence_data['lower_bound']:.3f}, {confidence_data['upper_bound']:.3f}]")
            print(f"  Margin of error: ±{confidence_data['margin_of_error']:.3f}")
            print(f"  Sample confidence: {confidence_data['sample_confidence']:.1%}")
            print(f"  Sample size: {confidence_data['sample_size']}")
        else:
            print("  Error calculating confidence interval")

def test_confidence_weighted_kelly():
    """Test confidence-weighted Kelly calculations"""
    print("\n🎯 TESTING CONFIDENCE-WEIGHTED KELLY CALCULATIONS")
    print("=" * 60)
    
    # Test scenarios with different confidence levels
    scenarios = [
        {
            'name': 'High confidence estimates',
            'p': 0.6, 'g': 0.2, 'l': 0.1,
            'p_conf': 0.9, 'g_conf': 0.85, 'l_conf': 0.8
        },
        {
            'name': 'Medium confidence estimates',
            'p': 0.6, 'g': 0.2, 'l': 0.1,
            'p_conf': 0.7, 'g_conf': 0.65, 'l_conf': 0.6
        },
        {
            'name': 'Low confidence estimates',
            'p': 0.6, 'g': 0.2, 'l': 0.1,
            'p_conf': 0.5, 'g_conf': 0.45, 'l_conf': 0.4
        },
        {
            'name': 'Very low confidence estimates',
            'p': 0.6, 'g': 0.2, 'l': 0.1,
            'p_conf': 0.3, 'g_conf': 0.25, 'l_conf': 0.2
        }
    ]
    
    for scenario in scenarios:
        print(f"\n{scenario['name']}:")
        
        # Calculate base Kelly
        base_kelly = calculate_kelly_fraction(scenario['p'], scenario['g'], scenario['l'])
        
        # Calculate confidence-weighted Kelly
        conf_kelly = calculate_confidence_weighted_kelly(
            scenario['p'], scenario['g'], scenario['l'],
            scenario['p_conf'], scenario['g_conf'], scenario['l_conf']
        )
        
        print(f"  Base Kelly: {base_kelly:.1%}")
        print(f"  Confidence-weighted Kelly: {conf_kelly['confidence_weighted_kelly']:.1%}")
        print(f"  Conservative Kelly: {conf_kelly['conservative_kelly']:.1%}")
        print(f"  Optimistic Kelly: {conf_kelly['optimistic_kelly']:.1%}")
        print(f"  Confidence factor: {conf_kelly['confidence_factor']:.1%}")
        print(f"  Risk adjustment: {conf_kelly['risk_adjustment']:.3f}")
        
        # Show the reduction due to confidence
        reduction = (base_kelly - conf_kelly['confidence_weighted_kelly']) / base_kelly * 100
        print(f"  Reduction due to confidence: {reduction:.1f}%")

def test_risk_aversion_impact():
    """Test how risk aversion affects confidence-weighted Kelly"""
    print("\n⚠️  TESTING RISK AVERSION IMPACT")
    print("=" * 60)
    
    # Base scenario
    p, g, l = 0.6, 0.2, 0.1
    p_conf, g_conf, l_conf = 0.7, 0.65, 0.6
    
    risk_aversion_levels = [0.5, 1.0, 1.5, 2.0, 3.0]
    
    print(f"Base scenario: p={p}, g={g}, l={l}")
    print(f"Confidence levels: p_conf={p_conf}, g_conf={g_conf}, l_conf={l_conf}")
    print()
    
    for risk_aversion in risk_aversion_levels:
        conf_kelly = calculate_confidence_weighted_kelly(
            p, g, l, p_conf, g_conf, l_conf, risk_aversion
        )
        
        print(f"Risk aversion {risk_aversion}:")
        print(f"  Confidence-weighted Kelly: {conf_kelly['confidence_weighted_kelly']:.1%}")
        print(f"  Risk adjustment: {conf_kelly['risk_adjustment']:.3f}")
        print()

def test_sample_size_impact():
    """Test how sample size affects confidence levels"""
    print("\n📈 TESTING SAMPLE SIZE IMPACT ON CONFIDENCE")
    print("=" * 60)
    
    # Simulate different sample sizes
    sample_sizes = [30, 60, 125, 252, 500, 1000]
    
    for n in sample_sizes:
        # Simulate returns with 60% win rate
        import numpy as np
        returns = np.random.choice([0.1, -0.05], n, p=[0.6, 0.4])
        
        confidence_data = calculate_confidence_interval(returns, confidence_level=0.95)
        
        if confidence_data:
            print(f"Sample size {n:4d}:")
            print(f"  Point estimate: {confidence_data['point_estimate']:.3f}")
            print(f"  Confidence interval: [{confidence_data['lower_bound']:.3f}, {confidence_data['upper_bound']:.3f}]")
            print(f"  Margin of error: ±{confidence_data['margin_of_error']:.3f}")
            print(f"  Sample confidence: {confidence_data['sample_confidence']:.1%}")
            print()

def test_portfolio_allocation_comparison():
    """Test confidence-weighted vs standard portfolio allocation"""
    print("\n🎯 TESTING PORTFOLIO ALLOCATION COMPARISON")
    print("=" * 60)
    
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
    
    print("Calculating confidence-weighted portfolio allocation...")
    print("Note: This will take time to fetch historical data for each stock.")
    
    try:
        # Calculate confidence-weighted allocation
        confidence_allocation = calculate_confidence_weighted_portfolio_allocation(
            sample_stocks, 
            portfolio_value=1000, 
            scaling_factor=0.5,
            risk_aversion=1.0
        )
        
        # Display results
        display_confidence_weighted_allocation(confidence_allocation, 1000)
        
        # Show confidence statistics
        if confidence_allocation['allocations']:
            print(f"\n📊 CONFIDENCE STATISTICS:")
            print("-" * 40)
            
            confidences = [alloc['confidence_factor'] for alloc in confidence_allocation['allocations']]
            print(f"  Average confidence: {sum(confidences)/len(confidences):.1%}")
            print(f"  Min confidence: {min(confidences):.1%}")
            print(f"  Max confidence: {max(confidences):.1%}")
            
            # Show how confidence affects allocation
            print(f"\n📈 CONFIDENCE vs ALLOCATION:")
            print("-" * 40)
            for alloc in confidence_allocation['allocations']:
                print(f"  {alloc['ticker']}: {alloc['confidence_factor']:.1%} confidence → ${alloc['dollar_allocation']:.0f} allocation")
        
    except Exception as e:
        print(f"Error in portfolio allocation: {e}")

def main():
    """Main test function"""
    print("🚀 CONFIDENCE-WEIGHTED KELLY CRITERION TEST")
    print("=" * 70)
    print("This script demonstrates how confidence in probability estimates")
    print("affects Kelly Criterion position sizing for more robust allocations.")
    print()
    
    # Test confidence interval calculations
    test_confidence_intervals()
    
    # Test confidence-weighted Kelly calculations
    test_confidence_weighted_kelly()
    
    # Test risk aversion impact
    test_risk_aversion_impact()
    
    # Test sample size impact
    test_sample_size_impact()
    
    # Test portfolio allocation (commented out to avoid API calls)
    # test_portfolio_allocation_comparison()
    
    print("\n✅ CONFIDENCE-WEIGHTED KELLY TEST COMPLETED")
    print("\n💡 KEY INSIGHTS:")
    print("• Higher confidence in estimates = larger position sizes")
    print("• Lower confidence = smaller position sizes (more conservative)")
    print("• Sample size directly affects confidence levels")
    print("• Risk aversion factor provides additional safety margin")
    print("• Confidence intervals provide uncertainty bounds")
    print("• More data = higher confidence = larger allocations")
    print("• Conservative approach: bias confidence estimates downward")

if __name__ == "__main__":
    main() 
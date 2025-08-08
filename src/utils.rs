pub fn format_currency(amount: f64) -> String {
    if amount >= 1_000_000_000.0 {
        format!("${:.2}B", amount / 1_000_000_000.0)
    } else if amount >= 1_000_000.0 {
        format!("${:.2}M", amount / 1_000_000.0)
    } else if amount >= 1_000.0 {
        format!("${:.2}K", amount / 1_000.0)
    } else {
        format!("${:.2}", amount)
    }
}

pub fn format_percentage(value: f64) -> String {
    format!("{:.2}%", value * 100.0)
}

pub fn calculate_volatility(returns: &[f64]) -> f64 {
    if returns.len() < 2 {
        return 0.0;
    }
    
    let mean = returns.iter().sum::<f64>() / returns.len() as f64;
    let variance = returns.iter()
        .map(|&r| (r - mean).powi(2))
        .sum::<f64>() / (returns.len() - 1) as f64;
    
    variance.sqrt()
}

pub fn calculate_sharpe_ratio(returns: &[f64], risk_free_rate: f64) -> f64 {
    if returns.is_empty() {
        return 0.0;
    }
    
    let avg_return = returns.iter().sum::<f64>() / returns.len() as f64;
    let volatility = calculate_volatility(returns);
    
    if volatility > 0.0 {
        (avg_return - risk_free_rate / 252.0) / volatility
    } else {
        0.0
    }
}

pub fn calculate_max_drawdown(prices: &[f64]) -> f64 {
    if prices.len() < 2 {
        return 0.0;
    }
    
    let mut max_drawdown: f64 = 0.0;
    let mut peak = prices[0];
    
    for &price in prices {
        if price > peak {
            peak = price;
        }
        let drawdown = (price - peak) / peak;
        max_drawdown = max_drawdown.min(drawdown);
    }
    
    max_drawdown.abs()
}

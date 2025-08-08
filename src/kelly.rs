use crate::{
    models::*,
    error::TradingBotError,
    config::TradingConfig,
};
use log::info;

pub struct KellyAnalyzer {
    config: TradingConfig,
}

impl KellyAnalyzer {
    pub fn new(config: TradingConfig) -> Self {
        Self { config }
    }
    
    pub fn enhance_kelly_analysis(&self, kelly_data: KellyAnalysis) -> Result<KellyAnalysis, TradingBotError> {
        info!("🔧 Enhancing Kelly analysis for {}", kelly_data.ticker);
        
        // For now, just return the original data
        // In a full implementation, you'd add additional calculations
        Ok(kelly_data)
    }
    
    pub fn calculate_unified_metric(
        &self,
        stock: &StockData,
        kelly: &KellyAnalysis,
    ) -> Result<UnifiedRiskRewardMetric, TradingBotError> {
        info!("🧮 Calculating unified metric for {}", stock.ticker);
        
        // Calculate Sortino ratio
        let sortino_ratio = Self::calculate_sortino_ratio(&stock.returns, 0.0, self.config.risk_free_rate)?;
        
        // Calculate Calmar ratio
        let calmar_ratio = Self::calculate_calmar_ratio(&stock.returns, self.config.lookback_days as f64)?;
        
        // Calculate unified score (weighted average)
        let unified_score = (kelly.confidence_weighted_kelly * 0.4 + 
                           sortino_ratio * 0.3 + 
                           calmar_ratio * 0.3).max(0.0).min(1.0);
        
        // Calculate average return
        let avg_return = if !stock.returns.is_empty() {
            stock.returns.iter().sum::<f64>() / stock.returns.len() as f64
        } else {
            0.0
        };
        
        // Calculate risk-adjusted Kelly
        let risk_adjusted_kelly = kelly.confidence_weighted_kelly * unified_score;
        
        Ok(UnifiedRiskRewardMetric {
            ticker: stock.ticker.clone(),
            unified_score,
            kelly_score: kelly.confidence_weighted_kelly,
            sortino_score: sortino_ratio,
            calmar_score: calmar_ratio,
            kelly_ratio: kelly.confidence_weighted_kelly,
            sortino_ratio,
            calmar_ratio,
            sharpe_ratio: kelly.sharpe_ratio,
            risk_adjusted_kelly,
            volatility: stock.volatility,
            avg_return,
            max_drawdown: kelly.max_drawdown,
            win_probability: kelly.win_probability,
            confidence_factor: kelly.confidence_factor,
            sample_size: stock.returns.len(),
        })
    }
    
    fn calculate_sortino_ratio(returns: &[f64], target_return: f64, risk_free_rate: f64) -> Result<f64, TradingBotError> {
        if returns.is_empty() {
            return Ok(0.0);
        }
        
        let daily_rf = (1.0 + risk_free_rate).powf(1.0 / 252.0) - 1.0;
        let excess_returns: Vec<f64> = returns.iter().map(|r| r - daily_rf).collect();
        
        let avg_excess_return = excess_returns.iter().sum::<f64>() / excess_returns.len() as f64;
        
        let downside_returns: Vec<f64> = excess_returns
            .iter()
            .map(|&r| (r - target_return).min(0.0))
            .collect();
        
        let downside_variance = downside_returns.iter().map(|&r| r * r).sum::<f64>() / downside_returns.len() as f64;
        let downside_deviation = downside_variance.sqrt();
        
        if downside_deviation > 0.0 {
            Ok(avg_excess_return / downside_deviation)
        } else {
            Ok(0.0)
        }
    }
    
    fn calculate_calmar_ratio(returns: &[f64], lookback_days: f64) -> Result<f64, TradingBotError> {
        if returns.is_empty() {
            return Ok(0.0);
        }
        
        let cagr = Self::calculate_annualized_return(returns, lookback_days);
        let max_dd = Self::calculate_max_drawdown(returns);
        
        if max_dd.abs() > 0.0 {
            Ok(cagr / max_dd.abs())
        } else {
            Ok(0.0)
        }
    }
    
    fn calculate_annualized_return(returns: &[f64], days: f64) -> f64 {
        if returns.is_empty() || days <= 0.0 {
            return 0.0;
        }
        
        let total_return = returns.iter().fold(1.0, |acc, &ret| acc * (1.0 + ret)) - 1.0;
        let years = days / 252.0;
        
        if years > 0.0 {
            (1.0 + total_return).powf(1.0 / years) - 1.0
        } else {
            0.0
        }
    }
    
    fn calculate_max_drawdown(returns: &[f64]) -> f64 {
        if returns.len() < 2 {
            return 0.0;
        }
        
        let mut cumulative_returns = Vec::new();
        let mut cumulative = 1.0;
        
        for &ret in returns {
            cumulative *= 1.0 + ret;
            cumulative_returns.push(cumulative);
        }
        
        let mut max_drawdown: f64 = 0.0;
        let mut peak = cumulative_returns[0];
        
        for &cumulative_return in &cumulative_returns {
            if cumulative_return > peak {
                peak = cumulative_return;
            }
            let drawdown = (cumulative_return - peak) / peak;
            max_drawdown = max_drawdown.min(drawdown);
        }
        
        if max_drawdown.abs() > 0.0 {
            max_drawdown.abs()
        } else {
            0.0
        }
    }
    
    pub fn calculate_kelly_fraction(&self, p: f64, g: f64, l: f64) -> Result<f64, TradingBotError> {
        self.validate_kelly_parameters(p, g, l)?;
        
        if l == 0.0 {
            return Ok(0.0);
        }
        
        let q = 1.0 - p;
        let b = g / l;
        let kelly_fraction = (b * p - q) / b;
        
        Ok(kelly_fraction.max(0.0))
    }
    
    pub fn calculate_scaled_kelly(&self, kelly_fraction: f64, scaling_factor: f64) -> f64 {
        kelly_fraction * scaling_factor
    }
    
    pub fn validate_kelly_parameters(&self, p: f64, g: f64, l: f64) -> Result<(), TradingBotError> {
        if p < 0.0 || p > 1.0 {
            return Err(TradingBotError::Calculation("Win probability must be between 0 and 1".to_string()));
        }
        
        if g < 0.0 {
            return Err(TradingBotError::Calculation("Average gain must be positive".to_string()));
        }
        
        if l < 0.0 {
            return Err(TradingBotError::Calculation("Average loss must be positive".to_string()));
        }
        
        Ok(())
    }
}

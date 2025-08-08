use crate::{
    models::*,
    error::TradingBotError,
    config::TradingConfig,
};
use log::info;
use statrs::distribution::{Normal, ContinuousCDF, Continuous};

pub struct OptionsAnalyzer {
    config: TradingConfig,
}

impl OptionsAnalyzer {
    pub fn new(config: TradingConfig) -> Self {
        Self { config }
    }
    
    pub fn enhance_options_analysis(&self, options_data: Vec<OptionsAnalysis>) -> Result<Vec<OptionsAnalysis>, TradingBotError> {
        info!("🔧 Enhancing options analysis...");
        
        let mut enhanced_options = Vec::new();
        
        for option in options_data {
            let enhanced_option = self.enhance_single_option(option)?;
            enhanced_options.push(enhanced_option);
        }
        
        Ok(enhanced_options)
    }
    
    fn enhance_single_option(&self, mut option: OptionsAnalysis) -> Result<OptionsAnalysis, TradingBotError> {
        // Calculate Greeks if not already present
        if option.greeks.is_none() {
            let greeks = Self::calculate_greeks(
                option.current_price,
                option.strike,
                option.days_to_expiry as f64 / 365.0,
                self.config.risk_free_rate,
                0.3, // Default volatility - in practice, you'd calculate implied volatility
            )?;
            option.greeks = Some(greeks);
        }
        
        // Calculate risk metrics
        let _risk_metrics = self.calculate_option_risk_metrics(&option)?;
        
        // Validate parameters
        self.validate_option_parameters(&option)?;
        
        Ok(option)
    }
    
    pub fn calculate_greeks(
        s: f64, // Current stock price
        k: f64, // Strike price
        t: f64, // Time to expiration (in years)
        r: f64, // Risk-free rate
        sigma: f64, // Volatility
    ) -> Result<OptionGreeks, TradingBotError> {
        if s <= 0.0 || k <= 0.0 || t <= 0.0 || sigma <= 0.0 {
            return Err(TradingBotError::Calculation("Invalid option parameters".to_string()));
        }
        
        let normal = Normal::new(0.0, 1.0)
            .map_err(|e| TradingBotError::Calculation(format!("Failed to create normal distribution: {}", e)))?;
        
        let d1 = (s.ln() / k + (r + sigma * sigma / 2.0) * t) / (sigma * t.sqrt());
        let d2 = d1 - sigma * t.sqrt();
        
        // Calculate Greeks for call option
        let delta = normal.cdf(d1);
        let gamma = normal.pdf(d1) / (s * sigma * t.sqrt());
        let theta = -s * normal.pdf(d1) * sigma / (2.0 * t.sqrt()) - 
                   r * k * (-r * t).exp() * normal.cdf(d2);
        let vega = s * t.sqrt() * normal.pdf(d1);
        
        Ok(OptionGreeks {
            delta,
            gamma,
            theta,
            vega,
        })
    }
    
    fn calculate_option_risk_metrics(&self, option: &OptionsAnalysis) -> Result<f64, TradingBotError> {
        // Calculate a simple risk score based on Greeks and other factors
        let risk_score = if let Some(greeks) = &option.greeks {
            let delta_risk = greeks.delta.abs();
            let gamma_risk = greeks.gamma.abs();
            let theta_risk = greeks.theta.abs();
            let vega_risk = greeks.vega.abs();
            
            // Normalize and combine risk factors
            (delta_risk + gamma_risk * 10.0 + theta_risk * 100.0 + vega_risk * 0.1) / 4.0
        } else {
            0.5 // Default risk score
        };
        
        Ok(risk_score)
    }
    
    pub fn validate_option_parameters(&self, option: &OptionsAnalysis) -> Result<(), TradingBotError> {
        if option.strike <= 0.0 {
            return Err(TradingBotError::Calculation("Strike price must be positive".to_string()));
        }
        
        if option.current_price <= 0.0 {
            return Err(TradingBotError::Calculation("Current price must be positive".to_string()));
        }
        
        if option.days_to_expiry == 0 {
            return Err(TradingBotError::Calculation("Days to expiry must be greater than 0".to_string()));
        }
        
        if option.ask < 0.0 {
            return Err(TradingBotError::Calculation("Ask price cannot be negative".to_string()));
        }
        
        if option.bid < 0.0 {
            return Err(TradingBotError::Calculation("Bid price cannot be negative".to_string()));
        }
        
        Ok(())
    }
}

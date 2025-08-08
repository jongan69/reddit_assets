use serde::{Deserialize, Serialize};
use std::path::Path;
use crate::error::TradingBotError;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    pub python: PythonConfig,
    pub api: ApiConfig,
    pub trading: TradingConfig,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PythonConfig {
    pub script_path: String,
    pub python_executable: String,
    pub modules: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ApiConfig {
    pub yahoo_finance_timeout: u64,
    pub finviz_timeout: u64,
    pub coingecko_timeout: u64,
    pub user_agent: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TradingConfig {
    pub default_portfolio_value: f64,
    pub default_scaling_factor: f64,
    pub max_positions: usize,
    pub min_allocation: f64,
    pub max_allocation_per_position: f64,
    pub risk_free_rate: f64,
    pub lookback_days: u32,
}

impl Config {
    pub fn load<P: AsRef<Path>>(path: P) -> Result<Self, TradingBotError> {
        let config = config::Config::builder()
            .add_source(config::File::from(path.as_ref()))
            .add_source(config::Environment::with_prefix("TRADING_BOT"))
            .build()
            .map_err(|e| TradingBotError::Config(e.to_string()))?;
        
        config.try_deserialize()
            .map_err(|e| TradingBotError::Config(e.to_string()))
    }
    
    pub fn default() -> Self {
        Self {
            python: PythonConfig {
                script_path: "./python_scripts".to_string(),
                python_executable: "python3".to_string(),
                modules: vec![
                    "main".to_string(),
                    "crypto".to_string(),
                ],
            },
            api: ApiConfig {
                yahoo_finance_timeout: 30,
                finviz_timeout: 30,
                coingecko_timeout: 30,
                user_agent: "TradingBot/1.0".to_string(),
            },
            trading: TradingConfig {
                default_portfolio_value: 1000.0,
                default_scaling_factor: 0.5,
                max_positions: 10,
                min_allocation: 10.0,
                max_allocation_per_position: 0.2,
                risk_free_rate: 0.05,
                lookback_days: 252,
            },
        }
    }
}

pub mod config;
pub mod error;
pub mod python_bridge;
pub mod trading;
pub mod models;
pub mod utils;
pub mod kelly;
pub mod options;
pub mod crypto;
pub mod portfolio;

pub use error::TradingBotError;
pub use config::Config;
pub use trading::TradingBot;
pub use python_bridge::PythonBridge;

#[cfg(test)]
mod tests {
    use super::*;
    use crate::utils::*;

    #[test]
    fn test_format_currency() {
        assert_eq!(format_currency(1234.56), "$1.23K");
        assert_eq!(format_currency(1234567.89), "$1.23M");
        assert_eq!(format_currency(1234567890.12), "$1.23B");
    }

    #[test]
    fn test_format_percentage() {
        assert_eq!(format_percentage(0.1234), "12.34%");
        assert_eq!(format_percentage(0.05), "5.00%");
    }

    #[test]
    fn test_calculate_volatility() {
        let returns = vec![0.01, -0.02, 0.03, -0.01, 0.02];
        let volatility = calculate_volatility(&returns);
        assert!(volatility > 0.0);
    }

    #[test]
    fn test_calculate_sharpe_ratio() {
        let returns = vec![0.01, -0.02, 0.03, -0.01, 0.02];
        let sharpe = calculate_sharpe_ratio(&returns, 0.05);
        assert!(sharpe.is_finite());
    }

    #[test]
    fn test_calculate_max_drawdown() {
        let prices = vec![100.0, 110.0, 105.0, 120.0, 115.0, 130.0];
        let max_dd = calculate_max_drawdown(&prices);
        assert!(max_dd >= 0.0);
    }

    #[test]
    fn test_kelly_calculations() {
        use crate::kelly::KellyAnalyzer;
        use crate::config::TradingConfig;

        let config = TradingConfig {
            default_portfolio_value: 1000.0,
            default_scaling_factor: 0.5,
            max_positions: 10,
            min_allocation: 10.0,
            max_allocation_per_position: 0.2,
            risk_free_rate: 0.05,
            lookback_days: 252,
        };

        let analyzer = KellyAnalyzer::new(config);
        
        // Test Kelly fraction calculation
        let kelly = analyzer.calculate_kelly_fraction(0.6, 0.1, 0.05).unwrap();
        assert!(kelly > 0.0);
        
        // Test scaled Kelly
        let scaled = analyzer.calculate_scaled_kelly(kelly, 0.5);
        assert_eq!(scaled, kelly * 0.5);
    }

    #[test]
    fn test_config_loading() {
        let config = Config::default();
        assert_eq!(config.trading.default_portfolio_value, 1000.0);
        assert_eq!(config.trading.default_scaling_factor, 0.5);
    }
}

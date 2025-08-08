use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StockData {
    pub ticker: String,
    pub current_price: f64,
    pub market_cap: Option<f64>,
    pub volume: Option<f64>,
    pub pe_ratio: Option<f64>,
    pub peg_ratio: Option<f64>,
    pub price_to_sales: Option<f64>,
    pub beta: Option<f64>,
    pub volatility: f64,
    pub returns: Vec<f64>,
    pub timestamp: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct KellyAnalysis {
    pub ticker: String,
    pub win_probability: f64,
    pub avg_gain: f64,
    pub avg_loss: f64,
    pub kelly_fraction: f64,
    pub confidence_weighted_kelly: f64,
    pub volatility: f64,
    pub sharpe_ratio: f64,
    pub max_drawdown: f64,
    pub sample_size: usize,
    pub confidence_factor: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OptionsAnalysis {
    pub ticker: String,
    pub strike: f64,
    pub ask: f64,
    pub bid: f64,
    pub expiry: String,
    pub current_price: f64,
    pub days_to_expiry: u32,
    pub return_25: f64,
    pub return_50: f64,
    pub return_100: f64,
    pub score: f64,
    pub reasons: Vec<String>,
    pub greeks: Option<OptionGreeks>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OptionGreeks {
    pub delta: f64,
    pub gamma: f64,
    pub theta: f64,
    pub vega: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PortfolioAllocation {
    pub ticker: String,
    pub current_price: f64,
    pub kelly_fraction: f64,
    pub scaled_kelly: f64,
    pub dollar_allocation: f64,
    pub shares_to_buy: u32,
    pub win_probability: f64,
    pub avg_gain: f64,
    pub avg_loss: f64,
    pub volatility: f64,
    pub sharpe_ratio: f64,
    pub doubling_score: f64,
    pub reasons: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PortfolioSummary {
    pub allocations: Vec<PortfolioAllocation>,
    pub total_allocated: f64,
    pub cash_remaining: f64,
    pub allocation_percentage: f64,
    pub expected_return: f64,
    pub portfolio_volatility: f64,
    pub portfolio_sharpe: f64,
    pub max_drawdown_estimate: f64,
    pub number_of_positions: usize,
    pub concentration_risk: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CryptoData {
    pub symbol: String,
    pub name: String,
    pub current_price: f64,
    pub market_cap: f64,
    pub volume_24h: f64,
    pub price_change_24h: f64,
    pub price_change_7d: f64,
    pub price_change_30d: f64,
    pub timestamp: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CryptoAnalysis {
    pub top_gainers: Vec<CryptoData>,
    pub top_losers: Vec<CryptoData>,
    pub market_overview: MarketOverview,
    pub analysis_summary: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MarketOverview {
    pub total_market_cap: f64,
    pub total_volume_24h: f64,
    pub bitcoin_dominance: f64,
    pub market_sentiment: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UnifiedRiskRewardMetric {
    pub ticker: String,
    pub unified_score: f64,
    pub kelly_score: f64,
    pub sortino_score: f64,
    pub calmar_score: f64,
    pub kelly_ratio: f64,
    pub sortino_ratio: f64,
    pub calmar_ratio: f64,
    pub sharpe_ratio: f64,
    pub risk_adjusted_kelly: f64,
    pub volatility: f64,
    pub avg_return: f64,
    pub max_drawdown: f64,
    pub win_probability: f64,
    pub confidence_factor: f64,
    pub sample_size: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AnalysisResult {
    pub timestamp: DateTime<Utc>,
    pub stock_analysis: Vec<StockData>,
    pub kelly_analysis: Vec<KellyAnalysis>,
    pub options_analysis: Vec<OptionsAnalysis>,
    pub crypto_analysis: Option<CryptoAnalysis>,
    pub portfolio_summary: Option<PortfolioSummary>,
    pub unified_metrics: Vec<UnifiedRiskRewardMetric>,
}

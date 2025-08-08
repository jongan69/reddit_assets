use crate::{
    models::*,
    error::TradingBotError,
    config::ApiConfig,
};
use log::info;
use reqwest::Client;
use serde_json::Value;

pub struct CryptoAnalyzer {
    config: ApiConfig,
    client: Client,
}

impl CryptoAnalyzer {
    pub fn new(config: ApiConfig) -> Self {
        let client = Client::builder()
            .timeout(std::time::Duration::from_secs(config.coingecko_timeout))
            .user_agent(&config.user_agent)
            .build()
            .unwrap_or_default();
        
        Self { config, client }
    }
    
    pub async fn enhance_crypto_analysis(&self, crypto_data: CryptoAnalysis) -> Result<CryptoAnalysis, TradingBotError> {
        info!("🔧 Enhancing crypto analysis...");
        
        // Fetch additional market data from CoinGecko API
        let market_data = self.fetch_crypto_market_data().await?;
        
        // Parse the market data and enhance the analysis
        let enhanced_crypto = self.parse_market_data(market_data, crypto_data).await?;
        
        Ok(enhanced_crypto)
    }
    
    async fn fetch_crypto_market_data(&self) -> Result<Value, TradingBotError> {
        info!("📊 Fetching crypto market data from CoinGecko...");
        
        let url = "https://api.coingecko.com/api/v3/coins/markets";
        let params = [
            ("vs_currency", "usd"),
            ("order", "market_cap_desc"),
            ("per_page", "50"),
            ("sparkline", "false"),
            ("price_change_percentage", "24h,7d,30d"),
        ];
        
        let response = self.client
            .get(url)
            .query(&params)
            .send()
            .await
            .map_err(|e| TradingBotError::Api(format!("Failed to fetch crypto data: {}", e)))?;
        
        if !response.status().is_success() {
            return Err(TradingBotError::Api(format!("CoinGecko API returned status: {}", response.status())));
        }
        
        let data = response.json::<Value>().await
            .map_err(|e| TradingBotError::Http(e))?;
        
        Ok(data)
    }
    
    async fn parse_market_data(&self, market_data: Value, mut crypto_analysis: CryptoAnalysis) -> Result<CryptoAnalysis, TradingBotError> {
        if let Some(coins) = market_data.as_array() {
            let mut top_gainers = Vec::new();
            let mut top_losers = Vec::new();
            let mut total_market_cap = 0.0;
            let mut total_volume = 0.0;
            let mut bitcoin_market_cap = 0.0;
            
            for coin in coins {
                if let (Some(symbol), Some(name), Some(price), Some(market_cap), Some(volume), Some(change_24h)) = (
                    coin.get("symbol").and_then(|s| s.as_str()),
                    coin.get("name").and_then(|s| s.as_str()),
                    coin.get("current_price").and_then(|p| p.as_f64()),
                    coin.get("market_cap").and_then(|m| m.as_f64()),
                    coin.get("total_volume").and_then(|v| v.as_f64()),
                    coin.get("price_change_percentage_24h").and_then(|c| c.as_f64()),
                ) {
                    let crypto_data = CryptoData {
                        symbol: symbol.to_uppercase(),
                        name: name.to_string(),
                        current_price: price,
                        market_cap,
                        volume_24h: volume,
                        price_change_24h: change_24h,
                        price_change_7d: coin.get("price_change_percentage_7d_in_currency")
                            .and_then(|c| c.as_f64()).unwrap_or(0.0),
                        price_change_30d: coin.get("price_change_percentage_30d_in_currency")
                            .and_then(|c| c.as_f64()).unwrap_or(0.0),
                        timestamp: chrono::Utc::now(),
                    };
                    
                    total_market_cap += market_cap;
                    total_volume += volume;
                    
                    if symbol.to_lowercase() == "bitcoin" {
                        bitcoin_market_cap = market_cap;
                    }
                    
                    // Categorize as gainer or loser
                    if change_24h > 0.0 {
                        top_gainers.push(crypto_data);
                    } else {
                        top_losers.push(crypto_data);
                    }
                }
            }
            
            // Sort by 24h change
            top_gainers.sort_by(|a, b| b.price_change_24h.partial_cmp(&a.price_change_24h).unwrap());
            top_losers.sort_by(|a, b| a.price_change_24h.partial_cmp(&b.price_change_24h).unwrap());
            
            // Take top 5 gainers and losers
            top_gainers.truncate(5);
            top_losers.truncate(5);
            
            // Calculate Bitcoin dominance
            let bitcoin_dominance = if total_market_cap > 0.0 {
                (bitcoin_market_cap / total_market_cap) * 100.0
            } else {
                0.0
            };
            
            // Determine market sentiment
            let market_sentiment = self.calculate_market_sentiment(&top_gainers, &top_losers);
            
            crypto_analysis.top_gainers = top_gainers;
            crypto_analysis.top_losers = top_losers;
            crypto_analysis.market_overview = MarketOverview {
                total_market_cap,
                total_volume_24h: total_volume,
                bitcoin_dominance,
                market_sentiment,
            };
        }
        
        Ok(crypto_analysis)
    }
    
    fn calculate_market_sentiment(&self, gainers: &[CryptoData], losers: &[CryptoData]) -> String {
        let avg_gain = gainers.iter().map(|c| c.price_change_24h).sum::<f64>() / gainers.len().max(1) as f64;
        let avg_loss = losers.iter().map(|c| c.price_change_24h).sum::<f64>() / losers.len().max(1) as f64;
        
        let sentiment_score = (avg_gain + avg_loss.abs()) / 2.0;
        
        match sentiment_score {
            s if s > 10.0 => "Very Bullish".to_string(),
            s if s > 5.0 => "Bullish".to_string(),
            s if s > 2.0 => "Slightly Bullish".to_string(),
            s if s > -2.0 => "Neutral".to_string(),
            s if s > -5.0 => "Bearish".to_string(),
            s if s > -10.0 => "Very Bearish".to_string(),
            _ => "Extremely Bearish".to_string(),
        }
    }
}

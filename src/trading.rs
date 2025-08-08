use crate::{
    config::Config,
    python_bridge::PythonBridge,
    models::*,
    error::TradingBotError,
    kelly::KellyAnalyzer,
    options::OptionsAnalyzer,
    crypto::CryptoAnalyzer,
    portfolio::PortfolioManager,
};
use log::{info, warn};
use chrono::Utc;

pub struct TradingBot {
    config: Config,
    python_bridge: PythonBridge,
    kelly_analyzer: KellyAnalyzer,
    options_analyzer: OptionsAnalyzer,
    crypto_analyzer: CryptoAnalyzer,
    portfolio_manager: PortfolioManager,
}

impl TradingBot {
    pub fn new(config: Config, python_bridge: PythonBridge) -> Result<Self, TradingBotError> {
        info!("🤖 Initializing Trading Bot...");
        
        let kelly_analyzer = KellyAnalyzer::new(config.trading.clone());
        let options_analyzer = OptionsAnalyzer::new(config.trading.clone());
        let crypto_analyzer = CryptoAnalyzer::new(config.api.clone());
        let portfolio_manager = PortfolioManager::new(config.trading.clone());
        
        Ok(Self {
            config,
            python_bridge,
            kelly_analyzer,
            options_analyzer,
            crypto_analyzer,
            portfolio_manager,
        })
    }
    
    pub async fn run_complete_analysis(
        &mut self,
        portfolio_value: f64,
        scaling_factor: f64,
    ) -> Result<AnalysisResult, TradingBotError> {
        info!("🚀 Starting complete trading analysis...");
        
        let start_time = Utc::now();
        
        // Step 1: Get trending stocks
        let trending_stocks = self.get_trending_stocks().await?;
        info!("📈 Found {} trending stocks", trending_stocks.len());
        
        // Step 2: Analyze each stock
        let mut stock_analysis = Vec::new();
        let mut kelly_analysis = Vec::new();
        let mut options_analysis = Vec::new();
        
        for ticker in trending_stocks.iter().take(self.config.trading.max_positions) {
            info!("📊 Analyzing {}", ticker);
            
            // Stock analysis
            match self.analyze_stock_potential(ticker).await {
                Ok(stock_data) => {
                    stock_analysis.push(stock_data.clone());
                    
                    // Kelly analysis
                    match self.analyze_kelly_criterion(ticker, self.config.trading.lookback_days).await {
                        Ok(kelly_data) => {
                            kelly_analysis.push(kelly_data);
                        }
                        Err(e) => {
                            warn!("Failed to analyze Kelly criterion for {}: {}", ticker, e);
                        }
                    }
                    
                    // Options analysis (only for stocks under $5)
                    if stock_data.current_price < 5.0 {
                        match self.analyze_options(ticker).await {
                            Ok(options) => {
                                options_analysis.extend(options);
                            }
                            Err(e) => {
                                warn!("Failed to analyze options for {}: {}", ticker, e);
                            }
                        }
                    }
                }
                Err(e) => {
                    warn!("Failed to analyze stock {}: {}", ticker, e);
                }
            }
        }
        
        // Step 3: Crypto analysis
        let crypto_analysis = match self.analyze_crypto().await {
            Ok(crypto) => Some(crypto),
            Err(e) => {
                warn!("Failed to analyze crypto: {}", e);
                None
            }
        };
        
        // Step 4: Portfolio allocation
        let portfolio_summary = if !stock_analysis.is_empty() {
            match self.calculate_portfolio_allocation(&stock_analysis, portfolio_value, scaling_factor).await {
                Ok(summary) => Some(summary),
                Err(e) => {
                    warn!("Failed to calculate portfolio allocation: {}", e);
                    None
                }
            }
        } else {
            None
        };
        
        // Step 5: Calculate unified risk-reward metrics
        let unified_metrics = self.calculate_unified_metrics(&stock_analysis, &kelly_analysis).await?;
        
        let result = AnalysisResult {
            timestamp: start_time,
            stock_analysis,
            kelly_analysis,
            options_analysis,
            crypto_analysis,
            portfolio_summary,
            unified_metrics,
        };
        
        // Step 6: Display results
        self.display_analysis_results(&result).await?;
        
        info!("✅ Complete analysis finished successfully");
        Ok(result)
    }
    
    pub async fn analyze_kelly_criterion(
        &self,
        ticker: &str,
        lookback_days: u32,
    ) -> Result<KellyAnalysis, TradingBotError> {
        info!("🎯 Analyzing Kelly Criterion for {}", ticker);
        
        // Use Python bridge to get Kelly analysis
        let kelly_data = self.python_bridge.estimate_stock_probabilities(ticker, lookback_days)?;
        
        // Enhance with Rust-based calculations
        let enhanced_kelly = self.kelly_analyzer.enhance_kelly_analysis(kelly_data)?;
        
        Ok(enhanced_kelly)
    }
    
    pub async fn analyze_stock_potential(&self, ticker: &str) -> Result<StockData, TradingBotError> {
        info!("📈 Analyzing stock potential for {}", ticker);
        
        // Use Python bridge to get stock data
        let stock_data = self.python_bridge.analyze_stock_potential(ticker)?;
        
        Ok(stock_data)
    }
    
    pub async fn analyze_options(&self, ticker: &str) -> Result<Vec<OptionsAnalysis>, TradingBotError> {
        info!("📊 Analyzing options for {}", ticker);
        
        // Use Python bridge to get options analysis
        let options_data = self.python_bridge.analyze_options(ticker)?;
        
        // Enhance with Rust-based calculations
        let enhanced_options = self.options_analyzer.enhance_options_analysis(options_data)?;
        
        Ok(enhanced_options)
    }
    
    pub async fn analyze_crypto(&self) -> Result<CryptoAnalysis, TradingBotError> {
        info!("🪙 Analyzing crypto market...");
        
        // Use Python bridge to get crypto analysis
        let crypto_data = self.python_bridge.analyze_crypto()?;
        
        // Enhance with Rust-based calculations
        let enhanced_crypto = self.crypto_analyzer.enhance_crypto_analysis(crypto_data).await?;
        
        Ok(enhanced_crypto)
    }
    
    pub async fn calculate_portfolio_allocation(
        &self,
        stocks_data: &[StockData],
        portfolio_value: f64,
        scaling_factor: f64,
    ) -> Result<PortfolioSummary, TradingBotError> {
        info!("💼 Calculating portfolio allocation...");
        
        // Convert StockData to the format expected by Python
        let stocks_for_python = stocks_data.iter().map(|stock| {
            // Create a simplified structure for Python
            stock.clone()
        }).collect();
        
        // Use Python bridge to calculate allocation
        let portfolio_summary = self.python_bridge.calculate_portfolio_allocation(
            stocks_for_python,
            portfolio_value,
            scaling_factor,
        )?;
        
        // Enhance with Rust-based portfolio management
        let enhanced_summary = self.portfolio_manager.enhance_portfolio_summary(portfolio_summary)?;
        
        Ok(enhanced_summary)
    }
    
    async fn get_trending_stocks(&self) -> Result<Vec<String>, TradingBotError> {
        info!("🔍 Getting trending stocks...");
        
        // For now, return a list of popular penny stocks
        // In a full implementation, you'd scrape trending stocks from various sources
        let trending_stocks = vec![
            "SNDL".to_string(),
            "BITF".to_string(),
            "HEXO".to_string(),
            "ACB".to_string(),
            "TLRY".to_string(),
            "CGC".to_string(),
            "APHA".to_string(),
            "CRON".to_string(),
            "OGI".to_string(),
            "VFF".to_string(),
        ];
        
        Ok(trending_stocks)
    }
    
    async fn calculate_unified_metrics(
        &self,
        stock_analysis: &[StockData],
        kelly_analysis: &[KellyAnalysis],
    ) -> Result<Vec<UnifiedRiskRewardMetric>, TradingBotError> {
        info!("🧮 Calculating unified risk-reward metrics...");
        
        let mut unified_metrics = Vec::new();
        
        for stock in stock_analysis {
            if let Some(kelly) = kelly_analysis.iter().find(|k| k.ticker == stock.ticker) {
                let unified_metric = self.kelly_analyzer.calculate_unified_metric(stock, kelly)?;
                unified_metrics.push(unified_metric);
            }
        }
        
        Ok(unified_metrics)
    }
    
    async fn display_analysis_results(&self, result: &AnalysisResult) -> Result<(), TradingBotError> {
        info!("📊 Displaying analysis results...");
        
        println!("\n{}", "=".repeat(80));
        println!("🎯 TRADING BOT ANALYSIS RESULTS");
        println!("{}", "=".repeat(80));
        println!("Timestamp: {}", result.timestamp.format("%Y-%m-%d %H:%M:%S UTC"));
        
        // Display stock analysis
        if !result.stock_analysis.is_empty() {
            println!("\n📈 STOCK ANALYSIS ({} stocks):", result.stock_analysis.len());
            println!("{:<8} {:<10} {:<12} {:<10} {:<10}", "Ticker", "Price", "Market Cap", "Volume", "Volatility");
            println!("{}", "-".repeat(60));
            
            for stock in &result.stock_analysis {
                let market_cap = stock.market_cap.map(|m| format!("${:.0}M", m / 1_000_000.0)).unwrap_or("N/A".to_string());
                let volume = stock.volume.map(|v| format!("{:.0}K", v / 1_000.0)).unwrap_or("N/A".to_string());
                println!("{:<8} ${:<9.2} {:<12} {:<10} {:<10.1}%", 
                    stock.ticker, stock.current_price, market_cap, volume, stock.volatility * 100.0);
            }
        }
        
        // Display Kelly analysis
        if !result.kelly_analysis.is_empty() {
            println!("\n🎯 KELLY CRITERION ANALYSIS:");
            println!("{:<8} {:<10} {:<10} {:<10} {:<10} {:<10}", 
                "Ticker", "Win Prob", "Avg Gain", "Avg Loss", "Kelly %", "Confidence");
            println!("{}", "-".repeat(70));
            
            for kelly in &result.kelly_analysis {
                println!("{:<8} {:<9.1}% {:<9.1}% {:<9.1}% {:<9.1}% {:<9.1}%", 
                    kelly.ticker, 
                    kelly.win_probability * 100.0,
                    kelly.avg_gain * 100.0,
                    kelly.avg_loss * 100.0,
                    kelly.confidence_weighted_kelly * 100.0,
                    kelly.confidence_factor * 100.0);
            }
        }
        
        // Display options analysis
        if !result.options_analysis.is_empty() {
            println!("\n📊 OPTIONS ANALYSIS ({} opportunities):", result.options_analysis.len());
            println!("{:<8} {:<8} {:<8} {:<8} {:<8} {:<8}", 
                "Ticker", "Strike", "Ask", "Expiry", "Return 25%", "Score");
            println!("{}", "-".repeat(60));
            
            for option in &result.options_analysis {
                println!("{:<8} ${:<7.2} ${:<7.2} {:<8} {:<7.0}% {:<7.0}", 
                    option.ticker, option.strike, option.ask, 
                    option.expiry.split('-').last().unwrap_or("N/A"),
                    option.return_25 * 100.0, option.score);
            }
        }
        
        // Display portfolio summary
        if let Some(summary) = &result.portfolio_summary {
            println!("\n💼 PORTFOLIO ALLOCATION SUMMARY:");
            println!("Total Allocated: ${:.2}", summary.total_allocated);
            println!("Cash Remaining: ${:.2}", summary.cash_remaining);
            println!("Allocation %: {:.1}%", summary.allocation_percentage);
            println!("Number of Positions: {}", summary.number_of_positions);
            println!("Expected Return: {:.2}%", summary.expected_return * 100.0);
            println!("Portfolio Volatility: {:.2}%", summary.portfolio_volatility * 100.0);
            println!("Portfolio Sharpe: {:.2}", summary.portfolio_sharpe);
            
            if !summary.allocations.is_empty() {
                println!("\n📋 ALLOCATION BREAKDOWN:");
                println!("{:<8} {:<10} {:<10} {:<12} {:<8}", 
                    "Ticker", "Price", "Allocation", "Shares", "Kelly %");
                println!("{}", "-".repeat(60));
                
                for alloc in &summary.allocations {
                    println!("{:<8} ${:<9.2} ${:<10.2} {:<8} {:<8.1}%", 
                        alloc.ticker, alloc.current_price, alloc.dollar_allocation, 
                        alloc.shares_to_buy, alloc.scaled_kelly * 100.0);
                }
            }
        }
        
        // Display crypto analysis
        if let Some(crypto) = &result.crypto_analysis {
            println!("\n🪙 CRYPTO MARKET ANALYSIS:");
            println!("{}", crypto.analysis_summary);
        }
        
        // Display unified metrics
        if !result.unified_metrics.is_empty() {
            println!("\n🏆 UNIFIED RISK-REWARD METRICS:");
            println!("{:<8} {:<10} {:<10} {:<10} {:<10}", 
                "Ticker", "Unified", "Kelly", "Sortino", "Calmar");
            println!("{}", "-".repeat(60));
            
            for metric in &result.unified_metrics {
                println!("{:<8} {:<9.1}% {:<9.1}% {:<9.1}% {:<9.1}%", 
                    metric.ticker,
                    metric.unified_score * 100.0,
                    metric.kelly_score * 100.0,
                    metric.sortino_score * 100.0,
                    metric.calmar_score * 100.0);
            }
        }
        
        println!("\n{}", "=".repeat(80));
        println!("✅ Analysis complete!");
        println!("{}", "=".repeat(80));
        
        Ok(())
    }
    
    pub async fn test_python_bridge(&self) -> Result<(), TradingBotError> {
        info!("🧪 Testing Python bridge...");
        
        self.python_bridge.test_python_bridge()?;
        
        info!("✅ Python bridge test completed successfully");
        Ok(())
    }
}

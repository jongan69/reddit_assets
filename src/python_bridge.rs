use pyo3::prelude::*;
use pyo3::types::PyDict;
use crate::error::TradingBotError;
use crate::models::*;
use log::info;

pub struct PythonBridge {
    py_runtime: Option<PyObject>,
}

impl PythonBridge {
    pub fn new() -> Result<Self, TradingBotError> {
        info!("🔗 Initializing Python bridge...");
        
        // Initialize Python interpreter
        let py_runtime = Python::with_gil(|py| -> Result<PyObject, TradingBotError> {
            // Add the current directory to Python path
            let sys = PyModule::import_bound(py, "sys")?;
            let path = sys.getattr("path")?;
            path.call_method1("append", (".",))?;
            
            // Import our Python modules
            let main_module = PyModule::import_bound(py, "main")?;
            let crypto_module = PyModule::import_bound(py, "crypto")?;
            
            // Store references to the modules
            let modules = PyDict::new_bound(py);
            modules.set_item("main", main_module)?;
            modules.set_item("crypto", crypto_module)?;
            
            Ok(modules.into())
        })?;
        
        info!("✅ Python bridge initialized successfully");
        Ok(Self {
            py_runtime: Some(py_runtime),
        })
    }
    
    pub fn estimate_stock_probabilities(&self, ticker: &str, lookback_days: u32) -> Result<KellyAnalysis, TradingBotError> {
        info!("📊 Estimating stock probabilities for {}", ticker);
        
        Python::with_gil(|py| {
            let modules = self.py_runtime.as_ref().unwrap().bind(py);
            let main_item = modules.get_item("main").unwrap();
            let main_module = main_item.downcast::<PyModule>()
                .map_err(|e| TradingBotError::PythonBridge(format!("Failed to downcast main module: {}", e)))?;
            
            // Call the Python function
            let result = main_module.call_method1(
                "estimate_stock_probabilities_with_confidence",
                (ticker, lookback_days)
            )?;
            
                               // Convert Python result to Rust struct
                   let ticker: String = result.get_item("ticker")?.extract()?;
                   let win_probability: f64 = result.get_item("win_probability")?.extract()?;
                   let avg_gain: f64 = result.get_item("avg_gain")?.extract()?;
                   let avg_loss: f64 = result.get_item("avg_loss")?.extract()?;
                   let volatility: f64 = result.get_item("volatility")?.extract()?;
                   let sharpe_ratio: f64 = result.get_item("sharpe_ratio")?.extract()?;
                   let max_drawdown: f64 = result.get_item("max_drawdown")?.extract()?;
                   let sample_size: usize = result.get_item("sample_size")?.extract()?;
            
                               // Get Kelly results
                   let kelly_results = result.get_item("kelly_results")?;
                   let confidence_weighted_kelly: f64 = kelly_results.get_item("confidence_weighted_kelly")?.extract()?;
                   let confidence_factor: f64 = kelly_results.get_item("confidence_factor")?.extract()?;
            
            // Calculate base Kelly fraction
            let kelly_fraction = self.calculate_kelly_fraction(win_probability, avg_gain, avg_loss)?;
            
            Ok(KellyAnalysis {
                ticker,
                win_probability,
                avg_gain,
                avg_loss,
                kelly_fraction,
                confidence_weighted_kelly,
                volatility,
                sharpe_ratio,
                max_drawdown,
                sample_size,
                confidence_factor,
            })
        })
    }
    
    pub fn analyze_stock_potential(&self, ticker: &str) -> Result<StockData, TradingBotError> {
        info!("📈 Analyzing stock potential for {}", ticker);
        
        Python::with_gil(|py| {
            let modules = self.py_runtime.as_ref().unwrap().bind(py);
            let main_item = modules.get_item("main").unwrap();
            let main_module = main_item.downcast::<PyModule>()
                .map_err(|e| TradingBotError::PythonBridge(format!("Failed to downcast main module: {}", e)))?;
            
            // Call the Python function
            let result = main_module.call_method1("analyze_stock_potential", (ticker,))?;
            
                               // Convert Python result to Rust struct
                   let ticker: String = result.get_item("Ticker")?.extract()?;
                   let current_price: f64 = result.get_item("Current_Price")?.extract()?;
                   let market_cap: Option<f64> = result.get_item("Market_Cap")?.extract().ok();
                   let volume: Option<f64> = result.get_item("Volume_Avg")?.extract().ok();
                   let pe_ratio: Option<f64> = result.get_item("PE_Ratio")?.extract().ok();
                   let peg_ratio: Option<f64> = result.get_item("PEG_Ratio")?.extract().ok();
                   let price_to_sales: Option<f64> = result.get_item("Price_to_Sales")?.extract().ok();
                   let beta: Option<f64> = result.get_item("Beta")?.extract().ok();
                   let volatility: f64 = result.get_item("Volatility")?.extract()?;
            
            // For now, we'll use a placeholder for returns
            // In a full implementation, you'd extract historical returns
            let returns = vec![0.0]; // Placeholder
            
            Ok(StockData {
                ticker,
                current_price,
                market_cap,
                volume,
                pe_ratio,
                peg_ratio,
                price_to_sales,
                beta,
                volatility,
                returns,
                timestamp: chrono::Utc::now(),
            })
        })
    }
    
    pub fn analyze_options(&self, ticker: &str) -> Result<Vec<OptionsAnalysis>, TradingBotError> {
        info!("📊 Analyzing options for {}", ticker);
        
        Python::with_gil(|py| {
            let modules = self.py_runtime.as_ref().unwrap().bind(py);
            let main_item = modules.get_item("main").unwrap();
            let main_module = main_item.downcast::<PyModule>()
                .map_err(|e| TradingBotError::PythonBridge(format!("Failed to downcast main module: {}", e)))?;
            
            // Call the Python function
            let result = main_module.call_method1("analyze_options_with_greeks", (ticker,))?;
            
            // Convert Python list to Rust Vec
            let mut options = Vec::new();
            
            if let Ok(py_list) = result.downcast::<pyo3::types::PyList>() {
                                       for item in py_list.iter() {
                           let ticker: String = item.get_item("symbol")?.extract()?;
                           let strike: f64 = item.get_item("strike")?.extract()?;
                           let ask: f64 = item.get_item("ask")?.extract()?;
                           let bid: f64 = item.get_item("bid")?.extract()?;
                           let expiry: String = item.get_item("expiry")?.extract()?;
                           let current_price: f64 = item.get_item("current_price")?.extract()?;
                           let days_to_expiry: u32 = item.get_item("days_to_expiry")?.extract()?;
                           let return_25: f64 = item.get_item("return_25")?.extract()?;
                           let return_50: f64 = item.get_item("return_50")?.extract()?;
                           let return_100: f64 = item.get_item("return_100")?.extract()?;
                           let score: f64 = item.get_item("score")?.extract()?;
                    
                                               // Extract reasons list
                           let py_reasons = item.get_item("reasons")?;
                           let reasons: Vec<String> = if let Ok(py_list) = py_reasons.downcast::<pyo3::types::PyList>() {
                               py_list.iter().map(|r| r.extract::<String>().unwrap_or_default()).collect()
                           } else {
                               vec![]
                           };
                           
                           // Extract Greeks if available
                           let greeks = if let Ok(py_greeks) = item.get_item("greeks") {
                               if !py_greeks.is_none() {
                                   Some(OptionGreeks {
                                       delta: py_greeks.get_item("delta")?.extract()?,
                                       gamma: py_greeks.get_item("gamma")?.extract()?,
                                       theta: py_greeks.get_item("theta")?.extract()?,
                                       vega: py_greeks.get_item("vega")?.extract()?,
                                   })
                               } else {
                                   None
                               }
                           } else {
                               None
                           };
                    
                    options.push(OptionsAnalysis {
                        ticker,
                        strike,
                        ask,
                        bid,
                        expiry,
                        current_price,
                        days_to_expiry,
                        return_25,
                        return_50,
                        return_100,
                        score,
                        reasons,
                        greeks,
                    });
                }
            }
            
            Ok(options)
        })
    }
    
    pub fn analyze_crypto(&self) -> Result<CryptoAnalysis, TradingBotError> {
        info!("🪙 Analyzing crypto market...");
        
        Python::with_gil(|py| {
            let modules = self.py_runtime.as_ref().unwrap().bind(py);
            let crypto_item = modules.get_item("crypto").unwrap();
            let crypto_module = crypto_item.downcast::<PyModule>()
                .map_err(|e| TradingBotError::PythonBridge(format!("Failed to downcast crypto module: {}", e)))?;
            
            // Call the Python function to generate market summary
            let summary = crypto_module.call_method0("generate_market_summary")?;
            let summary_text: String = summary.extract()?;
            
            // For now, return a basic structure
            // In a full implementation, you'd parse the summary and extract structured data
            Ok(CryptoAnalysis {
                top_gainers: vec![],
                top_losers: vec![],
                market_overview: MarketOverview {
                    total_market_cap: 0.0,
                    total_volume_24h: 0.0,
                    bitcoin_dominance: 0.0,
                    market_sentiment: "neutral".to_string(),
                },
                analysis_summary: summary_text,
            })
        })
    }
    
    pub fn calculate_portfolio_allocation(
        &self,
        stocks_data: Vec<StockData>,
        portfolio_value: f64,
        scaling_factor: f64,
    ) -> Result<PortfolioSummary, TradingBotError> {
        info!("💼 Calculating portfolio allocation...");
        
        Python::with_gil(|py| {
            let modules = self.py_runtime.as_ref().unwrap().bind(py);
            let main_item = modules.get_item("main").unwrap();
            let main_module = main_item.downcast::<PyModule>()
                .map_err(|e| TradingBotError::PythonBridge(format!("Failed to downcast main module: {}", e)))?;
            
            // Convert Rust data to Python format
            let py_stocks_data = pyo3::types::PyList::new_bound(py, Vec::<PyObject>::new());
            for stock in &stocks_data {
                let py_dict = PyDict::new_bound(py);
                py_dict.set_item("Ticker", stock.ticker.as_str())?;
                py_dict.set_item("Current_Price", stock.current_price)?;
                py_dict.set_item("Doubling_Score", 50.0)?; // Placeholder
                let reasons = pyo3::types::PyList::new_bound(py, ["Analysis complete"]);
                py_dict.set_item("Reasons", reasons)?;
                py_stocks_data.append(py_dict)?;
            }
            
            // Call the Python function
            let result = main_module.call_method1(
                "calculate_confidence_weighted_portfolio_allocation",
                (py_stocks_data, portfolio_value, scaling_factor)
            )?;
            
            // Convert Python result to Rust struct
            let total_allocated: f64 = result.getattr("total_allocated")?.extract()?;
            let cash_remaining: f64 = result.getattr("cash_remaining")?.extract()?;
            let allocation_percentage: f64 = result.getattr("allocation_percentage")?.extract()?;
            
            // Extract allocations
            let py_allocations = result.getattr("allocations")?;
            let mut allocations = Vec::new();
            
            if let Ok(py_list) = py_allocations.downcast::<pyo3::types::PyList>() {
                for item in py_list.iter() {
                    let ticker: String = item.getattr("ticker")?.extract()?;
                    let current_price: f64 = item.getattr("current_price")?.extract()?;
                    let kelly_fraction: f64 = item.getattr("confidence_weighted_kelly")?.extract()?;
                    let scaled_kelly: f64 = item.getattr("scaled_kelly")?.extract()?;
                    let dollar_allocation: f64 = item.getattr("dollar_allocation")?.extract()?;
                    let shares_to_buy: u32 = item.getattr("shares_to_buy")?.extract()?;
                    let win_probability: f64 = item.getattr("win_probability")?.extract()?;
                    let avg_gain: f64 = item.getattr("avg_gain")?.extract()?;
                    let avg_loss: f64 = item.getattr("avg_loss")?.extract()?;
                    let volatility: f64 = item.getattr("volatility")?.extract()?;
                    let sharpe_ratio: f64 = item.getattr("sharpe_ratio")?.extract()?;
                    let doubling_score: f64 = item.getattr("doubling_score")?.extract()?;
                    
                    // Extract reasons
                    let py_reasons = item.getattr("reasons")?;
                    let reasons: Vec<String> = if let Ok(py_list) = py_reasons.downcast::<pyo3::types::PyList>() {
                        py_list.iter().map(|r| r.extract::<String>().unwrap_or_default()).collect()
                    } else {
                        vec![]
                    };
                    
                    allocations.push(PortfolioAllocation {
                        ticker,
                        current_price,
                        kelly_fraction,
                        scaled_kelly,
                        dollar_allocation,
                        shares_to_buy,
                        win_probability,
                        avg_gain,
                        avg_loss,
                        volatility,
                        sharpe_ratio,
                        doubling_score,
                        reasons,
                    });
                }
            }
            
            // Calculate portfolio metrics
            let expected_return = allocations.iter()
                .map(|a| a.win_probability * a.avg_gain * (a.dollar_allocation / total_allocated))
                .sum::<f64>();
            
            let portfolio_volatility = allocations.iter()
                .map(|a| a.volatility * (a.dollar_allocation / total_allocated))
                .sum::<f64>();
            
            let portfolio_sharpe = allocations.iter()
                .map(|a| a.sharpe_ratio * (a.dollar_allocation / total_allocated))
                .sum::<f64>();
            
            let max_drawdown_estimate = portfolio_volatility * 2.0;
            
            let concentration_risk = allocations.iter()
                .map(|a| a.dollar_allocation / total_allocated)
                .fold(0.0, f64::max);
            
            let number_of_positions = allocations.len();
            
            Ok(PortfolioSummary {
                allocations,
                total_allocated,
                cash_remaining,
                allocation_percentage,
                expected_return,
                portfolio_volatility,
                portfolio_sharpe,
                max_drawdown_estimate,
                number_of_positions,
                concentration_risk,
            })
        })
    }
    
    fn calculate_kelly_fraction(&self, p: f64, g: f64, l: f64) -> Result<f64, TradingBotError> {
        if l == 0.0 {
            return Ok(0.0);
        }
        
        let q = 1.0 - p;
        let b = g / l;
        let kelly_fraction = (b * p - q) / b;
        
        Ok(kelly_fraction.max(0.0))
    }
    
    pub fn test_python_bridge(&self) -> Result<(), TradingBotError> {
        info!("🧪 Testing Python bridge functionality...");
        
        // Test basic Python function call
        Python::with_gil(|py| {
            let modules = self.py_runtime.as_ref().unwrap().bind(py);
            let main_item = modules.get_item("main").unwrap();
            let main_module = main_item.downcast::<PyModule>()
                .map_err(|e| TradingBotError::PythonBridge(format!("Failed to downcast main module: {}", e)))?;
            
            // Test a simple function call
            let result = main_module.call_method1("calculate_kelly_fraction", (0.6, 0.1, 0.05))?;
            let kelly_fraction: f64 = result.extract()?;
            
            info!("✅ Python bridge test successful - Kelly fraction: {:.4}", kelly_fraction);
            Ok(())
        })
    }
}

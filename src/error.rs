use thiserror::Error;

#[derive(Error, Debug)]
pub enum TradingBotError {
    #[error("Configuration error: {0}")]
    Config(String),
    
    #[error("Python bridge error: {0}")]
    PythonBridge(String),
    
    #[error("API error: {0}")]
    Api(String),
    
    #[error("Data processing error: {0}")]
    DataProcessing(String),
    
    #[error("Calculation error: {0}")]
    Calculation(String),
    
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
    
    #[error("JSON error: {0}")]
    Json(#[from] serde_json::Error),
    
    #[error("HTTP error: {0}")]
    Http(#[from] reqwest::Error),
    
    #[error("PyO3 error: {0}")]
    PyO3(#[from] pyo3::PyErr),
    
    #[error("Anyhow error: {0}")]
    Anyhow(#[from] anyhow::Error),
}

impl From<String> for TradingBotError {
    fn from(err: String) -> Self {
        TradingBotError::DataProcessing(err)
    }
}

impl From<&str> for TradingBotError {
    fn from(err: &str) -> Self {
        TradingBotError::DataProcessing(err.to_string())
    }
}

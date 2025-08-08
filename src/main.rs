use clap::{Parser, Subcommand};
use log::info;
use trading_bot::{
    config::Config,
    trading::TradingBot,
    python_bridge::PythonBridge,
    error::TradingBotError,
};

#[derive(Parser)]
#[command(name = "trading_bot")]
#[command(about = "A modular Rust trading bot with Python integration")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
    
    #[arg(short, long, default_value = "config.toml")]
    config: String,
}

#[derive(Subcommand)]
enum Commands {
    /// Run the complete trading analysis workflow
    Analyze {
        #[arg(short, long, default_value = "1000")]
        portfolio_value: f64,
        
        #[arg(short, long, default_value = "0.5")]
        scaling_factor: f64,
    },
    
    /// Run Kelly Criterion analysis only
    Kelly {
        #[arg(short, long)]
        ticker: String,
        
        #[arg(short, long, default_value = "252")]
        lookback_days: u32,
    },
    
    /// Run options analysis
    Options {
        #[arg(short, long)]
        ticker: String,
    },
    
    /// Run crypto analysis
    Crypto,
    
    /// Test Python bridge functionality
    TestPython,
}

#[tokio::main]
async fn main() -> Result<(), TradingBotError> {
    // Initialize logging
    env_logger::init();
    
    let cli = Cli::parse();
    
    info!("🚀 Starting Trading Bot...");
    
    // Load configuration
    let config = Config::load(&cli.config)?;
    info!("✅ Configuration loaded from {}", cli.config);
    
    // Initialize Python bridge
    let python_bridge = PythonBridge::new()?;
    info!("✅ Python bridge initialized");
    
    // Initialize trading bot
    let mut trading_bot = TradingBot::new(config, python_bridge)?;
    info!("✅ Trading bot initialized");
    
    match cli.command {
        Commands::Analyze { portfolio_value, scaling_factor } => {
            info!("📊 Running complete trading analysis...");
            trading_bot.run_complete_analysis(portfolio_value, scaling_factor).await?;
        }
        
        Commands::Kelly { ticker, lookback_days } => {
            info!("🎯 Running Kelly Criterion analysis for {}", ticker);
            let result = trading_bot.analyze_kelly_criterion(&ticker, lookback_days).await?;
            println!("Kelly Analysis Result: {:#?}", result);
        }
        
        Commands::Options { ticker } => {
            info!("📈 Running options analysis for {}", ticker);
            let result = trading_bot.analyze_options(&ticker).await?;
            println!("Options Analysis Result: {:#?}", result);
        }
        
        Commands::Crypto => {
            info!("🪙 Running crypto analysis...");
            let result = trading_bot.analyze_crypto().await?;
            println!("Crypto Analysis Result: {:#?}", result);
        }
        
        Commands::TestPython => {
            info!("🧪 Testing Python bridge...");
            trading_bot.test_python_bridge().await?;
        }
    }
    
    info!("✅ Trading bot completed successfully");
    Ok(())
}

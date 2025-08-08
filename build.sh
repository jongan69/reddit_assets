#!/bin/bash

# Rust Trading Bot Build Script
# This script helps set up and test the trading bot

set -e

echo "🚀 Building Rust Trading Bot..."

# Check if Rust is installed
if ! command -v cargo &> /dev/null; then
    echo "❌ Rust is not installed. Please install Rust first:"
    echo "   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

echo "✅ Rust and Python are available"

# Check if Python modules exist
if [ ! -f "main.py" ]; then
    echo "⚠️  Warning: main.py not found. The Python bridge may not work correctly."
    echo "   Make sure your Python analysis modules are in the current directory."
fi

if [ ! -f "crypto.py" ]; then
    echo "⚠️  Warning: crypto.py not found. Crypto analysis may not work correctly."
fi

# Build the project
echo "🔨 Building project..."
cargo build --release

if [ $? -eq 0 ]; then
    echo "✅ Build successful!"
else
    echo "❌ Build failed!"
    exit 1
fi

# Run tests
echo "🧪 Running tests..."
cargo test

if [ $? -eq 0 ]; then
    echo "✅ Tests passed!"
else
    echo "❌ Tests failed!"
    exit 1
fi

# Check if config file exists
if [ ! -f "config.toml" ]; then
    echo "📝 Creating default config.toml..."
    cat > config.toml << EOF
[python]
script_path = "."
python_executable = "python3"
modules = ["main", "crypto"]

[api]
yahoo_finance_timeout = 30
finviz_timeout = 30
coingecko_timeout = 30
user_agent = "TradingBot/1.0"

[trading]
default_portfolio_value = 1000.0
default_scaling_factor = 0.5
max_positions = 10
min_allocation = 10.0
max_allocation_per_position = 0.2
risk_free_rate = 0.05
lookback_days = 252

[database]
url = "sqlite:trading_bot.db"
max_connections = 5
EOF
    echo "✅ Created config.toml"
fi

echo ""
echo "🎉 Rust Trading Bot is ready!"
echo ""
echo "📖 Usage examples:"
echo "   # Test Python bridge"
echo "   cargo run -- test-python"
echo ""
echo "   # Run complete analysis"
echo "   cargo run -- analyze --portfolio-value 1000 --scaling-factor 0.5"
echo ""
echo "   # Kelly analysis for specific stock"
echo "   cargo run -- kelly --ticker AAPL --lookback-days 252"
echo ""
echo "   # Options analysis"
echo "   cargo run -- options --ticker TSLA"
echo ""
echo "   # Crypto analysis"
echo "   cargo run -- crypto"
echo ""
echo "📚 For more information, see README_RUST.md"
echo ""

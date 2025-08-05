# reddit_assets

[![Reddit Post](https://github.com/jongan69/reddit_assets/actions/workflows/reddit_post.yml/badge.svg)](https://github.com/jongan69/reddit_assets/actions/workflows/reddit_post.yml)

📘 Introduction: A Unified Risk-Reward Metric for Short-Term Trading

In the world of quantitative finance, measuring the risk-adjusted return of an investment strategy is fundamental. Several established ratios have emerged as leading indicators of performance, each offering a unique lens on volatility, drawdown, and return dynamics. Notably, this research draws theoretical and empirical motivation from the Kelly Criterion, the Calmar Ratio, and the Sortino Ratio—all while taking inspiration from the exceptional track record of the Medallion Fund, managed by Renaissance Technologies.

The goal of this paper is to explore how these concepts can be harmonized into a single composite formula to guide short-term trading strategies across various asset classes. We propose that an intelligent fusion of these metrics may allow for superior capital allocation and better reward-to-risk optimization over shorter time horizons.

⸻

📐 Background: Key Formulas

1. Kelly Criterion

The Kelly Criterion determines the optimal fraction of capital to allocate to a trade to maximize the long-term growth of wealth:

```math
$f^* = \frac{\mu - r}{\sigma^2}
```

Where:
	•	f^* is the optimal fraction of capital to wager
	•	p is the probability of a win
	•	q = 1 - p is the probability of a loss
	•	b is the net odds received on the wager (e.g. 1:1, 2:1, etc.)

For assets with a known expected return \mu and variance \sigma^2, a continuous form is often used:

f^* = \frac{\mu}{\sigma^2}

This version relates closely to the Sharpe Ratio, as we’ll see.

⸻

2. Sharpe Ratio

The Sharpe Ratio measures the risk-adjusted return by comparing excess return to volatility:

\text{Sharpe} = \frac{R_p - R_f}{\sigma_p}

Where:
	•	R_p = portfolio return
	•	R_f = risk-free rate
	•	\sigma_p = standard deviation of portfolio returns

This ratio assumes symmetric volatility and penalizes upside and downside equally.

⸻

3. Sortino Ratio

The Sortino Ratio improves on the Sharpe Ratio by focusing on downside volatility only:

\text{Sortino} = \frac{R_p - R_f}{\sigma_D}

Where \sigma_D is the downside deviation, calculated as:

\sigma_D = \sqrt{ \frac{1}{N} \sum_{i=1}^{N} \min(0, R_i - T)^2 }

	•	T = target return (can be set to 0, or a benchmark)
	•	Penalizes only negative returns, thus better capturing asymmetric risk

⸻

4. Calmar Ratio

The Calmar Ratio emphasizes drawdown risk, useful in trend-following or short-term systems:

\text{Calmar} = \frac{\text{CAGR}}{\text{Max Drawdown}}

Where:
	•	CAGR = Compound Annual Growth Rate
	•	Max Drawdown = Maximum observed portfolio loss from peak to trough

This is particularly useful in short-term or leveraged strategies where drawdowns can be fast and deep.

⸻

🧠 Philosophical and Practical Influence: The Medallion Fund

The Medallion Fund, with average annual returns exceeding 66% before fees, is arguably the most successful hedge fund in history. While its inner workings remain secretive, many researchers believe it applies a scientific, probabilistic, and risk-managed framework:
	•	Position sizing optimized probabilistically (Kelly-like)
	•	Short holding periods with asymmetric risk (Sortino-like)
	•	Aggressive drawdown control and capital preservation (Calmar-like)

This fund’s unparalleled performance inspires us to combine mathematically grounded, yet practical, approaches for achieving high reward per unit of downside risk.
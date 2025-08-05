# reddit_assets

[![Reddit Post](https://github.com/jongan69/reddit_assets/actions/workflows/reddit_post.yml/badge.svg)](https://github.com/jongan69/reddit_assets/actions/workflows/reddit_post.yml)

# 1. Background and Motivation

## 1.1 The Challenge of Balancing Risk and Reward

Short-term trading strategies are notoriously difficult to optimize due to the trade-off between return potential and rapidly compounding risk. In environments characterized by volatility clustering, fat tails, and autocorrelation, traditional reward-based strategies often suffer from uncontrolled drawdowns and inconsistent performance. The need for a systematic, quantitative approach to balancing risk and reward is therefore critical—particularly when aiming to generate **sustained profitability over short time horizons**.

One of the most successful examples of such balance is **Renaissance Technologies' Medallion Fund**, widely regarded as the most successful hedge fund in history. The fund is believed to produce **returns exceeding 60% annualized before fees** with remarkably low drawdowns, leading many to speculate that it employs aggressive but risk-aware strategies grounded in probabilistic modeling and adaptive leverage. While its methods remain proprietary, it is reasonable to assume that some form of **dynamic position sizing**, **risk-adjusted return maximization**, and **drawdown control** underlies its performance. This research draws inspiration from these principles to develop a formulaic trading approach tailored for short-term horizons.

## 1.2 The Kelly Criterion: Optimal Leverage for Growth

The **Kelly Criterion**, introduced by J.L. Kelly in 1956, provides a formula for determining the optimal bet size in repeated probabilistic games to maximize long-term capital growth. In the context of trading, the Kelly fraction for a normally distributed asset return is:

f* = (μ - r_f) / σ²

Where:
- `f*` is the optimal fraction of capital to invest,
- `μ` is the expected return,
- `r_f` is the risk-free rate,
- `σ²` is the variance of returns.

While theoretically elegant, the Kelly Criterion has practical limitations:
- It assumes log-normal returns and stationary distributions.
- It is extremely sensitive to estimation errors in `μ` and `σ`.
- It maximizes **long-term** wealth, often at the cost of **short-term** volatility and drawdowns.

To mitigate these issues, traders often use **fractional Kelly** or modify the formula with risk penalties—a principle we adopt in this research.

## 1.3 The Sortino Ratio: Penalizing Downside Risk

The **Sharpe Ratio**, while widely used for evaluating risk-adjusted returns, treats upside and downside volatility equally—a problematic assumption for most traders. The **Sortino Ratio**, developed as an improvement, focuses only on **downside deviation**:

Sortino Ratio = (R_p - R_f) / σ_d

Where:
- `R_p` is the portfolio return,
- `R_f` is the risk-free rate,
- `σ_d` is the standard deviation of **negative** (downside) returns.

This ratio provides a more accurate view of risk from the trader’s perspective, especially in short-term systems where upside volatility is desirable. As such, it aligns well with Kelly’s philosophy of compounding only **net-positive edge**, while introducing an asymmetric risk control mechanism.

## 1.4 The Calmar Ratio: Drawdown-Aware Risk Assessment

The **Calmar Ratio** is defined as:

Calmar Ratio = Annualized Return / Maximum Drawdown

Unlike volatility-based measures, the Calmar Ratio accounts for **tail risk and path dependency**, making it particularly suitable for evaluating strategies over finite time windows. In short-term trading, avoiding large drawdowns is essential, not just for capital preservation, but to enable **continuous compounding** and maintain **psychological discipline**.

## 1.5 Why Combine These?

Each of these metrics represents a different perspective on risk and reward:

| Metric  | Focus                          | Weakness                                |
|---------|--------------------------------|------------------------------------------|
| Kelly   | Long-term growth               | Sensitive to estimation error            |
| Sortino | Asymmetric risk-adjusted return| Ignores drawdown                         |
| Calmar  | Path-dependent drawdown control| Ignores return volatility & upside       |

We propose a unified approach that **synthesizes these metrics** into a composite formula. The goal is to develop a **position sizing and asset selection model** that maximizes short-term profitability while respecting multiple dimensions of risk.
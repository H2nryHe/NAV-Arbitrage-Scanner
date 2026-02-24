# Risk Notes

## NAV Timing / Staleness Risk
- Premium/discount signals can be overstated or understated when NAV timestamp lags market pricing.
- Rows with lagged NAV should be treated with lower confidence.

## Event Coverage Risk
- Distribution and rebalance events are not guaranteed complete.
- Missing events can cause false positives around mechanical price/NAV moves.

## Borrow / Shortability Risk
- Borrow fee proxy is unavailable in the free-source MVP.
- A candidate may be economically unattractive or untradeable after real borrow checks.

## Liquidity / Slippage Risk
- Dollar volume is a coarse liquidity proxy.
- Real fills depend on spread, order book depth, volatility, and execution style.

## Fund Structure Risk
- Levered CEFs can exhibit nonlinear behavior in stressed markets.
- Expense drag and distribution policy effects can shift expected reversion behavior.

## Model Risk
- Half-life is a simplified mean-reversion heuristic, not a guarantee of timing.
- Short samples can overfit or fail; null half-life should not be forced into ranking.

## Non-Investment-Advice
- This project is a research tool and demonstration artifact, not investment advice.

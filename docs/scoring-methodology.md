# Scoring Methodology

This document records the rationale behind every threshold used by the scoring, credit readiness,
and risk-flagging logic. The prototype favors simple, auditable rules over opaque models (see
"Regulated AI Considerations" in the [README](../README.md)), which means every cutoff must be
traceable to an explicit assumption rather than a fitted parameter. This page is that trace.

Two kinds of thresholds are used, and they carry different weight:

- **Externally anchored**: loosely grounded in widely cited personal-finance heuristics.
- **Internally calibrated**: chosen relative to the synthetic population's own distribution, because
  no general external benchmark applies at monthly granularity. These are explicit design choices,
  not empirical findings, and should be revisited if the prototype is ever pointed at real data.

## Financial Health Score

Implemented in [`scoring.py`](../src/swiss_financial_health/scoring.py).

| Dimension | Metric | good | excellent / poor | Rationale |
| --- | --- | --- | --- | --- |
| Liquidity | reserve months: `sum(income - expense) / avg(expense)` | 1.0 | 3.0 | Reserves accumulated over the observation window (current account plus savings pocket, assuming no opening balance), expressed in months of average spending. Anchored to the common emergency-fund guidance of holding about three months of expenses in liquid savings; one month is the minimum useful cushion. Savings transfers count as reserves, not as outflows (see "Liquidity revision" below). |
| Income stability | coefficient of variation | 0.10 | 0.35 (poor) | No general external benchmark exists at monthly granularity. Calibrated against the synthetic profiles: `stable_saver` has volatility 0.08, `variable_income` has 0.32 (see [`data_generation.py`](../src/swiss_financial_health/data_generation.py)), so the band brackets the designed spread between "stable" and "variable" profiles. |
| Savings capacity | savings rate | 0.10 | 0.25 | Loosely anchored to the widely cited 50/30/20 budgeting rule, which targets ~20% of income toward savings and debt repayment. |
| Debt exposure | debt-to-income | 0.05 | 0.25 (poor) | Swiss mortgage affordability practice commonly caps total debt service near one third of gross income (the "Tragbarkeit" rule of thumb). 25% is set deliberately below that ceiling so the score flags rising debt burden before a user approaches it. |

## Credit Readiness Score

Implemented in [`credit_readiness.py`](../src/swiss_financial_health/credit_readiness.py). Thresholds
are intentionally stricter than the Financial Health Score's, since this signal is meant to gate a
new credit exposure rather than describe current health.

| Dimension | Metric | good | excellent / poor | Rationale |
| --- | --- | --- | --- | --- |
| Income reliability | coefficient of variation | 0.08 | 0.30 (poor) | Tighter than the health-score band above, reflecting that lenders weigh income predictability more heavily than a general wellbeing signal would. Internally calibrated. |
| Debt capacity | debt-to-income | 0.08 | 0.30 (poor) | Same Swiss affordability reasoning as above; the "poor" cutoff sits at the commonly cited ~1/3 affordability ceiling itself, since this score is specifically about capacity for *new* debt. |
| Cashflow resilience | free cashflow / income | 0.05 | 0.22 | Free cashflow (`income - expense`, before savings transfers) as a share of income, because credit readiness is about repayment capacity relative to gross inflows, and savings transfers are voluntary money that could be redirected to a repayment. Internally calibrated. |
| Savings discipline | savings rate | 0.08 | 0.22 | Same 50/30/20 anchor as the health score's savings dimension, narrowed slightly. |
| Spending control | discretionary ratio | 0.16 | 0.34 (poor) | Internally calibrated against the synthetic profiles' discretionary ratios (0.18-0.38 across profiles). |

## Risk Flags

Implemented in [`risk_flags_for_user`](../src/swiss_financial_health/credit_readiness.py). Each flag
reuses the same metrics above but adds a "medium" tier between "healthy" and the credit-readiness
"poor" cutoff, so a user can be warned before they reach the level that suppresses their readiness
score.

| Flag | Medium | High | Notes |
| --- | --- | --- | --- |
| Debt burden | debt-to-income >= 0.18 | >= 0.25 | 0.18 sits between the health score's "poor" (0.25) and the credit score's "poor" (0.30), acting as an early warning band. |
| Variable income | CV >= 0.22 | >= 0.30 | Mirrors the credit readiness "poor" cutoff at the high tier. |
| Cashflow buffer | free cashflow ratio < 0.05 | < 0 (negative) | Negative free cashflow means spending exceeds income outright. |
| Savings discipline | savings rate < 0.05 | - | Single tier; below half the health score's "good" cutoff (0.10). |
| Discretionary spend | ratio >= 0.32 | - | Single tier; set just below the credit score's "poor" cutoff (0.34) so it fires slightly earlier as a warning. |

## Liquidity revision

The first version measured liquidity as `net_cashflow / expense`, where net cashflow is what remains
*after* savings transfers. Because the synthetic customers route most of their surplus to savings,
that ratio never reached the 0.25 "good" cutoff and **the liquidity score was 0 for all 150 users**:
30% of the Financial Health Score carried no information, and the users who saved the most were told
to "build a cash buffer". The same after-savings figure also drove cashflow resilience, the cashflow
risk flag and the loan simulator, so a customer saving a quarter of their income looked like they had
almost no repayment capacity.

The revision treats savings transfers as reserves the customer still holds rather than as spending:

- `free_cashflow = income - expense` is used for cashflow resilience, the cashflow risk flag and the
  loan simulator.
- Liquidity becomes a stock measure, *reserve months*, anchored to emergency-fund guidance.

Effect on the demo population (segment medians of the Financial Health Score): Stable saver 98.6,
Variable income 60.8, Balanced user 46.5, High discretionary 36.3, Debt pressure 16.5. The ordering now
matches the behavioural story of each segment. The K-Means segments are unchanged because the
clustering features do not include liquidity.

Trade-off: with flow-only synthetic data, reserve months and the savings rate are highly correlated
(both derive from the same monthly surplus), so the two dimensions overlap. With real data, liquidity
should be computed from actual current-account and savings balances, which would make it an
independent signal.

## Known limitation

None of these thresholds have been validated against real transaction data or a labeled outcome
(e.g., actual defaults or missed payments). They are defensible starting assumptions for a synthetic,
educational prototype, not calibrated risk parameters. Any production use would require re-deriving
them from real, consented data and validating against actual repayment outcomes.

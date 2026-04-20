# Stochastic Calculus Validation

Generated on: **2026-04-20**

## Stochastic Model

Validation is built on a regime-switching jump-diffusion process:

$$
dS_t = \mu_{r_t} S_t \, dt + \sigma_{r_t} S_t \, dW_t + S_t (e^{J_t} - 1) \, dN_t
$$

where $r_t$ is a Markov regime state, $W_t$ is Brownian motion, and $N_t$ is a Poisson jump process.

Estimated annualized parameters from historical returns:

| Parameter | Value |
| :--- | ---: |
| Historical drift $\mu$ | +0.1773 |
| Historical volatility $\sigma$ | 0.5832 |
| Jump intensity $\lambda$ | 11.3120 |
| Jump mean $E[J]$ | +0.00492 |
| Jump std $\sigma_J$ | 0.10539 |

Regime annualized drifts and vols:

| Regime | Drift | Volatility |
| :--- | ---: | ---: |
| 0 | +0.1598 | 0.3444 |
| 1 | -0.0573 | 0.5261 |
| 2 | +0.4220 | 0.7859 |

## Monte Carlo Setup

- Paths: `220`
- Horizon: `180` days
- Cost model: `15.00` bps per side
- Debt carry: `10.00%` annual

## Model Robustness Under Stochastic Paths

| Model | Paths | Mean Return | Std Return | VaR 95% | CVaR 95% | Mean Sharpe | Mean Max DD | Worst DD | P(Return>0) | P(Beat BnH) | Mean Trades |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| legacy_cooldown3_baseline | 220 | +2.96% | 11.87% | -16.24% | -22.57% | 0.503 | -11.33% | -29.19% | 61.82% | 55.91% | 14.2 |
| production_legacy_cooldown1 | 220 | +2.87% | 12.62% | -19.39% | -25.47% | 0.522 | -11.94% | -36.63% | 61.36% | 56.82% | 17.4 |
| advanced_adaptive_research | 220 | +2.65% | 19.70% | -19.57% | -23.71% | 0.085 | -18.91% | -42.01% | 42.73% | 44.09% | 153.7 |
| legacy_confidence_research | 220 | +1.53% | 6.57% | -8.56% | -11.31% | 0.403 | -6.18% | -18.55% | 55.91% | 53.18% | 25.7 |

## Sensitivity Surface

The 3D surface maps expected production-model return as drift and volatility are jointly perturbed.

| Drift Scale | Vol Scale | Mean Return | Median Return | Mean Max DD |
| ---: | ---: | ---: | ---: | ---: |
| 0.60 | 0.70 | +1.94% | +3.08% | -5.04% |
| 0.60 | 0.88 | +1.99% | +2.96% | -6.99% |
| 0.60 | 1.07 | +0.85% | +4.86% | -9.42% |
| 0.60 | 1.25 | +1.21% | +3.87% | -10.27% |
| 0.60 | 1.43 | +2.07% | +5.25% | -12.62% |
| 0.60 | 1.62 | +5.45% | +9.84% | -13.06% |
| 0.60 | 1.80 | +8.40% | +11.45% | -14.46% |
| 0.75 | 0.70 | +0.93% | +3.04% | -5.09% |
| 0.75 | 0.88 | +0.24% | +2.50% | -8.19% |
| 0.75 | 1.07 | +0.87% | +2.84% | -9.78% |
| 0.75 | 1.25 | +1.02% | +4.83% | -11.88% |
| 0.75 | 1.43 | +2.80% | +5.91% | -13.23% |
| 0.75 | 1.62 | +2.37% | +7.23% | -15.18% |
| 0.75 | 1.80 | +1.20% | -0.58% | -18.00% |
| 0.90 | 0.70 | +1.86% | +3.38% | -4.84% |
| 0.90 | 0.88 | -0.72% | +2.04% | -8.37% |
| 0.90 | 1.07 | +1.85% | +3.64% | -9.39% |
| 0.90 | 1.25 | +2.06% | +3.33% | -11.13% |
| 0.90 | 1.43 | +2.32% | +6.90% | -12.15% |
| 0.90 | 1.62 | +1.40% | +6.80% | -15.34% |
| 0.90 | 1.80 | +5.99% | +11.84% | -15.48% |
| 1.05 | 0.70 | +0.76% | +2.96% | -5.90% |
| 1.05 | 0.88 | +1.20% | +3.42% | -6.54% |
| 1.05 | 1.07 | +2.68% | +4.78% | -8.18% |
| 1.05 | 1.25 | +0.29% | +3.71% | -11.27% |
| 1.05 | 1.43 | +3.52% | +7.83% | -12.10% |
| 1.05 | 1.62 | -0.06% | +1.10% | -15.86% |
| 1.05 | 1.80 | +3.07% | +9.32% | -17.95% |
| 1.20 | 0.70 | +1.68% | +2.83% | -5.07% |
| 1.20 | 0.88 | +1.23% | +2.92% | -6.79% |
| 1.20 | 1.07 | +2.94% | +5.08% | -7.37% |
| 1.20 | 1.25 | +1.08% | +3.49% | -11.54% |
| 1.20 | 1.43 | +3.32% | +4.19% | -11.93% |
| 1.20 | 1.62 | -0.91% | +0.93% | -14.41% |
| 1.20 | 1.80 | +1.53% | +7.00% | -18.00% |
| 1.35 | 0.70 | +1.57% | +3.07% | -5.05% |
| 1.35 | 0.88 | +1.87% | +2.89% | -7.14% |
| 1.35 | 1.07 | +1.52% | +4.31% | -8.17% |
| 1.35 | 1.25 | +2.27% | +4.43% | -9.88% |
| 1.35 | 1.43 | +3.66% | +7.30% | -12.44% |
| 1.35 | 1.62 | +6.00% | +9.04% | -12.21% |
| 1.35 | 1.80 | +7.83% | +9.41% | -14.44% |
| 1.50 | 0.70 | +2.59% | +2.91% | -4.47% |
| 1.50 | 0.88 | +1.88% | +3.62% | -6.66% |
| 1.50 | 1.07 | +1.81% | +3.28% | -8.72% |
| 1.50 | 1.25 | +4.61% | +8.08% | -9.15% |
| 1.50 | 1.43 | +5.43% | +10.14% | -11.56% |
| 1.50 | 1.62 | +4.40% | +6.45% | -12.37% |
| 1.50 | 1.80 | +2.05% | +1.27% | -16.36% |

## Figures

- Fan chart: `reports/stochastic/figures/stochastic_fan_chart.html`
- 3D surface: `reports/stochastic/figures/stochastic_surface_3d.html`
- 3D scatter: `reports/stochastic/figures/stochastic_scatter_3d.html`
- Regime heatmap: `reports/stochastic/figures/regime_transition_heatmap.html`

## Notes

- Synthetic features are rebuilt path-by-path, then scored and executed by the same strategy code used in backtests.
- Results are scenario evidence and should be combined with walk-forward gate decisions before production promotion.
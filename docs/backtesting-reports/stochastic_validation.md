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
- White Reality Check bootstraps: `3000`
- Bayesian posterior draws (beat probability): `30000`

## Model Robustness Under Stochastic Paths

| Scenario | Model | Paths | Mean Return | VaR 95% | CVaR 95% | Mean Sharpe | Mean Max DD | P(Beat BnH) | Bayesian 95% CI | Mean Trades |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- | ---: |
| regime_jump | legacy_cooldown3_baseline | 220 | +2.96% | -16.24% | -22.57% | 0.503 | -11.33% | 55.91% | [49.34%, 62.25%] | 14.2 |
| regime_jump | production_legacy_cooldown1 | 220 | +2.87% | -19.39% | -25.47% | 0.522 | -11.94% | 56.82% | [50.17%, 63.22%] | 17.4 |
| regime_jump | advanced_adaptive_research | 220 | +2.10% | -13.95% | -20.36% | 0.607 | -9.25% | 54.09% | [47.41%, 60.51%] | 135.4 |
| regime_jump | legacy_confidence_research | 220 | +1.53% | -8.56% | -11.31% | 0.403 | -6.18% | 53.18% | [46.57%, 59.66%] | 25.7 |
| heston_jump | legacy_cooldown3_baseline | 140 | +4.52% | -22.40% | -25.57% | 0.764 | -11.01% | 45.00% | [37.02%, 53.35%] | 14.0 |
| heston_jump | production_legacy_cooldown1 | 140 | +4.23% | -22.21% | -27.66% | 0.758 | -11.47% | 47.14% | [39.03%, 55.40%] | 16.8 |
| heston_jump | advanced_adaptive_research | 140 | +2.43% | -21.37% | -27.92% | 0.787 | -9.24% | 46.43% | [38.38%, 54.64%] | 126.8 |
| heston_jump | legacy_confidence_research | 140 | +2.33% | -10.30% | -12.82% | 0.640 | -5.91% | 41.43% | [33.61%, 49.74%] | 24.9 |

## Heston Expansion Scenario

Roadmap upgrade: stochastic-volatility (Heston-style) with jumps, for model-risk stress under volatility-of-volatility.

| Scenario | Model | Mean Return | VaR 95% | Mean Sharpe | Mean Max DD | P(Beat BnH) |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: |
| heston_jump | legacy_cooldown3_baseline | +4.52% | -22.40% | 0.764 | -11.01% | 45.00% |
| heston_jump | production_legacy_cooldown1 | +4.23% | -22.21% | 0.758 | -11.47% | 47.14% |
| heston_jump | advanced_adaptive_research | +2.43% | -21.37% | 0.787 | -9.24% | 46.43% |
| heston_jump | legacy_confidence_research | +2.33% | -10.30% | 0.640 | -5.91% | 41.43% |

## Multiple-Testing Control (White RC + Holm)

White Reality Check-style bootstrap tests were applied to model alpha vs Buy and Hold, with Holm-Bonferroni correction across candidates.

| Scenario | Comparison | Mean Alpha | White RC p-value | Holm-adjusted p-value | Reject at 5% |
| :--- | :--- | ---: | ---: | ---: | :---: |
| heston_jump | advanced_adaptive_research vs buy_and_hold | -21.791% | 1.00000 | 1.00000 | False |
| heston_jump | legacy_confidence_research vs buy_and_hold | -21.882% | 1.00000 | 1.00000 | False |
| heston_jump | legacy_cooldown3_baseline vs buy_and_hold | -19.694% | 1.00000 | 1.00000 | False |
| heston_jump | production_legacy_cooldown1 vs buy_and_hold | -19.987% | 1.00000 | 1.00000 | False |
| regime_jump | advanced_adaptive_research vs buy_and_hold | -9.309% | 0.99633 | 1.00000 | False |
| regime_jump | legacy_confidence_research vs buy_and_hold | -9.880% | 0.99733 | 1.00000 | False |
| regime_jump | legacy_cooldown3_baseline vs buy_and_hold | -8.449% | 0.99500 | 1.00000 | False |
| regime_jump | production_legacy_cooldown1 vs buy_and_hold | -8.537% | 0.99567 | 1.00000 | False |

## Factor Attribution (Cross-Sectional)

Cross-sectional regressions decompose path-level return dispersion by score factors. Risk share is a normalized proxy based on coefficient-scaled factor volatility.

| Scenario | Model | Factor | Beta | Alpha Contribution | Risk Share | Model R2 |
| :--- | :--- | :--- | ---: | ---: | ---: | ---: |
| heston_jump | advanced_adaptive_research | reversion_mean | +409.65207 | +86.5423% | 42.44% | 0.680 |
| heston_jump | advanced_adaptive_research | trend_mean | -204.14159 | -42.5895% | 31.22% | 0.680 |
| heston_jump | advanced_adaptive_research | risk_mean | -507.54260 | -28.0189% | 11.88% | 0.680 |
| heston_jump | advanced_adaptive_research | regime_mean | -75.51705 | +9.3947% | 5.99% | 0.680 |
| heston_jump | advanced_adaptive_research | macro_mean | +742.86885 | +85.0522% | 2.67% | 0.680 |
| heston_jump | advanced_adaptive_research | valuation_mean | +34.85430 | +2.3583% | 2.31% | 0.680 |
| heston_jump | advanced_adaptive_research | momentum_mean | +37.36584 | -0.6910% | 2.18% | 0.680 |
| heston_jump | advanced_adaptive_research | uncertainty_mean | +135.65138 | +89.2700% | 1.30% | 0.680 |
| heston_jump | legacy_confidence_research | reversion_mean | +106.80302 | +22.5630% | 30.98% | 0.634 |
| heston_jump | legacy_confidence_research | trend_mean | -52.02994 | -10.8549% | 22.28% | 0.634 |
| heston_jump | legacy_confidence_research | risk_mean | -303.66215 | -16.7637% | 19.91% | 0.634 |
| heston_jump | legacy_confidence_research | momentum_mean | -92.84657 | +1.7169% | 15.20% | 0.634 |
| heston_jump | legacy_confidence_research | valuation_mean | -24.97052 | -1.6896% | 4.64% | 0.634 |
| heston_jump | legacy_confidence_research | regime_mean | -15.34473 | +1.9090% | 3.41% | 0.634 |
| heston_jump | legacy_confidence_research | macro_mean | -279.50089 | -32.0005% | 2.81% | 0.634 |
| heston_jump | legacy_confidence_research | uncertainty_mean | +28.85197 | +18.9870% | 0.77% | 0.634 |
| heston_jump | legacy_cooldown3_baseline | reversion_mean | +140.33526 | +29.6470% | 28.42% | 0.740 |
| heston_jump | legacy_cooldown3_baseline | risk_mean | -481.24169 | -26.5670% | 22.03% | 0.740 |
| heston_jump | legacy_cooldown3_baseline | trend_mean | -63.17181 | -13.1794% | 18.89% | 0.740 |
| heston_jump | legacy_cooldown3_baseline | momentum_mean | -146.55610 | +2.7101% | 16.75% | 0.740 |
| heston_jump | legacy_cooldown3_baseline | macro_mean | -644.23427 | -73.7594% | 4.52% | 0.740 |
| heston_jump | legacy_cooldown3_baseline | valuation_mean | -34.66366 | -2.3454% | 4.50% | 0.740 |
| heston_jump | legacy_cooldown3_baseline | regime_mean | -27.06708 | +3.3673% | 4.20% | 0.740 |
| heston_jump | legacy_cooldown3_baseline | uncertainty_mean | +36.74157 | +24.1790% | 0.69% | 0.740 |
| heston_jump | production_legacy_cooldown1 | reversion_mean | +133.43327 | +28.1889% | 25.80% | 0.717 |
| heston_jump | production_legacy_cooldown1 | risk_mean | -506.76692 | -27.9761% | 22.15% | 0.717 |
| heston_jump | production_legacy_cooldown1 | trend_mean | -66.64060 | -13.9030% | 19.03% | 0.717 |
| heston_jump | production_legacy_cooldown1 | momentum_mean | -160.52517 | +2.9684% | 17.52% | 0.717 |
| heston_jump | production_legacy_cooldown1 | valuation_mean | -63.44481 | -4.2928% | 7.86% | 0.717 |
| heston_jump | production_legacy_cooldown1 | macro_mean | -742.57001 | -85.0180% | 4.98% | 0.717 |
| heston_jump | production_legacy_cooldown1 | regime_mean | +12.02242 | -1.4956% | 1.78% | 0.717 |
| heston_jump | production_legacy_cooldown1 | uncertainty_mean | +49.84061 | +32.7993% | 0.89% | 0.717 |
| regime_jump | advanced_adaptive_research | reversion_mean | +369.40372 | +93.0337% | 43.60% | 0.574 |
| regime_jump | advanced_adaptive_research | trend_mean | -185.73857 | -49.2257% | 33.05% | 0.574 |
| regime_jump | advanced_adaptive_research | risk_mean | -393.61628 | -26.1999% | 10.87% | 0.574 |
| regime_jump | advanced_adaptive_research | regime_mean | -57.11256 | +4.5840% | 5.31% | 0.574 |
| regime_jump | advanced_adaptive_research | macro_mean | +580.42661 | +67.6585% | 2.64% | 0.574 |
| regime_jump | advanced_adaptive_research | momentum_mean | +39.00446 | -2.1529% | 2.64% | 0.574 |
| regime_jump | advanced_adaptive_research | valuation_mean | +12.81858 | +1.3794% | 1.00% | 0.574 |
| regime_jump | advanced_adaptive_research | uncertainty_mean | +79.42765 | +52.4382% | 0.90% | 0.574 |
| regime_jump | legacy_confidence_research | reversion_mean | +93.05625 | +23.4361% | 31.05% | 0.596 |
| regime_jump | legacy_confidence_research | trend_mean | -41.06496 | -10.8833% | 20.65% | 0.596 |
| regime_jump | legacy_confidence_research | risk_mean | -243.07527 | -16.1796% | 18.97% | 0.596 |
| regime_jump | legacy_confidence_research | momentum_mean | -72.19241 | +3.9848% | 13.81% | 0.596 |
| regime_jump | legacy_confidence_research | regime_mean | -31.11035 | +2.4970% | 8.17% | 0.596 |
| regime_jump | legacy_confidence_research | macro_mean | -291.86637 | -34.0219% | 3.75% | 0.596 |
| regime_jump | legacy_confidence_research | valuation_mean | -10.02771 | -1.0791% | 2.20% | 0.596 |
| regime_jump | legacy_confidence_research | uncertainty_mean | +43.16008 | +28.4943% | 1.39% | 0.596 |
| regime_jump | legacy_cooldown3_baseline | reversion_mean | +191.47143 | +48.2217% | 37.30% | 0.659 |
| regime_jump | legacy_cooldown3_baseline | trend_mean | -86.20995 | -22.8480% | 25.31% | 0.659 |
| regime_jump | legacy_cooldown3_baseline | risk_mean | -395.09941 | -26.2986% | 18.00% | 0.659 |
| regime_jump | legacy_cooldown3_baseline | momentum_mean | -69.97024 | +3.8621% | 7.82% | 0.659 |
| regime_jump | legacy_cooldown3_baseline | regime_mean | -44.21514 | +3.5488% | 6.78% | 0.659 |
| regime_jump | legacy_cooldown3_baseline | macro_mean | -404.78789 | -47.1848% | 3.04% | 0.659 |
| regime_jump | legacy_cooldown3_baseline | valuation_mean | -10.63440 | -1.1443% | 1.36% | 0.659 |
| regime_jump | legacy_cooldown3_baseline | uncertainty_mean | +20.68141 | +13.6539% | 0.39% | 0.659 |
| regime_jump | production_legacy_cooldown1 | reversion_mean | +194.77116 | +49.0528% | 36.11% | 0.628 |
| regime_jump | production_legacy_cooldown1 | trend_mean | -88.83732 | -23.5443% | 24.83% | 0.628 |
| regime_jump | production_legacy_cooldown1 | risk_mean | -439.42766 | -29.2492% | 19.06% | 0.628 |
| regime_jump | production_legacy_cooldown1 | momentum_mean | -83.16999 | +4.5907% | 8.84% | 0.628 |
| regime_jump | production_legacy_cooldown1 | regime_mean | -35.28210 | +2.8318% | 5.15% | 0.628 |
| regime_jump | production_legacy_cooldown1 | macro_mean | -414.32961 | -48.2971% | 2.96% | 0.628 |
| regime_jump | production_legacy_cooldown1 | valuation_mean | -19.52602 | -2.1012% | 2.38% | 0.628 |
| regime_jump | production_legacy_cooldown1 | uncertainty_mean | +37.68376 | +24.8789% | 0.67% | 0.628 |

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
- Heston fan chart: `reports/stochastic/figures/stochastic_heston_fan_chart.html`
- 3D surface: `reports/stochastic/figures/stochastic_surface_3d.html`
- 3D scatter: `reports/stochastic/figures/stochastic_scatter_3d.html`
- Regime heatmap: `reports/stochastic/figures/regime_transition_heatmap.html`

## Notes

- Synthetic features are rebuilt path-by-path, then scored and executed by the same strategy code used in backtests.
- Bayesian credible intervals quantify uncertainty in outperform probability vs Buy and Hold.
- White RC + Holm adjustment control data-mining bias across multiple candidate models.
- Results are scenario evidence and should be combined with walk-forward gate decisions before production promotion.
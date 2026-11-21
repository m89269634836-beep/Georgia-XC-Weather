# XC v3: Can antecedent weather patterns predict actual route distance?

Training days 2024–2025: 71. Held-out site/days 2026: 46.

**Retrospective hypothesis test only:** past-day ERA5 is not available by departure day at fixed lead (5d latency).

| XC target | Site/season MAE | Day-0 analog MAE | 5-day analog MAE | Gain 5-day vs day-only | 95% date bootstrap interval |
|---|---:|---:|---:|---:|---|
| q75_route_km | 26.17 km | 27.3 km | 28.86 km | -1.56 km | [-3.78, 0.62] km |
| median_route_km | 21.31 km | 21.92 km | 22.88 km | -0.96 km | [-3.13, 1.21] km |

Interpretation: positive improvement is better. A 95% interval crossing zero does NOT establish gain. Only route distances from days that have at least two published flights appear in training.
Live forecast prediction must use as-available day−5..day−1 history and the issued D0 forecast, never reanalysis known days later.
Without no-flight or failed-launch observations this cannot certify flight safety, and will not predict probability that a good XC day occurs among *all* calendar days.

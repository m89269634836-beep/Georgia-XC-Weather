# Georgia XC v2 — forecasts conditioned on observations

Issued: 2026-11-24T12:54:18.070006+00:00 UTC

**These are NOT safe-to-fly or all-day flyability probabilities.**

Only registered sites with >=15 historical site-days and lead D−1 get experimental conditional-to-flight proxies.

**Current validation outcome:** weather adjustments are only active if 2026 holdout data show a statistically supported improvement. When none are activated, the percentages below are **historical site-season references**, NOT day-specific weather predictions.

| Start | D−1 wind 10m FROM | Normal component | Ridge pattern | Thermal pattern | Low cloud | Gusts |
|---|---|---:|---:|---:|---:|---:|
| Лалискури | 4.0 m/s @298° | 1.89 | 0% | 13% | 36.5% | 12.5 m/s |
| Гудаури район | 1.2 m/s @247° | — | 6% | 11% | 67.83% | 8.9 m/s |

The percentages represent expected fraction of tracks showing a **heuristic signature conditioned on a flight**, NOT percentage chance of flying. Models without clear holdout weather improvement default to site/season baseline.

Untrained candidates (Kaspi, Sagarejo, etc.) retain meteorological/terrain diagnostics but no calibrated probability. All forecasts and uncertainties: [JSON](xc_v2_live_diagnostics.json).
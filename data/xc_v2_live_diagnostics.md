# Georgia XC v2 — forecasts conditioned on observations

Issued: 2026-11-22T10:13:11.407157+00:00 UTC

**These are NOT safe-to-fly or all-day flyability probabilities.**

Only registered sites with >=15 historical site-days and lead D−1 get experimental conditional-to-flight proxies.

**Current validation outcome:** weather adjustments are only active if 2026 holdout data show a statistically supported improvement. When none are activated, the percentages below are **historical site-season references**, NOT day-specific weather predictions.

| Start | D−1 wind 10m FROM | Normal component | Ridge pattern | Thermal pattern | Low cloud | Gusts |
|---|---|---:|---:|---:|---:|---:|
| Лалискури | 1.0 m/s @54° | 0.59 | 0% | 13% | 0.67% | 5.0 m/s |
| Гудаури район | 0.9 m/s @229° | — | 6% | 11% | 4.0% | 6.2 m/s |

The percentages represent expected fraction of tracks showing a **heuristic signature conditioned on a flight**, NOT percentage chance of flying. Models without clear holdout weather improvement default to site/season baseline.

Untrained candidates (Kaspi, Sagarejo, etc.) retain meteorological/terrain diagnostics but no calibrated probability. All forecasts and uncertainties: [JSON](xc_v2_live_diagnostics.json).
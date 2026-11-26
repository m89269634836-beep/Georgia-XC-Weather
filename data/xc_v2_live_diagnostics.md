# Georgia XC v2 — forecasts conditioned on observations

Issued: 2026-11-26T11:26:46.235637+00:00 UTC

**These are NOT safe-to-fly or all-day flyability probabilities.**

Only registered sites with >=15 historical site-days and lead D−1 get experimental conditional-to-flight proxies.

**Current validation outcome:** weather adjustments are only active if 2026 holdout data show a statistically supported improvement. When none are activated, the percentages below are **historical site-season references**, NOT day-specific weather predictions.

| Start | D−1 wind 10m FROM | Normal component | Ridge pattern | Thermal pattern | Low cloud | Gusts |
|---|---|---:|---:|---:|---:|---:|
| Лалискури | 1.0 m/s @58° | 0.52 | 0% | 13% | 0.17% | 4.9 m/s |
| Гудаури район | 0.7 m/s @147° | — | 6% | 11% | 27.67% | 6.9 m/s |

The percentages represent expected fraction of tracks showing a **heuristic signature conditioned on a flight**, NOT percentage chance of flying. Models without clear holdout weather improvement default to site/season baseline.

Untrained candidates (Kaspi, Sagarejo, etc.) retain meteorological/terrain diagnostics but no calibrated probability. All forecasts and uncertainties: [JSON](xc_v2_live_diagnostics.json).
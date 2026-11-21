# Georgia XC Weather v2: actual GPS tracks + as-issued weather (2026-11-21)

## Goal
Improve Georgian paragliding **ridge soaring** and **thermal** planning using real past flights and the weather forecast that was available before the flight, keeping these physical processes distinct. This is research into predicting *outcomes conditional on a flight*, not proof that any day is safe or flyable.

## Ground truth and publication privacy
- User-provided XContest archive: 1,012 JSON flight traces, ~6.68 million decoded GPS points; 1,010 traces with valid time consistency.
- 332 start/day groupings; 197 groupings from 2024 onward.
- Public training labels contain **116 multi-flight site/day groupings (499 flights)**, while retaining private individual route, pilot, glider and flight IDs only in a local downloadable report. No raw GPS routes in this repository.
- Labels: ridge-like shuttle/near-ridge duration, circling-climb-like signature, sustained local holding fraction. They are **GPS behavior signatures**, not verified meteorological lift classification.
- Date/site sample is affected by pilot choice, launch face, day of week, glider performance and voluntary publication.

## What was actually executed and checked
- Source: Open-Meteo Previous Runs, specifically `models=ecmwf_ifs025`, 24h and 48h fixed prior forecast for each target day, local 11:00-16:00 Asia/Tbilisi.
- Date-matched 116/116 multi-flight site-days successfully, in **29/29 quarterly requests** with zero errors. Wind at 10m and 80m, humidity, temperature, solar shortwave, total cloud, precipitation. Low cloud and gusts missing in historical archive requests are excluded, not filled as observations.
- Trained on 71 days from 2024–2025; validation held out 45 days in 2026.
- Pre-specified ridge regression with ridge regularization `alpha=15` and site/month baselines versus weather features.
- Bootstrapped improvement by date. Rejects all adjusted regressions if 95% confidence interval spans zero or MAE gain <=0.005.

| Outcome (0-1 conditional GPS measure) | Site+season baseline MAE | Baseline + as-issued weather MAE | Result |
|---|---:|---:|---|
| Ridge-like shuttle rate | **0.0904** | 0.0894 | Difference not significant, reject adjustment |
| Thermal-like circling rate | **0.1606** | 0.1765 | Weather worse, reject adjustment |
| Staying near launch | **0.1973** | 0.2212 | Weather worse, reject adjustment |

**Weather regressions are NOT deployed as a proven forecast improvement. All three selected daily-score models are currently site/season baselines.** Daily weather is displayed separately as *raw model diagnostics* with winds/gusts and hazards.

Data/code:
- `data/xc_v2_multiflight_daily_labels_2024_2026.csv.gz.b64`: minimal public outcome aggregates
- `scripts/learning/fetch_issued_forecasts.py`, `data/xc_v2_issued_forecast_features.csv`: historic prior-run features
- `data/xc_v2_weather_fetch_status.json`: 116/116 status
- `scripts/learning/train_conditional_v2.py`, `data/xc_v2_validation_report.md`: out-of-sample protocol and results
- `data/xc_v2_model.json`: coefficients for site/month baseline and rejected alternatives
- `scripts/learning/predict_live_v2.py`, `data/xc_v2_live_diagnostics.json`: updated live diagnostics for D-1, only at sites with 15+ historic site-days. All other sites have weather observations, not trained probabilities.
- `.github/workflows/xc-v2-issued-weather.yml`, `.github/workflows/xc-v2-train.yml`, `.github/workflows/xc-v2-live.yml`: historical archive, year-split training, scheduled daily diagnostics.

## Important limitations
1. **No negative labels.** A day without a published flight is not proof that flight was impossible; no binary flyable-day probability can be trained from this archive alone.
2. **Very little winter ridge ground truth:** only 49 flight tracks across Nov–Feb among all 1,012 spanning 2013–2026. Published summer flights should not be uncritically transferred to winter ridge conditions.
3. Wind from the GFS/IFS coarse grid is not local gorge or ridge wind. ICON-EU point forecasts and 11 actual static WindNinja CFD-lite mass-conserving scenarios exist, but must be integrated with precise launch faces and validated against field observations.
4. “More wind” is **not** inherently a negative for dynamic soaring, only wind in the lee, excessive gusting, rotor or unsuitable face is a problem. Score only wind **normal to the verified windward face**; never apply one global speed cap as a flight rating.
5. Use actual IGC logs / 1Hz GPS with reliable clock for segment-level lift inference. XContest JSON can be sampled/thinned and does not prove exact source of lift.

## Required physical and observational upgrade
- Identify exact launch face bearings, along-valley axis, ridge continuity, landing and obstacles for each site; represent multiple Gudauri/Mestia launch faces separately.
- Use full hourly ICON-EU / ECMWF, surface 10/80m wind, winds at 100-300m AGL and topographic exposure, stable layers, gusts, and weather trend between successive runs (D-2 vs D-1).
- WindNinja: initialize a site-specific spatial calculation with the actual model wind and digital terrain, not hypothetical constant direction/speed; validate residuals against local stations/flight experiments. Mass-conserving mode alone cannot resolve lee rotors.
- Obtain voluntary unsuccessful outing/no-flight observations, local sensor measurements, and wind direction near launch. These are needed before learning a probability that *any day* is actually flyable.
- Hold out future dates or full weeks per site when validating. Track non-flight observations separate from flights.

## Reporting safety
All heights AMSL, wind meteorological FROM. Model diagnostics do not supersede local anemometer, airspace/NOTAM, site inspection or a pilot's decision.

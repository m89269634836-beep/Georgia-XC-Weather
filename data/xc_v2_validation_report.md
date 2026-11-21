# Georgia XC v2: held-out year weather validation

**Scope:** *conditional quality of published flights*, not safe flyability or presence of flyable weather.

D-1 forecasts matched: 116/116 site-days, train 2024–25: 71, test 2026: 45.

| Track-derived target | Site/month MAE | + Weather MAE | Weather gain | Date-bootstrap 95% CI | Deployed |
|---|---:|---:|---:|---|---|
| ridge_signature_rate | 0.090 | 0.089 | +0.001 | [-0.0099, 0.0109] | baseline |
| thermal_signature_rate | 0.161 | 0.176 | -0.016 | [-0.036, 0.0083] | baseline |
| local_hold_proxy | 0.197 | 0.221 | -0.024 | [-0.0426, -0.0038] | baseline |

Weather correction is activated only for a date-held-out positive improvement with 95% bootstrap CI above zero. All other outcomes keep the climatological baseline.
A GPS shuttle is a *ridge-like signature*, not direct measurement of slope lift. No absence-of-flight negatives. No rotor or airspace clearance.

"""Conditional flight-quality model. Not a probability that a day is safe/flyable.

Use D-1 historical ECMWF forecasts issued before valid time; strictly train on
2024-2025 and validate 2026. Never use the absence of a track as a negative.
"""
import base64,gzip,io,json,math
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error
OUT=Path("data")
labels=pd.read_csv(io.BytesIO(gzip.decompress(base64.b64decode(
    (OUT/"xc_v2_multiflight_daily_labels_2024_2026.csv.gz.b64").read_text().strip()))))
weather=pd.read_csv(OUT/"xc_v2_issued_forecast_features.csv")
allrows=labels.merge(weather,on=["site","date"],how="left",validate="one_to_one")
allrows["year"]=allrows.date.str[:4].astype(int)
allrows["month"]=allrows.date.str[5:7].astype(int)
allrows["ridge_target"]=allrows.n_ridge_signatures/allrows.n_flights
allrows["thermal_target"]=allrows.n_thermal_signatures/allrows.n_flights
allrows["hold_target"]=allrows.local_soaring_proxy.clip(0,1)
allrows.to_csv(OUT/"xc_v2_training_joined.csv",index=False)
data=allrows[allrows.d1_wind10_ms.notna()].copy()
if len(data)<30:raise SystemExit("Too few real archived prior-run forecasts: "+str(len(data)))
for level in ("10","80"):
 s=pd.to_numeric(data[f"d1_wind{level}_ms"],errors="coerce")
 d=np.deg2rad(pd.to_numeric(data[f"d1_wind{level}_from_deg"],errors="coerce"))
 data[f"wx{level}"]=s*np.sin(d)
 data[f"wy{level}"]=s*np.cos(d)
data["season_sin"]=np.sin(2*np.pi*data.month/12)
data["season_cos"]=np.cos(2*np.pi*data.month/12)
sites=sorted(data.site.unique())
for site in sites:data["site_"+site]=(data.site==site).astype(float)
base=["site_"+site for site in sites]+["season_sin","season_cos"]
weather_features=["d1_wind10_ms","wx10","wy10","d1_wind80_ms","wx80","wy80",
 "d1_sun_wm2","d1_cloud_pct","d1_low_cloud_pct","d1_rain_11_16_mm",
 "d1_temp_c","d1_rh_pct","d1_gust10_max_ms"]
trmask=data.year<=2025
temask=data.year==2026
if trmask.sum()<25 or temask.sum()<10:raise SystemExit("Not enough year-separated data")
# Omit variables missing on >35% of historical training cases; do not fabricate them.
weather_features=[c for c in weather_features if data.loc[trmask,c].notna().mean()>=.65]
means={c:float(data.loc[trmask,c].median()) for c in weather_features}
stds={c:max(1e-8,float(data.loc[trmask,c].std())) for c in weather_features}
for c in weather_features:
 data[c]=((data[c].fillna(means[c])-means[c])/stds[c]).clip(-8,8)
features=base+weather_features
X0=data[base].to_numpy(dtype=float)
X1=data[features].to_numpy(dtype=float)
tr=np.flatnonzero(trmask.to_numpy());te=np.flatnonzero(temask.to_numpy())
w=np.sqrt(data.n_flights.clip(upper=6).to_numpy(dtype=float))
targets={"ridge_signature_rate":"ridge_target","thermal_signature_rate":"thermal_target",
         "local_hold_proxy":"hold_target"}
report={"n_cases_from_traces":len(labels),"n_weather_matched":len(data),
 "n_training_2024_25":int(len(tr)),"n_test_2026":int(len(te)),
 "data_model":"Open-Meteo previous runs ECMWF IFS 0.25 D-1 (fixed validity lead)",
 "inputs_weather":weather_features,
 "sites":{k:int(v) for k,v in data.site.value_counts().items()},
 "targets":{},
 "warning":"This predicts GPS ridge/thermal signatures GIVEN a published flight, not whether the day is flyable or safe. Unflown days are not labelled negative.",
 "caveats":["Launch choices, pilot skills and glider type are unobserved confounders.",
   "Gudauri and Mestia include multiple launch positions and aspect sectors.",
   "GPS does not identify source of lift; ridge and thermal proxy thresholds are hypotheses.",
   "Year 2026 is held out from initial fit. Bootstrap groups by date.",
   "Any selection of a model using 2026 is deployment validation, not independent proof of future skill."]}
artifact={"version":"xc-v2-2026-11-21","sites":sites,"feature_names":features,
 "baseline_features":base,"weather_features":weather_features,"weather_medians":means,
 "weather_scales":stds,"targets":{},"confidence":"experimental conditional-to-flight only",
 "not_new_site_calibrated":True}
for key,col in targets.items():
 y=data[col].to_numpy(dtype=float)
 preds={}
 for nm,X in (("baseline",X0),("weather",X1)):
  m=Ridge(alpha=15.0).fit(X[tr],y[tr],sample_weight=w[tr])
  preds[nm]=np.clip(m.predict(X[te]),0,1)
 errors={nm:{"mae":round(float(mean_absolute_error(y[te],p)),4),
             "rmse":round(float(np.sqrt(mean_squared_error(y[te],p))),4)}
         for nm,p in preds.items()}
 delta=np.abs(y[te]-preds["baseline"])-np.abs(y[te]-preds["weather"])
 daygroups=[np.flatnonzero(data.date.to_numpy()[te]==date)
            for date in np.unique(data.date.to_numpy()[te])]
 rng=np.random.default_rng(20261121)
 bs=[]
 for _ in range(700):
  ii=np.concatenate([daygroups[j] for j in rng.integers(len(daygroups),size=len(daygroups))])
  bs.append(float(delta[ii].mean()))
 ci=np.quantile(bs,[.025,.975])
 gain=float(delta.mean())
 # Conservative gate; retain seasonal baseline if meteorology does not prove
 # an incremental error reduction over the independent site-month climatology.
 activate=bool(gain>.005 and ci[0]>0)
 selected="weather" if activate else "baseline"
 report["targets"][key]={"baseline":errors["baseline"],"weather":errors["weather"],
  "gain_mae":round(gain,4),"gain_bootstrap_ci95":[round(float(t),4) for t in ci],
  "selected":selected,"activated_weather_correction":activate,
  "heldout_positive_day_fraction":round(float((y[te]>0).mean()),3)}
 artifact["targets"][key]={"selected":selected,"models":{}}
 for nm,X in (("baseline",X0),("weather",X1)):
  fitted=Ridge(alpha=15).fit(X,y,sample_weight=w)
  artifact["targets"][key]["models"][nm]={"intercept":float(fitted.intercept_),
      "coef":[float(q) for q in fitted.coef_]}
 artifact["targets"][key]["holdout_abs_error_q80"]=round(float(
     np.quantile(np.abs(y[te]-preds[selected]),.8)),4)
(OUT/"xc_v2_validation_report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
(OUT/"xc_v2_model.json").write_text(json.dumps(artifact,ensure_ascii=False,indent=2),encoding="utf-8")
lines=["# Georgia XC v2: held-out year weather validation","",
 "**Scope:** *conditional quality of published flights*, not safe flyability or presence of flyable weather.","",
 f"D-1 forecasts matched: {len(data)}/{len(labels)} site-days, train 2024–25: {len(tr)}, test 2026: {len(te)}.","",
 "| Track-derived target | Site/month MAE | + Weather MAE | Weather gain | Date-bootstrap 95% CI | Deployed |",
 "|---|---:|---:|---:|---|---|"]
for n,v in report["targets"].items():
 lines.append(f"| {n} | {v['baseline']['mae']:.3f} | {v['weather']['mae']:.3f} | {v['gain_mae']:+.3f} | {v['gain_bootstrap_ci95']} | {v['selected']} |")
lines+=["",
 "Weather correction is activated only for a date-held-out positive improvement with 95% bootstrap CI above zero. All other outcomes keep the climatological baseline.",
 "A GPS shuttle is a *ridge-like signature*, not direct measurement of slope lift. No absence-of-flight negatives. No rotor or airspace clearance.", ""]
(OUT/"xc_v2_validation_report.md").write_text("\n".join(lines),encoding="utf-8")
print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)

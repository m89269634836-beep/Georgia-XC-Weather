"""Out-of-year evaluation of *route distance* using 5-day weather analogs.

This is a retrospective hypothesis test: antecedent ERA5 reanalysis is not
available promptly enough for operational D−1 forecasts. Goal is to test whether
multi-day sequences carry predictive signal beyond launch/season and D0 weather.
Do not claim probability of a flyable day; only outcomes of published flights.
"""
import datetime,json,math
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error
OUT=Path("data")
x=pd.read_csv(OUT/"xc_v3_five_day_weather_sequences.csv")
w=pd.read_csv(OUT/"xc_v2_issued_forecast_features.csv")
df=x.merge(w,on=["site","date"],how="left",validate="one_to_one")
df["year"]=df.date.str[:4].astype(int)
df["doy"]=pd.to_datetime(df.date).dt.dayofyear
df["month"]=pd.to_datetime(df.date).dt.month
tr=df[df.year<=2025].index.to_numpy();te=df[df.year==2026].index.to_numpy()
if len(tr)<30 or len(te)<15:raise SystemExit("Insufficient holdout year data")
weather_day_cols=["d1_temp_c","d1_rh_pct","d1_sun_wm2","d1_cloud_pct","d1_rain_11_16_mm",
                  "d1_wind10_ms","d1_wind80_ms"]
for lev in ["10","80"]:
 sp=pd.to_numeric(df[f"d1_wind{lev}_ms"],errors="coerce")
 ang=np.deg2rad(pd.to_numeric(df[f"d1_wind{lev}_from_deg"],errors="coerce"))
 df[f"d1_wind{lev}_u"]=sp*np.sin(ang)
 df[f"d1_wind{lev}_v"]=sp*np.cos(ang)
 weather_day_cols += [f"d1_wind{lev}_u",f"d1_wind{lev}_v"]
lags=[]
for lag in range(1,6):
 tag=f"lag{lag}_"
 speed=df[tag+"wind_speed_10m_mean"]
 ang=np.deg2rad(pd.to_numeric(df[tag+"wind_direction_10m_dominant"],errors="coerce"))
 df[tag+"windu"]=speed*np.sin(ang)
 df[tag+"windv"]=speed*np.cos(ang)
 lags+= [tag+z for z in ["temperature_2m_mean","precipitation_sum","windu","windv",
                         "shortwave_radiation_sum","pressure_msl_mean","cloud_cover_mean"]]
# Pressure and temperature changes are potential proxies for approaching fronts;
# no target data used to fit any transform.
for var in ["pressure_msl_mean","temperature_2m_mean","cloud_cover_mean","wind_speed_10m_mean"]:
 df["trend3_"+var]=df["lag1_"+var]-df["lag3_"+var]
lags += ["trend3_"+z for z in ["pressure_msl_mean","temperature_2m_mean","cloud_cover_mean","wind_speed_10m_mean"]]
allcols=weather_day_cols+lags
for col in allcols:
 df[col]=pd.to_numeric(df[col],errors="coerce")
# Features are scaled with statistics from 2024-25 ONLY.
med=df.loc[tr,allcols].median()
valid=[c for c in allcols if df.loc[tr,c].notna().mean()>=.85 and pd.notna(med[c])]
day=[c for c in weather_day_cols if c in valid]
history=[c for c in lags if c in valid]
X=df[valid].fillna(med[valid]).to_numpy(dtype=float)
scaler=StandardScaler().fit(X[tr])
X=np.clip(scaler.transform(X),-5,5)
ci={k:i for i,k in enumerate(valid)}
sites=df.site.to_numpy()
seas=(df.doy.to_numpy()%365)/365*2*np.pi
y=np.log1p(df.q75_route_km.to_numpy(float))
y2=np.log1p(df.median_route_km.to_numpy(float))
rng=np.random.default_rng(20261121)
def dist(a,b,cols):
 if not cols:return 0.
 z=np.array([X[a,ci[k]]-X[b,ci[k]] for k in cols])
 # 5-day time ordering preserved, recent changes carry more weight.
 wt=[]
 for c in cols:
  if c.startswith("lag"):wt.append(1.05/math.sqrt(int(c.split("_")[0][3:])))
  elif c.startswith("trend"):wt.append(.8)
  else:wt.append(1.)
 wt=np.asarray(wt)
 return math.sqrt(float(np.sum((z*wt)**2)/np.sum(wt**2)))
def baseline(idx,yrvals):
 # seasonal/site prior independent of weather; never use post-2025 outcomes.
 same=[a for a in tr if sites[a]==sites[idx]]
 if len(same)<3:same=list(tr)
 theta=np.abs(seas[same]-seas[idx]);theta=np.minimum(theta,2*np.pi-theta)
 wa=np.exp(-1.8*theta**2)
 return float(np.average(yrvals[same],weights=wa))
def knn(idx,yrvals,with_history):
 same=[a for a in tr if sites[a]==sites[idx]]
 pool=same if len(same)>=3 else list(tr)
 blocks=[(day,1.0)]
 if with_history:blocks.append((history,1.0))
 distances=[]
 for a in pool:
  theta=abs(seas[a]-seas[idx]);theta=min(theta,2*np.pi-theta)
  val=sum(weight*dist(idx,a,cols) for cols,weight in blocks)
  val+=0.65*theta
  if sites[a]!=sites[idx]:val+=1.5
  distances.append((val,a))
 distances.sort()
 neighbours=distances[:min(5,len(distances))]
 weight=np.exp(-np.array([q[0] for q in neighbours])*.8)
 vals=yrvals[[q[1] for q in neighbours]]
 return float(np.average(vals,weights=weight)),neighbours
outcome={}
for yname,labels in [("q75_route_km",y),("median_route_km",y2)]:
 prediction={}
 comps={"site_season":[],"today_analog":[],"five_day_analog":[]}
 details=[]
 for idx in te:
  pred_b=baseline(idx,labels)
  pred_d,d_neigh=knn(idx,labels,False)
  pred_h,h_neigh=knn(idx,labels,True)
  comps["site_season"].append(pred_b)
  comps["today_analog"].append(pred_d)
  comps["five_day_analog"].append(pred_h)
  details.append({"site":sites[idx],"date":df.loc[idx,"date"],
    "observed_km":round(float(np.expm1(labels[idx])),1),
    "site_season_km":round(float(np.expm1(pred_b)),1),
    "today_analog_km":round(float(np.expm1(pred_d)),1),
    "five_day_analog_km":round(float(np.expm1(pred_h)),1),
    "past_analogs":[{"date":df.loc[a,"date"],"site":sites[a],
      "route_km":round(float(np.expm1(labels[a])),1),"relative_distance":round(float(dis),2)}
      for dis,a in h_neigh[:3]]})
 for method,preds in comps.items():
  pp=np.expm1(np.array(preds))
  actual=np.expm1(labels[te])
  errors=np.abs(actual-pp)
  prediction[method]={"mae_km":round(float(np.mean(errors)),2),
   "median_absolute_error_km":round(float(np.median(errors)),2),
   "mae_log_km":round(float(mean_absolute_error(labels[te],preds)),4)}
 # Group bootstrap by distinct dates to avoid treating simultaneous site days as iid.
 dayids=df.loc[te,"date"].to_numpy()
 grps=[np.flatnonzero(dayids==d) for d in np.unique(dayids)]
 imp=np.abs(np.expm1(labels[te])-np.expm1(comps["today_analog"]))-np.abs(np.expm1(labels[te])-np.expm1(comps["five_day_analog"]))
 boot=[]
 for _ in range(1000):
  indices=np.concatenate([grps[j] for j in rng.integers(len(grps),size=len(grps))])
  boot.append(float(np.mean(imp[indices])))
 gain=float(np.mean(imp))
 ci95=np.quantile(boot,[.025,.975])
 outcome[yname]={"metrics":prediction,"gain_vs_dayonly_km":round(gain,2),
 "gain_bootstrap_ci95_km":[round(float(q),2) for q in ci95],
 "five_day_improves_uncertainty_bound":bool(gain>1 and ci95[0]>0),
 "note":"Model and distance metric were fixed a priori, no hyperparameter search on 2026."}
 if yname=="q75_route_km":
  (OUT/"xc_v3_analog_examples_2026.json").write_text(json.dumps(details,ensure_ascii=False,indent=2),encoding="utf-8")
report={"version":"v3-5day-analog-experiment","generated_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "input_site_days":len(df),"train_2024_2025":len(tr),"test_2026":len(te),
 "n_complete_history":int(df[[f"lag{lag}_precipitation_sum" for lag in range(1,6)]].notna().all(axis=1).sum()),
 "features_today_used":day,"features_history_used":history,
 "goals":"Retrospectively test 5-day weather patterns for actual XContest route distance conditional on multiple published flights from site-day",
 "weather_day0":"24h-as-issued ECMWF previous runs 0.25deg",
 "weather_prior_days":"ERA5 reanalysis, hindsight; NOT operationally available on D−1 (5 day delay)",
 "outcomes":outcome,
 "major_limitations":["No negative examples of flyable/nonflyable days; not P(flyable).",
  "Number of published flights and pilot choice influence day q75 distance.",
  "Only 2024+ and multiple pilots per day retained for this prototype; narrow site seasonal distribution.",
  "The real route distance is score route km from XContest, not total GPS track length.",
  "ERA5 hindsight antecedents must be replaced with preflight-available historic forecasts/station observations before use operationally.",
  "No hyperparameter tuning on 2026 held-out data; nearest analogs not guarantees of similar lift.",
  "Different flight sites in Gudauri/Mestia sometimes grouped into a single site; harmonize exact launches before true physical calibration."]}
(OUT/"xc_v3_analog_validation.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
lines=["# XC v3: Can antecedent weather patterns predict actual route distance?","",
f"Training days 2024–2025: {len(tr)}. Held-out site/days 2026: {len(te)}.","",
"**Retrospective hypothesis test only:** past-day ERA5 is not available by departure day at fixed lead (5d latency).",
"", "| XC target | Site/season MAE | Day-0 analog MAE | 5-day analog MAE | Gain 5-day vs day-only | 95% date bootstrap interval |",
"|---|---:|---:|---:|---:|---|"]
for key,values in outcome.items():
 stats=values["metrics"]
 lines.append(f"| {key} | {stats['site_season']['mae_km']} km | {stats['today_analog']['mae_km']} km | {stats['five_day_analog']['mae_km']} km | {values['gain_vs_dayonly_km']:+.2f} km | {values['gain_bootstrap_ci95_km']} km |")
lines+=["",
 "Interpretation: positive improvement is better. A 95% interval crossing zero does NOT establish gain. Only route distances from days that have at least two published flights appear in training.",
 "Live forecast prediction must use as-available day−5..day−1 history and the issued D0 forecast, never reanalysis known days later.",
 "Without no-flight or failed-launch observations this cannot certify flight safety, and will not predict probability that a good XC day occurs among *all* calendar days.",
 ""]
(OUT/"xc_v3_analog_validation.md").write_text("\n".join(lines),encoding="utf-8")
print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)

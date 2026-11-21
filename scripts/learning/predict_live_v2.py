"""V2 daily forecasts: meteorological scenario + strictly validated GPS proxies.

The 2024-2026 model is conditional on a flight. Never use the scores as
probabilities of a safe launch. Never extrapolate to unseen starts as trained.
D-1 model is flagged outside the one-day-ahead forecast horizon.
"""
import json,datetime,math
from zoneinfo import ZoneInfo
from pathlib import Path
D=Path("data")
mdl=json.loads((D/"xc_v2_model.json").read_text(encoding="utf-8"))
wx=json.loads((D/"dynamic_ridge_forecast.json").read_text(encoding="utf-8"))
registry={x["id"]:x for x in json.loads((D/"dynamic_sites_registry.json").read_text(encoding="utf-8"))["sites"]}
validation=json.loads((D/"xc_v2_validation_report.json").read_text(encoding="utf-8"))
DAY=datetime.datetime.fromisoformat(wx["retrieved_utc"].replace("Z","+00:00")).astimezone(ZoneInfo("Asia/Tbilisi")).date()
facing={"N":0,"N-NE":22.5,"NE":45,"E":90,"SE":135,"S":180,"SW":225,"W":270,"NW":315}
def numeric(x):
    return float(x) if isinstance(x,(int,float)) and math.isfinite(x) else None
def project(w,facing_deg):
    if not w or facing_deg is None or numeric(w.get("mean_speed_ms")) is None or numeric(w.get("wind_from_deg")) is None:return None
    return round(w["mean_speed_ms"]*math.cos(math.radians(w["wind_from_deg"]-facing_deg)),2)
def predict(site,day,condition):
    mo=int(day[5:7])
    wind10=condition.get("wind10") or {}
    wind80=condition.get("wind80") or {}
    features={}
    for s in mdl["sites"]:features["site_"+s]=1 if s==site else 0
    features["season_sin"]=math.sin(2*math.pi*mo/12)
    features["season_cos"]=math.cos(2*math.pi*mo/12)
    raw={"d1_wind10_ms":wind10.get("mean_speed_ms"),
         "d1_wind80_ms":wind80.get("mean_speed_ms"),
         "d1_sun_wm2":condition.get("sun_wm2"),
         "d1_cloud_pct":condition.get("cloud_pct"),
         "d1_low_cloud_pct":condition.get("low_cloud_pct"),
         "d1_rain_11_16_mm":condition.get("precip_11_16_mm"),
         "d1_temp_c":condition.get("temp_c"),
         "d1_rh_pct":condition.get("rh_pct"),
         "d1_gust10_max_ms":condition.get("gust10_ms_max")}
    for suff,w in [("10",wind10),("80",wind80)]:
        speed=numeric(w.get("mean_speed_ms"));theta=numeric(w.get("wind_from_deg"))
        raw["wx"+suff]=speed*math.sin(math.radians(theta)) if speed is not None and theta is not None else None
        raw["wy"+suff]=speed*math.cos(math.radians(theta)) if speed is not None and theta is not None else None
    for key in mdl["weather_features"]:
        v=numeric(raw.get(key))
        if v is None:v=mdl["weather_medians"][key]
        mean=mdl["weather_medians"][key]
        std=mdl["weather_scales"][key]
        features[key]=max(-8,min(8,(v-mean)/std))
    result={}
    for name,target in mdl["targets"].items():
        chosen=target["selected"]
        params=target["models"][chosen]
        cols=mdl["feature_names"] if chosen=="weather" else mdl["baseline_features"]
        y=params["intercept"]+sum(features.get(k,0)*v for k,v in zip(cols,params["coef"]))
        y=max(0,min(1,y))
        margin=target["holdout_abs_error_q80"]
        result[name]={"observed_flight_proxy":round(y,3),
            "rough_80pct_holdout_abs_error":margin,
            "model_component":chosen,
            "forecast_weather_adjustment_validated":chosen=="weather",
            "warning":"GPS signature conditioned on pilots having flown. Not probability of safety or a flyable day."}
    return result
rows=[]
for sid,s in wx["sites"].items():
    sources=s.get("models",{})
    # It is important that live forecasts and the archived training forecasts
    # use the *same* 25 km model, not an unrecorded blend with ICON or IFS 9km.
    ref=sources.get("ecmwf_ifs025",{}).get("days",{})
    for day,met in sorted(ref.items()):
        if not met:continue
        lead=(datetime.date.fromisoformat(day)-DAY).days
        p=registry.get(sid,{})
        face=facing.get(p.get("reported_facing"))
        sample_count=validation.get("sites",{}).get(sid,0)
        reasons=[]
        if p.get("exact_launch_confirmed") is False:reasons.append("exact takeoff or ridge face unverified")
        if p.get("airspace_or_safety_note"):reasons.append("check local airspace/access")
        if met.get("precip_11_16_mm") and met["precip_11_16_mm"]>=1:reasons.append("forecast precipitation")
        if met.get("low_cloud_pct") is not None and met["low_cloud_pct"]>=80:reasons.append("forecast low cloud / potential visibility")
        if met.get("gust10_ms_max") is not None and met["gust10_ms_max"]>=11:reasons.append("forecast gusts: verify slope/ridge turbulence")
        available=(sid in mdl["sites"] and sample_count>=15 and lead==1)
        pred=predict(sid,day,met) if available else None
        if sid not in mdl["sites"]:reasons.append("no historical calibration at this site")
        elif sample_count<5:reasons.append("fewer than 15 historical multi-flight site-days")
        if lead!=1:reasons.append("D-1 training lead does not match today's lead; score withheld")
        rows.append({"date":day,"forecast_lead_days":lead,"site":sid,"site_name":s["label"],
           "model":"ecmwf_ifs025","model_issued_time":wx["retrieved_utc"],
           "training_site_day_cases":sample_count,
           "wind10":met.get("wind10"),"wind80":met.get("wind80"),
           "wind_component_to_confirmed_windward_slope_ms":project(met.get("wind10"),face),
           "surface_gust_max_ms":met.get("gust10_ms_max"),
           "cloud_pct":met.get("cloud_pct"),"cloud_low_pct":met.get("low_cloud_pct"),
           "radiation_wm2":met.get("sun_wm2"),
           "rain_daytime_mm":met.get("precip_11_16_mm"),
           "trained_flight_signature_prediction":pred,
           "unverified_reasons":reasons})
report={"generated_utc":wx["retrieved_utc"],"trained_version":mdl["version"],
    "never_safe_to_launch_score":True,
    "weather_adjustments_activated":{k:v["activated_weather_correction"] for k,v in validation.get("targets",{}).items()},
    "scope":"Experimental conditional ridge/thermal holding on recorded flight days; normal wind component is physical not a rating",
    "notes":["Only lead==1 with trained site >=15 historical multi-flight cases yields a calibrated conditional score.",
       "Unknown start, complex gorges, rotors, landing, ridge shape and airspace are not modeled as safe/unsafe here.",
       "WindNinja neutral scenarios are NOT equivalent to hour-by-hour data-driven dynamic lift forecast.",
       "For other days only uncalibrated physical forecast features are shown."],
    "rows":rows}
(D/"xc_v2_live_diagnostics.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
lines=["# Georgia XC v2 — forecasts conditioned on observations","",f"Issued: {wx['retrieved_utc']} UTC","",
 "**These are NOT safe-to-fly or all-day flyability probabilities.**", "",
 "Only registered sites with >=15 historical site-days and lead D−1 get experimental conditional-to-flight proxies.","",
 "**Current validation outcome:** weather adjustments are only active if 2026 holdout data show a statistically supported improvement. When none are activated, the percentages below are **historical site-season references**, NOT day-specific weather predictions.",""]
tomorrow=(DAY+datetime.timedelta(days=1)).isoformat()
rows1=[r for r in rows if r["date"]==tomorrow and r["trained_flight_signature_prediction"]]
lines+=["| Start | D−1 wind 10m FROM | Normal component | Ridge pattern | Thermal pattern | Low cloud | Gusts |",
"|---|---|---:|---:|---:|---:|---:|"]
for r in rows1:
 w=r["wind10"];pr=r["trained_flight_signature_prediction"]
 lines.append("| "+r["site_name"]+" | "+str(round(w["mean_speed_ms"],1))+" m/s @"+str(w["wind_from_deg"])+"° | "+
  ("—" if r["wind_component_to_confirmed_windward_slope_ms"] is None else str(r["wind_component_to_confirmed_windward_slope_ms"]))+
  " | "+str(round(100*pr["ridge_signature_rate"]["observed_flight_proxy"]))+
  "% | "+str(round(100*pr["thermal_signature_rate"]["observed_flight_proxy"]))+
  "% | "+str(r["cloud_low_pct"] if r["cloud_low_pct"] is not None else "—")+
  "% | "+str(r["surface_gust_max_ms"])+" m/s |")
lines+=["","The percentages represent expected fraction of tracks showing a **heuristic signature conditioned on a flight**, NOT percentage chance of flying. Models without clear holdout weather improvement default to site/season baseline.", "",
"Untrained candidates (Kaspi, Sagarejo, etc.) retain meteorological/terrain diagnostics but no calibrated probability. All forecasts and uncertainties: [JSON](xc_v2_live_diagnostics.json)."]
(D/"xc_v2_live_diagnostics.md").write_text("\n".join(lines),encoding="utf-8")
print("V2 LIVE",len(rows),"site-days",len(rows1),"calibrated tomorrow")

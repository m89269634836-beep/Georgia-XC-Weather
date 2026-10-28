"""Local road-ground wetness context at Lalisquri takeoff (not actual road observation)."""
import json, urllib.parse, urllib.request, datetime, time, statistics
from pathlib import Path

LAT, LON = 42.099182, 45.418038
TODAY = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=4))).date()
START = TODAY - datetime.timedelta(days=8)
YESTERDAY = TODAY - datetime.timedelta(days=1)
OUT = Path("data")
OUT.mkdir(exist_ok=True)

def fetch(url, params):
    uri = url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(uri, headers={"User-Agent": "Georgia-XC-RoadWeather/1.0"})
    with urllib.request.urlopen(req, timeout=65) as response:
        data = json.load(response)
    if "error" in data: raise RuntimeError(str(data))
    return data

def rounded(value, digits=1):
    return round(value, digits) if isinstance(value, (int,float)) else None

def day_hourly(h, day, field, subset=None):
    a = h.get(field, [])
    times = h.get("time", [])
    vals = [a[i] for i,t in enumerate(times)
            if i < len(a) and t.startswith(day)
            and (subset is None or int(t[11:13]) in subset) and a[i] is not None]
    return rounded(statistics.mean(vals), 3) if vals else None

def rows(data, keys):
    d=data.get("daily",{}); h=data.get("hourly",{})
    result=[]
    for i,day in enumerate(d.get("time",[])):
        record={"date":day}
        for key in keys:
            series=d.get(key,[])
            record[key]=rounded(series[i],2) if i<len(series) else None
        record["rh_mean_pct"]=day_hourly(h,day,"relative_humidity_2m")
        record["rh_early_pct"]=day_hourly(h,day,"relative_humidity_2m",range(5,10))
        record["soil_moisture_0_7_mean"]=day_hourly(h,day,"soil_moisture_0_to_7cm")
        record["soil_moisture_0_1_mean"]=day_hourly(h,day,"soil_moisture_0_to_1cm")
        record["soil_temp_0_7_mean_c"]=day_hourly(h,day,"soil_temperature_0_to_7cm")
        result.append(record)
    return result

hist_params={"latitude":LAT,"longitude":LON,"start_date":START.isoformat(),
             "end_date":YESTERDAY.isoformat(),"timezone":"Asia/Tbilisi",
             "daily":"precipitation_sum,temperature_2m_max,temperature_2m_min,shortwave_radiation_sum,sunshine_duration",
             "hourly":"relative_humidity_2m,soil_moisture_0_to_7cm,soil_temperature_0_to_7cm,precipitation"}
forecast_params={"latitude":LAT,"longitude":LON,"past_days":7,"forecast_days":2,
                 "timezone":"Asia/Tbilisi",
                 "daily":"precipitation_sum,temperature_2m_max,temperature_2m_min,shortwave_radiation_sum,sunshine_duration",
                 "hourly":"relative_humidity_2m,soil_moisture_0_to_1cm,soil_temperature_0cm,precipitation"}
KEYS=["precipitation_sum","temperature_2m_max","temperature_2m_min","shortwave_radiation_sum","sunshine_duration"]
result={"generated_local":datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=4))).isoformat(),
        "point":"Lalisquri takeoff","latitude":LAT,"longitude":LON,"known_takeoff_m_amsl":780,
        "disclaimer":"Model-grid weather and soil moisture; NOT measured condition of the access road. Terrain resolution and soil type may differ.",
        "sources":{},"errors":[]}
for name,url,params in [
    ("historical_reanalysis","https://archive-api.open-meteo.com/v1/archive",hist_params),
    ("recent_forecast_analysis","https://api.open-meteo.com/v1/forecast",forecast_params)]:
    try:
        data=fetch(url,params)
        result["sources"][name]={"api":url,"model_elevation_m":data.get("elevation"),
                                "days":rows(data,KEYS)}
        print("OK",name,len(result["sources"][name]["days"]))
    except Exception as e:
        result["errors"].append({"source":name,"error":str(e)})
        print("ERROR",name,str(e))
if not result["sources"]:
    raise SystemExit("No historical data received; old report remains intact")
(OUT/"lalisquri_road_conditions.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")

lines=["# Lalisquri access-road wetness context","",
       "Weather values are gridded estimates, not observations of the road surface.",
       f"Takeoff: {LAT}, {LON}; 780 m AMSL; local time Asia/Tbilisi.",
       "Soil moisture is volumetric (m³/m³) and model-specific, not a universal mud threshold.",
       "Historical data and recent forecast analysis are both MODEL estimates, not rain gauge observations.",
       ""] 
for name, source in result["sources"].items():
    lines += [f"## {name}","",f"Weather grid elevation: {source['model_elevation_m']} m AMSL","",
              "| Day | Rain mm | Tmax °C | Tmin °C | Solar MJ/m² | Sunshine h | RH mean % | Soil moisture 0–7 cm | Soil moisture 0–1 cm |",
              "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for d in source["days"]:
        sunshine=d["sunshine_duration"]
        lines.append("| "+" | ".join([
            d["date"],str(d["precipitation_sum"]),str(d["temperature_2m_max"]),
            str(d["temperature_2m_min"]),str(d["shortwave_radiation_sum"]),
            str(round(sunshine/3600,1)) if sunshine is not None else "—",
            str(d["rh_mean_pct"]),str(d["soil_moisture_0_7_mean"]),
            str(d["soil_moisture_0_1_mean"])])+" |")
    lines.append("")
if result["errors"]:
    lines += ["## Missing sources","",json.dumps(result["errors"],ensure_ascii=False),""] 
(OUT/"lalisquri_road_report.md").write_text("\n".join(lines),encoding="utf-8")

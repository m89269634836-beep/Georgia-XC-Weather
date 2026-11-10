"""Supplemental ridge-soaring point forecast, not an aviation flyability decision.

Samples ICON-EU (~7km), ECMWF IFS (~9km) and GFS global; models do NOT
resolve individual cliffs or local valley wind acceleration. No auth.
"""
import urllib.request,urllib.parse,json,datetime,time,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
REGISTRY=json.loads((ROOT/"data/dynamic_sites_registry.json").read_text(encoding="utf-8"))
SITES=[(s["id"],s["name"],float(s["latitude"]),float(s["longitude"]),
        s["coordinate_type"],s.get("reported_facing","unknown")) for s in REGISTRY["sites"]]
SCOUT_FILE=ROOT/"data/dynamic_tbilisi_dem_scout.json"
if SCOUT_FILE.exists():
    for point in json.loads(SCOUT_FILE.read_text(encoding="utf-8")).get("candidates",[]):
        SITES.append(("scout_"+point["id"],point["region"]+" "+point["possible_face"],
             float(point["lat"]),float(point["lon"]),
             "Hypothetical DEM candidate; NOT a launch",point["possible_face"]))
MODELS={"icon_eu":"dwd_icon_eu","ecmwf_ifs":"ecmwf_ifs","gfs":"ncep_gfs_global"}
BASE="https://api.open-meteo.com/v1/forecast"
HOUR=["wind_speed_10m","wind_direction_10m","wind_gusts_10m","wind_speed_80m","wind_direction_80m","temperature_2m","precipitation","cloud_cover"]
START=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=4))).date()
DAYS=[(START+datetime.timedelta(days=i)).isoformat() for i in range(1,7)]
def avg(values):
    a=[q for q in values if isinstance(q,(float,int)) and math.isfinite(q)]
    return round(sum(a)/len(a),2) if a else None
def wind_from(speeds, dirs):
    # Scalar average and vector resultant (meteorological FROM direction)
    pairs=[(s,d) for s,d in zip(speeds,dirs) if isinstance(s,(float,int)) and isinstance(d,(float,int))]
    if not pairs:return {"mean_speed_ms":None,"wind_from_deg":None,"resultant_speed_ms":None}
    u=sum(-s*math.sin(math.radians(d)) for s,d in pairs)/len(pairs)
    v=sum(-s*math.cos(math.radians(d)) for s,d in pairs)/len(pairs)
    return {"mean_speed_ms":avg([s for s,d in pairs]),
        "wind_from_deg":round(math.degrees(math.atan2(-u,-v))%360),
        "resultant_speed_ms":round(math.hypot(u,v),2)}
def get(model,fields):
    params={"latitude":",".join(str(s[2]) for s in SITES),
        "longitude":",".join(str(s[3]) for s in SITES),
        "models":model,"hourly":",".join(fields),
        "forecast_days":7,"timezone":"Asia/Tbilisi","wind_speed_unit":"ms"}
    url=BASE+"?"+urllib.parse.urlencode(params)
    req=urllib.request.Request(url,headers={"User-Agent":"GeorgiaXC-RidgeWind/0.1"})
    with urllib.request.urlopen(req,timeout=90) as r:return json.load(r)
report={"retrieved_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "date_window_local":DAYS,
 "notes":["Grid 7km or 9km DOES NOT represent wind at an individual takeoff or narrow gorge.",
          "Winds are meteorological FROM directions, AMSL takeoff heights come from separate DEM.",
          "AREA CENTER point labels must not be treated as takeoff sites.",
          "Rustavi has reported airport CTR restrictions. No flyability claim.",
          "The high-resolution ICON-EU forecast horizon may be shorter than other models."],
 "sites":{},"errors":[]}
for key,label,lat,lon,provenance,face in SITES:
 report["sites"][key]={"label":label,"lat":lat,"lon":lon,"coordinate_type":provenance,
 "reported_facing":face,"models":{}}
for short,model in MODELS.items():
  try:
    try:data=get(model,HOUR)
    except Exception as exc:
        print("FULL_FALLBACK",short,str(exc)[:150],flush=True)
        data=get(model,[k for k in HOUR if "_80m" not in k])
    if isinstance(data,dict):data=[data]
    if not isinstance(data,list) or len(data)!=len(SITES):raise RuntimeError("Not site-aligned response")
    for (key,label,lat,lon,provenance,face),j in zip(SITES,data):
      h=j.get("hourly",{})
      vals={}
      for day in DAYS:
        indices=[i for i,t in enumerate(h.get("time",[]))
                 if t.startswith(day) and 11<=int(t[11:13])<=16]
        def getv(name):
           a=h.get(name,[])
           return [a[i] if i<len(a) else None for i in indices]
        if not indices:continue
        vals[day]={
          "wind10":wind_from(getv("wind_speed_10m"),getv("wind_direction_10m")),
          "wind80":wind_from(getv("wind_speed_80m"),getv("wind_direction_80m")),
          "gust10_ms_mean":avg(getv("wind_gusts_10m")),
          "gust10_ms_max":max((v for v in getv("wind_gusts_10m") if isinstance(v,(int,float))),default=None),
          "temp_c":avg(getv("temperature_2m")),
          "cloud_pct":avg(getv("cloud_cover")),
          "precip_11_16_mm":round(sum(v or 0 for v in getv("precipitation")),2)
        }
      report["sites"][key]["models"][short]={"model_code":model,
         "grid_elevation_m":j.get("elevation"),"days":vals}
    print("SUCCESS",short,len(data),flush=True)
  except Exception as e:report["errors"].append({"model":short,"error":str(e)[:350]});print("ERROR",short,str(e)[:350],flush=True)
Path("data").mkdir(exist_ok=True)
Path("data/dynamic_ridge_forecast.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
if not any(x["models"] for x in report["sites"].values()):raise SystemExit("No forecast data")

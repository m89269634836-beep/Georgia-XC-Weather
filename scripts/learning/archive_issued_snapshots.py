"""Keep actual issued forecast snapshots for future honest verification.

Do not overwrite historical forecasts with updated ones. Data is site-level
public NWP, no user GPS or identifiable flight records.
"""
import gzip,json,datetime
from pathlib import Path
BASE=Path("data")
source=json.loads((BASE/"dynamic_ridge_forecast.json").read_text(encoding="utf-8"))
issued=datetime.datetime.fromisoformat(source["retrieved_utc"].replace("Z","+00:00"))
d0=issued.strftime("%Y%m%d_%H%M%S")
entries=[]
for key,site in source["sites"].items():
 for model,part in site.get("models",{}).items():
  for day,forecast in part.get("days",{}).items():
   if not forecast:continue
   entries.append({"site":key,"date_local":day,"model":part["model_code"],
    "wind10":forecast.get("wind10"),"wind80":forecast.get("wind80"),
    "gust10_ms_max":forecast.get("gust10_ms_max"),
    "temp_c":forecast.get("temp_c"),"rh_pct":forecast.get("rh_pct"),
    "sun_wm2":forecast.get("sun_wm2"),
    "cloud_pct":forecast.get("cloud_pct"),
    "low_cloud_pct":forecast.get("low_cloud_pct"),
    "precip_11_16_mm":forecast.get("precip_11_16_mm")})
payload={"issued_utc":source["retrieved_utc"],"source":"Open-Meteo regional model forecast retrieved by Georgia XC scheduled workflow",
"limitations":["Forecast issuance time is when the pipeline downloaded it, NOT the original ECMWF model cycle.",
 "Point grid data may not resolve local slope/rotor/gorge effects.",
 "These records cannot label an unflown day as bad weather.",
 "No pilot, route or flight track details are stored."],
"records":entries}
target=BASE/"forecast_issue_snapshots"
target.mkdir(exist_ok=True,parents=True)
file=target/f"xc_wind_{d0}UTC.json.gz"
# Gzip deterministic header removes write-time noise to make identical reruns easy to compare.
with file.open("wb") as out:
 with gzip.GzipFile(filename="",mode="wb",fileobj=out,mtime=0,compresslevel=9) as gz:
  gz.write(json.dumps(payload,ensure_ascii=False,separators=(",",":")).encode("utf-8"))
status={"last_issued_utc":source["retrieved_utc"],"snapshot_path":str(file),
 "sites":len(source["sites"]),"records":len(entries),"size_bytes":file.stat().st_size}
(BASE/"xc_v2_forecast_snapshot_status.json").write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(status,ensure_ascii=False),flush=True)

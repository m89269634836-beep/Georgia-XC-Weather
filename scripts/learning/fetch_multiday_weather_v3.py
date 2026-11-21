"""Backtest dataset for 5-day synoptic sequences before observed XC route days.

Uses completed previous-days ERA5 reanalysis as a RETROSPECTIVE hypothesis
experiment. It is not a frozen D-5 forecast nor real-time available ERA5;
retrain against operationally available past observation/forecast inputs before
deployment. Day D0 comes from fixed-lead ECMWF D-1, not reanalysis.
"""
import base64,csv,datetime,gzip,io,json,math,time,urllib.parse,urllib.request
from collections import defaultdict
from pathlib import Path
from statistics import mean
BASE=Path("data")
routes=list(csv.DictReader(io.StringIO(gzip.decompress(base64.b64decode(
 (BASE/"xc_v3_multiflight_route_targets_2024_2026.csv.gz.b64").read_text().strip())).decode())))
POINTS={
"lalisquri":(42.099182,45.418038),"jidgeti":(42.178727,44.880777),
"ananuri":(42.184199,44.739236),"tsivi":(41.779460,45.451075),
"udzilaurta":(42.443674,44.979723),"gudauri":(42.487786,44.501733),
"sagarejo":(41.6836805556,45.2819722222),"mestia":(43.0635,42.719229)}
DAILY=["temperature_2m_mean","precipitation_sum","wind_speed_10m_mean",
 "wind_direction_10m_dominant","shortwave_radiation_sum",
 "pressure_msl_mean","cloud_cover_mean","relative_humidity_2m_mean"]
grouped=defaultdict(list)
for row in routes:
 d=datetime.date.fromisoformat(row["date"])
 grouped[(row["site"],d.year)].append(row)
status={"source":"Open-Meteo Historical Weather ERA5 daily reanalysis",
 "warning":"REANALYSIS IS POST-HOC. Past weather variables must be replaced with data actually accessible D-1 in final operational validation.",
 "date_alignment":"D−5...D−1 Europe/Asia Tbilisi local days plus ECMWF D−1 issued forecast for D0 in separate previous-runs file",
 "groups":len(grouped),"group_ok":0,"group_failed":0,"matched":0,"errors":[]}
def url_for(site,start,end):
 params={"latitude":POINTS[site][0],"longitude":POINTS[site][1],
  "start_date":start,"end_date":end,"timezone":"Asia/Tbilisi","models":"era5",
  "wind_speed_unit":"ms","daily":",".join(DAILY)}
 return "https://archive-api.open-meteo.com/v1/archive?"+urllib.parse.urlencode(params)
results=[]
for idx,((site,year),cases) in enumerate(sorted(grouped.items()),1):
 start=min(datetime.date.fromisoformat(r["date"]) for r in cases)-datetime.timedelta(days=5)
 end=max(datetime.date.fromisoformat(r["date"]) for r in cases)-datetime.timedelta(days=1)
 resp=None;err=None
 for attempt in range(3):
  try:
   url=url_for(site,start,end)
   req=urllib.request.Request(url,headers={"User-Agent":"Georgia-XC-V3-PastWeather-Analog-Research"})
   with urllib.request.urlopen(req,timeout=85) as f:resp=json.load(f)
   if "daily" not in resp:raise RuntimeError(str(resp)[:250])
   break
  except Exception as e:err=str(e);time.sleep(2*(attempt+1))
 if resp is None:
  status["group_failed"]+=1;status["errors"].append({"site":site,"year":year,"error":err[:300]})
  print("FAIL",idx,site,year,err[:250],flush=True);continue
 status["group_ok"]+=1
 d=resp["daily"];dayidx={k:i for i,k in enumerate(d.get("time",[]))}
 for x in cases:
  row={"site":site,"date":x["date"],"n_flights":x["n_flights"],
      "median_route_km":x["median_route_km"],"q75_route_km":x["q75_route_km"],
      "max_route_km":x["max_route_km"]}
  endday=datetime.date.fromisoformat(x["date"])
  for lag in range(1,6):
   prior=(endday-datetime.timedelta(days=lag)).isoformat()
   for v in DAILY:
    arr=d.get(v,[]);j=dayidx.get(prior)
    row[f"lag{lag}_{v}"]=arr[j] if j is not None and j<len(arr) else None
  results.append(row);status["matched"]+=1
 print("OK",idx,"/",len(grouped),site,year,"cases",len(cases),flush=True)
 time.sleep(.4)
columns=["site","date","n_flights","median_route_km","q75_route_km","max_route_km"]+[
 f"lag{lag}_{v}" for lag in range(1,6) for v in DAILY]
with (BASE/"xc_v3_five_day_weather_sequences.csv").open("w",newline="",encoding="utf-8") as o:
 w=csv.DictWriter(o,columns);w.writeheader();w.writerows(results)
(BASE/"xc_v3_weather_sequences_status.json").write_text(json.dumps(status,indent=2,ensure_ascii=False),encoding="utf-8")
print("STATUS",json.dumps(status,ensure_ascii=False),flush=True)
if status["matched"]<70:raise SystemExit("Insufficient complete historical weather cases")

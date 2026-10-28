"""Verify that day-ahead forecasts for selected paragliding days are actually returned."""
import json,urllib.request,urllib.parse,datetime,pathlib
cases=[("2025-09-06",42.099182,45.418038),("2026-07-05",42.099182,45.418038),("2026-05-09",42.178727,44.880777)]
base="https://previous-runs-api.open-meteo.com/v1/forecast"
variables=["temperature_2m","relative_humidity_2m","precipitation","cloud_cover","shortwave_radiation","wind_speed_10m"]
result={"checked_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"source":"Open-Meteo Previous Runs API","notes":"Fixed lead 24/48 h. For exact initialisation/publication time use Single Runs.","results":[]}
for day,lat,lon in cases:
    params={"latitude":lat,"longitude":lon,"start_date":day,"end_date":day,"timezone":"Asia/Tbilisi","wind_speed_unit":"ms",
      "hourly":",".join(f"{v}_previous_day{n}" for n in (1,2) for v in variables)}
    item={"date":day,"coords":[lat,lon]}
    try:
        url=base+"?"+urllib.parse.urlencode(params)
        req=urllib.request.Request(url,headers={"User-Agent":"GeorgiaXC-Archive-Backtest/0.1"})
        with urllib.request.urlopen(req,timeout=65) as response:j=json.load(response)
        h=j["hourly"]
        idx=h["time"].index(day+"T13:00")
        item.update({"ok":True,"grid_elevation_m":j.get("elevation"),
                     "fields_13_local":{k:v[idx] for k,v in h.items() if k!="time"}})
    except Exception as e:item.update({"ok":False,"error":str(e)[:300]})
    result["results"].append(item)
    print(day, "OK" if item["ok"] else "FAILED",str(item.get("fields_13_local",item.get("error")))[:250])
pathlib.Path("data").mkdir(exist_ok=True)
pathlib.Path("data/xcontest_historical_previous_runs_probe.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
if not any(item["ok"] for item in result["results"]):raise SystemExit("No valid previous-run data")

"""Probe real historical model coverage on specific independent flying days."""
import urllib.request,urllib.parse,json,datetime,pathlib,time
cases=[("2024-06-03",42.184199,44.739236),("2025-07-07",41.6836805556,45.2819722222),("2026-07-05",42.099182,45.418038)]
model="ecmwf_ifs025"
v=["wind_speed_10m","wind_direction_10m","wind_speed_80m","wind_direction_80m","temperature_2m","relative_humidity_2m","shortwave_radiation","cloud_cover","precipitation"]
out=[]
for date,lat,lon in cases:
 params={"latitude":lat,"longitude":lon,"start_date":date,"end_date":date,"models":model,
 "hourly":",".join(f"{k}_previous_day1" for k in v),"timezone":"Asia/Tbilisi","wind_speed_unit":"ms"}
 url="https://previous-runs-api.open-meteo.com/v1/forecast?"+urllib.parse.urlencode(params)
 item={"date":date,"model":model}
 try:
  t=time.monotonic()
  with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"GeorgiaXC-PriorRunsProbe"}),timeout=28) as r:
   j=json.load(r)
  h=j["hourly"];idx=h["time"].index(date+"T13:00")
  item.update({"ok":True,"elapsed_sec":round(time.monotonic()-t,1),"fields_13":{k:val[idx] for k,val in h.items() if k!="time"}})
 except Exception as e:item.update({"ok":False,"error":str(e)[:300]})
 out.append(item);print(item,flush=True)
pathlib.Path("data/xc_v2_forecast_probe.json").write_text(json.dumps(out,ensure_ascii=False,indent=2))

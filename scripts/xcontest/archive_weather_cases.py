"""Retrospective gridded weather at a few Georgia paragliding sites/dates.

This is HISTORICAL REANALYSIS, not the forecast that was issued on D-1.
No pilot identifiers, IGC tracks or coordinates other than publicly known
takeoff locations are included in repository outputs.
"""
import csv, datetime as dt, json, math, statistics, time, urllib.parse, urllib.request
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

SITES={
 "Лалискури":(42.099182,45.418038,780),
 "Джиджети":(42.178727,44.880777,1815),
 "Удзилаурта":(42.443674,44.979723,2200),
 "Циви":(41.779460,45.451075,1575),
 "Гудаури":(42.487786,44.501733,2661)
}
CASES=[
 ("2025-03-15","Джиджети"),("2025-03-24","Лалискури"),
 ("2025-05-24","Лалискури"),("2025-06-05","Лалискури"),
 ("2025-09-06","Лалискури"),("2025-10-12","Лалискури"),
 ("2025-11-02","Лалискури"),("2025-12-06","Удзилаурта"),
 ("2026-02-21","Джиджети"),("2026-05-09","Джиджети"),
 ("2026-06-04","Лалискури"),("2026-06-20","Циви"),
 ("2026-07-05","Лалискури"),("2026-10-10","Гудаури"),
 ("2025-05-31","Лалискури"),("2026-04-03","Лалискури"),("2026-06-28","Лалискури")
]
ARCHIVE="https://archive-api.open-meteo.com/v1/archive"
HR="temperature_2m,relative_humidity_2m,precipitation,cloud_cover,shortwave_radiation,wind_speed_10m,wind_direction_10m,temperature_850hPa,temperature_700hPa,geopotential_height_850hPa,geopotential_height_700hPa,relative_humidity_700hPa"
BASIC="temperature_2m,relative_humidity_2m,precipitation,cloud_cover,shortwave_radiation,wind_speed_10m,wind_direction_10m"

def average(seq):
    v=[x for x in seq if isinstance(x,(int,float)) and math.isfinite(x)]
    return round(sum(v)/len(v),2) if v else None
def get_one(date,site):
    lat,lon,elev=SITES[site]
    date_obj=dt.date.fromisoformat(date)
    prior=date_obj-dt.timedelta(days=3)
    params={"latitude":lat,"longitude":lon,"start_date":prior.isoformat(),
            "end_date":date,"timezone":"Asia/Tbilisi",
            "hourly":HR,
            "daily":"precipitation_sum,temperature_2m_max,temperature_2m_min,shortwave_radiation_sum"}
    def req(params):
        url=ARCHIVE+"?"+urllib.parse.urlencode(params)
        request=urllib.request.Request(url,headers={"User-Agent":"GeorgiaXC-HistoricalCaseCheck/0.1"})
        with urllib.request.urlopen(request,timeout=55) as f:result=json.load(f)
        if result.get("error"):raise RuntimeError(result.get("reason","Unknown API error"))
        return result
    try:
        data=req(params); pressure_avail=True
    except Exception as e:
        params["hourly"]=BASIC
        data=req(params);pressure_avail=False
    h=data["hourly"];d=data["daily"]
    ids=[i for i,t in enumerate(h["time"]) if t[:10]==date and 11<=int(t[11:13])<=16]
    def v(k):
        a=h.get(k,[]);return average([a[i] for i in ids if i<len(a)])
    def v_sum(k):
        a=h.get(k,[])
        return round(sum(a[i] or 0 for i in ids if i<len(a)),2)
    daily=dict(zip(d["time"],d["precipitation_sum"]))
    previous=sum(daily.get((date_obj-dt.timedelta(days=j)).isoformat()) or 0 for j in (1,2,3))
    result={"date":date,"site":site,"takeoff_elevation_m_amsl":elev,
            "source_grid_elevation_m":data.get("elevation"),
            "rain_3d_prior_mm":round(previous,1),
            "rain_flight_day_mm":round(daily[date] or 0,1),
            "rain_11_16_mm":v_sum("precipitation"),
            "sun_11_16_wm2":v("shortwave_radiation"),
            "cloud_11_16_pct":v("cloud_cover"),
            "rh_11_16_pct":v("relative_humidity_2m"),
            "temp_11_16_c":v("temperature_2m"),
            "wind10_11_16_ms":v("wind_speed_10m"),
            "rh700_11_16_pct":v("relative_humidity_700hPa"),
            "lapse_850_700_c_per_km":None,
            "pressure_level_data_available":pressure_avail,
            "weather_type":"historical model/reanalysis; NOT original D−1 forecast",
            "source_url":"https://archive-api.open-meteo.com/v1/archive"}
    if pressure_avail:
        a=h.get("temperature_850hPa",[])
        b=h.get("temperature_700hPa",[])
        za=h.get("geopotential_height_850hPa",[])
        zb=h.get("geopotential_height_700hPa",[])
        lapse=[]
        for i in ids:
            if max(i+1,0)<=min(len(a),len(b),len(za),len(zb)) and all(z[i] is not None for z in (a,b,za,zb)):
                dz=zb[i]-za[i]
                if dz>0:lapse.append((a[i]-b[i])/dz*1000)
        result["lapse_850_700_c_per_km"]=average(lapse)
        result["pressure_level_data_available"]=bool(lapse)
    return result

rows=[];errors=[]
with ThreadPoolExecutor(max_workers=3) as pool:
    futs={pool.submit(get_one,d,s):(d,s) for d,s in CASES}
    for f in as_completed(futs):
        case=futs[f]
        try:
            r=f.result();rows.append(r);print("OK",case,r["sun_11_16_wm2"],r["rain_3d_prior_mm"])
        except Exception as e:
            print("ERROR",case,str(e));errors.append({"case":case,"error":str(e)})
rows.sort(key=lambda x:(x["date"],x["site"]))
Path("data").mkdir(exist_ok=True)
with open("data/xcontest_historical_weather_cases.csv","w",newline="",encoding="utf-8") as file:
    wr=csv.DictWriter(file,fieldnames=list(rows[0]) if rows else [])
    if rows:wr.writeheader();wr.writerows(rows)
with open("data/xcontest_historical_weather_status.json","w",encoding="utf-8") as file:
    json.dump({"generated_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
               "requested_cases":len(CASES),"successful":len(rows),"errors":errors,
               "warning":"Retrospective historical weather/reanalysis only; not D−1 issued forecasts or observed weather-station measurements."},
              file,ensure_ascii=False,indent=2)
if not rows:raise SystemExit("No weather obtained")

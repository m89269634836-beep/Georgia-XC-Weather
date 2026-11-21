"""Historical *issued-ahead* forecasts joined to privacy-minimized site-day outcomes.

Only 2024+ cases with >=2 flights/site/day were shared: no pilot identity,
raw track, precise route or individual start coordinate in training labels.
Explicit ECMWF IFS 0.25 forecast model; don't silently substitute reanalysis.
No absence-of-flight negative labels! All measurements conditioned on flying.
"""
import base64,csv,datetime,gzip,io,json,math,time,urllib.parse,urllib.request
from pathlib import Path
from collections import defaultdict
OUT=Path("data")
LAB=OUT/"xc_v2_multiflight_daily_labels_2024_2026.csv.gz.b64"
rows=list(csv.DictReader(io.StringIO(gzip.decompress(base64.b64decode(LAB.read_text().strip())).decode())))
POINTS={
 "lalisquri":(42.099182,45.418038),
 "jidgeti":(42.178727,44.880777),
 "ananuri":(42.184199,44.739236),
 "tsivi":(41.779460,45.451075),
 "udzilaurta":(42.443674,44.979723),
 "gudauri":(42.487786,44.501733),
 "sagarejo":(41.6836805556,45.2819722222),
 "mestia":(43.0635,42.719229)
}
M="ecmwf_ifs025"
VARS=["temperature_2m","relative_humidity_2m","wind_speed_10m","wind_direction_10m",
      "wind_speed_80m","wind_direction_80m","cloud_cover","precipitation",
      "shortwave_radiation"]
OPTIONAL=["cloud_cover_low","wind_gusts_10m"]
LEADS=[1,2]
GROUPS=defaultdict(list)
for row in rows:
    day=datetime.date.fromisoformat(row["date"])
    GROUPS[(row["site"],day.year,(day.month-1)//3)].append(row)
def number(v):
    return float(v) if isinstance(v,(int,float)) and math.isfinite(v) else None
def avg(vals):
    s=[number(v) for v in vals]
    a=[v for v in s if v is not None]
    return round(sum(a)/len(a),4) if a else None
def query(site,start,end,variables):
    args={"latitude":POINTS[site][0],"longitude":POINTS[site][1],"models":M,
      "hourly":",".join(f"{v}_previous_day{lead}" for lead in LEADS for v in variables),
      "start_date":str(start),"end_date":str(end),"timezone":"Asia/Tbilisi",
      "wind_speed_unit":"ms"}
    url="https://previous-runs-api.open-meteo.com/v1/forecast?"+urllib.parse.urlencode(args)
    req=urllib.request.Request(url,headers={"User-Agent":"GeorgiaXC-Backtest-V2/0.2"})
    with urllib.request.urlopen(req,timeout=90) as r:
        payload=json.load(r)
    if "hourly" not in payload:raise RuntimeError("Hourly missing: "+str(payload)[:260])
    return payload
def derive(h,day,lead):
    dates=h.get("time",[])
    ids=[i for i,x in enumerate(dates) if x.startswith(day+"T") and 11<=int(x[11:13])<=16]
    if len(ids)<4:return None
    k=lambda v:f"{v}_previous_day{lead}"
    def samples(v):
        a=h.get(k(v))
        return [a[i] if a is not None and i<len(a) else None for i in ids]
    def wind(height):
        ss=samples("wind_speed_"+height)
        dd=samples("wind_direction_"+height)
        pairs=[(number(s),number(d)) for s,d in zip(ss,dd)]
        pairs=[(s,d) for s,d in pairs if s is not None and d is not None]
        if not pairs:return (None,None,None)
        x=sum(s*math.sin(math.radians(d)) for s,d in pairs)/len(pairs)
        y=sum(s*math.cos(math.radians(d)) for s,d in pairs)/len(pairs)
        return round(math.hypot(x,y),3),round(math.degrees(math.atan2(x,y))%360,2),round(sum(s for s,d in pairs)/len(pairs),3)
    w10,d10,_=wind("10m")
    w80,d80,_=wind("80m")
    prec=samples("precipitation");prec=[number(x) for x in prec]
    gust=[number(x) for x in samples("wind_gusts_10m")]
    return {
       "temp_c":avg(samples("temperature_2m")),
       "rh_pct":avg(samples("relative_humidity_2m")),
       "wind10_ms":w10,"wind10_from_deg":d10,
       "wind80_ms":w80,"wind80_from_deg":d80,
       "cloud_pct":avg(samples("cloud_cover")),
       "low_cloud_pct":avg(samples("cloud_cover_low")),
       "sun_wm2":avg(samples("shortwave_radiation")),
       "rain_11_16_mm":round(sum(x for x in prec if x is not None),3) if any(x is not None for x in prec) else None,
       "gust10_max_ms":max((x for x in gust if x is not None),default=None)
    }
result=[];errors=[];stats={"groups":len(GROUPS),"multi_flight_site_days":len(rows),"model":M,
 "source":"Open-Meteo Previous Runs ECMWF IFS 0.25", "fixed_valid_time_leads":LEADS,
 "notes":"_previous_day1 and _previous_day2 are fixed 24/48 hour offsets, not exact 00Z/12Z issued runs",
 "group_successes":0,"group_failures":0,"cases_with_day1_wind":0,"cases_with_day2_wind":0}
for gi,((site,year,qtr),batch) in enumerate(sorted(GROUPS.items()),1):
    d1=min(x["date"] for x in batch);d2=max(x["date"] for x in batch)
    data=None;err=None
    for attempt in range(3):
        try:
            try: data=query(site,d1,d2,VARS+OPTIONAL)
            except Exception as exc:
                # Optional variables may not be archived for every model/year.
                data=query(site,d1,d2,VARS)
            break
        except Exception as e:
            err=str(e);time.sleep(2*(attempt+1))
    if data is None:
        stats["group_failures"]+=1;errors.append({"site":site,"quarter":str(year)+"Q"+str(qtr+1),"error":err[:300]})
        print("FAIL",gi,site,d1,d2,err[:220],flush=True)
        continue
    stats["group_successes"]+=1
    h=data["hourly"]
    for row in batch:
        case={"site":site,"date":row["date"],"model":M}
        for lead in LEADS:
            outcome=derive(h,row["date"],lead)
            if outcome:case.update({f"d{lead}_{k}":v for k,v in outcome.items()})
        result.append(case)
        if case.get("d1_wind10_ms") is not None:stats["cases_with_day1_wind"]+=1
        if case.get("d2_wind10_ms") is not None:stats["cases_with_day2_wind"]+=1
    print("OK",gi,"/",len(GROUPS),site,d1,d2,"rows",len(batch),"fields",len(h.keys()),flush=True)
    time.sleep(.5)
OUT.mkdir(exist_ok=True)
columns=["site","date","model"]+[f"d{lead}_{k}" for lead in LEADS for k in
  ["temp_c","rh_pct","wind10_ms","wind10_from_deg","wind80_ms","wind80_from_deg",
  "cloud_pct","low_cloud_pct","sun_wm2","rain_11_16_mm","gust10_max_ms"]]
with (OUT/"xc_v2_issued_forecast_features.csv").open("w",newline="",encoding="utf-8") as f:
    writer=csv.DictWriter(f,columns);writer.writeheader();writer.writerows(result)
stats["errors"]=errors
(OUT/"xc_v2_weather_fetch_status.json").write_text(json.dumps(stats,ensure_ascii=False,indent=2),encoding="utf-8")
print("STATUS",json.dumps(stats,ensure_ascii=False),flush=True)
if not stats["cases_with_day1_wind"]:raise SystemExit("No historical forecast features downloaded")

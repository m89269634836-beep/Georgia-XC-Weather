"""Small per-day model diagnostics for Georgian paragliding XC.
Numerical model values are NOT a launch clearance or observed weather.
Wind directions are the direction FROM which the wind blows.
All altitudes are AMSL, including interpolation targets.
"""
import json, math
from pathlib import Path

ROOT=Path("data")
src=json.loads((ROOT/"latest.json").read_text(encoding="utf-8"))
MODELS=("ecmwf","gfs","icon")
LEVELS=(1000,975,950,925,900,850,800,700,600,500)
HOURS=range(11,17)
WIND_HEIGHTS=(2000,2500,3000,3500,4000)
NAMES={"lalisquri":"Лалискури","jidgeti":"Джиджети",
       "ananuri":"Ананури","tsivi":"Циви","udzilaurta":"Удзилаурта"}
first=next(iter(next(iter(src["points"].values()))["forecasts"].values()))
DAYS=sorted({t[:10] for t in first["hourly"]["time"]})

def ave(x):
    v=[n for n in x if isinstance(n,(int,float)) and math.isfinite(n)]
    return round(sum(v)/len(v),1) if v else None

def series(h,k,ids):
    a=h.get(k,[])
    return [a[i] for i in ids if i<len(a) and a[i] is not None]

def wvec(speed,direction):
    a=math.radians(direction)
    return (speed*math.sin(a),speed*math.cos(a))

def wind(h,i,target,elevation):
    if target is not None and elevation is not None and target<elevation+75:
        return None
    if target is None:
        speeds=h.get("wind_speed_10m",[])
        dirs=h.get("wind_direction_10m",[])
        if i>=len(speeds) or i>=len(dirs) or speeds[i] is None or dirs[i] is None:return None
        return wvec(speeds[i],dirs[i])
    profile=[]
    for level in LEVELS:
        for key in [f"wind_speed_{level}hPa",f"wind_direction_{level}hPa",f"geopotential_height_{level}hPa"]:
            if key not in h or i>=len(h[key]) or h[key][i] is None:break
        else:
            profile.append((h[f"geopotential_height_{level}hPa"][i],
                            *wvec(h[f"wind_speed_{level}hPa"][i],h[f"wind_direction_{level}hPa"][i])))
    profile.sort()
    for (z1,x1,y1),(z2,x2,y2) in zip(profile,profile[1:]):
        if z1<=target<=z2 and z2>z1:
            f=(target-z1)/(z2-z1)
            return (x1+(x2-x1)*f,y1+(y2-y1)*f)
    return None

def direction(x,y):
    deg=math.degrees(math.atan2(x,y))%360
    return round(deg)

def represent(vecs):
    vecs=[v for v in vecs if v is not None]
    if not vecs:return None
    x=sum(v[0] for v in vecs)/len(vecs)
    y=sum(v[1] for v in vecs)/len(vecs)
    deg=direction(x,y)
    return {"ms":round(math.hypot(x,y),1),"from_deg":deg,
            "from":["С","ССВ","СВ","ВСВ","В","ВЮВ","ЮВ","ЮЮВ",
                    "Ю","ЮЮЗ","ЮЗ","ЗЮЗ","З","ЗСЗ","СЗ","ССЗ"][int((deg+11.25)%360//22.5)]}

def lcl_estimate(temp,rh,elevation):
    if temp is None or rh is None or elevation is None or rh<=0:return None
    a,b=17.625,243.04
    gamma=math.log(max(min(rh,100),1)/100)+a*temp/(b+temp)
    dew=b*gamma/(a-gamma)
    # LCL estimate from 2m T/Td is approximate and is not predicted cumulus base.
    return round(elevation+125*(temp-dew))

def site_day(site_id,info,model,day):
    fc=info["forecasts"].get(model)
    if not fc:return None
    h=fc["hourly"]
    ids=[i for i,t in enumerate(h["time"]) if t[:10]==day and int(t[11:13]) in HOURS]
    whole=[i for i,t in enumerate(h["time"]) if t[:10]==day]
    if not ids:return None
    mean=lambda k:ave(series(h,k,ids))
    sumrain=lambda indices:round(sum(series(h,"precipitation",indices)),1)
    ground=info.get("takeoff_elevation_m_amsl") or fc.get("elevation")
    winds={"surface":represent([wind(h,i,None,ground) for i in ids])}
    for z in WIND_HEIGHTS:
        winds[str(z)]=represent([wind(h,i,z,ground) for i in ids])
    bearing=None
    if "_b" in site_id and "_d" in site_id:
        bearing=int(site_id.split("_b")[1].split("_d")[0])
    tail={}
    if bearing is not None:
        for z in (2000,2500,3000):
            ws=winds[str(z)]
            if ws:
                tail[str(z)]=round(-ws["ms"]*math.cos(math.radians(ws["from_deg"]-bearing)),1)
    return {"cloud_pct":mean("cloud_cover"),
      "cloud_low_pct":mean("cloud_cover_low"),
      "cloud_mid_pct":mean("cloud_cover_mid"),
      "cloud_high_pct":mean("cloud_cover_high"),
      "sun_wm2":mean("shortwave_radiation"),
      "rain_11_16_mm":sumrain(ids),"rain_24h_mm":sumrain(whole),
      "temp_surface_c":mean("temperature_2m"),
      "rh_surface_pct":mean("relative_humidity_2m"),
      "rh_850_pct":mean("relative_humidity_850hPa"),
      "rh_800_pct":mean("relative_humidity_800hPa"),
      "rh_700_pct":mean("relative_humidity_700hPa"),
      "cape_jkg":mean("cape"),
      "estimated_surface_lcl_m_amsl":lcl_estimate(mean("temperature_2m"),
                                                  mean("relative_humidity_2m"),
                                                  fc.get("elevation")),
      "winds":winds,"route_bearing_deg":bearing,
      "tailwind_component_ms":tail}

overview=["# Weekly XC model overview","",
          "Forecast issued: "+src["generated_at_utc"]+" UTC",
          "Local time Georgia (Asia/Tbilisi). All daytime statistics: 11:00–16:00.",
          "Wind FROM directions. Fixed-altitude winds are linearly interpolated model pressure-level vectors.",
          "Note: model ground/10m wind may poorly resolve launch slope; pressure levels below terrain are ignored.",
          "LCL is derived from gridded surface T/RH, and is NOT observed cloudbase or thermal ceiling.",
          "",""]
for day in DAYS:
    base={"day_local":day,"forecast_issued_utc":src["generated_at_utc"],
          "time_window":"11:00–16:00 Asia/Tbilisi",
          "notes":["Winds are direction FROM, in m/s.",
                   "Route positive tailwind_component_ms aids movement in indicated bearing.",
                   "Interpolated winds do not resolve local mountain flows.",
                   "Surface LCL is a rough moisture diagnostic, NOT verified cloudbase.",
                   "Cloud, rainfall and thermal estimates are uncertain in complex terrain."],
          "sites":{}}
    paths=[("start",f"xc_day_{day}.json"),("corridor",f"xc_corridor_{day}.json")]
    sections={"start":{},"corridor":{}}
    for name,point in src["points"].items():
        bucket="corridor" if "_b" in name else "start"
        sections[bucket][name]={"lat":point["latitude"],"lon":point["longitude"],
             "takeoff_m_amsl":point["takeoff_elevation_m_amsl"],
             "models":{m:site_day(name,point,m,day) for m in MODELS}}
    for bucket,path in paths:
        package={k:v for k,v in base.items() if k!="sites"}
        package["sites"]=sections[bucket]
        (ROOT/path).write_text(json.dumps(package,ensure_ascii=False,separators=(",",":")),
                               encoding="utf-8")
        print(path,len(sections[bucket]),"points")
    overview += [f"## {day}","",
                 "| Start | Model | Sun W/m² | Cloud % | Rain 11–16 mm | Low cloud % | Wind 2000m | Wind 3000m | LCL estimate AMSL |",
                 "|---|---|---:|---:|---:|---:|---|---|---:|"]
    for name,obj in sections["start"].items():
        for model,v in obj["models"].items():
            if v is None:continue
            def fmtwind(w):
                return f"{w['from']} {w['ms']} m/s" if w else "—"
            def num(v):
                return str(v) if v is not None else "—"
            overview.append("| "+" | ".join([
                NAMES.get(name,name),model,num(v["sun_wm2"]),num(v["cloud_pct"]),
                num(v["rain_11_16_mm"]),num(v["cloud_low_pct"]),
                fmtwind(v["winds"]["2000"]),fmtwind(v["winds"]["3000"]),
                num(v["estimated_surface_lcl_m_amsl"])])+" |")
    overview.append("")
(ROOT/"xc_weekly_overview.md").write_text("\n".join(overview),encoding="utf-8")
print("Weekly report spans",DAYS)

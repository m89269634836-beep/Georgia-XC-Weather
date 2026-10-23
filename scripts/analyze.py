"""Compact XC diagnostics from saved Open-Meteo forecasts.

All elevations are AMSL; wind directions indicate where wind COMES FROM.
Pressure-level lapse rates cannot resolve thin inversions between levels.
This is a planning aid, not a flight safety decision.
"""
import json, math
from pathlib import Path

ROOT = Path("data")
src = json.loads((ROOT / "latest.json").read_text(encoding="utf-8"))
DAYS = ["2026-10-24", "2026-10-25"]
HOURS = range(11, 17)
LEVELS = [1000, 975, 950, 925, 900, 850, 800, 700, 600, 500]
NAMES = {"lalisquri":"Лалискури","jidgeti":"Джиджети",
         "ananuri":"Ананури","tsivi":"Циви","udzilaurta":"Удзилаурта"}
MODELS = ["ecmwf","gfs","icon"]
def avg(values):
    v = [x for x in values if isinstance(x,(int,float)) and math.isfinite(x)]
    return round(sum(v)/len(v),1) if v else None
def sample(h,key,idx):
    vals=h.get(key,[])
    return vals[idx] if idx<len(vals) else None
def compass(deg):
    if deg is None: return "—"
    return ["С","ССВ","СВ","ВСВ","В","ВЮВ","ЮВ","ЮЮВ",
            "Ю","ЮЮЗ","ЮЗ","ЗЮЗ","З","ЗСЗ","СЗ","ССЗ"][int((deg+11.25)%360//22.5)]
def wind_mean(h,indices,level):
    speed=f"wind_speed_{level}"
    direction=f"wind_direction_{level}"
    pairs=[(sample(h,speed,i),sample(h,direction,i)) for i in indices]
    pairs=[(s,d) for s,d in pairs if s is not None and d is not None]
    if not pairs: return None
    # Meteorological wind vector; averaging FROM directions weighted by speed.
    x=sum(s*math.sin(math.radians(d)) for s,d in pairs)/len(pairs)
    y=sum(s*math.cos(math.radians(d)) for s,d in pairs)/len(pairs)
    return {"speed_ms":round(math.hypot(x,y),1),
            "from_deg":round(math.degrees(math.atan2(x,y))%360),
            "from":compass(math.degrees(math.atan2(x,y))%360)}
def level_profile(h,i):
    a=[]
    for lev in LEVELS:
        z=sample(h,f"geopotential_height_{lev}hPa",i)
        t=sample(h,f"temperature_{lev}hPa",i)
        rh=sample(h,f"relative_humidity_{lev}hPa",i)
        w=sample(h,f"wind_speed_{lev}hPa",i)
        d=sample(h,f"wind_direction_{lev}hPa",i)
        if z is not None and t is not None:
            a.append({"hpa":lev,"z_m_amsl":round(z),"t_c":round(t,1),
                      "rh_pct":rh,"wind_ms":w,"wind_from":compass(d)})
    return sorted(a,key=lambda x:x["z_m_amsl"])
def inversions(profile):
    found=[]
    for a,b in zip(profile,profile[1:]):
        dz=b["z_m_amsl"]-a["z_m_amsl"]
        if dz<=0:continue
        lapse=(a["t_c"]-b["t_c"])/dz*1000
        if lapse<0:
            found.append({"from_m_amsl":a["z_m_amsl"],"to_m_amsl":b["z_m_amsl"],
                          "warming_c":round(b["t_c"]-a["t_c"],1)})
    return found
def cell(point,model,day):
    data=src["points"][point]["forecasts"].get(model)
    if not data:return None
    h=data["hourly"]
    ids=[i for i,t in enumerate(h["time"]) if t[:10]==day and int(t[11:13]) in HOURS]
    noon=next((i for i,t in enumerate(h["time"]) if t==day+"T13:00"),None)
    if not ids:return None
    val=lambda k:avg([sample(h,k,i) for i in ids])
    precip=sum(sample(h,"precipitation",i) or 0 for i in ids)
    prof=level_profile(h,noon) if noon is not None else []
    return {"sun_wm2":val("shortwave_radiation"),"cloud_pct":val("cloud_cover"),
            "rain_mm":round(precip,1),"rh700_pct":val("relative_humidity_700hPa"),
            "cape_jkg":val("cape"),"surface_wind":wind_mean(h,ids,"10m"),
            "wind_925":wind_mean(h,ids,"925hPa"),"wind_850":wind_mean(h,ids,"850hPa"),
            "wind_700":wind_mean(h,ids,"700hPa"),"wind_600":wind_mean(h,ids,"600hPa"),
            "profile_13":prof,"resolved_inversions_13":inversions(prof)}
result={"generated_from_utc":src["generated_at_utc"],"period_local":"11:00–16:00 Asia/Tbilisi",
        "dates":DAYS,"notes":["Wind is direction FROM, not TO.",
        "Profile altitude is AMSL. 13:00 profile only.",
        "Inversions are detected between available pressure levels only; unresolved thin inversions may exist.",
        "No thermal cloudbase or flight-safe ranking is inferred from pressure-level profiles alone."],
        "sites":{}}
for name,info in src["points"].items():
    result["sites"][name]={"lat":info["latitude"],"lon":info["longitude"],
                          "takeoff_m_amsl":info["takeoff_elevation_m_amsl"],
                          "days":{day:{m:cell(name,m,day) for m in MODELS} for day in DAYS}}
(ROOT/"xc_analysis.json").write_text(json.dumps(result,ensure_ascii=False,separators=(",",":")),encoding="utf-8")
lines=["# XC weather diagnostics","",
       f"Forecast issued: {src['generated_at_utc']} UTC",
       "Time: 11:00–16:00 Georgia; wind direction is **FROM**; heights are **AMSL**.",
       "","This report does not certify safe launch conditions. Thin inversions may not be resolved.",""]
for day in DAYS:
    lines.extend([f"## {day}","",
       "| Site / sample | Model | Radiation W/m² | Cloud % | Rain mm | Wind 10m | Wind 925hPa | Wind 850hPa | Wind 700hPa | RH 700hPa |",
       "|---|---|---:|---:|---:|---|---|---|---|---:|"])
    for name,info in result["sites"].items():
        for model,entry in info["days"][day].items():
            if entry is None:continue
            def fmtwind(w):
                return f"{w['from']} {w['speed_ms']}m/s" if w else "—"
            def n(x):return "—" if x is None else str(x)
            lines.append("| "+" | ".join([name,model,n(entry["sun_wm2"]),n(entry["cloud_pct"]),
                n(entry["rain_mm"]),fmtwind(entry["surface_wind"]),
                fmtwind(entry["wind_925"]),fmtwind(entry["wind_850"]),
                fmtwind(entry["wind_700"]),n(entry["rh700_pct"])])+" |")
    lines.append("")
lines.extend(["## Pressure profiles at 13:00","",
              "Temperature and relative humidity by pressure level. Levels below local terrain should not be used.",""])
for name,info in result["sites"].items():
    if "_b" in name:continue
    lines.append(f"### {NAMES.get(name,name)} ({info['takeoff_m_amsl']} m AMSL)")
    for day in DAYS:
        lines.append(f"**{day}**")
        for model in MODELS:
            entry=info["days"][day].get(model)
            if not entry:continue
            p=[x for x in entry["profile_13"] if x["z_m_amsl"] >= info["takeoff_m_amsl"]-50]
            lines.append(f"- {model}: "+("; ".join(f"{x['z_m_amsl']}m {x['t_c']}°C RH{x['rh_pct']}% {x['wind_from']} {x['wind_ms']}m/s" for x in p)))
            inv=[x for x in entry["resolved_inversions_13"] if x["to_m_amsl"]>info["takeoff_m_amsl"]]
            if inv:lines.append("  - Resolved inversions: "+", ".join(f"{x['from_m_amsl']}–{x['to_m_amsl']}m (+{x['warming_c']}°C)" for x in inv))
    lines.append("")
(ROOT/"xc_report.md").write_text("\n".join(lines),encoding="utf-8")
print("Wrote xc_analysis.json and xc_report.md for",len(result["sites"]),"points")

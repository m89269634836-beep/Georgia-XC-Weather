"""Experimental DEM exposure and local forecast coverage check for Georgia soaring.

No inferred "launchability": terrain aspect is reconnaissance only. A polygon
centre is NOT a verified launch coordinate. No pilot track or private data.
"""
import json, math, time, urllib.request, urllib.parse, datetime
from pathlib import Path
SITES=[
 ("lalisquri","Лалискури",42.099182,45.418038,"verified user launch","N"),
 ("jidgeti","Джиджети",42.178727,44.880777,"verified user launch","N"),
 ("ananuri","Ананури",42.184199,44.739236,"verified user launch","N"),
 ("tsivi","Циви",41.779460,45.451075,"verified user launch","N"),
 ("udzilaurta","Удзилаурта",42.443674,44.979723,"verified user launch","N-NE"),
 ("gudauri","Гудаури район",42.487786,44.501733,"existing site reference, multiple launch faces","multiple"),
 ("tbilisi_sea_area","Тбилисское море",41.756111,44.920417,"AIP UGA3 area centre; NOT launch coordinate","E-SE-S (Syride)"),
 ("sighnaghi_area","Сигнахи",41.6233,45.9372,"AIP UGA2 area centre; NOT launch coordinate","SE aspect hypothesis"),
 ("kazaniani_area","Казаниани",41.68056,45.30167,"AIP UGA1 approximate polygon centre; NOT launch coordinate","unknown"),
 ("rustavi","Рустави",41.55440,44.93460,"published takeoff coordinate; CTR restriction","unknown"),
]
DIRS=["N","NE","E","SE","S","SW","W","NW"]
DEGS=[0,45,90,135,180,225,270,315]
def destination(lat,lon,deg,km):
    a=math.radians(deg);r=6371.;d=km/r;phi=math.radians(lat);lam=math.radians(lon)
    q=math.asin(math.sin(phi)*math.cos(d)+math.cos(phi)*math.sin(d)*math.cos(a))
    ll=lam+math.atan2(math.sin(a)*math.sin(d)*math.cos(phi),math.cos(d)-math.sin(phi)*math.sin(q))
    return round(math.degrees(q),6),round(math.degrees(ll),6)
def fetch(url):
    req=urllib.request.Request(url,headers={"User-Agent":"GeorgiaXC-TerrainResearch/0.1 contact=GitHub"})
    with urllib.request.urlopen(req,timeout=65) as response:
        return json.load(response)
Path("data").mkdir(exist_ok=True)
points=[];owners=[]
for key,label,lat,lon,provenance,face in SITES:
    for radius in [0,0.4,1.5]:
        dlist=[("C",0)] if radius==0 else list(zip(DIRS,DEGS))
        for d,angle in dlist:
            coord=(lat,lon) if radius==0 else destination(lat,lon,angle,radius)
            points.append(coord);owners.append((key,radius,d))
heights={}
errors=[]
for i in range(0,len(points),75):
    batch=points[i:i+75]
    url="https://api.opentopodata.org/v1/srtm90m?"+urllib.parse.urlencode({
        "locations":"|".join(f"{lat:.6f},{lon:.6f}" for lat,lon in batch),
        "interpolation":"bilinear"})
    try:
        data=fetch(url)
        assert data.get("status")=="OK" and len(data["results"])==len(batch)
        for idx,res in enumerate(data["results"]):
            key,radius,d=owners[i+idx]
            heights[(key,radius,d)]=res.get("elevation")
        print("DEM_OK",i,len(batch),flush=True)
    except Exception as exc:
        errors.append(f"DEM batch {i}: {str(exc)[:180]}")
        print("DEM_ERROR",i,errors[-1],flush=True)
    time.sleep(1.4)
terrain=[]
for key,label,lat,lon,provenance,face in SITES:
    z=heights.get((key,0,"C"))
    differences={}
    for radius in [0.4,1.5]:
        vals={}
        for d in DIRS:
            v=heights.get((key,radius,d))
            vals[d]=None if z is None or v is None else round(z-v)
        differences[str(radius)+"km"]=vals
    terrain.append({"key":key,"label":label,"lat":lat,"lon":lon,"provenance":provenance,
       "known_face":face,"dem_elevation_m":z,"height_drop_from_centre_m":differences,
       "possible_open_downhill_sectors_400m":[d for d in DIRS if differences["0.4km"][d] is not None and differences["0.4km"][d]>20],
       "warning":"DEM difference indicates downhill direction only; not verified ridge face, takeoff, soaring suitability or freedom from lee/rotor."})
Path("data/dynamic_sites_terrain_probe.json").write_text(json.dumps({
 "checked_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "dem_dataset":"SRTM90m via OpenTopoData; area centres must NOT be treated as launch points",
 "sites":terrain,"errors":errors},ensure_ascii=False,indent=2),encoding="utf-8")

# Check model coverage in Caucasus. A valid HTTP response can still have all-null
# values; require actual usable wind numbers at the intended point.
models=["dwd_icon_eu","icon_eu","ecmwf_ifs","ecmwf_ifs025","icon_global"]
probes=[]
for model in models:
    lat,lon=42.099182,45.418038
    params={"latitude":lat,"longitude":lon,"models":model,"hourly":"wind_speed_10m,wind_direction_10m",
        "timezone":"Asia/Tbilisi","forecast_days":2,"wind_speed_unit":"ms"}
    item={"model":model}
    try:
        j=fetch("https://api.open-meteo.com/v1/forecast?"+urllib.parse.urlencode(params))
        vals=j.get("hourly",{}).get("wind_speed_10m",[])
        nonnull=sum(v is not None for v in vals)
        item.update({"http_ok":True,"nonnull_hours":nonnull,"grid_elevation_m":j.get("elevation"),
                     "first_hours":list(zip(j.get("hourly",{}).get("time",[])[:4],vals[:4]))})
    except Exception as e:item.update({"http_ok":False,"error":str(e)[:250]})
    probes.append(item);print("MODEL_PROBE",item,flush=True)
    time.sleep(.3)
Path("data/dynamic_forecast_models_probe.json").write_text(json.dumps({
 "checked_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "probe_point":"Lalisquri 42.099182N 45.418038E",
 "models":probes,
 "meaning":"API return and nonnull hours establish availability, not ability to predict wind along a 1-2 km gorge."},
 ensure_ascii=False,indent=2),encoding="utf-8")

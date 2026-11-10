"""Investigate tree-cover and mapped roads at four user-supplied soaring recon points.

Data is ESA WorldCover 2021 v200 at 10m and OSM Overpass highway geometries.
Do NOT equate mapped roads with 4x4 drivability or unobstructed runway.
"""
import json, math, datetime, time, urllib.parse, urllib.request
from pathlib import Path
import numpy as np
import rasterio
from rasterio.windows import from_bounds
from pyproj import Geod

ROOT=Path(__file__).resolve().parents[2]
REGISTRY=json.loads((ROOT/"data/dynamic_sites_registry.json").read_text(encoding="utf-8"))
IDS=["medvezhiy","sagarejo","kaspi","kaspi_2"]
SITES=[x for x in REGISTRY["sites"] if x["id"] in IDS]
OUTPUT={"timestamp_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
"data_sources":["ESA WorldCover 2021 v200 10m","OpenStreetMap Overpass mapped roads"],
"warnings":["2021 land cover classification does not replace a current satellite image or on-site inspection",
 "OpenStreetMap road mapping does not establish road surface condition, driveability, access rights, or snow clearance",
 "No inspected launch site or approved landing inferred from these metrics"],
"sites":{},"errors":[]}
geod=Geod(ellps="WGS84")
def worldcover(lat,lon):
    tilelat=int(math.floor(lat/3)*3);tilelon=int(math.floor(lon/3)*3)
    tile=f"{'N' if tilelat>=0 else 'S'}{abs(tilelat):02d}{'E' if tilelon>=0 else 'W'}{abs(tilelon):03d}"
    url=f"https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_{tile}_Map.tif"
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",GDAL_HTTP_MAX_RETRY="2",
                      CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif"):
      with rasterio.open(url) as src:
        # approximately 750m bbox and 60m inner circle, calculate true distances
        dlat=850/111000;dlon=850/(111000*math.cos(math.radians(lat)))
        win=from_bounds(lon-dlon,lat-dlat,lon+dlon,lat+dlat,transform=src.transform).round_offsets().round_lengths()
        a=src.read(1,window=win)
        tf=src.window_transform(win)
        rr,cc=np.indices(a.shape)
        xs,ys=rasterio.transform.xy(tf,rr.flatten(),cc.flatten())
        xs=np.asarray(xs);ys=np.asarray(ys)
        xmeters=(xs-lon)*111000*math.cos(math.radians(lat))
        ymeters=(ys-lat)*111000
        distances=np.hypot(xmeters,ymeters).reshape(a.shape)
        sectors={}
        for radius in [60,250,700]:
            sample=a[distances<=radius]
            sample=sample[np.isin(sample,[10,20,30,40,50,60,70,80,90,95,100])]
            if sample.size==0:sectors[str(radius)]={"error":"empty_valid_area"};continue
            classes={str(c):int((sample==c).sum()) for c in [10,20,30,40,50,60]}
            sectors[str(radius)]={"pixels":int(sample.size),
              "tree_pct":round(100*classes["10"]/sample.size,1),
              "open_grass_bare_pct":round(100*(classes["30"]+classes["60"])/sample.size,1),
              "shrub_pct":round(100*classes["20"]/sample.size,1),
              "cropland_pct":round(100*classes["40"]/sample.size,1),
              "built_pct":round(100*classes["50"]/sample.size,1),
              "class_counts":classes}
        return {"tile":tile,"radii_m":sectors,"center_class":int(next(src.sample([(lon,lat)]))[0])}
def roads(lat,lon):
  query=f'[out:json][timeout:30];way(around:1800,{lat},{lon})["highway"];out geom;'
  data=urllib.parse.urlencode({"data":query}).encode()
  servers=["https://overpass.kumi.systems/api/interpreter","https://overpass-api.de/api/interpreter",
           "https://overpass.nchc.org.tw/api/interpreter"]
  errors=[]
  for server in servers:
    try:
      req=urllib.request.Request(server,data=data,headers={"User-Agent":"GeorgiaXC-Soaring-Research/0.1","Content-Type":"application/x-www-form-urlencoded"})
      with urllib.request.urlopen(req,timeout=42) as rsp:obj=json.load(rsp)
      rows=[]
      for e in obj.get("elements",[]):
        tags=e.get("tags",{})
        coords=e.get("geometry",[])
        if not coords:continue
        nearest=min((geod.inv(lon,lat,p["lon"],p["lat"])[2] for p in coords),default=None)
        if nearest is None:continue
        rows.append({"id":e.get("id"),"highway":tags.get("highway"),"surface":tags.get("surface"),
                     "tracktype":tags.get("tracktype"),"access":tags.get("access"),
                     "distance_to_mapped_node_m":round(nearest)})
      rows.sort(key=lambda r:r["distance_to_mapped_node_m"])
      # Distances to mapped vertices, not to line segments, so they may be overestimates.
      return {"endpoint":server,"ways_count":len(rows),"nearest_mapped_ways":rows[:8],
              "warning":"distance measured to mapped road vertices; may overestimate true road distance"}
    except Exception as e:errors.append(f"{server}: {str(e)[:120]}")
  raise RuntimeError("; ".join(errors))
for s in SITES:
  k=s["id"]; lat=s["latitude"];lon=s["longitude"]
  item={"name":s["name"],"lat":lat,"lon":lon}
  for field,fn in (("landcover",lambda:worldcover(lat,lon)),("mapped_roads",lambda:roads(lat,lon))):
    try:
       item[field]=fn()
       print(k,field,"OK",str(item[field])[:350],flush=True)
    except Exception as e:
       item[field]={"error":str(e)[:500]}
       OUTPUT["errors"].append({"site":k,"part":field,"error":str(e)[:500]})
       print(k,field,"ERROR",str(e)[:180],flush=True)
  OUTPUT["sites"][k]=item
  time.sleep(1)
(ROOT/"data/dynamic_new_sites_access_vegetation.json").write_text(json.dumps(OUTPUT,ensure_ascii=False,indent=2),encoding="utf-8")
print("RESULT",len(OUTPUT["sites"]),"errors",len(OUTPUT["errors"]),flush=True)

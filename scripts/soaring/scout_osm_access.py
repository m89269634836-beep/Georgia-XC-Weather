"""Small OSM core API bbox checks for public mapped tracks near DEM ridge candidates.

OSM route availability is not drivable access, especially in mud/snow.
If API fails, output is marked unknown, not 'no roads'.
"""
import json,urllib.request,urllib.parse,xml.etree.ElementTree as ET,time,math,datetime
from pathlib import Path
ROOT=Path("data")
src=json.loads((ROOT/"dynamic_tbilisi_dem_scout.json").read_text(encoding="utf-8"))
registry=json.loads((ROOT/"dynamic_sites_registry.json").read_text(encoding="utf-8"))
points=[{"id":s["id"],"label":s["name"],"lat":s["latitude"],"lon":s["longitude"]}
        for s in registry["sites"] if s["id"] in {"medvezhiy","sagarejo","kaspi","kaspi_2"}]
points += [{"id":x["id"],"label":x["region"]+" "+x["possible_face"],"lat":x["lat"],"lon":x["lon"]}
           for x in src["candidates"]]
out={"generated_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "source":"OpenStreetMap core v0.6 bbox API (not Overpass)",
 "caveat":"An OSM road line may be impassable, blocked, legally private, snow-covered or too steep. Not a driving ETA.",
 "sites":{}}
for s in points:
 lat,lon=float(s["lat"]),float(s["lon"])
 dlat=900/111000
 dlon=900/(111000*math.cos(math.radians(lat)))
 bbox=f"{lon-dlon:.6f},{lat-dlat:.6f},{lon+dlon:.6f},{lat+dlat:.6f}"
 url="https://api.openstreetmap.org/api/0.6/map?"+urllib.parse.urlencode({"bbox":bbox})
 item={"label":s["label"],"lat":lat,"lon":lon,"nearest_highway":None,"road_ways":0}
 try:
  req=urllib.request.Request(url,headers={"User-Agent":"GeorgiaXC-RidgeRecce/0.1 (public OSM geometry research)"})
  with urllib.request.urlopen(req,timeout=25) as r: content=r.read(7_500_000)
  root=ET.fromstring(content)
  nodes={}
  for n in root.findall("node"):
   nodes[n.attrib["id"]]=(float(n.attrib["lat"]),float(n.attrib["lon"]))
  recs=[]
  for w in root.findall("way"):
   tags={t.attrib["k"]:t.attrib["v"] for t in w.findall("tag")}
   if "highway" not in tags:continue
   coords=[nodes[n.attrib["ref"]] for n in w.findall("nd") if n.attrib["ref"] in nodes]
   if len(coords)<2:continue
   distances=[]
   for a,b in zip(coords[:-1],coords[1:]):
    # local metric tangent approximation, closest to segment
    ax=(a[1]-lon)*111000*math.cos(math.radians(lat));ay=(a[0]-lat)*111000
    bx=(b[1]-lon)*111000*math.cos(math.radians(lat));by=(b[0]-lat)*111000
    vx,vy=bx-ax,by-ay;den=vx*vx+vy*vy
    t=min(1,max(0,-(ax*vx+ay*vy)/den)) if den else 0
    distances.append(math.hypot(ax+t*vx,ay+t*vy))
   if distances:
    recs.append({"highway":tags.get("highway"),"surface":tags.get("surface"),
      "tracktype":tags.get("tracktype"),"access":tags.get("access"),"distance_m":round(min(distances)),
      "osm_way_id":int(w.attrib["id"])})
  recs.sort(key=lambda x:x["distance_m"])
  item["road_ways"]=len(recs)
  item["nearest_highway"]=recs[0] if recs else None
  item["nearby_highways"]=recs[:5]
  item["api_success"]=True
  print("OSM_OK",s["id"],item["nearest_highway"],flush=True)
 except Exception as exc:
  item["api_success"]=False;item["error"]=str(exc)[:260]
  print("OSM_FAIL",s["id"],str(exc)[:150],flush=True)
 out["sites"][s["id"]]=item
 time.sleep(.5)
(ROOT/"dynamic_scout_osm_roads.json").write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
print("SUCCESS",sum(x["api_success"] for x in out["sites"].values()),"of",len(out["sites"]))

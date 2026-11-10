"""Prototype REAL WindNinja 4.0 CLI runs on Copernicus GLO-30 terrain.

Two source-normalized diagnostic wind scenarios on 8 km UTM grids. These are
not validated local forecasts, nor estimates of rotor position or safe launch.
Designed for GitHub Actions windows-latest with WindNinja_win64 ZIP.
"""
import os,sys,json,time,math,glob,subprocess,datetime,traceback
from pathlib import Path
import numpy as np
import rasterio
from rasterio.warp import reproject,Resampling
from rasterio.transform import from_origin
from pyproj import Transformer
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"data"/"windninja_spatial_prototype"
OUT.mkdir(parents=True,exist_ok=True)
REG=json.loads((ROOT/"data/dynamic_sites_registry.json").read_text(encoding="utf-8"))
SITES=[s for s in REG["sites"] if s["id"] in ["sagarejo","kaspi"]]
STATUS={"generated_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
"windninja_version":"4.0.0 (Windows binary)",
"dem_source":"Copernicus GLO-30 Public (30m DSM from radar)",
"coordinate_system":"EPSG:32638 UTM Zone 38N, meters",
"domain_width_m":8000,"grid_spacing_m":125,"mesh_resolution_m":200,
"initialization":"domainAverageInitialization, neutral atmosphere, uniform grass roughness",
"simulations":[],"errors":[],
"warning":"These are two hypothetical upstream wind scenarios, NOT a weather forecast or safe launch determination. Mass solver alone does not reliably predict rotor."}
def checkpoint():
 (OUT/"status.json").write_text(json.dumps(STATUS,ensure_ascii=False,indent=2),encoding="utf-8")
checkpoint()
def copdem_url(lat,lon):
  n=math.floor(lat); e=math.floor(lon)
  til=f"Copernicus_DSM_COG_10_{'N' if n>=0 else 'S'}{abs(n):02d}_00_{'E' if e>=0 else 'W'}{abs(e):03d}_00_DEM"
  return f"https://copernicus-dem-30m.s3.amazonaws.com/{til}/{til}.tif"
def make_dem(s):
  lat,lon=float(s["latitude"]),float(s["longitude"])
  to_utm=Transformer.from_crs("EPSG:4326","EPSG:32638",always_xy=True)
  x,y=to_utm.transform(lon,lat); n=64; cell=125
  transform=from_origin(x-4000,y+4000,cell,cell)
  height=np.full((n,n),-9999.0,dtype=np.float32)
  url=copdem_url(lat,lon)
  with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",GDAL_HTTP_MAX_RETRY="3",GDAL_HTTP_RETRY_DELAY="2"):
    with rasterio.open(url) as src:
      reproject(source=rasterio.band(src,1),destination=height,src_transform=src.transform,
        src_crs=src.crs,dst_transform=transform,dst_crs="EPSG:32638",
        dst_nodata=-9999.0,resampling=Resampling.bilinear,num_threads=1)
  if np.mean(height<=-9990)>0.002:raise RuntimeError(f"DEM has {np.mean(height<=-9990)*100:.1f}% missing cells; refusing fill")
  dem=OUT/f"{s['id']}_UTM38_125m.tif"
  with rasterio.open(dem,"w",driver="GTiff",height=n,width=n,count=1,
      dtype="float32",crs="EPSG:32638",transform=transform,
      nodata=-9999.0,compress="DEFLATE") as dst:dst.write(height,1)
  return dem,height,transform,url
def asc_layers(folder):
  files=list(folder.rglob("*.asc"))
  speed=[];direction=[]
  for p in files:
   try:
    with rasterio.open(p) as ds:
       a=ds.read(1,masked=True).filled(np.nan)
       if np.nanmax(a)>200 or np.nanmin(a)<-100:continue
       if any(q in p.stem.lower() for q in ["vel","spd","speed"]):speed.append((p,a,ds.transform))
       if any(q in p.stem.lower() for q in ["ang","dir"]):direction.append((p,a,ds.transform))
   except Exception:continue
  return speed,direction,[str(p) for p in files]
def plot_result(s,scenario,terrain,wind,demtransform,outpath):
  fig,ax=plt.subplots(figsize=(8,7))
  extent=(0,terrain.shape[1]*125,0,terrain.shape[0]*125)
  h=ax.imshow(terrain,origin="upper",extent=extent,cmap="terrain",alpha=.55)
  fig.colorbar(h,ax=ax,label="DEM elevation, m",shrink=.8)
  if wind is not None:
   v=wind[1]; ext=(0,terrain.shape[1]*125,0,terrain.shape[0]*125)
   im=ax.imshow(v,origin="upper",extent=ext,cmap="viridis",alpha=.65)
   fig.colorbar(im,ax=ax,label="Wind speed, m/s",shrink=.8)
  ax.scatter([4000],[4000],marker="+",s=160,c="red",linewidths=2)
  ax.set_title(f"{s['name']} | WindNinja scenario {scenario} FROM\nNot a real local wind measurement")
  ax.set_xlabel("Eastward offset within 8 km domain (m)")
  ax.set_ylabel("Northward offset within 8 km domain (m)")
  fig.tight_layout();fig.savefig(outpath,dpi=150);plt.close(fig)
def run():
  exe=Path(os.environ.get("WINDNINJA_EXE",""))
  if not exe.is_file():raise RuntimeError("WINDNINJA_EXE not configured or executable not found")
  for s in SITES:
    try:dem,z,transform,url=make_dem(s);print("DEM_OK",s["id"],float(z.min()),float(z.max()),url,flush=True)
    except Exception as exc:
       STATUS["errors"].append({"site":s["id"],"step":"DEM","error":str(exc)});checkpoint();continue
    for direction in [270,0]:
      speed=6
      label=f"{s['id']}_from_{direction}_6ms"
      directory=OUT/label;directory.mkdir(exist_ok=True)
      cfg=directory/"scenario.cfg"
      cfg.write_text("\n".join([
       f"elevation_file = {dem.as_posix()}",
       "num_threads = 2","initialization_method = domainAverageInitialization",
       f"input_speed = {speed}","input_speed_units = mps",
       f"input_direction = {direction}",
       "input_wind_height = 80","units_input_wind_height = m",
       "output_wind_height = 20","units_output_wind_height = m",
       "output_speed_units = mps","vegetation = grass",
       "diurnal_winds = false","mesh_resolution = 200","units_mesh_resolution = m",
       "write_ascii_output = true","write_goog_output = false",
       "write_shapefile_output = false","write_geotiff_output = false",
       f"output_path = {directory.as_posix()}", ""
      ]),encoding="utf-8")
      entry={"site":s["id"],"scenario_from_deg":direction,"input_wind_ms":speed,"config":str(cfg.relative_to(ROOT)),
        "dem":str(dem.relative_to(ROOT)),"executed":False}
      started=time.time()
      try:
        proc=subprocess.run([str(exe),str(cfg)],cwd=directory,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
              text=True,errors="replace",timeout=230,env=os.environ.copy())
        (directory/"windninja.log").write_text(proc.stdout[-20000:],encoding="utf-8")
        entry["duration_sec"]=round(time.time()-started,1)
        entry["process_return_code"]=proc.returncode
        speeds,dirs,allasc=asc_layers(directory)
        entry["ascii_files"]=allasc
        if proc.returncode!=0:raise RuntimeError(f"WindNinja exited {proc.returncode}: {proc.stdout[-1800:]}")
        if not speeds:raise RuntimeError(f"CLI exit=0 but no output speed ASC. Files: {allasc}")
        p,a,_=speeds[0];valid=a[np.isfinite(a)]
        if len(valid)<100:raise RuntimeError("Less than 100 valid output wind pixels")
        entry["executed"]=True
        entry["output_speed_ascii"]=str(p.relative_to(ROOT))
        entry["wind20m_mean_ms"]=round(float(np.mean(valid)),2)
        entry["wind20m_p90_ms"]=round(float(np.quantile(valid,.9)),2)
        entry["wind20m_max_ms"]=round(float(np.max(valid)),2)
        entry["wind20m_speedup_p90_vs_input"]=round(entry["wind20m_p90_ms"]/speed,2)
        png=OUT/f"{label}.png"
        plot_result(s,f"{direction}° {speed} m/s",z,speeds[0],transform,png)
        entry["preview_png"]=str(png.relative_to(ROOT))
        print("WINDNINJA_OK",entry,flush=True)
      except Exception as exc:
        entry["error"]=str(exc)[:1500]
        STATUS["errors"].append({"site":s["id"],"scenario":direction,"error":str(exc)[:1500]})
        print("WINDNINJA_FAILED",label,str(exc)[:400],flush=True)
      STATUS["simulations"].append(entry);checkpoint()
try:run()
except Exception as exc:
 STATUS["errors"].append({"step":"BOOTSTRAP","error":str(exc),"traceback":traceback.format_exc()[-2500:]})
 checkpoint()
 raise
print("FINISHED",sum(q["executed"] for q in STATUS["simulations"]),"successes",len(STATUS["errors"]),"errors",flush=True)

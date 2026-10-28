"""Minimal public XContest accessibility probe.

Makes only two unauthenticated GET requests. Does not bypass access controls,
store cookies, copy tracks or extract signed IGC URLs.
"""
import datetime
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

URLS = [
    ("flight_detail", "https://www.xcontest.org/2023/world/en/flights/detail:p_golovkin/24.03.2023/08:56"),
    ("route_kml", "https://www.xcontest.org/routekml.php?fl=3727392&rt=36103472"),
]
result = {
    "checked_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "flight_example_id": 3727392,
    "notices": [
        "Unauthenticated, low-rate public URL check only.",
        "HTTP success may still return an HTML login or anti-bot page.",
        "No IGC, KML, authentication material or signed tokens are stored.",
    ],
    "checks": []
}
for index, (kind,url) in enumerate(URLS):
    if index:time.sleep(3)
    item = {"type":kind,"url":url}
    try:
        req = urllib.request.Request(url,headers={
            "User-Agent":"Georgia-XC-Weather-Research/0.1 (public accessibility probe)",
            "Accept":"text/html,application/xml,application/vnd.google-earth.kml+xml,*/*",
        })
        with urllib.request.urlopen(req,timeout=25) as res:
            block=res.read(4096)
            ctype=res.headers.get("Content-Type","")
            item.update({"http_status":res.status,"content_type":ctype,
                         "first_bytes_kind":"xml_or_kml" if block.lstrip().startswith((b"<?xml",b"<kml"))
                         else "html" if b"<html" in block.lower() or b"<!doctype html" in block.lower()
                         else "other"})
    except urllib.error.HTTPError as e:
        item.update({"http_status":e.code,"error":"HTTP access denied or server error"})
    except (urllib.error.URLError,TimeoutError) as e:
        item.update({"http_status":None,"error":str(type(e).__name__)})
    result["checks"].append(item)
    print(kind,item.get("http_status"),item.get("content_type",""))
Path("data").mkdir(exist_ok=True)
Path("data/xcontest_access_status.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")

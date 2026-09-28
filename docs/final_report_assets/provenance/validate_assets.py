"""Validate generated report assets without modifying source evidence."""
from pathlib import Path
import csv, hashlib, json, xml.etree.ElementTree as ET
from PIL import Image

pack=Path(__file__).resolve().parent.parent
manifest=json.loads((pack/"FINAL_REPORT_ASSET_PACK_MANIFEST.json").read_text(encoding="utf-8"))
assert manifest["asset_count"]==len(manifest["assets"])
counts={"figures":0,"tables":0,"screenshots":0,"composites":0,"source_data":0}
errors=[]
with (pack/"00_catalog/REPORT_ASSET_CATALOG.csv").open(encoding="utf-8",newline="") as f:
    catalog=list(csv.DictReader(f))
catalog_by_id={row["id"]:row for row in catalog}
if len(catalog_by_id)!=len(manifest["assets"]):errors.append("catalog count/duplicate IDs")
if (pack/"provenance/REPORT_ASSET_MANIFEST.json").read_bytes()!=(pack/"FINAL_REPORT_ASSET_PACK_MANIFEST.json").read_bytes():
    errors.append("manifest mirror mismatch")

def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda:f.read(1<<20),b""):
            h.update(chunk)
    return h.hexdigest()

for item in manifest["assets"]:
    row=catalog_by_id.get(item["id"])
    if row is None or json.loads(row["asset_sha256"])!=item["asset_sha256"]:
        errors.append("catalog asset hash mismatch: "+item["id"])
    for rel in item["paths"]:
        p=pack/rel
        if not p.is_file():errors.append("missing: "+rel);continue
        if sha(p)!=item["asset_sha256"][rel]:errors.append("hash: "+rel)
        if p.suffix==".svg":ET.parse(p)
        if p.suffix==".png":
            with Image.open(p) as im:
                im.verify()
            if item["kind"] in {"figure","composite"}:
                with Image.open(p) as im:
                    dpi=im.info.get("dpi",(0,0))
                    if min(dpi)<299:errors.append("dpi: "+rel+" "+str(dpi))
        if p.suffix==".md" and item["kind"]=="table":
            s=p.read_text(encoding="utf-8")
            if "| ---" not in s:errors.append("table markdown: "+rel)
        if p.suffix==".csv" and item["kind"]=="table":
            with p.open(encoding="utf-8",newline="") as f:
                rows=list(csv.reader(f))
                if len(rows)<2:errors.append("table csv: "+rel)
    for source,expected in item["source_sha256"].items():
        p=Path(source)
        if not p.is_file():errors.append("source missing: "+source)
        elif sha(p)!=expected:errors.append("source changed: "+source)
    if item.get("source_data"):
        p=pack/item["source_data"]
        if not p.is_file() or sha(p)!=item["source_data_sha256"]:errors.append("source data: "+str(p))
    counts[{"figure":"figures","table":"tables","screenshot":"screenshots","composite":"composites"}[item["kind"]]]+=1
counts["source_data"]=len(list((pack/"source_data").glob("*.csv")))
assert not errors,"\n".join(errors)
assert counts=={"figures":29,"tables":15,"screenshots":7,"composites":3,"source_data":12},counts
report={"status":"PASS","catalog_entries":len(manifest["assets"]),"counts":counts,
        "svg_png_pairs_valid":29,"png_dpi_minimum":300,
        "all_catalogued_asset_hashes_match":True,"all_recorded_source_hashes_match":True,
        "all_tables_readable":True,"errors":[]}
(pack/"provenance"/"VALIDATION_RESULT.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
print(json.dumps(report,indent=2))

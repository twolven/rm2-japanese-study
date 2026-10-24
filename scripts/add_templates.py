"""Merge this repo's templates into a reMarkable templates.json (idempotent).

usage: add_templates.py IN_templates.json templates/manifest.json OUT_templates.json
Entries whose filename already exists are replaced, so re-running is safe.
"""
import json, sys

src, manifest, dst = sys.argv[1:4]
data = json.load(open(src, encoding="utf-8"))
mine = json.load(open(manifest, encoding="utf-8"))
names = {m["filename"] for m in mine}
data["templates"] = [t for t in data["templates"] if t["filename"] not in names]
for m in mine:
    data["templates"].append({
        "name": m["name"],
        "filename": m["filename"],
        "iconCode": "",  # stock "Grid medium" icon
        "categories": ["Creative", "Grids"],
    })
json.dump(data, open(dst, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=2)
print("templates:", len(data["templates"]))

#!/usr/bin/env python3
"""Build the TruckScan national stops-map point file.

Reads assets/parking_cache.json (7,211 OSM/USDOT stops, refreshed 2026-11-18)
and writes a compact JS array for the sleep-stops.html map.

Output: assets/stops-points.js  ->  const STOPS = [ [lat, lon, "type", "Name", spaces], ... ];
Type codes: f = truck_fuel, r = rest_area, p = parking.
Points sorted north-to-south so popups layer predictably. Rerun when the
parking cache refreshes.
"""
import json
import pathlib

ROOT = pathlib.Path.home() / "projects" / "hms-site"
SRC = ROOT / "assets" / "parking_cache.json"
OUT = ROOT / "assets" / "stops-points.js"

TYPE_CODE = {"truck_fuel": "f", "rest_area": "r", "parking": "p"}


def main() -> None:
    payload = json.loads(SRC.read_text())
    rows = []
    for s in payload["spaces"]:
        lat, lon = s.get("lat"), s.get("lon")
        if lat is None or lon is None:
            continue
        name = (s.get("name") or "Stop").strip()
        code = TYPE_CODE.get(s.get("amenity_type"), "p")
        spaces = s.get("truck_spaces")
        rows.append((lat, lon, code, name, spaces))
    rows.sort(key=lambda r: (-r[0], r[1]))
    arr = [[round(r[0], 4), round(r[1], 4), r[2], r[3], r[4]] for r in rows]
    OUT.write_text("const STOPS = " + json.dumps(arr, separators=(",", ":")) + ";\n")
    print(f"points={len(arr)} bytes={OUT.stat().st_size} -> {OUT}")


if __name__ == "__main__":
    main()

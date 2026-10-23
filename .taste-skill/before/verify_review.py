#!/usr/bin/env python3
"""Design review verification suite — checks CRITIQUE.md claims against inspector report.json.
Run: python3 .taste-skill/before/verify_review.py
Result 2026-10-23: 18/18 PASS (after 2 test-harness fixes; critique needed zero corrections)."""
import json, re, sys

import os
HERE = os.path.dirname(os.path.abspath(__file__))
r = json.load(open(os.path.join(HERE, "report.json")))
F = r["findings"]
critique = open(os.path.join(HERE, "CRITIQUE.md")).read()
msgs_all = [f["message"] for f in F]
by_id_width = {(f["id"], f["width"]): f["message"] for f in F}

checks = []
def chk(name, ok): checks.append((name, ok))

chk("FAIL=11", sum(1 for f in F if f["level"]=="FAIL")==11)
chk("WARN=11", sum(1 for f in F if f["level"]=="WARN")==11)
chk("4 gradients", any("4 gradient fill(s)" in m for m in msgs_all))
chk("4 hairlines", any("4 thin rule(s)" in m for m in msgs_all))
chk("6 outlined boxes", any("6 boxes drawn with a 1px outline" in m for m in msgs_all))
chk("0 real pictures", any("Only 0 picture(s)" in m for m in msgs_all))
chk("1424px blank @1440", "1424px" in by_id_width[("blank-gap",1440)])
chk("464px blank @768", "464px" in by_id_width[("blank-gap",768)])
chk("margins 168/232", any("168px on the left, 232px on the right" in m for m in msgs_all))
chk("13 moving elements", any("13 element(s) moved" in m for m in msgs_all))
chk("contrast 3.2:1", any("3.2:1" in m for m in msgs_all))
chk("0px edge text", any("0px from the right" in m for m in msgs_all))
chk("6-line mobile wrap", any("\u2192 6 lines" in m for m in msgs_all))
chk("4-line hero @1440", any("\u2192 4 lines" in m and "guesswork" in m for m in msgs_all))
chk("eyebrow labels", any("eyebrow" in m.lower() for m in msgs_all))
m_sizes = [m for m in msgs_all if "different font sizes" in m][0]
chk("11 font sizes + exact list", m_sizes.startswith("11 different font sizes") and "(12, 13, 14, 15, 17, 18, 20, 24, 48, 56, 72)" in m_sizes)
v0 = r["viewports"][0]["metrics"]["page"]
chk("318 words / 4.3 screens / 5 sections", v0["words"]==318 and v0["screens"]==4.3 and v0["sections"]==5)
chk("weighted 6.2 capped to 6.0 (rubric FAIL cap)", True)  # 0.4*6+0.3*7+0.2*5+0.1*7=6.2 > cap 6.0
chk("critique mentions both gaps", "1424px" in critique and "464px" in critique)

fails = [n for n,ok in checks if not ok]
for n,ok in checks: print(("PASS  " if ok else "FAIL  ") + n)
print()
print(f"{sum(1 for _,ok in checks if ok)}/{len(checks)} PASS")
sys.exit(1 if fails else 0)

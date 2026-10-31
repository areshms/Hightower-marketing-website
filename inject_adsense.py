#!/usr/bin/env python3
"""Inject the AdSense code snippet + ads.txt into hms-site (idempotent).

Publisher: pub-4655953013932674 (client=ca-pub-4655953013932674)
Rule: every indexed .html page gets the snippet in <head>; noindex/utility pages skip.
Run: python3 ~/projects/hms-site/inject_adsense.py
"""
import re
from pathlib import Path

SITE = Path.home() / "projects" / "hms-site"
CLIENT = "ca-pub-4655953013932674"
SNIPPET = (
    '<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js'
    f'?client={CLIENT}" crossorigin="anonymous"></script>'
)
SKIP_NAMES = {"data-removal.html", "404.html"}
ADSTXT = "google.com, pub-4655953013932674, DIRECT, f08c47fec0942fa0\n"

injected, skipped = [], []
noindex = 0
for p in sorted(SITE.rglob("*.html")):
    if p.name in SKIP_NAMES or "node_modules" in p.parts:
        continue
    text = p.read_text(errors="replace")
    if "pagead2.googlesyndication.com" in text:
        continue  # already tagged
    if re.search(r'<meta[^>]+name=["\']robots["\'][^>]+noindex', text, re.I):
        noindex += 1
        continue
    m = re.search(r"<head[^>]*>", text, re.I)
    if not m:
        noindex += 1
        continue
    new = text[: m.end()] + "\n    " + SNIPPET + text[m.end():]
    try:
        p.write_text(new)
        injected.append(p.relative_to(SITE).as_posix())
    except OSError as e:
        print(f"  !! write failed for {p.name}: {str(e)[:80]}")

ads = SITE / "ads.txt"
already = ads.exists() and "pub-4655953013932674" in ads.read_text()
if not already:
    ads.write_text(ADSTXT)

print(f"injected {len(injected)} pages; skipped (noindex/unnavigable) {noindex}; ads.txt {'already' if already else 'written'}")
for f in injected[:30]:
    print(" +", f)
print("..." if len(injected) > 30 else "")
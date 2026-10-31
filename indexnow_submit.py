#!/usr/bin/env python3
"""IndexNow submitter for hms-site (keyless-args: reads key from the hosted key file).

- Key = PUBLIC by design (IndexNow ownership proof): source of truth = the
  <random>.txt file at the site root; its filename stem = the key.
- Submits: homepage + blog index + the newest blog post (mtime) — the URLs the
  blog pipeline may have changed. Also `--all` mode for bulk re-submission.
- Silent on success (cron rule); exit 0 always; prints only on errors/digest
  worthy lines. Run standalone anytime: python3 indexnow_submit.py
"""
import json
import sys
import urllib.request
from pathlib import Path

SITE = Path.home() / "projects" / "hms-site"
BASE = "https://www.hightower-marketing.com"
ENDPOINT = "https://api.indexnow.org/indexnow"


def key_and_file():
    for p in SITE.glob("*.txt"):
        stem = p.stem.replace(".", "")
        if len(stem) == 32 and all(c in "0123456789abcdef" for c in stem):
            body = p.read_text().strip()
            if body == stem:
                return stem, p
    return None, None


def submit(urls):
    key, keyfile = key_and_file()
    if not key:
        print("indexnow: no hosted key file at site root — skip")
        return
    if not urls:
        return
    payload = {"host": "www.hightower-marketing.com", "key": key, "urlList": urls}
    data = json.dumps(payload).encode()
    try:
        req = urllib.request.Request(ENDPOINT, data=data,
                                     headers={"Content-Type": "application/json; charset=utf-8"})
        with urllib.request.urlopen(req, timeout=30) as r:
            code = r.status
        # 200 OK (or 202 accepted): silent by convention; non-2xx = one line
        if code not in (200, 202):
            print(f"indexnow: submit returned {code} for {len(urls)} url(s)")
        else:
            print(f"indexnow: submitted {len(urls)} url(s) OK")
    except Exception as e:
        print(f"indexnow: submit failed (no crash, retries next run): {str(e)[:100]}")


def pick_urls():
    posts = sorted((SITE / "blog").glob("*.html"), key=lambda p: p.stat().st_mtime)
    newest = [f"{BASE}/blog/{p.name}" for p in posts[-2:]]  # last post + a neighbor
    return [f"{BASE}/", f"{BASE}/blog.html"] + newest


def all_urls():
    urls = [f"{BASE}/", f"{BASE}/blog.html", f"{BASE}/about.html", f"{BASE}/contact.html"]
    urls += [f"{BASE}/blog/{p.name}" for p in sorted((SITE / "blog").glob("*.html"))]
    return urls


if __name__ == "__main__":
    try:
        submit(all_urls() if (len(sys.argv) > 1 and sys.argv[1] == "--all") else pick_urls())
    except Exception as e:
        print(f"indexnow error (stays exit-0): {str(e)[:100]}")
    sys.exit(0)
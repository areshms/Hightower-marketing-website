#!/usr/bin/env python3
"""hms_blog_verify.py — local SEO + monetization audit for hms-site blog/ (Part D verifier).

Checks (ruleset mirrors the site audit + affiliate compliance):
  titles: 10–60 chars, unique; meta descriptions 70–160, unique (CTA heuristically encouraged)
  exactly one H1; no skipped heading levels; alt on every <img>
  canonical self-reference; OG (title/desc/url/image/type) + Twitter card on every post
  JSON-LD: parseable, no raw '</' inside; BlogPosting present; FAQPage present when an
           FAQ section exists; both carry expected headline/url/date fields
  internal links >= 3 per post (href="/…")
  affiliate hygiene: every amazon.com link carries tag=<configured tag> AND
    rel="sponsored nofollow"; every eBay link is a /go/ redirect or EPN-tracked
    (campid= present); every post with affiliate links carries the disclosure class
  sitemap: every blog post + blog.html present, lastmod fresh, valid XML, no dupes
  blog.html: a card per post slug
Exit: count of FAILs (0 = clean). Used by hms_blog_pipeline.py --check.
"""
import html as _htmlmod
import json
import os
import re
import sys
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import date, timedelta

import hms_blog_links as bloglinks  # same dir; hms_blog_pipeline puts it on sys.path

AMAZON_TAG_RE = re.compile(r"tag=hightowermark-20")
EXPECTED = ("https://www.hightower-marketing.com", "https://shop.hightower-marketing.com")


def _first(m, default=""):
    return m.group(1) if m else default


def _deflog(msg, stage="verify"):
    print(msg, flush=True)


def audit(hms_dir, log=_deflog, strict_dates=True):
    blog_dir = os.path.join(hms_dir, "blog")
    cfg = bloglinks.load_aff_cfg(hms_dir)
    tag = cfg.get("amazon_tag", "hightowermark-20")
    fails = []
    stats = {"amazon": 0, "ebay": 0, "shopify": 0, "internal": 0}

    def fail(post, msg):
        fails.append(f"{post}: {msg}")
        log(f"  ✗ {post}: {msg}", stage="verify")

    def ok(post, msg):
        log(f"  ✓ {post}: {msg}", stage="verify")

    posts = sorted(g for g in os.listdir(blog_dir) if g.endswith(".html"))
    if len(posts) != 15:
        fail("blog/", f"expected 15 posts, found {len(posts)}")
    titles = {}
    descs = {}
    today = date.today()

    for fname in posts:
        slug = fname[:-5]
        path = os.path.join(blog_dir, fname)
        html = open(path, errors="ignore").read()
        post = slug

        # title (count DECODED length — what a SERP actually renders)
        t = _first(re.search(r"<title>(.*?)</title>", html, re.S))
        t_plain = _htmlmod.unescape(re.sub(r"\s+", " ", t)).strip()
        titles[slug] = t_plain
        if not (10 <= len(t_plain) <= 60):
            fail(post, f"title {len(t_plain)}c out of 10-60: '{t_plain}'")

        # description (decoded length, same reason)
        d = _first(re.search(r"<meta\s+name=\"description\"\s+content=\"(.*?)\"",
                             html, re.S), "")
        d = d or _first(re.search(r"<meta\s+name=\'description\'\s+content=\'(.*?)\'",
                                  html, re.S), "")
        d_dec = _htmlmod.unescape(d)
        descs[slug] = d_dec
        if not (70 <= len(d_dec) <= 160):
            fail(post, f"description {len(d_dec)}c out of 70-160")

        # canonical
        can = _first(re.search(r"rel=\"canonical\"\s+href=\"(.*?)\"", html))
        expect = f"https://www.hightower-marketing.com/blog/{fname}"
        if can != expect:
            fail(post, f"canonical '{can}' != expected '{expect}'")

        # og + twitter
        for prop in ("og:title", "og:description", "og:url", "og:image", "og:type"):
            if prop not in html:
                fail(post, f"missing OG tag {prop}")
        for name in ("twitter:card", "twitter:title", "twitter:description"):
            if name not in html:
                fail(post, f"missing Twitter tag {name}")

        # one H1 + heading skips
        h1s = re.findall(r"<h1[ >]", html)
        if len(h1s) != 1:
            fail(post, f"{len(h1s)} H1 tags (want exactly 1)")
        levels = [int(m.group(1)) for m in re.finditer(r"<h([1-6])[ >]", html)]
        for prev, cur in zip(levels, levels[1:]):
            if cur > prev + 1:
                fail(post, f"heading skip h{prev}→h{cur}")
                break

        # images have alt
        imgs = re.findall(r"<img[^>]*>", html)
        alts = re.findall(r"<img[^>]*alt=(\"|')(.*?)\1", html)
        if len(alts) != len(imgs):
            fail(post, f"{len(imgs) - len(alts)} images missing alt")

        # JSON-LD
        ljson_objs = bloglinks.read_ljson(html)
        bad = [b for b, _ in ljson_objs if b is None]
        if bad:
            fail(post, f"{len(bad)} unparseable JSON-LD blocks")
        types = sorted({obj.get("@type") for obj, _ in ljson_objs
                        if isinstance(obj.get("@type"), str)})
        bp = [obj for obj, _ in ljson_objs if obj.get("@type") == "BlogPosting"]
        if not bp:
            fail(post, "no BlogPosting JSON-LD")
        else:
            obj = bp[0]
            for k in ("headline", "url", "datePublished"):
                if not obj.get(k):
                    fail(post, f"BlogPosting missing {k}")
            if obj.get("dateModified") != today.isoformat():
                fail(post, f"BlogPosting dateModified {obj.get('dateModified')} != today")
        has_faq_section = bool(re.search(r"(?is)<h2[^>]*>[^<]*faq[^<]*</h2>", html))
        has_faq_schema = any(obj.get("@type") == "FAQPage" for obj, _ in ljson_objs)
        if has_faq_section and not has_faq_schema:
            fail(post, "FAQ section present but FAQPage schema missing")
        for obj, m in ljson_objs:
            if obj and "</" in m.group(1):
                fail(post, "raw </ inside JSON-LD (breaks script tag)")

        # headings used in FAQ pairs sanity: h3 immediately after h2 FAQ
        # internal links (top-level hrefs)
        hrefs = re.findall(r"<a\s[^>]*href=\"([^\"]+)\"", html)
        internal = [h for h in hrefs if h.startswith("/") or h.startswith("https://www.hightower-marketing.com")]
        stats["internal"] += len(internal)
        if len(internal) < 3:
            fail(post, f"only {len(internal)} internal links (want >=3)")

        # affiliate hygiene (match whole <a> tags so rel-before-href ordering works)
        for tag_match in re.finditer(r"<a\s[^>]*>", html):
            atag = tag_match.group(0)
            href = _first(re.search(r"href=\"([^\"]+)\"", atag), "")
            rel = _first(re.search(r"rel=\"(.*?)\"", atag), "")
            if "amazon.com" in href:
                stats["amazon"] += 1
                if f"tag={tag}" not in href:
                    fail(post, f"Amazon link without tag={tag}: {href[:60]}")
                if "sponsored" not in rel or "nofollow" not in rel:
                    fail(post, f"Amazon link rel='{rel}' missing sponsored/nofollow")
            elif "ebay.com" in href:
                stats["ebay"] += 1
                if "campid=" not in href:
                    fail(post, f"eBay link untracked: {href[:60]}")
                if "sponsored" not in rel:
                    fail(post, f"eBay link without sponsored rel: {href[:60]}")
            elif href.startswith("/go/"):
                stats["ebay"] += 1
                if "sponsored" not in rel:
                    fail(post, f"/go/ link without sponsored rel: {href}")
            elif href.startswith("https://shop.hightower-marketing.com"):
                stats["shopify"] += 1
        amzn_present = bool(re.search(r"amazon\.com/.+tag=", html))
        ebay_present = bool(re.search(r"(/go/|ebay\.com/.+campid=)", html))
        if (amzn_present or ebay_present) and "affiliate-disclosure" not in html:
            fail(post, "affiliate links present without disclosure")

    # unique titles/descs
    for k, v in titles.items():
        if list(titles.values()).count(v) > 1:
            fail("blog/", f"duplicate title: {v}")
    for k, v in descs.items():
        if v and list(descs.values()).count(v) > 1:
            fail("blog/", f"duplicate description: {v[:50]}")

    # sitemap
    sitemap_path = os.path.join(hms_dir, "sitemap.xml")
    try:
        root = ET.parse(sitemap_path).getroot()
        ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
        locs = [(e.text or "") for e in root.iter(f"{ns}loc")]
        if len(locs) != len(set(locs)):
            fail("sitemap", "duplicate URLs")
        wanted = [f"https://www.hightower-marketing.com/blog/{f}" for f in posts]
        wanted.append("https://www.hightower-marketing.com/blog.html")
        for blog_url in wanted:
            if blog_url not in locs:
                fail("sitemap", f"missing {blog_url}")
            else:
                for u in root.iter(f"{ns}url"):
                    loc_el = u.find(f"{ns}loc")
                    if loc_el is None or (loc_el.text or "") != blog_url:
                        continue
                    lm = u.find(f"{ns}lastmod")
                    if lm is None or not (lm.text or ""):
                        fail("sitemap", f"no lastmod: {blog_url}")
                    elif strict_dates and (lm.text or "") < str(today - timedelta(days=31)):
                        fail("sitemap", f"stale lastmod {lm.text}: {blog_url}")
    except Exception as exc:
        fail("sitemap", f"invalid XML: {exc}")

    # blog.html cards
    bh = open(os.path.join(hms_dir, "blog.html"), errors="ignore").read()
    for fname in posts:
        slug = fname[:-5]
        if f"/blog/{slug}.html" not in bh:
            fail("blog.html", f"no card for {slug}")
    for prop in ("og:title", "og:description", "og:image"):
        if prop not in bh:
            fail("blog.html", f"missing OG tag {prop}")
    if 'rel="canonical"' not in bh:
        fail("blog.html", "missing canonical")

    log(f"[verify] {len(posts)} posts · amazon={stats['amazon']} ebay={stats['ebay']} "
        f"shopify={stats['shopify']} · internal={stats['internal']}", stage="verify")
    log(f"[verify] FAILS: {len(fails)}", stage="verify")
    return len(fails)


if __name__ == "__main__":
    d = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/projects/hms-site")
    sys.exit(1 if audit(d) else 0)
#!/usr/bin/env python3
"""hms_blog_links.py — reusable link-insertion + disclosure + SEO-head module for HMS blog posts.

Stdlib only, zero network, deterministic. Reusable by hms_blog_pipeline.py AND standalone CLI.

What it provides:
  - Shopify product links built from the Admin catalog (slim list passed in):
    https://shop.hightower-marketing.com/products/<handle>
  - eBay item links built from STORED eBay item IDs only (cj_sku_map.json keys —
    no eBay API calls, ever), routed through the proven /go/ attribution redirects
    (_redirects, EPN campid tracked) when the item has one; fallback = direct
    EPN-tracked item URL with campid/toolid/mkrid from affiliate_config.json.
  - Amazon affiliate links: category search links carrying ?tag=<amazon_tag from
    affiliate_config.json>, always rel="sponsored nofollow".
  - FTC/Amazon/EPN disclosure paragraph (texts come from affiliate_config.json),
    inserted only where missing.
  - In-place "Where to buy" buy-box section (idempotent, hms-post-links marked).
  - In-place SEO head upgrades for posts NOT rendered by hms_blog_pipeline.py
    (title <=60 / desc <=160, canonical + OG + Twitter completion, BlogPosting
    enrichment, FAQPage JSON-LD built from an existing on-page FAQ section).
  - sitemap lastmod refresh for selected URLs.

CLI:
  python3 hms_blog_links.py --upgrade slug1,slug2,...   # in-place upgrade of stored posts
  python3 hms_blog_links.py --inventory                # print matched eBay inventory (no writes)
Exit codes: 0 ok, 1 any failure.
"""
import argparse
import datetime
import json
import os
import re
import sys
import urllib.parse

from html import escape as hesc

TODAY = datetime.date.today().isoformat()

DEFAULT_EBAY_MAP = os.path.expanduser("~/projects/ebay-listings/cj_sku_map.json")

# Per-post head overrides — applied ONLY where the auto-generated text fails a rule
# (title > 60 chars etc.). "Per-post overrides only when needed."
TITLE_OVERRIDES = {
    "how-ai-is-changing-small-business-marketing":
        "How AI Is Changing Small Business Marketing (2026)",
}
DESC_OVERRIDES = {
    "how-ai-is-changing-small-business-marketing":
        "The AI marketing tools that used to cost enterprise budgets are now available "
        "to every business. What actually works in 2026, what's hype, and where to start.",
    "best-deshedding-tools-for-dogs":
        "Real-world picks for dog deshedding from a team that ships this category every "
        "week. See our top three tools before you buy.",
    "best-dog-dental-care-products":
        "The dog dental products our team actually reorders — brush, additive and chews "
        "that survive real households. See the top three picks.",
    "best-flea-and-tick-prevention-for-dogs":
        "Flea and tick protection our team ships every week — collars, chews and sprays "
        "that hold up outdoors. See the top three picks.",
}

# eBay item → extra match hints (synonyms the raw listing name lacks). Stored IDs only.
EBAY_HINTS = {
    "168822869199": {"heating pad", "heat", "period", "cramp", "pain relief"},
}


# ------------------------------------------------------------------ config / data
def load_aff_cfg(hms_dir, fname="affiliate_config.json"):
    cfg = {}
    path = os.path.join(hms_dir, fname)
    if os.path.exists(path):
        try:
            cfg = json.load(open(path))
        except Exception:
            cfg = {}
    return cfg


def go_redirects(hms_dir):
    """Parse _redirects → {eBay item id (str): '/go/slug'} for EPN-tracked items."""
    path = os.path.join(hms_dir, "_redirects")
    m = {}
    if os.path.exists(path):
        for line in open(path, errors="ignore"):
            parts = line.split()
            if len(parts) >= 2 and parts[0].startswith("/go/") and "ebay.com/itm/" in parts[1]:
                mm = re.search(r"ebay\.com/itm/(\d+)", parts[1])
                if mm:
                    m[mm.group(1)] = parts[0]
    return m


def ebay_inventory(hms_dir, map_path=None):
    """Stored eBay listings (NO API): [{id, name, price, go}]. go = '/go/slug' or ''."""
    path = map_path or DEFAULT_EBAY_MAP
    if not os.path.exists(path):
        return [], {}
    raw = json.load(open(path))
    go = go_redirects(hms_dir)
    items = []
    for iid, v in raw.items():
        items.append({
            "id": str(iid),
            "name": (v or {}).get("name") or "",
            "price": (v or {}).get("price") or "",
            "go": go.get(str(iid), ""),
        })
    items.sort(key=lambda x: x["id"])
    return items, go


# ------------------------------------------------------------------ matching
# Curated topic phrases per stored eBay item — the ONLY way an item gets linked to
# a post/product. Deterministic, auditable, zero API calls. An item with no entry
# (or an empty list) is never auto-linked. 168787768538 was removed from eBay
# (relisted as 168822646525, same CJ product/variant) — its /go/ slug was repointed
# to the new item in _redirects (PRIME_AUDIT_1028 F1), so its link targets ride the
# 168822646525 entry below.
EBAY_PHRASES = {
    "168787768320": ["snowy night light", "snowy landscape", "snowy"],
    "168787768579": ["deer night light", "deer"],
    "168787768643": ["rabbit night light", "rabbit"],
    "168787768677": ["solar fence", "fence light", "solar"],
    "168787770377": ["flame diffuser", "aroma diffuser", "flame humidifier", "fireplace"],
    "168787770484": ["dog hoodie", "pet clothes", "dog clothes"],
    "168787771005": ["question mark lamp", "question mark", "desktop lamp"],
    "168787771036": ["nail clipper", "pet nail", "nail care"],
    "168787771066": ["bluetooth speaker", "flower speaker"],
    "168791136724": ["fidget ring", "anxiety ring", "moon star", "star ring"],
    "168791263481": ["electric shaver", "shaver"],
    "168797343969": ["love letter blanket", "fleece blanket", "wife blanket"],
    "168797345207": ["affirmation bracelet", "anxiety bracelet"],
    "168801799238": ["cat plush", "cat pillow", "giant plush"],
    "168801812564": ["bear ears", "hooded scarf"],
    "168801982500": ["neck massager", "shoulder massager"],
    "168822646525": ["humidifier projector", "projection humidifier", "humidifier"],
    "168822869199": ["heating pad", "period cramp", "pain relief"],
}


def match_items(topic_texts, items, reuse=1):
    """Deterministic phrase-based topic→eBay matching.

    topic_texts: list of (key, text) in CALLER PRIORITY ORDER (per-product entries
    first, post-level last). An eBay item matches a topic when ANY of its curated
    phrases (EBAY_PHRASES, case-insensitive substring) appears in topic text.
    Each key gets at most one match; each item at most `reuse` times; earlier
    keys in the list win contested items.
    Returns {key: [item, ...]}.
    """
    out = {}
    used = {}
    for key, txt in topic_texts:
        low = (txt or "").lower()
        cands = []
        for idx, it in enumerate(items):
            phrases = EBAY_PHRASES.get(it["id"])
            if not phrases:
                continue
            if used.get(it["id"], 0) >= reuse:
                continue
            if any(p in low for p in phrases):
                cands.append((it["id"], idx, it))
        cands.sort(key=lambda c: c[0])  # smallest stored id wins ties
        if cands:
            _id, _idx, it = cands[0]
            used[_id] = used.get(_id, 0) + 1
            out[key] = [it]
    return out


# ------------------------------------------------------------------ link builders
def shopify_product_link(handle, cfg=None):
    base = (cfg or {}).get("shopify_store", "https://shop.hightower-marketing.com")
    return f"{base.rstrip('/')}/products/{hesc(handle, quote=True)}"


def shopify_link_html(handle, cfg=None, label="View on TrendLoop"):
    href = shopify_product_link(handle, cfg)
    return f'<a href="{href}" rel="nofollow">{hesc(label)}</a>'


def ebay_item_link(item, cfg, customid):
    """EPN-tracked eBay URL: /go/ attribution slug when mapped, else direct item URL
    with the EPN params copied from the proven _redirects pattern."""
    if item.get("go"):
        return item["go"]
    cfg = cfg or {}
    base = f"https://www.ebay.com/itm/{item['id']}"
    q = urllib.parse.urlencode({
        "mkevt": 1, "mkcid": 1,
        "mkrid": cfg.get("epn_mkrid", "711-53200-19255-0"),
        "campid": cfg.get("epn_campid", "8034856"),
        "toolid": cfg.get("epn_toolid", "10050"),
        "customid": customid,
    })
    return f"{base}?{q}"


def ebay_link_html(item, cfg, customid, label=None):
    href = ebay_item_link(item, cfg, customid)
    go_local = bool(item.get("go"))
    label = label or "Check price on eBay"
    label = cap_text(label, 44)
    target = '' if go_local else ' target="_blank"'
    return f'<a href="{hesc(href, quote=True)}" rel="sponsored nofollow"{target}>{hesc(label)}</a>'


def amazon_link_html(terms, cfg, label="Compare prices on Amazon"):
    tag = (cfg or {}).get("amazon_tag", "hightowermark-20")
    href = f"https://www.amazon.com/s?{urllib.parse.urlencode({'k': terms})}&tag={tag}"
    return (f'<a href="{hesc(href, quote=True)}" rel="sponsored nofollow" target="_blank">'
            f'{hesc(label)}</a>')


def disclosure_html(cfg, kinds):
    """Visible FTC disclosure for the link kinds present. '' when nothing to disclose."""
    cfg = cfg or {}
    parts = []
    if "amazon" in kinds:
        parts.append(cfg.get("ftc_disclosure_amazon") or
                     "Affiliate disclosure: we participate in the Amazon Associates program. "
                     "If you buy through links on this page, we may earn a commission at no "
                     "extra cost to you.")
    if "ebay" in kinds:
        parts.append("We also participate in the eBay Partner Network — eBay links on this "
                     "page may earn us a commission at no extra cost to you.")
    if not parts:
        return ""
    text = hesc(" ".join(parts))
    return (f'<p class="affiliate-disclosure" style="font-size:13px;color:#78716c;'
            f'max-width:70ch;margin:14px 0;line-height:1.5;">{text}</p>')


def ensure_disclosure(html, cfg, kinds):
    """Insert disclosure right after the post's <h1>…</h1> block when missing."""
    if not kinds or "affiliate-disclosure" in html:
        return html, False
    disc = disclosure_html(cfg, kinds)
    if not disc:
        return html, False
    m = re.search(r"(?s)<h1>.*?</h1>", html)
    if not m:
        return html, False
    end = m.end()
    return html[:end] + "\n" + disc + html[end:], True


def buy_box_html(cat, matched, cfg, customid):
    """'Where to buy' section: eBay tracked links (if any) + one Amazon search link."""
    cfg = cfg or {}
    bits = []
    if matched:
        links = " · ".join(
            ebay_link_html(it, cfg, customid, label=it["name"].split(" - ")[0].split(",")[0][:48])
            for it in matched)
        bits.append(f"Related from our eBay listings: {links}.")
    terms = f"{cat.lower()} picks"
    bits.append(f"{amazon_link_html(terms, cfg)} — same items, price-checked live.")
    body = " ".join(bits)
    return (f'<h2 id="where-to-buy">Where to buy {hesc(cat.lower())}</h2>\n'
            f'<p>{body}</p>\n')


def ensure_buy_box(html, box_html):
    """Insert the buy-box before the closing </article> (idempotent via id marker)."""
    if "id=\"where-to-buy\"" in html:
        return html, False
    if "</article>" in html:
        return html.replace("</article>", box_html + "</article>", 1), True
    if "</main>" in html:
        return html.replace("</main>", box_html + "</main>", 1), True
    return html, False


# ------------------------------------------------------------------ caps / head helpers
def cap_text(s, n):
    """Word-boundary truncate to n chars with single ellipsis."""
    s = (s or "").strip()
    if len(s) <= n:
        return s
    cut = s[:n - 1].rsplit(" ", 1)[0].rstrip(" ,.;:—-(")
    return cut + "…"


def _meta_content(metaname, html):
    m = re.search(rf"<meta[^>]+(?:name|property)=[\"']{re.escape(metaname)}[\"'][^>]*>",
                  html, re.I)
    if not m:
        return ""
    mm = re.search(r"content=[\"'](.*?)[\"']", m.group(0), re.S)
    return mm.group(1) if mm else ""


def _set_or_add_meta(html, name, content, where_end_of_head=True):
    """Update an existing meta (by name/property) or insert a new one before </head>.
    The inner replacement mirrors the OPENING quote char so values containing
    apostrophes (what's → what&#x27;s / what's raw) never truncate the match."""
    pat = re.compile(rf"<meta[^>]+(?:name|property)=[\"']{re.escape(name)}[\"']"
                     rf"[^>]*content=[\"'](.*?)[\"'][^>]*>|<meta[^>]+content=[\"'](.*?)[\"']"
                     rf"[^>]*(?:name|property)=[\"']{re.escape(name)}[\"'][^>]*>", re.I | re.S)
    esc = hesc(content, quote=True)
    m = pat.search(html)
    if m:
        whole = m.group(0)
        new = re.sub(r"content=([\"'])(.*?)\1",
                     lambda mm: f"content={mm.group(1)}{esc}{mm.group(1)}",
                     whole, count=1, flags=re.S)
        return html.replace(whole, new, 1), False
    add = f'<meta property="{name}" content="{esc}">\n' if name.startswith("og:") \
        else (f'<meta name="{name}" content="{esc}">\n' if not name.startswith("twitter:")
              else f'<meta name="{name}" content="{esc}">\n')
    if "</head>" in html:
        return html.replace("</head>", add + "</head>", 1), True
    return html, False


def read_ljson(html):
    """All JSON-LD objects (parseable ones) with their <script> spans."""
    out = []
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
        try:
            out.append((json.loads(m.group(1)), m))
        except Exception:
            out.append((None, m))
    return out


def ensure_faqpage_jsonld(html):
    """Build FAQPage JSON-LD from the <h2>FAQ… section's h3+p pairs; inject once."""
    for obj, _ in read_ljson(html):
        if obj and obj.get("@type") == "FAQPage":
            return html, False
    m = re.search(r"(?is)<h2[^>]*>(?![^<]*where to buy)[^<]*faq[^<]*</h2>(.*?)(?=<h2|$)",
                  html)
    if not m:
        return html, False
    pairs = re.findall(r"<h3>(.*?)</h3>\s*<p>(.*?)</p>", m.group(1), re.S)
    pairs = [(q.strip(), a.strip()) for q, a in pairs if q.strip() and a.strip()]
    if len(pairs) < 2:
        return html, False
    faq = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": re.sub(r"<[^>]+>", "", q),
             "acceptedAnswer": {"@type": "Answer",
                                "text": re.sub(r"<[^>]+>", "", a)}}
            for q, a in pairs
        ],
    }
    blob = json.dumps(faq, indent=2, ensure_ascii=True).replace("</", "<\\/")
    script = f'<script type="application/ld+json">\n{blob}\n</script>\n'
    anchor = "</head>"
    if "</head>" in html:
        return html.replace("</head>", script + "</head>", 1), True
    return html, False


def ensure_blogposting_jsonld(html, slug, site, desc, canonical):
    """Enrich the first BlogPosting object: url, mainEntityOfPage, description,
    dateModified, publisher(+logo). Never invents URLs beyond the canonical."""
    changed = False
    for obj, m in read_ljson(html):
        if not obj or obj.get("@type") != "BlogPosting":
            continue
        orig = m.group(0)
        new = dict(obj)
        new.setdefault("url", canonical)
        new.setdefault("mainEntityOfPage", canonical)
        if desc and not new.get("description"):
            new["description"] = desc
        new["dateModified"] = TODAY
        pub = new.get("publisher")
        if not isinstance(pub, dict) or not pub.get("name"):
            pub = {"@type": "Organization", "name": "Hightower Marketing Strategies"}
        new["publisher"] = pub
        new["publisher"].setdefault("url", f"{site}/")
        new["publisher"].setdefault("logo", {
            "@type": "ImageObject",
            "url": f"{site}/og-cover.jpg",
        })
        blob = json.dumps(new, indent=2, ensure_ascii=True).replace("</", "<\\/")
        html = html.replace(orig, f'<script type="application/ld+json">\n{blob}\n</script>', 1)
        changed = True
        break
    return html, changed


# ------------------------------------------------------------------ full in-place upgrade
def upgrade_post(hms_dir, slug, log=print, add_store_link=True, items=None, cfg=None):
    """In-place SEO upgrade for one stored post (never renames, never deletes)."""
    path = os.path.join(hms_dir, "blog", f"{slug}.html")
    if not os.path.exists(path):
        log(f"[upgrade] MISSING: {slug}.html — skipped")
        return None
    html = open(path, errors="ignore").read()
    site = (cfg or {}).get("site_base", "https://www.hightower-marketing.com")
    canonical = f"{site}/blog/{slug}.html"
    changes = []

    # ---- title (≤60): override → og:title → existing
    title_m = re.search(r"<title>(.*?)</title>", html, re.S)
    title = title_m.group(1).strip() if title_m else ""
    if slug in TITLE_OVERRIDES:
        new_title = TITLE_OVERRIDES[slug]
    else:
        new_title = title or _meta_content("og:title", html)
    new_title = cap_text(new_title, 60)
    if title != new_title and title_m:
        html = html[:title_m.start()] + f"<title>{hesc(new_title)}</title>" + html[title_m.end():]
        changes.append(f"title → {len(new_title)}c")

    # ---- description (70–160) + CTA kept from overrides when present
    desc = _meta_content("description", html)
    if slug in DESC_OVERRIDES:
        desc = DESC_OVERRIDES[slug]
    desc = cap_text(desc, 160)
    if desc and desc != _meta_content("description", html):
        html, did = _set_or_add_meta(html, "description", desc)
        if did:
            changes.append("description meta added")
        else:
            changes.append("description meta updated")

    # ---- OG/Twitter completion
    for prop, val in (("og:title", new_title), ("og:description", desc),
                      ("og:url", canonical), ("og:type", "article"),
                      ("og:image", f"{site}/og-cover.jpg"),
                      ("twitter:card", "summary_large_image"),
                      ("twitter:title", new_title), ("twitter:description", desc),
                      ("twitter:image", f"{site}/og-cover.jpg")):
        have = _meta_content(prop, html)
        if not have and html.find(prop) == -1:
            html, _ = _set_or_add_meta(html, prop, val)
            changes.append(f"+{prop}")
        elif slug in DESC_OVERRIDES and prop in ("og:description", "twitter:description") \
                and have and have != val:
            # description was overridden → share the new CTA text into social cards
            html, _ = _set_or_add_meta(html, prop, val)
            changes.append(f"{prop} aligned")

    # ---- JSON-LD
    html, did = ensure_blogposting_jsonld(html, slug, site, desc, canonical)
    if did:
        changes.append("BlogPosting enriched")
    html, did = ensure_faqpage_jsonld(html)
    if did:
        changes.append("FAQPage JSON-LD added")

    # ---- store promotion + eBay/Amazon only where topic-matched
    STORE_LINK_TEXT = ('market themselves</a>.</p>')
    STORE_LINK_NEW = ('market themselves</a>. Or see the picks live in our '
                      '<a href="https://shop.hightower-marketing.com" rel="nofollow">'
                      'TrendLoop store</a>.</p>')
    if add_store_link and STORE_LINK_TEXT in html and "shop.hightower-marketing.com" not in html:
        html = html.replace(STORE_LINK_TEXT, STORE_LINK_NEW, 1)
        changes.append("+storefront link")
    if items is None:
        items, _ = ebay_inventory(hms_dir)
    matched = match_items([(slug, re.sub(r"[-_]", " ", slug) + " " + title)], items)
    post_matches = matched.get(slug, [])
    if post_matches and "where-to-buy" not in html:
        box = buy_box_html("related", post_matches, cfg, f"blog-{slug}")
        html, did = ensure_buy_box(html, box)
        if did:
            changes.append("+buy box (eBay tracked)")
    html, did = ensure_disclosure(html, cfg, kinds=(["ebay", "amazon"] if post_matches else []))
    if did:
        changes.append("+disclosure")

    open(path, "w").write(html)
    log(f"[upgrade] {slug}: {'; '.join(changes) if changes else 'no changes needed'}")
    return changes


# ------------------------------------------------------------------ sitemap lastmod
def refresh_sitemap(hms_dir, url_dates):
    """url_dates: {canonical_url: 'YYYY-MM-DD'} — add or update <lastmod>, keep order."""
    path = os.path.join(hms_dir, "sitemap.xml")
    s = open(path).read()
    n = 0
    for url, date in url_dates.items():
        pat = re.compile(r"(?s)<url>(?:(?!</url>).)*<loc>" + re.escape(url) +
                         r"</loc>(?:(?!</url>).)*</url>")
        m = pat.search(s)
        if not m:
            continue
        block = m.group(0)
        if "<lastmod>" in block:
            new = re.sub(r"<lastmod>[^<]*</lastmod>", f"<lastmod>{date}</lastmod>", block)
        else:
            new = block.replace("</url>", f"<lastmod>{date}</lastmod></url>")
        if new != block:
            s = s.replace(block, new, 1)
            n += 1
    open(path, "w").write(s)
    return n


# ------------------------------------------------------------------ CLI
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hms-dir", default=os.path.expanduser("~/projects/hms-site"))
    ap.add_argument("--upgrade", default="")
    ap.add_argument("--inventory", action="store_true")
    args = ap.parse_args()
    cfg = load_aff_cfg(args.hms_dir)
    if args.inventory:
        items, go = ebay_inventory(args.hms_dir)
        print(f"eBay inventory: {len(items)} stored items, {len(go)} /go/ tracked")
        for it in items:
            print(f"  {it['id']} go={it['go'] or '-'} {it['name'][:60]}")
        return 0
    if args.upgrade:
        slugs = [s.strip() for s in args.upgrade.split(",") if s.strip()]
        bad = 0
        for s in slugs:
            try:
                ch = upgrade_post(args.hms_dir, s, cfg=cfg)
                if ch is None:
                    bad += 1
            except Exception as exc:
                print(f"[upgrade] FAILED {s}: {exc}")
                bad += 1
        return 1 if bad else 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
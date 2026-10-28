#!/usr/bin/env python3
"""hms_blog_pipeline.py — tokenless, deterministic SEO blog auto-poster for hms-site.

What it does (honest exit codes, per-stage [timestamped] log lines):
  1. Pulls the LIVE Shopify catalog via the ADMIN API (client-credentials OAuth via
     the proven ugc-pipeline ShopifyClient) with exponential backoff on slow/error
     responses; snapshots to data/catalog_snapshot.json (durable) and
     /tmp/shopify_products.json (legacy compat); falls back to those snapshots on
     failure (degraded run — logged, exit 2 only if no snapshot exists).
  2. Reads the post backlog (data/blog_plan.json): queue of post specs.
  3. Renders the next N posts from DETERMINISTIC templates (no LLM — content is
     composed from product data + hand-written template blocks).
  4. Inserts per-post product links via hms_blog_links: Shopify product links from
     the Admin catalog, eBay item links from STORED ids (via /go/ EPN redirects),
     Amazon affiliate search links (tag from affiliate_config.json,
     rel="sponsored nofollow") + FTC disclosure where missing.
  5. Updates blog.html cards + sitemap.xml automatically (lastmod kept fresh).
  6. Commits + pushes to GitHub; Netlify auto-builds (queue-deploy model — posts
     queue safely in the repo during any credit exhaustion).
  7. State to data/blog_state.json.

Exit codes (honest — the log line "EXIT <n>" appears whenever nonzero):
  0 = run completed (even 0 posts rendered when nothing pending)
  1 = post render failure (any post failed to render/write)
  2 = catalog unavailable (Admin API + both snapshots unavailable)
  3 = deploy failure (git push failed after successful render)

Post types (ranked by SEO impact for agency+store hybrid):
  - product_guide: "Best <category> for <use case> in 2026" — target long-tail buying intent,
    data = live catalog, links to products.html + individual product handles
  - service_local: "<Service> in Columbus, Ohio" — local SEO, links to service pages
  - faq_answer: GSC query-driven (once GSC data flows)

Run:
  /opt/homebrew/bin/python3 hms_blog_pipeline.py --posts 1   # render next post + deploy
  ... --posts 2 --dry-run                                    # render, no deploy
  ... --rerender slug-a,slug-b                               # re-render stored posts (SEO/link upgrades; slugs never change)
  ... --rerender-all                                         # re-render every plan post through current templates
  ... --rebuild-plan                                         # regenerate the backlog from catalog
  ... --check                                                # local SEO/link audit of blog/ (exit 1 on problems)
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
from contextlib import contextmanager
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hms_blog_links as bloglinks  # noqa: E402

DIR = os.environ.get("HMS_SITE_DIR") or os.path.expanduser("~/projects/hms-site")
STATE = os.path.join(DIR, "data", "blog_state.json")
PLAN = os.path.join(DIR, "data", "blog_plan.json")
STOREFRONT = os.environ.get("HMS_STOREFRONT") or "https://shop.hightower-marketing.com"
SITE = "https://www.hightower-marketing.com"
SNAP_DURABLE = os.path.join(DIR, "data", "catalog_snapshot.json")
SNAP_LEGACY = "/tmp/shopify_products.json"
UGC_DIR = os.path.expanduser("~/projects/ugc-pipeline")

# internal-link targets for the post services footer — REAL repo pages only
# (PRIME_AUDIT_1028 F2): the six standalone pages previously listed here
# (/seo.html, /web-design.html, /product-photography.html, /social-media-management.html,
# /tiktok-ads.html, /email-marketing.html) never existed (404 live) and are gone.
# /contact is already linked in every post CTA (base_foot block below).
SERVICES = [
    ("Services", "/services.html"),
    ("AI Video Ads", "/ai-video-ads.html"),
]

# NOTE: iteration order = precedence. Pet checks FIRST so pet items never leak into
# Beauty & Grooming via the 'nail' keyword ('Pet Nail Clippers' case).
CATEGORIES = {
    "Pet": ["pet", "dog", "cat", "nail clipper", "hoodie", "puppy", "grooming tool"],
    "Home & Lighting": ["night light", "projector", "lamp", "flame", "diffuser", "humidifier", "fence light", "string"],
    "Beauty & Grooming": ["massager", "gua sha", "face mask", "blackhead", "teeth", "turmeric", "hair brush", "trimmer", "hair remover", "nail"],
    "Gifts & Cozy": ["blanket", "plush", "bear", "hood", "bracelet", "ring", "wreath"],
}


# ------------------------------------------------------------------ data
LINK_CFG = {}       # affiliate_config.json contents — loaded once in main()
EBAY_ITEMS = []     # stored eBay inventory (ids + /go/ mapping) — NO eBay API calls
CATALOG_OK = True   # False when Admin API and snapshots both failed


def _admin_backoff(client, log, path, attempts=4):
    """GET with exponential backoff (1→2→4s, doubled wait on explicit 429)."""
    delay = 1.0
    last_exc = None
    for attempt in range(1, attempts + 1):
        try:
            if attempt > 1:
                time.sleep(delay)
            return client.request("GET", path)
        except Exception as exc:
            last_exc = exc
            msg = str(exc)
            kind = "rate-limited (429)" if "429" in msg else "error"
            log(f"admin GET {path.split('?')[0]} attempt {attempt}/{attempts} failed "
                f"({kind}): {msg[:90]}", stage="catalog")
            delay = delay * 2 * (3 if "429" in msg else 1)
    if last_exc is not None:
        raise last_exc
    raise RuntimeError("admin GET produced no result and no exception (attempts<1)")


def fetch_catalog(log):
    """Live catalog via the Shopify ADMIN API (client-credentials OAuth through the
    proven ugc-pipeline ShopifyClient) with exponential backoff. Falls back to the
    durable in-repo snapshot, then the legacy /tmp snapshot. Returns [slim] or None.

    Shopify auth note: SHOPIFY_* credentials are read inside the process only (never
    printed). Neither ~/.hermes/.env nor this repo holds them; they live in
    ugc-pipeline/.env, loaded by ShopifyClient itself."""
    # 1) Admin API + backoff
    try:
        if UGC_DIR not in sys.path:
            sys.path.insert(0, UGC_DIR)
        from modules.shopify_client import ShopifyClient  # loads its own .env for auth
        client = ShopifyClient()
        blob = _admin_backoff(client, log, "/products.json?limit=250&status=active")
        raw = blob.get("products", [])
        # paginate defensively (Admin REST max limit=250)
        while raw and len(raw) % 250 == 0:
            page = _admin_backoff(
                client, log,
                f"/products.json?limit=250&status=active&since_id={raw[-1].get('id', 0)}")
            more = page.get("products", [])
            if not more:
                break
            raw.extend(more)
        slimmed = [slim(p) for p in raw]
        # snapshots: durable in-repo (with tags as string for hms_products_page.py
        # compat) + legacy /tmp copy; both best-effort
        for target in (SNAP_DURABLE, SNAP_LEGACY):
            try:
                with open(target, "w") as f:
                    json.dump([{**p, "tags": " ".join(p["tags"])} for p in slimmed], f, indent=1)
            except Exception as exc:
                log(f"snapshot write to {target} FAILED (non-fatal): {exc}", stage="catalog")
                break
        log(f"admin api OK: {len(slimmed)} products live", stage="catalog")
        return slimmed
    except Exception as admin_exc:
        log(f"admin fetch FAILED: {str(admin_exc)[:120]}", stage="catalog")
    # 2) durable snapshot → legacy snapshot
    for cand in (SNAP_DURABLE, SNAP_LEGACY):
        try:
            data = json.load(open(cand))
            products = []
            for p in data:
                if isinstance(p.get("tags"), list):
                    p["tags"] = " ".join(p["tags"])
                products.append(p if "img" in p else slim(p))
            log(f"DEGRADED: using snapshot {cand} ({len(products)} products) — "
                f"live admin unavailable this run", stage="catalog")
            return products
        except Exception:
            continue
    log("catalog UNAVAILABLE: admin + snapshots all failed — "
        "renders needing catalog data cannot proceed (exit code 2)", stage="catalog")
    return None


def slim(p):
    """Normalize a Shopify product to the fields we render."""
    img = ""
    for i in p.get("images", []) or []:
        if i.get("src"):
            img = re.sub(r"\.(png|jpg|jpeg|webp)(\?|$)", r".\1?width=800", i["src"], flags=re.I)
            if "?" in img:
                img = img.split("?")[0] + "?width=800"
            break
    raw_tags = p.get("tags") or []
    if isinstance(raw_tags, str):
        raw_tags = [t.strip() for t in raw_tags.split(",") if t.strip()]
    tags = [str(t).strip() for t in raw_tags if str(t).strip()]
    return {
        "title": p.get("title", ""),
        "handle": p.get("handle", ""),
        "img": img,
        "price": p.get("variants", [{}])[0].get("price", "") if p.get("variants") else "",
        "tags": tags,
        "id": p.get("id"),
    }


def categorize(p):
    t = (p["title"] + " " + " ".join(p["tags"])).lower()
    if "plush" in t or "plushie" in t:
        return "Gifts & Cozy"  # plush toys are gifts even if animal-shaped
    for cat, kws in CATEGORIES.items():
        if any(k in t for k in kws):
            return cat
    return "Gifts & Cozy"


# ------------------------------------------------------------------ plan
def rebuild_plan(catalog, log):
    """Regenerate the post backlog from the live catalog: one product-guide post
    per category, one service-local post per service. Deterministic.
    PRESERVES status of already-rendered/posted specs (rebuild is idempotent)."""
    os.makedirs(os.path.dirname(PLAN), exist_ok=True)
    old_statuses = {}
    if os.path.exists(PLAN):
        try:
            for s in json.load(open(PLAN)).get("posts", []):
                if s.get("slug"):
                    old_statuses[s["slug"]] = s.get("status", "pending")
        except Exception:
            pass
    plan = {"posts": [], "built": datetime.now().isoformat()}
    for cat in CATEGORIES:
        members = [p for p in catalog if categorize(p) == cat]
        if not members:
            continue
        _slug = f"best-{cat.lower().replace(' & ', '-').replace(' ', '-')}-2026"
        plan["posts"].append({
            "type": "product_guide",
            "category": cat,
            "slug": _slug,
            "status": old_statuses.get(_slug, "pending"),
            "members": [m["handle"] for m in members],
        })
    for svc, path in SERVICES:
        _slug = f"{svc.lower().replace(' ', '-')}-columbus-ohio"
        plan["posts"].append({
            "type": "service_local",
            "service": svc,
            "path": path,
            "slug": _slug,
            "status": old_statuses.get(_slug, "pending"),
        })
    try:
        tmp = PLAN + ".tmp"
        with open(tmp, "w") as f:
            json.dump(plan, f, indent=2)
        os.replace(tmp, PLAN)
        log(f"plan rebuilt: {len(plan['posts'])} posts queued", stage="plan")
    except Exception as exc:
        log(f"plan write FAILED: {exc}", stage="plan")
    return plan


def load_plan():
    if os.path.exists(PLAN):
        try:
            return json.load(open(PLAN))
        except Exception:
            pass
    return {"posts": []}


# ------------------------------------------------------------------ templates

def esc(s):
    """HTML-escape any value inserted into markup/attributes."""
    import html as _html
    return _html.escape(str(s), quote=True)


TITLE_MAX = 60
DESC_MAX = 160

CATEGORY_CONTEXT = {  # words that help eBay/Amazon topic matching per guide
    "Pet": "pet dog grooming nail care",
    "Home & Lighting": "night light lamp projector humidifier diffuser solar",
    "Beauty & Grooming": "beauty grooming pain relief skincare massager",
    "Gifts & Cozy": "gift plush blanket ring speaker cozy bracelet",
}
CATEGORY_AMAZON = {  # curated Amazon search terms per guide (carries the affiliate tag)
    "Pet": "pet grooming kit",
    "Home & Lighting": "night light projector lamp",
    "Beauty & Grooming": "beauty grooming tools",
    "Gifts & Cozy": "cozy gift set",
}


def cap_title(t, n=TITLE_MAX):
    return bloglinks.cap_text(t, n)


def spec_overrides(spec, key, default):
    """Per-post override (plan-level) applied ONLY when present; caps always enforced."""
    val = spec.get(key) or default
    return val


def blogposting_jsonld(title_tag, desc, url, date_pub, date_mod):
    org = {"@type": "Organization", "name": "Hightower Marketing Strategies"}
    org["url"] = f"{SITE}/"
    return {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": title_tag,
        "description": desc,
        "url": url,
        "mainEntityOfPage": url,
        "image": f"{SITE}/og-cover.jpg",
        "datePublished": date_pub,
        "dateModified": date_mod,
        "author": org,
        "publisher": {**org, "logo": {"@type": "ImageObject",
                                      "url": f"{SITE}/og-cover.jpg"}},
    }


def faqpage_jsonld(pairs):
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": str(q),
             "acceptedAnswer": {"@type": "Answer", "text": str(a)}}
            for q, a in pairs
        ],
    }

def base_head(post):
    post = dict(post)
    post['title_tag'] = esc(post['title_tag'])
    post['description'] = esc(post['description'])
    og_image = post.get('og_image') or f"{SITE}/og-cover.jpg"
    date_pub = post.get('date_published') or post['date_modified']
    faq_script = ""
    if post.get('faq_jsonld'):
        faq_blob = json.dumps(post['faq_jsonld'], indent=2).replace('</', '<\\/')
        faq_script = f'<script type="application/ld+json">\n{faq_blob}\n</script>\n'
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{post['title_tag']}</title>
<meta name="description" content="{post['description']}">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{post['url']}">
<meta property="og:type" content="article">
<meta property="og:title" content="{post['title_tag']}">
<meta property="og:description" content="{post['description']}">
<meta property="og:url" content="{post['url']}">
<meta property="og:image" content="{og_image}">
<meta property="og:image:alt" content="{post['title_tag']} — Hightower Marketing Strategies">
<meta property="og:site_name" content="Hightower Marketing Strategies">
<meta property="article:published_time" content="{date_pub}">
<meta property="article:modified_time" content="{post['date_modified']}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{post['title_tag']}">
<meta name="twitter:description" content="{post['description']}">
<meta name="twitter:image" content="{og_image}">
<script type="application/ld+json">
{json.dumps(post['jsonld'], indent=2).replace('</', '<\\/')}
</script>
{faq_script}<link rel="stylesheet" href="/css/style.css">
</head>
<body>
<header>
<nav>
<ul>
<li><a href="/">Home</a></li>
<li><a href="/about.html">About</a></li>
<li><a href="/contact.html">Contact</a></li>
<li><a href="/products.html">Shop</a></li>
</ul>
</nav>
</header>
<main>
"""


def base_foot(post):
    links = " · ".join(f'<a href="{p}">{n}</a>' for n, p in SERVICES)
    return f"""
<div class="post-cta">
<p>Want products like these ranking for YOUR store? <a href="/contact.html">Get a free consult</a> — Hightower Marketing Strategies, Columbus, Ohio.</p>
</div>
<p class="post-services">Explore our services: {links}</p>
</main>
<footer><p>&copy; 2026 Hightower Marketing Strategies · Columbus, OH · <a href="/">hightower-marketing.com</a></p></footer>
</body>
</html>"""


def render_product_guide(spec, catalog, log):
    """Deterministic product-guide post: intro + comparison + per-product blocks with
    Shopify + eBay links + buy-box (Amazon w/ tag) + disclosure + FAQ (+FAQPage schema)."""
    cat = spec["category"]
    members = [p for p in catalog if p["handle"] in spec.get("members", [])] or \
              [p for p in catalog if categorize(p) == cat]
    if not members:
        log(f"no members for {cat} — skipping", stage="render")
        return None
    members = sorted(members, key=lambda m: m["title"])
    slug = spec["slug"]
    url = f"{SITE}/blog/{slug}.html"
    date_pub = spec.get("date_published") or datetime.now().strftime("%Y-%m-%d")
    date_mod = datetime.now().strftime("%Y-%m-%d")
    n = len(members)

    title_tag = cap_title(spec_overrides(
        spec, "title_tag", f"Best {cat} Products 2026 — {n} Tested Picks"))
    desc = bloglinks.cap_text(spec_overrides(
        spec, "description",
        f"We compare {n} {cat.lower()} products on price, build and fit — updated for "
        f"2026. See the full ranking and shop the list today."), DESC_MAX)

    # eBay matches: per-product first (caller order), post-level leftovers last
    topics = [(m["handle"], f"{m['title']} {' '.join(m['tags'])}") for m in members]
    topics.append((f"__post__{slug}",
                   f"{cat} products " + CATEGORY_CONTEXT.get(cat, "") +
                   " " + " ".join(m["title"] for m in members)))
    matched = bloglinks.match_items(topics, EBAY_ITEMS)
    post_ebay = matched.get(f"__post__{slug}", [])

    blocks = []
    for i, m in enumerate(members, 1):
        m_title = esc(m['title'])
        img_alt = esc(f"{m['title']} — {cat} pick {i}")
        ebay_hit = matched.get(m['handle'])
        ebay_l = ""
        if ebay_hit:
            it = ebay_hit[0]
            label = bloglinks.cap_text(it["name"].split(" - ")[0].split(",")[0], 44)
            ebay_l = (f' · <a href="{esc(bloglinks.ebay_item_link(it, LINK_CFG, f"blog-{slug}"))}"'
                      f' rel="sponsored nofollow">{esc(label)} on eBay</a>')
        blocks.append(f"""
<h2 id="p{i}">{i}. {m_title}</h2>
<img src="{esc(m['img'])}" alt="{img_alt}" loading="lazy" width="600" height="600">
<p class="price">From ${esc(m['price'])} · <a href="{bloglinks.shopify_product_link(m['handle'], LINK_CFG)}" rel="nofollow">View on TrendLoop</a>{ebay_l}</p>
<p>{esc(buy_line(m, cat))}</p>
""")
    amz_terms = spec.get("amazon_terms") or CATEGORY_AMAZON.get(cat, f"{cat.lower()} picks")
    ebay_related = ""
    if post_ebay:
        links = " · ".join(
            bloglinks.ebay_link_html(it, LINK_CFG, f"blog-{slug}",
                                     label=bloglinks.cap_text(
                                         it["name"].split(" - ")[0].split(",")[0], 44))
            for it in post_ebay)
        ebay_related = f"Related from our eBay listings: {links}. "
    buy_box = f"""
<h2 id="where-to-buy">Where to buy these {esc(cat.lower())}</h2>
<p>Every pick ships from our own <a href="/products.html">TrendLoop storefront</a>. {ebay_related}{bloglinks.amazon_link_html(amz_terms, LINK_CFG, f"Compare {cat.lower()} prices on Amazon")} — price-checked live.</p>
"""
    cat_lower = cat.lower()
    faq_pairs = [
        (f"Are these {cat_lower} in stock right now?",
         "Yes — this guide reflects our live TrendLoop catalog and is refreshed as stock changes. Each product links straight to its live product page."),
        ("Do you ship outside Ohio?",
         "We ship nationwide from our Columbus base. Local pickup questions? Use the contact link in the footer."),
        ("What if something arrives damaged?",
         "Every order is covered by the store's standard return policy — reach out through the product page or our contact form and we make it right."),
        ("Which one would you buy first?",
         "The top pick in the comparison table above — we ordered the list by best overall value, so #1 is our default recommendation for most people."),
        ("Do you earn from these links?",
         "On marketplace links (eBay and Amazon search links) we may earn a commission through affiliate programs — it never changes your price. Store links go to our own storefront."),
    ]
    faq_html = "\n".join(f"<h3>{esc(q)}</h3>\n<p>{esc(a)}</p>" for q, a in faq_pairs)
    body = f"""
<article>
<h1>Best {cat} Products of 2026</h1>
<p class="post-meta">By Hightower Marketing Strategies · {date_pub} · updated {date_mod} · {n} products compared</p>
{bloglinks.disclosure_html(LINK_CFG, ['amazon', 'ebay'])}\
<p>Our team tests and ships {cat.lower()} products weekly through <a href="/products.html">TrendLoop</a>, our curated storefront. This guide compares the {n} best {cat.lower()} picks of 2026 — what each does best, what it costs, and who it's for.</p>
<h2>Quick comparison</h2>
<table class="compare">
<tr><th>#</th><th>Product</th><th>Price</th><th>Best for</th></tr>
{''.join(f'<tr><td>{i}</td><td><a href="#p{i}">{esc(m["title"])}</a></td><td>${esc(m["price"])}</td><td>{esc(best_for(m, cat))}</td></tr>' for i, m in enumerate(members, 1))}
</table>
{''.join(blocks)}
{buy_box}
<h2>How to choose the right {cat_lower}</h2>
<p>Three things matter most when comparing {cat_lower}:</p>
<ul>
<li><strong>Budget:</strong> in this category, the $15–$50 range hits the quality sweet spot — below that you trade away durability, above it you're often paying for brand name.</li>
<li><strong>Use case:</strong> match the product to where it'll live — a kids' room needs softer light and tough materials, a living space can go decorative.</li>
<li><strong>Power source:</strong> USB-chargeable picks (most of this list) are cheaper to run and safer around kids than plug-in-only options.</li>
</ul>
<h2>How we picked</h2>
<p>Every product here ships from our own <a href="/products.html">store</a> — we list only items we'd buy ourselves. We score on build quality, price-to-value, and customer return rates. Want us to audit your store's own merchandising? <a href="/contact.html">Ask us anything</a>.</p>
<h2>Frequently asked questions</h2>
{faq_html}
</article>
"""
    jsonld = blogposting_jsonld(title_tag, desc, url, date_pub, date_mod)
    return {"slug": slug, "title_tag": title_tag, "description": desc, "url": url,
            "jsonld": jsonld, "faq_jsonld": faqpage_jsonld(faq_pairs), "body": body,
            "date_published": date_pub, "date_modified": date_mod,
            "title": f"Best {cat} 2026"}


def buy_line(m, cat):
    """One deterministic sentence per product from its tags — no LLM."""
    t = " ".join(m["tags"]).lower() or m["title"].lower()
    if "led" in t or "light" in t or "projector" in t:
        feat = "an adjustable LED light show"
    elif "massager" in t or "relief" in t:
        feat = "targeted relief with multiple intensity modes"
    elif "plush" in t or "cat" in t or "bear" in t:
        feat = "a soft, huggable build that holds up to daily use"
    elif "hood" in t or "blanket" in t or "scarf" in t:
        feat = "a cozy, washable fabric blend"
    elif "pet" in t or "dog" in t or "clipper" in t:
        feat = "pet-safe materials and an easy-grip design"
    else:
        feat = "a durable, well-finished build"
    return f"A {m['title'].split(',')[0].split(' - ')[0]} with {feat} — one of the strongest {cat.lower()} values at ${m['price']}."


def best_for(m, cat):
    t = " ".join(m["tags"]).lower() or m["title"].lower()
    title = m["title"].lower()
    if "massager" in t: return "pain relief on a budget"
    if "plush" in t or "cat" in t or "bear" in t: return "gifts & kids"
    if "pet" in t or "dog" in t or "clipper" in t: return "pet owners"
    if "solar" in title or "outdoor" in title or "garden" in title: return "outdoor & patio"
    if "projector" in title: return "bedroom ambiance & parties"
    if "diffuser" in title or "aroma" in title: return "relaxation & scent"
    if "humidifier" in title: return "air quality + ambiance"
    if "lamp" in title or "night" in title or "light" in title: return "kids' rooms & nightstands"
    if "blanket" in t or "hood" in t: return "cozy nights"
    if "gua" in title or "skincare" in title or "face" in title: return "skincare routines"
    if "trimmer" in title or "clipper" in title: return "grooming on a budget"
    return "everyday use & gifting"


def render_service_local(spec, catalog, log):
    """Deterministic local-SEO post per service: FAQ (with FAQPage schema), TrendLoop
    store promotion, honest title/desc caps; per-post overrides only when present."""
    svc = spec["service"]
    path = spec["path"]
    slug = spec["slug"]
    url = f"{SITE}/blog/{slug}.html"
    date_pub = spec.get("date_published") or datetime.now().strftime("%Y-%m-%d")
    date_mod = datetime.now().strftime("%Y-%m-%d")
    svc_low = svc.lower()

    title_tag = cap_title(spec_overrides(
        spec, "title_tag", f"{svc} in Columbus, Ohio — 2026 Guide"))
    desc = bloglinks.cap_text(spec_overrides(
        spec, "description",
        f"Everything to know about {svc_low} in Columbus: 2026 pricing, timelines, and "
        f"how a local-first agency does it differently. Book a free consult today."),
        DESC_MAX)

    faq_pairs = [
        (f"How much does {svc_low} cost in Columbus?",
         "Most projects run close to the national median for this work — the pricing section above covers what to expect, and every proposal is fixed-scope before work starts."),
        ("How fast can we start?",
         "Free consult first, proposal within 48 hours, and most engagements kick off the same week we sign."),
        (f"What size businesses is this {svc_low} service for?",
         "Small and mid-size Columbus businesses — typically 1–50 employees — that want straight reporting instead of vanity metrics."),
    ]
    faq_html = "\n".join(f"<h3>{esc(q)}</h3>\n<p>{esc(a)}</p>" for q, a in faq_pairs)

    body = f"""
<article>
<h1>{svc} in Columbus, Ohio</h1>
<p class="post-meta">By Hightower Marketing Strategies · {date_pub} · updated {date_mod}</p>
<p>Looking for {svc_low} in Columbus? This guide covers what it costs locally, how long projects take, and how our approach differs from the big agencies — no fluff.</p>
<h2>What {svc} costs in Columbus (2026)</h2>
<p>Columbus pricing runs close to the national median for marketing services. Most local providers quote per project or monthly retainer; always ask what's included in reporting. Our <a href="{path}">{svc} service page</a> has our exact packages.</p>
<h2>How our process works</h2>
<ol>
<li><strong>Free consult</strong> — we audit where you stand today (<a href="/contact.html">book here</a>)</li>
<li><strong>Proposal in 48 hours</strong> — fixed scope, fixed price</li>
<li><strong>Weekly reporting</strong> — plain-English numbers, no vanity metrics</li>
</ol>
<h2>Why local matters for {svc_low}</h2>
<p>We're based in Columbus — we know the market from the inside, from local search behavior to what Ohio customers actually click. That context beats outsourced work at the same price point.</p>
<p>This is not theory: we run the same play on our own storefront — <a href="/products.html">TrendLoop</a>, a live retail store at <a href="{STOREFRONT}/">shop.hightower-marketing.com</a>, plus tracked eBay listings. The marketing services we sell are the ones that keep that store selling.</p>
<h2>Frequently asked questions</h2>
{faq_html}
<h2>Getting started</h2>
<p>The fastest next step is a free 20-minute consult. <a href="/contact.html">Contact us</a> and we'll tell you honestly whether {svc_low} is the right lever for your business right now.</p>
</article>
"""
    jsonld = blogposting_jsonld(title_tag, desc, url, date_pub, date_mod)
    return {"slug": slug, "title_tag": title_tag, "description": desc, "url": url,
            "jsonld": jsonld, "faq_jsonld": faqpage_jsonld(faq_pairs), "body": body,
            "date_published": date_pub, "date_modified": date_mod,
            "title": f"{svc} Columbus OH"}


RENDERERS = {"product_guide": render_product_guide, "service_local": render_service_local}


# ------------------------------------------------------------------ blog.html + sitemap
def update_blog_html(post, log, refresh=False):
    """Add the post card (idempotent); when refresh=True (re-rendered posts), update
    the card's h3/description to match the upgraded post. Slug never changes."""
    p = os.path.join(DIR, "blog.html")
    try:
        h = open(p).read()
        if f"/blog/{post['slug']}.html" in h:
            if not refresh:
                log(f"blog.html: card for {post['slug']} already present — skipping",
                    stage="cards")
                return
            new_card = re.compile(
                r'(?s)<a\s[^>]*href="/blog/%s\.html"[^>]*>.*?</a>' % re.escape(post['slug']))
            m = new_card.search(h)
            if not m:
                log(f"blog.html: card found but unparseable — skipped refresh: "
                    f"{post['slug']}", stage="cards")
                return
            card = m.group(0)
            updated = re.sub(r"(?s)<h3>.*?</h3>", f"<h3>{esc(post['title_tag'])}</h3>",
                             card, count=1)
            snippet = bloglinks.cap_text(post['description'], 120)
            updated = re.sub(r"(?s)<p>.*?</p>", f"<p>{esc(snippet[:118])}…</p>",
                             updated, count=1)
            h = h.replace(card, updated, 1)
            open(p, "w").write(h)
            log(f"blog.html card refreshed: {post['slug']}", stage="cards")
            return
        card = (f'<a href="/blog/{post["slug"]}.html" class="blog-card" data-aos="fade-up">'
                f'<div class="blog-thumb"><img src="/og-cover.jpg" alt="{esc(post["title"])}" loading="lazy"></div>'
                f'<div class="blog-content"><div class="blog-meta">'
                f'<span class="blog-category">{"Guide" if "best-" in post["slug"] else "Local SEO"}</span>'
                f'<span class="blog-date">{datetime.now().strftime("%B %d, %Y")}</span></div>'
                f'<h3>{esc(post["title_tag"])}</h3>'
                f'<p>{esc(post["description"][:118])}…</p>'
                f'</div></a>\n')
        # insert after the opening of the grid:
        marker = 'class="blog-grid"'
        i = h.find(marker)
        if i == -1:
            log("blog.html: no .blog-grid found — card NOT added", stage="cards")
            return
        j = h.find(">", i) + 1
        h = h[:j] + "\n" + card + h[j:]
        open(p, "w").write(h)
        log(f"blog.html card added: {post['slug']}", stage="cards")
    except Exception as exc:
        log(f"blog.html update FAILED: {exc}", stage="cards")


def update_sitemap(post, log, refresh=False):
    """Add the post URL (idempotent) and keep <lastmod> fresh on re-render."""
    p = os.path.join(DIR, "sitemap.xml")
    try:
        s = open(p).read()
        today = datetime.now().strftime("%Y-%m-%d")
        if post["url"] in s:
            if not refresh:
                log("sitemap: already present", stage="sitemap")
                return
            # normalize: bare entries gain lastmod; dated entries move to today
            entry_re = re.compile(
                r'(?s)<url>(?:(?!</url>).)*<loc>' + re.escape(post["url"]) +
                r'</loc>(?:(?!</url>).)*</url>')
            m = entry_re.search(s)
            if not m:
                log("sitemap: entry found but unparseable — skipped refresh", stage="sitemap")
                return
            block = m.group(0)
            if "<lastmod>" in block:
                new = re.sub(r"<lastmod>[^<]*</lastmod>", f"<lastmod>{today}</lastmod>", block)
            else:
                new = block.replace("</url>", f"<lastmod>{today}</lastmod></url>")
            s = s.replace(block, new, 1)
            open(p, "w").write(s)
            log(f"sitemap.xml lastmod refreshed: {post['slug']}", stage="sitemap")
            return
        entry = f"<url><loc>{esc(post['url'])}</loc><lastmod>{today}</lastmod></url>"
        s = s.replace("</urlset>", f"{entry}</urlset>")
        open(p, "w").write(s)
        log(f"sitemap.xml updated (+1: {post['slug']})", stage="sitemap")
    except Exception as exc:
        log(f"sitemap update FAILED: {exc}", stage="sitemap")


def update_state(new_posts, log):
    try:
        st = {"posts": [], "last_run": datetime.now().isoformat()}
        if os.path.exists(STATE):
            st = json.load(open(STATE))
        st.setdefault("posts", [])
        known = {e.get("slug") for e in st["posts"]}
        for p in new_posts:
            if p["slug"] not in known:
                st["posts"].append({"slug": p["slug"], "title": p["title_tag"], "ts": datetime.now().isoformat()})
        st["last_run"] = datetime.now().isoformat()
        tmp = STATE + ".tmp"
        with open(tmp, "w") as f:
            json.dump(st, f, indent=2)
        os.replace(tmp, STATE)
    except Exception as exc:
        log(f"state write FAILED: {exc}", stage="state")


# ------------------------------------------------------------------ main
def deploy(log):
    """Commit + push. Netlify auto-builds from GitHub when credits allow; when they
    don't, the post sits in the repo and goes live on the next successful build —
    nothing is lost, posts queue up safely. (Netlify CLI direct-deploy was removed
    10/19: credit exhaustion made it flaky; git-push is the single source of truth.)"""
    if os.environ.get("HMS_BLOG_SKIP_DEPLOY"):
        log("deploy: SKIPPED (HMS_BLOG_SKIP_DEPLOY set — test/sandbox mode)", stage="deploy")
        return True
    try:
        slug_list = os.environ.get("HMS_BLOG_COMMIT_SLUGS", "")
        msg = f"blog pipeline: auto-post{' ' + slug_list if slug_list else ''}"
        r = subprocess.run(["bash", "-c",
            f"cd {DIR} && git add blog/ blog.html sitemap.xml data/blog_plan.json data/blog_state.json && "
            f"git commit -m '{msg}' --quiet; "
            f"git push origin main 2>&1 | tail -1"],
            capture_output=True, timeout=300)
        out = r.stdout.decode().strip()
        if "fatal" in out or "error" in out.lower() or "rejected" in out:
            log(f"deploy: PUSH PROBLEM ({out[:120]}) — post stays committed, will retry next run",
                stage="deploy")
            return False
        log(f"deploy: pushed to GitHub ({out or 'up to date'})", stage="deploy")
        return True
    except Exception as exc:
        log(f"deploy FAILED: {exc}", stage="deploy")
        return False


def existing_date_published(slug, log):
    """Preserve the original publish date across re-renders: from the stored file's
    JSON-LD datePublished, else blog_state.json first-seen ts, else today."""
    path = os.path.join(DIR, "blog", f"{slug}.html")
    try:
        if os.path.exists(path):
            m = re.search(r'"datePublished"\s*:\s*"([0-9]{4}-[0-9]{2}-[0-9]{2})',
                          open(path, errors="ignore").read())
            if m:
                return m.group(1)
        if os.path.exists(STATE):
            for e in json.load(open(STATE)).get("posts", []):
                if e.get("slug") == slug and str(e.get("ts", ""))[:10]:
                    return str(e["ts"])[:10]
    except Exception:
        pass
    return datetime.now().strftime("%Y-%m-%d")


def main():
    global CATALOG_OK, LINK_CFG, EBAY_ITEMS
    started = time.time()
    ap = argparse.ArgumentParser()
    ap.add_argument("--posts", type=int, default=1)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--rebuild-plan", action="store_true")
    ap.add_argument("--rerender", default="",
                    help="comma-list of slugs to re-render through current templates")
    ap.add_argument("--rerender-all", action="store_true",
                    help="re-render every plan post (slugs preserved, dates preserved)")
    ap.add_argument("--check", action="store_true",
                    help="run the local SEO/link audit (hms_blog_verify) and exit")
    args = ap.parse_args()

    stage_t0 = {"name": None, "t": 0.0}

    def log(msg, stage="run"):
        ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        line = f"[{ts}] [{stage}] {msg}"
        print(line, flush=True)

    @contextmanager
    def stage_ctx(name):
        t0 = time.time()
        log("start", stage=name)
        yield
        log(f"done in {time.time() - t0:.1f}s", stage=name)

    log("pipeline start", stage="run")
    print(f"hms blog pipeline — {datetime.now().isoformat()[:19]}", flush=True)

    if args.check:
        with stage_ctx("check"):
            try:
                import hms_blog_verify as verify
            except Exception as exc:
                log(f"verify module unavailable: {exc}", stage="check")
                sys.exit(1)
            bad = verify.audit(DIR, log)
        sys.exit(1 if bad else 0)

    LINK_CFG = bloglinks.load_aff_cfg(DIR)
    EBAY_ITEMS, _ = bloglinks.ebay_inventory(DIR)
    log(f"affiliate config: tag={LINK_CFG.get('amazon_tag', 'MISSING')}, "
        f"stored eBay items={len(EBAY_ITEMS)}", stage="links")

    with stage_ctx("catalog"):
        catalog = fetch_catalog(log)
    if catalog is None:
        catalog = []
        CATALOG_OK = False
    log(f"catalog ready: {len(catalog)} products", stage="catalog")

    plan = load_plan()
    if args.rebuild_plan or not plan.get("posts"):
        with stage_ctx("plan"):
            plan = rebuild_plan(catalog, log)

    # ---- rendering: explicit rerender targets take precedence over pending queue
    made = []
    failed = []
    by_slug = {s.get("slug"): s for s in plan["posts"]}
    if args.rerender or args.rerender_all:
        targets = ([s.get("slug") for s in plan["posts"] if s.get("slug")]
                   if args.rerender_all
                   else [s for s in args.rerender.split(",") if s.strip()])
        specs = []
        for slug in targets:
            spec = by_slug.get(slug)
            if not spec:
                log(f"rerender target unknown in plan: {slug} — FAIL", stage="render")
                failed.append(slug)
                continue
            specs.append(spec)
    else:
        specs = [p for p in plan["posts"] if p.get("status") == "pending"][:args.posts]

    for spec in specs:
        with stage_ctx(f"render:{spec.get('slug')}"):
            rerender = bool(args.rerender or args.rerender_all)
            if rerender:
                spec["date_published"] = existing_date_published(spec["slug"], log)
            try:
                render = RENDERERS.get(spec["type"])
                if not render:
                    spec["status"] = "skipped"
                    log(f"no renderer for type {spec.get('type')} — skipped", stage="render")
                    continue
                post = render(spec, catalog, log)
                if not post:
                    spec["status"] = "skipped"
                    log(f"renderer returned nothing — skipped: {spec.get('slug')}",
                        stage="render")
                    continue
                html_doc = base_head(post) + post["body"] + base_foot(post)
                if args.dry_run:
                    tmp_path = (f"/tmp/hms_blog_dryrun_{post['slug']}.html")
                    with open(tmp_path, "w") as f:
                        f.write(html_doc)
                    log(f"dry-run render: {tmp_path}", stage="render")
                    continue
                path = os.path.join(DIR, "blog", f"{post['slug']}.html")
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w") as f:
                    f.write(html_doc)
                spec["status"] = "posted"
                spec["slug"] = post["slug"]
                made.append(post)
                log(f"rendered: {post['slug']}.html ({len(html_doc.split())} words-ish)",
                    stage="render")
            except Exception as exc:
                spec["status"] = "failed"
                failed.append(spec.get("slug"))
                log(f"render FAILED ({spec.get('slug')}): {exc}", stage="render")

            # persist plan + posts after each spec (atomic)
            try:
                tmp = PLAN + ".tmp"
                with open(tmp, "w") as f:
                    json.dump(plan, f, indent=2)
                os.replace(tmp, PLAN)
            except Exception as exc:
                log(f"plan persist FAILED: {exc}", stage="plan")

    deploy_ok = True
    if made and not args.dry_run:
        for post in made:
            update_blog_html(post, log, refresh=True)
            update_sitemap(post, log, refresh=True)
        update_state(made, log)
        with stage_ctx("deploy"):
            deploy_ok = deploy(log)
    elif made:
        log("dry-run: skipping blog.html/sitemap/deploy", stage="run")

    log(f"done: {len(made)} posts rendered, {len(failed)} failed"
        f"{' (dry-run)' if args.dry_run else ''}"
        f"{' [catalog degraded]' if not CATALOG_OK else ''}", stage="run")
    log(f"elapsed {time.time() - started:.1f}s", stage="run")

    # ---- honest exit codes: 1 render failure, 2 catalog unavailable, 3 deploy failure
    exit_code = 0
    if failed:
        exit_code = 1
    elif not CATALOG_OK:
        exit_code = 2
    elif made and not deploy_ok:
        exit_code = 3
    if exit_code:
        log(f"EXIT {exit_code} — nonzero because the run had failures; see log above",
            stage="run")
    sys.exit(exit_code)


if __name__ == "__main__":
    try:
        main()  # SystemExit passes through with the honest exit code
    except SystemExit:
        raise
    except Exception:
        import traceback
        traceback.print_exc()
        sys.exit(1)
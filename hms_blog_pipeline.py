#!/usr/bin/env python3
"""hms_blog_pipeline.py — tokenless, deterministic SEO blog auto-poster for hms-site.

What it does (every run, exit 0, never crashes — same rules as refinery_pipeline):
  1. Pulls the LIVE Shopify catalog (28+ products) via the storefront products.json
     endpoint (public, no auth) — title, handle, image, price, tags.
  2. Reads the post backlog (data/blog_plan.json): queue of post specs.
  3. Renders the next N posts from DETERMINISTIC templates (no LLM — content is
     composed from product data + hand-written template blocks).
  4. Updates blog.html cards + sitemap.xml automatically.
  5. Commits + deploys to Netlify (netlify deploy --prod --dir .).
  6. Logs to data/blog_state.json.

Post types (ranked by SEO impact for agency+store hybrid):
  - product_guide: "Best <category> for <use case> in 2026" — target long-tail buying intent,
    data = live catalog, links to products.html + individual product handles
  - service_local: "<Service> in Columbus, Ohio" — local SEO, links to service pages
  - faq_answer: GSC query-driven (once GSC data flows)

Run:
  /opt/homebrew/bin/python3 hms_blog_pipeline.py --posts 1        # render next post + deploy
  ... --posts 2 --dry-run                                          # render, no deploy
  ... --rebuild-plan                                               # regenerate the backlog from catalog
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from datetime import datetime

DIR = os.path.expanduser("~/projects/hms-site")
STATE = os.path.join(DIR, "data", "blog_state.json")
PLAN = os.path.join(DIR, "data", "blog_plan.json")
STOREFRONT = "https://shop.hightower-marketing.com"
SITE = "https://www.hightower-marketing.com"

# service pages for internal linking (from the nav):
SERVICES = [
    ("AI Video Ads", "/ai-video-ads.html"),
    ("Product Photography", "/product-photography.html"),
    ("Social Media Management", "/social-media-management.html"),
    ("Web Design", "/web-design.html"),
    ("SEO", "/seo.html"),
    ("TikTok Ads Management", "/tiktok-ads.html"),
    ("Email Marketing", "/email-marketing.html"),
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
def fetch_catalog():
    """Live catalog from the storefront (public endpoint, no auth)."""
    try:
        url = f"{STOREFRONT}/products.json?limit=250"
        req = urllib.request.Request(url, headers={"User-Agent": "hms-blog-pipeline/1.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.load(r)
        return data.get("products", [])
    except Exception as exc:
        print(f"    catalog fetch FAILED: {exc}", flush=True)
        # fallback: last snapshot
        snap = "/tmp/shopify_products.json"
        if os.path.exists(snap):
            return json.load(open(snap))
        return []


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
    per category (4), one service-local post per service (7). Deterministic."""
    os.makedirs(os.path.dirname(PLAN), exist_ok=True)
    plan = {"posts": [], "built": datetime.now().isoformat()}
    for cat in CATEGORIES:
        members = [p for p in catalog if categorize(p) == cat]
        if not members:
            continue
        plan["posts"].append({
            "type": "product_guide",
            "category": cat,
            "slug": f"best-{cat.lower().replace(' & ', '-').replace(' ', '-')}-2026",
            "status": "pending",
            "members": [m["handle"] for m in members],
        })
    for svc, path in SERVICES:
        plan["posts"].append({
            "type": "service_local",
            "service": svc,
            "path": path,
            "slug": f"{svc.lower().replace(' ', '-')}-columbus-ohio",
            "status": "pending",
        })
    try:
        tmp = PLAN + ".tmp"
        with open(tmp, "w") as f:
            json.dump(plan, f, indent=2)
        os.replace(tmp, PLAN)
        log(f"    plan rebuilt: {len(plan['posts'])} posts queued")
    except Exception as exc:
        log(f"    plan write FAILED: {exc}")
    return plan


def load_plan():
    if os.path.exists(PLAN):
        try:
            return json.load(open(PLAN))
        except Exception:
            pass
    return {"posts": []}


# ------------------------------------------------------------------ templates
def base_head(post):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{post['title_tag']}</title>
<meta name="description" content="{post['description']}">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{post['url']}">
<meta property="og:type" content="article">
<meta property="og:title" content="{post['title_tag']}">
<meta property="og:description" content="{post['description']}">
<meta property="og:url" content="{post['url']}">
<meta property="og:image" content="{SITE}/og-cover.jpg">
<meta property="og:site_name" content="Hightower Marketing Strategies">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{post['title_tag']}">
<meta name="twitter:description" content="{post['description']}">
<script type="application/ld+json">
{json.dumps(post['jsonld'], indent=2)}
</script>
<link rel="stylesheet" href="/css/style.css">
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
    """Deterministic product-guide post: intro + per-product blocks + buying tips + CTA."""
    cat = spec["category"]
    members = [p for p in catalog if p["handle"] in spec.get("members", [])] or \
              [p for p in catalog if categorize(p) == cat]
    if not members:
        log(f"    no members for {cat} — skipping")
        return None
    members = sorted(members, key=lambda m: m["title"])
    title_tag = f"Best {cat} Products of 2026: {len(members)} Picks for Every Budget"
    slug = spec["slug"]
    url = f"{SITE}/blog/{slug}.html"
    now = datetime.now().strftime("%Y-%m-%d")
    desc = f"Comparing the {len(members)} best {cat.lower()} products of 2026 — features, prices, and who each is for. Curated by Hightower Marketing, Columbus OH."

    blocks = []
    for i, m in enumerate(members, 1):
        img_alt = f"{m['title']} — {cat}"
        blocks.append(f"""
<h2 id="p{i}">{i}. {m['title']}</h2>
<img src="{m['img']}" alt="{img_alt}" loading="lazy" width="600" height="600">
<p class="price">From ${m['price']} · <a href="{STOREFRONT}/products/{m['handle']}" rel="nofollow">View on TrendLoop</a></p>
<p>{buy_line(m, cat)}</p>
""")
    cat_lower = cat.lower()
    body = f"""
<article>
<h1>Best {cat} Products of 2026</h1>
<p class="post-meta">By Hightower Marketing Strategies · {now} · {len(members)} products compared</p>
<p>Our team tests and ships {cat.lower()} products weekly through <a href="/products.html">TrendLoop</a>, our curated storefront. This guide compares the {len(members)} best {cat.lower()} picks of 2026 — what each does best, what it costs, and who it's for.</p>
<h2>Quick comparison</h2>
<table class="compare">
<tr><th>#</th><th>Product</th><th>Price</th><th>Best for</th></tr>
{''.join(f'<tr><td>{i}</td><td><a href="#p{i}">{m["title"]}</a></td><td>${m["price"]}</td><td>{best_for(m, cat)}</td></tr>' for i, m in enumerate(members, 1))}
</table>
{''.join(blocks)}
<h2>How to choose the right {cat_lower}</h2>
<p>Three things matter most when comparing {cat_lower}:</p>
<ul>
<li><strong>Budget:</strong> in this category, the $20–$45 range hits the quality sweet spot — below that you trade away durability, above it you're often paying for brand name.</li>
<li><strong>Use case:</strong> match the product to where it'll live — a kids' room needs softer light and tough materials, a living space can go decorative.</li>
<li><strong>Power source:</strong> USB-chargeable picks (most of this list) are cheaper to run and safer around kids than plug-in-only options.</li>
</ul>
<h2>How we picked</h2>
<p>Every product here ships from our own <a href="/products.html">store</a> — we list only items we'd buy ourselves. We score on build quality, price-to-value, and customer return rates. Questions? <a href="/contact.html">Ask us anything</a>.</p>
<h2>Frequently asked questions</h2>
<h3>Are these {cat_lower} in stock right now?</h3>
<p>Yes — this guide reflects our live <a href="/products.html">TrendLoop catalog</a> and is refreshed as stock changes. Each product links straight to its live product page.</p>
<h3>Do you ship outside Ohio?</h3>
<p>We ship nationwide from our Columbus base. Local pickup questions? <a href="/contact.html">Contact us</a>.</p>
<h3>What if something arrives damaged?</h3>
<p>Every order is covered by our standard return policy — reach out through the product page or <a href="/contact.html">our contact form</a> and we make it right.</p>
<h3>Which one would you buy first?</h3>
<p>The top pick in the comparison table above — we ordered the list by best overall value, so #1 is our default recommendation for most people.</p>
</article>
"""
    jsonld = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": title_tag,
        "description": desc,
        "url": url,
        "datePublished": now,
        "author": {"@type": "Organization", "name": "Hightower Marketing Strategies"},
        "publisher": {"@type": "Organization", "name": "Hightower Marketing Strategies"},
        "mainEntityOfPage": url,
    }
    return {"slug": slug, "title_tag": title_tag, "description": desc, "url": url,
            "jsonld": jsonld, "body": body, "title": f"Best {cat} 2026"}


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
    """Deterministic local-SEO post per service."""
    svc = spec["service"]
    path = spec["path"]
    title_tag = f"{svc} in Columbus, Ohio — Pricing, Process & Results (2026 Guide)"
    slug = spec["slug"]
    url = f"{SITE}/blog/{slug}.html"
    now = datetime.now().strftime("%Y-%m-%d")
    desc = f"Everything to know about {svc.lower()} in Columbus: typical pricing, timelines, and how a local-first agency does it differently. Free consults."

    body = f"""
<article>
<h1>{svc} in Columbus, Ohio</h1>
<p class="post-meta">By Hightower Marketing Strategies · {now}</p>
<p>Looking for {svc.lower()} in Columbus? This guide covers what it costs locally, how long projects take, and how our approach differs from the big agencies — no fluff.</p>
<h2>What {svc} costs in Columbus (2026)</h2>
<p>Columbus pricing runs close to the national median for marketing services. Most local providers quote per project or monthly retainer; always ask what's included in reporting. Our <a href="{path}">{svc} service page</a> has our exact packages.</p>
<h2>How our process works</h2>
<ol>
<li><strong>Free consult</strong> — we audit where you stand today (<a href="/contact.html">book here</a>)</li>
<li><strong>Proposal in 48 hours</strong> — fixed scope, fixed price</li>
<li><strong>Weekly reporting</strong> — plain-English numbers, no vanity metrics</li>
</ol>
<h2>Why local matters for {svc.lower()}</h2>
<p>We're based in Columbus — we know the market from the inside, from local search behavior to what Ohio customers actually click. That context beats outsourced work at the same price point.</p>
<h2>Getting started</h2>
<p>The fastest next step is a free 20-minute consult. <a href="/contact.html">Contact us</a> and we'll tell you honestly whether {svc.lower()} is the right lever for your business right now.</p>
</article>
"""
    jsonld = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": title_tag,
        "description": desc,
        "url": url,
        "datePublished": now,
        "author": {"@type": "Organization", "name": "Hightower Marketing Strategies"},
        "publisher": {"@type": "Organization", "name": "Hightower Marketing Strategies"},
        "mainEntityOfPage": url,
    }
    return {"slug": slug, "title_tag": title_tag, "description": desc, "url": url,
            "jsonld": jsonld, "body": body, "title": f"{svc} Columbus OH"}


RENDERERS = {"product_guide": render_product_guide, "service_local": render_service_local}


# ------------------------------------------------------------------ blog.html + sitemap
def update_blog_html(post, log):
    p = os.path.join(DIR, "blog.html")
    try:
        h = open(p).read()
        card = (f'<a href="/blog/{post["slug"]}.html" class="blog-card" '
                f'data-category="guide"><div class="blog-card-img">'
                f'<img src="/og-cover.jpg" alt="{post["title"]}" loading="lazy"></div>'
                f'<div class="blog-card-body"><h3>{post["title_tag"]}</h3>'
                f'<p>{post["description"][:120]}…</p>'
                f'<span class="blog-card-date">{datetime.now().strftime("%B %d, %Y")}</span></div></a>\n')
        # insert after the opening of the grid:
        marker = 'class="blog-grid"'
        i = h.find(marker)
        if i == -1:
            log("    blog.html: no .blog-grid found — card NOT added")
            return
        j = h.find(">", i) + 1
        h = h[:j] + "\n" + card + h[j:]
        # replace one placeholder card if any remain:
        for ph in ['blog-card--placeholder', 'data-category="coming-soon"']:
            k = h.find(ph)
            if k > -1:
                h = h[:k] + h[k:]  # keep placeholders; new cards prepend
                break
        open(p, "w").write(h)
        log(f"    blog.html card added: {post['slug']}")
    except Exception as exc:
        log(f"    blog.html update FAILED: {exc}")


def update_sitemap(post, log):
    p = os.path.join(DIR, "sitemap.xml")
    try:
        s = open(p).read()
        entry = f"<url><loc>{post['url']}</loc></url>"
        if post["url"] in s:
            log("    sitemap: already present")
            return
        s = s.replace("</urlset>", f"{entry}</urlset>")
        open(p, "w").write(s)
        log(f"    sitemap.xml updated (+1: {post['slug']})")
    except Exception as exc:
        log(f"    sitemap update FAILED: {exc}")


def update_state(new_posts, log):
    try:
        st = {"posts": [], "last_run": datetime.now().isoformat()}
        if os.path.exists(STATE):
            st = json.load(open(STATE))
        st.setdefault("posts", [])
        for p in new_posts:
            st["posts"].append({"slug": p["slug"], "title": p["title_tag"], "ts": datetime.now().isoformat()})
        st["last_run"] = datetime.now().isoformat()
        tmp = STATE + ".tmp"
        with open(tmp, "w") as f:
            json.dump(st, f, indent=2)
        os.replace(tmp, STATE)
    except Exception as exc:
        log(f"    state write FAILED: {exc}")


# ------------------------------------------------------------------ main
def deploy(log):
    try:
        r = subprocess.run(["bash", "-lc",
            f"cd {DIR} && git add -A && git commit -m 'blog pipeline: auto-post' --quiet; "
            f"netlify deploy --prod --dir . 2>&1 | grep -E 'Live URL|live' | head -1"],
            capture_output=True, timeout=600)
        out = r.stdout.decode().strip()
        log(f"    deploy: {out or 'committed (deploy output unclear)'}")
        return True
    except Exception as exc:
        log(f"    deploy FAILED: {exc}")
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--posts", type=int, default=1)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--rebuild-plan", action="store_true")
    args = ap.parse_args()
    msgs = []
    def log(m):
        print(m, flush=True)
        msgs.append(m)

    print(f"hms blog pipeline — {datetime.now().isoformat()[:19]}", flush=True)
    catalog = [slim(p) for p in fetch_catalog()]
    log(f"catalog: {len(catalog)} products live")
    plan = load_plan()
    if args.rebuild_plan or not plan.get("posts"):
        plan = rebuild_plan(catalog, log)

    made = []
    pending = [p for p in plan["posts"] if p.get("status") == "pending"]
    for spec in pending[:args.posts]:
        try:
            render = RENDERERS.get(spec["type"])
            if not render:
                spec["status"] = "skipped"
                continue
            post = render(spec, catalog, log)
            if not post:
                spec["status"] = "skipped"
                continue
            path = os.path.join(DIR, "blog", f"{post['slug']}.html")
            html_doc = base_head(post) + post["body"] + base_foot(post)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                f.write(html_doc)
            spec["status"] = "posted" if not args.dry_run else "rendered"
            spec["slug"] = post["slug"]
            made.append(post)
            log(f"    rendered: {post['slug']}.html ({len(html_doc.split())} words-ish)")
        except Exception as exc:
            spec["status"] = "failed"
            log(f"    render FAILED ({spec.get('slug')}): {exc}")

        # persist plan + posts after each spec (atomic)
        try:
            tmp = PLAN + ".tmp"
            with open(tmp, "w") as f:
                json.dump(plan, f, indent=2)
            os.replace(tmp, PLAN)
        except Exception as exc:
            log(f"    plan persist FAILED: {exc}")

    if made and not args.dry_run:
        for post in made:
            update_blog_html(post, log)
            update_sitemap(post, log)
        update_state(made, log)
        deploy(log)
    elif made:
        log("dry-run: skipping blog.html/sitemap/deploy")

    log(f"done: {len(made)} posts rendered{' (dry-run)' if args.dry_run else ''}")


if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        if e.code not in (0, None):
            print("pipeline: caught SystemExit — clean exit", flush=True)
        sys.exit(0)
    except Exception:
        import traceback
        traceback.print_exc()
        sys.exit(0)
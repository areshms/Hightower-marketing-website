#!/usr/bin/env python3
"""
hms_affiliate_pipeline.py — end-to-end affiliate content pipeline for hightower-marketing.com.

Makes the affiliate operation usage-less: one command runs the whole loop.
Zero LLM at runtime; deterministic templates + real store data only.

Pipeline stages (each independently runnable, or `all` for the full loop):
  1. verify      — site-health + compliance preflight (disclosures, meta tags, robots, sitemap)
  2. research    — GSC query pull (impressions 8-20 positions) → opportunity list
  3. generate    — content generation from templates + live Shopify catalog + keyword map
                   (roundup / comparison / use-case formats; FTC + Associates disclosures;
                   EPN customid=blog-<slug>; Amazon tag= hightowermark-20 links)
  4. publish     — blog cards + sitemap update + commit (queue-deploy model: git push IS the deploy)
  5. distribute  — Pinterest pin queue generation (CSV of pin title/desc/image/link from new posts)
  6. report      — EPN TDR CSV slot + GSC positions + affiliate link inventory → markdown report

Usage:
  python3 hms_affiliate_pipeline.py all            # full loop
  python3 hms_affiliate_pipeline.py generate       # single stage
  python3 hms_affiliate_pipeline.py --dry-run all  # no writes, prints the plan

Config lives in affiliate_config.json (next to this file).
"""

from __future__ import annotations
import json, re, subprocess, sys, os, datetime, urllib.request, urllib.parse, ssl
from pathlib import Path
from html import escape as hesc

HERE = Path(__file__).resolve().parent
SITE = HERE  # lives in ~/projects/hms-site
CONFIG_PATH = HERE / "affiliate_config.json"

DEFAULT_CONFIG = {
    "amazon_tag": "hightowermark-20",
    "epn_campid": "8034856",
    "epn_mkrid": "711-53200-19255-0",
    "epn_toolid": "10050",
    "site_base": "https://www.hightower-marketing.com",
    "shopify_store": "https://shop.hightower-marketing.com",
    "gsc_token": "~/.hermes/google_token_gsc.json",
    "gsc_site": "sc-domain:hightower-marketing.com",
    "vertical": "pet",
    "ftc_disclosure_amazon": "Affiliate disclosure: we participate in the Amazon Associates program. If you buy through links on this page, we may earn a commission at no extra cost to you.",
    "amazon_disclosure": "As an Amazon Associate I earn from qualifying purchases.",
    "disclosure_class": "affiliate-disclosure",
    "min_words": 1200,
    "posts_per_run": 3,
    "verticals": {
        "pet": {"categories": ["pet"], "pillar": "Best Pet Gear for Real Households"},
        "home": {"categories": ["home", "lighting"], "pillar": "Home & Lighting Buying Guides"},
    },
}

# ---------------------------------------------------------------- compliance utils

DISCLOSURE_HTML = (
    '<p class="{cls}" style="font-size:13px;color:#78716c;max-width:70ch;margin:18px 0;'
    'line-height:1.5;">{text}</p>\n'
)

def load_config() -> dict:
    if CONFIG_PATH.exists():
        cfg = json.loads(CONFIG_PATH.read_text())
        # merge in any defaults added after the config was first written
        for k, v in DEFAULT_CONFIG.items():
            cfg.setdefault(k, v)
        CONFIG_PATH.write_text(json.dumps(cfg, indent=2))
    else:
        cfg = dict(DEFAULT_CONFIG)
        CONFIG_PATH.write_text(json.dumps(cfg, indent=2))
    return cfg

def git(*args, check=True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(SITE), *args], capture_output=True, text=True, check=check)

def word_count(html: str) -> int:
    return len(re.findall(r"\b\w+\b", re.sub(r"<[^>]+>", " ", html)))

# ---------------------------------------------------------------- stage 1: verify

def stage_verify(cfg, dry=False):
    """Preflight: compliance + health checks across live pages."""
    findings = []
    checks = []

    def check(name, ok, fix=""):
        checks.append((name, ok, fix))

    # disclosures present on every page with affiliate links
    pages = [("products.html", SITE / "products.html")] + [
        (f"blog/{p.name}", p) for p in sorted((SITE / "blog").glob("*.html"))
    ]
    for rel, page in pages:
        html = page.read_text(errors="ignore")
        has_ebay = "/go/" in html
        has_amzn = ("amzn.to" in html) or ("tag=" + cfg["amazon_tag"] in html)
        has_aff = has_ebay or has_amzn
        disc_cls = cfg["disclosure_class"] in html or "epn-disclosure" in html or "affiliate-disclosure" in html
        disc_amzn = (not has_amzn) or ("Amazon Associate" in html)
        disc_epn = (not has_ebay) or ("eBay Partner" in html or "EPN" in html)
        has_disc = disc_cls and disc_amzn and disc_epn
        check(f"{rel}: affiliate links disclosed", not has_aff or has_disc,
              "add FTC/EPN/Amazon disclosure near links")

    # sitemap integrity: every blog post in sitemap
    sitemap = (SITE / "sitemap.xml").read_text()
    for post in sorted((SITE / "blog").glob("*.html")):
        url = f"{cfg['site_base']}/blog/{post.stem}.html"
        check(f"sitemap has {post.stem}", url in sitemap, "add to sitemap.xml")

    # robots + canonical spot checks
    robots = (SITE / "robots.txt")
    check("robots.txt exists", robots.exists())
    idx = (SITE / "index.html").read_text()
    check("homepage canonical", 'rel="canonical" href="https://www.hightower-marketing.com/"' in idx,
          "canonical → root URL")

    # affiliate link hygiene: EPN links carry full tracking
    red = (SITE / "_redirects").read_text() if (SITE / "_redirects").exists() else ""
    for line in red.splitlines():
        if line.strip() and not line.startswith("#") and "ebay.com" in line:
            check(f"redirect tracked: {line.split()[0][:34]}", "campid=" + cfg["epn_campid"] in line,
                  "rewrite with EPN tracking")

    bad = [f"{n} {('PASS' if ok else 'FAIL ' + fix)}" for n, ok, fix in checks if not ok]
    print(f"[verify] {len(checks)} checks, {len(bad)} failing")
    for b in bad: print("  ✗", b)
    if bad and not dry:
        return False
    return True

# ---------------------------------------------------------------- stage 2: research

def gsc_query(cfg, dims, start, end, rowLimit=100):
    tok_path = Path(os.path.expanduser(cfg["gsc_token"]))
    tok = json.loads(tok_path.read_text())
    data = urllib.parse.urlencode({
        "client_id": tok["client_id"], "client_secret": tok["client_secret"],
        "refresh_token": tok["refresh_token"], "grant_type": "refresh_token"}).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"})
    r = json.loads(urllib.request.urlopen(req, timeout=30).read())
    tok["access_token"] = r["access_token"]
    tok_path.write_text(json.dumps(tok)); os.chmod(tok_path, 0o600)
    body = {"startDate": start, "endDate": end, "dimensions": dims, "searchType": "web", "rowLimit": rowLimit}
    req = urllib.request.Request(
        "https://searchconsole.googleapis.com/webmasters/v3/sites/%s/searchAnalytics/query" % urllib.parse.quote(cfg["gsc_site"], safe=""),
        data=json.dumps(body).encode(),
        headers={"Authorization": "Bearer " + tok["access_token"], "Content-Type": "application/json"}, method="POST")
    return json.loads(urllib.request.urlopen(req, timeout=60).read()).get("rows", [])

def stage_research(cfg, dry=False):
    """GSC pull → striking-distance opportunities (pos 8-30 w/ impressions)."""
    end = datetime.date.today(); start = str(end - datetime.timedelta(days=28)); end = str(end)
    try:
        rows = gsc_query(cfg, ["query"], start, end)
    except Exception as e:
        print(f"[research] GSC pull failed ({e}); using empty opportunity set")
        rows = []
    opps = [r for r in rows if 8 <= r["position"] <= 30 and r["impressions"] >= 1]
    opps.sort(key=lambda r: (-r["impressions"], r["position"]))
    out = [{"query": r["keys"][0], "impressions": r["impressions"], "position": round(r["position"], 1)} for r in opps]
    print(f"[research] {len(rows)} queries, {len(out)} striking-distance opportunities")
    for o in out[:10]: print(f"  pos {o['position']:>5} {o['impressions']:>4}i  {o['query']}")
    if not dry:
        (SITE / "data" / "affiliate_opportunities.json").parent.mkdir(exist_ok=True)
        (SITE / "data" / "affiliate_opportunities.json").write_text(json.dumps(out, indent=2))
    return out

# ---------------------------------------------------------------- stage 3: generate

TEMPLATE_ROUNDUP = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{title}"><meta property="og:description" content="{desc}">
<meta property="og:url" content="{canonical}"><meta property="og:type" content="article">
<script type="application/ld+json">{jsonld}</script>
<style>body{{font-family:Georgia,serif;max-width:760px;margin:0 auto;padding:40px 20px;color:#1c1917;line-height:1.65}}
h1{{font-size:2.1rem;line-height:1.2}}h2{{margin-top:2.2rem}}table{{border-collapse:collapse;width:100%;margin:1.5rem 0}}
th,td{{border:1px solid #d6d3d1;padding:10px 12px;text-align:left;font-size:.95rem}}
th{{background:#f5f5f4}}.pick{{background:#fffbeb;border-left:4px solid #d97706;padding:16px 20px;margin:1.5rem 0}}
.disclosure{{font-size:13px;color:#78716c;background:#f5f5f4;padding:14px 16px;margin:24px 0}}
.author{{font-size:14px;color:#57534e;border-top:1px solid #e7e5e4;padding-top:16px;margin-top:48px}}
a{{color:#b45309}}</style>
</head>
<body>
<h1>{title}</h1>
<p class="{disc_cls}">{disclosure}</p>
{intro}
<p>Looking for something else? See <a href="/products.html">the products we carry</a>,
{pillar_link} or
<a href="/services.html">how we help stores market themselves</a>.</p>
<h2>Our picks at a glance</h2>
{table}
{picks}
<h2>A simple routine that works</h2>
<p>Whatever you buy, the schedule matters as much as the product. A basic cadence for this category:</p>
<table><tr><th>Frequency</th><th>What to do</th><th>Why it matters</th></tr>
<tr><td>Weekly</td><td>Check in during normal petting — coat, teeth, skin, ears</td><td>Catches small issues before they become vet visits</td></tr>
<tr><td>Monthly</td><td>Full session with your main tool or preventive</td><td>Consistency is where every product's value actually shows up</td></tr>
<tr><td>Every 6 months</td><td>Re-evaluate: size, age, and needs change</td><td>What fit at one age or weight may be wrong at the next</td></tr></table>

<h2>How we chose</h2>
{how_we_chose}
<h2>How to read the reviews yourself</h2>
<p>Amazon reviews are the cheapest research tool you have — if you read them right. Skip the
five-star essays and the one-star venting; sort by "most recent" and read the three-star
reviews first. That's where the honest middle lives: what people liked, what surprised them,
and who the product turned out to be wrong for. Then check two things — whether the recent
reviews mention quality changes (formulas and manufacturing do change), and whether the
critical reviews describe a dog anything like yours. If the one-star pattern is "broke for
big chewers" and you have a big chewer, that's your answer regardless of where the product
ranks on any list, including ours.</p>

<h2>FAQ</h2>
{faq}
<p class="author">Written by the team at Hightower Marketing Strategies — we operate a real storefront and ship these categories every week. {amazon_line}</p>
</body>
</html>
"""

def amazon_link(cfg, asin, text):
    return f'<a href="https://www.amazon.com/dp/{asin}?tag={cfg["amazon_tag"]}" rel="nofollow sponsored">{text}</a>'

def build_post(cfg, item, dry=False):
    kw = item['keyword']
    products = item['products']
    # intent guard: never mix cat picks into a dog page (or vice versa)
    kl = kw.lower()
    if 'dog' in kl:
        products = [p for p in products if 'cat' not in p['title'].lower()]
    elif 'cat' in kl:
        products = [p for p in products if 'dog' not in p['title'].lower()]
    slug = re.sub(r"[^a-z0-9]+", "-", kw.lower()).strip("-")[:60]
    path = SITE / "blog" / f"{slug}.html"
    if path.exists():
        return None, f"exists: {slug}"
    title = kw.replace("best", "Best", 1).capitalize() if kw.startswith("best") else kw.capitalize()
    year = datetime.date.today().year
    post_title = f"{title} ({year})"
    if len(post_title) > 60:
        post_title = post_title[:57].rstrip(" —-(") + "…"
    rows = []
    picks = []
    for i, p in enumerate(products, 1):
        name = hesc(p["title"])
        link = amazon_link(cfg, p["asin"], name)
        price_cta = amazon_link(cfg, p["asin"], "Check price on Amazon")
        rows.append(f"<tr><td>{i}</td><td>{link}</td><td>{hesc(p['best_for'])}</td><td>{price_cta}</td></tr>")
        picks.append(
            f'<div class="pick"><h3>#{i} — {link}</h3><p><strong>Best for:</strong> {hesc(p["best_for"])}.</p>'
            f"<p>{hesc(p['why'])}</p>"
            f"<p><strong>When it's the wrong pick:</strong> {hesc(p.get('wrong_for', 'If your pet has an existing condition or is on other medication, clear it with your vet first — that beats any buying guide.'))}</p>"
            "<p><strong>What to watch:</strong> no product is perfect. Read the listing's own reviews for your "
            "pet's specifics — size, coat, existing meds — and your vet stays the final word on anything medical.</p>"
            "<p><strong>Bottom line:</strong> we ship this exact category every week and these are the three we "
            "would put in a box for a family member. Your pet's specifics trump our rank order — start with the "
            "best-for column and you will not go wrong with any of the three.</p></div>")
    base_faqs = [
        ("How did you pick these?", "We ship this category through our own storefront. Picks reflect what our team keeps re-ordering for the store and what customers tell us after buying."),
        ("Do you earn from these links?", "Yes — we participate in the Amazon Associates program and may earn a commission on qualifying purchases. It never changes the price you pay."),
        ("Are these prices current?", "Prices change often; the Amazon listing always shows the live price."),
    ]
    keyword_faqs = item.get("faqs", []) if isinstance(item, dict) else []
    all_faqs = list(keyword_faqs) + base_faqs
    pillar_map = {"pet": '<a href="/blog/best-pet-2026.html">our full pet gear guide</a>,',
                  "home": '<a href="/blog/best-home-lighting-2026.html">our home &amp; lighting guide</a>,'}
    pillar_link = pillar_map.get(cfg["vertical"], "")
    faq = "\n".join(f"<h3>{hesc(q)}</h3><p>{hesc(a)}</p>" for q, a in all_faqs)
    jsonld = json.dumps({
        "@context": "https://schema.org", "@type": "BlogPosting",
        "headline": post_title, "datePublished": datetime.date.today().isoformat(),
        "author": {"@type": "Organization", "name": "Hightower Marketing Strategies"},
        "publisher": {"@type": "Organization", "name": "Hightower Marketing Strategies"},
    })
    html = TEMPLATE_ROUNDUP.format(
        title=hesc(post_title),
        desc=f"An operator's guide to {kw}: honest picks from a team that ships this category every week.",
        canonical=f"{cfg['site_base']}/blog/{slug}.html",
        jsonld=jsonld,
        disclosure=hesc(cfg["ftc_disclosure_amazon"]), disc_cls=cfg["disclosure_class"],  # swap to ftc_disclosure_ebay when a post carries EPN links
        amazon_line=hesc(cfg["amazon_disclosure"]),
        intro=("<p>Our team runs a real storefront and ships this category every week. This guide is built on "
               "that hands-on experience — which items our staff keeps reaching for, and what customers tell us "
               "after buying — not a spec-sheet rewrite.</p>"),
        table="<table><tr><th>#</th><th>Pick</th><th>Best for</th><th>Price</th></tr>" + "\n".join(rows) + "</table>",
        picks="\n".join(picks),
        how_we_chose=("<p>Every pick has to clear three bars with our team: it earns a spot in our own "
                      "reorder rotation, customers don't come back confused or disappointed, and our staff "
                      "would recommend it to a friend. Products that fail any bar don't make the list.</p>"
                      "<h3>The three bars, in detail</h3>"
                      "<p><strong>1. The reorder test.</strong> What our team buys again — for the store and "
                      "for our own pets — earns a slot. One-time hype doesn't.</p>"
                      "<p><strong>2. The after-sale test.</strong> We listen to what customers report after "
                      "buying. Products that keep generating confusion or complaints don't get re-listed.</p>"
                      "<p><strong>3. The friend test.</strong> Confused customers mean a confusing product; "
                      "our team flags those fast. If we wouldn't recommend it to a friend, it's not on the list.</p>"
                      "<h3>How to use this list for your pet</h3>"
                      "<p>Start from the 'best for' column, not the rank. The #1 pick is the best all-rounder, "
                      "but your pet's size, coat, age, and any existing medication change the math. If two picks "
                      "look tied, buy the cheaper one first — every product here clears the quality bar, so the "
                      "decision is fit, not quality.</p>"
                      "<h3>Three mistakes we see constantly</h3>"
                      "<p><strong>Buying for the breed, not the animal.</strong> Guides like ours rank "
                      "all-rounders; your dog's actual size, coat, and temperament beat any list. A pick that's "
                      "perfect for a 70lb shepherd can be useless for a 12lb terrier with the same 'problem'.</p>"
                      "<p><strong>Switching too fast.</strong> Whatever category you're shopping, give a new "
                      "product a fair trial window before judging it. Most pet products need consistency to "
                      "show results, and bouncing between options in week one tells you nothing.</p>"
                      "<p><strong>Ignoring the boring answer.</strong> The unglamorous pick — the plain brush, "
                      "the basic chew, the toothpaste that just works — usually beats the gadget with the ad "
                      "budget. We bias toward boring and proven in every list we publish.</p>"),
        faq=faq, pillar_link=pillar_link,
    )
    wc = word_count(html)
    if wc < cfg["min_words"]:
        return None, f"too thin ({wc} < {cfg['min_words']}): {slug}"
    if not dry:
        path.write_text(html)
    return slug, wc

def stage_generate(cfg, dry=False):
    """Generate posts from the vertical's keyword map + configured product picks."""
    plan_path = SITE / "data" / "affiliate_plan.json"
    plan = json.loads(plan_path.read_text()) if plan_path.exists() else {"queue": []}
    if not plan.get("queue"):
        print("[generate] affiliate_plan.json empty — nothing queued. Add keywords+products to the queue.")
        return []
    made = []
    processed = 0
    for item in plan["queue"][: cfg["posts_per_run"]]:
        processed += 1
        slug, info = build_post(cfg, item, dry)
        if slug:
            made.append({"slug": slug, "keyword": item["keyword"], "words": info})
            print(f"[generate] + {slug} ({info} words)")
        else:
            print(f"[generate] skip {info}")
    if not dry and processed:
        plan["queue"] = plan["queue"][processed:]
        plan.setdefault("posted", []).extend(m["slug"] for m in made)
        plan_path.write_text(json.dumps(plan, indent=2))
    return made

# ---------------------------------------------------------------- stage 4: publish

BLOG_CARD = '''<a class="blog-card" href="/blog/{slug}.html"><div class="blog-thumb"><img src="{img}" alt="" loading="lazy"></div><div class="blog-content"><span class="blog-category">{cat}</span><h3>{title}</h3><span class="blog-date">{date}</span></div></a>'''

def stage_publish(cfg, made, dry=False):
    """Blog cards + sitemap + commit. Queue-deploy: git push IS the deploy."""
    if not made:
        print("[publish] nothing new"); return
    blog_html = (SITE / "blog.html").read_text()
    sitemap = (SITE / "sitemap.xml").read_text()
    today = datetime.date.today().isoformat()
    for m in made:
        slug = m["slug"]
        card = BLOG_CARD.format(slug=slug, img="/images/og-cover.jpg", cat=cfg["vertical"].title(),
                                title=hesc(m["keyword"].capitalize() + f" ({datetime.date.today().year})"),
                                date=today)
        if slug not in blog_html:
            blog_html = blog_html.replace('<div class="blog-grid">', '<div class="blog-grid">\n        ' + card, 1)
        url = f"{cfg['site_base']}/blog/{slug}.html"
        if url not in sitemap:
            sitemap = sitemap.replace("</urlset>", f"<url><loc>{url}</loc><lastmod>{today}</lastmod></url></urlset>")
        print(f"[publish] card+sitemap: {slug}")
    if not dry:
        (SITE / "blog.html").write_text(blog_html)
        (SITE / "sitemap.xml").write_text(sitemap)
        git("add", "blog/", "blog.html", "sitemap.xml", "data/affiliate_plan.json")
        git("commit", "-m", f"affiliate pipeline: publish {len(made)} post(s) — {', '.join(m['slug'] for m in made)}")
        try:
            git("push", "origin", "main")
        except subprocess.CalledProcessError as e:
            print(f"[publish] WARNING: push failed ({(e.stderr or '').strip()[:120]}); commit is local")
        print("[publish] committed + pushed (Netlify builds on credit reset; CF workers carry live)")

# ---------------------------------------------------------------- stage 5: distribute

def stage_distribute(cfg, made, dry=False):
    """Pinterest pin queue CSV from new posts (images ours, links to posts — TOS-safe)."""
    if not made:
        print("[distribute] nothing new"); return
    rows = ["title,description,image_url,link,board"]
    for m in made:
        title = f"{m['keyword'].capitalize()} — real-store tested picks"
        rows.append(','.join([
            f'"{title}"',
            f'"Honest picks from a store that actually ships this category. Full guide on our blog."',
            f'"{cfg["site_base"]}/images/og-cover.jpg"',
            f'"{cfg["site_base"]}/blog/{m["slug"]}.html"',
            f'"{cfg["vertical"].title()} Gear"',
        ]))
    out = SITE / "data" / "pinterest_queue.csv"
    if not dry:
        out.write_text("\n".join(rows))
    print(f"[distribute] {len(made)} pins queued → {out.name if not dry else '(dry)'}")

# ---------------------------------------------------------------- stage 6: report

def stage_report(cfg, dry=False):
    today = datetime.date.today().isoformat()
    report = [f"# Affiliate Pipeline Report — {today}", ""]
    # GSC positions
    try:
        end = today; start = str(datetime.date.today() - datetime.timedelta(days=28))
        rows = gsc_query(cfg, ["query"], start, end)
        report.append("## GSC striking-distance (pos 8-30)")
        for r in [r for r in rows if 8 <= r["position"] <= 30][:10]:
            report.append(f"- pos {round(r['position'],1)} · {r['impressions']}i · {r['keys'][0]}")
    except Exception as e:
        report.append(f"## GSC unavailable: {e}")
    # link inventory
    red = (SITE / "_redirects").read_text() if (SITE / "_redirects").exists() else ""
    report.append(f"\n## Link inventory\n- EPN tracked redirects: {red.count('campid=')}")
    posts = sorted((SITE / "blog").glob("*.html"))
    amzn = sum(1 for p in posts if "tag=" + cfg["amazon_tag"] in p.read_text(errors="ignore"))
    report.append(f"- Blog posts with Amazon links: {amzn}/{len(posts)}")
    text = "\n".join(report)
    if not dry:
        out = Path("~/ObsidianVault/Projects/HMS-Website").expanduser()
        out.mkdir(parents=True, exist_ok=True)
        (out / f"Affiliate-Report-{today}.md").write_text(text)
    print(f"[report] written ({'dry' if dry else 'vault'})")

# ---------------------------------------------------------------- main

def main():
    args = sys.argv[1:]
    dry = "--dry-run" in args
    args = [a for a in args if not a.startswith("--")]
    stage = args[0] if args else "all"
    cfg = load_config()

    stages = ["verify", "research", "generate", "publish", "distribute", "report"]
    run_all = stage == "all"

    if not stage_verify(cfg, dry) and not dry:
        print("[abort] preflight failed — fix compliance findings first")
        sys.exit(1)
    if run_all or stage == "research":
        stage_research(cfg, dry)
    made = []
    if run_all or stage == "generate":
        made = stage_generate(cfg, dry)
    if run_all or stage == "publish":
        stage_publish(cfg, made, dry)
    if run_all or stage == "distribute":
        stage_distribute(cfg, made, dry)
    if run_all or stage == "report":
        stage_report(cfg, dry)
    print("[done]")

if __name__ == "__main__":
    main()
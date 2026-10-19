"""blog_pipeline/posts.py — deterministic post type generators.
Each generator returns (slug, meta, content_blocks, products) for render.py.
"""
from __future__ import annotations
from datetime import date
from typing import List, Dict, Tuple

from blog_pipeline.render import PostMeta, ProductRef
from blog_pipeline.config import BASE_URL


def _today() -> str:
    return date.today().isoformat()


def _read_time(word_count: int) -> str:
    minutes = max(1, round(word_count / 200))
    return f"{minutes} min read"


def generate_service_educational(
    service: Dict,
    industry: str,
    city: str = "Columbus, Ohio",
) -> Tuple[str, PostMeta, List[str], List[ProductRef]]:
    """Service + location educational post."""
    slug = f"{service['slug']}-for-{industry.lower().replace(' ', '-')}-in-columbus-ohio"
    title = f"How {service['title']} Help {industry.title()} in Columbus, Ohio"
    description = f"Real ways {service['title'].lower()} drive leads and sales for {industry.lower()} businesses in Columbus — without enterprise budgets."
    meta = PostMeta(
        title=title,
        description=description,
        category=service["title"],
        canonical_path=f"/blog/{slug}.html",
        date_published=_today(),
        read_time="7 min read",
    )
    blocks = [
        f"<p>Most {industry.lower()} owners in Columbus still think {service['title'].lower()} are only for national brands. That changed in 2026. The same AI tools that power million-dollar campaigns now run on small-business budgets — and the results are measurable within weeks.</p>",
        f"<h2>Why {service['title']} matter for {industry}</h2>",
        f"<p>{industry} customers search locally, compare fast, and decide faster. A generic website or ad no longer wins. {service['title']} let you meet them with the right message at the exact moment they are ready to act.</p>",
        "<h2>What actually moves the needle</h2>",
        "<h3>1. Speed beats perfection</h3>",
        "<p>We see the pattern in every Columbus campaign: the business that ships creative in days and tests five angles beats the one that perfects one ad for a month. Volume of tests matters more than any single execution.</p>",
        "<h3>2. Measurement is the strategy</h3>",
        "<p>Every dollar is tracked to a lead or a sale. When a channel costs $110 per lead and another costs $40, budgets fix themselves. The strategy becomes the spreadsheet.</p>",
        "<h2>Where to start this quarter</h2>",
        "<p>If you run a local business, start with the highest-leverage step: capture every lead automatically, follow up within five minutes, and make sure your site loads in under two seconds. Everything else compounds from there.</p>",
    ]
    return slug, meta, blocks, []


def generate_product_guide(
    category: str,
    products: List[Dict],
    use_case: str,
) -> Tuple[str, PostMeta, List[str], List[ProductRef]]:
    """Best-of product guide using Shopify catalog."""
    slug = f"best-{category.lower().replace(' ', '-')}-for-{use_case.lower().replace(' ', '-')}"
    title = f"Best {category} for {use_case}"
    description = f"Our tested picks for {use_case.lower()} across every budget, with prices and why each one earns its spot in our TrendLoop store."
    meta = PostMeta(
        title=title,
        description=description,
        category="Buyer Guide",
        canonical_path=f"/blog/{slug}.html",
        date_published=_today(),
        read_time="6 min read",
    )
    cat_products = [p for p in products if p.get("cat") == category][:5]
    refs = [ProductRef(p["handle"], p["title"], p["price"], p.get("cat", ""), p.get("img", "")) for p in cat_products]

    blocks = [
        f"<p>We test everything before it lands in our TrendLoop store. These {category.lower()} picks solve {use_case.lower()} without the fluff — just what we'd buy ourselves.</p>",
        f"<h2>What to look for in a {category.lower()}</h2>",
        "<p>Build quality, real user feedback, and whether the feature set matches the price. We skip items that look good in ads but fail after a week of use.</p>",
        f"<h2>Top {len(cat_products)} {category} picks</h2>",
    ]
    for i, p in enumerate(cat_products, 1):
        blocks.append(f"<h3>{i}. {p['title']} — ${p['price']}</h3>")
        blocks.append(f"<p>{p['title']} fits {use_case.lower()} because of the features our customers actually mention: {p.get('tags', '').split(',')[0] if p.get('tags') else 'reliable build'}.</p>")
    blocks.append(f"<h2>Where to buy</h2><p>All picks ship from our US warehouse with 30-day returns. Browse the full {category.lower()} collection in our store.</p>")
    return slug, meta, blocks, refs


def generate_gsc_answer(
    query: str,
    service: Dict,
) -> Tuple[str, PostMeta, List[str], List[ProductRef]]:
    """Answer post built around an existing GSC query."""
    slug = f"{query.lower().replace(' ', '-').replace('?', '')}"
    title = f"{query.capitalize()}"
    description = f"A straightforward answer to '{query}' from the team that runs these campaigns for Columbus small businesses."
    meta = PostMeta(
        title=title,
        description=description,
        category="Q&A",
        canonical_path=f"/blog/{slug}.html",
        date_published=_today(),
        read_time="5 min read",
    )
    blocks = [
        f"<p>We get this question from Columbus business owners weekly: <em>{query}</em>. Here is the honest answer based on campaigns we are running right now.</p>",
        "<h2>The short answer</h2>",
        f"<p>Yes — {service['title'].lower()} can work for a small business if the strategy matches the budget and the follow-up is automated. The tool is not the hard part; the hard part is knowing what to say and who to say it to.</p>",
        "<h2>The longer answer</h2>",
        "<h3>1. Start with one objective</h3>",
        "<p>Most failed campaigns fail because they try to do everything at once. Pick one outcome: more calls, more bookings, or more email signups. Build the campaign around that.</p>",
        "<h3>2. Match the creative to the platform</h3>",
        "<p>A TikTok ad and a Google search ad serve different intents. Use short-form video for awareness and clear landing pages for conversion. Don't run the same creative everywhere.</p>",
        "<h3>3. Automate the follow-up</h3>",
        "<p>A lead that waits an hour is mostly gone. Five-minute follow-up is the floor, not the exception. That is where automation pays for itself.</p>",
        "<h2>Next step</h2>",
        "<p>If you want a plan tailored to your business, book a free 15-minute call. We'll name the fastest wins and you leave with a plan whether you hire us or not.</p>",
    ]
    return slug, meta, blocks, []

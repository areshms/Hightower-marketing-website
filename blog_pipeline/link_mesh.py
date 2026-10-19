"""blog_pipeline/link_mesh.py — deterministic internal-link selection + anchor text rules.
"""
from __future__ import annotations
import random
from dataclasses import dataclass
from typing import List, Dict
from pathlib import Path

from blog_pipeline.config import SERVICE_PAGES, BASE_URL, VALIDATION, SHOPIFY_SHOP


@dataclass
class LinkTarget:
    href: str
    label: str  # human name, used to construct anchors
    category: str  # service, product, post, cta
    hub: str | None = None  # which service hub this target belongs to


ANCHOR_TEMPLATES = {
    "service": [
        "our {label} service",
        "{label} for Columbus businesses",
        "learn more about {label}",
        "the {label} we run",
    ],
    "product_hub": [
        "the products we feature in those campaigns",
        "curated {label} we recommend",
        "our {label} shop",
    ],
    "post": [
        "how {label} fits in",
        "our guide to {label}",
        "read the {label} breakdown",
    ],
    "cta": [
        "Book a free consultation",
        "Get a free 15-minute call",
        "Talk to our team",
    ],
}


def build_service_targets() -> List[LinkTarget]:
    return [
        LinkTarget(href=f"/{p['slug']}.html", label=p["title"], category="service", hub=p["slug"])
        for p in SERVICE_PAGES
    ]


def build_product_targets(products: List[Dict]) -> List[LinkTarget]:
    targets = [LinkTarget(href="/products.html", label="TrendLoop products", category="product_hub")]
    for p in products:
        targets.append(LinkTarget(
            href=f"{SHOPIFY_SHOP}{p['handle']}",
            label=p["title"],
            category="product",
            hub=p.get("cat"),
        ))
    return targets


def build_post_targets(blog_dir: Path) -> List[LinkTarget]:
    targets = []
    if not blog_dir.exists():
        return targets
    for path in sorted(blog_dir.glob("*.html")):
        # summary extraction would be done here; for now use filename
        label = path.stem.replace("-", " ")
        targets.append(LinkTarget(href=f"/blog/{path.name}", label=label, category="post"))
    return targets


def select_links(
    post_type: str,
    primary_hub: str,
    service_targets: List[LinkTarget],
    product_targets: List[LinkTarget],
    post_targets: List[LinkTarget],
    seed: int | None = None,
) -> List[Dict]:
    """Return 3-5 internal links with anchor text, obeying exact-match rules.

    Returns list of {"href", "anchor", "target", "link_type"}.
    """
    rng = random.Random(seed)
    links = []

    # 1. Primary service link
    primary = next((t for t in service_targets if t.hub == primary_hub), None)
    if primary:
        tpl = rng.choice(ANCHOR_TEMPLATES["service"])
        links.append({
            "href": primary.href,
            "anchor": tpl.format(label=primary.label),
            "target": "_self",
            "link_type": "internal",
        })

    # 2. Product hub link (only for product/service posts)
    if post_type in ("product_guide", "service_educational", "case_study"):
        hub = next((t for t in product_targets if t.href == "/products.html"), None)
        if hub:
            links.append({
                "href": hub.href,
                "anchor": rng.choice(ANCHOR_TEMPLATES["product_hub"]).format(label=hub.label),
                "target": "_self",
                "link_type": "internal",
            })

    # 4. Cross-post links (prefer related hubs)
    related = [t for t in post_targets if primary_hub.replace("-", " ") in t.label or primary_hub in t.href]
    if not related:
        related = post_targets
    if related:
        for t in rng.sample(related, min(1, len(related))):
            tpl = rng.choice(ANCHOR_TEMPLATES["post"])
            links.append({
                "href": t.href,
                "anchor": tpl.format(label=t.label),
                "target": "_self",
                "link_type": "internal",
            })

    # Template already includes CTA + back-link; cap content links at 3 so total stays ≤ 5.
    if len(links) > 3:
        links = links[:3]
    return links


def anchor_audit(links: List[Dict], exact_keywords: List[str]) -> Dict:
    """Return exact-match ratio and forbidden anchors."""
    exact = sum(1 for l in links if any(kw.lower() in l["anchor"].lower() for kw in exact_keywords))
    forbidden = [l["anchor"] for l in links if l["anchor"].lower() in ("click here", "read more", "link", "here")]
    return {
        "exact_count": exact,
        "exact_ratio": exact / len(links) if links else 0,
        "forbidden": forbidden,
    }

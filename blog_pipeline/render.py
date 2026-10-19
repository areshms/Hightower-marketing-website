"""blog_pipeline/render.py — deterministic HTML post renderer.
No LLM calls. All content comes from templates + data inserts.
"""
from __future__ import annotations
import json, re, html
from datetime import date
from pathlib import Path
from string import Template
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from blog_pipeline.config import (
    TEMPLATE_DIR, BASE_URL, BLOG_DIR, SERVICE_PAGES, SHOPIFY_SHOP,
)


@dataclass(frozen=True)
class PostMeta:
    title: str
    description: str
    category: str
    canonical_path: str
    og_image: str = "/og-cover.jpg"
    date_published: str | None = None
    read_time: str | None = None


@dataclass
class InternalLink:
    href: str
    anchor: str
    target: str = "_self"
    link_type: str = "internal"  # internal, cta, product


@dataclass
class ProductRef:
    handle: str
    title: str
    price: str
    category: str
    img: str


def _safe(value: Any) -> str:
    if value is None:
        return ""
    return html.escape(str(value))


def estimate_read_time(word_count: int) -> str:
    minutes = max(1, round(word_count / 200))
    return f"{minutes} min read"


def build_schema_blog_posting(meta: PostMeta) -> Dict[str, Any]:
    return {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": meta.title,
        "url": f"{BASE_URL}{meta.canonical_path}",
        "datePublished": meta.date_published or date.today().isoformat(),
        "publisher": {
            "@type": "Organization",
            "name": "Hightower Marketing Strategies",
            "url": f"{BASE_URL}/",
        },
        "description": meta.description,
    }


def _link_to_html(link: InternalLink) -> str:
    rel = ' rel="noopener"' if link.target == "_blank" else ""
    return f'<a href="{link.href}" target="{link.target}"{rel}>{_safe(link.anchor)}</a>'


def render_post(
    post_type: str,
    slug: str,
    meta: PostMeta,
    content_blocks: List[str],
    links: List[InternalLink],
    products: Optional[List[ProductRef]] = None,
    featured_img_alt: str = "",
) -> str:
    """Assemble a complete blog HTML page from a type template.

    Args:
        post_type: matches templates/type_{post_type}.html.
        slug: filename stem used in /blog/{slug}.html.
        meta: SEO + display metadata.
        content_blocks: rendered HTML body sections in order.
        links: internal links selected by link_mesh.
        products: optional product cards for product-guide posts.
        featured_img_alt: alt text for the hero image.

    Returns:
        Full HTML page string.
    """
    template_path = TEMPLATE_DIR / f"type_{post_type}.html"
    base_path = TEMPLATE_DIR / "base.html"
    if not template_path.exists():
        raise FileNotFoundError(f"Missing post template: {template_path}")
    if not base_path.exists():
        raise FileNotFoundError(f"Missing base template: {base_path}")

    body_template = Template(base_path.read_text())
    type_template = Template(template_path.read_text())

    cta_link = next((l for l in links if l.link_type == "cta"), None)
    cta_html = _link_to_html(cta_link) if cta_link else '<a href="/contact" class="btn-gold">Get a free consultation</a>'

    body_content = type_template.safe_substitute(
        H1=_safe(meta.title),
        LEDE="".join(content_blocks[:1]) if content_blocks else "",
        BODY="".join(content_blocks[1:]) if len(content_blocks) > 1 else "",
        CTA=cta_html,
        BACK_LINK='<a href="/blog" class="back-link">← Back to all posts</a>',
        PRIMARY_CATEGORY=_safe(meta.category),
        DATE_PUBLISHED=_safe(meta.date_published or date.today().isoformat()),
        READ_TIME=_safe(meta.read_time or estimate_read_time(count_words("".join(content_blocks)))),
    )

    schema = build_schema_blog_posting(meta)
    canonical = f"{BASE_URL}{meta.canonical_path}"
    twitter_image = meta.og_image if meta.og_image.startswith("http") else f"{BASE_URL}{meta.og_image}"
    og_image = twitter_image

    page = body_template.safe_substitute(
        TITLE=_safe(meta.title),
        DESCRIPTION=_safe(meta.description),
        CANONICAL=canonical,
        OG_TYPE="article",
        OG_TITLE=_safe(meta.title),
        OG_DESCRIPTION=_safe(meta.description),
        OG_URL=canonical,
        OG_IMAGE=og_image,
        TWITTER_CARD="summary_large_image",
        TWITTER_TITLE=_safe(meta.title),
        TWITTER_DESCRIPTION=_safe(meta.description),
        TWITTER_IMAGE=twitter_image,
        SCHEMA_LD=json.dumps(schema, indent=2),
        BODY_CONTENT=body_content,
    )
    return page


def write_post(slug: str, html_out: str) -> Path:
    out_path = BLOG_DIR / f"{slug}.html"
    out_path.write_text(html_out)
    return out_path

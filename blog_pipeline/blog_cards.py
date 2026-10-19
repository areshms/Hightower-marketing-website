"""blog_pipeline/blog_cards.py — inject newest post cards into blog.html."""
from __future__ import annotations
import re, html
from datetime import datetime
from pathlib import Path
from typing import List, Dict

from blog_pipeline.config import REPO_ROOT, BASE_URL


def parse_post_summary(post_html_path: Path) -> Dict:
    """Extract title, category, date, lede, url from a generated post."""
    text = post_html_path.read_text()
    title_match = re.search(r"<title>(.*?)</title>", text)
    title = title_match.group(1).split(" — ")[0] if title_match else post_html_path.stem.replace("-", " ")

    meta_desc = re.search(r'<meta name="description" content="(.*?)"', text)
    lede = meta_desc.group(1) if meta_desc else ""

    category_match = re.search(r'"post-meta"[^>]*>([^·]+)', text)
    category = category_match.group(1).strip() if category_match else "Marketing"

    date_match = re.search(r"datePublished\": \"(\d{4}-\d{2}-\d{2})\"", text)
    date_str = date_match.group(1) if date_match else datetime.fromtimestamp(post_html_path.stat().st_mtime).strftime("%B %d, %Y")

    return {
        "url": f"/blog/{post_html_path.name}",
        "title": title,
        "category": category,
        "date": date_str,
        "lede": lede,
        "slug": post_html_path.stem,
    }


def _card_html(post: Dict) -> str:
    title = html.escape(post["title"])
    category = html.escape(post["category"])
    date_display = _iso_to_display(post["date"])
    lede = html.escape(post["lede"][:140] + "…" if len(post["lede"]) > 140 else post["lede"])
    lines = [
        '                <a href="{url}" class="blog-card" data-aos="fade-up">'.format(url=post["url"]),
        '                    <div class="blog-thumb">',
        '                        <span style="position: relative; z-index: 2;"></span>',
        '                    </div>',
        '                    <div class="blog-content">',
        '                        <div class="blog-meta">',
        '                            <span class="blog-category">{category}</span>'.format(category=category),
        '                            <span class="blog-date">{date}</span>'.format(date=date_display),
        '                        </div>',
        '                        <h3>{title}</h3>'.format(title=title),
        '                        <p>{lede}</p>'.format(lede=lede),
        '                        <span class="read-more">Read more →</span>',
        '                    </div>',
        '                </a>',
    ]
    return "\n".join(lines)


def _iso_to_display(iso: str) -> str:
    try:
        dt = datetime.strptime(iso, "%Y-%m-%d")
        return dt.strftime("%B %d, %Y")
    except Exception:
        return iso


def update_blog_cards(
    blog_html_path: Path = REPO_ROOT / "blog.html",
    blog_dir: Path = REPO_ROOT / "blog",
    max_cards: int = 9,
) -> Path:
    """Replace the contents of <div class="blog-grid"> with newest posts."""
    if not blog_dir.exists():
        return blog_html_path
    posts = [parse_post_summary(p) for p in sorted(blog_dir.glob("*.html"), key=lambda p: p.stat().st_mtime, reverse=True)]
    posts = posts[:max_cards]
    cards_html = "".join(_card_html(p) for p in posts)

    text = blog_html_path.read_text()
    pattern = r'(<div class="blog-grid">)(.*?)(</div>)'
    replacement = r"\1" + cards_html + "\n            \3"
    new_text = re.sub(pattern, replacement, text, flags=re.DOTALL)
    blog_html_path.write_text(new_text)
    return blog_html_path

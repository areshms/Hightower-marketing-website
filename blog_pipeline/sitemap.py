"""blog_pipeline/sitemap.py — regenerate sitemap.xml with new blog posts."""
from __future__ import annotations
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path
from typing import List

from blog_pipeline.config import REPO_ROOT, BASE_URL, BLOG_DIR


def discover_blog_paths(blog_dir: Path) -> List[str]:
    """Return /blog/*.html paths sorted by file mtime descending."""
    if not blog_dir.exists():
        return []
    paths = sorted(blog_dir.glob("*.html"), key=lambda p: p.stat().st_mtime, reverse=True)
    return [f"/blog/{p.name}" for p in paths]


def _existing_pages(sitemap_path: Path) -> List[str]:
    if not sitemap_path.exists():
        return []
    tree = ET.parse(sitemap_path)
    root = tree.getroot()
    ns = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    locs = []
    for loc in root.findall("ns:url/ns:loc", ns):
        if loc.text:
            locs.append(loc.text.replace(BASE_URL, ""))
    return locs


def update_sitemap(
    repo_root: Path = REPO_ROOT,
    base_url: str = BASE_URL,
    blog_dir: Path = BLOG_DIR,
) -> Path:
    """Merge static pages from existing sitemap with current blog posts."""
    sitemap_path = repo_root / "sitemap.xml"
    existing = _existing_pages(sitemap_path)
    # Keep non-blog pages, drop stale blog entries
    static_pages = [p for p in existing if not p.startswith("/blog/")]
    blog_paths = discover_blog_paths(blog_dir)
    all_paths = static_pages + blog_paths

    ns = "http://www.sitemaps.org/schemas/sitemap/0.9"
    root = ET.Element("urlset", {"xmlns": ns})
    today = date.today().isoformat()
    priorities = {
        "/": "1.0",
        "/contact.html": "0.8",
        "/case-studies.html": "0.8",
        "/products.html": "0.8",
        "/services.html": "0.7",
        "/blog.html": "0.7",
    }

    seen = set()
    for path in all_paths:
        if path in seen:
            continue
        seen.add(path)
        url = ET.SubElement(root, "url")
        ET.SubElement(url, "loc").text = f"{base_url}{path}"
        ET.SubElement(url, "lastmod").text = today
        ET.SubElement(url, "changefreq").text = "monthly"
        ET.SubElement(url, "priority").text = priorities.get(path, "0.6")

    tree = ET.ElementTree(root)
    tree.write(sitemap_path, encoding="UTF-8", xml_declaration=True)
    return sitemap_path

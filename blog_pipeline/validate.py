"""blog_pipeline/validate.py — guards against thin / harmful / duplicate content."""
from __future__ import annotations
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict

from blog_pipeline.config import VALIDATION, BLOCKED_PHRASES, BLOG_DIR


@dataclass
class PostValidation:
    word_count: int
    h2_count: int
    internal_link_count: int
    exact_anchor_ratio: float
    has_blocked_phrase: bool
    duplicate_title: bool
    schema_valid: bool
    errors: List[str]


def count_words(html_text: str) -> int:
    text = re.sub(r"<[^>]+>", " ", html_text)
    text = re.sub(r"&\w+;", " ", text)
    return len(re.findall(r"\b\w+\b", text))


def count_h2(html_text: str) -> int:
    return len(re.findall(r"<h2[\s\S]*?>", html_text, flags=re.IGNORECASE))


def extract_title(html_text: str) -> str:
    m = re.search(r"<title>(.*?)\s*—\s*", html_text)
    if m:
        return m.group(1).strip().lower()
    m = re.search(r"<title>(.*?)</title>", html_text)
    return m.group(1).strip().lower() if m else ""


def has_blocked_phrase(html_text: str) -> bool:
    lowered = html_text.lower()
    return any(re.search(pat, lowered) for pat in BLOCKED_PHRASES)


def is_duplicate_title(title: str, blog_dir: Path, exclude: Path | None = None) -> bool:
    if not blog_dir.exists():
        return False
    for p in blog_dir.glob("*.html"):
        if exclude and p == exclude:
            continue
        if extract_title(p.read_text()) == title:
            return True
    return False


def validate_post(html_text: str, post_path: Path | None = None) -> PostValidation:
    errors: List[str] = []
    words = count_words(html_text)
    h2s = count_h2(html_text)
    article = re.search(r"(<article>)(.*?)(</article>)", html_text, flags=re.DOTALL)
    links = len(re.findall(r'<a [^>]*href="[^"]+"', article.group(2) if article else html_text))
    exact_ratio = 0.0
    blocked = has_blocked_phrase(html_text)
    title = extract_title(html_text)
    dup = is_duplicate_title(title, BLOG_DIR, exclude=post_path)
    schema_valid = '"@type": "BlogPosting"' in html_text and "datePublished" in html_text

    if words < VALIDATION.min_words:
        errors.append(f"Too few words: {words} < {VALIDATION.min_words}")
    if h2s < VALIDATION.min_h2:
        errors.append(f"Too few H2: {h2s} < {VALIDATION.min_h2}")
    if links < VALIDATION.min_internal_links:
        errors.append(f"Too few internal links: {links} < {VALIDATION.min_internal_links}")
    if links > VALIDATION.max_internal_links:
        errors.append(f"Too many internal links: {links} > {VALIDATION.max_internal_links}")
    if blocked:
        errors.append("Contains blocked phrase")
    if dup:
        errors.append("Duplicate title")
    if not schema_valid:
        errors.append("Missing valid BlogPosting schema")

    return PostValidation(
        word_count=words,
        h2_count=h2s,
        internal_link_count=links,
        exact_anchor_ratio=exact_ratio,
        has_blocked_phrase=blocked,
        duplicate_title=dup,
        schema_valid=schema_valid,
        errors=errors,
    )


def passes_gates(pv: PostValidation) -> bool:
    return len(pv.errors) == 0 and pv.exact_anchor_ratio <= VALIDATION.max_exact_anchor_ratio

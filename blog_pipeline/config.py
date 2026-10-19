"""blog_pipeline/config.py — deterministic pipeline settings."""
from pathlib import Path
from dataclasses import dataclass

REPO_ROOT = Path('/Users/ares.hmsgmail.com/projects/hms-site')
PIPELINE_DIR = REPO_ROOT / 'blog_pipeline'
DATA_DIR = PIPELINE_DIR / 'data'
TEMPLATE_DIR = PIPELINE_DIR / 'templates'
BLOG_DIR = REPO_ROOT / 'blog'
BASE_URL = 'https://www.hightower-marketing.com'
SHOPIFY_SHOP = 'https://shop.hightower-marketing.com/products/'
NETLIFY_DEPLOY_HOOK = None  # set to URL in env or local override

@dataclass(frozen=True)
class ValidationLimits:
    min_words: int = 700
    min_h2: int = 2
    min_internal_links: int = 3
    max_internal_links: int = 5
    max_exact_anchor_ratio: float = 0.20
    max_posts_per_week: int = 4

VALIDATION = ValidationLimits()

SERVICE_PAGES = [
    {"slug": "ai-video-ads", "title": "AI Video Ads", "kw": "ai video ads"},
    {"slug": "ai-website-builder", "title": "AI Website Builder", "kw": "ai website builder"},
    {"slug": "automation-services", "title": "Marketing Automation", "kw": "marketing automation"},
    {"slug": "digital-strategy", "title": "Digital Strategy", "kw": "digital marketing strategy"},
    {"slug": "pet-portraits", "title": "AI Pet Portraits", "kw": "ai pet portraits"},
    {"slug": "services", "title": "Services", "kw": "marketing services"},
    {"slug": "products", "title": "Shop", "kw": "trendloop products"},
]

BLOCKED_PHRASES = [
    r"guaranteed\s+#?1",
    r"instant\s+results",
    r"cures?\s+",
    r"permanent\s+(whiten|clear|remove)",
]

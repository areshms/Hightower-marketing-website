# Tokenless SEO Blog Pipeline Design — Hightower Marketing

A deterministic, template-driven system that generates static HTML blog posts from three on-site / free data sources (Shopify catalog, GSC query cache, service-page manifest), updates `sitemap.xml` and `blog.html`, then commits and deploys to Netlify. No LLM token is consumed at generation time.

---

## 1. Post Types (Ranked by SEO Impact)

| Rank | Type | Why it ranks | Data source | Primary target keywords | Internal-link plan |
|------|------|--------------|-------------|-------------------------|-------------------|
| **1** | **Service + location educational** | Local commercial intent, low competition, ties agency to city + offering | `service_pages.json` + Columbus OH geo slots | `ai video ads Columbus Ohio`, `marketing automation small business Columbus`, `website builder Columbus Ohio` | → Own service page (exact service), → `/contact`, → 1 related product category on `/products.html`, → 1 older post |
| **2** | **Product category buyer guides** | Captures bottom-funnel product search, monetizes Shopify store via content | Shopify JSON (`title`, `tags`, `price`, `cat`, `handle`) | `best night light for kids`, `LED face mask review`, `pet grooming tools 2026`, `cozy gifts under $25` | → `/products.html#filter`, → related product detail (Shopify), → `/services.html` or `/ai-video-ads.html` ("we use these in ads"), → 1 service post |
| **3** | **GSC query-answer expansion** | Doubles down on queries Google already associates with the site; fastest impression→click lift | Cached GSC top queries + pages | Existing `query` strings with impressions but low CTR/position 5-15 | → Service page that matches query intent, → `/blog.html`, → relevant product post, → `/contact` |
| **4** | **Case-study / results posts** (anonymized) | Proof + E-E-A-T for agency side; earns backlinks and branded search | Internal campaign notes (manually curated JSON) | `small business marketing results Columbus`, `ai video ad campaign case study` | → `/case-studies.html`, → matching service page, → `/contact`, → 2 related posts |
| **5** | **Seasonal / calendar trend posts** | Recurring traffic spikes; low-effort refresh each year | Date + product catalog (seasonal tags) | `holiday marketing ideas small business`, `2026 small business marketing trends` | → `/products.html`, → `/services.html`, → 2 related posts |
| **6** | **Tool / template giveaway posts** | Lead-gen + list-building; indirect SEO via shares/backlinks | Static template list + Shopify product tie-ins | `free marketing automation checklist`, `small business video ad script template` | → `/contact`, → `/automation-services.html`, → giveaway landing page, → 1 product post |

### Template structure for every post

```
├── HEAD
│   ├── <title> (≤ 60 chars)
│   ├── meta description (≤ 160 chars)
│   ├── canonical
│   ├── robots index,follow
│   ├── OG + Twitter tags
│   └── JSON-LD BlogPosting (datePublished, author=publisher)
├── NAV (matches site)
├── ARTICLE
│   ├── post-meta (category, date, read time)
│   ├── H1
│   ├── lede paragraph
│   ├── 2-4 H2 sections
│   │   └── 2-3 H3 subsections
│   ├── internal CTA box (links to service/contact)
│   └── back-link to /blog
└── FOOTER
```

Every post must contain **≥ 700 words**, **1 featured image with alt text**, **3-5 internal links**, and **2 outbound nofollow links only when citing sources**.

---

## 2. Pipeline Architecture

### Module list & file responsibilities

```
blog_pipeline/
├── config.py                    # Paths, URLs, cadence, thresholds
├── data/
│   ├── service_pages.json       # 7 service hubs + slugs + target keywords
│   ├── shopify_products.json -> /tmp/shopify_products.json (symlink)
│   └── gsc_queries.json         # cached Search Console top queries/pages
├── templates/
│   ├── base.html                # HEAD, NAV, FOOTER skeleton
│   ├── type_service_educational.html
│   ├── type_product_guide.html
│   ├── type_gsc_answer.html
│   ├── type_case_study.html
│   └── type_seasonal_trend.html
├── render.py                    # Template engine + post assembly
├── posts.py                     # Post type definitions + generators
├── link_mesh.py                 # Hub/spoke internal-link selection + anchor text
├── sitemap.py                   # Regenerate sitemap.xml
├── blog_cards.py                # Inject newest cards into blog.html
├── gsc_loader.py                # Refresh GSC cache (reuses token chain)
├── validate.py                  # Thin-content / penalty guards
└── deploy.py                    # git commit + Netlify deploy hook

hms_blog_pipeline.py             # CLI entry point: generate, update, deploy
```

### Render function signatures

```python
# render.py
def render_post(
    post_type: str,                 # e.g. "service_educational"
    slug: str,                      # URL-safe filename stem
    title: str,
    meta: PostMeta,
    content_blocks: list[ContentBlock],
    links: list[InternalLink],
    products: list[ProductRef] | None,
    publish_date: str,               # ISO-8601
) -> str:
    """Return full HTML string from template + data."""

def estimate_read_time(word_count: int) -> str:
    """1 min per 200 words, rounded."""

def build_schema_blog_posting(meta, slug, date) -> dict:
    """Return JSON-LD dict for BlogPosting."""
```

### Sitemap updater

```python
# sitemap.py
def update_sitemap(
    repo_root: Path,
    base_url: str = "https://www.hightower-marketing.com",
    extra_paths: list[str] | None = None,
) -> None:
    """Read existing sitemap, add new blog paths, keep priorities, rewrite lastmod."""

def discover_blog_paths(blog_dir: Path) -> list[str]:
    """Return /blog/*.html paths sorted by file mtime descending."""
```

### Blog-card updater

```python
# blog_cards.py
def update_blog_cards(
    blog_html_path: Path,
    posts: list[PostSummary],
    max_cards: int = 9,
) -> None:
    """Replace the .blog-grid inner HTML with the newest posts."""

def parse_post_summary(post_html_path: Path) -> PostSummary:
    """Extract title, date, category, lede, url from a generated post."""
```

### Deploy step

```python
# deploy.py
def commit_and_push(
    repo_root: Path,
    message: str,
    files: list[Path],
) -> bool:
    """git add, commit, push origin main."""

def deploy_netlify(
    deploy_hook: str | None = None,
    poll_seconds: int = 60,
) -> bool:
    """Hit Netlify build hook URL; optional poll for success."""
```

### Cron schedule

```cron
# /etc/cron.d/hms-blog-pipeline
# GSC cache refresh: Sunday 06:00
0 6 * * 0 ares cd /Users/ares.hmsgmail.com/projects/hms-site && /Users/ares.hmsgmail.com/.local/bin/uv run python hms_blog_pipeline.py --refresh-gsc
# Generate + deploy one post: Tuesday and Friday 08:00
0 8 * * 2,5 ares cd /Users/ares.hmsgmail.com/projects/hms-site && /Users/ares.hmsgmail.com/.local/bin/uv run python hms_blog_pipeline.py --publish-next
```

---

## 3. Interlinking Mesh: 28 Products + 7 Services + Posts

### Topology: hybrid hub-and-spoke + topic clusters

* **Hubs (7 service pages):** `/ai-video-ads.html`, `/ai-website-builder.html`, `/automation-services.html`, `/digital-strategy.html`, `/pet-portraits.html`, `/services.html`, `/products.html` (store hub).
* **Topic clusters:** each service hub owns a cluster of 3-5 posts. Example: `ai-video-ads` cluster = "5-second hook", "TikTok ad script template", "video ad case study Columbus", "AI video tools 2026".
* **Product spokes:** product-guide posts link to `/products.html` filtered category + individual Shopify product pages. Each product card on `/products.html` is already a spoke.
* **Cross-cluster bridges:** 1 link per post to a related cluster to spread authority (e.g. a video-ads post links to an automation-services post because "follow-up automation converts ad leads").

### Rules per post

* **3-5 internal links total** (including CTA).
* **1 primary service link** matching post intent.
* **0-1 product links** (only when post is product-focused).
* **1-2 cross-post links** to published related posts.
* **No orphan pages:** every new post is linked from `/blog.html` and at least 1 older post.

### Anchor-text rules

```python
ANCHOR_RULES = {
    "exact_match_max_ratio": 0.20,      # ≤ 20% of links use exact keyword
    "preferred_types": ["branded", "partial", "natural", "CTA"],
    "forbidden": ["click here", "read more", "link", "this page", "here"],
    "brand_anchor": "Hightower Marketing",
    "cta_anchor": "Book a free consultation",
}
```

Example anchor set for a post about AI video ads:

1. "our AI video ads service" → `/ai-video-ads.html` (partial)
2. "schedule a free 15-minute call" → `/contact` (CTA)
3. "the products we feature in those ads" → `/products.html` (natural)
4. "automated follow-up turns views into leads" → `/blog/automation-services-smb.html` (cross-post, natural)

---

## 4. What NOT to Auto-Post

| Risk | Guard in `validate.py` | Example of blocked output |
|------|------------------------|---------------------------|
| **Thin content** | `word_count < 700` OR no H2/H3 | A 200-word product blurb |
| **Duplicate titles/descriptions** | Hash set of titles + meta desc across `/blog/*.html` | Two posts titled "Best Marketing Tools" |
| **Helpful-content penalty bait** | Flesch ease / fluff score; no substantive "how-to" steps | Generic listicle with no steps, screenshots, or data |
| **Doorway pages** | Same template used >3× with only city/keyword swapped | 50 pages of "[Service] in [City]" with no unique proof |
| **Unverifiable claims** | Blocked phrases regex: "guaranteed #1", "instant results" | "We guarantee first-page rankings" |
| **Medical/beauty overclaims** | Shopify tags `acne`, `anti-aging`, `whitening` trigger review flag | "This teeth whitening pen cures stains permanently" |
| **Over-optimized anchors** | Exact-match anchor ratio > 20% across new posts | Every post links to `/ai-video-ads.html` with exact anchor "AI video ads" |
| **Future-dated or stale** | `publish_date` must be today or past; seasonal posts refreshed yearly | A post dated 2027 published in 2026 |
| **Auto-generated index bloat** | Max 1 post per scheduled run; no more than 4 posts/week | Burst of 20 posts in one day |

### Hard validation gates

```python
VALIDATION_GATES = [
    lambda p: p.word_count >= 700,
    lambda p: p.h2_count >= 2,
    lambda p: p.internal_link_count in range(3, 6),
    lambda p: p.duplicate_title is False,
    lambda p: p.exact_anchor_ratio <= 0.20,
    lambda p: not p.has_blocked_phrase,
    lambda p: p.schema_valid,
]
```

---

## 5. Phased Rollout

### Phase 0 — Foundation (Week 0)

1. Build `blog_pipeline/` modules.
2. Create 3 post-type templates + 1 base template.
3. Seed `service_pages.json` and link-mesh rules.
4. Wire `hms_blog_pipeline.py` CLI with `--dry-run` mode.
5. Validate one dry-run post renders and passes all gates.

### Phase 1 — Seed Authority (Weeks 1-2)

* **Cadence:** 2 posts/week (Tue/Fri).
* **Types:** service-educational + product-guide.
* **Goal:** establish topical authority around agency services + Shopify categories.
* **Examples:**
  * "How AI Video Ads Work for Columbus Restaurants"
  * "Best Night Lights and Projectors for Cozy Rooms in 2026"

### Phase 2 — Capture Existing Demand (Weeks 3-4)

* **Cadence:** 2 posts/week.
* **Types:** GSC query-answer + case-study.
* **Goal:** lift CTR on queries already showing impressions.
* **Measurement:** compare pre/post GSC clicks and position for target query bucket.

### Phase 3 — Scale & Compound (Week 5+)

* **Cadence:** 3 posts/week if validation gates stay green.
* **Types:** rotate through all 6 types; refresh top-performing posts quarterly.
* **Goal:** 50+ posts within 6 months, each linked into the mesh.

### Measurement cadence

| Metric | Tool | Frequency |
|--------|------|-----------|
| Indexed pages | `site:hightower-marketing.com/blog/` | Weekly |
| Impressions / clicks per post | GSC cache (`gsc_queries.json`) | Weekly |
| Average position for target query | GSC API | Bi-weekly |
| Internal-link coverage | `link_mesh.py` audit | Monthly |
| Core Web Vitals | Netlify + PageSpeed | Monthly |

### Stop/scale rules

* **Pause if:** 2+ consecutive posts fail validation, or average position drops >2 positions for 2 weeks.
* **Scale if:** 3+ posts reach position ≤ 10 within 60 days.

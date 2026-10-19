#!/usr/bin/env python3
"""hms_products_page.py — build products.html for hms-site from the live Shopify catalog.
Links route to the Shopify storefront (shop.hightower-marketing.com). Images: Shopify CDN URLs direct.
Categories derived from tags/titles. Design matches site (dark + gold)."""
import json, os, re, html

DIR = os.path.expanduser('~/projects/hms-site')
prods = json.load(open('/tmp/shopify_products.json'))
SHOP = 'https://shop.hightower-marketing.com/products/'

def categorize(p):
    t = (p['title'] + ' ' + p['tags']).lower()
    if any(w in t for w in ['neck massager', 'gua sha', 'face mask', 'blackhead', 'teeth', 'turmeric', 'hair brush', 'trimmer', 'hair remover']): return 'Beauty & Grooming'
    if any(w in t for w in ['nail clipper', 'dog hoodie', 'pet']): return 'Pet'
    if any(w in t for w in ['night light', 'projector', 'lamp', 'humidifier', 'diffuser', 'solar', 'step fence']): return 'Home & Lighting'
    if any(w in t for w in ['plush', 'cat', 'bear', 'blanket', 'bracelet', 'eye mask', 'cable']): return 'Gifts & Cozy'
    return 'Home & Lighting'

cats = ['Beauty & Grooming', 'Pet', 'Home & Lighting', 'Gifts & Cozy']
for p in prods:
    p['cat'] = categorize(p)

def card(p):
    title = html.escape(p['title'])
    return f'''                    <div class="product-card" data-cat="{p['cat']}">
                        <a href="{SHOP}{p['handle']}" target="_blank" rel="noopener">
                            <div class="product-img-wrap">
                                <img src="{p['img']}" alt="{title}" loading="lazy">
                            </div>
                            <div class="product-info">
                                <span class="product-cat">{p['cat']}</span>
                                <h3 class="product-title">{title}</h3>
                                <div class="product-price">${p['price']}</div>
                                <span class="product-cta">View in store →</span>
                            </div>
                        </a>
                    </div>'''

cards = '\n'.join(card(p) for p in prods)
cat_tabs = '\n'.join(f'                    <button class="filter-btn" data-filter="{c}">{c}</button>' for c in cats)
cat_counts = {c: sum(1 for p in prods if p['cat'] == c) for c in cats}

page = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Shop TrendLoop Products — Hightower Marketing</title>
    <meta name="description" content="Shop curated TrendLoop products: cozy gifts, night lights, beauty tools and pet essentials. Fast US shipping, every item tested by our team before it lists.">
    <link rel="canonical" href="https://www.hightower-marketing.com/products.html">
    <meta name="robots" content="index, follow">
    <link rel="stylesheet" href="/aos.css">
    <script src="/aos.js"></script>
    <!-- motion layer (lenis + gsap, security-scanned 2026-10-16) -->
    <script src="/vendor/lenis.min.js"></script>
    <script src="/vendor/gsap.min.js"></script>
    <script src="/vendor/ScrollTrigger.min.js"></script>
    <script src="/vendor/hms-motion.js" defer></script>
    <meta property="og:type" content="website">
    <meta property="og:site_name" content="Hightower Marketing Strategies">
    <meta property="og:title" content="Shop TrendLoop Products — Hightower Marketing">
    <meta property="og:description" content="Shop curated TrendLoop products: cozy gifts, night lights, beauty tools and pet essentials. Fast US shipping.">
    <meta property="og:url" content="https://www.hightower-marketing.com/products.html">
    <meta property="og:image" content="https://www.hightower-marketing.com/og-cover.jpg">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="Shop TrendLoop Products — Hightower Marketing">
    <meta name="twitter:description" content="Curated TrendLoop products: cozy gifts, night lights, beauty tools and pet essentials. Fast US shipping.">
    <meta name="twitter:image" content="https://www.hightower-marketing.com/og-cover.jpg">
    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "CollectionPage",
      "name": "TrendLoop Products",
      "url": "https://www.hightower-marketing.com/products.html",
      "description": "Curated TrendLoop products: cozy gifts, night lights, beauty tools and pet essentials."
    }}
    </script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ background: #0c0e12; color: #e8e8e3; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; line-height: 1.6; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 0 24px; }}
        nav {{ background: rgba(12,14,18,0.92); backdrop-filter: blur(10px); position: sticky; top: 0; z-index: 100; border-bottom: 1px solid rgba(212,175,55,0.12); }}
        .nav-inner {{ display: flex; justify-content: space-between; align-items: center; padding: 18px 0; }}
        .logo {{ color: #e8e8e3; text-decoration: none; font-size: 1.25rem; font-weight: 700; }}
        .logo span {{ color: #d4af37; }}
        .nav-links {{ list-style: none; display: flex; gap: 28px; }}
        .nav-links a {{ color: rgba(232,232,227,0.75); text-decoration: none; font-size: 0.9rem; transition: color 0.2s; }}
        .nav-links a:hover {{ color: #d4af37; }}
        .nav-cta {{ background: #d4af37; color: #0c0e12; padding: 10px 22px; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 0.9rem; }}
        .hero {{ padding: 90px 0 50px; text-align: center; }}
        .hero h1 {{ font-size: clamp(2rem, 5vw, 3.2rem); font-weight: 800; margin-bottom: 16px; }}
        .hero h1 em {{ color: #d4af37; font-style: normal; }}
        .hero p {{ color: rgba(232,232,227,0.65); max-width: 640px; margin: 0 auto 0; font-size: 1.05rem; }}
        .hero-bar {{ width: 64px; height: 4px; background: #d4af37; margin: 22px auto 0; }}
        .filters {{ display: flex; flex-wrap: wrap; gap: 12px; justify-content: center; margin: 44px 0 40px; }}
        .filter-btn {{ background: transparent; border: 1px solid rgba(212,175,55,0.3); color: rgba(232,232,227,0.8); padding: 9px 20px; border-radius: 999px; cursor: pointer; font-size: 0.9rem; transition: all 0.25s; }}
        .filter-btn:hover, .filter-btn.active {{ background: #d4af37; color: #0c0e12; border-color: #d4af37; font-weight: 600; }}
        .products-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 22px; padding-bottom: 90px; }}
        .product-card {{ background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06); border-radius: 14px; overflow: hidden; transition: transform 0.3s, border-color 0.3s; }}
        .product-card:hover {{ transform: translateY(-4px); border-color: rgba(212,175,55,0.45); }}
        .product-card a {{ text-decoration: none; color: inherit; display: block; }}
        .product-img-wrap {{ aspect-ratio: 1; background: rgba(255,255,255,0.04); overflow: hidden; }}
        .product-img-wrap img {{ width: 100%; height: 100%; object-fit: cover; transition: transform 0.4s; }}
        .product-card:hover .product-img-wrap img {{ transform: scale(1.04); }}
        .product-info {{ padding: 16px 18px 20px; }}
        .product-cat {{ font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.08em; color: #d4af37; font-weight: 600; }}
        .product-title {{ font-size: 0.95rem; font-weight: 600; margin: 8px 0 10px; line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; min-height: 2.7em; }}
        .product-price {{ font-size: 1.15rem; font-weight: 700; color: #e8e8e3; }}
        .product-cta {{ display: inline-block; margin-top: 10px; font-size: 0.82rem; color: rgba(212,175,55,0.9); font-weight: 500; }}
        .store-note {{ text-align: center; color: rgba(232,232,227,0.5); font-size: 0.9rem; padding-bottom: 60px; }}
        .store-note a {{ color: #d4af37; }}
        @media (max-width: 768px) {{
            .nav-links {{ display: none; }}
            .products-grid {{ grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 14px; }}
        }}
    </style>
</head>
<body>
    <nav>
        <div class="container">
            <div class="nav-inner">
                <a href="/" class="logo">Hightower <span>Marketing</span></a>
                <ul class="nav-links">
                    <li><a href="/">Home</a></li>
                    <li><a href="/about">About</a></li>
                    <li><a href="/case-studies">Case Studies</a></li>
                    <li><a href="/ai-video-ads">AI Video Ads</a></li>
                    <li><a href="/pet-portraits">Pet Portraits</a></li>
                    <li><a href="/blog">Blog</a></li>
                    <li><a href="/contact">Contact</a></li>
                </ul>
                <a href="/contact" class="nav-cta">Get Started</a>
            </div>
        </div>
    </nav>

    <section class="hero">
        <div class="container">
            <h1>Shop <em>TrendLoop</em> Products</h1>
            <div class="hero-bar"></div>
            <p style="margin-top:22px">Curated, tested, and shipped fast from our US warehouse. We only list what we'd buy ourselves.</p>
        </div>
    </section>

    <section>
        <div class="container">
            <div class="filters">
                <button class="filter-btn active" data-filter="all">All</button>
{cat_tabs}
            </div>
            <div class="products-grid" id="grid">
{cards}
            </div>
            <p class="store-note">All purchases are processed securely in our <a href="https://shop.hightower-marketing.com" target="_blank" rel="noopener">TrendLoop Shopify store</a> · 30-day returns · US shipping</p>
        </div>
    </section>

    <script>
        document.querySelectorAll('.filter-btn').forEach(btn => {{
            btn.addEventListener('click', () => {{
                document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                const f = btn.dataset.filter;
                document.querySelectorAll('.product-card').forEach(c => {{
                    c.style.display = (f === 'all' || c.dataset.cat === f) ? '' : 'none';
                }});
            }});
        }});
    </script>
    <script src="/hms-motion.js" defer></script>
</body>
</html>'''

open(os.path.join(DIR, 'products.html'), 'w').write(page)
print(f'products.html built: {len(prods)} products, {len(cats)} categories')
print('category counts:', cat_counts)
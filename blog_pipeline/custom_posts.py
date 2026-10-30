#!/usr/bin/env python3
"""custom_posts.py — author + validate + sitemap + deploy our data-product blog posts.

Run: python3 custom_posts.py   (from repo root or blog_pipeline/)
Builds two posts through the standard pipeline, validates gates, regenerates the
sitemap (incl. adding grants-db.html as a static entry), commits and pushes.
"""
from __future__ import annotations
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root

from blog_pipeline.render import PostMeta, InternalLink, render_post, write_post
from blog_pipeline.validate import validate_post, passes_gates
from blog_pipeline.sitemap import update_sitemap
from blog_pipeline.deploy import commit_and_push

POSTS = []

# ---------------- POST 1: grants ----------------
slug1 = 'how-to-filter-grants-gov-for-small-business-grants'
meta1 = PostMeta(
    title='How to Find Federal Grants Your Small Business Is Eligible For',
    description='Grants.gov mixes thousands of opportunities across every applicant type. Here is the filter chain that finds only the ones small businesses can actually win — and how we automated it.',
    category='SB Grants Database',
    canonical_path=f'/blog/{slug1}.html',
    date_published=date.today().isoformat(),
    read_time='7 min read',
)
blocks1 = [
    '<p>Most small-business owners give up on federal grants for the same reason: they open Grants.gov, type "small business," and get thousands of results — most of which their company could never legally win. The search bar is not the bottleneck. Filters are. This post walks through the filter chain we run weekly to surface the handful of opportunities genuinely open to small businesses, and how to become application-ready for them.</p>',
    '<h2>Why raw Grants.gov search fails for small businesses</h2>',
    '<p>Grants.gov aggregates thousands of live opportunities across federal agencies. The default keyword search does not distinguish between applicants: a National Science Foundation program open to universities, a state-matching program open to nonprofits, and a Small Business Innovation Research award open to for-profit companies all sit in the same list. Hours of reading later, the honest conclusion is that most "grants" you found were not for you at all.</p>',
    '<p>The fix is mechanical rather than motivational: filter on the eligibility field, the status field, and the closing-date field in that order. Everything below assumes you have already cleared the paperwork that makes an application possible — more on that at the end.</p>',
    '<h2>The five filters that separate real opportunities from noise</h2>',
    '<h3>1. Eligibility first — one code matters most</h3>',
    '<p>Every opportunity carries eligibility categories. For-profit companies appear under a few codes; the one you want for most small-business federal money is "Small businesses." Filtering by that code first removes the universities, nonprofits, and tribal entities that dominate raw results. For-profit, non-small businesses have their own separate code — worth knowing if you are on the edge of "small" by SBA standards.</p>',
    '<h3>2. Status: posted only</h3>',
    '<p>Opportunities exist as "posted," "forecast," and closed states. Forecast entries describe funding agencies expect to publish later — useful for planning a queue, not for applying today. If you are building an active pipeline, posted-only is the set you can act on now; if you are planning a quarter ahead, forecast entries tell you what is coming.</p>',
    '<h3>3. Cost sharing before you fall in love</h3>',
    '<p>A grant that requires you to match, say, 50% of the award is a very different deal from one that does not. Some programs demand documented cash on hand. Checking the cost-sharing flag before you read the full proposal saves the most expensive kind of wasted afternoon.</p>',
    '<h3>4. The CFDA / program mapping</h3>',
    '<p>Every federal grant runs under a program number (the CFDA number). It tells you what the money actually does — research, training, export, technical assistance — and it is how you group related opportunities when several agencies fund the same program.</p>',
    '<h3>5. Closing dates you can survive</h3>',
    '<p>Realistically, a small company needs two to six weeks to assemble an acceptable federal application. Filtering out anything closing inside that window leaves you opportunities you can actually pursue rather than opportunities you can only watch close.</p>',
    '<h2>The paperwork that makes any of it possible</h2>',
    '<p>Before chasing opportunities, clear the application-readiness chain. Register on <strong>SAM.gov</strong> (free — never pay for registration help) and keep it renewed. Get your EIN letter. Make your entity name, address, and bank statements match each other exactly across the IRS, your state filing, and your bank — mismatches are the quietest way to lose a federal application. Keep recent financial statements and a capability statement on file. Then submit at least 48 hours before the deadline; portal congestion and document errors are the classic way strong applications die.</p>',
    '<p>The honest truth: this readiness chain, once complete, applies to nearly every federal grant you will ever apply for. It is a one-time project with an annual maintenance cost, not a per-grant chore.</p>',
    '<h2>How we automated the whole scan</h2>',
    '<p>We rebuilt this filter chain as a weekly refresh over the official Grants.gov API — the same source data, screened programmatically. The result is our <a href="/grants-db.html">SB Grants Database</a>: 162 live opportunities filtered to small-business eligibility, deadline-sorted, with plain-English eligibility notes, cost-share flags, CFDA program names, a direct link to each official listing, and a separate Readiness Playbook tab covering the paperwork sequence above. A new, larger scan runs every Monday morning; subscribers get the updated sheet, and anyone can join the free weekly digest of what is closing soon.</p>',
    '<p>We also apply the same "build the data product we would use ourselves" approach to real estate: see our <a href="/re-data-refinery.html">scored Columbus and Ohio property data</a> for the investment lane.</p>',
    '<h2>Bottom line</h2>',
    '<p>Federal grants for small businesses are real, but the funnel is guarded by filters, not by luck. Run eligibility first, status second, cost-sharing third; clear your SAM.gov and paper-chain obligations before you write a word; and only chase opportunities with closing dates you can survive. If you would rather let the filters run themselves, that is exactly what the Grants sheet does every Monday — or <a href="/contact.html">reach out</a> and we will point you at the right starting filter.</p>',
]
links1 = [
    InternalLink(href='/grants-db.html', anchor='SB Grants Database', link_type='cta'),
    InternalLink(href='/re-data-refinery.html', anchor='scored Columbus and Ohio property data'),
    InternalLink(href='/blog/how-ai-is-changing-small-business-marketing.html', anchor='how AI is changing small-business marketing'),
    InternalLink(href='/contact.html', anchor='reach out', link_type='internal'),
]
POSTS.append(('service_educational', slug1, meta1, blocks1, links1))

# ---------------- POST 2: RE refinery ----------------
slug2 = 'how-we-score-ohio-properties-for-flips-wholesale-and-rentals'
meta2 = PostMeta(
    title='How We Score Ohio Properties for Flips, Wholesale, and Rentals',
    description='10,000+ Ohio properties, county records, and market data — screened nightly and scored for flips, wholesale profit, and rental yield. Here is exactly what the scores measure.',
    category='RE Data Refinery',
    canonical_path=f'/blog/{slug2}.html',
    date_published=date.today().isoformat(),
    read_time='7 min read',
)
blocks2 = [
    '<p>Every real-estate strategy asks the same question of a property — "what is it worth to ME, on MY exit path?" — from a different angle. A flipper cares about the gap between purchase and renovated value. A wholesaler cares about distressed owners and assignment margins. A landlord cares about yield. We built the RE Data Refinery to answer all three from one dataset, and this post explains what the scores actually measure.</p>',
    '<h2>The pipeline: public records in, scores out</h2>',
    '<p>The raw material is public: county property records, tax delinquency lists, sheriff-sale calendars, and property-market data including automated estimate tracks. Across 18 Ohio cities the pipeline now covers more than 10,000 properties, enriched where available with parcel and neighborhood attributes. The Columbus set refreshes on a daily cadence overnight; the wider Ohio sweep runs on a longer cycle. Nothing in the sheet is scraped from a login wall — it is all public or licensable data, cleaned and joined.</p>',
    '<h2>Flip score</h2>',
    '<p>The flip score asks: how much room is there between what this property costs and what a renovated exit could plausibly bring? It weighs the spread between listing price and neighborhood sold-price benchmarks, the age and size profile that typically correlates with renovation demand, and how comparable properties in the area have moved. High scores signal properties where the math is already plausible — not guarantees, but properties where the underwriting conversation is worth having.</p>',
    '<h2>Wholesale score</h2>',
    '<p>Wholesale is a velocity game: you profit from the spread between a motivated seller and an investor buyer, fast. The wholesale score leans into distress signals — tax-delinquent status, recent sheriff-sale proximity, ownership patterns that correlate with motivated sellers — together with price bands where assignment margins historically breathe. This is the tab most of our early customers filter first.</p>',
    '<h2>Rental yield and market heat</h2>',
    '<p>For buy-and-hold underwriting we compute rental yield percent — expected annual rent over total acquisition cost — plus a market-heat index that tracks how quickly inventory is moving in the surrounding area. Hot markets compress your entry negotiation; cooling markets reward patience. Yield and heat together tell you whether a property is a cash-flow candidate in a neighborhood still worth buying into.</p>',
    '<h2>What the scores are — and are not</h2>',
    '<p>The scores are screening tools, not valuations. A high flip score means the public-data math looks inviting; it does not replace walking the property, checking condition, or pulling title. We say this directly in the sheet because our customers use it to prioritize where they spend their underwriting hours, not as a substitute for them. The same discipline applies to our <a href="/blog/how-to-filter-grants-gov-for-small-business-grants.html">federal-grants screening</a> — the tool surfaces candidates; the operator closes.</p>',
    '<h2>Working with the sheet</h2>',
    '<p>The Refinery ships as a Google Sheet with tabs built per decision: a Dashboard for at-a-glance totals, ranked Flip and Wholesale tables, Rental Yields, a Tax Delinquency Watchlist, Sheriff Sales, and city-specific tabs for markets from Cleveland to Cincinnati. Subscribers get the live link and the refresh cadence; we have run the sheet commercially all quarter and the scoring code evolves with the data.</p>',
    '<p>Curious whether your market or strategy is covered? The <a href="/re-data-refinery.html">RE Data Refinery page</a> lists exactly what each tab contains, and you can always <a href="/contact.html">ask about a city extension</a> — the pipeline is designed to add counties. If you are here for the data-products angle rather than real estate itself, our store page explains the broader product family.</p>',
]
links2 = [
    InternalLink(href='/re-data-refinery.html', anchor='RE Data Refinery page', link_type='cta'),
    InternalLink(href='/blog/how-to-filter-grants-gov-for-small-business-grants.html', anchor='federal-grants screening'),
    InternalLink(href='/blog/seo-columbus-ohio.html', anchor='SEO in Columbus, Ohio'),
    InternalLink(href='/contact.html', anchor='ask about a city extension'),
]
POSTS.append(('service_educational', slug2, meta2, blocks2, links2))


def main():
    written = []
    for post_type, slug, meta, blocks, links in POSTS:
        html = render_post(post_type, slug, meta, blocks, links)
        path = write_post(slug, html)
        pv = validate_post(html, path)
        gates = passes_gates(pv)
        written.append((slug, str(path), pv, gates))
        print(f'POST {slug}: gates={"PASS" if gates else "FAIL"} words={pv.word_count} h2={pv.h2_count} links={pv.internal_link_count}')
        if not gates:
            print(f'  details: {pv}')
    sitemap = update_sitemap()
    # add newly-created static product pages (update_sitemap only preserves existing statics)
    import xml.etree.ElementTree as ET
    ns = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    ET.register_namespace('', ns['ns'])
    sitemap_path = Path('sitemap.xml')
    tree = ET.parse(sitemap_path)
    locs = {l.text for l in tree.getroot().iter('{%s}loc' % ns['ns'])}
    for extra in ('/grants-db.html',):
        url = f'https://www.hightower-marketing.com{extra}'
        if url not in locs:
            u = ET.SubElement(tree.getroot(), 'url')
            ET.SubElement(u, 'loc').text = url
            tree.write(sitemap_path, xml_declaration=True, encoding='utf-8')
            print(f'sitemap: added {extra}')
    print(f'sitemap updated: {sitemap}')
    if all(g for _, _, _, g in written):
        files = [Path(p) for _, p, _, _ in written] + [sitemap]
        ok = commit_and_push(files,
                             message='blog: 2 data-product posts (grants filter + RE scoring) + sitemap incl. grants-db')
        print(f'DEPLOY {"OK" if ok else "FAIL"}')
    else:
        print('DEPLOY SKIPPED (gates failed)')


if __name__ == '__main__':
    main()
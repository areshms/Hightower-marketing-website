# Design Review — hightower-marketing.com (BEFORE), 2026-10-23
Inspector: taste-skill v2 inspect.mjs @ 1440/768/390 — **11 FAIL, 11 WARN**

## Scores (Awwwards-weighted, caps applied)
- Design 6/10 — clean charcoal/gold system, but 11 font sizes, 6 outlined boxes, 4 hairlines, 4 gradient fills; type scale lacks a decisive jump (72/56/48 crowd the top; body 17px grey)
- Usability 7/10 — clear nav, but 3 hero buttons competing for the click (Get Started / Explore AI Video Ads / Contact Us), and hero headline wraps 4 lines @1440, 6-line wrap on phone ("Built by someone…"), text touching screen edge on mobile, contrast 3.2:1 on "Coming soon" + 3.6:1 on "Marketing"
- Creativity 5/10 (capped) — the page could belong to any marketing agency: cover the logo and it's interchangeable; no idea sentence, no live thing. Stock structure: hero → services → about → stats → cta → footer (section order per report.json)
- Content 7/10 — honest copy (real pricing, real Columbus location, "built by someone who actually runs businesses"), but 0 real pictures on the page and no video

**Overall: 6.0/10** (cap: 11 inspector FAILs → max 6.0). Calibration benchmark from taste-skill references/critique.md §2: real Sites of the Day land ~7.5-8.0 overall.

## The measured findings (all from the inspector, not opinion)
FAILs: 4-line hero headline @1440 · eyebrow labels ("What We Do", "About") · 4 micro uppercase labels · 4 gradient fills (hero glow/bg/visual) · 4 hairline rules · 6 outlined 1px boxes · **0 real pictures on the whole page** · 1424px blank stretch · 6-line mobile headline wrap · mobile text at 0px/11px from screen edge · low contrast (3.2-3.6:1)
WARNs: 11 font sizes · grey body text (6.9:1) · no video · unequal margins (168 vs 232px) · pinned "Three ways" text held 4 screens · only 13 moving elements · lopsided 433px half-empty section @768 + separate 464px blank stretch @768 (two findings: lopsided=433px empty beside the About headline; blank-gap=464px at 680px) · 2 identical card rows on mobile

## The three changes that would move the page most
1. **Give it real imagery — the page has ZERO pictures.** This is the single biggest gap. Not stock: real fragments of the actual work (a TrendLoop storefront crop, an eBay listing dashboard, the GovCon/SAM worksheet, a blog-post screenshot) built as honest interface fragments. One dominant image in the hero. The inspector's few-pictures FAIL is the page's whole personality problem.
2. **Kill the template tells: gradients + hairlines + outlined boxes + eyebrows.** Replace the 3 hero gradient glows with a flat charcoal field + one gold accent; remove "What We Do"/"About" eyebrow labels; replace the 6 outlined service/stat boxes with tone-stepped surfaces; delete hairline dividers (space or tone steps instead). This alone takes 5 of the 11 FAILs — but the 6.0 cap only lifts when ALL FAILs clear (6 would remain: headline-lines x3, few-pictures, blank-gap, edge-text), so this change is necessary but not sufficient for the cap.
3. **Fix the type system + the frame.** Collapse 11 sizes to 5 (display/heading/lead/body/small); rewrite the two long headlines to ≤2 lines at every width ("Growth without the guesswork" / "Built by an operator, not an agency"); body copy from grey to full ink; equalize margins (168 vs 232px left/right); close the 1424px blank gap. Mobile: fix the 6-line wrap + edge-touching text.

## Idea (currently missing)
Competitor test FAILS: swap "Hightower" for any agency name and the page still works. The un-mined idea is already in the copy: **an operator's agency** — built by someone who actually runs the businesses (external facts about HMS operations: eBay store, Shopify, trading bot, GovCon pipeline). The page should SHOW the machine: real screenshots of the actual portfolio, live numbers from the real portfolio (external verified facts, proposed as page content — not measurements of the current page: 12 blog posts, 17 eBay listings, $34.99 first sale), the automation stack as the visual language. That's a page no competitor can copy, and it converts the "Coming soon" services into evidence.

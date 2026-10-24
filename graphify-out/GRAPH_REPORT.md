# Graph Report - hms-site  (2026-10-24)

## Corpus Check
- 56 files · ~3,812,174 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 11 file(s) not represented in the graph (top: (none) 2, .zip 2, .toml 2)

## Summary
- 530 nodes · 989 edges · 35 communities (27 shown, 8 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 69 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `75a7976d`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- re
- hms_blog_pipeline.py
- lenis.min.js
- gsap.min.js
- ScrollTrigger.min.js
- 2. Pipeline Architecture
- n
- render.py
- s
- Cc
- package.json
- Tween
- hf
- ae
- L
- hms_seo_fix.py
- ja
- nc
- manifest.json
- ye
- Design Review — hightower-marketing.com (BEFORE), 2026-10-23
- Ra
- db
- Mc
- create-checkout.js
- startMotion
- vercel.json
- Vb
- Wb
- M
- sitemap.py
- Research: What high-converting AI automation agency websites have (2026-10-23)
- fetch

## God Nodes (most connected - your core abstractions)
1. `Cc()` - 18 edges
2. `n()` - 17 edges
3. `main()` - 15 edges
4. `s()` - 13 edges
5. `Tween()` - 13 edges
6. `render_post()` - 11 edges
7. `r()` - 11 edges
8. `ja()` - 10 edges
9. `o()` - 9 edges
10. `m()` - 9 edges

## Surprising Connections (you probably didn't know these)
- `Hk()` --indirect_call--> `c()`  [INFERRED]
  vendor/ScrollTrigger.min.js → aos.js
- `destroy()` --indirect_call--> `l()`  [INFERRED]
  vendor/lenis.min.js → aos.js
- `Jq()` --indirect_call--> `p()`  [INFERRED]
  vendor/ScrollTrigger.min.js → aos.js
- `m()` --indirect_call--> `w()`  [INFERRED]
  aos.js → vendor/gsap.min.js
- `xd()` --indirect_call--> `e()`  [INFERRED]
  vendor/gsap.min.js → aos.js

## Import Cycles
- None detected.

## Communities (35 total, 8 thin omitted)

### Community 0 - "re"
Cohesion: 0.05
Nodes (26): _card_html(), _iso_to_display(), parse_post_summary(), update_blog_cards(), ValidationLimits, commit_and_push(), deploy_netlify(), run_git() (+18 more)

### Community 1 - "hms_blog_pipeline.py"
Cohesion: 0.05
Nodes (32): Handler, amazon_link(), build_post(), git(), gsc_query(), load_config(), main(), stage_distribute() (+24 more)

### Community 2 - "lenis.min.js"
Cohesion: 0.08
Nodes (28): ay(), Eo(), Iw(), advance(), checkOverflow(), cleanUpClassName(), constructor(), destroy() (+20 more)

### Community 3 - "gsap.min.js"
Cohesion: 0.07
Nodes (14): fe(), ga(), Kd(), Ld(), ma(), Md(), na(), Nd() (+6 more)

### Community 4 - "ScrollTrigger.min.js"
Cohesion: 0.07
Nodes (4): hc(), Ka(), La(), rb()

### Community 5 - "2. Pipeline Architecture"
Cohesion: 0.08
Nodes (23): 1. Post Types (Ranked by SEO Impact), 2. Pipeline Architecture, 3. Interlinking Mesh: 28 Products + 7 Services + Posts, 4. What NOT to Auto-Post, 5. Phased Rollout, Anchor-text rules, Blog-card updater, Cron schedule (+15 more)

### Community 6 - "n"
Cohesion: 0.31
Nodes (19): a(), e(), i(), n(), c(), d(), f(), i() (+11 more)

### Community 7 - "render.py"
Cohesion: 0.15
Nodes (13): generate_gsc_answer(), generate_product_guide(), generate_service_educational(), _today(), build_schema_blog_posting(), estimate_read_time(), InternalLink, _link_to_html() (+5 more)

### Community 8 - "s"
Cohesion: 0.17
Nodes (16): ab(), bc(), eb(), fb(), hb(), ib(), mb(), pa() (+8 more)

### Community 9 - "Cc"
Cohesion: 0.17
Nodes (14): o(), Cc(), Jq(), Kq(), Qq(), Ia(), Ja(), Jp() (+6 more)

### Community 10 - "package.json"
Cohesion: 0.14
Nodes (13): author, dependencies, stripe, description, keywords, license, main, name (+5 more)

### Community 11 - "Tween"
Cohesion: 0.21
Nodes (13): _assertThisInitialized(), Fc(), Gc(), hc(), ra(), t(), Timeline(), Tween() (+5 more)

### Community 12 - "hf"
Cohesion: 0.22
Nodes (13): G(), ed(), hf(), kf(), lf(), mf(), N(), nf() (+5 more)

### Community 13 - "ae"
Cohesion: 0.23
Nodes (12): ae(), ce(), ea(), fa(), ia(), je(), ka(), ke() (+4 more)

### Community 14 - "L"
Cohesion: 0.18
Nodes (12): A(), B(), F(), L(), P(), Q(), qc(), r() (+4 more)

### Community 15 - "hms_seo_fix.py"
Cohesion: 0.31
Nodes (4): fix_alt(), fix_description(), inject_head(), main()

### Community 16 - "ja"
Cohesion: 0.28
Nodes (9): Aa(), Animation(), Ba(), ja(), la(), Sa(), Ta(), ub() (+1 more)

### Community 17 - "nc"
Cohesion: 0.22
Nodes (9): Db(), J(), nb(), nc(), pc(), Ua(), ub(), Va() (+1 more)

### Community 18 - "manifest.json"
Cohesion: 0.29
Nodes (6): functions, system, arch, platform, timestamp, version

### Community 19 - "ye"
Cohesion: 0.29
Nodes (7): Pd(), Td(), Ud(), Vd(), wd(), xe(), ye()

### Community 20 - "Design Review — hightower-marketing.com (BEFORE), 2026-10-23"
Cohesion: 0.33
Nodes (5): Design Review — hightower-marketing.com (BEFORE), 2026-10-23, Idea (currently missing), Scores (Awwwards-weighted, caps applied), The measured findings (all from the inspector, not opinion), The three changes that would move the page most

### Community 21 - "Ra"
Cohesion: 0.53
Nodes (6): Eb(), Ma(), Na(), Oa(), Ra(), z()

### Community 22 - "db"
Cohesion: 0.40
Nodes (5): Bb(), Cb(), Context(), db(), gb()

### Community 23 - "Mc"
Cohesion: 0.50
Nodes (4): ha(), Kc(), Mc(), Tb()

### Community 26 - "startMotion"
Cohesion: 0.12
Nodes (9): raf(), raf(), raf(), splitInto(), startMotion(), heroIntro(), raf(), runLoader() (+1 more)

### Community 32 - "sitemap.py"
Cohesion: 0.36
Nodes (3): discover_blog_paths(), _existing_pages(), update_sitemap()

### Community 33 - "Research: What high-converting AI automation agency websites have (2026-10-23)"
Cohesion: 0.33
Nodes (5): Gap list for hms-site v3 (current homepage), Honesty rules (all sources): never invent clients/numbers; label illustrative work; small real, Research: What high-converting AI automation agency websites have (2026-10-23), Sources, The universal section pattern (all sources agree)

## Knowledge Gaps
- **1 isolated node(s):** `stripe`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 189 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `s()` connect `s` to `lenis.min.js`, `gsap.min.js`, `Tween`, `hf`, `ae`?**
  _High betweenness centrality (0.035) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `Cc()` (e.g. with `Gq()` and `Qq()`) actually correct?**
  _`Cc()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `stripe` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `re` be split into smaller, more focused modules?**
  _Cohesion score 0.05427547363031234 - nodes in this community are weakly interconnected._
- **Why does `i()` connect `lenis.min.js` to `nc`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `n()` (e.g. with `c()` and `f()`) actually correct?**
  _`n()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Should `hms_blog_pipeline.py` be split into smaller, more focused modules?**
  _Cohesion score 0.050239234449760764 - nodes in this community are weakly interconnected._
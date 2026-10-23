# Graph Report - hms-site  (2026-10-23)

## Corpus Check
- 49 files · ~3,800,392 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 10 file(s) not represented in the graph (top: (none) 2, .zip 2, .toml 2)

## Summary
- 508 nodes · 929 edges · 34 communities (26 shown, 8 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 72 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `c8354b23`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- render.py
- hms_blog_pipeline.py
- lenis.min.js
- gsap.min.js
- ScrollTrigger.min.js
- 2. Pipeline Architecture
- n
- link_mesh.py
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
- init
- vercel.json
- Vb
- Wb
- M
- g_oauth_capture.py
- Research: What high-converting AI automation agency websites have (2026-10-23)

## God Nodes (most connected - your core abstractions)
1. `Cc()` - 18 edges
2. `n()` - 17 edges
3. `main()` - 15 edges
4. `s()` - 13 edges
5. `Tween()` - 13 edges
6. `render_post()` - 11 edges
7. `r()` - 11 edges
8. `ja()` - 10 edges
9. `init()` - 10 edges
10. `o()` - 9 edges

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

## Communities (34 total, 8 thin omitted)

### Community 0 - "render.py"
Cohesion: 0.06
Nodes (30): _card_html(), _iso_to_display(), parse_post_summary(), update_blog_cards(), ValidationLimits, generate_gsc_answer(), generate_product_guide(), generate_service_educational() (+22 more)

### Community 1 - "hms_blog_pipeline.py"
Cohesion: 0.06
Nodes (24): commit_and_push(), deploy_netlify(), run_git(), load_gsc_cache(), pick_query_opportunities(), refresh_gsc_cache(), base_foot(), base_head() (+16 more)

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

### Community 7 - "link_mesh.py"
Cohesion: 0.24
Nodes (6): anchor_audit(), build_post_targets(), build_product_targets(), build_service_targets(), LinkTarget, select_links()

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

### Community 26 - "init"
Cohesion: 0.09
Nodes (8): init(), fmt(), runCountUp(), init(), fmt(), runCountUp(), raf(), ScrollTrigger()

### Community 33 - "Research: What high-converting AI automation agency websites have (2026-10-23)"
Cohesion: 0.33
Nodes (5): Gap list for hms-site v3 (current homepage), Honesty rules (all sources): never invent clients/numbers; label illustrative work; small real, Research: What high-converting AI automation agency websites have (2026-10-23), Sources, The universal section pattern (all sources agree)

## Knowledge Gaps
- **1 isolated node(s):** `stripe`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 186 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ScrollTrigger()` connect `init` to `ScrollTrigger.min.js`?**
  _High betweenness centrality (0.045) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `Cc()` (e.g. with `Gq()` and `Qq()`) actually correct?**
  _`Cc()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `stripe` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `render.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06105834464043419 - nodes in this community are weakly interconnected._
- **Why does `s()` connect `s` to `lenis.min.js`, `gsap.min.js`, `Tween`, `hf`, `ae`?**
  _High betweenness centrality (0.040) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `n()` (e.g. with `c()` and `f()`) actually correct?**
  _`n()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Should `hms_blog_pipeline.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05803571428571429 - nodes in this community are weakly interconnected._
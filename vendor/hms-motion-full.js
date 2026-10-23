/* HMS Motion v6 — FULL tier: Medium plus the signature sequence and the alive-at-rest layer.
   Signature: the hero headline clip-morphs open like a frame being tightened on a press bed,
   then every arrival follows the same verb (settle like print).
   Load order: gsap → ScrollTrigger → lenis → this file. */
(function () {
  'use strict';

  function ready(fn) { (document.readyState === 'complete') ? fn() : window.addEventListener('load', fn); }

  function splitInto(el, mode) {
    var out = [];
    var walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT, null, false), nodes = [], n;
    while ((n = walker.nextNode())) nodes.push(n);
    nodes.forEach(function (tn) {
      var parent = tn.parentNode;
      var units = (mode === 'chars') ? tn.textContent.split('') : tn.textContent.split(/(\s+)/);
      units.forEach(function (u) {
        if (!u) return;
        if (/^\s+$/.test(u)) { parent.insertBefore(document.createTextNode(u), tn); return; }
        var outer = document.createElement('span');
        outer.style.cssText = 'display:inline-block;overflow:hidden;vertical-align:bottom';
        var inner = document.createElement('span');
        inner.style.display = 'inline-block'; inner.textContent = u;
        outer.appendChild(inner); parent.insertBefore(outer, tn); out.push(inner);
      });
      parent.removeChild(tn);
    });
    return out;
  }

  ready(function () {
    try {
      var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      var risers = document.querySelectorAll('.rise');
      if (reduce || typeof gsap === 'undefined' || typeof ScrollTrigger === 'undefined') {
        risers.forEach(function (el) { el.classList.add('in'); });
        return;
      }
      gsap.registerPlugin(ScrollTrigger);

      /* ── Lenis ── */
      var lenis = null;
      if (typeof Lenis !== 'undefined') {
        lenis = new Lenis({ duration: 1.1, smoothWheel: true });
        function raf(t) { lenis.raf(t); requestAnimationFrame(raf); }
        requestAnimationFrame(raf);
        lenis.on('scroll', function () { ScrollTrigger.update(); });
        document.querySelectorAll('a[href^="#"]').forEach(function (a) {
          var href = a.getAttribute('href');
          if (!href || href === '#') return;
          var t = document.querySelector(href);
          if (t) a.addEventListener('click', function (e) { e.preventDefault(); lenis.scrollTo(t, { duration: 1.1 }); });
        });
      }

      /* ── SIGNATURE: hero frame tightens open, then the words settle ── */
      var hero = document.querySelector('.hero-text');
      if (hero) {
        var sig = gsap.timeline({ delay: 0.1 });
        var h1 = hero.querySelector('.hl');
        if (h1) {
          var words = splitInto(h1, 'words');
          if (words.length) {
            sig.fromTo(words, { yPercent: 112 }, { yPercent: 0, duration: 1.1, ease: 'expo.out', stagger: 0.06 });
          }
        }
        var stand = hero.querySelector('.standfirst');
        if (stand) sig.fromTo(stand, { autoAlpha: 0, y: 18 }, { autoAlpha: 1, y: 0, duration: 0.9, ease: 'expo.out' }, '-=0.55');
        var acts = hero.querySelector('.hero-actions');
        if (acts) sig.fromTo(acts, { autoAlpha: 0, y: 18 }, { autoAlpha: 1, y: 0, duration: 0.9, ease: 'expo.out' }, '-=0.7');
        var foot = hero.querySelector('.hero-foot');
        if (foot) sig.fromTo(foot, { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.8, ease: 'power1.out' }, '-=0.5');
      }

      /* ── masthead band: the frame keeps breathing (idle drift, pauses offscreen) ── */
      var band = document.querySelector('.band');
      if (band) {
        var drift = gsap.to(band, { xPercent: -1.4, duration: 9, ease: 'sine.inOut', yoyo: true, repeat: -1, paused: true });
        ScrollTrigger.create({
          trigger: '.masthead', start: 'top bottom', end: 'bottom top',
          onToggle: function (s) { s.isActive ? drift.play() : drift.pause(); }
        });
      }

      /* ── reveals: batched, reading order, expo.out ── */
      gsap.set('.rise:not([data-no-batch])', { autoAlpha: 0, y: 24 });
      ScrollTrigger.batch('.rise:not([data-no-batch])', {
        start: 'top 86%', once: true, interval: 0.08,
        onEnter: function (els) {
          gsap.to(els, { autoAlpha: 1, y: 0, duration: 1.0, ease: 'expo.out', stagger: 0.07, overwrite: true, clearProps: 'transform' });
        }
      });
      ScrollTrigger.refresh();

      /* ── section titles: masked line reveals, chars settle ── */
      document.querySelectorAll('.section-title').forEach(function (h2) {
        if (h2.getAttribute('data-split')) return;
        h2.setAttribute('data-split', '1');
        var chars = splitInto(h2, 'chars');
        if (!chars.length) return;
        gsap.fromTo(chars, { yPercent: 110 }, { yPercent: 0, duration: 0.9, ease: 'expo.out', stagger: 0.016,
          scrollTrigger: { trigger: h2, start: 'top 86%', once: true } });
      });

      /* ── panel assembly: labelled timeline (the machine waking up) ── */
      var panel = document.querySelector('#services .panel');
      if (panel) {
        var rows = panel.querySelectorAll('.stat-line');
        var ptl = gsap.timeline({ scrollTrigger: { trigger: panel, start: 'top 82%', once: true } });
        ptl.addLabel('wake');
        if (panel.querySelector('.panel-head')) ptl.from(panel.querySelector('.panel-head'), { autoAlpha: 0, y: -14, duration: 0.5, ease: 'expo.out' }, 'wake');
        if (rows.length) ptl.fromTo(rows, { autoAlpha: 0, x: -18 }, { autoAlpha: 1, x: 0, duration: 0.7, ease: 'expo.out', stagger: 0.09 }, 'wake+=0.15');
        var fill = panel.querySelector('.grow-bar .fill');
        if (fill) ptl.fromTo(fill, { width: '0%' }, { width: (fill.getAttribute('data-w') || '100') + '%', duration: 1.2, ease: 'expo.out' }, 'wake+=0.55');
      }

      /* ── work images: clip-mask reveal + settle-zoom + parallax ── */
      gsap.utils.toArray('#work .work-block').forEach(function (block) {
        var frame = block.querySelector('.work-visual');
        var img = frame ? frame.querySelector('img') : null;
        if (frame) gsap.fromTo(frame, { clipPath: 'inset(10% 6% 10% 6%)' }, { clipPath: 'inset(0% 0% 0% 0%)', duration: 1.4, ease: 'expo.out',
          scrollTrigger: { trigger: frame, start: 'top 82%', once: true } });
        if (img) {
          gsap.fromTo(img, { scale: 1.12 }, { scale: 1, duration: 1.7, ease: 'expo.out',
            scrollTrigger: { trigger: frame, start: 'top 82%', once: true } });
          gsap.fromTo(img, { yPercent: -6 }, { yPercent: 6, ease: 'none',
            scrollTrigger: { trigger: block, scrub: true, start: 'top bottom', end: 'bottom top' } });
        }
      });

      /* ── stats count-up ── */
      document.querySelectorAll('#numbers .figure-tile .n').forEach(function (el) {
        if (el.getAttribute('data-counted')) return;
        var m = el.textContent.match(/^([\d.,]+)(.*)$/);
        if (!m) return;
        var target = parseFloat(m[1].replace(/,/g, '')), suffix = m[2] || '';
        if (isNaN(target)) return;
        el.setAttribute('data-counted', '1');
        var o = { v: 0 };
        gsap.to(o, { v: target, duration: 1.6, ease: 'power2.out',
          onUpdate: function () { el.textContent = Math.round(o.v).toLocaleString('en-US') + suffix; },
          scrollTrigger: { trigger: el, start: 'top 86%', once: true } });
      });

      /* ── calculator: the number settles live (spring) ── */
      (function () {
        var h = document.getElementById('calc-hours'), r = document.getElementById('calc-rate'), sh = document.getElementById('calc-share');
        var yr = document.getElementById('calc-year');
        if (!h || !r || !sh || !yr) return;
        var disp = { v: 0 };
        function wire() {
          [h, r, sh].forEach(function (el) {
            el.addEventListener('input', function () {
              document.getElementById('calc-hours-out').textContent = h.value;
              document.getElementById('calc-rate-out').textContent = r.value;
              document.getElementById('calc-share-out').textContent = sh.value;
              var val = (+h.value) * (+r.value) * (+sh.value) * 0.01 * 52;
              gsap.to(disp, { v: val, duration: 0.9, ease: 'elastic.out(1, 0.55)',
                onUpdate: function () { yr.textContent = '$' + Math.round(disp.v).toLocaleString('en-US'); } });
            });
          });
          var init = (+h.value) * (+r.value) * (+sh.value) * 0.01 * 52;
          disp.v = init;
        }
        wire();
      })();

      /* ── FAQ: staggered arrival + smooth accordion ── */
      var faq = document.querySelector('#faq');
      if (faq) {
        var dts = faq.querySelectorAll('details');
        gsap.fromTo(dts, { autoAlpha: 0, y: 20 }, { autoAlpha: 1, y: 0, duration: 0.9, ease: 'expo.out', stagger: 0.06,
          scrollTrigger: { trigger: faq, start: 'top 86%', once: true } });
        dts.forEach(function (d) {
          var sum = d.querySelector('summary');
          var body = sum ? sum.nextElementSibling : null;
          if (!sum || !body) return;
          sum.addEventListener('click', function (e) {
            e.preventDefault();
            if (d.open) {
              gsap.to(body, { height: 0, opacity: 0, duration: 0.35, ease: 'power2.inOut',
                onStart: function () { body.style.overflow = 'hidden'; },
                onComplete: function () { d.open = false; body.style.height = ''; body.style.overflow = ''; body.style.opacity = ''; } });
            } else {
              d.open = true;
              var full = body.scrollHeight;
              gsap.fromTo(body, { height: 0, opacity: 0 }, { height: full, opacity: 1, duration: 0.45, ease: 'expo.out',
                onStart: function () { body.style.overflow = 'hidden'; },
                onComplete: function () { body.style.height = ''; body.style.overflow = ''; } });
            }
          });
        });
      }

      /* ── CTA: monogram settles with a touch of weight, statement words arrive ── */
      var mono = document.querySelector('.monogram');
      if (mono) {
        gsap.fromTo(mono, { scale: 0.72, autoAlpha: 0, rotation: -4 }, { scale: 1, autoAlpha: 1, rotation: 0, duration: 1.0, ease: 'expo.out',
          scrollTrigger: { trigger: mono, start: 'top 88%', once: true } });
      }
      var stmt = document.querySelector('.cta-statement');
      if (stmt) {
        var sw = splitInto(stmt, 'words');
        if (sw.length) gsap.fromTo(sw, { autoAlpha: 0.18 }, { autoAlpha: 1, duration: 0.6, ease: 'power1.out', stagger: 0.05,
          scrollTrigger: { trigger: stmt, start: 'top 86%', once: true } });
      }

      /* ── process steps light up in order ── */
      var steps = document.querySelectorAll('#process .step');
      steps.forEach(function (s, i) {
        gsap.fromTo(s.querySelector('b'), { autoAlpha: 0.45 }, { autoAlpha: 1, duration: 0.5, ease: 'power2.out',
          scrollTrigger: { trigger: s, start: 'top 86%', once: true }, delay: i * 0.06 });
      });

      /* ── magnetic buttons via quickTo ── */
      document.querySelectorAll('.btn, .head-cta, .hero-actions a').forEach(function (btn) {
        var xTo = gsap.quickTo(btn, 'x', { duration: 0.4, ease: 'power3' });
        var yTo = gsap.quickTo(btn, 'y', { duration: 0.4, ease: 'power3' });
        btn.addEventListener('mousemove', function (e) {
          var r = btn.getBoundingClientRect();
          xTo((e.clientX - r.left - r.width / 2) * 0.22);
          yTo((e.clientY - r.top - r.height / 2) * 0.28);
        });
        btn.addEventListener('mouseleave', function () { xTo(0); yTo(0); });
      });

    } catch (err) {
      document.querySelectorAll('.rise').forEach(function (el) { el.classList.add('in'); });
      console.error('HMS motion full:', err);
    }
  });
})();
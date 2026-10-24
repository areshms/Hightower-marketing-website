/* HMS Motion — SIGNATURE tier (variant D): loader counter → curtain handoff → press open.
   The awwwards-skill pattern: one designed open, continuous motion between states,
   html.motion-gated so no-JS and reduced-motion see everything immediately. */
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

  function startMotion() {
    try {
      var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      var risers = document.querySelectorAll('.rise');
      if (reduce || typeof gsap === 'undefined' || typeof ScrollTrigger === 'undefined') {
        risers.forEach(function (el) { el.classList.add('in'); el.style.opacity = ''; });
        document.documentElement.classList.add('is-loaded');
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
        lenis.stop(); /* the loader owns the first moment */
        document.querySelectorAll('a[href^="#"]').forEach(function (a) {
          var href = a.getAttribute('href');
          if (!href || href === '#') return;
          var t = document.querySelector(href);
          if (t) a.addEventListener('click', function (e) { e.preventDefault(); lenis.scrollTo(t, { duration: 1.1 }); });
        });
      }

      /* ── SCROLL-DRIVEN layer (reveals, titles, panel, work, stats, faq, cta, magnetic) ── */
      gsap.set('.rise:not([data-no-batch])', { autoAlpha: 0, y: 24 });
      ScrollTrigger.batch('.rise:not([data-no-batch])', {
        start: 'top 86%', once: true, interval: 0.08,
        onEnter: function (els) {
          gsap.to(els, { autoAlpha: 1, y: 0, duration: 1.0, ease: 'expo.out', stagger: 0.07, overwrite: true, clearProps: 'transform' });
        }
      });

      document.querySelectorAll('.section-title').forEach(function (h2) {
        if (h2.getAttribute('data-split')) return;
        h2.setAttribute('data-split', '1');
        var chars = splitInto(h2, 'chars');
        if (!chars.length) return;
        gsap.fromTo(chars, { yPercent: 110 }, { yPercent: 0, duration: 0.9, ease: 'expo.out', stagger: 0.016,
          scrollTrigger: { trigger: h2, start: 'top 86%', once: true } });
      });

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

      /* calculator spring */
      (function () {
        var h = document.getElementById('calc-hours'), r = document.getElementById('calc-rate'), sh = document.getElementById('calc-share');
        var yr = document.getElementById('calc-year');
        if (!h || !r || !sh || !yr) return;
        var disp = { v: (+h.value) * (+r.value) * (+sh.value) * 0.01 * 52 };
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
      })();

      /* idle band drift, pauses offscreen */
      var band = document.querySelector('.band');
      if (band) {
        var drift = gsap.to(band, { xPercent: -1.4, duration: 9, ease: 'sine.inOut', yoyo: true, repeat: -1, paused: true });
        ScrollTrigger.create({
          trigger: '.masthead', start: 'top bottom', end: 'bottom top',
          onToggle: function (s) { s.isActive ? drift.play() : drift.pause(); }
        });
      }

      /* ── THE SIGNATURE: loader → handoff → press open ── */
      var loader = document.getElementById('loader');
      var count = loader ? loader.querySelector('[data-loader-count]') : null;
      var bar = loader ? loader.querySelector('.loader-fill') : null;

      function heroIntro() {
        /* the handoff: headline words settle as the curtain clears */
        var h1 = document.querySelector('.hl');
        var words = h1 ? splitInto(h1, 'words') : [];
        var tl = gsap.timeline();
        if (words.length) tl.fromTo(words, { yPercent: 112 }, { yPercent: 0, duration: 1.1, ease: 'expo.out', stagger: 0.06 });
        var stand = document.querySelector('.standfirst');
        if (stand) tl.fromTo(stand, { autoAlpha: 0, y: 18 }, { autoAlpha: 1, y: 0, duration: 0.9, ease: 'expo.out' }, '-=0.55');
        var acts = document.querySelector('.hero-actions');
        if (acts) tl.fromTo(acts, { autoAlpha: 0, y: 18 }, { autoAlpha: 1, y: 0, duration: 0.9, ease: 'expo.out' }, '-=0.7');
        var foot = document.querySelector('.hero-foot');
        if (foot) tl.fromTo(foot, { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.8, ease: 'power1.out' }, '-=0.5');
        return tl;
      }

      function runLoader() {
        var MIN = 1.1, MAX = 2.6;
        var t0 = performance.now();
        var imgs = [].slice.call(document.images);
        var pending = [document.fonts ? document.fonts.ready : Promise.resolve()].concat(
          imgs.map(function (im) { return im.complete ? Promise.resolve() : (im.decode ? im.decode().catch(function(){}) : Promise.resolve()); })
        );
        var shown = { p: 0 };
        var real = Promise.all(pending).then(function () { return 1; });
        var cap = new Promise(function (res) { setTimeout(res, MAX * 1000); });
        var floor = new Promise(function (res) { setTimeout(res, MIN * 1000); });

        function tick(p) {
          if (count) count.textContent = String(Math.round(p * 100)).padStart(2, '0');
          if (bar) bar.style.width = (p * 100) + '%';
        }
        var clock = gsap.to(shown, { p: 1, duration: MAX, ease: 'power1.inOut', onUpdate: function () { tick(Math.min(shown.p, 0.92)); } });

        Promise.race([real, cap]).then(function () {
          floor.then(function () {
            gsap.to(shown, { p: 1, duration: 0.35, ease: 'power2.out',
              onUpdate: function () { tick(shown.p); },
              onComplete: function () {
                clock.kill();
                var exit = gsap.timeline({
                  onComplete: function () {
                    document.documentElement.classList.add('is-loaded');
                    if (lenis) lenis.start();
                    ScrollTrigger.refresh();
                  }
                });
                /* the loader panel wipes up; hero settles in underneath — no hard cut */
                exit.to(loader, { yPercent: -100, duration: 1.0, ease: 'expo.inOut' })
                    .add(heroIntro(), '-=0.35');
              }
            });
          });
        });
      }

      if (loader) runLoader();
      else { document.documentElement.classList.add('is-loaded'); if (lenis) lenis.start(); }

      ScrollTrigger.refresh();
    } catch (err) {
      document.querySelectorAll('.rise').forEach(function (el) { el.classList.add('in'); el.style.opacity = ''; });
      document.documentElement.classList.add('is-loaded');
      var l = document.getElementById('loader'); if (l) l.style.display = 'none';
      console.error('HMS signature motion:', err);
    }
  }

  /* The loader needs to exist on FIRST paint; motion init after load. */
  ready(startMotion);
})();
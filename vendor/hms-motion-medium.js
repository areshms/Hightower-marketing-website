/* HMS Motion v6 — MEDIUM tier, rebuilt on the official GSAP skill + Awwwards motion references.
   Motion verb: "settle like print" — everything arrives with a confident deceleration (expo.out),
   images reveal through clip masks, hovers answer in roll/fill. Restraint: no pin choreography
   beyond the process steps, no spectacle. Load order: gsap → ScrollTrigger → lenis → this file. */
(function () {
  'use strict';

  function ready(fn) { (document.readyState === 'complete') ? fn() : window.addEventListener('load', fn); }

  ready(function () {
    try {
      var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      var risers = document.querySelectorAll('.rise');
      if (reduce || typeof gsap === 'undefined' || typeof ScrollTrigger === 'undefined') {
        risers.forEach(function (el) { el.classList.add('in'); });
        return;
      }
      gsap.registerPlugin(ScrollTrigger);

      /* ── Lenis, wired once ── */
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

      /* ── reveal engine: batch per section, in reading order, expo.out arrivals ── */
      ScrollTrigger.batch('.rise', {
        start: 'top 86%',
        once: true,
        interval: 0.08,
        onEnter: function (els) {
          gsap.to(els, { autoAlpha: 1, y: 0, duration: 1.0, ease: 'expo.out', stagger: 0.07, overwrite: true, clearProps: 'transform' });
        }
      });
      /* elements above the fold reveal immediately */
      gsap.set('.rise', { autoAlpha: 0, y: 24 });
      ScrollTrigger.refresh();

      /* hero headline: the CSS masked reveal owns it (no JS fight) */

      /* ── work images: clip-mask reveal (the print-world arrival) ── */
      gsap.utils.toArray('#work .work-visual').forEach(function (frame) {
        var img = frame.querySelector('img');
        if (!img) return;
        gsap.fromTo(frame, { clipPath: 'inset(12% 8% 12% 8%)' }, {
          clipPath: 'inset(0% 0% 0% 0%)', duration: 1.4, ease: 'expo.out',
          scrollTrigger: { trigger: frame, start: 'top 82%', once: true }
        });
        if (img) gsap.fromTo(img, { scale: 1.12 }, { scale: 1, duration: 1.6, ease: 'expo.out',
          scrollTrigger: { trigger: frame, start: 'top 82%', once: true } });
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

      /* ── process: steps light up in order (no pin — the batch reveal carries it) ── */
      var steps = document.querySelectorAll('#process .step');
      if (steps.length) {
        steps.forEach(function (s, i) {
          gsap.fromTo(s.querySelector('b'), { autoAlpha: 0.45 }, { autoAlpha: 1, duration: 0.5, ease: 'power2.out',
            scrollTrigger: { trigger: s, start: 'top 86%', once: true }, delay: i * 0.06 });
        });
      }

      /* ── magnetic buttons via quickTo (one reused tween per axis) ── */
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
      console.error('HMS motion medium:', err);
    }
  });
})();
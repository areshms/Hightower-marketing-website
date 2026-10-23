/* HMS Motion — MEDIUM tier (Lenis + GSAP: staggered reveals, process pin, parallax, count-up, magnetic buttons)
   Load order: gsap.min.js → ScrollTrigger.min.js → lenis.min.js → this file */
(function () {
  'use strict';
  function whenReady(fn) { (document.readyState !== 'loading') ? fn() : document.addEventListener('DOMContentLoaded', fn); }
  function init() {
    try {
      var prefersReduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      var risers = document.querySelectorAll('.rise');
      if (prefersReduced) { risers.forEach(function (el) { el.classList.add('in'); }); return; }
      if (typeof gsap === 'undefined' || typeof ScrollTrigger === 'undefined') {
        risers.forEach(function (el) { el.classList.add('in'); }); /* never leave the page hidden */
        return;
      }
      gsap.registerPlugin(ScrollTrigger);

      /* Lenis smooth scroll, wired to ScrollTrigger's ticker */
      var lenis = null;
      if (typeof Lenis !== 'undefined') {
        lenis = new Lenis({ duration: 1.1, smoothWheel: true });
        function lenisRaf(t) { lenis.raf(t); requestAnimationFrame(lenisRaf); }
        requestAnimationFrame(lenisRaf);
        lenis.on('scroll', function () { ScrollTrigger.update(); });
        /* keep anchor jumps working through the smooth scroller */
        document.querySelectorAll('a[href^="#"]').forEach(function (a) {
          var href = a.getAttribute('href');
          if (!href || href === '#') return;
          var target = document.querySelector(href);
          if (!target) return;
          a.addEventListener('click', function (e) {
            e.preventDefault();
            lenis.scrollTo(target, { duration: 1.1 });
          });
        });
      }

      function fmt(v, d) { return new Intl.NumberFormat('en-US', { minimumFractionDigits: d, maximumFractionDigits: d }).format(v); }
      function runCountUp(el) {
        if (el.getAttribute('data-counted') === 'true') return;
        var raw = el.textContent, m = raw.match(/^(.*?)([\d.,]+)(.*)$/);
        var prefix = '', suffix = '', target = 0, decimals = 0;
        if (m) { prefix = m[1]; suffix = m[3]; target = parseFloat(m[2].replace(/,/g, '')); decimals = m[2].split('.')[1] ? m[2].split('.')[1].length : 0; }
        if (isNaN(target)) return;
        el.setAttribute('data-counted', 'true');
        var obj = { val: 0 };
        gsap.to(obj, {
          val: target, duration: 1.6, ease: 'power2.out',
          onUpdate: function () { el.textContent = prefix + fmt(obj.val, decimals) + suffix; },
          scrollTrigger: { trigger: el, start: 'top 85%', once: true }
        });
      }

      /* staggered section reveals — replaces the uniform IO reveal */
      gsap.utils.toArray('section').forEach(function (section) {
        var els = section.querySelectorAll('.rise');
        if (!els.length) return;
        gsap.from(els, {
          y: 28, autoAlpha: 0, duration: 0.75, ease: 'power2.out', stagger: 0.09,
          scrollTrigger: { trigger: section, start: 'top 82%', once: true }
        });
      });

      /* process: pin + step advance — desktop only (pin feels broken on phones) */
      var mm = gsap.matchMedia();
      mm.add('(min-width: 769px)', function () {
        var section = document.querySelector('#process');
        if (!section) return;
        var steps = section.querySelectorAll('.process-grid .step');
        if (!steps.length) return;
        function setActive(p) {
          var idx = Math.min(steps.length - 1, Math.floor(p * steps.length));
          steps.forEach(function (s, i) { s.classList.toggle('is-active', i <= idx); });
        }
        ScrollTrigger.create({
          trigger: section, start: 'top top', end: '+=180%', pin: true, scrub: 0.5,
          onUpdate: function (self) { setActive(self.progress); },
          onLeaveBack: function () { setActive(0); }
        });
        setActive(0);
      });

      /* work visuals: slow parallax + grayscale-to-color on enter */
      gsap.utils.toArray('#work .work-block').forEach(function (block) {
        var img = block.querySelector('.work-visual img');
        if (!img) return;
        gsap.fromTo(img, { yPercent: -8 }, { yPercent: 8, ease: 'none',
          scrollTrigger: { trigger: block, scrub: true, start: 'top bottom', end: 'bottom top' } });
        gsap.fromTo(img, { filter: 'grayscale(100%)' }, { filter: 'grayscale(0%)', duration: 1.2, ease: 'power2.out',
          scrollTrigger: { trigger: block, start: 'top 80%', once: true } });
      });

      /* stats count-up (our real tiles) */
      document.querySelectorAll('#numbers .figure-tile .n').forEach(runCountUp);

      /* magnetic buttons */
      document.querySelectorAll('.btn, .head-cta, .hero-actions a').forEach(function (btn) {
        function onMove(e) {
          var r = btn.getBoundingClientRect();
          gsap.to(btn, { x: (e.clientX - r.left - r.width / 2) * 0.25, y: (e.clientY - r.top - r.height / 2) * 0.3, duration: 0.3, ease: 'power2.out', overwrite: 'auto' });
        }
        function onLeave() { gsap.to(btn, { x: 0, y: 0, duration: 0.55, ease: 'elastic.out(1, 0.4)', overwrite: 'auto' }); }
        btn.addEventListener('mousemove', onMove);
        btn.addEventListener('mouseleave', onLeave);
        btn.addEventListener('blur', onLeave);
      });

      var rt; window.addEventListener('resize', function () { clearTimeout(rt); rt = setTimeout(function () { ScrollTrigger.refresh(); }, 200); });
    } catch (err) {
      document.querySelectorAll('.rise').forEach(function (el) { el.classList.add('in'); });
      console.error('HMS Motion Medium error:', err);
    }
  }
  /* Init AFTER full load (images settle layout) so ScrollTrigger never needs a
   reverting refresh — reverting once-triggers would leave the page invisible. */
if (document.readyState === 'complete') init();
else window.addEventListener('load', init);
})();
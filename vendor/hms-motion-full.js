/* HMS Motion — FULL tier (everything in Medium PLUS: hero word cascade, panel assembly,
   live-tweening calculator, masthead drift, FAQ accordion motion, letter-level titles, CTA moments)
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
        risers.forEach(function (el) { el.classList.add('in'); }); /* no-GSAP safety: page stays visible */
        return;
      }
      gsap.registerPlugin(ScrollTrigger);

      /* ── Lenis smooth scroll ── */
      var lenis = null;
      if (typeof Lenis !== 'undefined') {
        lenis = new Lenis({ duration: 1.1, smoothWheel: true });
        function lenisRaf(t) { lenis.raf(t); requestAnimationFrame(lenisRaf); }
        requestAnimationFrame(lenisRaf);
        lenis.on('scroll', function () { ScrollTrigger.update(); });
        document.querySelectorAll('a[href^="#"]').forEach(function (a) {
          var href = a.getAttribute('href');
          if (!href || href === '#') return;
          var target = document.querySelector(href);
          if (!target) return;
          a.addEventListener('click', function (e) { e.preventDefault(); lenis.scrollTo(target, { duration: 1.1 }); });
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

      /* ── text splitting helpers ── */
      function splitWords(el) {
        var words = [];
        var walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT, null, false), nodes = [], n;
        while ((n = walker.nextNode())) nodes.push(n);
        nodes.forEach(function (tn) {
          var parent = tn.parentNode, parts = tn.textContent.split(/(\s+)/);
          parts.forEach(function (part) {
            if (!part) return;
            if (/^\s+$/.test(part)) { parent.insertBefore(document.createTextNode(part), tn); return; }
            var outer = document.createElement('span');
            outer.style.display = 'inline-block'; outer.style.overflow = 'hidden'; outer.style.verticalAlign = 'bottom';
            var inner = document.createElement('span');
            inner.style.display = 'inline-block'; inner.textContent = part;
            outer.appendChild(inner); parent.insertBefore(outer, tn); words.push(inner);
          });
          parent.removeChild(tn);
        });
        return words;
      }
      function splitChars(el) {
        var walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT, null, false), nodes = [], n;
        while ((n = walker.nextNode())) nodes.push(n);
        nodes.forEach(function (tn) {
          var parent = tn.parentNode, frag = document.createDocumentFragment(), text = tn.textContent;
          for (var i = 0; i < text.length; i++) {
            var ch = text[i];
            if (ch === ' ') { frag.appendChild(document.createTextNode(' ')); continue; }
            var outer = document.createElement('span');
            outer.style.display = 'inline-block'; outer.style.overflow = 'hidden';
            var inner = document.createElement('span');
            inner.style.display = 'inline-block'; inner.textContent = ch;
            outer.appendChild(inner); frag.appendChild(outer);
          }
          parent.replaceChild(frag, tn);
        });
        return el.querySelectorAll('span > span');
      }

      /* ── 1. HERO: word cascade + delayed standfirst/actions ── */
      var hero = document.querySelector('.hero-text');
      if (hero) {
        var h1 = hero.querySelector('.hl');
        var tl = gsap.timeline({ delay: 0.15, defaults: { ease: 'power4.out' } });
        if (h1 && !h1.querySelector('span > span')) {
          var words = splitWords(h1);
          if (words.length) tl.fromTo(words,
            { yPercent: 110 }, { yPercent: 0, duration: 0.9, stagger: 0.07 });
        }
        var stand = hero.querySelector('.standfirst');
        if (stand) tl.fromTo(stand, { autoAlpha: 0, y: 24 }, { autoAlpha: 1, y: 0, duration: 0.8 }, '-=0.5');
        var acts = hero.querySelector('.hero-actions');
        if (acts) tl.fromTo(acts, { autoAlpha: 0, y: 24 }, { autoAlpha: 1, y: 0, duration: 0.8 }, '-=0.6');
      }

      /* ── 2. PANEL assembly: stat lines wipe in, grow-bar draws, numbers count ── */
      var panel = document.querySelector('#services .panel');
      if (panel) {
        var rows = panel.querySelectorAll('.stat-line');
        var ptl = gsap.timeline({ scrollTrigger: { trigger: panel, start: 'top 80%', once: true } });
        if (rows.length) ptl.fromTo(rows, { x: -24, autoAlpha: 0 }, { x: 0, autoAlpha: 1, duration: 0.6, stagger: 0.09, ease: 'power2.out' }, 0);
        var head = panel.querySelector('.panel-head');
        if (head) ptl.from(head, { autoAlpha: 0, y: -12, duration: 0.5, ease: 'power2.out' }, 0);
        ptl.call(function () {
          var fill = panel.querySelector('.grow-bar .fill');
          if (fill) gsap.fromTo(fill, { width: '0%' }, { width: (fill.getAttribute('data-w') || '100') + '%', duration: 1.2, ease: 'power2.out' });
        }, null, 0.5);
      }

      /* ── 3. CALCULATOR: result number springs live as sliders move ── */
      var calcSection = document.querySelector('#calculator');
      if (calcSection) {
        var sliders = calcSection.querySelectorAll('input[type=range]');
        var yearOut = document.getElementById('calc-year');
        if (sliders.length === 3 && yearOut) {
          var disp = { v: parseFloat((yearOut.textContent || '0').replace(/[^0-9.]/g, '')) || 0 };
          var fmtDisp = { v: parseFloat((yearOut.textContent || '0').replace(/[^0-9.]/g, '')) || 0 };
          sliders.forEach(function (sl) {
            sl.addEventListener('input', function () {
              var v = +document.getElementById('calc-hours').value * (+document.getElementById('calc-rate').value) * (+document.getElementById('calc-share').value) * 0.01 * 52;
              document.getElementById('calc-hours-out').textContent = document.getElementById('calc-hours').value;
              document.getElementById('calc-rate-out').textContent = document.getElementById('calc-rate').value;
              document.getElementById('calc-share-out').textContent = document.getElementById('calc-share').value;
              gsap.to(disp, { v: v, duration: 0.9, ease: 'elastic.out(1, 0.55)',
                onUpdate: function () { yearOut.textContent = '$' + Math.round(disp.v).toLocaleString('en-US'); } });
            });
          });
        }
      }

      /* ── 4. MASTHEAD: horizontal band drift ── */
      var band = document.querySelector('.masthead .band');
      if (band) {
        gsap.fromTo(band, { xPercent: 3 }, { xPercent: -6, ease: 'none',
          scrollTrigger: { trigger: '.masthead', scrub: true, start: 'top bottom', end: 'bottom top' } });
      }

      /* ── 5. FAQ: stagger + GSAP-height accordion (native details semantics kept) ── */
      var faq = document.querySelector('#faq');
      if (faq) {
        var dts = faq.querySelectorAll('details');
        gsap.fromTo(dts, { y: 22, autoAlpha: 0 }, { y: 0, autoAlpha: 1, duration: 0.55, ease: 'power2.out', stagger: 0.08,
          scrollTrigger: { trigger: faq, start: 'top 80%', once: true } });
        dts.forEach(function (d) {
          var summary = d.querySelector('summary');
          var content = summary ? summary.nextElementSibling : null;
          if (!summary || !content) return;
          summary.addEventListener('click', function (e) {
            e.preventDefault();
            if (d.open) {
              gsap.to(content, { height: 0, opacity: 0, duration: 0.35, ease: 'power2.inOut',
                onStart: function () { content.style.overflow = 'hidden'; },
                onComplete: function () { d.open = false; content.style.height = ''; content.style.overflow = ''; content.style.opacity = ''; } });
            } else {
              d.open = true;
              var full = content.scrollHeight;
              gsap.fromTo(content, { height: 0, opacity: 0 }, { height: full, opacity: 1, duration: 0.45, ease: 'power2.out',
                onStart: function () { content.style.overflow = 'hidden'; },
                onComplete: function () { content.style.height = ''; content.style.overflow = ''; } });
            }
          });
        });
      }

      /* ── 6. SECTION TITLES: letter-level reveal ── */
      document.querySelectorAll('.section-title').forEach(function (h2) {
        if (h2.getAttribute('data-split') === 'true' || !h2.textContent.trim()) return;
        h2.setAttribute('data-split', 'true');
        var chars = splitChars(h2);
        if (!chars.length) return;
        gsap.fromTo(chars, { yPercent: 110 }, { yPercent: 0, duration: 0.7, ease: 'power4.out', stagger: 0.018,
          scrollTrigger: { trigger: h2, start: 'top 85%', once: true } });
      });

      /* ── 7. CTA: monogram pop + statement words highlight sequentially ── */
      var mono = document.querySelector('.monogram');
      if (mono) {
        gsap.fromTo(mono, { scale: 0.6, autoAlpha: 0, rotate: -6 }, { scale: 1, autoAlpha: 1, rotate: 0, duration: 0.9, ease: 'back.out(1.6)',
          scrollTrigger: { trigger: mono, start: 'top 88%', once: true } });
      }
      var stmt = document.querySelector('.cta-statement');
      if (stmt) {
        var swords = splitWords(stmt);
        if (swords.length) {
          gsap.fromTo(swords, { autoAlpha: 0.25 }, { autoAlpha: 1, duration: 0.5, ease: 'power1.out', stagger: 0.05,
            scrollTrigger: { trigger: stmt, start: 'top 85%', once: true } });
        }
      }

      /* ── everything from MEDIUM below ── */
      gsap.utils.toArray('section').forEach(function (section) {
        var els = section.querySelectorAll('.rise');
        if (!els.length) return;
        gsap.from(els, { y: 28, autoAlpha: 0, duration: 0.75, ease: 'power2.out', stagger: 0.09,
          scrollTrigger: { trigger: section, start: 'top 82%', once: true } });
      });

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

      gsap.utils.toArray('#work .work-block').forEach(function (block) {
        var img = block.querySelector('.work-visual img');
        if (!img) return;
        gsap.fromTo(img, { yPercent: -8 }, { yPercent: 8, ease: 'none',
          scrollTrigger: { trigger: block, scrub: true, start: 'top bottom', end: 'bottom top' } });
        gsap.fromTo(img, { filter: 'grayscale(100%)' }, { filter: 'grayscale(0%)', duration: 1.2, ease: 'power2.out',
          scrollTrigger: { trigger: block, start: 'top 80%', once: true } });
      });

      document.querySelectorAll('#numbers .figure-tile .n').forEach(runCountUp);

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
      console.error('HMS Motion Full error:', err);
    }
  }
  /* Init AFTER full load (images settle layout) so ScrollTrigger never needs a
   reverting refresh — reverting once-triggers would leave the page invisible. */
if (document.readyState === 'complete') init();
else window.addEventListener('load', init);
})();
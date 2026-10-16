/* HMS motion layer — Lenis smooth scroll + GSAP (v2026-10-16)
   Installed after security scan: lenis MIT, GSAP free-tier commercial OK. */
(function () {
  'use strict';
  var prefersReduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (prefersReduced) return; // accessibility: no motion for those who ask

  /* Lenis buttery scroll */
  if (window.Lenis) {
    var lenis = new Lenis({ duration: 1.1, smoothWheel: true });
    function raf(t) { lenis.raf(t); requestAnimationFrame(raf); }
    requestAnimationFrame(raf);
    window.__lenis = lenis;
  }

  /* GSAP: hero entrance + ScrollTrigger reveals (AOS stays for legacy cards) */
  if (window.gsap) {
    gsap.registerPlugin(ScrollTrigger);

    var hero = document.querySelector('.hero');
    if (hero) {
      var tl = gsap.timeline({ defaults: { ease: 'power3.out' } });
      var heroEls = hero.querySelectorAll('h1, .hero-sub, .hero-cta, .hero-tag');
      if (heroEls.length) tl.from(heroEls, { y: 28, opacity: 0, duration: 0.9, stagger: 0.12, delay: 0.15 });
      var glow = hero.querySelector('.hero-glow');
      if (glow) gsap.to(glow, { opacity: 0.85, scale: 1.06, duration: 2.4, repeat: -1, yoyo: true, ease: 'sine.inOut' });
    }

    /* Service/pricing cards: subtle rise as they enter */
    gsap.utils.toArray('.service-card, .pricing-card').forEach(function (card) {
      gsap.from(card, {
        scrollTrigger: { trigger: card, start: 'top 88%' },
        y: 24, opacity: 0, duration: 0.7, ease: 'power2.out', clearProps: 'all'
      });
    });

    /* CTA buttons: magnetic hover */
    document.querySelectorAll('.btn, .hero-cta a, .cta a').forEach(function (btn) {
      btn.addEventListener('mousemove', function (e) {
        var r = btn.getBoundingClientRect();
        var x = e.clientX - r.left - r.width / 2, y = e.clientY - r.top - r.height / 2;
        gsap.to(btn, { x: x * 0.18, y: y * 0.22, duration: 0.3, ease: 'power2.out' });
      });
      btn.addEventListener('mouseleave', function () {
        gsap.to(btn, { x: 0, y: 0, duration: 0.45, ease: 'elastic.out(1, 0.5)' });
      });
    });
  }
})();

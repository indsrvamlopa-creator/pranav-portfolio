/* =============================================================
   Pranav — animation layer (GSAP + ScrollTrigger)
   Falls back gracefully if GSAP is missing or the visitor
   prefers reduced motion.
   ============================================================= */
(() => {
  const $ = (s, c = document) => c.querySelector(s);
  const $$ = (s, c = document) => [...c.querySelectorAll(s)];
  const root = document.documentElement;
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const hasGsap = !!(window.gsap && window.ScrollTrigger);

  /* ---------------------------------------------------------
     Always on: gold dust in hero, tool tabs, orbit pop-in
     --------------------------------------------------------- */
  if (!reduce) initDust();
  initOrbit();
  initToolTabs();

  if (reduce || !hasGsap) {
    root.classList.add("fx-static");
    toolCardsFallback();
    return;
  }

  gsap.registerPlugin(ScrollTrigger);
  root.classList.add("fx-on");

  /* remove the simple CSS fade so GSAP owns these elements */
  const take = (els) => {
    els = Array.isArray(els) ? els : [els];
    els.filter(Boolean).forEach((el) => { el.classList.remove("reveal"); el.style.transitionDelay = ""; });
    return els.filter(Boolean);
  };
  const st = (trigger, start = "top 85%") => ({ trigger, start, once: true });
  // small "pop in" groups: hide now, animate when the container scrolls into view
  const popIn = (container, items, vars) => {
    if (!container || !items.length) return;
    gsap.set(items, { opacity: 0, y: vars.y ?? 20, scale: vars.scale ?? 1 });
    const io = new IntersectionObserver(([e]) => {
      if (!e.isIntersecting) return;
      io.disconnect();
      gsap.to(items, { opacity: 1, y: 0, scale: 1, duration: vars.duration ?? 0.6, ease: vars.ease ?? "back.out(3)", stagger: vars.stagger ?? 0.05, clearProps: "transform,opacity" });
    }, { threshold: 0.1 });
    io.observe(container);
  };

  /* ---------------------------------------------------------
     Text splitting
     --------------------------------------------------------- */
  function splitChars(el) {
    const units = [];
    [...el.childNodes].forEach((node) => {
      if (node.nodeType === 3) {
        const frag = document.createDocumentFragment();
        for (const ch of node.textContent) {
          if (/\s/.test(ch)) { frag.appendChild(document.createTextNode(ch)); continue; }
          const s = document.createElement("span");
          s.className = "ch"; s.textContent = ch;
          frag.appendChild(s); units.push(s);
        }
        node.replaceWith(frag);
      } else if (node.nodeType === 1 && node.tagName !== "BR") {
        node.classList.add("ch"); units.push(node);  // gold / outline words move as one piece
      }
    });
    return units;
  }

  function splitWords(el) {
    const inners = [];
    [...el.childNodes].forEach((node) => {
      if (node.nodeType === 3) {
        const frag = document.createDocumentFragment();
        node.textContent.split(/(\s+)/).forEach((part) => {
          if (!part) return;
          if (/^\s+$/.test(part)) { frag.appendChild(document.createTextNode(part)); return; }
          const w = document.createElement("span"); w.className = "w";
          const wi = document.createElement("span"); wi.className = "wi"; wi.textContent = part;
          w.appendChild(wi); frag.appendChild(w); inners.push(wi);
        });
        node.replaceWith(frag);
      } else if (node.nodeType === 1 && node.tagName !== "BR") {
        const w = document.createElement("span"); w.className = "w";
        node.replaceWith(w); w.appendChild(node); node.classList.add("wi"); inners.push(node);
      }
    });
    return inners;
  }

  /* ---------------------------------------------------------
     1. Hero — letters drop in with a bounce after the loader
     --------------------------------------------------------- */
  const heroChars = $$(".hero__title .line__inner").flatMap(splitChars);
  gsap.set(heroChars, { yPercent: 120, rotate: () => gsap.utils.random(-25, 25), opacity: 0 });
  const playHero = () => {
    gsap.to(heroChars, { yPercent: 0, rotate: 0, opacity: 1, duration: 1.1, ease: "back.out(2)", stagger: 0.035, delay: 0.1 });
    ScrollTrigger.refresh();
  };
  if (window.__pfReady) playHero(); else document.addEventListener("pf:ready", playHero, { once: true });

  // hero content drifts up & fades as you scroll away
  gsap.to(".hero__orb--1", { yPercent: 40, ease: "none", scrollTrigger: { trigger: ".hero", start: "top top", end: "bottom top", scrub: true } });

  /* ---------------------------------------------------------
     2. Section titles — words rise from a mask
     --------------------------------------------------------- */
  $$(".section-title, .cta-band h2").forEach((title) => {
    take(title);
    const words = splitWords(title);
    gsap.from(words, { yPercent: 115, rotate: 5, duration: 1, ease: "power4.out", stagger: 0.06, scrollTrigger: st(title, "top 88%") });
  });
  $$(".eyebrow").forEach((el) => {
    take(el);
    gsap.from(el, { x: -40, opacity: 0, letterSpacing: "0.6em", duration: 1, ease: "power3.out", scrollTrigger: st(el, "top 90%") });
  });

  /* ---------------------------------------------------------
     3. Marquee leans with scroll speed
     --------------------------------------------------------- */
  const marquee = $(".marquee");
  if (marquee) {
    gsap.set(marquee, { rotation: -2, scale: 1.04 });
    const skewTo = gsap.quickTo(marquee, "skewX", { duration: 0.5, ease: "power3" });
    ScrollTrigger.create({ onUpdate: (self) => skewTo(gsap.utils.clamp(-10, 10, self.getVelocity() / -300)) });
  }

  /* ---------------------------------------------------------
     4. About — photo swings in, stats pop
     --------------------------------------------------------- */
  const aboutVisual = $(".about__visual");
  if (aboutVisual) {
    take(aboutVisual);
    gsap.from(aboutVisual, { x: -120, rotate: -12, opacity: 0, duration: 1.4, ease: "elastic.out(1, 0.7)", scrollTrigger: st(aboutVisual) });
  }
  const stats = take($$(".stat"));
  if (stats.length) gsap.from(stats, { scale: 0.4, y: 50, opacity: 0, duration: 0.9, ease: "back.out(2.6)", stagger: 0.1, clearProps: "transform", scrollTrigger: st(".stats", "top 90%") });
  const tags = $$(".about__tags span");
  if (tags.length) { take($(".about__tags")); popIn($(".about__tags"), tags, { y: 30, scale: 0.6, stagger: 0.06 }); }

  /* ---------------------------------------------------------
     5. Services — cards flip up, then tilt with the mouse
     --------------------------------------------------------- */
  const services = take($$(".service-card"));
  if (services.length) {
    const grid = $(".services__grid");
    // icons are drawn line-by-line: normalise every stroke to length 1
    $$(".service-card__icon svg *").forEach((shape) => shape.setAttribute("pathLength", "1"));
    // cards swing in from alternating sides in 3D
    gsap.from(services, {
      y: 120, scale: 0.85, opacity: 0,
      rotationY: (i) => [-38, 0, 38][i % 3], rotationX: -18,
      transformPerspective: 1100, transformOrigin: "50% 100%",
      duration: 1.3, ease: "back.out(1.35)", stagger: 0.12,
      clearProps: "transform,opacity", scrollTrigger: st(grid),
    });
    // big numbers roll up, icons spring in, then draw themselves
    gsap.from($$(".service-card__num"), { yPercent: 120, opacity: 0, duration: 1, ease: "power4.out", stagger: 0.12, delay: 0.3, clearProps: "transform,opacity", scrollTrigger: st(grid) });
    gsap.from($$(".service-card__icon"), { scale: 0, rotate: -140, duration: 1.1, ease: "elastic.out(1, 0.45)", stagger: 0.12, delay: 0.35, clearProps: "transform", scrollTrigger: st(grid) });
    const drawIO = new IntersectionObserver(([e]) => {
      if (!e.isIntersecting) return;
      drawIO.disconnect();
      services.forEach((c, i) => setTimeout(() => c.classList.add("is-drawn"), 650 + i * 150));
    }, { threshold: 0.15 });
    drawIO.observe(grid);
    // giant outline words drift sideways while you scroll
    const bg = $(".services__bgtext");
    if (bg) gsap.fromTo(bg, { xPercent: 5, yPercent: -50 }, { xPercent: -40, yPercent: -50, ease: "none", scrollTrigger: { trigger: ".services", start: "top bottom", end: "bottom top", scrub: 0.6 } });
  }
  tilt($$(".service-card"), 8);

  /* ---------------------------------------------------------
     6. Projects — cards rise in batches
     --------------------------------------------------------- */
  const projects = take($$(".project"));
  if (projects.length) {
    gsap.set(projects, { y: 120, opacity: 0, rotate: (i) => (i % 2 ? 2.5 : -2.5) });
    ScrollTrigger.batch(projects, {
      start: "top 90%", once: true,
      onEnter: (batch) => gsap.to(batch, { y: 0, opacity: 1, rotate: 0, duration: 1.1, ease: "back.out(1.3)", stagger: 0.12, clearProps: "transform" }),
    });
  }
  const filters = $("#filters");
  if (filters) { take(filters); popIn(filters, [...filters.children], { y: 20 }); }

  /* ---------------------------------------------------------
     7. Toolkit — orbit spins in, cards JUMP into place
     --------------------------------------------------------- */
  const orbit = $(".orbit");
  if (orbit) {
    gsap.from(orbit, { scale: 0.35, rotate: -120, opacity: 0, duration: 1.8, ease: "elastic.out(1, 0.6)", scrollTrigger: st(orbit, "top 85%") });
  }
  const toolCards = $$(".tcard");
  if (toolCards.length) {
    gsap.set(toolCards, { y: 160, scale: 0.3, opacity: 0, rotation: () => gsap.utils.random(-35, 35) });
    ScrollTrigger.create({
      trigger: "#toolGrid", start: "top 88%", once: true,
      onEnter: () => {
        gsap.to(toolCards, {
          y: 0, scale: 1, opacity: 1, rotation: 0, duration: 1.5, ease: "elastic.out(1, 0.5)",
          stagger: { each: 0.08, from: "random" }, clearProps: "transform",
          onStart: () => toolCards.forEach((c, i) => setTimeout(() => fillCard(c), 250 + i * 80)),
        });
      },
    });
    tilt(toolCards, 14);
    startRandomJumps(toolCards);
  }
  const tabs = $("#toolTabs");
  if (tabs) popIn(tabs, [...tabs.children], { y: -20 });

  const why = $(".why");
  if (why) {
    take(why);
    gsap.from(why, { opacity: 0, duration: 0.6, scrollTrigger: st(why, "top 90%") });
    gsap.from($$(".why__item", why), { y: 50, opacity: 0, duration: 0.9, ease: "back.out(2)", stagger: 0.1, clearProps: "transform", scrollTrigger: st(why, "top 90%") });
    gsap.from($$(".why__item b", why), { scale: 0, rotate: 180, duration: 1, ease: "elastic.out(1, 0.4)", stagger: 0.1, delay: 0.2, scrollTrigger: st(why, "top 90%") });
  }

  /* ---------------------------------------------------------
     8. Process — dots pop along the line
     --------------------------------------------------------- */
  const steps = take($$(".step"));
  if (steps.length) {
    gsap.from(steps, { y: 60, opacity: 0, duration: 0.9, ease: "power3.out", stagger: 0.15, clearProps: "transform", scrollTrigger: st(".process__track") });
    gsap.from($$(".step__dot"), { scale: 0, duration: 1.1, ease: "elastic.out(1, 0.35)", stagger: 0.15, delay: 0.2, scrollTrigger: st(".process__track") });
  }

  /* ---------------------------------------------------------
     9. Testimonials, clients, CTA, contact, footer
     --------------------------------------------------------- */
  const quotes = take($$(".quote"));
  if (quotes.length) gsap.from(quotes, { rotationY: -35, y: 70, opacity: 0, transformPerspective: 1000, duration: 1.1, ease: "back.out(1.4)", stagger: 0.12, clearProps: "transform", scrollTrigger: st(".testimonials__grid") });

  const clientRow = $(".clients__row");
  if (clientRow) { take(clientRow); popIn(clientRow, [...clientRow.children], { y: 40, scale: 0.7, stagger: 0.07 }); }

  const cta = $(".cta-band__inner");
  if (cta) {
    take(cta);
    gsap.fromTo(cta, { scale: 0.86, borderRadius: 80, opacity: 0.4 }, { scale: 1, borderRadius: 32, opacity: 1, ease: "none", scrollTrigger: { trigger: cta, start: "top bottom", end: "top 45%", scrub: true } });
  }

  const contactCards = take($$(".contact-card"));
  if (contactCards.length) gsap.from(contactCards, { x: -60, opacity: 0, duration: 0.9, ease: "back.out(1.8)", stagger: 0.1, clearProps: "transform", scrollTrigger: st(".contact__cards") });
  const form = $(".contact__form");
  if (form) { take(form); gsap.from(form, { y: 80, rotate: 2, opacity: 0, duration: 1.2, ease: "power4.out", scrollTrigger: st(form) }); }
  const chips = $$(".chip span");
  popIn($(".contact__form"), chips, { y: 0, scale: 0.5, duration: 0.5, stagger: 0.025 });

  const big = $(".footer__big");
  if (big) gsap.from(big, { yPercent: 60, opacity: 0, letterSpacing: "0.1em", ease: "none", scrollTrigger: { trigger: ".footer", start: "top bottom", end: "top 40%", scrub: true } });

  // refresh positions once fonts/images settle
  addEventListener("load", () => ScrollTrigger.refresh());
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(() => ScrollTrigger.refresh());

  /* =========================================================
     Helpers
     ========================================================= */
  function fillCard(card) {
    card.classList.add("is-in");
    const b = $("[data-count]", card);
    if (!b) return;
    const obj = { v: 0 }, target = +b.dataset.count;
    gsap.to(obj, { v: target, duration: 1.6, ease: "power2.out", onUpdate: () => (b.textContent = Math.round(obj.v)) });
  }

  function tilt(els, max) {
    if (!matchMedia("(hover: hover) and (pointer: fine)").matches) return;
    els.forEach((el) => {
      el.addEventListener("pointermove", (e) => {
        const r = el.getBoundingClientRect();
        const px = (e.clientX - r.left) / r.width - 0.5, py = (e.clientY - r.top) / r.height - 0.5;
        el.style.setProperty("--rx", (-py * max).toFixed(2) + "deg");
        el.style.setProperty("--ry", (px * max).toFixed(2) + "deg");
      });
      el.addEventListener("pointerleave", () => { el.style.setProperty("--rx", "0deg"); el.style.setProperty("--ry", "0deg"); });
    });
  }

  function startRandomJumps(cards) {
    let visible = false;
    new IntersectionObserver(([e]) => (visible = e.isIntersecting), { threshold: 0.2 }).observe($("#toolGrid"));
    setInterval(() => {
      if (!visible || document.hidden) return;
      const pool = cards.filter((c) => c.offsetParent && !c.matches(":hover"));
      if (!pool.length) return;
      const c = pool[Math.floor(Math.random() * pool.length)];
      c.classList.remove("is-jump"); void c.offsetWidth; c.classList.add("is-jump");
      setTimeout(() => c.classList.remove("is-jump"), 900);
    }, 1400);
  }

  /* ---- non-GSAP pieces ---- */
  function toolCardsFallback() {
    const cards = $$(".tcard");
    if (!cards.length) return;
    const io = new IntersectionObserver((entries) => entries.forEach((e) => {
      if (e.isIntersecting) { e.target.classList.add("is-in"); io.unobserve(e.target); }
    }), { threshold: 0.3 });
    cards.forEach((c) => io.observe(c));
  }

  function initOrbit() {
    const orbitEl = $(".orbit");
    if (!orbitEl) return;
    new IntersectionObserver(([e], obs) => {
      if (e.isIntersecting) { orbitEl.classList.add("is-in"); obs.disconnect(); }
    }, { threshold: 0.25 }).observe(orbitEl);
  }

  function initToolTabs() {
    const tabsEl = $("#toolTabs");
    if (!tabsEl) return;
    const cards = $$(".tcard");
    $$(".tool-tab", tabsEl).forEach((tab) => tab.addEventListener("click", () => {
      $$(".tool-tab", tabsEl).forEach((t) => t.classList.toggle("is-active", t === tab));
      const g = tab.dataset.group;
      const show = cards.filter((c) => g === "all" || c.dataset.group === g);
      const hide = cards.filter((c) => !show.includes(c));
      if (window.gsap && !reduce) {
        gsap.to(hide, { scale: 0.6, opacity: 0, duration: 0.25, ease: "power2.in", onComplete: () => hide.forEach((c) => (c.style.display = "none")) });
        show.forEach((c) => (c.style.display = ""));
        gsap.fromTo(show, { y: 60, scale: 0.6, opacity: 0 }, { y: 0, scale: 1, opacity: 1, duration: 0.9, ease: "elastic.out(1, 0.55)", stagger: 0.05, delay: 0.2, clearProps: "transform" });
      } else {
        cards.forEach((c) => (c.style.display = show.includes(c) ? "" : "none"));
      }
    }));
  }

  function initDust() {
    const canvas = $("#heroDust");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    let w, h, parts = [], running = true, mx = -999, my = -999;
    const resize = () => {
      w = canvas.clientWidth; h = canvas.clientHeight;
      canvas.width = w * dpr; canvas.height = h * dpr; ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      const count = Math.round(Math.min(90, (w * h) / 16000));
      parts = Array.from({ length: count }, () => ({
        x: Math.random() * w, y: Math.random() * h, r: Math.random() * 1.8 + 0.4,
        vx: (Math.random() - 0.5) * 0.15, vy: -(Math.random() * 0.35 + 0.08),
        a: Math.random() * 0.6 + 0.2, t: Math.random() * Math.PI * 2,
      }));
    };
    resize(); addEventListener("resize", resize);
    canvas.parentElement.addEventListener("pointermove", (e) => { const r = canvas.getBoundingClientRect(); mx = e.clientX - r.left; my = e.clientY - r.top; });
    let looping = false;
    new IntersectionObserver(([e]) => {
      running = e.isIntersecting;
      if (running && !looping) { looping = true; requestAnimationFrame(draw); }
    }).observe(canvas);
    function draw() {
      if (!running) { looping = false; return; }
      ctx.clearRect(0, 0, w, h);
      for (const p of parts) {
        p.t += 0.02; p.x += p.vx + Math.sin(p.t) * 0.12; p.y += p.vy;
        const dx = p.x - mx, dy = p.y - my, d = Math.hypot(dx, dy);
        if (d < 110) { p.x += (dx / d) * 1.4; p.y += (dy / d) * 1.4; }
        if (p.y < -10) { p.y = h + 10; p.x = Math.random() * w; }
        if (p.x < -10) p.x = w + 10; if (p.x > w + 10) p.x = -10;
        const tw = 0.5 + Math.sin(p.t * 1.7) * 0.5;
        ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(246, 226, 122, ${p.a * (0.4 + tw * 0.6)})`;
        ctx.shadowColor = "rgba(212,175,55,.8)"; ctx.shadowBlur = 8;
        ctx.fill();
      }
      requestAnimationFrame(draw);
    }
  }
})();

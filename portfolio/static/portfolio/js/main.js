(() => {
  const $ = (s, c = document) => c.querySelector(s);
  const $$ = (s, c = document) => [...c.querySelectorAll(s)];
  const body = document.body;
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------- Preloader ---------- */
  const preloader = $("#preloader");
  const fill = $("#preloaderFill");
  const count = $("#preloaderCount");
  let progress = 0;
  const finishLoading = () => {
    preloader.classList.add("is-done");
    body.classList.remove("is-loading");
    body.classList.add("is-ready");
    window.__pfReady = true;
    document.dispatchEvent(new Event("pf:ready"));
    revealHeroBits();
  };
  if (reduceMotion) {
    finishLoading();
  } else {
    const tick = setInterval(() => {
      progress = Math.min(100, progress + Math.ceil(Math.random() * 9));
      fill.style.clipPath = `inset(0 ${100 - progress}% 0 0)`;
      count.textContent = progress + "%";
      if (progress >= 100) {
        clearInterval(tick);
        setTimeout(finishLoading, 350);
      }
    }, 55);
  }

  function revealHeroBits() {
    $$(".hero .reveal").forEach((el, i) => setTimeout(() => el.classList.add("is-visible"), 400 + i * 140));
  }

  /* ---------- Year ---------- */
  $("#year").textContent = new Date().getFullYear();

  /* ---------- Role rotator: text "decodes" into the next role ---------- */
  let roles = [];
  try { roles = JSON.parse($("#roles").textContent); } catch (e) { roles = []; }
  const rot = $("#rotator");
  const GLYPHS = "!<>-_/[]{}=+*^?#ABCDEFGHIJKLMNOPQRSTUVWXYZ";
  function scrambleTo(el, text) {
    const from = el.textContent, len = Math.max(from.length, text.length);
    const queue = Array.from({ length: len }, (_, i) => {
      const start = Math.floor(Math.random() * 14);
      return { from: from[i] || "", to: text[i] || "", start, end: start + 6 + Math.floor(Math.random() * 14), ch: "" };
    });
    let frame = 0;
    (function tick() {
      el.textContent = "";
      let done = 0;
      queue.forEach((q) => {
        if (frame >= q.end) { done++; el.append(q.to); }
        else if (frame >= q.start) {
          if (!q.ch || Math.random() < 0.3) q.ch = GLYPHS[Math.floor(Math.random() * GLYPHS.length)];
          const s = document.createElement("span"); s.className = "sc"; s.textContent = q.ch; el.append(s);
        } else el.append(q.from);
      });
      frame++;
      if (done < queue.length) requestAnimationFrame(tick);
    })();
  }
  let ri = 0;
  if (rot && roles.length > 1) setInterval(() => {
    ri = (ri + 1) % roles.length;
    if (reduceMotion) rot.textContent = roles[ri]; else scrambleTo(rot, roles[ri]);
  }, 2800);

  /* ---------- Nav ---------- */
  const nav = $("#nav");
  const burger = $("#navBurger");
  burger.addEventListener("click", () => nav.classList.toggle("is-open"));
  $$("#navLinks a").forEach((a) => a.addEventListener("click", () => nav.classList.remove("is-open")));

  const sections = $$("main section[id]");
  const navLinks = $$("#navLinks a");
  const progressBar = $("#scrollProgress");
  const processLine = $("#processLine");
  const processTrack = $(".process__track");

  const onScroll = () => {
    const y = window.scrollY;
    nav.classList.toggle("is-scrolled", y > 40);
    const max = document.documentElement.scrollHeight - innerHeight;
    progressBar.style.width = (y / max) * 100 + "%";

    let current = "";
    sections.forEach((s) => { if (y >= s.offsetTop - innerHeight / 3) current = s.id; });
    navLinks.forEach((a) => a.classList.toggle("is-active", a.getAttribute("href") === "#" + current));

    // process timeline fill
    if (processTrack && processLine) {
      const r = processTrack.getBoundingClientRect();
      const pct = Math.max(0, Math.min(1, (innerHeight * 0.75 - r.top) / r.height));
      processLine.style.width = pct * 100 + "%";
      processLine.style.setProperty("--h", pct * 100 + "%");
    }
  };
  addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  /* ---------- Reveal on scroll ---------- */
  const io = new IntersectionObserver((entries) => {
    entries.forEach((e) => {
      if (!e.isIntersecting) return;
      const el = e.target;
      const siblings = el.parentElement ? $$(":scope > .reveal", el.parentElement) : [];
      const idx = Math.max(0, siblings.indexOf(el));
      el.style.transitionDelay = Math.min(idx, 6) * 80 + "ms";
      el.classList.add("is-visible");
      io.unobserve(el);
    });
  }, { threshold: 0.15, rootMargin: "0px 0px -40px 0px" });
  $$(".reveal").filter((el) => !el.closest(".hero")).forEach((el) => io.observe(el));

  /* ---------- Counters ---------- */
  const counterIO = new IntersectionObserver((entries) => {
    entries.forEach((e) => {
      if (!e.isIntersecting) return;
      const el = e.target, target = +el.dataset.target, dur = 1800, t0 = performance.now();
      const step = (now) => {
        const p = Math.min(1, (now - t0) / dur);
        el.textContent = Math.round(target * (1 - Math.pow(1 - p, 4)));
        if (p < 1) requestAnimationFrame(step);
      };
      requestAnimationFrame(step);
      counterIO.unobserve(el);
    });
  }, { threshold: 0.6 });
  $$(".counter").forEach((c) => counterIO.observe(c));

  /* ---------- Spotlight hover ---------- */
  $$(".spotlight").forEach((card) => {
    card.addEventListener("pointermove", (e) => {
      const r = card.getBoundingClientRect();
      card.style.setProperty("--mx", e.clientX - r.left + "px");
      card.style.setProperty("--my", e.clientY - r.top + "px");
    });
  });

  /* ---------- Magnetic buttons (desktop only) ---------- */
  if (matchMedia("(hover: hover) and (pointer: fine)").matches) {
    $$(".magnetic").forEach((btn) => {
      btn.addEventListener("pointermove", (e) => {
        const r = btn.getBoundingClientRect();
        const x = e.clientX - r.left - r.width / 2, y = e.clientY - r.top - r.height / 2;
        btn.style.transform = `translate(${x * 0.25}px, ${y * 0.35}px)`;
      });
      btn.addEventListener("pointerleave", () => (btn.style.transform = ""));
    });
  }

  /* ---------- Project filters ---------- */
  const projects = $$(".project");
  $$("#filters .filter").forEach((btn) => {
    btn.addEventListener("click", () => {
      $$("#filters .filter").forEach((b) => b.classList.remove("is-active"));
      btn.classList.add("is-active");
      const f = btn.dataset.filter;
      projects.forEach((p) => {
        const show = f === "all" || p.dataset.category === f;
        p.classList.toggle("is-hidden", !show);
        if (show) { p.classList.remove("is-visible"); requestAnimationFrame(() => requestAnimationFrame(() => p.classList.add("is-visible"))); }
      });
    });
  });

  /* ---------- Hover video previews ---------- */
  $$(".project__preview[data-hover]").forEach((v) => {
    const card = v.closest(".project");
    card.addEventListener("pointerenter", () => { v.classList.add("is-playing"); v.play().catch(() => {}); });
    card.addEventListener("pointerleave", () => { v.classList.remove("is-playing"); v.pause(); });
  });

  /* ---------- Modal ---------- */
  const modal = $("#modal"), media = $("#modalMedia"), modalBody = $("#modalBody");
  const fillMedia = (videoSrc, embedSrc, fallbackEl) => {
    media.innerHTML = "";
    if (videoSrc) {
      const v = document.createElement("video");
      v.src = videoSrc; v.controls = true; v.autoplay = true; v.playsInline = true;
      media.appendChild(v);
    } else if (embedSrc) {
      const iframe = document.createElement("iframe");
      iframe.src = embedSrc;
      iframe.allow = "autoplay; fullscreen; picture-in-picture; encrypted-media";
      iframe.allowFullscreen = true;
      media.appendChild(iframe);
    } else if (fallbackEl) {
      const clone = fallbackEl.cloneNode(true);
      clone.querySelector(".project__overlay")?.remove();
      clone.querySelectorAll("video").forEach((v) => v.remove());
      clone.style.cssText = "width:100%;height:100%;aspect-ratio:auto;border:0;border-radius:0";
      media.appendChild(clone);
    }
  };
  const showModal = () => {
    modal.classList.add("is-open");
    modal.setAttribute("aria-hidden", "false");
    body.style.overflow = "hidden";
  };
  $$("[data-showreel]").forEach((btn) => btn.addEventListener("click", () => {
    fillMedia(btn.dataset.video, btn.dataset.embed);
    modalBody.hidden = true;
    showModal();
  }));
  const openModal = (p) => {
    modalBody.hidden = false;
    $("#modalCat").textContent = [p.dataset.catLabel, p.dataset.year].filter(Boolean).join(" · ");
    $("#modalTitle").textContent = p.dataset.title;
    $("#modalDesc").textContent = p.dataset.desc;
    $("#modalClient").textContent = p.dataset.client || "—";
    $("#modalRole").textContent = p.dataset.role || "—";
    $("#modalTools").textContent = p.dataset.tools || "—";
    fillMedia(p.dataset.video, p.dataset.embed, $(".project__media", p));
    modal.classList.add("is-open");
    modal.setAttribute("aria-hidden", "false");
    body.style.overflow = "hidden";
  };
  const closeModal = () => {
    modal.classList.remove("is-open");
    modal.setAttribute("aria-hidden", "true");
    body.style.overflow = "";
    setTimeout(() => (media.innerHTML = ""), 400);
  };
  projects.forEach((p) => {
    p.addEventListener("click", () => openModal(p));
    p.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); openModal(p); } });
  });
  $$("[data-close]", modal).forEach((el) => el.addEventListener("click", closeModal));
  addEventListener("keydown", (e) => { if (e.key === "Escape" && modal.classList.contains("is-open")) closeModal(); });
})();

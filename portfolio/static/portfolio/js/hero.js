/* =============================================================
   Hero — program monitor + interactive editing timeline
   (no external libraries needed)
   ============================================================= */
(() => {
  const $ = (s, c = document) => c.querySelector(s);
  const $$ = (s, c = document) => [...c.querySelectorAll(s)];
  const hero = $(".hero");
  const body = $("#tlBody");
  if (!hero || !body) return;

  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const finePointer = matchMedia("(hover: hover) and (pointer: fine)").matches;

  const playhead = $("#playhead");
  const clips = $$("#tlV1 .clip--video");
  const slides = $$("#monScreen .monitor__slide");
  const screen = $("#monScreen");
  const titleEl = $("#monTitle"), catEl = $("#monCat");
  const tcEls = [$("#timecode"), $("#tlTc")].filter(Boolean);
  const progressEl = $("#monProgress");
  const toggle = $("#monToggle");
  const monitor = $("#monitor");

  // showreel autoplaying inside the monitor (uploaded MP4 → real sync; YouTube/Vimeo → visual only)
  const reelMode = !!monitor && monitor.classList.contains("monitor--reel");
  const reel = $("#monReel");
  const reelReady = () => reel && isFinite(reel.duration) && reel.duration > 0;

  const DURATION = 22;          // seconds for one pass of the playhead
  const FAKE_SEQ = 96;          // what the timecode pretends the sequence is (real length when the reel is an MP4)
  let p = 0;                    // playhead position 0..1
  let playing = !reduce;
  let visible = true;
  let active = -1;
  let ranges = [];

  /* ---------- waveform ---------- */
  const wave = $("#tlWave");
  if (wave) {
    const bars = Math.max(60, Math.round(wave.clientWidth / 6)) || 120;
    let html = "", phase = Math.random() * 10;
    for (let i = 0; i < bars; i++) {
      const v = Math.abs(Math.sin(i * 0.21 + phase) * 0.55 + Math.sin(i * 0.07) * 0.3 + (Math.random() - 0.5) * 0.35);
      const h = Math.max(12, Math.min(100, Math.round(v * 100)));
      html += `<i style="--h:${h}%;--d:${(i % 12) * 0.08}s"></i>`;
    }
    wave.innerHTML = `<div class="wave__bars">${html}</div><div class="wave__played" id="wavePlayed"><div class="wave__bars">${html}</div></div>`;
  }
  const wavePlayed = $("#wavePlayed");

  /* ---------- clip ranges (as fractions of the lane) ---------- */
  function measure() {
    const lane = $("#tlV1");
    if (!lane) return;
    const w = lane.clientWidth || 1;
    ranges = clips.map((c) => [c.offsetLeft / w, (c.offsetLeft + c.offsetWidth) / w]);
    if (wavePlayed) wavePlayed.firstElementChild.style.width = (wave.clientWidth || 0) + "px";
  }
  measure();
  addEventListener("resize", measure);
  if ("ResizeObserver" in window) new ResizeObserver(measure).observe($("#tlV1"));
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(measure);

  /* ---------- timecode ---------- */
  const pad = (n) => String(n).padStart(2, "0");
  function timecode(frac) {
    const t = frac * (reelReady() ? reel.duration : FAKE_SEQ);
    return `00:${pad(Math.floor(t / 60))}:${pad(Math.floor(t % 60))}:${pad(Math.floor((t % 1) * 24))}`;
  }

  /* ---------- cut the monitor to a clip ---------- */
  function cutTo(i) {
    if (i === active) return;
    if (reelMode) {               // the showreel is on screen — just light up the clip
      active = i;
      clips.forEach((c, j) => c.classList.toggle("is-live", j === i));
      return;
    }
    if (!slides.length) return;
    active = i;
    const slide = slides[i % slides.length];
    slides.forEach((s) => s.classList.toggle("is-active", s === slide));
    clips.forEach((c, j) => c.classList.toggle("is-live", j === i));
    if (titleEl) titleEl.textContent = slide.dataset.title || "";
    if (catEl) catEl.textContent = slide.dataset.cat || "";
    const v = slide.querySelector("video");
    if (v && !reduce) { v.currentTime = 0; v.play().catch(() => {}); }
    slides.forEach((s) => { if (s !== slide) s.querySelector("video")?.pause(); });
    if (!reduce && screen) {
      screen.classList.remove("is-glitch"); void screen.offsetWidth; screen.classList.add("is-glitch");
      setTimeout(() => screen.classList.remove("is-glitch"), 420);
    }
  }

  /* ---------- render one frame ---------- */
  function render() {
    const pct = (p * 100).toFixed(3) + "%";
    playhead.style.left = pct;
    if (progressEl) progressEl.style.width = pct;
    if (wavePlayed) wavePlayed.style.width = pct;
    const tc = timecode(p);
    tcEls.forEach((el) => (el.textContent = tc));
    const idx = ranges.findIndex(([a, b]) => p >= a && p < b);
    if (idx !== -1) cutTo(idx);
  }

  /* ---------- loop ---------- */
  let last = performance.now();
  function loop(now) {
    const dt = Math.min(0.1, (now - last) / 1000);
    last = now;
    if (reelReady()) {
      if (dragging) reel.currentTime = p * reel.duration;   // scrub the real video
      else p = Math.min(0.9999, reel.currentTime / reel.duration);
    } else if (playing && visible && !dragging) { p += dt / DURATION; if (p >= 1) p -= 1; }
    render();
    requestAnimationFrame(loop);
  }
  requestAnimationFrame(loop);

  const syncReel = () => {
    if (!reel) return;
    if (playing && visible) { reel.muted = true; reel.play().catch(() => {}); } else reel.pause();
  };
  new IntersectionObserver(([e]) => { visible = e.isIntersecting; syncReel(); }, { threshold: 0.05 }).observe(hero);

  /* ---------- play / pause ---------- */
  function setPlaying(v) {
    playing = v;
    syncReel();
    monitor?.classList.toggle("is-paused", !v);
    hero.classList.toggle("is-paused", !v);
    toggle?.setAttribute("aria-label", v ? "Pause timeline" : "Play timeline");
  }
  setPlaying(playing);
  toggle?.addEventListener("click", () => setPlaying(!playing));

  /* ---------- scrub: drag anywhere on the timeline ---------- */
  let dragging = false;
  const seek = (clientX) => {
    const r = body.getBoundingClientRect();
    p = Math.max(0, Math.min(0.9999, (clientX - r.left) / r.width));
  };
  body.addEventListener("pointerdown", (e) => {
    dragging = true; body.classList.add("is-scrubbing");
    body.setPointerCapture(e.pointerId);
    seek(e.clientX);
  });
  body.addEventListener("pointermove", (e) => { if (dragging) seek(e.clientX); });
  const endDrag = () => { dragging = false; body.classList.remove("is-scrubbing"); };
  body.addEventListener("pointerup", endDrag);
  body.addEventListener("pointercancel", endDrag);

  // keyboard: clips are buttons — Enter jumps there
  clips.forEach((c, i) => c.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") { e.preventDefault(); if (ranges[i]) p = ranges[i][0] + 0.001; }
  }));

  /* ---------- mouse spotlight + monitor tilt ---------- */
  if (finePointer && !reduce) {
    const spot = $(".hero__spot");
    const chips = $$(".chip-float");
    hero.addEventListener("pointermove", (e) => {
      const r = hero.getBoundingClientRect();
      const x = e.clientX - r.left, y = e.clientY - r.top;
      if (spot) { spot.style.setProperty("--sx", x + "px"); spot.style.setProperty("--sy", y + "px"); spot.style.opacity = 1; }
      const nx = x / r.width - 0.5, ny = y / r.height - 0.5;
      if (monitor) monitor.style.setProperty("--tilt", `rotateY(${(nx * 8).toFixed(2)}deg) rotateX(${(-ny * 6).toFixed(2)}deg)`);
      chips.forEach((c, i) => { c.style.translate = `${(nx * (16 + i * 10)).toFixed(1)}px ${(ny * (14 + i * 8)).toFixed(1)}px`; });
    });
    hero.addEventListener("pointerleave", () => {
      if (spot) spot.style.opacity = 0;
      monitor?.style.setProperty("--tilt", "rotateY(0deg) rotateX(0deg)");
    });
  }
})();

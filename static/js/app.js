/* ============================================================
   Aurelia Grand — interaction engine (guest + PMS)
   Progressive enhancement: everything degrades gracefully.
   ============================================================ */
(function () {
  "use strict";
  const REDUCED = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  document.addEventListener("DOMContentLoaded", () => {
    /* ---------- toasts ---------- */
    document.querySelectorAll(".toast").forEach((t, i) => {
      setTimeout(() => {
        t.style.transition = "opacity .4s, transform .4s";
        t.style.opacity = "0";
        t.style.transform = "translateX(16px)";
        setTimeout(() => t.remove(), 420);
      }, 4600 + i * 300);
    });

    /* ---------- mobile sidebar ---------- */
    const toggle = document.getElementById("sidebar-toggle");
    const sidebar = document.getElementById("sidebar");
    const sidebarScrim = document.getElementById("pms-scrim");
    const closeSidebar = () => {
      if (!sidebar) return;
      sidebar.classList.remove("open");
      sidebarScrim?.classList.remove("on");
      sidebarScrim?.setAttribute("aria-hidden", "true");
      toggle?.setAttribute("aria-expanded", "false");
      document.body.classList.remove("ui-locked");
    };
    const openSidebar = () => {
      if (!sidebar) return;
      sidebar.classList.add("open");
      sidebarScrim?.classList.add("on");
      sidebarScrim?.setAttribute("aria-hidden", "false");
      toggle?.setAttribute("aria-expanded", "true");
      document.body.classList.add("ui-locked");
    };
    if (toggle && sidebar) toggle.addEventListener("click", () => {
      sidebar.classList.contains("open") ? closeSidebar() : openSidebar();
    });
    sidebarScrim?.addEventListener("click", closeSidebar);
    sidebar?.querySelectorAll("a").forEach((a) => a.addEventListener("click", closeSidebar));
    // Do not leave the document scroll-locked after a mobile drawer is open
    // and the viewport becomes desktop-sized (rotation, tablet split view,
    // browser resize). This affects every staff role using the PMS shell.
    const syncPmsScrollLock = () => {
      if (window.matchMedia("(min-width: 1021px)").matches) {
        sidebar?.classList.remove("open");
        sidebarScrim?.classList.remove("on");
        sidebarScrim?.setAttribute("aria-hidden", "true");
        toggle?.setAttribute("aria-expanded", "false");
        document.body.classList.remove("ui-locked");
      }
    };
    window.addEventListener("resize", syncPmsScrollLock, { passive: true });
    window.addEventListener("pageshow", syncPmsScrollLock, { passive: true });
    syncPmsScrollLock();
    document.addEventListener("keydown", (e) => { if (e.key === "Escape") closeSidebar(); });

    /* ---------- destructive confirms ---------- */
    document.querySelectorAll("form[data-confirm]").forEach((f) => {
      f.addEventListener("submit", (e) => { if (!window.confirm(f.dataset.confirm)) e.preventDefault(); });
    });

    /* ---------- prevent accidental double submits ---------- */
    document.addEventListener("submit", (e) => {
      if (e.defaultPrevented) return;
      const form = e.target;
      if (!form || (form.getAttribute("method") || "get").toLowerCase() !== "post") return;
      if (form.hasAttribute("data-no-loading") || form.dataset.busy === "1") return;
      const button = form.querySelector("button[type=submit]:not([disabled])");
      if (!button) return;
      form.dataset.busy = "1";
      form.setAttribute("aria-busy", "true");
      button.disabled = true;
      button.classList.add("is-busy");
      button.setAttribute("aria-busy", "true");
      button.innerHTML = '<i class="ri-loader-4-line busy-spin" aria-hidden="true"></i> Working…';
    });

    /* ---------- autosubmit selects ---------- */
    document.querySelectorAll("select[data-autosubmit]").forEach((s) => {
      s.addEventListener("change", () => s.form.submit());
    });

    /* ---------- linked date pairs ---------- */
    document.querySelectorAll("form[data-datepair]").forEach((form) => {
      const ci = form.querySelector('[name="check_in"]');
      const co = form.querySelector('[name="check_out"]');
      if (!ci || !co) return;
      const sync = () => {
        if (ci.value) {
          const next = new Date(ci.value + "T00:00:00");
          next.setDate(next.getDate() + 1);
          co.min = next.toISOString().slice(0, 10);
          if (co.value && co.value <= ci.value) co.value = co.min;
        }
      };
      ci.addEventListener("change", sync);
      sync();
    });

    if (REDUCED) return; // motion-sensitive users get the calm experience

    /* ---------- scroll progress bar ---------- */
    const bar = document.querySelector(".scroll-progress");
    const nav = document.querySelector(".site-nav");
    const onScroll = () => {
      if (bar) {
        const h = document.documentElement;
        const pct = h.scrollTop / Math.max(h.scrollHeight - h.clientHeight, 1);
        bar.style.width = (pct * 100).toFixed(2) + "%";
      }
      if (nav) nav.classList.toggle("scrolled", window.scrollY > 40);
      // hero parallax
      const heroBg = document.querySelector(".hero-bg");
      if (heroBg && window.scrollY < window.innerHeight) {
        heroBg.style.transform = "translateY(" + (window.scrollY * 0.35).toFixed(1) + "px)";
      }
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();

    /* ---------- reveal on scroll ---------- */
    const io = new IntersectionObserver((entries) => {
      entries.forEach((en) => {
        if (en.isIntersecting) {
          en.target.classList.add("in");
          if (en.target.classList.contains("room-card")) en.target.classList.add("in-view");
          // animate any progress bars inside
          en.target.querySelectorAll?.(".progress").forEach((p) => {
            const inner = p.firstElementChild;
            if (inner) { p.style.setProperty("--w", inner.dataset.w || inner.style.width); p.classList.add("animated"); }
          });
          if (en.target.classList.contains("progress")) {
            en.target.classList.add("animated");
          }
          io.unobserve(en.target);
        }
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -40px 0px" });
    document.querySelectorAll(".rv").forEach((el) => io.observe(el));

    // progress bars: move inline width into --w so CSS can animate from 0
    document.querySelectorAll(".progress > div").forEach((inner) => {
      if (!inner.dataset.w) { inner.dataset.w = inner.style.width || "0%"; }
      const p = inner.parentElement;
      if (p.classList.contains("animated")) return;
      p.style.setProperty("--w", inner.dataset.w);
    });
    document.querySelectorAll(".cal-occ > div").forEach((inner) => {
      const w = inner.style.width; inner.style.width = "0%";
      requestAnimationFrame(() => requestAnimationFrame(() => { inner.style.width = w; }));
    });

    /* ---------- auto-stagger grids ---------- */
    document.querySelectorAll(".room-grid, .kpi-grid, .kanban, .feature-strip .cols, .grid").forEach((g) => {
      Array.from(g.children).forEach((el, i) => {
        if (el.classList.contains("rv")) el.style.setProperty("--d", Math.min(i, 8) * 110 + "ms");
      });
    });

    /* ---------- count-up numbers ---------- */
    const fmt = (v, dec, prefix, suffix, group) => {
      let n = v.toFixed(dec);
      if (group) n = Number(n).toLocaleString("en-US", { minimumFractionDigits: dec, maximumFractionDigits: dec });
      return prefix + n + suffix;
    };
    const countIO = new IntersectionObserver((entries) => {
      entries.forEach((en) => {
        if (!en.isIntersecting) return;
        const el = en.target;
        countIO.unobserve(el);
        const target = parseFloat(el.dataset.countup);
        const dec = parseInt(el.dataset.decimals || "0", 10);
        const prefix = el.dataset.prefix || "";
        const suffix = el.dataset.suffix || "";
        const group = el.dataset.group === "1";
        if (isNaN(target)) return;
        const dur = 1400;
        const t0 = performance.now();
        const step = (t) => {
          const p = Math.min((t - t0) / dur, 1);
          const eased = 1 - Math.pow(1 - p, 4);
          el.textContent = fmt(target * eased, dec, prefix, suffix, group);
          if (p < 1) requestAnimationFrame(step);
        };
        requestAnimationFrame(step);
      });
    }, { threshold: 0.4 });
    document.querySelectorAll("[data-countup]").forEach((el) => countIO.observe(el));

    /* ---------- button ripple ---------- */
    document.addEventListener("pointerdown", (e) => {
      const btn = e.target.closest(".btn");
      if (!btn) return;
      const r = btn.getBoundingClientRect();
      const rip = document.createElement("span");
      const size = Math.max(r.width, r.height);
      rip.className = "ripple";
      rip.style.width = rip.style.height = size + "px";
      rip.style.left = e.clientX - r.left - size / 2 + "px";
      rip.style.top = e.clientY - r.top - size / 2 + "px";
      btn.appendChild(rip);
      setTimeout(() => rip.remove(), 700);
    });

    /* ---------- table row stagger ---------- */
    document.querySelectorAll("table.data tbody").forEach((tb) => {
      Array.from(tb.children).forEach((tr, i) => tr.style.setProperty("--i", Math.min(i, 18)));
    });

    /* ---------- KPI stagger ---------- */
    document.querySelectorAll(".kpi-grid").forEach((grid) => {
      Array.from(grid.children).forEach((k, i) => k.querySelector(".kpi-value")?.style.setProperty("--d", i * 90 + "ms"));
    });

    /* ---------- hero rotating word ---------- */
    const rot = document.getElementById("rotator");
    if (rot) {
      const words = (rot.dataset.words || "").split("|").filter(Boolean);
      let idx = 0;
      const span = rot.firstElementChild;
      setInterval(() => {
        idx = (idx + 1) % words.length;
        span.classList.add("out");
        setTimeout(() => {
          span.textContent = words[idx];
          span.classList.remove("out");
          span.classList.add("enter");
          requestAnimationFrame(() => requestAnimationFrame(() => span.classList.remove("enter")));
        }, 480);
      }, 3800);
    }

    /* ---------- testimonials carousel ---------- */
    const testis = Array.from(document.querySelectorAll(".testi"));
    if (testis.length) {
      const dots = Array.from(document.querySelectorAll(".testi-dots button"));
      let cur = 0, timer = null;
      const show = (i) => {
        testis[cur].classList.remove("active");
        dots[cur]?.classList.remove("active");
        cur = i;
        testis[cur].classList.add("active");
        dots[cur]?.classList.add("active");
      };
      const auto = () => { timer = setInterval(() => show((cur + 1) % testis.length), 5600); };
      dots.forEach((d, i) => d.addEventListener("click", () => { clearInterval(timer); show(i); auto(); }));
      show(0); auto();
    }

    /* ---------- room-board SSE: flash changed tiles ---------- */
    const board = document.querySelector(".room-grid-board");
    if (board && window.EventSource) {
      const stream = document.getElementById("room-stream-url");
      if (stream) {
        const prev = {};
        const src = new EventSource(stream.dataset.url);
        const live = document.querySelector(".pms-head .live");
        const streamState = (online) => {
          live?.classList.toggle("offline", !online);
          if (live) live.title = online ? "Room statuses are updating live" : "Live connection lost — reconnecting";
        };
        src.onopen = () => streamState(true);
        src.onerror = () => streamState(false);
        window.addEventListener("pagehide", () => src.close(), { once: true });
        src.onmessage = (e) => {
          const filtered = /[?&]status=/.test(location.search);
          if (filtered) { clearTimeout(src._rt); src._rt = setTimeout(() => location.reload(), 2500); return; }
          const tileClass = { vacant_clean: "vc", vacant_dirty: "vd", occupied_clean: "oc", occupied_dirty: "od", maintenance: "mm", out_of_order: "oo" };
          const toneClass = { vacant_clean: "success", vacant_dirty: "warning", occupied_clean: "info", occupied_dirty: "violet", maintenance: "danger", out_of_order: "danger" };
          let payload;
          try { payload = JSON.parse(e.data); } catch (_) { return; }
          if (!Array.isArray(payload)) return;
          payload.forEach((r) => {
            const tile = document.querySelector('[data-room-id="' + r.id + '"]');
            if (!tile) return;
            if (prev[r.id] && prev[r.id] !== r.status) {
              tile.classList.remove("flash");
              void tile.offsetWidth;
              tile.classList.add("flash");
            }
            prev[r.id] = r.status;
            tile.className = "room-tile " + tileClass[r.status] + (tile.classList.contains("flash") ? " flash" : "");
            const badge = tile.querySelector("[data-status-badge]");
            if (badge) {
              badge.className = "badge badge-" + toneClass[r.status];
              badge.style.fontSize = "10.5px"; badge.style.padding = "2px 8px";
              badge.textContent = r.label;
            }
          });
        };
      }
    }

    /* ---------- confirmation confetti ---------- */
    if (document.body.dataset.confetti) {
      const colors = ["#c3a15a", "#d9bd7e", "#0e1a2f", "#e8cf94", "#8a6d2f", "#ffffff"];
      for (let i = 0; i < 60; i++) {
        const c = document.createElement("span");
        c.className = "confetti-piece";
        c.style.left = Math.random() * 100 + "vw";
        c.style.background = colors[i % colors.length];
        c.style.setProperty("--x", (Math.random() * 220 - 110) + "px");
        c.style.setProperty("--r", (Math.random() * 900 + 260) + "deg");
        c.style.setProperty("--t", (Math.random() * 1.8 + 2.2) + "s");
        c.style.setProperty("--dl", (Math.random() * 0.9) + "s");
        c.style.borderRadius = Math.random() > 0.5 ? "2px" : "50%";
        document.body.appendChild(c);
        setTimeout(() => c.remove(), 5200);
      }
    }
  });

  /* ---------- staff new-booking live price preview ---------- */
  document.addEventListener("DOMContentLoaded", () => {
    const nb = document.getElementById("new-booking-form");
    if (!nb) return;
    const out = document.getElementById("price-preview");
    const fields = ["room_type", "check_in", "check_out", "rooms_count"];
    let timer = null;
    const refresh = () => {
      const v = {};
      fields.forEach((f) => (v[f] = nb.elements[f] ? nb.elements[f].value : ""));
      if (!v.room_type || !v.check_in || !v.check_out) return;
      const params = new URLSearchParams({
        room_type: v.room_type, check_in: v.check_in, check_out: v.check_out, rooms: v.rooms_count || 1,
      });
      clearTimeout(timer);
      timer = setTimeout(async () => {
        try {
          const r = await fetch(window.PRICE_API + "?" + params.toString());
          if (!r.ok) return;
          const d = await r.json();
          if (out) {
            out.style.opacity = "0.4";
            setTimeout(() => {
              out.innerHTML =
                '<div class="summary-line"><span>Rooms subtotal (' + d.night_count + ' nights × ' + d.rooms + ')</span><b>$' + d.subtotal + "</b></div>" +
                '<div class="summary-line"><span>Service (5%)</span><b>$' + d.service + "</b></div>" +
                '<div class="summary-line"><span>Tax (10%)</span><b>$' + d.tax + "</b></div>" +
                '<div class="summary-line total"><span>Total</span><b>$' + d.total + "</b></div>" +
                '<div class="summary-line"><span>Available now</span><span class="badge badge-' + (d.available > 0 ? "success" : "danger") + '">' + d.available + " rooms</span></div>";
              out.style.transition = "opacity .35s";
              out.style.opacity = "1";
            }, 140);
          }
        } catch (e) { /* offline: skip silently */ }
      }, 320);
    };
    fields.forEach((f) => nb.elements[f] && nb.elements[f].addEventListener("change", refresh));
    refresh();
  });
})();

/* ---- iOS bottom-sheet mobile menu ---- */
(function () {
  var sheet = document.querySelector(".mm-sheet"),
      scrim = document.querySelector(".mm-scrim"),
      burger = document.querySelector("[data-mmenu]");
  if (!sheet || !scrim || !burger) return;
  function openM() {
    scrim.classList.add("on"); sheet.classList.add("on");
    burger.setAttribute("aria-expanded", "true");
    document.body.classList.add("ui-locked");
  }
  function closeM() {
    scrim.classList.remove("on"); sheet.classList.remove("on");
    burger.setAttribute("aria-expanded", "false");
    document.body.classList.remove("ui-locked");
  }
  burger.addEventListener("click", openM);
  scrim.addEventListener("click", closeM);
  sheet.querySelectorAll("[data-mclose]").forEach(function (el) { el.addEventListener("click", closeM); });
  sheet.querySelectorAll("a").forEach(function (a) { a.addEventListener("click", closeM); });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape") closeM(); });
})();

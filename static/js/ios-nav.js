/* iOS-style page transitions: cross-fade + slide on same-origin
   navigations, with bfcache (back/forward) handling and a
   prefers-reduced-motion guard. Loaded with defer on every page. */
(function () {
  var html = document.documentElement;
  var reduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  html.classList.add("ios-nav");

  function enter() {
    if (reduced) { html.classList.remove("leaving", "entering"); return; }
    html.classList.remove("leaving");
    html.classList.add("entering");
    setTimeout(function () { html.classList.remove("entering"); }, 380);
  }
  enter();

  /* Back/forward cache can restore the old DOM, including a transition layer
     that was added just before the previous page left. Always clean it up on
     pageshow so a restored page can never be trapped behind "Loading…". */
  window.addEventListener("pageshow", function () {
    document.querySelectorAll(".ios-load").forEach(function (node) { node.remove(); });
    html.classList.remove("leaving", "entering");
  });

  function showLoad() {
    if (reduced || document.querySelector(".ios-load")) return;
    var ov = document.createElement("div");
    ov.className = "ios-load";
    ov.innerHTML = '<span class="ios-load-bar"></span>' +
      '<span class="ios-load-chip"><span class="ios-spin"></span>Loading…</span>';
    document.body.appendChild(ov);
    setTimeout(function () { ov.classList.add("chip"); }, 420);
  }

  /* boot splash: brief branded veil while first paint settles */
  if (!reduced) {
    var boot = document.createElement("div");
    boot.className = "ios-boot";
    boot.innerHTML = '<span class="ios-boot-mark" aria-hidden="true"></span>' +
      '<span class="ios-boot-name">Aurelia Collection</span>';
    document.body.appendChild(boot);
    requestAnimationFrame(function () {
      requestAnimationFrame(function () { boot.classList.add("out"); });
    });
    setTimeout(function () { boot.remove(); }, 640);
  }

  function leave(then) {
    showLoad();
    if (reduced) { then(); return; }
    if (html.classList.contains("leaving")) { then(); return; }
    html.classList.add("leaving");
    setTimeout(then, 130);
  }

  /* links */
  document.addEventListener("click", function (e) {
    if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    var a = e.target && e.target.closest ? e.target.closest("a[href]") : null;
    if (!a) return;
    if (a.target && a.target !== "_self") return;
    if (a.hasAttribute("download") || a.hasAttribute("data-no-transition")) return;
    var url;
    try { url = new URL(a.href, location.href); } catch (err) { return; }
    if (url.origin !== location.origin) return;
    if (url.pathname === location.pathname && url.search === location.search) {
      /* Same-page hash links keep native smooth scrolling and focus behavior. */
      if (url.hash !== location.hash) return;
      e.preventDefault();
      return;
    }
    e.preventDefault();
    leave(function () { window.location.assign(url.href); });
  });

  /* GET forms (search dock, room-detail dates, PMS filters) */
  document.addEventListener("submit", function (e) {
    if (e.defaultPrevented) return;
    var f = e.target;
    if (!f || (f.getAttribute("method") || "get").toLowerCase() !== "get") return;
    if (f.hasAttribute("data-noanim")) return;
    e.preventDefault();
    leave(function () { f.submit(); });
  });
})();

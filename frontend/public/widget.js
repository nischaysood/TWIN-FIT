/**
 * TwinFit Embed Widget — B2B integration in one line.
 *
 * Retailer adds to any product page:
 *   <script src="https://YOUR-TWINFIT-DOMAIN/widget.js"
 *           data-brand="myntra" defer></script>
 * and marks product images with:
 *   <img src="..." data-twinfit>
 * A "Try It On" button appears under each marked image; clicking opens
 * TwinFit in a modal with the garment pre-loaded.
 */
(function () {
  var script = document.currentScript;
  var APP = (script && script.getAttribute("data-app")) || script.src.replace(/\/widget\.js.*$/, "");
  var BRAND = (script && script.getAttribute("data-brand")) || "generic";

  function makeButton(imgUrl) {
    var btn = document.createElement("button");
    btn.textContent = "✨ Try It On";
    btn.setAttribute("aria-label", "Virtual try-on with TwinFit");
    btn.style.cssText = [
      "display:block", "margin-top:8px", "padding:10px 18px",
      "background:#1E3A5F", "color:#fff", "border:none", "border-radius:8px",
      "font:600 14px/1 -apple-system,system-ui,sans-serif", "cursor:pointer",
      "box-shadow:0 2px 8px rgba(30,58,95,.3)",
    ].join(";");
    btn.onmouseenter = function () { btn.style.opacity = "0.88"; };
    btn.onmouseleave = function () { btn.style.opacity = "1"; };
    btn.onclick = function () { openModal(imgUrl); };
    return btn;
  }

  function openModal(imgUrl) {
    var overlay = document.createElement("div");
    overlay.style.cssText =
      "position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:999999;" +
      "display:flex;align-items:center;justify-content:center;padding:20px";

    var frame = document.createElement("iframe");
    frame.src = APP + "/?garment=" + encodeURIComponent(imgUrl) +
                "&brand=" + encodeURIComponent(BRAND) + "&embed=1";
    frame.style.cssText =
      "width:min(520px,100%);height:min(760px,95vh);border:none;" +
      "border-radius:16px;background:#fff;box-shadow:0 20px 60px rgba(0,0,0,.4)";

    var close = document.createElement("button");
    close.textContent = "✕";
    close.setAttribute("aria-label", "Close try-on");
    close.style.cssText =
      "position:absolute;top:16px;right:20px;width:36px;height:36px;" +
      "border-radius:50%;border:none;background:#fff;font-size:16px;cursor:pointer";
    close.onclick = function () { document.body.removeChild(overlay); };
    overlay.onclick = function (e) { if (e.target === overlay) close.onclick(); };

    overlay.appendChild(frame);
    overlay.appendChild(close);
    document.body.appendChild(overlay);
  }

  function init() {
    var targets = document.querySelectorAll("[data-twinfit]");
    for (var i = 0; i < targets.length; i++) {
      var el = targets[i];
      if (el.getAttribute("data-twinfit-done")) continue;
      el.setAttribute("data-twinfit-done", "1");
      var imgUrl = el.getAttribute("data-twinfit") || el.src || el.getAttribute("data-src");
      if (!imgUrl || imgUrl === "") imgUrl = el.src;
      el.insertAdjacentElement("afterend", makeButton(imgUrl));
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();

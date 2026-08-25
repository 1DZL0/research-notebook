(function () {
  "use strict";

  var mount = document.getElementById("hub");
  var data = window.HUB_DATA;
  if (!mount || !data || !data.sections.length) return;

  var NS = "http://www.w3.org/2000/svg";
  var W = 780, H = 530, CX = 390, CY = 265, R = 152, CHILD = 96;
  var sections = data.sections.slice().sort(function (a, b) { return a.order - b.order; });
  var openId = null;
  var showParked = false;

  function e(tag, attrs) {
    var n = document.createElementNS(NS, tag);
    for (var k in attrs) n.setAttribute(k, attrs[k]);
    return n;
  }

  function angleFor(i) {
    return (-Math.PI / 2) + (i * 2 * Math.PI / sections.length);
  }

  mount.innerHTML =
    '<div class="hub-controls">' +
      '<label class="hub-toggle"><input type="checkbox" id="hub-parked"> Show parked</label>' +
      '<button type="button" id="hub-reset" class="hub-btn">Show all</button>' +
    '</div>' +
    '<svg id="hub-svg" viewBox="0 0 ' + W + ' ' + H + '" role="img" ' +
      'aria-label="Section map. A full list of entries follows below."></svg>' +
    '<div id="hub-brief" class="hub-brief" role="status" aria-live="polite"></div>';

  var svg = document.getElementById("hub-svg");
  var brief = document.getElementById("hub-brief");
  var gEdges = e("g", { "class": "hub-edges" });
  var gKids = e("g", {});
  var gMains = e("g", {});

  function clearBrief() {
    if (openId) return;
    brief.innerHTML = '<p class="hub-brief-empty">Nothing selected. Hover or click a node.</p>';
  }

  function renderSpotlight(section, kids) {
    var top = kids.slice(0, 3);
    var list = top.map(function (entry) {
      var desc = entry.description || "Open this entry to see the current notes and status.";
      return (
        '<li class="hub-spotlight-item">' +
          '<a class="hub-spotlight-link" href="' + entry.url + '">' + entry.title + "</a>" +
          ' <span class="status-badge status-' + entry.status + '">' + entry.status + "</span>" +
          '<p class="hub-spotlight-desc">' + desc + "</p>" +
        "</li>"
      );
    }).join("");

    var helper = kids.length > 3 ? ('<p class="hub-spotlight-more">' + (kids.length - 3) + ' more entries in this section.</p>') : "";
    brief.innerHTML =
      '<div class="hub-spotlight">' +
        '<div class="hub-spotlight-head">' +
          '<span class="hub-brief-title">' + section.label + '</span>' +
          '<span class="hub-spotlight-count">' + kids.length + (kids.length === 1 ? ' entry' : ' entries') + '</span>' +
        '</div>' +
        '<p class="hub-brief-body">' + section.blurb + "</p>" +
        '<ul class="hub-spotlight-list">' + list + "</ul>" +
        helper +
      "</div>";
  }

  function setBrief(title, badge, body, href) {
    var head = '<span class="hub-brief-title">' + title + '</span>';
    if (badge) head += ' <span class="status-badge status-' + badge + '">' + badge + '</span>';
    var tail = href ? ' <a class="hub-brief-link" href="' + href + '">Open entry &rarr;</a>' : '';
    brief.innerHTML = '<div class="hub-brief-head">' + head + '</div>' +
      '<p class="hub-brief-body">' + (body || "") + tail + '</p>';
  }

  function visibleEntries(s) {
    return showParked ? s.entries : s.entries.filter(function (x) { return x.status !== "parked"; });
  }

  function collapse() {
    openId = null;
    gKids.textContent = "";
    svg.classList.remove("is-focused");
    Array.prototype.forEach.call(gMains.children, function (g) { g.classList.remove("is-dim", "is-open"); });
    clearBrief();
  }

  function expand(section, index) {
    if (openId === section.id) { collapse(); return; }
    openId = section.id;
    gKids.textContent = "";

    var kids = visibleEntries(section);
    var base = angleFor(index);
    var spread = Math.min(0.46, 1.5 / Math.max(kids.length, 1));
    var px = CX + Math.cos(base) * R, py = CY + Math.sin(base) * R;

    kids.forEach(function (entry, i) {
      var a = base + (i - (kids.length - 1) / 2) * spread;
      var x = px + Math.cos(a) * CHILD, y = py + Math.sin(a) * CHILD;
      var g = e("g", { "class": "hub-kid", tabindex: "0", role: "link", style: "color:" + section.color });

      g.appendChild(e("path", { d: "M" + px + "," + py + " L" + x + "," + y, "class": "hub-kid-edge", stroke: section.color }));
      g.appendChild(e("circle", { cx: x, cy: y, r: 22, fill: "transparent" }));
      g.appendChild(e("circle", { cx: x, cy: y, r: 6.5, "class": "hub-kid-dot" }));

      var right = Math.cos(a) >= -0.15;
      var label = e("text", {
        x: x + (right ? 14 : -14), y: y + 4,
        "text-anchor": right ? "start" : "end", "class": "hub-kid-label"
      });
      label.textContent = entry.title.length > 34 ? entry.title.slice(0, 33) + "\u2026" : entry.title;
      g.appendChild(label);

      var title = e("title", {});
      title.textContent = entry.title;
      g.appendChild(title);

      function show() { setBrief(entry.title, entry.status, entry.description, entry.url); }
      function go() { window.location.href = entry.url; }
      g.addEventListener("mouseenter", show);
      g.addEventListener("focus", show);
      g.addEventListener("click", function (ev) { ev.stopPropagation(); go(); });
      g.addEventListener("keydown", function (ev) {
        if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); go(); }
      });
      gKids.appendChild(g);
    });

    svg.classList.add("is-focused");
    Array.prototype.forEach.call(gMains.children, function (g) {
      var mine = g.getAttribute("data-id") === section.id;
      g.classList.toggle("is-dim", !mine);
      g.classList.toggle("is-open", mine);
    });
    renderSpotlight(section, kids);
  }

  sections.forEach(function (s, i) {
    var a = angleFor(i);
    var x = CX + Math.cos(a) * R, y = CY + Math.sin(a) * R;
    var mx = CX + Math.cos(a) * R * 0.5, my = CY + Math.sin(a) * R * 0.5;
    var bow = 16;
    gEdges.appendChild(e("path", {
      stroke: s.color,
      d: "M" + CX + "," + CY + " Q" + (mx - Math.sin(a) * bow) + "," + (my + Math.cos(a) * bow) + " " + x + "," + y
    }));

    var cosA = Math.cos(a), sinA = Math.sin(a);
    var anchor = cosA > 0.34 ? "start" : cosA < -0.34 ? "end" : "middle";
    var lx = x + (anchor === "start" ? 27 : anchor === "end" ? -27 : 0);
    var ly = y + (anchor === "middle" ? (sinA > 0 ? 42 : -30) : 5);

    var g = e("g", { "class": "hub-main", "data-id": s.id, tabindex: "0", role: "button" });
    g.appendChild(e("circle", { cx: x, cy: y, r: 30, fill: "transparent" }));
    g.appendChild(e("circle", { cx: x, cy: y, r: 10.5, "class": "hub-main-dot", fill: s.color, stroke: s.color }));

    var label = e("text", { x: lx, y: ly, "text-anchor": anchor, "class": "hub-main-label" });
    label.textContent = s.label;
    g.appendChild(label);

    var count = e("tspan", { "class": "hub-main-count" });
    count.textContent = "  " + visibleEntries(s).length;
    label.appendChild(count);

    function peek() { if (!openId) setBrief(s.label, null, s.blurb); }
    g.addEventListener("mouseenter", peek);
    g.addEventListener("focus", peek);
    g.addEventListener("mouseleave", clearBrief);
    g.addEventListener("click", function (ev) { ev.stopPropagation(); expand(s, i); });
    g.addEventListener("keydown", function (ev) {
      if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); expand(s, i); }
      if (ev.key === "Escape") collapse();
    });
    gMains.appendChild(g);
  });

  svg.appendChild(gEdges);
  svg.appendChild(gKids);
  svg.appendChild(e("circle", { cx: CX, cy: CY, r: 10, "class": "hub-core" }));
  svg.appendChild(gMains);

  svg.addEventListener("click", collapse);
  document.getElementById("hub-reset").addEventListener("click", collapse);
  document.getElementById("hub-parked").addEventListener("change", function () {
    showParked = this.checked;
    Array.prototype.forEach.call(gMains.children, function (g, i) {
      g.querySelector(".hub-main-count").textContent = "  " + visibleEntries(sections[i]).length;
    });
    var was = openId;
    collapse();
    if (was) {
      sections.forEach(function (s, i) { if (s.id === was) expand(s, i); });
    }
  });

  function openFromHash() {
    var want = (window.location.hash || "").replace("#", "");
    if (!want) return false;
    for (var i = 0; i < sections.length; i++) {
      if (sections[i].id === want) { expand(sections[i], i); return true; }
    }
    return false;
  }

  window.addEventListener("hashchange", function () {
    if (!openFromHash()) collapse();
  });

  if (!openFromHash()) clearBrief();
})();

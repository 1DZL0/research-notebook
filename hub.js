
(function () {
  "use strict";

  var mount = document.getElementById("hub");
  var data = window.HUB_DATA;
  if (!mount || !data || !data.sections.length) return;

  var NS = "http://www.w3.org/2000/svg";
  var W = 780, H = 530, CX = 390, CY = 265, R = 152;
  var sections = data.sections.slice().sort(function (a, b) { return a.order - b.order; });
  var openId = null;



  // Deterministic per-index variety so arms don't read as a perfect, mechanical
  // circle. Values are hand-tuned offsets, not randomised, so the layout is
  // stable across renders.
  var ANGLE_JITTER = [-16, 20, -9, 24, -22, 12, -6];
  var RADIUS_JITTER = [-30, 26, -14, 34, -26, 16, 8];
  var TWIST_JITTER = [14, -22, 18, -12, 24, -16, 10];

  function e(tag, attrs) {
    var n = document.createElementNS(NS, tag);
    for (var k in attrs) n.setAttribute(k, attrs[k]);
    return n;
  }

  function angleFor(i) {
    var base = (-Math.PI / 2) + (i * 2 * Math.PI / sections.length);
    var jitter = (ANGLE_JITTER[i % ANGLE_JITTER.length] * Math.PI) / 180;
    return base + jitter;
  }

  function sectionPoint(i) {
    var a = angleFor(i);
    var radius = R + RADIUS_JITTER[i % RADIUS_JITTER.length];
    return {
      angle: a,
      radius: radius,
      x: CX + Math.cos(a) * radius,
      y: CY + Math.sin(a) * radius * 0.92
    };
  }

  mount.innerHTML =
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
    brief.innerHTML = '<p class="hub-brief-empty">All section entries are visible.</p>';
  }

  function clearBranchHighlight() {
    Array.prototype.forEach.call(gEdges.children, function (edge) {
      edge.classList.remove("is-highlighted");
    });
    Array.prototype.forEach.call(gKids.querySelectorAll(".hub-kid-edge"), function (edge) {
      edge.classList.remove("is-highlighted");
    });
  }

  function highlightBranch(sectionId, childEdge) {
    clearBranchHighlight();
    Array.prototype.forEach.call(gEdges.children, function (edge) {
      edge.classList.toggle("is-highlighted", edge.getAttribute("data-id") === sectionId);
    });
    childEdge.classList.add("is-highlighted");
  }

  function compactHubLabel(title) {
    var raw = (title || "").trim();
    if (!raw) return "";
    if (raw.indexOf("Research ") === 0) {
      return raw.replace(/^Research\s+/, "");
    }
    if (raw.indexOf("Project: ") === 0) {
      return raw.replace(/^Project:\s*/, "");
    }
    if (raw.indexOf("Experiment ") === 0) {
      return raw.replace(/^Experiment\s+\d+\s+[—-]\s*/, "");
    }
    return raw.length > 24 ? raw.slice(0, 21) + "…" : raw;
  }

  function renderExpandedSection(section, index) {
    var kids = visibleEntries(section);
    if (!kids.length) return;
    var parent = sectionPoint(index);
    var px = parent.x, py = parent.y;
    // Radiate children outward from the shared centre, like petals continuing
    // past the parent — angle *and* distance both grow with each child, so
    // separation only ever increases and labels can't stack on one another.
    // A lone child still gets nudged off the parent's own ray so it never
    // lands where the section label sits.
    var laneDir = (index % 2 === 0) ? 1 : -1;
    var angularStep = kids.length > 1 ? Math.min(0.3, 1.15 / kids.length) : 0;

    kids.forEach(function (entry, i) {
      var offset = kids.length > 1
        ? (i - (kids.length - 1) / 2) * angularStep
        : laneDir * 0.24;
      var a = parent.angle + offset;
      var radial = parent.radius + 74 + (i * 46);
      var x = CX + Math.cos(a) * radial;
      var y = CY + Math.sin(a) * radial * 0.92;
      var mx = (px + x) * 0.5;
      var my = (py + y) * 0.5;
      var dir = (i % 2 === 0) ? 1 : -1;
      var bend = 12 + (i * 4);
      var cx = mx - Math.sin(a) * bend * dir;
      var cy = my + Math.cos(a) * bend * dir;
      var g = e("g", { "class": "hub-kid", tabindex: "0", role: "link", style: "color:" + section.color });

      var childEdge = e("path", {
        d: "M" + px + "," + py + " Q" + cx + "," + cy + " " + x + "," + y,
        "class": "hub-kid-edge",
        stroke: section.color
      });
      g.appendChild(childEdge);
      g.appendChild(e("circle", { cx: x, cy: y, r: 22, fill: "transparent" }));
      g.appendChild(e("circle", { cx: x, cy: y, r: 10.5, "class": "hub-kid-halo", stroke: section.color }));
      g.appendChild(e("circle", { cx: x, cy: y, r: 6.8, "class": "hub-kid-dot" }));

      var right = Math.cos(a) >= -0.05;
      var shortTitle = compactHubLabel(entry.title);
      var label = e("text", {
        x: x + (right ? 15 : -15), y: y + 4,
        "text-anchor": right ? "start" : "end", "class": "hub-kid-label"
      });
      label.textContent = shortTitle;
      g.appendChild(label);

      var title = e("title", {});
      title.textContent = entry.title;
      g.appendChild(title);

      function show() {
        setBrief(entry.title, entry.description, entry.url);
        highlightBranch(section.id, childEdge);
      }
      function hide() {
        clearBranchHighlight();
        clearBrief();
      }
      function go() { window.location.href = entry.url; }
      g.addEventListener("mouseenter", show);
      g.addEventListener("focus", show);
      g.addEventListener("mouseleave", hide);
      g.addEventListener("blur", hide);
      g.addEventListener("click", function (ev) { ev.stopPropagation(); go(); });
      g.addEventListener("keydown", function (ev) {
        if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); go(); }
      });
      gKids.appendChild(g);
    });
  }

  function renderSpotlight(section, kids) {
    var top = kids.slice(0, 3);
    var list = top.map(function (entry) {
      var desc = entry.description || "Open this entry to see the current notes and status.";
      return (
        '<li class="hub-spotlight-item">' +
        '<a class="hub-spotlight-link" href="' + entry.url + '">' + entry.title + "</a>" +
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

  function setBrief(title, body, href) {
    var head = '<span class="hub-brief-title">' + title + '</span>';
    var tail = href ? ' <a class="hub-brief-link" href="' + href + '">Open entry &rarr;</a>' : '';
    brief.innerHTML = '<div class="hub-brief-head">' + head + '</div>' +
      '<p class="hub-brief-body">' + (body || "") + tail + '</p>';
  }

  function visibleEntries(s) {
    return s.entries;
  }

  function escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, function (character) {
      return {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
      }[character];
    });
  }

  function renderNotebookIndex() {
    var index = document.getElementById("notebook-index");
    if (!index) return;

    index.innerHTML = sections.map(function (section) {
      var entries = visibleEntries(section);
      var links = entries.map(function (entry) {
        return '<li><a href="' + escapeHtml(entry.url) + '">' +
          escapeHtml(entry.title) + "</a></li>";
      }).join("");

      return '<section class="notebook-index-section" style="--index-colour:' +
        escapeHtml(section.color) + '">' +
        '<div class="notebook-index-heading">' +
          '<h3><span class="notebook-index-mark" aria-hidden="true"></span>' +
          escapeHtml(section.label) + "</h3>" +
          '<span class="notebook-index-count">' + entries.length +
          (entries.length === 1 ? " note" : " notes") + "</span>" +
        "</div>" +
        '<ul class="notebook-index-links">' + links + "</ul>" +
      "</section>";
    }).join("");
  }

  function collapse() {
    openId = null;
    clearBrief();
    Array.prototype.forEach.call(gMains.children, function (g) {
      g.classList.remove("is-dim", "is-open");
    });
  }

  function expand(section, index) {
    openId = section.id;
    setBrief(section.label, section.blurb);
    Array.prototype.forEach.call(gMains.children, function (g) {
      g.classList.remove("is-dim", "is-open");
    });
    if (index >= 0) {
      var kids = visibleEntries(section);
      renderSpotlight(section, kids);
    }
  }

  sections.forEach(function (s, i) {
    var point = sectionPoint(i);
    var a = point.angle;
    var x = point.x, y = point.y;
    var twist = 20 + TWIST_JITTER[i % TWIST_JITTER.length];
    var c1x = CX + Math.cos(a - 0.5) * (point.radius * 0.42);
    var c1y = CY + Math.sin(a - 0.5) * (point.radius * 0.34);
    var c2x = x - Math.cos(a + 0.2) * twist;
    var c2y = y - Math.sin(a + 0.2) * twist;
    gEdges.appendChild(e("path", {
      stroke: s.color,
      "data-id": s.id,
      d: "M" + CX + "," + CY + " C" + c1x + "," + c1y + " " + c2x + "," + c2y + " " + x + "," + y
    }));

    var cosA = Math.cos(a), sinA = Math.sin(a);
    var anchor = cosA > 0.34 ? "start" : cosA < -0.34 ? "end" : "middle";
    var lx = x + (anchor === "start" ? 27 : anchor === "end" ? -27 : 0);
    var ly = y + (anchor === "middle" ? (sinA > 0 ? 42 : -30) : 5);

    var g = e("g", { "class": "hub-main", "data-id": s.id, tabindex: "0", role: "button" });
    g.appendChild(e("circle", { cx: x, cy: y, r: 30, fill: "transparent" }));
    g.appendChild(e("circle", { cx: x, cy: y, r: 16.5, "class": "hub-main-halo", stroke: s.color }));
    g.appendChild(e("circle", { cx: x, cy: y, r: 10.4, "class": "hub-main-dot", fill: s.color, stroke: s.color }));

    var label = e("text", { x: lx, y: ly, "text-anchor": anchor, "class": "hub-main-label" });
    label.textContent = s.label;
    g.appendChild(label);

    var count = e("tspan", { "class": "hub-main-count" });
    count.textContent = "  " + visibleEntries(s).length;
    label.appendChild(count);

    function peek() { if (!openId) setBrief(s.label, s.blurb); }
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
  svg.appendChild(e("circle", { cx: CX, cy: CY, r: 26, "class": "hub-core" }));
  var coreMonogram = e("text", {
    x: CX,
    y: CY + 9,
    "text-anchor": "middle",
    "class": "hub-core-monogram",
    "aria-label": "Phi, the Greek initial of Phronesis"
  });
  coreMonogram.textContent = "Φ";
  svg.appendChild(coreMonogram);
  svg.appendChild(gMains);

  svg.addEventListener("click", collapse);

  function openFromHash() {
    return false;
  }

  window.addEventListener("hashchange", function () {
    if (!openFromHash()) collapse();
  });

  if (!openFromHash()) {
    gKids.textContent = "";
    sections.forEach(function (section, index) { renderExpandedSection(section, index); });
    clearBrief();
    Array.prototype.forEach.call(gMains.children, function (g) {
      g.classList.remove("is-dim", "is-open");
    });
  }
  renderNotebookIndex();
})();

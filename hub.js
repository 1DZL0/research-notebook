
(function () {
  "use strict";

  var mount = document.getElementById("hub");
  var data = window.HUB_DATA;
  if (!mount || !data || !data.sections.length) return;

  var NS = "http://www.w3.org/2000/svg";
  var W = 900, H = 400, CX = 450, CY = 285, R = 152, X_SPREAD = 1.22;
  var sections = data.sections.slice().sort(function (a, b) { return a.order - b.order; });
  var openId = null;



  var BRANCH_ANGLES = [-35, -106, 25, 150, -155, 125, 130];
  var TWIST_JITTER = [14, -22, 18, -12, 24, -16, 10];
  var BRANCH_RADII = [250, 170, 250, 245, 250];
  var MAIN_LABEL_OFFSETS = [[0, 38], [0, 36], [0, -26], [0, -26], [0, 36], [0, -26]];
  var DEFAULT_BRANCH_LAYOUT = {
    "03-experiments": { x: 222.5, y: 144.8 },
    "04-meetings": { x: 340.2, y: 299.4 },
    "01-literature": { x: 322.2, y: 116.7 },
    "02-projects": { x: 601.3, y: 297.2 },
    "06-thinking": { x: 432.1, y: 205.3 }
  };
  var DEFAULT_CHILD_LAYOUT = {
    "01-literature:01-literature/papers.html": { x: 299.8, y: 49.5 },
    "00-research:00-research/q1-note.html": { x: 743.7, y: 6.9 },
    "00-research:00-research/q2-note.html": { x: 668.6, y: 23.7 },
    "00-research:00-research/q3-note.html": { x: 591.2, y: 41.6 },
    "00-research:00-research/q4-note.html": { x: 519.5, y: 54.0 },
    "00-research:00-research/research-development.html": { x: 815.4, y: 159.3 },
    "00-research:00-research/research-roadmap.html": { x: 794.1, y: 94.3 },
    "00-research:00-research/thesis.html": { x: 533.0, y: 123.5 },
    "00-research:00-research/o2-self-relevant-action.html": { x: 650.0, y: 130.0 },
    "02-projects:02-projects/pharos-cy.html": { x: 642.8, y: 271.4 },
    "02-projects:02-projects/genai4ed.html": { x: 652.9, y: 329.7 },
    "03-experiments:03-experiments/prisoners-dilemma.html": { x: 140.7, y: 156.0 },
    "04-meetings:04-meetings/supervisor.html": { x: 280.8, y: 270.3 },
    "04-meetings:04-meetings/other-meetings.html": { x: 269.6, y: 319.6 },
    "06-thinking:06-thinking/log.html": { x: 426.5, y: 139.2 }
  };

  function e(tag, attrs) {
    var n = document.createElementNS(NS, tag);
    for (var k in attrs) n.setAttribute(k, attrs[k]);
    return n;
  }

  function angleFor(i) {
    return (BRANCH_ANGLES[i % BRANCH_ANGLES.length] * Math.PI) / 180;
  }

  function sectionPoint(i) {
    var saved = DEFAULT_BRANCH_LAYOUT[sections[i].id];
    if (saved && Number.isFinite(saved.x) && Number.isFinite(saved.y)) {
      var dx = (saved.x - CX) / X_SPREAD;
      var dy = (saved.y - CY) / 0.92;
      return {
        angle: Math.atan2(dy, dx),
        radius: Math.sqrt((dx * dx) + (dy * dy)),
        x: saved.x,
        y: saved.y
      };
    }

    var a = angleFor(i);
    var radius = BRANCH_RADII[i % BRANCH_RADII.length] || R;
    return {
      angle: a,
      radius: radius,
      x: CX + Math.cos(a) * radius * X_SPREAD,
      y: CY + Math.sin(a) * radius * 0.92
    };
  }

  mount.innerHTML =
    '<svg id="hub-svg" viewBox="0 0 ' + W + ' ' + H + '" role="img" ' +
    'aria-label="Section map. A full list of entries follows below."></svg>' +
    '<aside id="hub-tooltip" class="hub-tooltip" role="status" aria-live="polite"></aside>';

  var svg = document.getElementById("hub-svg");
  var tooltip = document.getElementById("hub-tooltip");
  var gEdges;
  var gKids;
  var gMains;

  function clearBrief() {
    tooltip.className = "hub-tooltip";
    tooltip.innerHTML = "";
  }

  function setBrief(title, body, x, y) {
    tooltip.className = "hub-tooltip is-visible";
    tooltip.style.left = ((x / W) * 100) + "%";
    tooltip.style.top = ((y / H) * 100) + "%";
    tooltip.innerHTML =
      '<strong class="hub-tooltip-title">' + escapeHtml(title) + "</strong>" +
      '<p class="hub-tooltip-body">' + escapeHtml(body || "Select this node to open the note.") + "</p>";
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
      var radial = parent.radius + 84 + (i * 44);
      var shortTitle = compactHubLabel(entry.title);
      var labelHalfWidth = Math.min(110, 10 + (shortTitle.length * 4.2));
      var x = CX + Math.cos(a) * radial * X_SPREAD;
      var y = CY + Math.sin(a) * radial * 0.92;
      var childId = section.id + ":" + entry.url;
      var saved = DEFAULT_CHILD_LAYOUT[childId];
      if (saved && Number.isFinite(saved.x) && Number.isFinite(saved.y)) {
        x = saved.x;
        y = saved.y;
      } else {
        x = Math.max(labelHalfWidth + 14, Math.min(W - labelHalfWidth - 14, x));
      }
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
      g.appendChild(e("circle", { cx: x, cy: y, r: 20, fill: "transparent" }));
      g.appendChild(e("circle", { cx: x, cy: y, r: 9.3, "class": "hub-kid-halo", stroke: section.color }));
      g.appendChild(e("circle", { cx: x, cy: y, r: 6, "class": "hub-kid-dot" }));

      var label = e("text", {
        x: x, y: y - 18,
        "text-anchor": "middle", "class": "hub-kid-label"
      });
      label.textContent = shortTitle;
      g.appendChild(label);

      var title = e("title", {});
      title.textContent = entry.title;
      g.appendChild(title);

      function show() {
        setBrief(entry.title, entry.description, x, y);
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
      g.addEventListener("click", function (ev) {
        ev.stopPropagation();
        go();
      });
      g.addEventListener("keydown", function (ev) {
        if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); go(); }
      });
      gKids.appendChild(g);
    });
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
    Array.prototype.forEach.call(gMains.children, function (g) {
      g.classList.remove("is-dim", "is-open");
    });
  }

  function renderMap() {
    svg.textContent = "";
    gEdges = e("g", { "class": "hub-edges" });
    gKids = e("g", {});
    gMains = e("g", {});

    sections.forEach(function (s, i) {
      var point = sectionPoint(i);
      var a = point.angle;
      var x = point.x, y = point.y;
      var twist = 20 + TWIST_JITTER[i % TWIST_JITTER.length];
      var c1x = CX + Math.cos(a - 0.5) * (point.radius * 0.42) * X_SPREAD;
      var c1y = CY + Math.sin(a - 0.5) * (point.radius * 0.34);
      var c2x = x - Math.cos(a + 0.2) * twist;
      var c2y = y - Math.sin(a + 0.2) * twist;
      gEdges.appendChild(e("path", {
        stroke: s.color,
        "data-id": s.id,
        d: "M" + CX + "," + CY + " C" + c1x + "," + c1y + " " + c2x + "," + c2y + " " + x + "," + y
      }));

      var mainLabelOffset = MAIN_LABEL_OFFSETS[i % MAIN_LABEL_OFFSETS.length];
      var anchor = "middle";
      var lx = x + mainLabelOffset[0];
      var ly = y + mainLabelOffset[1];

      var g = e("g", { "class": "hub-main", "data-id": s.id, tabindex: "0", role: "button" });
      g.appendChild(e("circle", { cx: x, cy: y, r: 18, fill: "transparent" }));
      g.appendChild(e("circle", { cx: x, cy: y, r: 10, "class": "hub-main-halo", stroke: s.color }));
      g.appendChild(e("circle", { cx: x, cy: y, r: 6.4, "class": "hub-main-dot", fill: s.color, stroke: s.color }));

      var label = e("text", { x: lx, y: ly, "text-anchor": anchor, "class": "hub-main-label" });
      label.textContent = s.label;
      g.appendChild(label);

      function peek() { setBrief(s.label, s.blurb, x, y); }
      g.addEventListener("mouseenter", peek);
      g.addEventListener("focus", peek);
      g.addEventListener("mouseleave", clearBrief);
      g.addEventListener("click", function (ev) {
        ev.stopPropagation();
        expand(s, i);
      });
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
      y: CY + 10,
      "text-anchor": "middle",
      "class": "hub-core-monogram",
      "aria-label": "Phi, the Greek initial of Phronesis"
    });
    coreMonogram.textContent = "Φ";
    svg.appendChild(coreMonogram);
    svg.appendChild(gMains);
    sections.forEach(function (section, index) { renderExpandedSection(section, index); });
    clearBrief();
  }

  svg.addEventListener("click", collapse);

  function openFromHash() {
    return false;
  }

  window.addEventListener("hashchange", function () {
    if (!openFromHash()) collapse();
  });

  renderMap();
  renderNotebookIndex();
})();

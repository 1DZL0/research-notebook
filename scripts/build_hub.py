#!/usr/bin/env python3
"""Scan entry front matter and emit hub-data.js for the landing-page graph.

Run automatically by Quarto before each render (see `pre-render` in _quarto.yml).
Nothing here needs editing except SECTIONS.
"""

import json
import pathlib
import re
import sys

try:
    import yaml
except ImportError:
    sys.exit("PyYAML is required:  pip install pyyaml")

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "_hub-include.html"

# folder -> (label shown on the node, order around the circle)
SECTIONS = {
    "00-research":    ("Research", 0, "#4A3A7A"),
    "01-literature":  ("Literature", 1, "#356D9A"),
    "02-projects":    ("Projects", 2, "#8F5F30"),
    "03-experiments": ("Experiments", 3, "#8A3E4E"),
    "04-meetings":    ("Meetings", 4, "#59636E"),
    "05-reference":   ("Reference", 5, "#6B6440"),
}

# one-line briefing shown when a section node is hovered
BLURBS = {
    "Research": "Vision, live questions, and the roadmap.",
    "Literature": "Papers read, and the map connecting them.",
    "Projects": "Applied work where the ideas meet something real.",
    "Experiments": "Prototypes and evaluations, with results or an honest blank.",
    "Meetings": "Supervisor discussions and the decisions from them.",
    "Reference": "Definitions and metrics, written once and linked to.",
}

VALID_STATUS = {"question", "active", "evidence", "parked", "reference"}
FM = re.compile(r"\A\ufeff?---\s*\n(.*?)\n---\s*\n", re.S)
SKIP = {"index.qmd", "notebook.qmd"}


def front_matter(path):
    text = path.read_text(encoding="utf-8")
    match = FM.match(text)
    if not match:
        return None
    try:
        return yaml.safe_load(match.group(1)) or None
    except yaml.YAMLError as exc:
        print(f"  ! {path.name}: unreadable front matter ({exc})", file=sys.stderr)
        return None


def collect():
    sections = []
    for folder, (label, order, color) in sorted(SECTIONS.items(), key=lambda kv: kv[1][1]):
        directory = ROOT / folder
        if not directory.is_dir():
            continue

        entries = []
        for qmd in sorted(directory.glob("*.qmd")):
            if qmd.name in SKIP or qmd.name.startswith("_"):
                continue

            meta = front_matter(qmd)
            if not meta or not meta.get("title"):
                print(f"  - skipped {folder}/{qmd.name}: no title in front matter")
                continue

            status = str(meta.get("status", "active")).lower()
            if status not in VALID_STATUS:
                print(f"  ! {qmd.name}: unknown status '{status}', using 'active'")
                status = "active"

            entries.append({
                "title": meta["title"],
                "url": f"{folder}/{qmd.stem}.html",
                "status": status,
                "description": meta.get("description", ""),
                "date": str(meta.get("date", "")),
            })

        entries.sort(key=lambda e: e["date"], reverse=True)
        sections.append({
            "id": folder,
            "label": label,
            "order": order,
            "color": color,
            "blurb": BLURBS.get(label, ""),
            "entries": entries,
        })

    return [s for s in sections if s["entries"]]


BACKLINK = """
<script>
(function () {
  var d = window.HUB_DATA;
  if (!d) return;
  var parts = window.location.pathname.split("/").filter(Boolean);
  var folder = parts.length > 1 ? parts[parts.length - 2] : null;
  var section = null;
  for (var i = 0; i < d.sections.length; i++) {
    if (d.sections[i].id === folder) section = d.sections[i];
  }
  if (!section) return;
  document.addEventListener("DOMContentLoaded", function () {
    var host = document.querySelector("#quarto-document-content") ||
               document.querySelector("main.content");
    if (!host) return;
    var a = document.createElement("a");
    a.className = "back-link";
    a.href = "../index.html#" + section.id;
    a.style.setProperty("--back-color", section.color);
    a.innerHTML = '<span aria-hidden="true">&larr;</span> ' + section.label;
    host.insertBefore(a, host.firstChild);
  });
})();
</script>
"""


def main():
    sections = collect()
    total = sum(len(s["entries"]) for s in sections)
    payload = json.dumps({"sections": sections}, indent=2, ensure_ascii=False)
    OUT.write_text(
        "<script>\nwindow.HUB_DATA = " + payload + ";\n</script>\n" + BACKLINK,
        encoding="utf-8",
    )
    print(f"_hub-include.html: {total} entries across {len(sections)} sections")


if __name__ == "__main__":
    main()

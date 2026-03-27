import csv
from utils import YEARS, nav_dropdown, escape_js

NOTES_CSV = "data_notes.csv"


def read_notes():
    notes = []
    with open(NOTES_CSV, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            notes.append({
                "year": int(row["year"].strip()),
                "category": row["category"].strip(),
                "note": row["note"].strip(),
            })
    return notes


def build_js_data(notes):
    lines = []
    for n in notes:
        lines.append(
            f'  {{year:{n["year"]},category:"{escape_js(n["category"])}",note:"{escape_js(n["note"])}"}}'
        )
    return "[\n" + ",\n".join(lines) + "\n]"


def build_page(notes):
    js_data = build_js_data(notes)

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Garden Notes - The Gardening Gals</title>
  <link rel="stylesheet" href="style.css" />
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=Lato:wght@300;400;700&display=swap" rel="stylesheet">
</head>
<body class="notes-page">
  <header>
    <div class="header-inner">
      <div class="header-icon"> </div>
      <h1>The Gardening Gals</h1>
      <p class="subtitle"><strong>Welcome to our online gardening journal!</strong></p>
    </div>
  </header>
  <nav>
    <ul>
      <li><a href="index.html">Home</a></li>
      <li class="dropdown">
        <a href="#">Layout</a>
        <ul class="dropdown-menu">
{nav_dropdown()}        </ul>
      </li>
      <li><a href="view_plant_list.html">Plant List</a></li>
      <li><a href="view_garden_notes.html">Garden Notes</a></li>
      <li><a href="about.html">About</a></li>
      <!-- <li><a href="view_varietals.html">Varietals</a></li> -->
    </ul>
  </nav>
  <main>
    <h1 class="page-title">Garden Notes</h1>

    <div class="garden-section-card" style="margin-bottom: 1.5rem;">
      <div class="notes-search-row">
        <div class="notes-search-box">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          <input id="notes-search" type="text" placeholder="Search notes... try &ldquo;pest&rdquo;, &ldquo;tomato&rdquo;, &ldquo;carrot&rdquo;" autocomplete="off" />
        </div>
      </div>
      <div class="notes-filter-row" id="notesFilterRow">
        <span class="notes-filter-label">Category:</span>
        <span class="notes-pill notes-pill-all active" data-cat="all">All</span>
      </div>
      <p class="notes-results-meta" id="notesResultsMeta"></p>
    </div>

    <div id="notesContainer"></div>

  </main>
  <footer>
    <p></p>
  </footer>

<script>
const NOTES = {js_data};

const allCats = [...new Set(NOTES.map(n => n.category))].sort();

const CAT_CLASS = {{
  "Pest":               "ncat-pest",
  "Soil":               "ncat-soil",
  "Planting":           "ncat-planting",
  "Infrastructure":     "ncat-infrastructure",
  "Harvest":            "ncat-harvest",
  "Water":              "ncat-water",
  "Plant choices":      "ncat-plant-choices",
  "Plant observations": "ncat-plant-obs",
  "Garden layout":      "ncat-garden-layout",
}};

function catClass(cat) {{
  return CAT_CLASS[cat] || "ncat-default";
}}

// Build category filter pills
const filterRow = document.getElementById("notesFilterRow");
allCats.forEach(cat => {{
  const pill = document.createElement("span");
  pill.className = "notes-pill";
  pill.dataset.cat = cat;
  pill.textContent = cat;
  filterRow.appendChild(pill);
}});

let activeCat = "all";
let searchQuery = "";

filterRow.addEventListener("click", e => {{
  if (!e.target.classList.contains("notes-pill")) return;
  activeCat = e.target.dataset.cat;
  document.querySelectorAll(".notes-pill").forEach(p =>
    p.classList.toggle("active", p.dataset.cat === activeCat)
  );
  render();
}});

document.getElementById("notes-search").addEventListener("input", e => {{
  searchQuery = e.target.value.trim().toLowerCase();
  render();
}});

function escHtml(t) {{
  return t.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}}

function highlight(text, query) {{
  if (!query) return escHtml(text);
  const escaped = escHtml(text);
  const re = new RegExp("(" + query.replace(/[.*+?^${{}}()|[\\]\\\\]/g, "\\\\$&") + ")", "gi");
  return escaped.replace(re, "<mark>$1</mark>");
}}

function render() {{
  const q = searchQuery;
  const cat = activeCat;

  const filtered = NOTES.filter(n => {{
    const matchCat = cat === "all" || n.category === cat;
    const matchQ = !q || n.note.toLowerCase().includes(q) || n.category.toLowerCase().includes(q);
    return matchCat && matchQ;
  }});

  const byYear = {{}};
  filtered.forEach(n => {{
    if (!byYear[n.year]) byYear[n.year] = [];
    byYear[n.year].push(n);
  }});

  const years = Object.keys(byYear).sort((a, b) => b - a);
  const container = document.getElementById("notesContainer");
  const meta = document.getElementById("notesResultsMeta");

  meta.textContent = filtered.length === NOTES.length
    ? NOTES.length + " notes total"
    : filtered.length + " of " + NOTES.length + " notes";

  if (filtered.length === 0) {{
    container.innerHTML = `<div class="garden-section-card" style="text-align:center;padding:2.5rem 1rem;">
      <p style="font-family:\'Playfair Display\',serif;font-size:1.2rem;color:var(--bark);">No notes found</p>
      <p style="color:var(--text-light);font-size:0.9rem;margin-top:0.5rem;">Try a different keyword or clear the search.</p>
    </div>`;
    return;
  }}

  container.innerHTML = years.map(year => `
    <h2 class="section-heading">${{year}}</h2>
    <div class="garden-section-card">
      <div class="notes-grid">
        ${{byYear[year].map(n => `
          <div class="note-card">
            <span class="note-cat-tag ${{catClass(n.category)}}">${{escHtml(n.category)}}</span>
            <p>${{highlight(n.note, q)}}</p>
          </div>`).join("")}}
      </div>
    </div>`).join("");
}}

render();
</script>
</body>
</html>'''


def main():
    notes = read_notes()
    html = build_page(notes)
    with open("view_garden_notes.html", "w", encoding="utf-8") as f:
        f.write(html)
    print(f"view_garden_notes.html generated successfully! ({len(notes)} notes)")


main()

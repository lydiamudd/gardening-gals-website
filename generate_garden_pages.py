import csv
from collections import defaultdict

# -------------------------------------------------------
# generate_garden_pages.py
# Reads planting_data.csv and generates a page for each year
# Usage: python3 generate_garden_pages.py
# -------------------------------------------------------

CSV_FILE = "planting_data.csv"
YEARS = [2022, 2023, 2024, 2025, 2026]

LOWER_BED_ORDER = ["One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Sunflower"]
UPPER_BED_ORDER = ["Strawberry", "Apple Terrace 1", "Apple Terrace 2", "Apple Terrace 3", "Apple Terrace 4", "Asparagus"]


def read_csv(year):
    lower = defaultdict(list)
    upper = defaultdict(list)
    with open(CSV_FILE, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if str(row["year"]).strip() != str(year):
                continue
            bed = row["bed_name"].strip()
            location = row["bed_location"].strip()
            plant = row["plant_name"].strip()
            season = row["season"].strip()
            if location == "Lower":
                lower[bed].append((plant, season))
            elif location == "Upper":
                upper[bed].append((plant, season))
    return lower, upper


def plant_lines(plants):
    lines = []
    for plant, season in plants:
        lines.append(f'<span class="plant-entry">{plant} <span class="season">({season})</span></span>')
    return "\n".join(lines)


def build_lower_map(lower):
    def bed(name):
        plants = lower.get(name, [])
        return f'''<div class="bed-card">
          <div class="bed-label">Bed {name}</div>
          <div class="plant-list">{plant_lines(plants)}</div>
        </div>'''

    sunflower_plants = lower.get("Sunflower", [])
    return f'''
      <div class="lower-garden-map">
        <div class="sunflower-bed">
          <div class="bed-label">Sunflower Bed</div>
          <div class="plant-list">{plant_lines(sunflower_plants)}</div>
        </div>
        <div class="lower-beds-grid">
          <div class="beds-row row-tall">
            {bed("One")}
            {bed("Two")}
            {bed("Three")}
            {bed("Four")}
          </div>
          <div class="beds-row row-wide">
            {bed("Five")}
            {bed("Six")}
          </div>
          <div class="beds-row row-wide">
            {bed("Seven")}
            {bed("Eight")}
          </div>
        </div>
      </div>'''


def build_upper_map(upper):
    def atbed(name):
        plants = upper.get(name, [])
        return f'''<div class="at-quadrant">
          <div class="bed-label">{name}</div>
          <div class="plant-list">{plant_lines(plants)}</div>
        </div>'''

    strawberry_plants = upper.get("Strawberry", [])
    asparagus_plants = upper.get("Asparagus", [])
    return f'''
      <div class="upper-garden-map">
        <div class="upper-bed strawberry-bed">
          <div class="bed-label">Strawberry Bed</div>
          <div class="plant-list">{plant_lines(strawberry_plants)}</div>
        </div>
        <div class="upper-bed apple-terrace-bed">
          <div class="bed-label apple-terrace-label">Apple Terrace Bed</div>
          <div class="at-grid">
            {atbed("Apple Terrace 1")}
            {atbed("Apple Terrace 2")}
            {atbed("Apple Terrace 3")}
            {atbed("Apple Terrace 4")}
          </div>
        </div>
        <div class="upper-bed asparagus-bed">
          <div class="bed-label">Asparagus Bed</div>
          <div class="plant-list">{plant_lines(asparagus_plants)}</div>
        </div>
      </div>'''


def build_list_view(lower, upper):
    rows = ""
    for bed_name in LOWER_BED_ORDER:
        plants = lower.get(bed_name, [])
        if plants:
            label = f"Bed {bed_name}" if bed_name != "Sunflower" else "Sunflower Bed"
            for plant, season in plants:
                rows += f"<tr><td>Lower</td><td>{label}</td><td>{plant}</td><td>{season}</td></tr>\n"
    for bed_name in UPPER_BED_ORDER:
        plants = upper.get(bed_name, [])
        if plants:
            for plant, season in plants:
                rows += f"<tr><td>Upper</td><td>{bed_name}</td><td>{plant}</td><td>{season}</td></tr>\n"
    return f'''
      <table>
        <thead>
          <tr><th>Garden</th><th>Bed</th><th>Plant</th><th>Season</th></tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>'''


def nav_links():
    links = '<li><a href="index.html">Home</a></li>\n'
    for year in sorted(YEARS, reverse=True):
        links += f'      <li><a href="{year}.html">{year}</a></li>\n'
    return links


def build_page(year):
    lower, upper = read_csv(year)
    lower_map = build_lower_map(lower)
    upper_map = build_upper_map(upper)
    list_view = build_list_view(lower, upper)

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>{year} Garden Map</title>
  <link rel="stylesheet" href="style.css" />
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=Lato:wght@300;400;700&display=swap" rel="stylesheet">
</head>
<body>
  <header>
    <div class="header-inner">
      <div class="header-icon">🌱</div>
      <h1>The Gardening Gals</h1>
      <p class="subtitle">Welcome to our online gardening record!</p>
    </div>
  </header>
  <nav>
    <ul>
      {nav_links()}
    </ul>
  </nav>
  <main>
    <h1 class="page-title">🌿 {year} Garden Map</h1>
    <p class="page-subtitle">Lower-level and upper-level beds</p>
    <div class="view-toggle">
      <button class="toggle-btn active" onclick="toggleView('map', this)">Map View</button>
      <button class="toggle-btn" onclick="toggleView('list', this)">List View</button>
    </div>
    <div id="map-view">
      <h2 class="section-heading">Lower-Level Garden</h2>
      {lower_map}
      <h2 class="section-heading">Upper-Level Garden</h2>
      {upper_map}
    </div>
    <div id="list-view" style="display:none;" class="list-view">
      {list_view}
    </div>
  </main>
  <footer>
    <p></p>
  </footer>
  <script>
    function toggleView(view, btn) {{
      document.getElementById('map-view').style.display = view === 'map' ? 'block' : 'none';
      document.getElementById('list-view').style.display = view === 'list' ? 'block' : 'none';
      document.querySelectorAll('.toggle-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
    }}
  </script>
</body>
</html>'''


def main():
    for year in YEARS:
        html = build_page(year)
        filename = f"{year}.html"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"✅ {filename} generated successfully!")


main()

import csv
import re

CSV_FILE = "varietals.csv"
YEARS = [2022, 2023, 2024, 2025, 2026]


def read_varietals(year):
    items = []
    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if str(row["year"]).strip() == str(year):
                items.append({
                    "varietal": row["varietal"].strip(),
                    "seed_type": row["seed_type"].strip(),
                })
    return items


def clean_seed_type(seed_type):
    s = seed_type
    s = re.sub(r'(?i)^(organic\s+)?(pelleted\s+)?\(f1\)\s+', '', s)
    s = re.sub(r'(?i)^organic\s+', '', s)
    s = re.sub(r'(?i)\s+seed$', '', s)
    s = re.sub(r'(?i)\s+seeds$', '', s)
    return s.strip()


def build_table_rows(items):
    if not items:
        return '<tr><td colspan="2">No varietal data available for this year.</td></tr>'
    rows = ""
    for item in items:
        plant_type = clean_seed_type(item["seed_type"])
        rows += f"        <tr><td>{item['varietal']}</td><td>{plant_type}</td></tr>\n"
    return rows


def nav_dropdown(current_year):
    options = ""
    for year in sorted(YEARS, reverse=True):
        options += f'<li><a href="varietals-{year}.html">{year}</a></li>\n'
    return options


def build_page(year):
    items = read_varietals(year)
    rows = build_table_rows(items)

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>{year} Garden</title>
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
      <li><a href="index.html">Home</a></li>
      <li class="dropdown">
        <a href="#">Year</a>
        <ul class="dropdown-menu">
          {nav_dropdown(year)}
        </ul>
      </li>
    </ul>
  </nav>
  <main>
    <h1 class="page-title">{year} Garden</h1>
    <div class="view-toggle">
      <button class="toggle-btn" onclick="window.location.href='{year}.html'">Map</button>
      <button class="toggle-btn active">Varietals</button>
    </div>
    <div class="list-view">
      <table>
        <thead>
          <tr><th>Varietal</th><th>Type</th></tr>
        </thead>
        <tbody>
{rows}        </tbody>
      </table>
    </div>
  </main>
  <footer>
    <p></p>
  </footer>
</body>
</html>'''


def main():
    for year in YEARS:
        html = build_page(year)
        filename = f"varietals-{year}.html"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"✅ {filename} generated successfully!")


main()

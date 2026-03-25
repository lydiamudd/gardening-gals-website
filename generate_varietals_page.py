import csv
import re
from collections import defaultdict

CSV_FILE = "varietals.csv"
YEARS = [2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026]


def clean_seed_type(seed_type):
    s = seed_type
    s = re.sub(r'(?i)^(organic\s+)?(pelleted\s+)?\(f1\)\s+', '', s)
    s = re.sub(r'(?i)^organic\s+', '', s)
    s = re.sub(r'(?i)\s+seed$', '', s)
    s = re.sub(r'(?i)\s+seeds$', '', s)
    return s.strip()


def read_varietals():
    # grouped[(type, varietal)] = set of years
    grouped = defaultdict(set)
    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            year = str(row["year"]).strip()
            varietal = row["varietal"].strip()
            seed_type = clean_seed_type(row["seed_type"].strip())
            grouped[(seed_type, varietal)].add(year)
    return grouped


def build_table_rows(grouped):
    rows = ""
    # Sort by type then varietal
    for (seed_type, varietal), years in sorted(grouped.items(), key=lambda x: (x[0][0].lower(), x[0][1].lower())):
        years_str = ", ".join(sorted(years))
        rows += f"        <tr><td>{seed_type}</td><td>{varietal}</td><td>{years_str}</td></tr>\n"
    return rows


def nav_dropdown():
    options = ""
    for year in sorted(YEARS, reverse=True):
        options += f'          <li><a href="{year}.html">{year}</a></li>\n'
    return options


def build_page():
    grouped = read_varietals()
    rows = build_table_rows(grouped)

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Plant Varietals</title>
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
        <a href="#">Layout</a>
        <ul class="dropdown-menu">
{nav_dropdown()}        </ul>
      </li>
      <li><a href="varietals.html">Varietals</a></li>
    </ul>
  </nav>
  <main>
    <h1 class="page-title">Plant Varietals</h1>
    <div class="list-view">
      <table>
        <thead>
          <tr><th>Type</th><th>Varietal</th><th>Year(s)</th></tr>
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


html = build_page()
with open("varietals.html", "w", encoding="utf-8") as f:
    f.write(html)
print("✅ varietals.html generated successfully!")

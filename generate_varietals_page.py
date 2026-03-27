import csv
import re
from collections import defaultdict
from utils import YEARS, nav_dropdown, clean_seed_type

CSV_FILE = "data_varietals.csv"


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
<body class="varietals">
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
    <p class="intro-note"><em>Note: This list reflects varietals for which we have recorded data and does not represent everything we've grown over the years. We do our best to keep it updated, but some seasons are better documented than others!</em></p>
      </table>
    </div>
  </main>
  <footer>
    <p></p>
  </footer>
</body>
</html>'''


html = build_page()
with open("view_varietals.html", "w", encoding="utf-8") as f:
    f.write(html)
print("✅ view_varietals.html generated successfully!")

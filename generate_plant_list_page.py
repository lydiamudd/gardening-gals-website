import csv
import re
from collections import defaultdict

PLANTING_CSV = "planting_data.csv"
VARIETALS_CSV = "varietals.csv"
YEARS = [2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026]

MANUAL_MAP = {
    "tomato": "Tomato",
    "pepper": "Sweet peppers",
    "zucchini": "Zucchini",
}

CATEGORY_FIXES = {
    "covercrop": "Cover crop",
}


def clean_seed_type(seed_type):
    s = seed_type
    s = re.sub(r'(?i)^(organic\s+)?(pelleted\s+)?\(f1\)\s+', '', s)
    s = re.sub(r'(?i)^organic\s+', '', s)
    s = re.sub(r'(?i)\s+seed$', '', s)
    s = re.sub(r'(?i)\s+seeds$', '', s)
    return s.strip()


def normalize(s):
    return s.lower().strip()


def clean_category(category):
    return CATEGORY_FIXES.get(category.lower().strip(), category.strip())


def read_planting_data():
    plant_years = defaultdict(set)
    plant_category = {}
    with open(PLANTING_CSV, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            plant = row["plant_name"].strip()
            year = str(row["year"]).strip()
            category = clean_category(row["plant_category"])
            plant_years[plant].add(year)
            plant_category[plant] = category
    plant_names = sorted(plant_years.keys(), key=lambda x: (plant_category[x].lower(), x.lower()))
    return {p: sorted(y) for p, y in plant_years.items()}, plant_category, plant_names


def read_varietals_data():
    type_varietals = defaultdict(set)
    norm_to_cleaned = {}
    with open(VARIETALS_CSV, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            varietal = row["varietal"].strip()
            cleaned = clean_seed_type(row["seed_type"].strip())
            type_varietals[cleaned].add(varietal)
            norm_to_cleaned[normalize(cleaned)] = cleaned
    return {k: sorted(v) for k, v in type_varietals.items()}, norm_to_cleaned


def get_cleaned_type(plant_name, norm_to_cleaned):
    n = normalize(plant_name)
    if n in MANUAL_MAP:
        return MANUAL_MAP[n]
    return norm_to_cleaned.get(n)


def build_category_sections(plant_names, plant_years, plant_category, type_varietals, norm_to_cleaned):
    # Group plants by category, preserving alphabetical sort order
    categories = []
    category_plants = defaultdict(list)
    for plant in plant_names:
        cat = plant_category.get(plant, "")
        if cat not in category_plants:
            categories.append(cat)
        category_plants[cat].append(plant)

    sections = ""
    for cat in categories:
        plants = category_plants[cat]
        rows = ""
        for plant in plants:
            years_str = ", ".join(plant_years.get(plant, []))
            cleaned = get_cleaned_type(plant, norm_to_cleaned)
            if cleaned and cleaned in type_varietals:
                varietals_str = ", ".join(type_varietals[cleaned])
            else:
                varietals_str = ""
            rows += f"            <tr><td>{plant}</td><td>{years_str}</td><td>{varietals_str}</td></tr>\n"

        sections += f'''    <h2 class="section-heading">{cat}</h2>
    <div class="garden-section-card">
      <div class="list-view">
        <table>
          <thead>
            <tr><th>Plant</th><th>Year(s)</th><th>Varietal(s)</th></tr>
          </thead>
          <tbody>
{rows}          </tbody>
        </table>
      </div>
    </div>
'''
    return sections


def nav_dropdown():
    options = ""
    for year in sorted(YEARS, reverse=True):
        options += f'          <li><a href="{year}.html">{year}</a></li>\n'
    return options


def build_page():
    plant_years, plant_category, plant_names = read_planting_data()
    type_varietals, norm_to_cleaned = read_varietals_data()
    sections = build_category_sections(plant_names, plant_years, plant_category, type_varietals, norm_to_cleaned)

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Plant List - The Gardening Gals</title>
  <link rel="stylesheet" href="style.css" />
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=Lato:wght@300;400;700&display=swap" rel="stylesheet">
</head>
<body class="plant-list-page">
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
      <li><a href="plant_list.html">Plant List</a></li>
      <li><a href="garden_notes.html">Garden Notes</a></li>  
      <!-- <li><a href="varietals.html">Varietals</a></li> -->
    </ul>
  </nav>
  <main>
    <h1 class="page-title">Plant List</h1>
{sections}  </main>
  <footer>
    <p></p>
  </footer>
</body>
</html>'''


html = build_page()
with open("plant_list.html", "w", encoding="utf-8") as f:
    f.write(html)
print("Plant list generated successfully!")

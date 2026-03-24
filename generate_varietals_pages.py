import csv
from collections import defaultdict

# -------------------------------------------------------
# generate_varietals_pages.py
# Reads varietals.csv and generates a varietals page for each year
# Usage: python3 generate_varietals_pages.py
# -------------------------------------------------------

CSV_FILE = "varietals.csv"
YEARS = [2022, 2023, 2024, 2025, 2026]


def read_varietals(year):
    """Read varietals.csv and return list of dicts for the given year."""
    items = []
    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if str(row["year"]).strip() == str(year):
                items.append({
                    "varietal": row["varietal"].strip(),
                    "seed_type": row["seed_type"].strip(),
                    "product_id": row["product_id"].strip(),
                })
    return items


def clean_seed_type(seed_type):
    """Extract the plant type from the seed type string."""
    # Remove organic/F1/pelleted prefixes and 'Seed' suffix
    import re
    s = seed_type
    s = re.sub(r'(?i)^(organic\s+)?(pelleted\s+)?\(f1\)\s+', '', s)
    s = re.sub(r'(?i)^organic\s+', '', s)
    s = re.sub(r'(?i)\s+seed$', '', s)
    s = re.sub(r'(?i)\s+seeds$', '', s)
    return s.strip()


def build_table_rows(items):
    if not items:
        return '<tr><td colspan="3">No varietal data available for this year.</td></tr>'
    rows = ""
    for item in items:
        plant_type = clean_seed_type(item["seed_type"])
        product_id = item["product_id"]
        link = f'<a href="https://www.johnnyseeds.com/search/#q={product_id}&t=product" target="_blank">{product_id}</a>' if product_id else "—"
        rows += f"""        <tr>
          <td>{item['varietal']}</td>
          <td>{plant_type}</td>
          <td>{link}</td>
        </tr>\n"""
    return rows


def nav_links(current_year):
    links = '<li><a href="index.html">Home</a></li>\n'
    for year in sorted(YEARS, reverse=True):
        active = ' class="active"' if year == current_year else ''
        links += f'      <li><a href="{year}.html"{active}>{year}</a></li>\n'
    return links


def build_page(year):
    items = read_varietals(year)
    rows = build_table_rows(items)
    count = len(items)

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>{year} Plant Varietals</title>
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
      {nav_links(year)}
    </ul>
  </nav>

  <main>
    <h1 class="page-title">🌿 {year} Plant Varietals</h1>
    <p class="page-subtitle">{count} varieties ordered from Johnny\'s Selected Seeds</p>

    <div class="list-view">
      <table>
        <thead>
          <tr>
            <th>Varietal</th>
            <th>Type</th>
            <th>Product ID</th>
          </tr>
        </thead>
        <tbody>
{rows}        </tbody>
      </table>
    </div>

    <p style="margin-top: 1.5rem;">
      <a href="{year}.html" class="year-btn" style="font-size: 0.9rem; padding: 0.5rem 1.25rem;">← Back to {year} Garden Map</a>
    </p>
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

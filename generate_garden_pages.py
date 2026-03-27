import csv
from collections import defaultdict
from utils import YEARS, nav_dropdown, load_config

CSV_FILE = "data_planting.csv"
CONFIG = load_config()
SEASON_ORDER = CONFIG['seasons']

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
    def season_key(item):
        season = item[1]
        return SEASON_ORDER.index(season) if season in SEASON_ORDER else len(SEASON_ORDER)
    sorted_plants = sorted(plants, key=season_key)
    lines = []
    for plant, season in sorted_plants:
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
      <div class="garden-section-card">
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
    kitchen_herbs_plants = upper.get("Kitchen Herbs", [])
    asparagus_plants = upper.get("Asparagus", [])
    return f'''
      <div class="garden-section-card">
        <div class="upper-garden-map">
          <div class="upper-bed strawberry-bed">
            <div class="bed-label">Strawberry Bed</div>
            <div class="plant-list">{plant_lines(strawberry_plants)}</div>
          </div>
          <div class="upper-bed kitchen-herbs-bed">
            <div class="bed-label">Kitchen Herbs Bed</div>
            <div class="plant-list">{plant_lines(kitchen_herbs_plants)}</div>
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
        </div>
      </div>'''


def build_page(year):
    lower, upper = read_csv(year)
    lower_map = build_lower_map(lower)
    upper_map = build_upper_map(upper)

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>{year} Garden</title>
  <link rel="stylesheet" href="style.css" />
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=Lato:wght@300;400;700&display=swap" rel="stylesheet">
</head>
<body class="layout">
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
    <h1 class="page-title">{year} Garden Layout</h1>
    <h2 class="section-heading">Lower-Level Garden</h2>
    {lower_map}
    <h2 class="section-heading">Upper-Level Garden</h2>
    {upper_map}
  </main>
  <footer>
    <p></p>
  </footer>
</body>
</html>'''


def main():
    for year in YEARS:
        html = build_page(year)
        filename = f"view_{year}.html"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"✅ {filename} generated successfully!")


main()

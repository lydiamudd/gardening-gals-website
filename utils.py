"""
Shared utilities for garden website generators.
"""

import csv
import yaml
import os
import re
from pathlib import Path

# Load configuration
CONFIG_PATH = Path(__file__).parent / "config.yaml"

def load_config():
    """Load configuration from config.yaml"""
    with open(CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)

CONFIG = load_config()
YEARS = CONFIG['years']

# Category name fixes (consolidated from individual scripts)
CATEGORY_FIXES = {
    "covercrop": "Cover crop",
}


def normalize(s):
    """Normalize a string to lowercase, stripped."""
    return s.lower().strip()


def clean_category(category):
    """Clean/normalize category names (e.g., 'covercrop' → 'Cover crop')."""
    return CATEGORY_FIXES.get(category.lower().strip(), category.strip())


def nav_dropdown():
    """Generate navigation dropdown HTML for year links."""
    options = ""
    for year in sorted(YEARS, reverse=True):
        options += f'          <li><a href="view_{year}.html">{year}</a></li>\n'
    return options


def escape_js(s):
    """Escape a string for safe embedding in a JS double-quoted string."""
    s = s.replace("\\", "\\\\")
    s = s.replace('"', '\\"')
    s = s.replace('\r', '')
    s = s.replace('\n', ' ')
    # Replace curly/smart quotes with straight equivalents
    s = s.replace('\u201c', '\\"').replace('\u201d', '\\"')
    s = s.replace('\u2018', "\\'").replace('\u2019', "\\'")
    return s


def read_csv(filename, encoding="utf-8-sig"):
    """Read CSV file with consistent encoding handling."""
    rows = []
    with open(filename, newline="", encoding=encoding) as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    return rows


def clean_seed_type(seed_type):
    """Normalize seed type names by removing common prefixes/suffixes."""
    import re
    s = seed_type
    s = re.sub(r'(?i)^(organic\s+)?(pelleted\s+)?\(f1\)\s+', '', s)
    s = re.sub(r'(?i)^organic\s+', '', s)
    s = re.sub(r'(?i)\s+seed$', '', s)
    s = re.sub(r'(?i)\s+seeds$', '', s)
    return s.strip()


def build_html_template(title, content, nav_dropdown_html):
    """Build standard HTML template with header, nav, and footer.
    
    Args:
        title: Page title (appears in <title> and <h1>)
        content: Main page HTML content
        nav_dropdown_html: HTML for nav dropdown (from nav_dropdown())
    """
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>{title}</title>
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
{nav_dropdown_html}        </ul>
      </li>
      <li><a href="plant_list.html">Plant List</a></li>
      <li><a href="garden_notes.html">Garden Notes</a></li>
    </ul>
  </nav>
  <main>
{content}
  </main>
  <footer>
    <p></p>
  </footer>
</body>
</html>'''

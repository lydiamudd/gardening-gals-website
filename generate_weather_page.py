"""
generate_weather_page.py
Generates weather.html for The Gardening Gals website.

Data sources:
  - Open-Meteo Historical Weather API (free, no key)
  - NOAA Climate Data Online API (free, requires token)

Usage:
  python generate_weather_page.py

Configuration:
  Set NOAA_TOKEN below before running.
  Longmont, CO coordinates and nearest NOAA station are pre-filled.
"""

import json
import urllib.request
import urllib.parse
from datetime import date, timedelta
from collections import defaultdict
from utils import YEARS, nav_dropdown

# ── Configuration ────────────────────────────────────────────────────────────

NOAA_TOKEN = "iXTeaXanbvDYbIoyDktIaeScjHrFDqKy"   # <-- paste your token here

# Longmont, CO
LATITUDE  = 40.1672
LONGITUDE = -105.1019

# NOAA station: Loveland/Fort Collins area (closest with long record)
# USC00055722 = Loveland, CO  |  USC00053005 = Fort Collins
NOAA_STATION = "USC00055722"

# How many years of history to pull from Open-Meteo
HISTORY_YEARS = 10

# Frost thresholds (°F)
LIGHT_FROST = 36   # 36°F — radiation frost risk
FROST       = 32   # 32°F — water freezes
HARD_FROST  = 28   # 28°F — kills most annuals

# ── Open-Meteo ────────────────────────────────────────────────────────────────

def fetch_openmeteo():
    """Fetch daily min temp (°C) + precipitation (mm) for the last HISTORY_YEARS years."""
    end   = date.today() - timedelta(days=1)
    start = date(end.year - HISTORY_YEARS, 1, 1)

    params = {
        "latitude":        LATITUDE,
        "longitude":       LONGITUDE,
        "start_date":      start.isoformat(),
        "end_date":        end.isoformat(),
        "daily":           "temperature_2m_min,temperature_2m_max,precipitation_sum",
        "temperature_unit":"fahrenheit",
        "precipitation_unit": "inch",
        "timezone":        "America/Denver",
    }
    url = "https://archive-api.open-meteo.com/v1/archive?" + urllib.parse.urlencode(params)
    print(f"Fetching Open-Meteo data ({start} → {end})...")
    with urllib.request.urlopen(url, timeout=30) as r:
        data = json.loads(r.read())

    daily = data["daily"]
    records = []
    for d, tmin, tmax, precip in zip(
        daily["time"],
        daily["temperature_2m_min"],
        daily["temperature_2m_max"],
        daily["precipitation_sum"],
    ):
        records.append({
            "date":   d,           # "YYYY-MM-DD"
            "tmin":   tmin,        # °F
            "tmax":   tmax,        # °F
            "precip": precip or 0, # inches
        })
    print(f"  Got {len(records)} daily records from Open-Meteo.")
    return records


# ── NOAA ──────────────────────────────────────────────────────────────────────

def fetch_noaa_frost_dates():
    """
    Fetch daily TMIN from NOAA for the station and compute first/last frost
    dates per year.  Returns dict: {year: {last_spring_frost, first_fall_frost}}
    """
    if NOAA_TOKEN == "YOUR_NOAA_TOKEN_HERE":
        print("  NOAA token not set — skipping NOAA data.")
        return {}

    end_year  = date.today().year - 1
    start_year = end_year - HISTORY_YEARS
    results = {}

    base = "https://www.ncei.noaa.gov/cdo-web/api/v2/data"
    headers = {"token": NOAA_TOKEN}

    for year in range(start_year, end_year + 1):
        params = {
            "datasetid":  "GHCND",
            "stationid":  f"GHCND:{NOAA_STATION}",
            "datatypeid": "TMIN",
            "startdate":  f"{year}-01-01",
            "enddate":    f"{year}-12-31",
            "limit":      1000,
            "units":      "standard",   # Fahrenheit
        }
        url = base + "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                data = json.loads(r.read())
        except Exception as e:
            print(f"  NOAA fetch failed for {year}: {e}")
            continue

        if "results" not in data:
            continue

        # Build date→tmin map (NOAA returns tenths of °C; units=standard gives °F)
        day_tmin = {}
        for rec in data["results"]:
            d    = rec["date"][:10]   # "YYYY-MM-DD"
            tmin = rec["value"] / 10  # tenths → whole degrees
            day_tmin[d] = tmin

        # Last spring frost = latest date before Jul 1 where tmin <= 32
        # First fall frost  = earliest date after Jul 1 where tmin <= 32
        spring_frosts = [d for d, t in day_tmin.items() if d <= f"{year}-06-30" and t <= 32]
        fall_frosts   = [d for d, t in day_tmin.items() if d >= f"{year}-07-01" and t <= 32]

        results[year] = {
            "last_spring_frost":  max(spring_frosts) if spring_frosts else None,
            "first_fall_frost":   min(fall_frosts)   if fall_frosts  else None,
        }
        print(f"  NOAA {year}: last spring frost={results[year]['last_spring_frost']}, "
              f"first fall frost={results[year]['first_fall_frost']}")

    return results


# ── Data crunching ────────────────────────────────────────────────────────────

def derive_frost_dates(records):
    """Derive first/last frost dates per year from Open-Meteo tmin data."""
    by_year = defaultdict(list)
    for r in records:
        year = int(r["date"][:4])
        by_year[year].append(r)

    frost_dates = {}
    for year, days in by_year.items():
        spring = [d["date"] for d in days if d["date"] <= f"{year}-06-30" and d["tmin"] is not None and d["tmin"] <= 32]
        fall   = [d["date"] for d in days if d["date"] >= f"{year}-07-01" and d["tmin"] is not None and d["tmin"] <= 32]
        frost_dates[year] = {
            "last_spring_frost": max(spring) if spring else None,
            "first_fall_frost":  min(fall)   if fall   else None,
        }
    return frost_dates


def frost_probability_curve(records):
    """
    For each day-of-year (1–365), what % of years had tmin <= 32?
    Returns list of {doy, date_label, prob_frost, prob_light, prob_hard}
    """
    # Group tmin values by day-of-year across all years
    doy_temps = defaultdict(list)
    for r in records:
        if r["tmin"] is None:
            continue
        d = date.fromisoformat(r["date"])
        doy = d.timetuple().tm_yday
        doy_temps[doy].append(r["tmin"])

    curve = []
    # Show Aug 1 (doy 213) through Jun 30 (doy 181 next year) — gardening season window
    # We'll just do all 365 days and let the chart zoom
    for doy in range(1, 366):
        temps = doy_temps.get(doy, [])
        if not temps:
            continue
        n = len(temps)
        # Representative date label (use a non-leap year)
        try:
            label_date = date(2001, 1, 1) + timedelta(days=doy - 1)
            label = label_date.strftime("%b %d")
        except Exception:
            label = str(doy)
        curve.append({
            "doy":        doy,
            "label":      label,
            "prob_light": round(100 * sum(1 for t in temps if t <= LIGHT_FROST) / n, 1),
            "prob_frost": round(100 * sum(1 for t in temps if t <= FROST) / n, 1),
            "prob_hard":  round(100 * sum(1 for t in temps if t <= HARD_FROST) / n, 1),
        })
    return curve


def monthly_stats(records):
    """Monthly average high, average low, total precipitation."""
    by_month = defaultdict(lambda: {"tmins": [], "tmaxs": [], "precip": 0.0})
    for r in records:
        ym = r["date"][:7]   # "YYYY-MM"
        if r["tmin"] is not None:
            by_month[ym]["tmins"].append(r["tmin"])
        if r["tmax"] is not None:
            by_month[ym]["tmaxs"].append(r["tmax"])
        by_month[ym]["precip"] += r["precip"]

    # Average across all years for each calendar month
    cal_month = defaultdict(lambda: {"tmins": [], "tmaxs": [], "precips": []})
    for ym, vals in by_month.items():
        m = int(ym[5:7])
        if vals["tmins"]: cal_month[m]["tmins"].extend(vals["tmins"])
        if vals["tmaxs"]: cal_month[m]["tmaxs"].extend(vals["tmaxs"])
        cal_month[m]["precips"].append(vals["precip"])

    MONTH_NAMES = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    result = []
    for m in range(1, 13):
        v = cal_month[m]
        result.append({
            "month":       MONTH_NAMES[m - 1],
            "avg_high":    round(sum(v["tmaxs"]) / len(v["tmaxs"]), 1) if v["tmaxs"] else None,
            "avg_low":     round(sum(v["tmins"]) / len(v["tmins"]), 1) if v["tmins"] else None,
            "avg_precip":  round(sum(v["precips"]) / len(v["precips"]), 2) if v["precips"] else None,
        })
    return result


def frost_table_rows(om_frosts, noaa_frosts):
    """Build combined frost date table data."""
    all_years = sorted(set(list(om_frosts.keys()) + list(noaa_frosts.keys())), reverse=True)
    rows = []
    for year in all_years:
        om   = om_frosts.get(year, {})
        noaa = noaa_frosts.get(year, {})

        def fmt(d):
            if not d: return "—"
            try: return date.fromisoformat(d).strftime("%b %d")
            except: return d

        rows.append({
            "year":               year,
            "om_last_spring":     fmt(om.get("last_spring_frost")),
            "om_first_fall":      fmt(om.get("first_fall_frost")),
            "noaa_last_spring":   fmt(noaa.get("last_spring_frost")),
            "noaa_first_fall":    fmt(noaa.get("first_fall_frost")),
        })
    return rows


# ── HTML builder ──────────────────────────────────────────────────────────────

def build_page(curve, monthly, frost_rows, has_noaa):
    curve_js   = json.dumps(curve)
    monthly_js = json.dumps(monthly)
    frost_js   = json.dumps(frost_rows)
    has_noaa_js = "true" if has_noaa else "false"

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Weather - The Gardening Gals</title>
  <link rel="stylesheet" href="style.css" />
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=Lato:wght@300;400;700&display=swap" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
</head>
<body class="weather-page">
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
    <h1 class="page-title">Historic Weather</h1>
    <p class="weather-subtitle">Longmont, CO &mdash; last {HISTORY_YEARS} years &mdash; Open-Meteo{"&nbsp;+ NOAA" if has_noaa else ""}</p>

    <!-- ── Frost Probability ── -->
    <h2 class="section-heading">Frost Probability by Day of Year</h2>
    <div class="garden-section-card">
      <p class="chart-note">Percentage of years (out of {HISTORY_YEARS}) that recorded a frost on or near each date. Covers August&ndash;June for gardening context.</p>
      <div class="chart-wrap">
        <canvas id="frostCurveChart"></canvas>
      </div>
      <div class="chart-legend">
        <span class="legend-dot" style="background:#60a5fa"></span> Light frost (&le;36&deg;F)&nbsp;&nbsp;
        <span class="legend-dot" style="background:#f97316"></span> Frost (&le;32&deg;F)&nbsp;&nbsp;
        <span class="legend-dot" style="background:#7c3aed"></span> Hard frost (&le;28&deg;F)
      </div>
    </div>

    <!-- ── First / Last Frost Dates ── -->
    <h2 class="section-heading">First &amp; Last Frost Dates by Year</h2>
    <div class="garden-section-card">
      <div class="list-view">
        <table id="frostTable">
          <thead>
            <tr>
              <th>Year</th>
              <th>Last Spring Frost<br><span class="th-sub">Open-Meteo</span></th>
              <th>First Fall Frost<br><span class="th-sub">Open-Meteo</span></th>
              {"<th>Last Spring Frost<br><span class='th-sub'>NOAA Station</span></th><th>First Fall Frost<br><span class='th-sub'>NOAA Station</span></th>" if has_noaa else ""}
            </tr>
          </thead>
          <tbody id="frostTableBody"></tbody>
        </table>
      </div>
    </div>

    <!-- ── Monthly Rainfall ── -->
    <h2 class="section-heading">Average Monthly Precipitation</h2>
    <div class="garden-section-card">
      <p class="chart-note">{HISTORY_YEARS}-year average monthly precipitation in inches.</p>
      <div class="chart-wrap chart-wrap-short">
        <canvas id="rainfallChart"></canvas>
      </div>
    </div>

    <!-- ── Temperature Highs & Lows ── -->
    <h2 class="section-heading">Average Monthly Temperature</h2>
    <div class="garden-section-card">
      <p class="chart-note">{HISTORY_YEARS}-year average daily high and low (&deg;F) by month. Shaded band shows the range.</p>
      <div class="chart-wrap chart-wrap-short">
        <canvas id="tempChart"></canvas>
      </div>
    </div>

  </main>
  <footer><p></p></footer>

<script>
const CURVE   = {curve_js};
const MONTHLY = {monthly_js};
const FROSTS  = {frost_js};
const HAS_NOAA = {has_noaa_js};

// ── Helpers ──────────────────────────────────────────────────────────────────
const SAGE       = "#7a9e7e";
const SAGE_LIGHT = "#a8c5a0";
const BARK       = "#4a3728";
const CREAM      = "#f5f0e8";

Chart.defaults.font.family = "'Lato', sans-serif";
Chart.defaults.color = BARK;

// ── Frost Probability Chart ───────────────────────────────────────────────────
(function() {{
  // Show Aug 1 (doy 213) → Dec 31 (365) → Jan 1 (1) → Jun 30 (181)
  // Reorder curve so Aug is first
  const aug1 = 213;
  const reordered = [
    ...CURVE.filter(d => d.doy >= aug1),
    ...CURVE.filter(d => d.doy < aug1 && d.doy <= 181),
  ];

  const ctx = document.getElementById("frostCurveChart").getContext("2d");
  new Chart(ctx, {{
    type: "line",
    data: {{
      labels: reordered.map(d => d.label),
      datasets: [
        {{
          label: "Light frost (≤36°F)",
          data: reordered.map(d => d.prob_light),
          borderColor: "#60a5fa",
          backgroundColor: "rgba(96,165,250,0.08)",
          borderWidth: 2,
          pointRadius: 0,
          fill: false,
          tension: 0.4,
        }},
        {{
          label: "Frost (≤32°F)",
          data: reordered.map(d => d.prob_frost),
          borderColor: "#f97316",
          backgroundColor: "rgba(249,115,22,0.08)",
          borderWidth: 2,
          pointRadius: 0,
          fill: false,
          tension: 0.4,
        }},
        {{
          label: "Hard frost (≤28°F)",
          data: reordered.map(d => d.prob_hard),
          borderColor: "#7c3aed",
          backgroundColor: "rgba(124,58,237,0.08)",
          borderWidth: 2,
          pointRadius: 0,
          fill: false,
          tension: 0.4,
        }},
      ],
    }},
    options: {{
      responsive: true,
      maintainAspectRatio: true,
      interaction: {{ mode: "index", intersect: false }},
      plugins: {{
        legend: {{ display: false }},
        tooltip: {{
          callbacks: {{
            label: ctx => ` ${{ctx.dataset.label}}: ${{ctx.parsed.y}}%`,
          }},
        }},
      }},
      scales: {{
        x: {{
          ticks: {{
            maxTicksLimit: 12,
            maxRotation: 0,
          }},
          grid: {{ color: "rgba(74,55,40,0.08)" }},
        }},
        y: {{
          min: 0, max: 100,
          ticks: {{ callback: v => v + "%" }},
          grid: {{ color: "rgba(74,55,40,0.08)" }},
          title: {{ display: true, text: "% of years with frost" }},
        }},
      }},
    }},
  }});
}})();

// ── Frost Table ───────────────────────────────────────────────────────────────
(function() {{
  const tbody = document.getElementById("frostTableBody");
  FROSTS.forEach(r => {{
    const tr = document.createElement("tr");
    let cells = `<td>${{r.year}}</td><td>${{r.om_last_spring}}</td><td>${{r.om_first_fall}}</td>`;
    if (HAS_NOAA) cells += `<td>${{r.noaa_last_spring}}</td><td>${{r.noaa_first_fall}}</td>`;
    tr.innerHTML = cells;
    tbody.appendChild(tr);
  }});
}})();

// ── Rainfall Chart ────────────────────────────────────────────────────────────
(function() {{
  const ctx = document.getElementById("rainfallChart").getContext("2d");
  new Chart(ctx, {{
    type: "bar",
    data: {{
      labels: MONTHLY.map(m => m.month),
      datasets: [{{
        label: "Avg precipitation (in)",
        data: MONTHLY.map(m => m.avg_precip),
        backgroundColor: "#7a9e7e",
        borderColor: "#4a3728",
        borderWidth: 1,
        borderRadius: 4,
      }}],
    }},
    options: {{
      responsive: true,
      maintainAspectRatio: true,
      plugins: {{
        legend: {{ display: false }},
        tooltip: {{ callbacks: {{ label: ctx => ` ${{ctx.parsed.y}}"` }} }},
      }},
      scales: {{
        x: {{ grid: {{ display: false }} }},
        y: {{
          beginAtZero: true,
          ticks: {{ callback: v => v + '"' }},
          grid: {{ color: "rgba(74,55,40,0.08)" }},
          title: {{ display: true, text: "Inches" }},
        }},
      }},
    }},
  }});
}})();

// ── Temperature Chart ─────────────────────────────────────────────────────────
(function() {{
  const ctx = document.getElementById("tempChart").getContext("2d");

  // Build fill-between band using a stacked area trick
  const highs = MONTHLY.map(m => m.avg_high);
  const lows  = MONTHLY.map(m => m.avg_low);

  new Chart(ctx, {{
    type: "line",
    data: {{
      labels: MONTHLY.map(m => m.month),
      datasets: [
        {{
          label: "Avg High",
          data: highs,
          borderColor: "#c1674a",
          backgroundColor: "rgba(193,103,74,0.15)",
          borderWidth: 2.5,
          pointRadius: 4,
          pointBackgroundColor: "#c1674a",
          fill: "+1",
          tension: 0.4,
        }},
        {{
          label: "Avg Low",
          data: lows,
          borderColor: "#60a5fa",
          backgroundColor: "rgba(96,165,250,0.0)",
          borderWidth: 2.5,
          pointRadius: 4,
          pointBackgroundColor: "#60a5fa",
          fill: false,
          tension: 0.4,
        }},
      ],
    }},
    options: {{
      responsive: true,
      maintainAspectRatio: true,
      interaction: {{ mode: "index", intersect: false }},
      plugins: {{
        legend: {{ position: "top" }},
        tooltip: {{
          callbacks: {{
            label: ctx => ` ${{ctx.dataset.label}}: ${{ctx.parsed.y}}°F`,
          }},
        }},
      }},
      scales: {{
        x: {{ grid: {{ display: false }} }},
        y: {{
          ticks: {{ callback: v => v + "°F" }},
          grid: {{ color: "rgba(74,55,40,0.08)" }},
          title: {{ display: true, text: "Temperature (°F)" }},
        }},
      }},
    }},
  }});
}})();
</script>
</body>
</html>'''


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    # 1. Fetch Open-Meteo
    records = fetch_openmeteo()

    # 2. Fetch NOAA
    noaa_frosts = fetch_noaa_frost_dates()
    has_noaa = bool(noaa_frosts)

    # 3. Crunch data
    print("Crunching data...")
    om_frosts  = derive_frost_dates(records)
    curve      = frost_probability_curve(records)
    monthly    = monthly_stats(records)
    frost_rows = frost_table_rows(om_frosts, noaa_frosts)

    # 4. Build page
    html = build_page(curve, monthly, frost_rows, has_noaa)
    with open("view_weather.html", "w", encoding="utf-8") as f:
        f.write(html)
    print(f"view_weather.html generated successfully!")
    print(f"  Frost curve: {len(curve)} data points")
    print(f"  Monthly stats: {len(monthly)} months")
    print(f"  Frost table rows: {len(frost_rows)} years")
    if has_noaa:
        print(f"  NOAA frost dates: {len(noaa_frosts)} years")
    else:
        print("  NOAA: skipped (token not set)")


main()

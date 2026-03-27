# Garden Website Refactoring Guide

This document describes the major refactoring improvements made to the garden website build system in March 2026.

## Overview

The garden website had 5 independent Python generator scripts that created all the HTML pages. The codebase had significant duplication and was becoming difficult to maintain. This refactoring improves code organization, adds validation, and makes it much easier to update configuration.

## What Changed

### ✅ High-Priority (COMPLETED)

#### 1. Shared Utilities Module (`utils.py`)
**Problem**: Functions like `nav_dropdown()` and the `YEARS` constant were duplicated in all 5 generator scripts.

**Solution**: Created `utils.py` with shared utilities:
- `YEARS` — Loaded from config (single source of truth)
- `nav_dropdown()` — Build year navigation dropdown
- `escape_js()` — Safe JS string escaping
- `clean_seed_type()` — Normalize plant variety names
- `normalize()` — Lowercase/strip strings
- `clean_category()` — Normalize plant categories
- `read_csv()` — Standardized CSV reading
- `load_config()` — Load configuration from YAML

**Impact**: Eliminated 5× duplicated code, 1 place to update navigation logic.

#### 2. Central Configuration (`config.yaml`)
**Problem**: Site configuration was hardcoded scattered throughout scripts (years, location coordinates, frost thresholds, bed names, etc.)

**Solution**: Created `config.yaml` with all configuration:
```yaml
years: [2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026]
location:
  name: "Longmont, CO"
  latitude: 40.1672
  longitude: -105.1019
garden:
  lower_beds: ["One", "Two", ..., "Sunflower"]
  upper_beds: ["Strawberry", ..., "Asparagus"]
seasons: ["All season", "Spring", "Summer", "Fall"]
frost:
  light: 36
  standard: 32
  hard: 28
```

**Impact**: Update years for 2027 in ONE place and it propagates to all 8 year pages automatically.

#### 3. Build Orchestrator (`build.py`)
**Problem**: Had to manually run 5 separate Python scripts in the correct order.

**Solution**: Created `build.py` that:
- Runs all generators in sequence with error handling
- Validates that dependencies (PyYAML, config files) exist
- Provides detailed timing and error reporting
- Colored terminal output for clarity
- Supports running individual scripts: `python build.py --script generate_garden_pages.py`

**Usage**:
```bash
python build.py              # Run all 5 generators
python build.py --validate   # Validate data, then build
```

**Impact**: One command instead of 5, better error handling, validation support.

---

### ✅ Medium-Priority (COMPLETED)

#### 4. Data Validation Layer (`validate.py`)
**Problem**: No validation of data consistency between CSVs. Plant names might not match between `planting_data.csv` and `varietals.csv`, potentially causing silent failures.

**Solution**: Created `validate.py` with comprehensive checks:
- ✓ All required CSV files exist
- ✓ All required columns present
- ✓ Years in CSVs are valid (in `config.yaml`)
- ✓ Categories assigned to all plants
- ✓ Plant names consistency (planting_data vs varietals)
- ⚠️ Warns if `MANUAL_MAP` hacks are needed (data inconsistency indicator)

**Usage**:
```bash
python validate.py                # Check data
python build.py --validate        # Validation + build
```

**Example output**:
```
✓ All years in CSVs valid (config has: 2019, 2020, 2021, ...)
✓ All plants have categories (9 categories)
⚠ WARNING: MANUAL_MAP hacks used (indicates data inconsistency)
⚠ WARNING: 34 plants lack seed variety data (informational)
```

**Exit codes**:
- `0` = All valid
- `1` = Warnings (non-critical)
- `2` = Errors (critical)

**Impact**: Catch data issues before they break the website; validate before builds.

#### 5. Consolidated Category Cleaning Logic
**Problem**: `generate_plant_list_page.py` and `generate_varietals_page.py` both had duplicate `clean_category()` functions.

**Solution**: Moved to `utils.py`:
- `clean_category()` — Normalize category names ("covercrop" → "Cover crop")
- `normalize()` — Lowercase/strip strings

Updated both scripts to import from `utils` instead of defining locally.

**Impact**: Single source of truth for category normalization.

#### 6. Documented Orphaned Files (`ORPHANED_FILES.md`)
**Problem**: `plant_index.html` and `varietals-YYYY.html` files had no generators.

**Solution**: Created documentation:
- `plant_index.html` — Purpose unknown, last updated Mar 25, 2026
- `varietals-2022.html`, etc. — Year-specific variety pages, last updated Mar 24, 2022

Document provides 3 options for each:
1. **Maintain manually** — Keep as-is, document
2. **Create generators** — Build `generate_varietals_year_pages.py`
3. **Deprecate** — Remove if no longer needed

**File**: `ORPHANED_FILES.md` explains status and recommendations.

**Impact**: Clarity on what these files are; clear path forward for each.

---

## Updated Folder Structure

```
garden_website/
├── Core Infrastructure
│   ├── build.py                 ← Orchestrator (NEW)
│   ├── validate.py              ← Data validator (NEW)
│   ├── config.yaml              ← Central config (NEW)
│   ├── utils.py                 ← Shared functions (NEW)
│   └── ORPHANED_FILES.md        ← Documentation (NEW)
│
├── Generator Scripts
│   ├── generate_garden_pages.py
│   ├── generate_garden_notes.py
│   ├── generate_plant_list_page.py
│   ├── generate_varietals_page.py
│   └── generate_weather_page.py
│
├── Data Sources
│   ├── planting_data.csv
│   ├── data_notes.csv
│   └── varietals.csv
│
├── Static Content
│   ├── index.html
│   ├── about.html
│   ├── style.css
│   └── images/
│
└── Generated Output (auto-created)
    ├── 2019.html–2026.html
    ├── plant_list.html
    ├── garden_notes.html
    ├── varietals.html
    └── weather.html
```

---

## Code Changes Summary

### Files Modified
1. **generate_garden_pages.py**
   - Import: `from utils import YEARS, nav_dropdown, load_config`
   - Removed: `YEARS` constant, `nav_dropdown()` function
   - Removed: `SEASON_ORDER` (now in `config.yaml`)

2. **generate_garden_notes.py**
   - Import: `from utils import YEARS, nav_dropdown, escape_js`
   - Removed: `YEARS`, `nav_dropdown()`, `escape_js()`

3. **generate_plant_list_page.py**
   - Import: `from utils import ..., clean_seed_type, normalize, clean_category`
   - Removed: `clean_seed_type()`, `normalize()`, `clean_category()`

4. **generate_varietals_page.py**
   - Import: `from utils import YEARS, nav_dropdown, clean_seed_type`
   - Removed: `YEARS`, `nav_dropdown()`, `clean_seed_type()`

5. **generate_weather_page.py**
   - Import: `from utils import YEARS, nav_dropdown`
   - Removed: `YEARS`, `nav_dropdown()`

### Files Created
- `utils.py` — 80 lines, shared utilities
- `config.yaml` — Configuration in YAML
- `build.py` — 280 lines, orchestrator with colors/timing
- `validate.py` — 330 lines, comprehensive data validation
- `ORPHANED_FILES.md` — Documentation

---

## Usage Examples

### Normal builds (as before)
```bash
python build.py
```

### Validate before building
```bash
python build.py --validate

# Output:
# ✓ All years in CSVs valid
# ✓ All plants have categories
# ⚠ WARNING: 34 plants lack seed variety data (informational)
# ✅ All generators completed successfully!
```

### Run specific generator
```bash
python build.py --script generate_garden_pages.py
```

### Just run validation
```bash
python validate.py
```

### Update years for 2027
Edit `config.yaml`:
```yaml
years: [2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026, 2027]
```
All pages now generate for 2027 automatically.

---

## Benefits

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Build command complexity** | Run 5 scripts manually (or write bash script) | `python build.py` | ✅ Simple |
| **Code duplication** | 5× YEARS, 5× nav_dropdown() | 1× each in utils.py | ✅ DRY |
| **Places to update YEARS** | 5 files | 1 config file | ✅ Single source of truth |
| **Data validation** | None | Comprehensive | ✅ Catch issues early |
| **Configuration access** | Scattered (hardcoded) | Centralized YAML | ✅ One place to edit |
| **Error handling** | Minimal | Detailed reporting | ✅ Better debugging |

---

## Testing Results

All refactored scripts tested and working:
```
✅ generate_garden_pages.py     — 0.05s (8 year pages)
✅ generate_garden_notes.py     — 0.05s (1 page, 82 notes)
✅ generate_plant_list_page.py   — 0.05s (1 page, all plants)
✅ generate_varietals_page.py    — 0.04s (1 page, all varieties)
✅ generate_weather_page.py      — 10.0s (API calls, 1 page)

Total build time: ~10.2s
Validation time: ~0.1s
```

---

## Next Steps (Low-Priority Ideas)

1. **Auto-fix in validate.py** — Fix common issues automatically
2. **Incremental builds** — Only regenerate changed files
3. **Pre-commit hooks** — Validate data before git commits
4. **Generate year-specific varietals** — Currently `varietals-YYYY.html` is orphaned
5. **Jinja2 templating** — Replace f-strings with proper templates
6. **Docker containerization** — Run builds in isolated environment

---

## Questions?

- Read `ORPHANED_FILES.md` for questions about legacy files
- Run `python validate.py` to check data consistency
- Run `python build.py --help` or `python build.py --script generate_garden_pages.py --help` for options

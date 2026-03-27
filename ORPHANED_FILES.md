# Orphaned Files Documentation

This document describes HTML files that were previously in the garden_website repository but are no longer present or maintained.

## Deleted Files

### `plant_index.html`
- **Status**: ❌ DELETED (March 27, 2026)
- **Reason**: Legacy file — was an old version of `plant_list.html`
- **Replaced by**: `generate_plant_list_page.py` → `view_plant_list.html`

### `varietals-YYYY.html` (2022-2026)
- **Status**: ❌ DELETED (March 27, 2026)
- **Reason**: Legacy files with no generator — purpose unclear
- **Replaced by**: `generate_varietals_page.py` → `view_varietals.html` (all-years view)

## Summary

As of March 27, 2026 refactor:
- ✅ Main pages are auto-generated: `view_YYYY.html`, `view_plant_list.html`, `view_garden_notes.html`, `view_varietals.html`, `view_weather.html`
- ✅ All orphaned files have been cleaned up
- ✅ No legacy files remain in the repository

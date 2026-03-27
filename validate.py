#!/usr/bin/env python3
"""
Data validation script for garden website.
Checks for consistency issues between CSV files and configuration.

Usage:
    python validate.py              # Run all validations
    python validate.py --fix        # Attempt to auto-fix issues

Exit codes:
    0 = All valid
    1 = Warnings (non-critical issues)
    2 = Errors (critical issues)
"""

import csv
import sys
from pathlib import Path
from collections import defaultdict
from utils import YEARS, normalize, clean_category, clean_seed_type, load_config

CONFIG = load_config()

# Color codes
RED = '\033[91m'
YELLOW = '\033[93m'
GREEN = '\033[92m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

# Manual plant name mapping (hardcoded in generate_plant_list_page.py)
# This should ideally not be needed if data is kept consistent
MANUAL_MAP = {
    "tomato": "Tomato",
    "pepper": "Sweet peppers",
    "zucchini": "Zucchini",
}

class Validator:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.info = []
        self.planting_data = None
        self.notes_data = None
        self.varietals_data = None
        
    def log_error(self, msg):
        """Log a critical error."""
        self.errors.append(msg)
        print(f"{RED}✗ ERROR{RESET}: {msg}")
    
    def log_warning(self, msg):
        """Log a non-critical warning."""
        self.warnings.append(msg)
        print(f"{YELLOW}⚠ WARNING{RESET}: {msg}")
    
    def log_info(self, msg):
        """Log informational message."""
        self.info.append(msg)
        print(f"{BLUE}ℹ INFO{RESET}: {msg}")
    
    def log_success(self, msg):
        """Log a success message."""
        print(f"{GREEN}✓{RESET} {msg}")
    
    def read_csv(self, filename, encoding="utf-8-sig"):
        """Read CSV file and return rows."""
        try:
            with open(filename, newline="", encoding=encoding) as f:
                return list(csv.DictReader(f))
        except FileNotFoundError:
            self.log_error(f"File not found: {filename}")
            return None
        except Exception as e:
            self.log_error(f"Error reading {filename}: {e}")
            return None
    
    def validate_files_exist(self):
        """Check that all required CSV files exist."""
        print(f"\n{BOLD}Checking file existence...{RESET}")
        
        files = {
            "data_planting.csv": "planting data",
            "data_notes.csv": "notes data",
            "data_varietals.csv": "varietals",
        }
        
        missing = []
        for filename, desc in files.items():
            if Path(filename).exists():
                self.log_success(f"Found {desc}: {filename}")
            else:
                self.log_error(f"Missing {desc}: {filename}")
                missing.append(filename)
        
        return len(missing) == 0
    
    def validate_years(self):
        """Check that all years in CSV files are in CONFIG['years']."""
        print(f"\n{BOLD}Validating years...{RESET}")
        
        self.planting_data = self.read_csv("data_planting.csv")
        self.notes_data = self.read_csv("data_notes.csv")
        self.varietals_data = self.read_csv("data_varietals.csv")
        
        if not all([self.planting_data, self.notes_data, self.varietals_data]):
            return False
        
        config_years = set(str(y) for y in YEARS)
        issues = {}
        
        # Check planting_data
        planting_years = set()
        for row in self.planting_data:
            y = row.get("year", "").strip()
            if y:
                planting_years.add(y)
        
        invalid_planting = planting_years - config_years
        if invalid_planting:
            issues['data_planting.csv'] = sorted(invalid_planting)
        
        # Check notes_data
        notes_years = set()
        for row in self.notes_data:
            y = row.get("year", "").strip()
            if y:
                notes_years.add(y)
        
        invalid_notes = notes_years - config_years
        if invalid_notes:
            issues['data_notes.csv'] = sorted(invalid_notes)
        
        # Check varietals_data
        varietals_years = set()
        for row in self.varietals_data:
            y = row.get("year", "").strip()
            if y:
                varietals_years.add(y)
        
        invalid_varietals = varietals_years - config_years
        if invalid_varietals:
            issues['data_varietals.csv'] = sorted(invalid_varietals)
        
        # Report
        if issues:
            for filename, bad_years in issues.items():
                self.log_error(
                    f"{filename} contains years not in config: {', '.join(bad_years)}"
                )
            return False
        
        self.log_success(f"All years in CSVs are valid (config has: {', '.join(sorted(config_years))})")
        self.log_info(f"planting_data: {len(planting_years)} years, "
                     f"notes: {len(notes_years)} years, "
                     f"varietals: {len(varietals_years)} years")
        return True
    
    def validate_plant_names(self):
        """Check for plant name consistency between CSVs."""
        print(f"\n{BOLD}Validating plant names...{RESET}")
        
        if not self.planting_data or not self.varietals_data:
            self.log_warning("Skipping plant name validation (missing data)")
            return True
        
        # Get plant names from each source
        planting_plants = set()
        for row in self.planting_data:
            p = row.get("plant_name", "").strip()
            if p:
                planting_plants.add(p)
        
        varietals_cleaned = set()
        for row in self.varietals_data:
            seed_type = clean_seed_type(row.get("seed_type", "").strip())
            if seed_type:
                varietals_cleaned.add(seed_type)
        
        # Normalize for comparison
        planting_normalized = {normalize(p): p for p in planting_plants}
        varietals_normalized = {normalize(v): v for v in varietals_cleaned}
        
        # Plants in planting_data that may not match varietals
        unmatched = []
        manual_used = []
        for norm_name, actual_name in planting_normalized.items():
            if norm_name not in varietals_normalized and norm_name not in MANUAL_MAP:
                unmatched.append(actual_name)
            elif norm_name in MANUAL_MAP:
                manual_used.append((actual_name, MANUAL_MAP[norm_name]))
        
        # Report
        if manual_used:
            self.log_warning(f"MANUAL_MAP hacks are being used ({len(manual_used)}):")
            for plant, mapped_to in manual_used:
                self.log_info(f"  '{plant}' → '{mapped_to}'")
            self.log_warning("Consider fixing these in the CSV data instead of relying on MANUAL_MAP")
        
        if unmatched:
            self.log_warning(f"Plants in planting_data without varietals ({len(unmatched)}):")
            for plant in sorted(unmatched):
                self.log_info(f"  '{plant}' - may not have seed variety data")
        
        if not unmatched and not manual_used:
            self.log_success(f"All plant names well-matched ({len(planting_plants)} plants)")
        
        return len(unmatched) == 0 and len(manual_used) == 0
    
    def validate_categories(self):
        """Check for category consistency and coverage."""
        print(f"\n{BOLD}Validating categories...{RESET}")
        
        if not self.planting_data:
            self.log_warning("Skipping category validation (missing data)")
            return True
        
        categories = set()
        missing_categories = []
        
        for row in self.planting_data:
            cat = row.get("plant_category", "").strip()
            if cat:
                cleaned = clean_category(cat)
                categories.add(cleaned)
        
        for row in self.planting_data:
            if not row.get("plant_category", "").strip():
                plant = row.get("plant_name", "?")
                missing_categories.append(plant)
        
        if missing_categories:
            self.log_warning(f"Plants without category ({len(missing_categories)}):")
            for plant in missing_categories[:5]:
                self.log_info(f"  '{plant}'")
            if len(missing_categories) > 5:
                self.log_info(f"  ... and {len(missing_categories) - 5} more")
        else:
            self.log_success(f"All plants have categories ({len(categories)} categories)")
        
        return len(missing_categories) == 0
    
    def validate_columns(self):
        """Check that all required columns exist in CSV files."""
        print(f"\n{BOLD}Validating CSV columns...{RESET}")
        
        specs = {
            "data_planting.csv": {
                "data": self.planting_data,
                "required": ["year", "plant_name", "plant_category", "bed_name", "bed_location", "season"]
            },
            "data_notes.csv": {
                "data": self.notes_data,
                "required": ["year", "category", "note"]
            },
            "data_varietals.csv": {
                "data": self.varietals_data,
                "required": ["year", "seed_type", "varietal"]
            }
        }
        
        all_valid = True
        for filename, spec in specs.items():
            data = spec["data"]
            required = spec["required"]
            
            if not data:
                continue
            
            columns = set(data[0].keys()) if data else set()
            missing = set(required) - columns
            
            if missing:
                self.log_error(f"{filename} missing columns: {', '.join(missing)}")
                all_valid = False
            else:
                self.log_success(f"{filename} has all required columns")
        
        return all_valid
    
    def run_all(self):
        """Run all validations."""
        print(f"\n{BOLD}{'='*70}{RESET}")
        print(f"{BOLD}Garden Website Data Validation{RESET}")
        print(f"{BOLD}{'='*70}{RESET}")
        
        # Run checks in order
        checks = [
            ("Files exist", self.validate_files_exist),
            ("Columns", self.validate_columns),
            ("Years", self.validate_years),
            ("Categories", self.validate_categories),
            ("Plant names", self.validate_plant_names),
        ]
        
        results = {}
        for name, check in checks:
            try:
                results[name] = check()
            except Exception as e:
                self.log_error(f"Validation '{name}' crashed: {e}")
                results[name] = False
        
        # Summary
        print(f"\n{BOLD}{'='*70}{RESET}")
        print(f"{BOLD}Summary{RESET}")
        print(f"{BOLD}{'='*70}{RESET}")
        
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        
        print(f"Passed: {passed}/{total}")
        print(f"Errors: {len(self.errors)}")
        print(f"Warnings: {len(self.warnings)}")
        
        # Determine exit code
        if self.errors:
            print(f"\n{RED}{BOLD}❌ Validation FAILED - critical errors found{RESET}")
            return 2
        elif self.warnings:
            print(f"\n{YELLOW}{BOLD}⚠️  Validation PASSED with warnings{RESET}")
            return 1
        else:
            print(f"\n{GREEN}{BOLD}✅ Validation PASSED - all checks clean{RESET}")
            return 0

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Validate garden website data")
    parser.add_argument("--fix", action="store_true", help="Attempt auto-fixes")
    args = parser.parse_args()
    
    v = Validator()
    exit_code = v.run_all()
    
    if args.fix and v.warnings:
        print(f"\n{YELLOW}Auto-fix not yet implemented{RESET}")
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()

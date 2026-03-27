#!/usr/bin/env python3
"""
Build orchestrator for garden website generators.
Runs all generation scripts in sequence with error handling and reporting.

Usage:
    python build.py                          # Run all generators
    python build.py --validate               # Validate data, then build
    python build.py --script generate_garden_pages.py    # Run specific generator
    python build.py --validate --script generate_garden_notes.py  # Validate then run one script

Exit codes:
    0 = Success
    1 = Build failed (critical errors)
    2 = Validation failed (critical errors)
"""

import sys
import subprocess
import time
from pathlib import Path
from datetime import datetime
import argparse

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

SCRIPTS = [
    "generate_garden_pages.py",
    "generate_garden_notes.py",
    "generate_plant_list_page.py",
    "generate_varietals_page.py",
    "generate_weather_page.py",
]

def print_header(title):
    """Print a formatted section header."""
    print(f"\n{BOLD}{BLUE}{'='*70}{RESET}")
    print(f"{BOLD}{BLUE}{title:^70}{RESET}")
    print(f"{BOLD}{BLUE}{'='*70}{RESET}\n")

def print_success(msg):
    """Print a success message."""
    print(f"{GREEN}✅ {msg}{RESET}")

def print_error(msg):
    """Print an error message."""
    print(f"{RED}❌ {msg}{RESET}")

def print_warning(msg):
    """Print a warning message."""
    print(f"{YELLOW}⚠️  {msg}{RESET}")

def print_info(msg):
    """Print an info message."""
    print(f"{BLUE}ℹ️  {msg}{RESET}")

def validate_dependencies():
    """Check that all necessary files exist and dependencies are available."""
    print_header("Validating Dependencies")
    
    required_files = ["config.yaml", "utils.py"]
    for fname in required_files:
        if not Path(fname).exists():
            print_error(f"Missing required file: {fname}")
            return False
        print_success(f"Found {fname}")
    
    required_packages = []
    try:
        import yaml
        print_success("PyYAML is available")
    except ImportError:
        required_packages.append("pyyaml")
    
    if required_packages:
        print_warning(f"Missing packages: {', '.join(required_packages)}")
        print_info(f"Install with: pip install {' '.join(required_packages)}")
        return False
    
    return True

def run_script(script_name):
    """Run a single generation script.
    
    Args:
        script_name: Name of the script to run
    
    Returns:
        Tuple of (success: bool, output: str, elapsed_time: float)
    """
    if not Path(script_name).exists():
        return False, f"Script not found: {script_name}", 0
    
    print_info(f"Running: {script_name}")
    
    start_time = time.time()
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout per script
        )
        elapsed = time.time() - start_time
        
        if result.returncode == 0:
            output = result.stdout
            return True, output, elapsed
        else:
            error = result.stderr or result.stdout or "Unknown error"
            return False, error, elapsed
            
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start_time
        return False, f"Script timeout (>5 min)", elapsed
    except Exception as e:
        elapsed = time.time() - start_time
        return False, str(e), elapsed

def main():
    parser = argparse.ArgumentParser(
        description="Build orchestrator for garden website"
    )
    parser.add_argument(
        "--script",
        type=str,
        help="Run specific script instead of all"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Run validation before building"
    )
    args = parser.parse_args()
    
    print(f"\n{BOLD}Garden Website Builder{RESET}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Run validation if requested
    if args.validate:
        print_header("Running Data Validation")
        try:
            import validate
            validator = validate.Validator()
            validation_result = validator.run_all()
            if validation_result == 2:
                print_error("Validation found critical errors - aborting build")
                sys.exit(1)
            elif validation_result == 1:
                print_warning("Validation found warnings - proceeding with build")
        except Exception as e:
            print_error(f"Validation failed: {e}")
            sys.exit(1)
    
    # Validate dependencies
    if not validate_dependencies():
        print_error("Dependency validation failed")
        sys.exit(1)
    
    # Determine which scripts to run
    if args.script:
        scripts_to_run = [args.script]
    else:
        scripts_to_run = SCRIPTS
    
    # Run scripts
    print_header(f"Running {len(scripts_to_run)} Generator(s)")
    
    results = {}
    total_time = 0
    
    for script in scripts_to_run:
        success, output, elapsed = run_script(script)
        results[script] = (success, output, elapsed)
        total_time += elapsed
        
        if success:
            print_success(f"{script} completed in {elapsed:.2f}s")
            # Print first few lines of output
            lines = output.strip().split('\n')
            for line in lines[:3]:
                print(f"  {line}")
        else:
            print_error(f"{script} failed after {elapsed:.2f}s")
            print(f"  Error: {output[:200]}")
    
    # Summary
    print_header("Build Summary")
    
    passed = sum(1 for success, _, _ in results.values() if success)
    failed = len(results) - passed
    
    print(f"Total scripts: {len(results)}")
    print_success(f"Passed: {passed}")
    if failed > 0:
        print_error(f"Failed: {failed}")
    print_info(f"Total time: {total_time:.2f}s")
    
    if failed > 0:
        print_header("Failed Scripts Details")
        for script, (success, output, elapsed) in results.items():
            if not success:
                print_error(f"\n{script}:")
                print(output)
        sys.exit(1)
    
    print(f"\n{GREEN}{BOLD}✅ All generators completed successfully!{RESET}\n")
    sys.exit(0)

if __name__ == "__main__":
    main()

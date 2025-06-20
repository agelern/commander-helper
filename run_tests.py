#!/usr/bin/env python3
"""
Test runner script for the Commander Helper Discord Bot.

See README.md for full usage instructions.
This script is the recommended way to run tests and coverage for the project.

Provides an easy way to run different types of tests:
- Unit tests only
- Integration tests only
- All tests
- Tests with coverage
- Performance tests
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print('='*60)
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"\n✅ {description} completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {description} failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"\n❌ Command not found: {cmd[0]}")
        print("Make sure pytest is installed: pip install pytest pytest-asyncio pytest-cov")
        return False


def main():
    parser = argparse.ArgumentParser(description="Run tests for Commander Helper Discord Bot")
    parser.add_argument(
        "--type",
        choices=["unit", "integration", "all", "coverage", "performance"],
        default="all",
        help="Type of tests to run (default: all)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Run tests in verbose mode"
    )
    parser.add_argument(
        "--fast", "-f",
        action="store_true",
        help="Skip slow tests"
    )
    parser.add_argument(
        "--output", "-o",
        choices=["console", "html", "xml"],
        default="console",
        help="Coverage output format (default: console)"
    )
    
    args = parser.parse_args()
    
    # Base pytest command
    base_cmd = [sys.executable, "-m", "pytest"]
    
    if args.verbose:
        base_cmd.append("-v")
    
    if args.fast:
        base_cmd.extend(["-m", "not slow"])
    
    # Configure coverage output
    if args.output == "html":
        base_cmd.extend(["--cov-report=html:htmlcov"])
    elif args.output == "xml":
        base_cmd.extend(["--cov-report=xml"])
    
    success = True
    
    if args.type == "unit":
        # Run only unit tests
        cmd = base_cmd + ["-m", "unit", "tests/"]
        success = run_command(cmd, "Unit Tests")
        
    elif args.type == "integration":
        # Run only integration tests
        cmd = base_cmd + ["-m", "integration", "tests/"]
        success = run_command(cmd, "Integration Tests")
        
    elif args.type == "coverage":
        # Run all tests with coverage
        cmd = base_cmd + [
            "--cov=src",
            "--cov-report=term-missing",
            "--cov-fail-under=80",
            "tests/"
        ]
        success = run_command(cmd, "Tests with Coverage")
        
    elif args.type == "performance":
        # Run performance tests
        cmd = base_cmd + ["-m", "performance", "tests/"]
        success = run_command(cmd, "Performance Tests")
        
    else:  # all
        # Run all tests
        cmd = base_cmd + ["tests/"]
        success = run_command(cmd, "All Tests")
    
    # Print summary
    print(f"\n{'='*60}")
    if success:
        print("🎉 All tests completed successfully!")
    else:
        print("💥 Some tests failed!")
        sys.exit(1)
    print('='*60)


if __name__ == "__main__":
    main() 
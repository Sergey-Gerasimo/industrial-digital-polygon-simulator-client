#!/usr/bin/env python3
"""
Script to run integration tests with Docker Compose setup.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_integration_tests():
    """Run integration tests."""
    project_root = Path(__file__).parent.parent

    print("Running integration tests...")

    # Change to project root
    os.chdir(project_root)

    # Run pytest with integration tests
    # Check if we're running in poetry environment
    try:
        import subprocess
        result = subprocess.run(["poetry", "run", "python", "-c", "import pytest"], capture_output=True)
        if result.returncode == 0:
            # Use poetry run
            cmd = [
                "poetry", "run", "pytest",
                "tests/integration/",
                "--tb=short",
                "--verbose",
                "-x",  # Stop on first failure
            ]
        else:
            # Use direct python
            cmd = [
                sys.executable, "-m", "pytest",
                "tests/integration/",
                "--tb=short",
                "--verbose",
                "-x",  # Stop on first failure
            ]
    except Exception:
        # Fallback to direct python
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/integration/",
            "--tb=short",
            "--verbose",
            "-x",  # Stop on first failure
        ]

    try:
        result = subprocess.run(cmd, check=True)
        print("Integration tests completed successfully!")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"Integration tests failed with exit code {e.returncode}")
        return e.returncode


if __name__ == "__main__":
    sys.exit(run_integration_tests())

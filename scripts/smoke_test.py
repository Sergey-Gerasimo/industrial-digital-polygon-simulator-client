#!/usr/bin/env python3
"""
Smoke tests - quick check of service availability.
"""

import asyncio
import sys
import subprocess


def get_pytest_cmd():
    """Get pytest command (with poetry if available)."""
    try:
        result = subprocess.run(["poetry", "run", "python", "-c", "import pytest"], capture_output=True, text=True)
        if result.returncode == 0:
            return ["poetry", "run", "pytest"]
    except Exception:
        pass
    return [sys.executable, "-m", "pytest"]


async def run_smoke_tests():
    """Run smoke tests."""
    cmd = get_pytest_cmd() + [
        "tests/integration/test_service_availability.py",
        "--tb=short",
        "--verbose",
        "-x",  # Stop on first failure
    ]

    print("Running smoke tests...")

    try:
        result = subprocess.run(cmd, check=True)
        print("✅ Smoke tests passed!")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Smoke tests failed with exit code {e.returncode}")
        return e.returncode


if __name__ == "__main__":
    exit_code = asyncio.run(run_smoke_tests())
    sys.exit(exit_code)

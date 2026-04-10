"""Test running utilities for the API."""

import subprocess
import json
import sys
import re
from typing import Dict, Any
import os


class TestRunner:
    """Runs pytest and returns results in a structured format."""

    @staticmethod
    def run_all_tests() -> Dict[str, Any]:
        """Run all tests and return results."""
        try:
            backend_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=backend_path,
            )

            return TestRunner._parse_pytest_output(result.stdout, result.returncode)
        except FileNotFoundError:
            return {
                "status": "error",
                "error_message": "pytest not found. Install with: pip install pytest pytest-asyncio",
                "raw_output": "",
            }
        except Exception as e:
            return {
                "status": "error",
                "error_message": str(e),
                "raw_output": "",
            }

    @staticmethod
    def run_specific_test_module(module_name: str) -> Dict[str, Any]:
        """Run a specific test module."""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", f"tests/{module_name}.py", "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=60,
            )
            return TestRunner._parse_pytest_output(result.stdout, result.returncode)
        except Exception as e:
            return {
                "status": "error",
                "error_message": str(e),
            }

    @staticmethod
    def _parse_pytest_output(output: str, returncode: int) -> Dict[str, Any]:
        """Parse pytest output to extract test results."""
        lines = output.split("\n")

        # Extract summary from the last lines
        passed = 0
        failed = 0
        errors = 0
        skipped = 0

        # Look for the summary line (e.g., "10 passed in 0.50s")
        for line in reversed(lines):
            if "passed" in line or "failed" in line or "error" in line:
                passed_match = re.search(r"(\d+)\s+passed", line)
                if passed_match:
                    passed = int(passed_match.group(1))

                failed_match = re.search(r"(\d+)\s+failed", line)
                if failed_match:
                    failed = int(failed_match.group(1))

                error_match = re.search(r"(\d+)\s+error", line)
                if error_match:
                    errors = int(error_match.group(1))

                skip_match = re.search(r"(\d+)\s+skipped", line)
                if skip_match:
                    skipped = int(skip_match.group(1))

                break

        tests = []
        for line in lines:
            if "PASSED" in line and "::" in line:
                test_name = (
                    line.split("::")[1].split()[0] if len(line.split("::")) > 1 else "unknown"
                )
                tests.append({"name": test_name, "status": "PASSED"})
            elif "FAILED" in line and "::" in line:
                test_name = (
                    line.split("::")[1].split()[0] if len(line.split("::")) > 1 else "unknown"
                )
                tests.append({"name": test_name, "status": "FAILED"})

        return {
            "status": "success" if returncode == 0 else "failure",
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "skipped": skipped,
            "total": passed + failed + errors + skipped,
            "tests": tests[:20],  # Limit to first 20 tests in response
            "raw_output": output[-2000:] if len(output) > 2000 else output,  # Last 2000 chars
        }

    @staticmethod
    def get_test_summary() -> Dict[str, Any]:
        """Get a summary of all available tests."""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "tests/", "--collect-only", "-q"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            tests = []
            for line in result.stdout.split("\n"):
                if "::" in line and line.strip():
                    tests.append(line.strip())

            return {
                "status": "success",
                "total_tests": len(tests),
                "tests": tests,
            }
        except Exception as e:
            return {
                "status": "error",
                "error_message": str(e),
            }

    @staticmethod
    def get_infrastructure_status() -> Dict[str, Any]:
        """Get status of backend infrastructure."""
        return {
            "status": "operational",
            "components": {
                "api": "operational",
                "database": "operational (in-memory)",
                "services": {
                    "step_loader": "ready (MOCK)",
                    "parts_extractor": "ready (MOCK)",
                    "svg_generator": "ready (MOCK)",
                    "assembly_generator": "ready (MOCK)",
                },
                "progress_tracking": "operational",
            },
            "test_infrastructure": "ready",
            "test_files": {
                "test_step_loader.py": "available",
                "test_parts_extractor.py": "available",
                "test_svg_generator.py": "available",
                "test_assembly_generator.py": "available",
                "test_api_endpoints.py": "available",
            },
        }

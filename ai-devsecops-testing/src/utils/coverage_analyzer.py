"""
Coverage Analyzer
=================
Pokrece postojece testove preko `coverage` paketa i vraca listu linija/funkcija
koje NISU pokrivene. Ovo se koristi u koraku 3 workflow-a iz Poglavlja 4.2.1
("Analiza pokrivenosti").
"""

import ast
import subprocess
import sys
from dataclasses import dataclass
from typing import List


@dataclass
class CoverageReport:
    percent_covered: float
    uncovered_lines: List[int]
    uncovered_functions: List[str]


def run_pytest_coverage(source_file: str, test_dir: str = "tests") -> CoverageReport:
    """Pokrece pytest sa coverage instrumentacijom nad source_file.

    Zahteva instalirane pakete: pytest, pytest-cov (videti requirements.txt).
    """
    module = source_file.replace("/", ".").rstrip(".py")

    result = subprocess.run(
        [
            sys.executable, "-m", "pytest", test_dir,
            f"--cov={module}",
            "--cov-report=json:coverage.json",
            "-q",
        ],
        capture_output=True,
        text=True,
    )

    import json
    import os

    if not os.path.exists("coverage.json"):
        # Nema testova ili je doslo do greske - vrati 0% pokrivenost
        return CoverageReport(
            percent_covered=0.0,
            uncovered_lines=[],
            uncovered_functions=_all_functions(source_file),
        )

    with open("coverage.json") as f:
        cov_data = json.load(f)

    file_data = cov_data.get("files", {}).get(source_file, {})
    percent = file_data.get("summary", {}).get("percent_covered", 0.0)
    missing_lines = file_data.get("missing_lines", [])

    uncovered_funcs = _functions_containing_lines(source_file, missing_lines)

    return CoverageReport(
        percent_covered=percent,
        uncovered_lines=missing_lines,
        uncovered_functions=uncovered_funcs,
    )


def _all_functions(source_file: str) -> List[str]:
    with open(source_file, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read())
    return [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]


def _functions_containing_lines(source_file: str, lines: List[int]) -> List[str]:
    with open(source_file, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read())

    result = []
    line_set = set(lines)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            func_lines = set(range(node.lineno, node.end_lineno + 1))
            if func_lines & line_set:
                result.append(node.name)
    return result

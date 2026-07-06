"""
AI Test Generator
==================
Servis koji analizira izvorni kod (Python funkcije/klase) i automatski
generise pytest test slucajeve koriscenjem Claude API-ja.

Ovo je centralna komponenta opisana u Poglavlju 4.2 i 5.2 diplomskog rada.
"""

import ast
import os
import re
import textwrap
from dataclasses import dataclass, field
from typing import List, Optional

from anthropic import Anthropic


# --------------------------------------------------------------------------
# Data modeli
# --------------------------------------------------------------------------

@dataclass
class TestGenerationRequest:
    source_code: str
    function_name: str
    language: str = "python"
    existing_tests: Optional[str] = None
    docstring: Optional[str] = None
    security_focus: bool = False


@dataclass
class GeneratedTestSuite:
    test_code: str
    test_count: int
    security_tests: int
    explanation: str = ""


# --------------------------------------------------------------------------
# System prompt - definise "personu" i pravila za model
# --------------------------------------------------------------------------

SYSTEM_PROMPT = """Ti si senior softverski inzenjer specijalizovan za testiranje.
Pisi pytest testove koji su:
- Sveobuhvatni: pokrivaju happy path, edge cases i error scenarios
- Odrzivi: jasni, dobro dokumentovani, bez nepotrebnih duplikacija
- Efikasni: brzi za izvrsavanje, bez suvisnih zavisnosti
- Bezbedni: testiraju input validaciju i, kada je relevantno,
  bezbednosne scenarije (SQL injection, XSS, auth bypass)

Format odgovora: vrati ISKLJUCIVO Python kod u jednom code bloku,
bez ikakvog objasnjenja van komentara u samom kodu."""


class AITestGenerator:
    """AI servis za automatsko generisanje unit testova."""

    def __init__(self, model: str = "claude-opus-4-5", api_key: Optional[str] = None):
        # Ako api_key nije prosledjen, klijent ce sam citati ANTHROPIC_API_KEY iz env-a
        self.client = Anthropic(api_key=api_key) if api_key else Anthropic()
        self.model = model

    # ------------------------------------------------------------------
    # Analiza pokrivenosti - koje funkcije nemaju testove
    # ------------------------------------------------------------------
    def analyze_coverage_gaps(self, source_file: str, test_file: Optional[str] = None) -> List[str]:
        """Vraca listu imena funkcija iz source_file koje NEMAJU odgovarajuci test.

        Pojednostavljena heuristika (bez pokretanja coverage.py): trazi se
        da li se za svaku definisanu funkciju pojavljuje 'test_<ime>' u
        test fajlu. Za realnu coverage analizu koristiti `coverage` paket
        (vidi run_pytest_coverage u utils/coverage_analyzer.py).
        """
        with open(source_file, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())

        function_names = [
            node.name for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")
        ]

        existing_test_names = set()
        if test_file and os.path.exists(test_file):
            with open(test_file, "r", encoding="utf-8") as f:
                existing_test_names = set(re.findall(r"def (test_\w+)", f.read()))

        uncovered = [
            fn for fn in function_names
            if not any(fn in t for t in existing_test_names)
        ]
        return uncovered

    # ------------------------------------------------------------------
    # Generisanje testova pozivom Claude API-ja
    # ------------------------------------------------------------------
    def generate_tests(self, request: TestGenerationRequest) -> GeneratedTestSuite:
        """Generise testove za specificnu funkciju/klasu."""
        prompt = self._build_prompt(request)

        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            temperature=0.2,  # nizak temperature radi konzistentnosti
            messages=[{"role": "user", "content": prompt}],
        )

        raw_text = response.content[0].text
        test_code = self._extract_code(raw_text)
        return self._package(test_code)

    def _build_prompt(self, req: TestGenerationRequest) -> str:
        parts = [
            f"Generisi pytest testove za sledecu {req.language} funkciju/klasu:",
            f"```{req.language}",
            req.source_code,
            "```",
        ]
        if req.docstring:
            parts.append(f"\nDodatni kontekst: {req.docstring}")
        if req.existing_tests:
            parts.append("\nPostojeci testovi (NE DUPLIRAJ ih, dopuni ih):")
            parts.append(req.existing_tests)
        if req.security_focus:
            parts.append(
                "\nPoseban fokus: dodaj bezbednosne test scenarije "
                "(SQL injection, XSS, auth bypass, input fuzzing) gde je primenljivo."
            )
        return "\n".join(parts)

    @staticmethod
    def _extract_code(text: str) -> str:
        """Izvlaci kod iz Markdown code bloka ako postoji."""
        match = re.search(r"```(?:python)?\n(.*?)```", text, re.DOTALL)
        return match.group(1).strip() if match else text.strip()

    @staticmethod
    def _package(test_code: str) -> GeneratedTestSuite:
        test_count = len(re.findall(r"def test_\w+", test_code))
        security_count = len(re.findall(
            r"(sql|injection|xss|auth|security|exploit)", test_code, re.IGNORECASE
        ))
        return GeneratedTestSuite(
            test_code=test_code,
            test_count=test_count,
            security_tests=security_count,
        )


# --------------------------------------------------------------------------
# CLI - omogucava direktno pokretanje: python -m ai_engine.test_generator
# --------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="AI Test Generator CLI")
    parser.add_argument("--source", required=True, help="Putanja do .py fajla sa kodom")
    parser.add_argument("--output", default=None, help="Gde sacuvati generisane testove")
    parser.add_argument("--security-focus", action="store_true")
    args = parser.parse_args()

    with open(args.source, "r", encoding="utf-8") as f:
        code = f.read()

    generator = AITestGenerator()
    result = generator.generate_tests(
        TestGenerationRequest(
            source_code=code,
            function_name=os.path.basename(args.source),
            security_focus=args.security_focus,
        )
    )

    output_path = args.output or f"tests/test_{os.path.basename(args.source)}"
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(result.test_code)

    print(f"Generisano {result.test_count} testova ({result.security_tests} bezbednosnih) -> {output_path}")

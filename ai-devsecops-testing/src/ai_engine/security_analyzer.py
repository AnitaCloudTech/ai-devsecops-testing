"""
AI Security Analyzer
=====================
Proширује mogucnosti tradicionalnih SAST alata (npr. SonarQube) koriscenjem
LLM-a za semanticko razumevanje koda i procenu verovatnoce lazno pozitivnog
nalaza (Poglavlje 4.3 / 5.4 diplomskog rada).
"""

import json
from dataclasses import dataclass
from enum import Enum
from typing import List

from anthropic import Anthropic


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


@dataclass
class SecurityFinding:
    severity: Severity
    category: str
    description: str
    line_number: int
    code_snippet: str
    recommendation: str
    cwe_id: str
    false_positive_probability: float  # 0.0 - 1.0


SECURITY_SYSTEM_PROMPT = """Ti si senior aplikacijski bezbednosni inzenjer sa 10+ godina iskustva.
Analiziraj prosledjeni kod i identifikuj bezbednosne ranjivosti.

Za svaku ranjivost navedi:
- tip ranjivosti (OWASP kategorija) i CWE ID
- ozbiljnost (CRITICAL / HIGH / MEDIUM / LOW / INFO)
- opis i potencijalni impact
- konkretnu preporuku za ispravku
- procenu verovatnoce da je nalaz lazno pozitivan (0.0 - 1.0)

VRLO VAZNO: Odgovori ISKLJUCIVO validnim JSON nizom objekata, bez Markdown
formatiranja, bez uvodnog teksta. Svaki objekat mora imati tacno ova polja:
severity, category, description, line_number, code_snippet, recommendation,
cwe_id, false_positive_probability.

Ako kod nema ranjivosti, vrati prazan niz: []"""


class AISecurityAnalyzer:
    """AI servis za semanticku bezbednosnu analizu izvornog koda."""

    def __init__(self, model: str = "claude-opus-4-5"):
        self.client = Anthropic()
        self.model = model

    def analyze(self, code: str, language: str = "python") -> List[SecurityFinding]:
        prompt = f"Analiziraj ovaj {language} kod:\n```{language}\n{code}\n```"

        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=SECURITY_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        return self._parse_findings(response.content[0].text)

    def triage_sast_warning(self, sast_tool: str, rule_id: str, code_context: str) -> SecurityFinding:
        """Kontekstualizuje POJEDINACNO upozorenje iz spoljasnjeg SAST alata
        (npr. SonarQube) i vraca AI ocenu - koristi se za smanjenje broja
        lazno pozitivnih rezultata (Poglavlje 4.3.1)."""
        prompt = (
            f"Alat '{sast_tool}' je prijavio pravilo '{rule_id}' na sledecem kodu:\n"
            f"```\n{code_context}\n```\n"
            "Oceni da li je ovo STVARNA ranjivost ili lazno pozitivan nalaz, "
            "uzimajuci u obzir kontekst (npr. da li je ulaz vec saniran ranije u toku)."
        )
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=SECURITY_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        findings = self._parse_findings(response.content[0].text)
        return findings[0] if findings else SecurityFinding(
            severity=Severity.INFO,
            category="unknown",
            description="Model nije vratio strukturirani nalaz.",
            line_number=0,
            code_snippet=code_context[:200],
            recommendation="Rucna provera preporucena.",
            cwe_id="N/A",
            false_positive_probability=0.5,
        )

    @staticmethod
    def _parse_findings(raw_text: str) -> List[SecurityFinding]:
        text = raw_text.strip()
        # ukloni eventualne markdown ograde ako ih model ipak doda
        if text.startswith("```"):
            text = text.strip("`")
            text = text.replace("json\n", "", 1)

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return []

        findings = []
        for item in data:
            try:
                findings.append(SecurityFinding(
                    severity=Severity(item.get("severity", "INFO")),
                    category=item.get("category", "unknown"),
                    description=item.get("description", ""),
                    line_number=int(item.get("line_number", 0)),
                    code_snippet=item.get("code_snippet", ""),
                    recommendation=item.get("recommendation", ""),
                    cwe_id=item.get("cwe_id", "N/A"),
                    false_positive_probability=float(item.get("false_positive_probability", 0.5)),
                ))
            except (ValueError, KeyError):
                continue
        return findings


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="AI Security Analyzer CLI")
    parser.add_argument("--source", required=True)
    parser.add_argument("--fail-on", default="HIGH", choices=["CRITICAL", "HIGH", "MEDIUM", "LOW"])
    args = parser.parse_args()

    with open(args.source, "r", encoding="utf-8") as f:
        code = f.read()

    analyzer = AISecurityAnalyzer()
    findings = analyzer.analyze(code)

    severity_order = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "INFO": 0}
    threshold = severity_order[args.fail_on]

    print(f"Pronadjeno {len(findings)} nalaza:\n")
    should_fail = False
    for finding in findings:
        print(f"[{finding.severity.value}] {finding.category} (linija {finding.line_number})")
        print(f"  CWE: {finding.cwe_id} | FP verovatnoca: {finding.false_positive_probability:.0%}")
        print(f"  {finding.description}")
        print(f"  -> {finding.recommendation}\n")
        if severity_order[finding.severity.value] >= threshold and finding.false_positive_probability < 0.5:
            should_fail = True

    if should_fail:
        print(f"BUILD FAILED: pronadjeni nalazi ozbiljnosti >= {args.fail_on}")
        exit(1)
    print("Provera prosla.")

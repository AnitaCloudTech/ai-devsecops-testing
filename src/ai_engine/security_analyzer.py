"""
AI Security Analyzer
=====================
Proширује mogucnosti tradicionalnih SAST alata (npr. SonarQube) koriscenjem
LLM-a za semanticko razumevanje koda i procenu verovatnoce lazno pozitivnog
nalaza (Poglavlje 4.3 / 5.4 diplomskog rada).
"""
import json
import os
import google.generativeai as genai
from dataclasses import dataclass
from enum import Enum
from typing import List

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
    false_positive_probability: float

SECURITY_SYSTEM_PROMPT = """Ti si senior aplikacijski bezbednosni inzenjer.
Analiziraj kod i identifikuj ranjivosti. Odgovori ISKLJUCIVO validnim JSON nizom objekata."""

class AISecurityAnalyzer:
    def __init__(self):
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY nije postavljen!")
        
        genai.configure(api_key=api_key)
        
        # Automatsko pronalaženje prvog dostupnog modela koji podržava generateContent
        available_models = [
            m.name for m in genai.list_models() 
            if 'generateContent' in m.supported_generation_methods
        ]
        
        if not available_models:
            raise RuntimeError("Nijedan model nije dostupan za generisanje sadržaja.")
            
        # Prioritetno biramo flash ili pro, ako ne, uzimamo prvi dostupni
        model_name = next((m for m in available_models if "gemini-1.5" in m), available_models[0])
        print(f"Koristim model: {model_name}")
        
        self.model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=SECURITY_SYSTEM_PROMPT
        )

    def analyze(self, code: str, language: str = "python") -> List[SecurityFinding]:
        prompt = f"Analiziraj ovaj {language} kod:\n```{language}\n{code}\n```"
        response = self.model.generate_content(prompt)
        return self._parse_findings(response.text)

    @staticmethod
    def _parse_findings(raw_text: str) -> List[SecurityFinding]:
        # Čišćenje teksta u slučaju da model doda markdown
        text = raw_text.replace("```json", "").replace("```", "").strip()
        try:
            data = json.loads(text)
            findings = []
            for item in data:
                findings.append(SecurityFinding(
                    severity=Severity(item.get("severity", "INFO")),
                    category=item.get("category", "unknown"),
                    description=item.get("description", ""),
                    line_number=int(item.get("line_number", 0)),
                    code_snippet=item.get("code_snippet", ""),
                    recommendation=item.get("recommendation", ""),
                    cwe_id=item.get("cwe_id", "N/A"),
                    false_positive_probability=float(item.get("false_positive_probability", 0.5))
                ))
            return findings
        except:
            return []

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    args = parser.parse_args()

    with open(args.source, "r", encoding="utf-8") as f:
        code = f.read()

    analyzer = AISecurityAnalyzer()
    findings = analyzer.analyze(code)

    for f in findings:
        print(f"[{f.severity}] {f.category} (Linija {f.line_number}) -> {f.description}")

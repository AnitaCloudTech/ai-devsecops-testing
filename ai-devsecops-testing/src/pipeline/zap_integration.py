"""
ZAP Integration
================
Cita OWASP ZAP JSON izvestaj i koristi AISecurityAnalyzer da triage-uje
(kontekstualizuje) svaki nalaz - u skladu sa Poglavljem 2.2.4 / 4.4.
"""

import argparse
import json
import sys

from src.ai_engine.security_analyzer import AISecurityAnalyzer


def load_zap_report(path: str) -> list:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    alerts = []
    for site in data.get("site", []):
        alerts.extend(site.get("alerts", []))
    return alerts


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", required=True, help="Putanja do ZAP report_json.json")
    parser.add_argument("--fail-on-high", action="store_true")
    args = parser.parse_args()

    alerts = load_zap_report(args.report)
    if not alerts:
        print("ZAP nije prijavio nalaze.")
        return

    analyzer = AISecurityAnalyzer()
    high_confirmed = 0

    for alert in alerts:
        name = alert.get("name", "unknown")
        risk = alert.get("riskdesc", "")
        instances = alert.get("instances", [])
        snippet = instances[0].get("evidence", "") if instances else ""

        finding = analyzer.triage_sast_warning(
            sast_tool="OWASP ZAP",
            rule_id=name,
            code_context=f"Rizik: {risk}\nDokaz: {snippet}",
        )

        print(f"[{finding.severity.value}] {name} - FP verovatnoca: {finding.false_positive_probability:.0%}")
        print(f"  {finding.recommendation}\n")

        if finding.severity.value in ("CRITICAL", "HIGH") and finding.false_positive_probability < 0.4:
            high_confirmed += 1

    if args.fail_on_high and high_confirmed > 0:
        print(f"BUILD FAILED: {high_confirmed} potvrdjenih HIGH/CRITICAL nalaza.")
        sys.exit(1)


if __name__ == "__main__":
    main()

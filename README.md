# ai-devsecops-testing
AI-powered testing framework for DevSecOps pipelines — automated test case generation, vulnerability detection, and CI/CD integration using LLMs.

AI-Driven DevSecOps Security Testing is a prototype developed as part of a bachelor's thesis. The project demonstrates how Artificial Intelligence can be integrated into a DevSecOps pipeline to automate the interpretation and prioritization of security vulnerabilities detected during application security testing.

## Features

- Automated CI/CD pipeline using GitHub Actions
- Automated OWASP ZAP security scanning
- SonarQube static code quality analysis
- AI-powered semantic interpretation of vulnerabilities
- Risk prioritization based on contextual analysis
- False positive probability estimation
- Structured security recommendations
- Modular architecture with AI model discovery support

## Technology Stack

- Python 3.11+
- Google Gemini API (gemini-2.5-flash)
- OWASP ZAP
- GitHub Actions
- SonarQube
- Docker
- JSON

## Project Structure

```
ai-devsecops-testing/
│
├── src/
│   ├── ai_engine/
│   ├── models/
│   ├── parsers/
│   └── reporting/
│
├── examples/
├── tests/
├── requirements.txt
└── README.md
```

## Installation

Clone the repository:

```bash
git clone https://github.com/AnitaCloudTech/ai-devsecops-testing.git
cd ai-devsecops-testing
```

Create a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

Set your Google Gemini API key:

Linux/macOS

```bash
export GEMINI_API_KEY="YOUR_API_KEY"
```

Windows (PowerShell)

```powershell
$env:GEMINI_API_KEY="YOUR_API_KEY"
```

## Usage

Run the security analyzer:

```bash
python3 src/ai_engine/security_analyzer.py --source zap_report.json
```

## Architecture

The system consists of four main components:

1. **Data Ingestion**
   - Parses OWASP ZAP JSON reports.

2. **AI Security Engine**
   - Sends vulnerability information to the Gemini API.
   - Performs contextual security analysis.
   - Estimates false positive probability.

3. **Risk Prioritization**
   - Assigns severity levels.
   - Generates remediation recommendations.

4. **Reporting**
   - Produces structured security findings.

## Future Improvements

- Support for additional LLM providers
- Integration with CI/CD platforms
- Automatic pull request review
- Support for SAST and dependency scanning
- Dashboard for vulnerability visualization

## License

This project was developed for academic purposes as part of a Bachelor's Thesis at the Faculty of Engineering, University of Kragujevac.

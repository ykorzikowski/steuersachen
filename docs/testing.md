# Testing Guide

## Setup
```bash
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
```

## Lint
```bash
ruff check modules/gf_gehalt modules/utils/helper tests
```

## Type Checks
```bash
mypy
```

## Unit Tests
```bash
pytest -m "not e2e"
```

## E2E Tests
```bash
pytest -m e2e
```

The e2e suite generates deterministic regression artifacts in:
- `.test-artifacts/e2e/steuersachen_report.json`

## Coverage XML (CI/SonarQube)
```bash
pytest --cov=modules/gf_gehalt --cov=modules/utils/helper --cov-report=xml:coverage.xml
```

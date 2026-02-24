# Steuersachen

Ein kleiner Rechner zur Berechnung von Einkommenssteuer und Gehaltsoptimierung für geschäftsführende Gesellschafter einer Kapitalgesellschaft. 

Gehostete Version: https://steuersachen.swokiz.com/

## Setup Local Dev
1. Setup python env (Python 3.12)
```
python3.12 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
pip3 install -r requirements-dev.txt
```

## Qualitätschecks und Tests
Alle Befehle sind im Projekt-Root auszuführen.

```
python3 -m ruff check .
python3 -m mypy
python3 -m pytest -m "not e2e"
python3 -m pytest -m e2e
python3 -m pytest --cov=. --cov-report=xml:coverage.xml
test -f coverage.xml
```

Details und Hinweise: [docs/testing.md](docs/testing.md)

## Docker Compose

docker-compose build
docker-compose up (add -d for run as daemon)

import json
from pathlib import Path

import pytest

from modules.gf_gehalt.service import (
    CalculationInput,
    calculate_business_report,
    write_report_artifact,
)

ARTIFACT_PATH = Path(".test-artifacts/e2e/steuersachen_report.json")


@pytest.mark.e2e
def test_e2e_report_artifact_regression() -> None:
    report = calculate_business_report(
        CalculationInput(
            steuerjahr=2025,
            gwst_hebesatz=350,
            gmbh_umsatz=220000,
            gmbh_kosten=25000,
            gf_gehalt=48000,
            andere_einkommen=5000,
            sonstige_absetzbare_ausgaben=6000,
            gkv=True,
            kv_zusatzbeitrag=2.45,
            krankentagegeld=True,
            pv_zuschlag=True,
            verheiratet=True,
            ehepartner_zve=10000,
        )
    )

    output_file = write_report_artifact(report, str(ARTIFACT_PATH))
    artifact = json.loads(Path(output_file).read_text(encoding="utf-8"))

    assert Path(output_file).exists()
    assert artifact["steuerjahr"] == 2025
    assert artifact["gmbh_gewinn_vor_steuern"] == 147000
    assert artifact["gmbh_steuern_gesamt"] == 41160.0
    assert artifact["einkommensteuer"] == 4418.29
    assert artifact["gesamter_nettoerloes"] == 143159.21
    assert artifact["gesamte_abgaben"] == 56840.79
    assert artifact["gesamte_abgaben_prozentual"] == 34.93

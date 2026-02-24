from modules.gf_gehalt.service import CalculationInput, calculate_business_report
from modules.utils.helper import Helper


def test_calculate_business_report_baseline_values() -> None:
    report = calculate_business_report(CalculationInput())

    assert report["steuerjahr"] == 2025
    assert report["gmbh_gewinn_vor_steuern"] == 125000
    assert report["gmbh_steuern_gesamt"] == 30625.0
    assert report["gesamtes_gf_brutto"] == 30000
    assert report["zve"] == 17395.0
    assert report["gesamter_nettoerloes"] == 116996.36
    assert report["gesamte_abgaben"] == 38003.64


def test_calculate_business_report_raises_on_loss() -> None:
    inputs = CalculationInput(gmbh_umsatz=10000, gmbh_kosten=9000, gf_gehalt=2000)

    try:
        calculate_business_report(inputs)
    except ValueError as exc:
        assert "keinen Verlust" in str(exc)
    else:
        raise AssertionError("Expected ValueError for loss-making scenario")


def test_yaml_include_loader(tmp_path) -> None:
    child = tmp_path / "child.yml"
    parent = tmp_path / "parent.yml"
    child.write_text("value: 42\n", encoding="utf-8")
    parent.write_text("child: !include child.yml\n", encoding="utf-8")

    data = Helper.load_yaml(str(parent))
    assert data["child"]["value"] == 42

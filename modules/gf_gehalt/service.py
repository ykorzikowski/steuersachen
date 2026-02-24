import json
from dataclasses import dataclass
from pathlib import Path

from modules.utils.helper import Helper


@dataclass(frozen=True)
class CalculationInput:
    steuerjahr: int = 2025
    gwst_hebesatz: float = 250
    gmbh_umsatz: float = 170000
    gmbh_kosten: float = 15000
    gf_gehalt: float = 30000
    andere_einkommen: float = 0
    sonstige_absetzbare_ausgaben: float = 5000
    gkv: bool = True
    kv_zusatzbeitrag: float = 2.45
    krankentagegeld: bool = True
    pv_zuschlag: bool = True
    beitrag_pkv: float = 1000
    kv_steuerlich_absetzbar_prozent: float = 100
    verheiratet: bool = False
    ehepartner_zve: float = 0


def _round2(value: float) -> float:
    return round(value, 2)


def calculate_annual_krankenkassenbeitrag_self_employed(
    brutto_income: float,
    additional_rate: float,
    year: int,
    krankentagegeld_enabled: bool,
    pv_zuschlag_enabled: bool,
    config: dict,
) -> float:
    kv_config = config["steuern"]["krankenversicherung"]
    contribution_ceiling = kv_config["beitragsbemessungsgrenzen"][year]
    min_contribution_basis = kv_config["mindestbemessungsgrundlage"][year]
    general_rate = kv_config["rates"]["general"]
    pv_rate = kv_config["rates"]["pv"]
    krankentagegeld = kv_config["rates"]["krankentagegeld"]
    pv_zuschlag = kv_config["rates"]["pv_zuschlag"]

    rate = general_rate + pv_rate + (additional_rate / 100)
    if krankentagegeld_enabled:
        rate += krankentagegeld
    if pv_zuschlag_enabled:
        rate += pv_zuschlag

    contributable_income = max(min(brutto_income, contribution_ceiling), min_contribution_basis)
    return _round2(contributable_income * rate)


def get_grenzsteuersatz(zve: float, verheiratet: bool, year: int, config: dict) -> float:
    steuer_config = config["steuern"]["einkommensteuer"]
    if year not in steuer_config:
        raise ValueError(f"Steuerjahr {year} ist nicht in der Konfiguration enthalten!")

    tariff = steuer_config[year]
    taxable_income = zve / 2 if verheiratet else zve

    if taxable_income <= tariff["zone1_start"]:
        return 0.0
    if taxable_income <= tariff["zone2_start"]:
        return 14 + ((taxable_income - tariff["zone1_start"]) / (tariff["zone2_start"] - tariff["zone1_start"])) * (
            24 - 14
        )
    if taxable_income <= tariff["zone3_start"]:
        return 24 + ((taxable_income - tariff["zone2_start"]) / (tariff["zone3_start"] - tariff["zone2_start"])) * (
            42 - 24
        )
    if taxable_income <= tariff["zone4_start"]:
        return 42.0
    return 45.0


def calc_tax(einkommen: float, verheiratet: bool, year: int, config: dict) -> float:
    steuer_config = config["steuern"]["einkommensteuer"]
    if year not in steuer_config:
        raise ValueError(f"Steuerjahr {year} ist nicht in der Konfiguration enthalten!")

    tariff = steuer_config[year]
    taxable_income = einkommen / 2 if verheiratet else einkommen

    if taxable_income <= tariff["zone1_start"]:
        steuer = 0.0
    elif taxable_income <= tariff["zone2_start"]:
        y = (taxable_income - tariff["zone1_start"]) / 10000
        steuer = (tariff["y_factor"] * y + tariff["y_offset"]) * y
    elif taxable_income <= tariff["zone3_start"]:
        z = (taxable_income - tariff["zone2_start"]) / 10000
        steuer = (tariff["z_factor"] * z + tariff["z_offset"]) * z + tariff["z_extra"]
    elif taxable_income <= tariff["zone4_start"]:
        steuer = 0.42 * taxable_income - tariff["tax_42_offset"]
    else:
        steuer = 0.45 * taxable_income - tariff["tax_45_offset"]

    if verheiratet:
        steuer *= 2
    return _round2(steuer)


def berechne_gewerbesteuer(gewinn: float, hebesatz: float, freibetrag: float = 24500) -> float:
    steuerpflichtiger_gewinn = max(0, gewinn - freibetrag)
    messbetrag = steuerpflichtiger_gewinn * 0.035
    return _round2(messbetrag * (hebesatz / 100))


def calculate_business_report(inputs: CalculationInput, config: dict | None = None) -> dict:
    data = config if config is not None else Helper.load_config_yml()

    gmbh_gewinn_vor_steuern = inputs.gmbh_umsatz - inputs.gmbh_kosten - inputs.gf_gehalt
    if gmbh_gewinn_vor_steuern <= 0:
        raise ValueError("Das Unternehmen darf keinen Verlust machen!")

    gwst = berechne_gewerbesteuer(gmbh_gewinn_vor_steuern, inputs.gwst_hebesatz, freibetrag=0)
    soli = gmbh_gewinn_vor_steuern * data["steuern"]["flat_tax"]["gmbh"]["soli"]
    kst = gmbh_gewinn_vor_steuern * data["steuern"]["flat_tax"]["gmbh"]["kst"]
    gmbh_steuern_gesamt = gwst + soli + kst
    gmbh_gewinn_nach_steuern = gmbh_gewinn_vor_steuern - gmbh_steuern_gesamt

    werbekostenpauschale = data["steuern"]["werbungskostenpauschale"][inputs.steuerjahr]
    gesamtes_gf_brutto = inputs.gf_gehalt + inputs.andere_einkommen

    if inputs.gkv:
        gf_krankenkassenbeitrag = calculate_annual_krankenkassenbeitrag_self_employed(
            brutto_income=gesamtes_gf_brutto,
            additional_rate=inputs.kv_zusatzbeitrag,
            year=inputs.steuerjahr,
            krankentagegeld_enabled=inputs.krankentagegeld,
            pv_zuschlag_enabled=inputs.pv_zuschlag,
            config=data,
        )
    else:
        gf_krankenkassenbeitrag = inputs.beitrag_pkv * 12

    kv_steuerlich_absetzbar = gf_krankenkassenbeitrag * (inputs.kv_steuerlich_absetzbar_prozent / 100)
    zve = gesamtes_gf_brutto - kv_steuerlich_absetzbar - werbekostenpauschale - inputs.sonstige_absetzbare_ausgaben
    if inputs.verheiratet:
        zve += inputs.ehepartner_zve

    ekst = calc_tax(zve, inputs.verheiratet, inputs.steuerjahr, data)
    grenzsteuersatz = get_grenzsteuersatz(zve, inputs.verheiratet, inputs.steuerjahr, data)

    persoenliche_abgabenlast = ekst + gf_krankenkassenbeitrag
    persoenliches_netto = gesamtes_gf_brutto - persoenliche_abgabenlast
    gesamter_nettoerloes = persoenliches_netto + gmbh_gewinn_nach_steuern
    gesamte_abgaben = gmbh_steuern_gesamt + persoenliche_abgabenlast
    gesamte_abgaben_prozentual = 1 - (gesamter_nettoerloes / inputs.gmbh_umsatz)

    return {
        "steuerjahr": inputs.steuerjahr,
        "gmbh_gewinn_vor_steuern": _round2(gmbh_gewinn_vor_steuern),
        "gmbh_steuern_gesamt": _round2(gmbh_steuern_gesamt),
        "gmbh_gewinn_nach_steuern": _round2(gmbh_gewinn_nach_steuern),
        "gesamtes_gf_brutto": _round2(gesamtes_gf_brutto),
        "krankenkassenbeitrag": _round2(gf_krankenkassenbeitrag),
        "zve": _round2(zve),
        "einkommensteuer": _round2(ekst),
        "grenzsteuersatz": _round2(grenzsteuersatz),
        "persoenliches_netto": _round2(persoenliches_netto),
        "gesamter_nettoerloes": _round2(gesamter_nettoerloes),
        "gesamte_abgaben": _round2(gesamte_abgaben),
        "gesamte_abgaben_prozentual": _round2(gesamte_abgaben_prozentual * 100),
    }


def write_report_artifact(report: dict, output_path: str) -> str:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, sort_keys=True)
    return str(path)

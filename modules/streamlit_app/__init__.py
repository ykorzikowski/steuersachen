import streamlit as st
from modules.utils.helper import Helper

CONFIG = Helper.load_config_yml()

class Steuersachen():
    @staticmethod
    def calculate_annual_krankenkassenbeitrag_self_employed(brutto_income, 
                                                            additional_rate=2.45, 
                                                            year=2024, 
                                                            krankentagegeld=False, 
                                                            pv_zuschlag=False):
        """
        Calculate the annual health insurance contribution (Krankenkassenbeitrag) for a self-employed person in Germany.
        
        Parameters:
        brutto_income (float): The yearly gross income.
        additional_rate (float): The additional contribution rate set by the health insurer (default is 2.45%).
        
        Returns:
        float: The annual health insurance contribution.
        """
        # Contribution ceiling (Beitragsbemessungsgrenze)

        contribution_ceiling = CONFIG['steuern']['krankenversicherung']['beitragsbemessungsgrenzen'][year]

        # Minimum contribution basis (Mindestbemessungsgrundlage) for self-employed
        min_contribution_basis = CONFIG['steuern']['krankenversicherung']['mindestbemessungsgrundlage'][year]

        general_rate = CONFIG['steuern']['krankenversicherung']['rates']['general']
        pv_rate = CONFIG['steuern']['krankenversicherung']['rates']['pv']
        pv_zuschlag = CONFIG['steuern']['krankenversicherung']['rates']['pv_zuschlag']
        krankentagegeld = CONFIG['steuern']['krankenversicherung']['rates']['krankentagegeld']
        rate = general_rate + pv_rate + (additional_rate/100)
        if krankentagegeld:
            rate += krankentagegeld
        if pv_zuschlag:
            rate += pv_zuschlag

        # Calculate the income subject to contribution (capped by the annual contribution ceiling, but with a minimum basis)
        contributable_income = max(min(brutto_income, contribution_ceiling), min_contribution_basis)
        
        # Calculate the full contribution for self-employed (general + additional)
        contribution = contributable_income * rate
        
        return round(contribution, 2)

    @staticmethod
    def get_grenzsteuersatz(zve, verheiratet=False, year=2024):
        """
        Berechnet den Grenzsteuersatz für das zu versteuernde Einkommen (ZVE) in Deutschland
        für ein bestimmtes Jahr (2020–2025).

        Parameter:
        - zve (float): Zu versteuerndes Einkommen in Euro.
        - verheiratet (bool): True für Splittingtarif, False für Grundtarif.
        - year (int): Steuerjahr (Standard: 2024).

        Rückgabe:
        - Grenzsteuersatz in Prozent (float)
        """
        steuer_config = CONFIG['steuern']['einkommensteuer']

        if year not in steuer_config:
            raise ValueError(f"Steuerjahr {year} ist nicht in der Konfiguration enthalten!")

        config = steuer_config[year]

        # Splittingtarif: Einkommen wird halbiert, Grenzsteuersatz bleibt gleich
        if verheiratet:
            zve /= 2

        # Bestimmung des Grenzsteuersatzes basierend auf den Steuerzonen
        if zve <= config["zone1_start"]:
            return 0.0
        elif zve <= config["zone2_start"]:
            return 14 + ((zve - config["zone1_start"]) / (config["zone2_start"] - config["zone1_start"])) * (24 - 14)
        elif zve <= config["zone3_start"]:
            return 24 + ((zve - config["zone2_start"]) / (config["zone3_start"] - config["zone2_start"])) * (42 - 24)
        elif zve <= config["zone4_start"]:
            return 42.0
        else:
            return 45.0  # Reichensteuer

    @staticmethod
    def calc_tax(einkommen, verheiratet=False, year=2025):
        """
        Berechnet die Einkommensteuer in Deutschland basierend auf den offiziellen Steuersätzen für ein gegebenes Jahr (2020–2025).

        Parameter:
        - einkommen (float): Zu versteuerndes Einkommen in Euro.
        - verheiratet (bool): True für Splittingtarif, False für Grundtarif.
        - year (int): Steuerjahr (zwischen 2020 und 2025).

        Rückgabe:
        - Einkommensteuerbetrag (float)
        """

        steuer_config = CONFIG['steuern']['einkommensteuer']

        if year not in steuer_config:
            raise ValueError(f"Steuerjahr {year} ist nicht in der Konfiguration enthalten!")

        config = steuer_config[year]
        
        # Splittingtarif: Einkommen halbieren, Steuer berechnen und dann verdoppeln
        if verheiratet:
            einkommen /= 2

        # Steuerformeln basierend auf der Steuerkonfiguration
        if einkommen <= config["zone1_start"]:
            steuer = 0
        elif einkommen <= config["zone2_start"]:
            y = (einkommen - config["zone1_start"]) / 10000
            steuer = (config["y_factor"] * y + config["y_offset"]) * y
        elif einkommen <= config["zone3_start"]:
            z = (einkommen - config["zone2_start"]) / 10000
            steuer = (config["z_factor"] * z + config["z_offset"]) * z + config["z_extra"]
        elif einkommen <= config["zone4_start"]:
            steuer = 0.42 * einkommen - config["tax_42_offset"]
        else:
            steuer = 0.45 * einkommen - config["tax_45_offset"]

        # Splittingtarif: Steuer verdoppeln
        if verheiratet:
            steuer *= 2

        return round(steuer, 2)

    @staticmethod
    def format_currency(value):
        """Formats a number as currency with thousand separators (e.g., 10.000 €)."""
        return f"{value:,.0f} €".replace(",", ".")

    @staticmethod
    def berechne_gewerbesteuer(gewinn, hebesatz, freibetrag=24500):
        """
        Berechnet die Gewerbesteuer in Deutschland.

        Parameter:
        - gewinn (float): Zu versteuernder Gewerbeertrag
        - hebesatz (float): Gewerbesteuer-Hebesatz der Gemeinde (z.B. 470 für 470%)
        - freibetrag (float): Steuerfreibetrag (Standard: 24.500 € für Einzelunternehmen & Personengesellschaften, 0€ für Kapitalgesellschaften)

        Rückgabe:
        - Gewerbesteuerbetrag (float)
        """
        # Freibetrag abziehen (gilt nicht für Kapitalgesellschaften)
        steuerpflichtiger_gewinn = max(0, gewinn - freibetrag)

        # Gewerbesteuermessbetrag (3.5% des steuerpflichtigen Gewinns)
        messbetrag = steuerpflichtiger_gewinn * 0.035

        # Gewerbesteuer berechnen
        gewerbesteuer = messbetrag * (hebesatz / 100)

        return round(gewerbesteuer, 2)

    def main(self):
        st.set_page_config(
            page_title="Steuersachen Rechner",
            page_icon="📊",
            layout="wide"
        )
        st.header("Optimierung GF Gehalt")
        st.markdown("""
        ### **Beschreibung des Rechners**
        Dieser Rechner hilft dabei, das optimale Geschäftsführergehalt zu bestimmen, um Steuer- und gg.f Krankenkassenbeiträge zu minimieren. 
        Das Gehalt beeinflusst sowohl die private Steuerbelastung als auch die Unternehmenssteuern der GmbH. Ziel ist es, möglichst viel Geld anzusparen
        und z.B. in breit gestreute ETF zu investieren. 

        **Wichtige Einflussfaktoren:**
        - **Körperschaftsteuer (KSt)** und **Gewerbesteuer (GwSt)**: Das Gehalt reduziert den steuerpflichtigen Gewinn der GmbH.
        - **Einkommensteuer (ESt)**: Das Geschäftsführergehalt unterliegt dem progressiven Einkommensteuertarif.
        - **Krankenkassenbeiträge**: Bei gesetzlicher Versicherung steigt der Beitrag mit dem Einkommen.

        ### **Optimierungsmöglichkeiten**
        1. **Steuerliche Balance finden:**  
        - Höheres Gehalt senkt die Unternehmenssteuer, erhöht aber die persönliche Steuerlast.
        - Ein niedrigeres Gehalt führt zu einer höheren Unternehmensbesteuerung, kann aber privat vorteilhafter sein.

        2. **Optimale Nutzung des Einkommensteuersplittings:**  
        Falls verheiratet, kann eine geschickte Verteilung des Einkommens eine niedrigere Steuerprogression bewirken.

        3. **Krankenkassenwahl berücksichtigen:**  
        - Bei gesetzlicher Krankenversicherung steigt der Beitrag mit dem Einkommen.
        - Eine private Krankenversicherung kann ab einem bestimmten Einkommen vorteilhafter sein.

        4. **Ausschüttung vs. Gehalt:**  
        - Alternativ kann eine Dividendenausschüttung geprüft werden, um Steuerbelastungen zu optimieren.
        - Dividenden unterliegen jedoch der Abgeltungsteuer.

        💡 **Hinweis:** Die optimale Gehaltsstruktur hängt von individuellen steuerlichen Rahmenbedingungen ab. Lassen Sie sich im Zweifel von einem Steuerberater beraten.
        """)

        st.warning("Bitte beachten Sie, dass diese Berechnungen auf Standardannahmen basieren und keine steuerliche oder rechtliche Beratung ersetzen. **Unter Ausschluss jeglicher Gewährleistung!**", icon="⚠️")

        # Steuerjahr Auswahl
        steuerjahr = st.slider(
            "Steuerjahr",
            min_value=2020, max_value=2025, step=1, value=2025,
            help=CONFIG["hint"]["steuerjahr"]
        )

        # Layout für Spalten
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("GmbH Ebene")
            
            gwst_hebesatz = st.slider(
                "Gewerbesteuer-Hebesatz (%)",
                min_value=100, max_value=600, step=5, value=250,
                help=CONFIG["hint"]["gwst_hebesatz"]
            )

            gmbh_umsatz = st.slider(
                "Jahresumsatz (€)",
                min_value=1000, max_value=1000000, step=1000, value=170000,
                help=CONFIG["hint"]["gmbh_umsatz"]
            )

            gmbh_kosten = st.slider(
                "Kosten (€)",
                min_value=1000, max_value=100000, step=1000, value=15000,
                help=CONFIG["hint"]["gmbh_kosten"]
            )

            gf_gehalt = st.slider(
                "Geschäftsführergehalt (€)",
                min_value=1000, max_value=200000, step=1000, value=30000,
                help=CONFIG["hint"]["gf_gehalt"]
            )

        with col2:
            st.subheader("Persönliche Ebene")

            andere_einkommen = st.slider(
                "Einkommen aus Vermietung, Verpachtung, andere Selbstständige Arbeit (€)",
                min_value=0, max_value=500000, step=100, value=0,
                help=CONFIG["hint"]["andere_einkommen"]
            )

            sonstige_absetzbare_ausgaben = st.slider(
                "Sonstige absetzbare Ausgaben (€)",
                min_value=0, max_value=50000, step=100, value=5000,
                help=CONFIG["hint"]["sonstige_absetzbare_ausgaben"]
            )

            gkv = st.checkbox(
                "Gesetzliche Krankenversicherung (GKV)", value=True,
                help=CONFIG["hint"]["gkv"]
            )

            kv_steuerlich_absetzbar = 100

            if gkv:
                kv_zusatzbeitrag = st.slider(
                    "KV Zusatzbeitrag (%)",
                    min_value=0.8, max_value=5.0, step=0.05, value=2.45,
                    help=CONFIG["hint"]["kv_zusatzbeitrag"]
                )
                krankentagegeld = st.checkbox(
                    "Krankentagegeld", value=True,
                    help=CONFIG["hint"]["krankentagegeld"]
                )
                pv_zuschlag = st.checkbox(
                    "Pflegeversicherung Zuschlag", value=True,
                    help=CONFIG["hint"]["pv_zuschlag"]
                )
            else:
                kv_zusatzbeitrag = 0
                krankentagegeld = False
                pv_zuschlag = False
                beitrag_pkv = st.slider(
                    "Beitrag zur PKV (€)",
                    min_value=0, max_value=2000, step=10, value=1000,
                    help=CONFIG["hint"]["beitrag_pkv"]
                )
                kv_steuerlich_absetzbar = st.slider(
                    "PKV Beitrg absetzbar (%)",
                    min_value=10, max_value=100, step=5, value=100,
                    help=CONFIG["hint"]["pkv_steuerlich_absetzbar"]
                )

            # Ehepartner-Einstellungen
            verheiratet = st.checkbox(
                "Verheiratet",
                help=CONFIG["hint"]["verheiratet"]
            )

            if verheiratet:
                ehepartner_zve = st.slider(
                    "ZvE Ehepartner (€)",
                    min_value=0, max_value=200000, step=1000, value=0,
                    help=CONFIG["hint"]["ehepartner_zve"]
                )
            else:
                ehepartner_zve = 0  # Default to 0 if not married

            # GmbH Ebene
            gmbh_gewinn_vor_steuern = gmbh_umsatz - gmbh_kosten - gf_gehalt
            gwst = 0
            soli = 0
            kst = 0

            if gmbh_gewinn_vor_steuern <= 0:
                st.error("**Fehler:** Das Unternehmen darf keinen Verlust machen!")
                return

            if gmbh_gewinn_vor_steuern > 0:
                gwst = Steuersachen.berechne_gewerbesteuer(gmbh_gewinn_vor_steuern, gwst_hebesatz, freibetrag=0)
                soli = gmbh_gewinn_vor_steuern * CONFIG['steuern']['flat_tax']['gmbh']['soli']
                kst = gmbh_gewinn_vor_steuern * CONFIG['steuern']['flat_tax']['gmbh']['kst']

            gmbh_steuern_gesamt = gwst + soli + kst
            gmbh_gewinn_nach_steuern = gmbh_gewinn_vor_steuern - gmbh_steuern_gesamt
            gmbh_abgabenlast_prozentual = gmbh_steuern_gesamt / gmbh_gewinn_vor_steuern
            pretty_print_gmbh_abgabenlast_prozentual = round(gmbh_abgabenlast_prozentual * 100, 2)

            # Persönliche Ebene
            werbekostenpauschale = CONFIG['steuern']['werbungskostenpauschale'][steuerjahr]

            gesamtes_gf_brutto = gf_gehalt + andere_einkommen

            if gkv:
                gf_krankenkassenbeitrag = Steuersachen.calculate_annual_krankenkassenbeitrag_self_employed(gesamtes_gf_brutto, additional_rate=kv_zusatzbeitrag, year=steuerjahr, krankentagegeld=krankentagegeld, pv_zuschlag=pv_zuschlag)
            else:
                gf_krankenkassenbeitrag = beitrag_pkv*12

            kv_steuerlich_absetzbar = gf_krankenkassenbeitrag * (kv_steuerlich_absetzbar / 100)
            zve = gesamtes_gf_brutto - kv_steuerlich_absetzbar - werbekostenpauschale - sonstige_absetzbare_ausgaben

            if verheiratet:
                zve += ehepartner_zve

            zve_grenzsteuersatz = Steuersachen.get_grenzsteuersatz(zve, verheiratet, steuerjahr)
            pretty_print_zve_grenzsteuersatz = round(zve_grenzsteuersatz, 2)

            ekst = Steuersachen.calc_tax(zve, verheiratet, steuerjahr)

            persoenlicher_durchschnitts_steuersatz_prozentual = ekst / zve
            pretty_print_persoenlicher_durchschnitts_steuersatz_prozentual = round(persoenlicher_durchschnitts_steuersatz_prozentual * 100, 2)

            persoenliche_abgabenlast = ekst + gf_krankenkassenbeitrag
            persoenliches_netto = gesamtes_gf_brutto - persoenliche_abgabenlast + sonstige_absetzbare_ausgaben
            persoenliche_abgabenlast_prozentual = persoenliche_abgabenlast / zve
            pretty_print_persoenliche_abgabenlast_prozentual = round(persoenliche_abgabenlast_prozentual * 100, 2)

            gesamter_nettoerlös = persoenliches_netto + gmbh_gewinn_nach_steuern
            gesamte_abgaben = gmbh_steuern_gesamt + persoenliche_abgabenlast
            gesamte_abgaben_prozentual = gesamte_abgaben / gesamter_nettoerlös
            pretty_print_gesamte_abgaben_prozentual = round(gesamte_abgaben_prozentual * 100, 2)

            if gkv:
                st.info("""
                        Für die Berechnung der Krankengassenbeiträge müssen ggf noch andere Einkünfte sowie die Art der Versicherung des Ehepartners und der Höhe der Beiträge dort berücksichtigt werden. 
                        Dies geschieht hier nicht. Der Beitrag wird zudem hier zur Vereinfachung zu 100% von dem zvE abgezogen, was auch nicht richtig ist. Für genauere Informationen Fragen Sie Ihren Steuerberater. 
                        """)

            with col1:
                st.divider()
                st.markdown(f"""
                Jahresumsatz: **{Steuersachen.format_currency(gmbh_umsatz)}**  
                Kosten: :red[**-{Steuersachen.format_currency(gmbh_kosten)}**]  
                GF Gehalt: :red[**-{Steuersachen.format_currency(gf_gehalt)}**]  
                Gewinn vor Steuern: **{Steuersachen.format_currency(gmbh_gewinn_vor_steuern)}**  
                Abgaben (KSt+Soli+GwSt): :red[**-{Steuersachen.format_currency(gmbh_steuern_gesamt)}**]  
                Gewinn nach Steuern: :green[**{Steuersachen.format_currency(gmbh_gewinn_nach_steuern)}**]  
                Abgabenlast in Prozent: **{pretty_print_gmbh_abgabenlast_prozentual}** %  
                """)

            with col2:
                st.divider()
                st.markdown(f"""
                GF Gehalt: **{Steuersachen.format_currency(gf_gehalt)}**  
                Andere Einkommen: **{Steuersachen.format_currency(andere_einkommen)}**  
                Absetzbare KV Beiträge GF: :red[**-{Steuersachen.format_currency(kv_steuerlich_absetzbar)}**]  
                Werbungskostenpauschale: :red[**-{Steuersachen.format_currency(werbekostenpauschale)}**]  
                Ehepartner ZvE: **+{Steuersachen.format_currency(ehepartner_zve)}**  
                Sonstige Absetzbare Ausgaben: :red[**-{Steuersachen.format_currency(sonstige_absetzbare_ausgaben)}**]  
                ZvE: **{Steuersachen.format_currency(zve)}**  
                """)
                
                st.markdown(f"""
                Abzug EkSt+Soli: :red[**-{Steuersachen.format_currency(ekst)}**]  
                Gezahlte KV Beiträge GF: :red[**-{Steuersachen.format_currency(gf_krankenkassenbeitrag)}**]  
                Abgaben Gesamt: :red[**{Steuersachen.format_currency(persoenliche_abgabenlast)}**]  
                """)

                st.markdown(f"""
                GF Netto: :green[**{Steuersachen.format_currency(persoenliches_netto)}**]  
                Zusammengefasste Abgabenlast in Prozent (inkl. KV): **{pretty_print_persoenliche_abgabenlast_prozentual} %**  
                Persönlicher Steuersatz (Durchschnitt): **{pretty_print_persoenlicher_durchschnitts_steuersatz_prozentual} %**  
                Persönlicher Grenzsteuersatz: **{pretty_print_zve_grenzsteuersatz} %**  
                """)


            st.subheader("Zusammenfassung")

            st.markdown(f"""
            Nettoerlös (ohne Ehepartner wenn zutreffend): **:green[{Steuersachen.format_currency(gesamter_nettoerlös)}]**  
            Abgaben Absolut: **{Steuersachen.format_currency(gesamte_abgaben)}**  
            Abgabenlast in Prozent: **{pretty_print_gesamte_abgaben_prozentual} %**  
            """)

        # Dynamischer Fließtext zur Erklärung der Steuerberechnungen
        summary_text = f"""
        ### **Gesamtauswertung der steuerlichen Berechnung**
        Das Steuerjahr **{steuerjahr}** wurde für die Berechnung herangezogen. Die GmbH erwirtschaftete einen **Jahresumsatz von {Steuersachen.format_currency(gmbh_umsatz)}**, 
        wovon **{Steuersachen.format_currency(gmbh_kosten)}** als Kosten und **{Steuersachen.format_currency(gf_gehalt)}** als Geschäftsführergehalt abgezogen wurden. 

        Dadurch ergibt sich ein **Gewinn vor Steuern von {Steuersachen.format_currency(gmbh_gewinn_vor_steuern)}**. Nach Abzug der Unternehmenssteuern 
        (**{Steuersachen.format_currency(gmbh_steuern_gesamt)}** für Körperschaftsteuer, Solidaritätszuschlag und Gewerbesteuer) bleibt ein **Gewinn nach Steuern von {Steuersachen.format_currency(gmbh_gewinn_nach_steuern)}** übrig.

        Für den Geschäftsführer ergibt sich ein zu versteuerndes Einkommen von **{Steuersachen.format_currency(zve)}**, 
        wobei **{Steuersachen.format_currency(gf_krankenkassenbeitrag)}** an Krankenkassenbeiträgen, eine Werbekostenpauschale von **{Steuersachen.format_currency(werbekostenpauschale)}** und **{Steuersachen.format_currency(sonstige_absetzbare_ausgaben)}** als sonstige absetzbare Ausgaben berücksichtigt wurden.

        Der persönliche Einkommensteuersatz liegt bei **{pretty_print_persoenlicher_durchschnitts_steuersatz_prozentual} %**, 
        während der Grenzsteuersatz **{pretty_print_zve_grenzsteuersatz} %** beträgt. Insgesamt fallen persönliche Abgaben in Höhe von **{Steuersachen.format_currency(persoenliche_abgabenlast)}** an, 
        was einer Abgabenlast von **{pretty_print_persoenliche_abgabenlast_prozentual} %** entspricht.
        """

        # Falls verheiratet, füge zusätzliche Erklärung hinzu
        if verheiratet:
            summary_text += f"""

        Da der Geschäftsführer verheiratet ist, wird auch das zu versteuernde Einkommen des Ehepartners berücksichtigt. 
        Das gemeinsame zu versteuernde Einkommen beträgt **{Steuersachen.format_currency(zve + ehepartner_zve)}**, 
        was sich positiv auf den progressiven Steuersatz auswirken kann. Die steuerliche Belastung kann durch den Splittingtarif 
        gemindert werden, sofern dieser vorteilhaft ist.
        """

        summary_text += f"""

        Zusammengefasst ergibt sich ein **Nettoerlös von {Steuersachen.format_currency(gesamter_nettoerlös)}**, 
        nachdem insgesamt **{Steuersachen.format_currency(gesamte_abgaben)}** an Steuern und Abgaben gezahlt wurden. Die gesamte Abgabenlast beträgt damit **{pretty_print_gesamte_abgaben_prozentual} %**.
        """

        # Zeige das aktualisierte Summary an
        st.markdown(summary_text)

        # Add footer with Impressum link
        st.markdown("""
        ---
        📄 [Impressum](https://yannik.swokiz.com/impressum/)
        📄 [GitHub](https://github.com/ykorzikowski/steuersachen)
        """, unsafe_allow_html=True)
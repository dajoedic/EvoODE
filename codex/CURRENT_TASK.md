# WP-OB-A2 — ODEBench-Smoke-Test: Nachbesserung nach der Abnahme von WP-OB-A
**Language: Python**

Grundlage: `docs/ODEBENCH_SMOKE_TEST.md` (Entwurf, am 06.10. in §2 und §8 nachgeführt, **neu lesen**) und
`codex/reports/REPORT_WP_OB_A.md`. Die Arbeit aus WP-OB-A liegt uncommittet in
`experiments/annihilator_odebench_smoke/`. Die Abnahme hat die folgenden Abweichungen von der Spezifikation
gefunden. Alle sind zu beheben. Was hier nicht genannt ist, bleibt wie es ist.

## Befunde und geforderte Änderungen

1. **Die Baselines sind kein pysindy, und W-SINDy fehlt.** `_baseline_record` rechnet die Ableitungen mit
   `np.gradient`, schneidet ohne Spaltennormierung nur einmal ab, und „wsindy“ ist derselbe Code wie „sindy“. Jeder
   Record trägt trotzdem `pysindy_parameters` mit `SmoothedFiniteDifference`, `normalize_columns = True` und
   `WeakPDELibrary`. **Das ist eine falsche Angabe in den Daten** und darf nicht vorkommen. Gefordert nach §6:
   - SINDy mit `pysindy.SINDy`, `differentiation_method = SmoothedFiniteDifference()` (Standardwerte), Library als
     `CustomLibrary` oder gleichwertig mit genau den Termen aus §6, Optimierer `STLSQ(threshold = s,
     normalize_columns = True)` (übrige STLSQ-Parameter Standard) je Schwelle $s$ aus dem Gitter. Beide
     Trainingstrajektorien gehen als Liste mehrerer Trajektorien in ein `fit`.
   - W-SINDy mit `pysindy.WeakPDELibrary` über derselben Funktions-Library, `spatiotemporal_grid = t`, $K = 200$,
     sonst Standardwerte, gleiche STLSQ-Schwellen.
   - AICc-Auswahl über das Gitter auf dem Regressionsresiduum des jeweiligen Verfahrens (bei W-SINDy auf der
     schwachen Form). Ist das in pysindy nicht direkt zugänglich, wird die Residuumsquelle im Report genannt.
   - `pysindy_parameters` wird **aus den tatsächlich instanziierten Objekten** gelesen (`get_params()` o. ä.), nicht
     als Konstante geschrieben.
   - Zulässigkeit der Library-Terme nach §6 auf den **verrauschten** Trainingszuständen.
2. **Gleiches Rauschen auf beiden Trainingstrajektorien.** `_rng(...)` wird innerhalb der Schleife je Trajektorie neu
   erzeugt, beide Trajektorien bekommen damit denselben Rauschvektor. Ein Generator je (Seed, System, Methode),
   aus dem nacheinander gezogen wird.
3. **Kette $L \to \hat f$ (§5).** Mit dem **exakten** Referenzoperator liefert `basis_ivp_fhat` auf dem
   Produktivintervall $[x_{\min} - 2R,\ x_{\max} + 10R]$ für die Systeme 7 und 19 `BASIS_INTEGRATION_FAILED`,
   weil über die Nullstelle des Leitkoeffizienten bei $x = 0$ integriert wird. §5 verlangt, das Intervall an der
   ersten reellen Nullstelle des Leitkoeffizienten außerhalb der Trainingsdomäne zu begrenzen. Umsetzung:
   - Die Grenzen sind die Nullstellen mit einem festen relativen Abstand, $10^{-3}\,R$ vor der Nullstelle.
   - Das wirksame Intervall wird im Record festgehalten.
   - Eine Trajektorie, die es verlässt, zählt nach §5 als gescheitert ($\infty$), **ohne Ausnahme im Lauf**:
     `fhat` darf beim Integrieren keinen Abbruch des ganzen Laufs auslösen.
4. **Plausibilitätsprüfung 2 (§8) prüft nicht den Lauf-Pfad.** `run_sanity` ruft `basis_ivp_fhat` nur mit der
   Trainingsdomäne als Auswertungsintervall auf. Gefordert:
   - derselbe Aufruf wie im Lauf, mit dem vollen Intervall;
   - zusätzlich die Integration der beiden Trainingstrajektorien mit diesem $\hat f$
     ($\mathrm{NRMSE}_x$ wird berichtet).

   Plausibilitätsprüfung 1 hat jetzt die Schwelle $10^{-4}$ (§8).
5. **Zustandslogik.** `annihilator_state` setzt `TRUE_NOT_REF` bei komponentenweise $r \ge r_{\text{ref}}$ und
   $d \ge d_{\text{ref}}$. In v3 (`run_gate2a.state_for`, `stage_k_calibration._state_for_clean`) gilt
   `TRUE_NOT_REF` genau dann, wenn $n_{\text{exact}}$ der **gewählten** Klasse für das wahre $f$ größer null ist.
   Genau so umsetzen, mit dem verallgemeinerten Orakel. Das Ergebnis wird je (System, Klasse) gecacht.
   $n_{\text{exact}}$ der gewählten Klasse steht im Record.
6. **Records unvollständig (§8 Komplexität).** In jeden Record kommen:
   - Annihilator: Koeffizienten von $\hat L$ (in $z$), $(r, d)$, die Fit-Koeffizienten $a_j$, das wirksame
     Intervall und gegebenenfalls `fhat_fail` mit Grund;
   - Baselines: die gewählten Terme **mit Koeffizienten**, die gewählte Schwelle, AICc;
   - alle Methoden: je Trainings- und Test-Anfangsbedingung $\mathrm{NRMSE}_x$, $R^2$ und gegebenenfalls den
     Fehlschlaggrund.
7. **`--workers` wird ignoriert.** Umsetzen: parallele Prozesse über (System, $\eta$, Seed, Methode), jeder Record
   wird sofort angehängt (Dateisperre oder ein Ausgabeteil je Worker plus Zusammenführung), Fortsetzen ohne
   Duplikate.
8. **Tests prüfen nicht den Produktivpfad.** `test_fhat.py` testet `polynomial_nullspace_fhat`, der im Lauf nie
   aufgerufen wird. Gefordert:
   - Tests auf `basis_ivp_fhat` mit dem Produktivintervall: (a) $D^3$ auf einem Polynom; (b) $xD^3 + D^2$ (Gompertz-
     Struktur) auf $a\,x\log x + b\,x$ über $[1.7, 30]$ mit Intervall über $x = 0$ hinaus, Erwartung: Begrenzung
     an der Nullstelle, exakte Reproduktion; (c) Nullstelle in der Trainingsdomäne ergibt `FHAT_FAIL`.
   - `polynomial_nullspace_fhat` entfernen, falls unbenutzt.
   - Ein Test, der für jede Baseline nachweist, dass pysindy tatsächlich aufgerufen wird und die Records die
     instanziierten Parameter tragen.
   - Ein Test, dass die beiden Trainingstrajektorien verschiedenes Rauschen bekommen.
   - Ein Test der Zustandslogik mit einem Fall, in dem die komponentenweise Regel und die $n_{\text{exact}}$-Regel
     verschieden entscheiden.
   - Die Record-Feldliste im Report stammt aus einem **echten** Record des Lauf-Pfads auf einer synthetischen
     Kleinstfunktion (nicht aus `run_one_synthetic_record`, das entfernt wird).

## Ausführen

Alle Tests (neu und v3, mit `--basetemp`), dann `--setup` neu (überschreibt `setup.json`, `reference.json`,
`sanity.json`). **Kein** `--run` auf den vier Systemen.

## Verboten

- Änderungen unter `experiments/annihilator_gate2a_v3/` und `docs/`.
- Discovery-Läufe auf den vier Systemen.
- Library, Gitter, Seeds, Regeln oder Schwellen anders als im Dokument.
- Andere Katalog-IDs lesen oder ausgeben.
- Git-Operationen. Nichts über 15 Minuten.

## Abnahme

1. Alle Tests grün, kein `skip`.
2. `sanity.json`: Prüfung 1 mit Schwelle $10^{-4}$, Prüfung 2 auf dem Produktivintervall mit Trainingstrajektorien.
   Der Report nennt je System die Zahlen. Scheitert etwas, steht es mit Zahlen im Report, und es wird nichts
   geändert.
3. Report `codex/reports/REPORT_WP_OB_A2.md`: je Befund 1–8, was geändert wurde (Datei, Funktion), Testausgabe aus
   diesem Lauf, die echte Record-Feldliste mit Herkunft und die tatsächlich instanziierten pysindy-Parameter.

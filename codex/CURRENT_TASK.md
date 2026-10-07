# WP-E2E-A — ODEBench End-to-End: gleiche Trajektorien für SINDy, W-SINDy und Annihilator
**Language: Python**

Grundlage: `docs/ODEBENCH_END2END.md` (Entwurf, vollständig lesen). Dort stehen Systeme, Daten, Rauschen, die
Protokolle P1/P2, die gemeinsame Auswahlregel, der Annihilator end-to-end, die Baselines, die Metriken und die
Plausibilitätsprüfungen verbindlich. Bei Widerspruch oder Unklarheit gilt das Dokument; dann `blocked` melden und
nicht selbst entscheiden.

## Zu bauen

1. Neues Modul `experiments/annihilator_odebench_smoke/end2end.py` und Tests in
   `experiments/annihilator_odebench_smoke/tests/test_end2end.py`. Ergebnisordner
   `experiments/annihilator_odebench_smoke/results_e2e/`. Wiederverwendet werden Katalog, `reference.json`,
   `setup.json` (Test-AB für P2), `basis_ivp_fhat`, Trajektorienmetriken und die pysindy-Bausteine aus dem
   Smoke-Code, **nur per Import**. Nötige Verallgemeinerungen kommen in neue Funktionen in `end2end.py`; bestehende
   Smoke-Funktionen werden nicht verändert.
2. **Daten und Rauschen** (§2): eine Rauschrealisierung je (Seed, System, Trajektorie), mit einem Generator
   `default_rng([seed, system_id, trajectory_index])`, identisch für alle Methoden. Ein Test weist nach, dass die
   drei Methoden bitgleiche Eingaben bekommen.
3. **Protokolle** (§3): drei Fits je (System, $\eta$, Seed, Methode): `P1_from_AB1`, `P1_from_AB2`, `P2`.
4. **Auswahlregel** (§4) als **eine** gemeinsame Funktion für alle Methoden:
   - Fit-Teil $t \le 8$, Validierung $t > 8$;
   - Integration ab der wahren AB über $[0, 10]$ (LSODA, rtol $10^{-8}$, atol $10^{-10}$, wie in den Smoke-Metriken);
   - $\mathrm{NRMSE}_x$ gegen die verrauschten Daten auf dem Validierungsteil, bei P2 gemittelt;
   - Tie-Regel $10^{-3}$ zugunsten des einfacheren Kandidaten;
   - danach Neu-Fit auf $[0, 10]$.

   Je Kandidat werden der Validierungsfehler und gegebenenfalls der Fehlschlaggrund im Record gespeichert.
5. **Annihilator** (§5):
   - `SmoothedFiniteDifference()` aus pysindy auf jeder Lern-Trajektorie (dieselbe Instanzkonfiguration wie für
     SINDy);
   - sortieren, gleiche $\tilde x$ mitteln, linear auf 2000 gleichmäßige Punkte interpolieren;
   - die 18 Klassen mit $C \le 12$ in v3-Ordnung (aus `class_order()` gefiltert, nicht abgetippt);
   - je Klasse `WeightContext(z, values, SEARCH_SETTINGS).split(r, d)`, `aml_candidate(a_fit, k_fit)` und
     `basis_ivp_fhat`;
   - kein $\chi^2$-Test, keine A1–A3, kein Bootstrap.
6. **SINDy und W-SINDy** (§6): pysindy wie im Smoke-Code (`fit_pysindy_baseline`-Bausteine), aber Auswahl über die
   gemeinsame Regel statt AICc; Library-Zulässigkeit auf den verrauschten Lernzuständen.
7. **Metriken** (§7) je Fit:
   - R² und $\mathrm{NRMSE}_x$ für Rekonstruktion und Generalisierung (je Trajektorie), $\mathrm{NRMSE}_f$;
   - Strukturtreffer und Obermenge (Annihilator: $n_{\text{exact}}$ der gewählten Klasse aus dem verallgemeinerten
     Orakel, gecacht);
   - gewählte Klasse bzw. Termmenge mit Koeffizienten, Operatorkoeffizienten, Zählgrößen;
   - `spec: "end2end_v1"`.
8. **Auswertung:** Funktion für §9 mit den Größen G und S und dem Verdikt „weiter diskutieren“ bzw. „beenden“, dazu
   die Tabellen. Die Schwellen sind Konstanten an einer Stelle; sie stehen erst nach dem Einfrieren fest.
   Implementiert wird der Vorschlag aus §9.
9. **Plausibilitätsprüfungen** (§8) als `--sanity`, schreibt `results_e2e/sanity.json`:
   - (1) synthetische 1D-ODE, die keines der vier Systeme ist, etwa $\dot x = 0.5x - 0.02x^2$ oder ähnlich, alle drei
     Methoden, $\eta = 0$;
   - (2) die vier Systeme mit **exaktem** $\dot x$ (aus der wahren rechten Seite) und **vorgegebener** Referenzklasse,
     Validierungsfehler.
10. **CLI:** `python -m experiments.annihilator_odebench_smoke.end2end` mit `--sanity`,
    `--run --systems … --eta … --seeds … --methods … --workers N --detach-marker` (Fortsetzen ohne Duplikate,
    Sekunden im Log, keine Ergebnisse im Log, `DONE`/`FAILED`) und `--summarize`.
11. **Tests** (ohne Fits auf den Systemen 3, 7, 19, 21):
    - gleiche Eingaben für alle Methoden;
    - Aufteilung $t \le 8$ / $t > 8$;
    - Tie-Regel;
    - Neu-Fit auf voller Zeit;
    - Resampling auf 2000 Punkte mit Mitteln gleicher $x$;
    - die 18 Klassen exakt aus `class_order()`;
    - Strukturtreffer und Obermenge je Methode;
    - Entscheidungsfunktion an Fixtures, die aus einem echten Record auf synthetischen Daten abgeleitet sind;
    - scheiternde Integration ergibt $\infty$ bzw. $R^2 = -\infty$ ohne Abbruch.

## Ausführen

Alle neuen Tests, alle Smoke-Tests und alle v3-Tests (mit `--basetemp`), dann `--sanity`. **Kein** `--run` auf den
vier Systemen. Scheitert eine Plausibilitätsprüfung, steht der Befund mit Zahlen im Report, und es wird nichts an
Methode oder Regel geändert.

## Verboten

- Änderungen unter `experiments/annihilator_gate2a_v3/`, an bestehenden Dateien in
  `experiments/annihilator_odebench_smoke/` (außer neuen Dateien), an `results/`, `results_v2/` und an `docs/`.
- Discovery-Läufe auf den vier Systemen, auch nicht in Tests. Erlaubt ist nur Plausibilitätsprüfung (2) mit
  vorgegebener Klasse.
- Andere Katalog-IDs lesen oder ausgeben.
- Abweichungen von Library, Gitter, Kandidatenliste, Seeds, Aufteilung oder Toleranzen.
- Git-Operationen. Nichts über 15 Minuten.

## Abnahme

1. Alle Tests grün, kein `skip`.
2. `results_e2e/sanity.json` mit beiden Prüfungen und Zahlen.
3. Report `codex/reports/REPORT_WP_E2E_A.md`: Dateien, Kommandos, Testausgabe aus diesem Lauf, die echte
   Record-Feldliste mit Herkunft (aus einem synthetischen Lauf), die tatsächlich instanziierten pysindy-Parameter und
   eine Kostenschätzung pro Annihilator-Fit (Zeit und Zählgrößen aus Prüfung (2)).

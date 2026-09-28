# WP-T1f — WP-T1d-Reparatur: Nachbarschaftsprobe mit warmem Start aus den wahren Parametern
**Language: Julia** (plus ein kleiner Python-Export für die wahren Koeffizienten, siehe Schritt 1)

## Ausführung

Codex kann in dieser Umgebung kein Julia ausführen (`codex/CODEX_PROTOCOL.md`). Also: umsetzen,
Python-Teile testen, Julia-Befehle für Claude im Report auflisten, Status `blocked` melden.
**Kein Lauf der Probe**, auch nicht teilweise. Keine Git-Operationen, kein Docker, kein `oc`/`kubectl`.

## Ausgangslage

WP-T1d (`studies/regression/wp_t1d_neighbourhood_loss.jl`, Report `codex/reports/REPORT_WP_T1d.md`
und `REPORT_WP_T1e.md`) ist Schritt 3 der eingefrorenen Guidance-Reihe in `docs/phd_thesis_arc.md`:
**Ist der wahre Träger ein lokales Optimum unseres Trajektorien-Loss?** Der Lauf auf Orion ist fertig,
36/36 Zellen, 3.910 Nachbarzeilen, Identität `5a87efb` / `0c9672de35c75a9d`. Die Rohdaten liegen
lokal unter `outputs/wp_t1d_neighbourhood/orion_5a87efb/cell_*/neighbour_rows.jsonl`.

**Der Defekt:** Die Probe fittet den wahren Träger einmal aus einem Zufallsstart und benutzt diesen
Loss als Maßstab für alle Nachbarn. Dieser Referenzfit scheitert in **30 von 36 Zellen**
(`loss_true ≥ 1e-3`, dim 2: 16/20, dim 3: 14/16). In den 6 sauberen Zellen schlägt **kein**
`swap_one`-Nachbar die Wahrheit (0/386) und kein `remove_one` (0/30). Die Probe misst also das
Scheitern des Fits, nicht die Landschaft (DIARY 2026-09-23, „WP-T1d, Zwischenblick“).

**Entscheidung des Nutzers (2026-09-28):** Die Frage wird mit einem reparierten Maßstab geschlossen,
bevor WP-T2a startet. Das ist dieselbe Frage mit einem korrigierten Instrument, kein neuer Schritt.

## Das Design (vorab festgelegt, nicht verändern)

Pro Zelle `(system, ic_set)` — **dieselben 36 Zellen** wie WP-T1d, dieselbe Nachbarschaft
(`add_one`, `remove_one`, `swap_one`), derselbe Phase-C-Optimierer und dasselbe Loss-Budget pro Fit:

1. **Kontrolle:** Loss des wahren Trägers **an den wahren Parametern, ohne Optimierung**. Das ist
   ein reiner Loss-Aufruf. Er prüft, dass Koeffizienten und Parameterreihenfolge stimmen.
2. **Boden:** Fit des wahren Trägers mit Start `p0` = wahre Parameter.
3. **Nachbarn, warm:** Jeder Nachbar startet vom nächstgelegenen Punkt zur Wahrheit: Koeffizienten
   der gemeinsamen Terme = wahre Werte, ein entfernter Term entfällt, ein neu hinzugekommener Term
   startet bei `0.0`. Ein Fit pro Nachbar. Verglichen wird gegen den **Boden** aus Punkt 2.
4. **Wahrheit, kalt:** Fit des wahren Trägers aus **m = 10** Zufallsstarts, jeder als **Einzelfit**
   (`max_fit_attempts = 1`), mit deterministisch aus Zelle und Startindex abgeleiteten Seeds. Das
   misst, wie oft unser Fit die Wahrheit aus einem Zufallsstart verfehlt. m ist vorab festgelegt
   und wird nicht nach Sicht der Daten geändert.

Für die Nachbarn und den Boden gilt die Phase-C-Retry-Regel (`max_fit_attempts = 3`) wie in WP-T1d:
Versuch 1 nutzt `p0`, ein weiterer Versuch zieht nach der Wächter-Regel einen Zufallsstart. **Jede
Zeile hält fest, welcher Versuch das Ergebnis geliefert hat** (Versuch 1 = warm, später = kalt),
damit ein Zufallsstart nie still als warmer Start durchgeht.

## Was zu tun ist

1. **Wahre Koeffizienten.** Es gibt genau eine Definition: die WP-N26-Extraktion aus der
   `equation`-Spalte von `analysis/data/paper1_phaseC_v1/system_classification.csv` mit der
   Konvention `x_i -> u{i+1}` (`codex/reports/REPORT_WP_N26.md`, Abschnitt „Coefficient error
   definition“). Diese Extraktion **wiederverwenden**, nicht in Julia nachbauen. Ein kleines
   Python-Skript exportiert für die exakten dim-2/dim-3-Systeme der Probe eine JSON-Datei
   `studies/regression/wp_t1f_true_coefficients.json`: pro System und Gleichung die Terme in den
   Namen der Basis `staged_polynomial_basis_with_constant` mit ihrem Koeffizienten. Harte Prüfung
   im Export: Die Termmenge jeder Gleichung muss **exakt** `support_terms` aus
   `studies/regression/phase_c_support.json` entsprechen, sonst Abbruch. Die JSON-Datei wird
   eingecheckt und ist Eingabe des Julia-Laufs.
2. **Neues Skript** `studies/regression/wp_t1f_warm_neighbourhood.jl`. Es verwendet die Bausteine
   von `wp_t1d_neighbourhood_loss.jl` wieder (Zellauswahl, Nachbarschaft, Trajektorien-Export mit
   Hash-Prüfung, Fixed-Structure-Fit, Index-Listen, k8s-Indexpfad), indem es die Datei einbindet.
   Wo dafür ein Fit-Baustein einen `p0`- oder `max_fit_attempts`-Parameter braucht, wird er mit
   einem Default ergänzt, der das bisherige Verhalten exakt erhält. **Das Verhalten von
   `wp_t1d_neighbourhood_loss.jl` bleibt unverändert.** Die Zuordnung Koeffizient → Position im
   Parametervektor wird aus der Parameterreihenfolge von `build_rhs` abgeleitet, nicht angenommen.
3. **Kontroll-Abbruch:** Liegt der Kontroll-Loss aus Punkt 1 des Designs in einer Zelle über
   `1e-4`, bricht die Zelle hart ab und meldet das. Das ist die Grenze für „Zuordnung kaputt“, keine
   Qualitätsschwelle. Der Kontroll-Loss wird in jeder Zelle mitgeschrieben, auch darunter.
4. **Rohzeilen:** eine JSONL-Zeile pro Fit mit mindestens: Identität (git hash,
   `config_fingerprint`), Zelle, Dimension, `fit_role` (`control` / `floor` / `neighbour_warm` /
   `truth_cold`), bei Nachbarn Klasse, Gleichung, entfernter und hinzugefügter Term und Trägerterme,
   bei `truth_cold` der Startindex und Seed, Loss, Budget erschöpft ja/nein, Wächterwert ja/nein,
   `winning_attempt`, `total_parameter_fits`, Loss-Evaluationen, die gefitteten Koeffizienten, und
   `elapsed_s_non_evidence` (Zeit ist nie Beleg). Trajektorien-Hash wie in WP-T1d.
5. **Aggregation ohne Neuberechnung:** Ein Modus `--aggregate-only --input-dir <dir>`, der aus
   vorhandenen Rohzeilen die Tabellen baut. Diesen Modus gibt es in WP-T1d nicht, und deshalb ließ
   sich der Orion-Lauf nicht lokal auswerten. **Die Aggregation muss auch die alten WP-T1d-Rohzeilen
   verarbeiten können** (dort als Variante `cold_reference`), damit kalt und warm nebeneinander
   stehen. Aggregate nach `analysis/data/wp_t1d_neighbourhood/<run_label>/`.
   Pro Dimension und Nachbarklasse getrennt, **nie über Klassen summiert**:
   - Anteil Nachbarn mit Loss unter dem Boden, als volles Raster über die bestehenden
     `WP_T1D_MARGIN_FACTORS` (1, 1,5, 2, 10, 100), und Quantile des `log10`-Verhältnisses;
   - Kontroll-Loss und Boden-Loss je Zelle;
   - `truth_cold`: je Zelle Anzahl der Starts unter `1e-8`, zwischen `1e-8` und `1e-3`, darüber
     und Wächter; daraus die Einzelstart-Trefferquote je Dimension;
   - Anteil Nachbarn, deren Ergebnis **nicht** aus dem warmen Versuch stammt, getrennt ausgewiesen.
   Die Schwellen `1e-8` und `1e-3` sind die aus der Zwischensichtung und werden nicht verändert.
6. **Kostenprojektion aus dem Smoke:** Der Smoke (Punkt 7) schreibt eine Projektion der
   Fit-Anzahl je Zelle und Dimension. Die Zeitprojektion wird aus der gemessenen Zeit pro
   Loss-Evaluation im Smoke abgeleitet, nicht aus einer Konstante, und ist als Nicht-Beleg markiert.
   Die alte Konstante `WP_T1D_REFERENCE_SECONDS_PER_FIT` wird dafür **nicht** verwendet.
7. **Smoke:** `--smoke` fährt eine dim-2-Zelle und eine dim-3-Zelle (nicht Lorenz 55/56), jeweils
   nur mit Kontrolle, Boden, **höchstens 5** Nachbarn pro Klasse und 2 `truth_cold`-Starts. Dazu
   `--self-test` ohne Fits: Nachbarschaftszahlen, Koeffizientenzuordnung, warmer Startvektor für
   je einen `add_one`-, `remove_one`- und `swap_one`-Nachbarn gegen einen handgerechneten Sollwert.
8. **Orion:** Manifeste `k8s/wp_t1f_bootstrap_index_job.yaml`, `k8s/wp_t1f_indexed_smoke_job.yaml`
   und `k8s/wp_t1f_indexed_campaign_job.yaml` nach dem Muster von `k8s/wp_t1e_*.yaml`, Ausgabe
   `/outputs/wp_t1f_<COMMIT_SHA>` bzw. `/outputs/wp_t1f_campaign_<COMMIT_SHA>`. Eigene
   Umgebungsvariablen (`EVO_T1F_…`), keine Wiederverwendung der `EVO_T1D_…`-Namen.
   `completions: 36`, `parallelism: 6`. **`activeDeadlineSeconds` als Platzhalter
   `<DEADLINE_SECONDS>`**, mit dem Kommentar, dass Claude ihn nach dem Smoke als großzügige obere
   Schranke aus der Projektion setzt (Lehre aus WP-T1d: eine Deadline aus einer Punktschätzung erbt
   deren Fehler). Die Trajektorien werden wie in WP-T1d gelesen und per Hash geprüft.
9. **Dokumentation:** `SCRIPTS.md` bekommt einen Abschnitt WP-T1f mit Self-Test, Smoke lokal,
   Orion-Ablauf (Bootstrap, Smoke, Kampagne), Einsammeln und `--aggregate-only` für beide Varianten.
   Für `cold_reference` den konkreten Befehl auf
   `outputs/wp_t1d_neighbourhood/orion_5a87efb/` angeben.

## Verboten

- Keine Änderung am Verhalten von `wp_t1d_neighbourhood_loss.jl`, am Optimierer-Default, an
  `src/` außer optionalen, verhaltensneutralen Parametern mit Default.
- Kein Nachbau der Koeffizienten-Extraktion in Julia; keine hartkodierten Koeffizienten.
- Keine Schwelle, kein m, keine Margin, die vom Design oben abweicht.
- Nichts unter `analysis/data/` schreiben außer über den Aggregationsmodus, und diesen nicht
  ausführen (kein Julia).
- Keine Änderung an `containers/Dockerfile`, `.gitlab-ci.yml` oder an Phase-C-Manifesten.

## Abnahme

1. Python-Export: Test, der die Termmengen gegen `phase_c_support.json` prüft, und ein Test mit einem
   absichtlich falschen Term, der abbricht. Export einmal ausgeführt, JSON-Datei liegt vor.
2. Julia-Test `test/test_wp_t1f_warm_neighbourhood.jl`: warmer Startvektor für die drei Klassen,
   Kontroll-Abbruch über `1e-4`, `winning_attempt` wird korrekt gesetzt, `--aggregate-only` liest
   eine kleine synthetische Rohdatei beider Varianten und summiert nie über Klassen.
3. YAML der drei Manifeste parst.
4. Report `codex/reports/REPORT_WP_T1f.md` mit den Julia-Befehlen für Claude in dieser Reihenfolge:
   Julia-Test, `--self-test`, lokaler `--smoke`, `--aggregate-only` auf den alten Rohdaten.
   Dazu die Dateiliste und jede Abweichung vom Design mit Begründung.
5. `codex/STATUS.md`: `status: blocked` (Julia nicht ausführbar), WP-T1f, Report-Pfad.

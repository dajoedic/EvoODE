# WP-N32 — Datenbedingung (Rauschen, Ausdünnung) und wählbare Parametergrenze im Kampagnenpfad
**Language: Julia** (plus ein kleines Python-Vergleichsskript, siehe Punkt 7)

Verbindliche Spezifikation: `docs/paper1_phaseC_benchmark_plan.md` **§9** (eingefroren am 2026-10-01).
Lies §9.1, §9.4 und §9.6 vollständig, bevor du anfängst. Wo dieser Auftrag und §9 sich zu
widersprechen scheinen, gilt §9, und der Widerspruch gehört in den Report.

## Ziel

Der bestehende Phase-C-Kampagnenpfad bekommt zwei neue, voneinander unabhängige Stellschrauben:

1. eine **Datenbedingung**: geseedetes multiplikatives Rauschen und zufällige Ausdünnung der
   Trainingstrajektorie nach dem ODEFormer-Protokoll;
2. eine **wählbare Parametergrenze** `clamp_val` (10, 1000 oder unbeschränkt) im Kampagnenlauf und im
   Orakel-Refit.

**Die Methode selbst ändert sich nicht.** Bei Rauschen 0, Ausdünnung 0 und `clamp_val = 10` muss der
neue Pfad die C-1-Records **bitgleich** reproduzieren. Das ist das wichtigste Abnahmekriterium.

## Ausgangslage im Code (geprüft von Claude)

- Die saubere Trajektorie entsteht in `build_trajectory` (`studies/regression/run_regression.jl:571`)
  und wird bei `run_regression.jl:819` an die Suche übergeben. Der Orakel-Refit holt sie bei
  `studies/regression/wp_n3_oracle_refit.jl:270`.
- `simulate` nimmt den **ersten Datenpunkt** als Anfangsbedingung und integriert auf `traj.t`
  (`src/simulate/solve.jl:27-39`). Ein unregelmäßiges Raster ist dort also schon zulässig.
- Die Grenze ist `BFGSOptimizer.clamp_val`. Sie wird an `src/optimize/bfgs.jl:178`, `:354` und
  `:676` angewendet und über `src/core/discover.jl:150` an `simulate` weitergereicht. In der
  Phase-C-Konfiguration steht sie als `BFGS_CLAMP_VAL` und geht über `phase_c_config.jl:296` in den
  Fingerprint ein.
- Phase-C-Methodenkennung `0c9672de35c75a9d` (`phase_c_fingerprint()`), Orakel-Kennung
  `925e3957a7a884e2`, Verhaltens-Fingerprint `ffb0266c7913352c`.
- Hash-Format für Trajektorien: `studies/regression/phase_c_trajectory_hash_lib.jl`
  (`sha256_raw_little_endian_float64`, Export über `export_trajectory!`). **Wiederverwenden, nicht
  neu bauen.**

## Umsetzung

**1. Datenbedingungs-Modul (neue Datei unter `studies/regression/`).**
Eingabe: saubere Trajektorie, `system_id`, `ic_set`, `noise_sigma`, `subsample_rho`,
`noise_realization`. Ausgabe: die verfälschte Trajektorie, die die Methode sieht.
- Rauschen: `x_obs = x + sigma * x * eps`, `eps` i.i.d. standardnormal je Zeitpunkt und
  Zustandskomponente.
- Ausdünnung **nach** dem Rauschen: `floor(n * rho)` Indizes gleichverteilt ohne Zurücklegen
  entfernen, jeder Index ist zulässig (auch der erste). Die verbleibenden Zeitpunkte bleiben
  aufsteigend sortiert.
- Getrennte RNG-Ströme für Rauschen und Ausdünnung. Der Seed wird deterministisch **nur** aus
  `(system_id, ic_set, sigma, rho, realization)` abgeleitet, nie aus dem Methoden-Seed. Das
  Ableitungsschema wird dokumentiert und trägt eine Versionskennung.
- `sigma == 0 && rho == 0`: Die saubere Trajektorie wird **unverändert** zurückgegeben, ohne
  RNG-Aufruf, der irgendetwas beeinflussen könnte.
- Keine neue Abhängigkeit ohne Begründung im Report. Die exportierten Dateien mit Hash sind die
  kanonischen Daten, deshalb genügt ein RNG aus der Standardbibliothek. Halte im Report fest,
  welcher es ist und dass seine Ausgabe nur innerhalb von Julia 1.12.6 als stabil gilt.

**2. Einbindung in den Kampagnenlauf.** Neue optionale Manifest-Spalten `noise_sigma`,
`subsample_rho`, `noise_realization` und `clamp_val`. **Fehlen sie, gilt 0 / 0 / 0 / 10**, damit
bestehende Phase-C-Manifeste unverändert laufen. Die Verfälschung greift nach `build_trajectory` und
vor der Suche. Stufenkappe und Fit sehen die verfälschte Trajektorie, sonst ändert sich nichts.

**3. Identität und Record-Felder.**
- `phase_c_fingerprint()` bleibt bei `clamp_val = 10` exakt `0c9672de35c75a9d` und hängt **nicht**
  von der Datenbedingung ab. Bei `clamp_val ≠ 10` ändert er sich, weil die Grenze schon heute im
  Fingerprint steckt. Das ist gewollt.
- Neu ist `data_condition_fingerprint`. Er hasht `sigma`, `rho`, `realization`, den
  Rauschmodellnamen, die Ausdünnungsregel und die Version des Seed-Schemas, und er ist getrennt vom
  Methoden-Fingerprint.
- Neue Experiment-ID für verrauschte bzw. ausgedünnte Records: `paper1_phaseC_robustness_v1`.
  Records bei (0, 0, 10) behalten die C-1-ID **nicht**. Begründe die Wahl im Report.
- Neue Record-Felder: `noise_sigma`, `subsample_rho`, `noise_realization`, `noise_model`,
  `data_condition_fingerprint`, `observed_data_sha256` (Zeit- und Zustandshash der verfälschten
  Trajektorie im bestehenden Hash-Format), `n_observed_points` und `clamp_val`.

**4. Export.** Ein Skript schreibt für eine Liste von (system, ic_set, sigma, rho, realization) die
verfälschten Trajektorien im bestehenden Exportformat samt Indexdatei mit Hashes. Der Hash im
Kampagnen-Record muss identisch sein, sonst ist die C-4-Regel nicht prüfbar. Ausgabe in einen eigenen
Unterordner unter `outputs/`.

**5. Unbeschränkt.** „Unbeschränkt“ heißt `clamp_val = Inf`. Prüfe jede Stelle aus der Ausgangslage
darauf, dass `Inf` korrekt durchläuft. JSON kennt kein `Inf`: Lege eine eindeutige Kodierung für
Records und Fingerprint-Eingabe fest und dokumentiere sie.

**6. Orakel-Refit.** `wp_n3_oracle_refit.jl` bekommt `--clamp-val` (10 | 1000 | Inf, Standard 10).
Bei 10 bleibt die Orakel-Kennung `925e3957a7a884e2`, und die Ausgaben bleiben bitgleich.

**7. Kontrollvergleich (Python).** Ein Skript vergleicht neu erzeugte Records mit den
C-1-Records unter `outputs/phase_c_campaign_221a3a7/`, und zwar Feld für Feld auf `loss`,
`support_terms`, `model_terms` (Koeffizienten bitgenau), `total_loss_evals` und `stage_caps`. Es
meldet jede Abweichung und endet bei Abweichung mit einem Fehlercode. Dasselbe Skript vergleicht
optional Orakel-Ergebnisse mit `outputs/wp_n3_oracle_refit_phase_c/` auf `reference_loss`,
`reference_coefficients` und `reference_fit_meta.loss_evals`.

**8. Prüfung auf unregelmäßige Raster, nur berichten, nichts ändern.** Geh jeden Codepfad durch,
den der Kampagnenlauf mit `evogrow_v2_2_stage_capped` berührt: Stufenkappe einschließlich
`_cap_uniform_step`, `_cap_coarsened_trajectory` und `_cap_interpolate_to_full`, die
Ableitungsschätzer, Loss, `simulate` und R². Liste jede Annahme eines gleichmäßigen Rasters mit
`Datei:Zeile` auf und sag, ob das Verhalten auf einem unregelmäßigen Raster definiert bleibt oder
einen Fehler wirft. **Methodencode wird nicht angepasst.** Er ist eingefroren, und sein Verhalten
auf unregelmäßigen Rastern gehört zur Methode. Wirft ein Pfad einen Fehler, meldest du `blocked`
mit der Fundstelle.

**9. Tests** (Julia, je Datei unter `test/`, Python unter `analysis/tests/` bzw. neben dem Skript):
- (0, 0) liefert eine bitgleiche Trajektorie;
- gleicher Schlüssel → gleiche Daten; andere Realisierung → andere Daten; der Methoden-Seed hat
  keinen Einfluss;
- die Rauschskala ist relativ, geprüft an einem festen Array;
- die Ausdünnung entfernt genau `floor(n*rho)` Punkte, Zeiten bleiben aufsteigend, keine Duplikate;
- `phase_c_fingerprint()` ist bei 10 `0c9672de35c75a9d` und invariant gegenüber der Datenbedingung;
- `Inf` übersteht Fingerprint und JSON in beiden Richtungen;
- die Record-Felder werden an einer Fixture geprüft, die **aus einem echten C-1-Record abgeleitet**
  ist (`CODEX_PROTOCOL.md`, „Fixtures werden abgeleitet“).

## Verboten

- Methodenverhalten ändern: Basis, Kappe, Pruning, Optimierer, Budgets, `loss_tol`, Level, Defaults.
  Der Standardwert von `clamp_val` bleibt 10.
- Bestehende Fingerprints oder deren Eingaben ändern, ausgenommen die oben beschriebene, gewollte
  Wirkung von `clamp_val ≠ 10`.
- Rauschspezifische Abbruch- oder Suchregeln.
- k8s-Manifeste, Kampagnen-Manifeste oder Cluster-Jobs erzeugen; das ist WP-N33.
- Läufe über 15 Minuten, Git-Operationen, `codex/CURRENT_TASK.md` bearbeiten, Dateien unter
  `docs/` ändern. Einen Eintrag in `SCRIPTS.md` darfst du anlegen.

## Abnahme

1. Alle Punkte 1–9 sind umgesetzt. Der Report nennt für jedes neue Record-Feld die Herkunft
   (bestehendes Recordfeld, neues Recordfeld oder Analysepipeline).
2. Die Python-Tests laufen grün **in deiner Sitzung**. Julia-Tests und Kontrollläufe stehen als
   Kommandos im Report, weil Julia in deiner Umgebung nicht läuft.
3. Der Report enthält Kommandos für Claude, jedes mit Zweck und erwarteter Dauer:
   - (a) die Julia-Tests;
   - (b) die vier Kontrollzellen über den neuen Pfad bei (0, 0, 10): Systeme 1 und 24, Seed 42,
     beide IC-Sets, jeweils mit anschließendem Kontrollvergleich gegen C-1. Erwartet ist eine
     bitgleiche Übereinstimmung;
   - (c) eine verrauschte Zelle auf System 1 bei (0.05, 0.5) als Durchstich, mit Prüfung, dass
     `observed_data_sha256` dem Export entspricht;
   - (d) drei Orakelzellen bei `--clamp-val 10` mit Vergleich gegen die C-5-Orakel-Ergebnisse,
     dazu dieselben drei bei `1000` und `Inf` als reiner Durchlauftest.
4. Die Prüfung auf unregelmäßige Raster (Punkt 8) steht vollständig im Report.
5. Report: `codex/reports/REPORT_WP_N32.md`. `STATUS.md` nach Protokoll. Weil Julia nicht
   ausführbar ist, ist `blocked` mit dem Vermerk *Umgebung, nicht Sache* der erwartete Abschluss.

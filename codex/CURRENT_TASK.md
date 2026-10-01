# WP-N33a — Auswertung gegen die saubere Wahrheit, Tor-Bericht, Fix am Kontrollvergleich
**Language: Julia** (Auswertung) **und Python** (Tor-Bericht, Fix)

Verbindliche Spezifikation: `docs/paper1_phaseC_benchmark_plan.md` **§9.3, §9.4 und §9.4a**.
Vorarbeit: WP-N32 (`codex/reports/REPORT_WP_N32.md`). Stufe 0 ist bestanden: System 1, Seed 42,
beide IC-Sets, bitgleich zu C-1 (Records unter `outputs/wp_n32_stage0/tasks/`).

## Ziel

Jede Stufe des gestuften Einstiegs endet an einem Tor. Dort berichtet Claude je Zelle eine fest
vorgegebene Liste von Zahlen (§9.4a). Dieses Paket baut die beiden Werkzeuge dafür und behebt einen
Fehler im Kontrollvergleich.

## 1. Fix: `analysis/scripts/aggregate/compare_phasec_controls.py`

Gefunden bei der Abnahme von WP-N32: Das Skript liest beim Verzeichnis-Eingang auch
`*.heartbeat.jsonl` mit ein. Heartbeat-Zeilen haben kein `loss`, also stürzt
`normalize_campaign_field` mit `TypeError: float() argument must be ... not 'NoneType'` ab.
Reproduktion:

```
python analysis/scripts/aggregate/compare_phasec_controls.py --candidate outputs/wp_n32_stage0/tasks --reference-c1 outputs/phase_c_campaign_221a3a7
```

Erwartet ist danach: Exit 0, beide Zellen bitgleich. Claude hat das von Hand geprüft. Zusätzlich
gilt: Ein fehlendes Feld auf einer Seite ist eine **gemeldete Abweichung** mit Feldnamen und Seite,
nie ein Absturz und nie ein stilles Bestehen. Kandidaten-Records anderer Varianten als der des
Referenz-Schlüssels werden nicht verglichen. Der Schlüssel enthält die Variante, nicht nur System,
IC und Seed. Ein Test dafür nutzt eine Fixture, die aus den echten Dateien unter
`outputs/wp_n32_stage0/tasks/` abgeleitet ist, einschließlich der Heartbeat-Datei.

## 2. Saubere Auswertung (Julia)

Ausgangspunkt ist `studies/regression/wp_n5_ic_generalization.jl` mit `main_phase_c`. Dort sind
Modellrekonstruktion aus `model_terms`, Integration und die Rekonstruktionskontrolle schon
vorhanden. **Erweitern oder wiederverwenden, nicht neu bauen.**

Für jeden Kampagnen-Record, ob mit oder ohne Datenbedingung:
- **Rekonstruktion:** das identifizierte Modell aus der **sauberen** Trainings-Anfangsbedingung auf
  dem **vollen sauberen** 512-Punkte-Raster integrieren (`build_trajectory(system, ic_set)`) und
  gegen die saubere Trajektorie messen. **Nicht** gegen die verrauschten Beobachtungen und **nicht**
  auf dem ausgedünnten Raster.
- **Generalisierung:** aus der sauberen **anderen** ODEBench-Anfangsbedingung auf deren vollem
  sauberen Raster integrieren, gemessen gegen die saubere Trajektorie.
- R² in **beiden** Aggregationen, das arithmetische Mittel über die Dimensionen (wie `r2` im Record)
  und das varianzgewichtete (§6b; die Gewichte sind die Varianzen der sauberen Referenz). Divergenz
  bzw. nicht-endliche Vorhersagen werden als solche markiert, nicht als R² = −∞ gemittelt.
- **Vorhersagen speichern** (§9.3): rekonstruierte und generalisierte Trajektorie je Zelle als
  Dateien im bestehenden Exportformat (`phase_c_trajectory_hash_lib.jl`), mit Hash in der
  Ergebniszeile.
- Ergebniszeile je Zelle mit Schlüssel (Variante, System, IC-Set, Seed, `noise_sigma`,
  `subsample_rho`, `noise_realization`, `clamp_val`), den vier R²-Werten, Divergenz-Flags und den
  Hashes der Vorhersagen. Jedes Skript schreibt in einen eigenen Unterordner unter `outputs/`.

**Kontrollen, im Code fest eingebaut und als Kommando für Claude:**
- Auf Records **ohne** Datenbedingung muss die Rekonstruktion das gespeicherte `r2` des Records
  **exakt** reproduzieren, mit derselben Toleranz wie die bestehende WP-N5-Kontrolle. Bei
  verrauschten Records gilt diese Kontrolle nicht, weil das `r2` im Record gegen die verrauschten
  Daten misst (§9.4). Das Skript darf sie dort nicht anwenden und auch nicht als bestanden melden.
- Auf den beiden Stufe-0-Records muss die Generalisierung bitgleich zu den C-1-Zahlen in
  `outputs/wp_n5_ic_generalization_phase_c/` sein.

## 3. Tor-Bericht (Python)

Ein Skript `analysis/scripts/aggregate/robustness_stage_report.py`. Eingabe: ein Verzeichnis mit
Stufen-Records, die Ausgabe von Punkt 2 und die C-1-Referenz. Ausgabe: eine CSV und eine kurze
Markdown-Tabelle mit **einer Zeile je Zelle, ohne Auswahl**. Neben jeder Zelle steht die C-1-Zelle
mit gleicher Variante, gleichem System, IC-Set und Seed. Spalten genau nach §9.4a, „Reported at
every stage“:

`executed_levels` (gegen C-1), `total_loss_evals`, `total_parameter_fits`, `final_stage`,
`stage_caps` je Gleichung samt Änderung gegenüber C-1 (gleich / enger / weiter / zu `nothing`),
roher und geprunter Treffer gegen die Wahrheit (nur exakte Systeme, sonst leer und als Surrogat
markiert), saubere Rekonstruktion und Generalisierung in beiden Aggregationen, `elapsed_s` als
Kapazitätskontext (in der Kopfzeile als *keine Evidenz* markiert). Dazu die Faktoren gegen C-1 für
Loss-Evals und Fits.

Dazu die **harten Prüfungen aus §9.4a** als eigener Block mit bestanden / nicht bestanden je Zelle:
kein `error` und kein `failure_reason`; Methoden-Fingerprint `0c9672de35c75a9d` (bei
`clamp_val = 10`); alle neuen Felder nicht null; `observed_data_sha256` gleich dem Hash der
exportierten Datei, wenn ein Exportindex angegeben ist. Das Skript fasst nicht zusammen, mittelt
nicht und bewertet nicht. Es zeigt die Zahlen.

Die Wahrheit für die Trefferprüfung kommt aus dem bestehenden Pfad, `phase_c_support.json` bzw.
`exact_support_match_raw` / `exact_support_match_pruned` im Record. Nicht neu ableiten.

## Verboten

- Methodencode, Kampagnen-Runner, Fingerprints oder Manifeste ändern.
- Läufe über 15 Minuten, Cluster, Git-Operationen, `codex/CURRENT_TASK.md` bearbeiten, Dateien
  unter `docs/` ändern. Einen Eintrag in `SCRIPTS.md` darfst du anlegen.
- Zusammenfassende Urteile im Tor-Bericht („gut“, „bestanden“ für die Stufe als Ganzes).

## Abnahme

1. Der Fix aus Punkt 1 ist umgesetzt. Das Reproduktionskommando endet mit Exit 0, und die Tests
   sind grün. Python läuft in deiner Sitzung, also führst du beides selbst aus.
2. Der Tor-Bericht läuft **in deiner Sitzung** auf `outputs/wp_n32_stage0/tasks/` gegen C-1. Fehlt
   noch die Ausgabe von Punkt 2, bleiben die R²-Spalten leer und sind als fehlend markiert. Die
   Python-Tests sind grün, mit Fixtures aus echten Records.
3. Für Punkt 2 stehen im Report Kommandos für Claude, mit Zweck und erwarteter Dauer:
   - die saubere Auswertung auf `outputs/wp_n32_stage0/tasks/` mit beiden Kontrollen;
   - danach der Tor-Bericht mit gefüllten R²-Spalten.
4. Report: `codex/reports/REPORT_WP_N33A.md`. `STATUS.md` nach Protokoll. Weil Julia nicht
   ausführbar ist, ist `blocked` mit dem Vermerk *Umgebung, nicht Sache* der erwartete Abschluss,
   sofern Punkte 1 und 3 fertig sind.

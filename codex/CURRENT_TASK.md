# WP-N34b — Nacharbeit WP-N34: C-4-Kontrolle umsetzen, Structural F1, mehrere Tor-Berichte
**Language: Python**

Abnahme von WP-N34 durch Claude (2026-10-01): Der Lauf auf System 1 funktioniert, und die Hashes
sind geprüft. **Drei Punkte fehlen**, und die Abnahme bleibt offen, bis sie erledigt sind.

## 1. Die C-4-Kontrolle ist nicht umgesetzt

`control_status()` meldet auch mit vorhandenem Index nur `not_run: control execution is
intentionally separate…`. Verlangt war, dass der neue Pfad die vorhandenen C-4-Ergebnisse
**exakt reproduziert**. Claude hat den Kontrollindex jetzt erzeugt:
`outputs/wp_n34_control_export/index.csv` (Systeme 1 und 24, IC-Sets 1 und 2, `(0, 0)`,
Realisierung 0, gequotet).

Umsetzen: Mit `--control-export-index` laufen alle zehn SINDy-Konfigurationen auf diesen Zellen.
Verglichen wird mit den bestehenden C-4-Ergebnissen. Den Pfad findest du über `SCRIPTS.md` bzw. die
WP-N30-Ausgaben, zum Beispiel unter `outputs/phase_c_campaign_221a3a7/agg/sindy_n30/` oder
`analysis/data/paper1_phaseC_v1/`; prüf, welche Datei die Einzelergebnisse je Konfiguration trägt.
Verglichen werden aktive Terme, Koeffizienten, R² der Rekonstruktion und R² der Generalisierung.
Jede Abweichung wird gemeldet, bei einer Abweichung ist der Exit-Code ungleich 0.
**Vorher klären und im Report festhalten:** ob C-4 dieselbe Trajektorie verwendet. Laut `CLAUDE.md`
(WP-C4b) konsumiert C-4 die exportierten Kampagnen-Trajektorien. Unser Export bei (0, 0) gibt die
saubere `build_trajectory`-Trajektorie zurück. Prüf per Hash, dass beide identisch sind, bevor du
Ergebnisse vergleichst. Sind sie es nicht, ist das der Befund, und die Kontrolle meldet es als
solchen.

## 2. Structural F1, Precision und Recall fehlen

§9.3 verlangt roh, gepruned und F1. `details.csv` hat bisher nur `sindy_structure_hit_raw` und
`sindy_structure_hit_pruned`. Ergänze Precision, Recall und F1 auf dem geprunten Träger. Nutze dafür
die bestehende Implementierung in `analysis/utils/metrics.py`, keine zweite. Nur exakte Systeme,
sonst leer und als nicht exakt markiert.

## 3. Mehrere Tor-Berichte

`--stage-report` nimmt nur eine Datei. Die Stufe-1-Berichte liegen je Bedingung getrennt vor
(`outputs/stage1/s0.01_r0/report/…`, `outputs/stage1/s0.05_r0.5/report/…`). Erlaube mehrere
Dateien oder ein Verzeichnis-Glob, damit die Vergleichstabelle beide Stufe-1-Zellen findet. Kein
Treffer bleibt sichtbar `missing_in_stage_report`.

## Verboten

Wie in WP-N34: keine Änderung an SINDy-Konfigurationen, keine Auswahl, keine Interpolation, kein
Julia- oder Methodencode, kein Git, kein `docs/`, `codex/CURRENT_TASK.md` nicht bearbeiten.

## Abnahme

1. Kontrolle auf `outputs/wp_n34_control_export/index.csv`: bestanden, oder ein klar benannter
   Befund mit Hashes. Ausgeführt **in deiner Sitzung**.
2. F1, Precision und Recall stehen in `details.csv`. Ein Test mit einer Fixture aus echtem Export
   ist grün.
3. Die Vergleichstabelle für Stufe 1 enthält beide EvoGrow-Zellen, also (0,01; 0) und (0,05; 0,5).
4. Report `codex/reports/REPORT_WP_N34B.md`, `STATUS.md` nach Protokoll.

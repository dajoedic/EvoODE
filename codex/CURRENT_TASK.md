# WP-T1f-d — Kontrolle trennen: Zuordnungsprüfung bei Datentoleranz, Optimiererboden als Messung
**Language: Julia**

## Ausführung

Codex kann in dieser Umgebung kein Julia ausführen (`codex/CODEX_PROTOCOL.md`). Umsetzen, Befehle für
Claude im Report auflisten, Status `blocked` melden. Keine Git-Operationen, kein `oc`/`kubectl`,
kein Lauf der Probe.

## Ausgangslage

WP-T1f, -b und -c liegen uncommittet im Working Tree. Alle Tests grün. `--control-only` ohne Kappung:
34 von 36 Zellen unter der Abbruchgrenze 1e-4, zwei chaotische Lorenz-Zellen darüber
(55/IC 2: 7,5e-4; 56/IC 2: 1,2e-4).

**Claude hat die Ursache gemessen:** Die Kontrolle simuliert mit der Optimierer-Toleranz
(`abstol = reltol = 1e-6`), die Daten sind mit 1e-9 integriert. Mit 1e-9 simuliert liegt der
Kontroll-Loss für 55 und 56, beide ICs, bei ~1e-21; mit 1e-6 bei 1e-5 bis 7,5e-4 (Datenvarianz
~200 bzw. ~2.500). Die Koeffizienten-Zuordnung ist also exakt; die Abweichung ist chaotisches
Anwachsen des Toleranzfehlers.

Die Kontrolle vermischt damit zwei Größen: ob die Zuordnung stimmt (ihr erklärter Zweck) und wie
tief der Optimierer auf diesem System überhaupt kommen kann.

## Was zu tun ist

1. **Zwei Kontrollgrößen statt einer**, in jeder Zelle und in `--control-only`:
   - `control_loss_data_tolerance`: Loss an den wahren Parametern, ohne Kappung, simuliert mit
     `abstol = reltol = 1e-9` (die Toleranz der Trajektorien-Erzeugung; als Konstante mit Kommentar
     auf ihre Herkunft, nicht als freie Zahl). **Nur diese Größe entscheidet über den Abbruch**, mit
     unveränderter Grenze 1e-4.
   - `control_loss_optimizer_tolerance`: derselbe Loss mit dem WP-T1f-Optimierer (ohne Kappung,
     Optimierer-Toleranzen). Wird mitgeschrieben, bricht nichts ab. Er ist der Boden des Optimierers
     auf dieser Zelle.
   Die Kontrollzeile trägt beide Werte; `control_loss` im bisherigen Sinn entfällt zugunsten dieser
   zwei eindeutigen Namen (die Aggregation muss damit umgehen).
2. **Aggregation:** `control_and_floor_loss_by_cell.csv` zeigt beide Kontrollgrößen neben dem Boden.
   Dazu je Zelle das Verhältnis Boden / `control_loss_optimizer_tolerance`, damit sichtbar ist, wo
   der Boden am Optimierer-Limit liegt.
3. **`--control-only`** schreibt beide Spalten in `control_only.csv`; Exit ≠ 0 nur, wenn
   `control_loss_data_tolerance` eine Zelle über 1e-4 bringt.
4. `SCRIPTS.md`, Abschnitt WP-T1f: ein Satz zur Trennung.

## Verboten

- Die Grenze 1e-4, m, Margins, Schwellen, Budget, Retry-Regel und die Optimierer-Toleranzen bleiben.
- Keine Änderung an `src/`, `run_regression.jl`, `phase_c_config.jl`. Das Verhalten von
  `wp_t1d_neighbourhood_loss.jl` bei Default-Aufruf bleibt unverändert.

## Abnahme

1. Test: Der Abbruch hängt nur an `control_loss_data_tolerance`; ein hoher Wert der
   Optimierer-Toleranz allein bricht nicht ab; beide Felder stehen in der Kontrollzeile.
2. Report `codex/reports/REPORT_WP_T1f_d.md` mit den Julia-Befehlen für Claude: beide Tests,
   `--self-test`, `--control-only` (Erwartung: Exit 0, alle 36 Zellen unter 1e-4 bei Datentoleranz),
   `--smoke --fresh`.
3. `codex/STATUS.md`: `status: blocked`, WP-T1f-d, Report-Pfad.

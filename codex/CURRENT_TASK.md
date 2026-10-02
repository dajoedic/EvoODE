# WP-N38 (Fortsetzung 2) — das Referenzraster-Skript bleibt, wie es war
**Language: Python**

Auftrag und Abnahme von WP-N38 gelten weiter. Die Dateien liegen uncommittet im Working Tree.
**Weiterarbeiten, nicht neu anfangen.**

## Befund (Claude, 2026-10-02)

Die Kontrolle besteht jetzt (`passed: true`, 0 Befunde), und `pytest baselines/tests` läuft grün
(49 passed, 5 skipped). Die Änderung an `baselines/compare_odeformer_equivalence.py` ist aber
**nicht verhaltensneutral** auf vollen Rastern. Claude hat die HEAD-Fassung und die neue Fassung
auf drei Paaren laufen lassen (`analysis/data/paper1_phaseC_v1/odeformer_baseline/`):

| Paar | alt: Records / Befunde | neu: Records / Befunde |
|---|---|---|
| reference_wp_n23 / candidate_wp_n23 | 126 / 615 | 504 / 2685 |
| reference_orion_55e9c75 / candidate_orion_8e0e699 | 126 / 617 | 504 (roh 1512) / 8079 |
| reference / candidate | 126 / 615 | 504 / 2687 |

Ursache: Die alte Fassung schlüsselt ohne Konfiguration und verdichtet damit 504 Records auf 126
Schlüssel. Je Zelle wird nur eine der vier Konfigurationen verglichen. Das ist ein Altfehler.
Behoben wird er aber **nicht stillschweigend** in einem Skript, dessen Ausgaben ältere Berichte
zitieren (WP-N21).

## Umsetzung

1. `baselines/compare_odeformer_equivalence.py` wird **byte-identisch auf HEAD** zurückgesetzt.
2. Die korrekte Paarung (Schlüssel mit Konfiguration, Bestehen gegen eine beliebige Wiederholung
   derselben Konfiguration, nur die Schnittmenge der Kandidatenschlüssel) kommt in
   `baselines/run_odeformer_noise.py` oder in ein eigenes neues Modul. Die vorhandenen Tests für den
   Fall aus Fortsetzung 1 bleiben und laufen gegen den neuen Ort.
3. **Altfehler beziffern, nicht reparieren:** In `codex/reports/REPORT_WP_N38.md` einen Abschnitt
   anlegen mit
   - welche Berichte oder Ausgaben die alte Fassung erzeugt haben (mindestens WP-N21 prüfen: Wie
     viele Konfigurationen je Zelle hatten die dort verglichenen Records? Bei genau einer war der
     Fehler dort wirkungslos);
   - ob die Raten des Referenz- und Kandidatenrasters (WP-N27/N29, `summarize_odeformer_grid.py`)
     über diesen Vergleich laufen oder unabhängig davon sind;
   - der obigen Tabelle.

   Ergebnisdateien werden dabei nicht verändert.

## Verboten

Wie WP-N38. Die alte Fassung inhaltlich ändern. Toleranzen lockern.

## Abnahme

`git diff HEAD -- baselines/compare_odeformer_equivalence.py` ist leer. Tests grün. Report
ergänzt. `STATUS.md` nach Protokoll.

# CURRENT TASK: WP-v3.3 — Gleichungsweise Kindergenerierung in EvoGrowV3

**Language: Julia**

## Context

Die Screening-Spur (WP-P2.x) ist per Abbruchregel eingestellt. Zurück zur eigentlichen
Forschungsarbeit: EvoGrow v3.

Stand: WP-v3.2 hat `EvoGrowV3` als **Lockstep-Brücke** gebaut. Die Variante führt bereits
gleichungsweise Stage-Zustände (`eq_stages`), promoviert aber alle Gleichungen gemeinsam und ist
dadurch verhaltensgleich zu v2.2 — nachgewiesen bit-identisch auf System 3, 11 und 26.

WP-v3.3 setzt Abschnitt 6 der Designnotiz `docs/evogrow_v3_design.md` um: die Kindergenerierung
wird gleichungsweise gesteuert. Die gleichungsweise **Promotion** kommt erst in WP-v3.4.

**Daraus folgt das entscheidende Akzeptanzkriterium:** Solange alle Gleichungen im Lockstep
promovieren, sind alle Einträge in `eq_stages` zu jedem Zeitpunkt gleich. Eine korrekt umgesetzte
gleichungsweise Kindergenerierung muss in diesem Zustand **exakt dieselben Kinder erzeugen** wie
heute. WP-v3.3 ist also ein verhaltensneutraler Umbau, dessen Wirkung erst mit WP-v3.4 sichtbar
wird. Jede Abweichung ist ein Fehler, kein Fortschritt.

## Goal

Kindergenerierung in `EvoGrowV3` so umbauen, dass die zulässigen Terme pro Gleichung aus
`eq_stages[k]` abgeleitet werden statt aus einer globalen `current_stage`, bei nachgewiesen
unverändertem Verhalten im Lockstep-Zustand.

## Files

- **Ändern:** `src/structure/evogrow_v3.jl`.
- **Nicht anfassen:** `src/structure/evogrow.jl`, `evogrow_screening.jl`, `gp.jl`,
  `core/stopping.jl`, `core/discover.jl`, `basis/`.

Falls für die gleichungsweise Termauswahl eine Hilfsfunktion in `evogrow.jl` benötigt wird, die
dort nicht existiert: neue Funktion in `evogrow_v3.jl` anlegen, `evogrow.jl` nicht verändern.

## Required Content

### 1. Gleichungsweise zulässige Terme

Die zulässigen Basisterme werden pro Gleichung `k` aus `eq_stages[k]` bestimmt, nicht mehr aus
einer aggregierten Stage. Die Erweiterung einer Gleichung darf nur Terme verwenden, die für **diese**
Gleichung freigeschaltet sind.

### 2. Regel für Kreuzterme

Designnotiz Abschnitt 6: Ein Kreuzterm, der Variablen der Gleichungen `i` und `j` enthält, ist für
Gleichung `k` nur verfügbar, wenn `min(eq_stages[i], eq_stages[j])` die für diesen Kreuzterm
erforderliche Stage erreicht. Die Stage-Zuordnung der Terme selbst bleibt unverändert gegenüber
`StagedPolynomialBasis`.

Diese Regel gilt als entschieden — Abschnitt 9 der Designnotiz führt sie fälschlich noch als offene
Frage. Setze Abschnitt 6 um.

Halte die Konsequenz im Docstring fest: ein Kreuzterm ist an die Stages der Gleichungen gebunden,
zu denen seine **Variablen** gehören, nicht an die Stage der verwendenden Gleichung `k`. Gleichung 3
kann `u1*u2` also erst nutzen, wenn Gleichung 1 und Gleichung 2 weit genug sind, selbst wenn
Gleichung 3 längst promoviert hat. Das ist die einzige Stelle, an der die Gleichungen gekoppelt
bleiben. Falls sich diese Regel in WP-v3.4 als hinderlich erweist, ist sie dort erneut zu prüfen.

### 3. Stage-Usage-Policy pro Gleichung

`StageUsagePolicy` wird pro Gleichung ausgewertet. `:hard`, `:soft` und `:passive` behalten ihre
Bedeutung aus v2.2, werden aber unabhängig für jede Gleichung angewandt, die im aktuellen Level
promoviert hat. Solange alle Gleichungen gemeinsam promovieren, muss das dasselbe Ergebnis liefern
wie heute.

### 4. Population bei Promotion unverändert

Abschnitt 7 der Designnotiz: die Population wird bei Promotion unverändert übernommen, kein Reset.
Nicht ändern.

### 5. Determinismus der Zufallsziehungen

Kritisch für die Verifikation: Die Umstellung darf die **Reihenfolge und Anzahl der Zufallsziehungen**
nicht verändern. Wird der RNG in anderer Reihenfolge oder anderer Häufigkeit abgefragt, weichen die
Ergebnisse ab, obwohl die Logik korrekt wäre — und das Akzeptanzkriterium aus Punkt 1 der
Verifikation wäre nicht mehr prüfbar. Plane den Umbau entsprechend und beschreibe im
Abschlussbericht, wie die RNG-Reihenfolge erhalten wurde.

### 6. Screening-Variante aus der Regression-Konfiguration nehmen

Getrennter, kleiner Punkt: Die Screening-Spur ist eingestellt. Entferne den Eintrag
`evogrow_screening_derivative` aus `VARIANTS` in `studies/regression/run_regression.jl`, damit
künftige Baselines nicht 50 % mehr Zellen rechnen. Der Code der Variante, die Designnotiz und das
Vergleichsskript bleiben erhalten — nur die Registrierung im Regression-Runner entfällt. Dass sich
dadurch der `config_fingerprint` ändert, ist beabsichtigt.

## Verification

Nur billige Zellen. **Kein** Volllauf, **nicht** System 26, 31 oder 63.

1. **Hauptkriterium:** `EvoGrowV3` liefert auf System 3 und System 11, Seed 42, nach dem Umbau
   **bit-identische** Ergebnisse zu vorher: Loss, `final_stage`, `pruned_match`,
   `total_parameter_fits`, `total_ode_solves`. Referenzwerte aus Baseline v0
   (`studies/regression/history.jsonl`): System 3 Loss `2.663641831768419e-10`, `final_stage = 3`;
   System 11 Loss `4.402192340718147e-15`, `final_stage = 4`.
   Weicht etwas ab, ist der Umbau nicht verhaltensneutral — melden, nicht glätten.
2. `evogrow_v2_2_stage_local` bleibt ebenfalls unverändert gegen dieselben Referenzwerte.
3. Ein konstruierter Fall mit künstlich ungleichen `eq_stages` (nur zur Prüfung, nicht als
   dauerhafte Funktion) zeigt, dass Gleichungen mit niedrigerer Stage tatsächlich weniger Terme
   angeboten bekommen und dass die Kreuzterm-Regel aus Punkt 2 greift. Beschreibe, wie du das
   geprüft hast.

`studies/debug/compare_screening_variant.jl` kann als Vorlage für den Vergleichslauf dienen; ein
eigenes kleines Skript ist ebenfalls in Ordnung. Ausgabe in einen eigenen Unterordner unter
`outputs/studies/debug/`.

Berichte die gemessenen Zahlen, nicht „läuft durch".

## Constraints

- Verhaltensneutral im Lockstep-Zustand. Das ist das zentrale Kriterium.
- Gleichungsweise **Promotion** ist ausdrücklich **nicht** Teil dieses WP (das ist WP-v3.4).
  `eq_stages` bleiben vorerst gleichgeschaltet.
- Kein Eingriff in Stopplogik, Plateau-Erkennung oder Selektion.
- `evogrow.jl` bleibt unangetastet.
- Keine neuen Abhängigkeiten.
- Nicht Teil dieses WP: WP-v3.4 bis WP-v3.6, WP-H2, Wiederaufnahme der Screening-Spur.

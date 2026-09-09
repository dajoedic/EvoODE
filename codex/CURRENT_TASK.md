# WP-N10 — Kanonischer Strukturschlüssel und die Messung der Duplikatrate

**Language: Julia**

## Warum

Die kanonische EvoGrow-Konfiguration enthält einen tragenden, unbenannten Mechanismus. Unter
`pretuning = false` zieht jeder Parameterfit `0.1 .* randn` (`src/optimize/bfgs.jl:269`). Jede
Kandidatenstruktur bekommt aber genau **einen** Fit — ein zweiter Start entsteht nur, wenn die Suche
dieselbe Struktur zufällig erneut erzeugt. Das effektive Restart-k ist damit die
**`StructureSpec`-Duplikatrate**, und die ist **nie gemessen worden**.

Ohne sie ist der k = 1-Referenzpunkt der Restart-Ablation (Abl-3 in
`docs/paper1_phaseC_benchmark_plan.md`) nicht definiert, und jede Aussage über Restarts hängt in der
Luft.

Nachgeprüft: **aus vorhandenen Daten ist das nicht rekonstruierbar.** `level_log`
(`src/structure/evogrow.jl:876`) hält je Level nur das Beste fest — `best_loss`, `best_objective`,
`n_params`. Die in `_expand*` erzeugten Kandidatenstrukturen werden nirgends persistiert, weder in
den Records noch in den Heartbeats.

## Was zu tun ist

### Teil 1 — Kanonische Gleichheit und Hash für `StructureSpec`

Ein kanonischer Schlüssel, der zwei Strukturen genau dann gleich abbildet, wenn sie **denselben
Support** haben — unabhängig von der Reihenfolge, in der die Terme aufgenommen wurden, und
unabhängig von den Parameterwerten.

Zwei Punkte, an denen es leicht falsch wird:

- Die Struktur ist **je Gleichung** definiert. Der Schlüssel muss die Gleichungszuordnung erhalten:
  `u1` in Gleichung 1 und `u1` in Gleichung 2 sind nicht dasselbe.
- Reihenfolgeunabhängigkeit **innerhalb** einer Gleichung ist erwünscht, **zwischen** Gleichungen
  nicht.

Der Schlüssel wird ausschließlich zum Zählen verwendet.

### Teil 2 — Zähler in der Suchschleife

In `src/structure/evogrow.jl` mitzählen und in die Ergebnis-Metadaten aufnehmen:

- Gesamtzahl bewerteter Kandidatenstrukturen
- Zahl **eindeutiger** Strukturschlüssel
- die Verteilung der Wiederholungen, nicht nur ein Mittelwert — mindestens Quantile oder ein
  Häufigkeitsgitter „wie oft wurde eine Struktur k-mal bewertet". Ein Mittelwert allein ist nach der
  stehenden Analyseregel des Projekts nicht berichtbar.
- dieselben Größen zusätzlich **je Level und je Stufe**, damit sichtbar wird, ob Duplikate am Anfang
  oder Ende der Suche entstehen

### Teil 3 — Ein Zähler, der nichts verändert

**Das ist die eigentliche Anforderung dieses Pakets.** Der Zähler darf das Suchverhalten in keiner
Weise beeinflussen — insbesondere **keine Zufallsziehung verändern, hinzufügen oder verschieben**.
Wird die RNG-Sequenz verändert, sind Phase-C-Zellen nicht mehr mit den Regressions- und
Kampagnendaten vergleichbar, und die gesamte Vergleichbarkeitskette des Projekts reißt.

Ebenso: **kein Caching, keine Deduplizierung, kein Überspringen** bereits gesehener Strukturen. Unter
`pretuning = false` wirken Duplikate als impliziter Multistart; sie zu überspringen würde die
experimentelle Bedingung ändern statt sie nur zu beschleunigen. Der Zähler zählt und tut sonst nichts.

## Abnahme

1. **Bit-identische Regression.** Ein Regressionslauf über das bestehende Gitter liefert mit Zähler
   **exakt** dieselben Ergebnisse wie ohne: `loss` bit-identisch, `pruned_match` unverändert, und die
   Auswertungszähler (`total_loss_evals`, `total_parameter_fits`, `total_ode_solves`) identisch. Eine
   einzige Abweichung heißt, dass der Zähler das Verhalten verändert, und ist ein Abnahmefehler.
   Nenne das Kommando; Claude fährt den Lauf.
2. **Fingerprints unverändert.** `phase_b_fingerprint()` bleibt `604e79733b22d64d`,
   `stage_cap_behavior_fingerprint()` bleibt `ffb0266c7913352c`. Ein Zähler ist keine
   Konfigurationskonstante und darf keinen Fingerprint bewegen.
3. Die neuen Größen stehen in den Ergebnis-Metadaten und landen im Record.
4. Tests für den kanonischen Schlüssel unter `test/`: gleiche Struktur in anderer Termreihenfolge
   ergibt denselben Schlüssel; dieselben Terme in **anderen Gleichungen** ergeben einen **anderen**;
   verschiedene Parameterwerte bei gleichem Support ergeben denselben.
5. Ein kurzer Lauf auf einem kleinen System zeigt plausible Zahlen — eindeutig ≤ gesamt, und die
   Verteilung ist ausgegeben.

**Julia lässt sich in deiner Sitzung nicht ausführen.** Code schreiben, statisch sorgfältig prüfen,
`status: blocked` melden mit `note: Umgebung, nicht Sache`. Claude fährt Regression und Abnahme.

Geh das geänderte Modul auf Laufzeitfehlerklassen durch, die ein statischer Blick übersieht: `Set`
gegen `Vector`, fehlende `collect`-Aufrufe, Indizierung mit `nothing`, Typinstabilität in der heißen
Schleife, und Zugriffe auf Felder, die je nach Variante fehlen können.

## Verboten

- **Keine Deduplizierung, kein Cache, kein Überspringen.** Nur zählen.
- **Keine Änderung an der RNG-Nutzung**, auch keine scheinbar harmlose Umstellung der Reihenfolge.
- **Keine Änderung an Ausdünnungsregel, Kappe, Stufenlogik oder Konfigurationskonstanten.**
- **Keinen Kampagnen- oder Cluster-Lauf starten.** Auf dem Cluster läuft gerade der dim-2-Probelauf;
  nichts einreichen, nichts löschen, keine `kubectl`- oder `oc`-Aufrufe.
- Nichts über 15 Minuten.
- Nicht committen, nicht stagen, keine Git-Operationen.

## Report

`codex/reports/REPORT_WP_N10.md`. Enthält:

- wie der kanonische Schlüssel gebildet wird und warum er reihenfolgeunabhängig innerhalb, aber nicht
  zwischen Gleichungen ist
- die Stelle in der Suchschleife, an der gezählt wird, und die Begründung, warum sie die RNG-Sequenz
  nicht berührt
- das Kommando für den bit-identischen Regressionsvergleich
- die durchgesehenen Laufzeitfehlerklassen

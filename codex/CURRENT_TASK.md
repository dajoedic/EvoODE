# WP-C4a2 — Der kontaminierte Median, und das korrigierte Abnahmekriterium

**Language: Python**

## Ausgangslage

WP-C4a ist abgenommen und committet (`465ef58`). Die Abgabe war gut: 2.520 Zeilen über 63 Systeme,
kanonische Repräsentierbarkeit, beide Generalisierungsrichtungen getrennt, alle zehn Konfigurationen
ohne Nachauswahl, Trajektorien-Hashes dokumentiert, Paarung gegen die Pilot-Records, 52 Tests grün.

Zwei Dinge bleiben, eines davon ein echter Defekt.

## 1. Der Defekt: `r2_median_valid` ist mit Müll aus divergierten Integrationen kontaminiert

In `analysis/scripts/aggregate/run_phasec_sindy_baseline.py` (Zeilen um 284–287) wird die Auswahl
für den Median über **Endlichkeit** von `r2` gebildet. Das ist die falsche Bedingung. Eine
divergierte Integration liefert regelmäßig einen **endlichen, aber sinnlosen** R²-Wert; die Spalte
`diverged_or_nonfinite` ist bereits vorhanden und trägt genau diese Information.

Messbare Folge in der eingecheckten Ausgabe
(`analysis/data/paper1_phaseC_v1/phasec_sindy_baseline/summary.csv`):

- `r2_median_valid` reicht bis **−1,181e+86**,
- `r2_valid_count == n_cells − diverged_or_nonfinite_count` gilt nur in **196 von 382** Zeilen,
- 324 der 473 divergierten Detailzeilen sind zugleich `valid_for_analysis`.

**Nicht betroffen ist die Schwellenkennzahl:** unter allen divergierten Zeilen ist
`r2_gt_0_9` nirgends wahr, `r2_gt_0_9_rate_over_cells` ist also korrekt. Der Defekt trifft
ausschließlich die Median-Spalte — aber eine Zahl dieser Größenordnung in einer Phase-C-Datendatei
wird später gelesen und geglaubt, und genau deshalb wird sie jetzt repariert.

**Aufgabe:** Divergierte beziehungsweise nichtendliche Zeilen aus der Median-Bildung ausschließen.
Die Zählspalte muss danach zur Auswahl passen und so heißen, dass ihr Filter aus dem Namen hervorgeht
— `r2_valid_count` sagt heute nicht, was „valid" bedeutet, und das ist die eigentliche Ursache des
Fehlers. Wenn die Umbenennung andere Dateien oder Tests berührt, ziehe sie mit.

**Was dabei nicht passieren darf:** Zeilen stillschweigend verschwinden lassen. Die Zahl der
ausgeschlossenen Zeilen muss in der Ausgabe stehen, so wie `diverged_or_nonfinite_count` es schon
tut. Ein Median über eine leere Auswahl ist `NaN` und keine Null.

**Zusatz, gleiche Stelle:** Das Projekt berichtet Verteilungen als **Quantile**, nicht als einzelne
Lagemaße (`CLAUDE.md`, stehende Regel seit WP-A7). Ergänze neben dem Median die Quantile 0, 0,25,
0,75 und 1 über dieselbe bereinigte Auswahl. Die Schwelle bleibt bei 0,9 und wird **nicht**
angefasst — sie ist die Literaturkennzahl.

## 2. Das Abnahmekriterium 1 war falsch formuliert — meine Schuld, nicht deine

Du hast zu Recht `blocked` gemeldet: Bit-Identität der WP-N6-Ausgaben ist unerreichbar, weil diese
Dateien Laufzeitspalten führen. Das Kriterium lautet ab jetzt:

> Ein WP-N6-Lauf mit der alten Konfiguration ist identisch in **allen berichteten Größen**.
> `summary.csv` und `trajectory_check.csv` sind byte-identisch. In `details.csv` und `costs.csv`
> dürfen ausschließlich abweichen: die Laufzeitspalten, und `r2` in Zeilen mit
> `integration_status == "diverged"`. Dass **keine** berichtete Größe kippt, ist zu zeigen —
> mindestens `r2_gt_0_9`, die Strukturtreffer-Spalten, die Termzahlen, `fit_status` und
> `integration_status`.

Das ist bereits nachgemessen worden und trifft zu: `r2` weicht in 109 von 2.520 Zeilen ab, alle 109
mit `integration_status = diverged`, und keine berichtete Größe kippt. **Deine Aufgabe ist, diesen
Nachweis als prüfbaren Schritt zu verankern**, damit er beim nächsten Lauf nicht wieder von Hand
geführt werden muss: die vorhandene Prüfroutine `check-wpn6-bitidentical` soll genau dieses
Kriterium umsetzen statt roher Byte-Gleichheit, mit benannten Ausnahmen und einer Fehlermeldung, die
sagt, **welche** Größe gekippt ist, wenn eine kippt.

## Tests

Für beide Punkte: Fixtures **aus echten Records ableiten**, nie erfinden — Protokollregel seit
`221a3a7`. Die Pilot-Records liegen weiterhin unter `outputs/phase_c_p9_pilot_records/`, die
SINDy-Detailzeilen unter `analysis/data/paper1_phaseC_v1/phasec_sindy_baseline/details.csv`.

Mindestens zu testen: dass eine divergierte Zeile mit endlichem, absurdem R² **nicht** in den Median
eingeht; dass die Ausschlusszahl berichtet wird; dass ein Median über eine leere Auswahl `NaN` ergibt
und nicht 0; und dass die WP-N6-Prüfung anschlägt, wenn eine berichtete Größe kippt, aber nicht,
wenn nur eine Laufzeitspalte abweicht.

## Abnahme

1. Keine `r2`-Kennzahl in `summary.csv` liegt mehr außerhalb dessen, was ein R² annehmen kann, ohne
   dass die zugehörige Zeile das ausdrücklich ausweist.
2. Die Zähl- und die Auswahlspalte passen zueinander, und der Filter geht aus dem Namen hervor.
3. Quantile liegen neben dem Median.
4. `r2_gt_0_9_rate_over_cells` ist **unverändert** gegenüber der eingecheckten Fassung — das ist die
   Kontrolle dafür, dass die Reparatur nur den Median betrifft. Zeige das.
5. `check-wpn6-bitidentical` setzt das neue Kriterium um und läuft grün.
6. Alle Python-Tests grün.

## Verboten

- Keine Änderung an `run_wp_n6_sindy_baseline.py` oder an den WP-N6-Ausgaben.
- Keine Änderung der Schwelle 0,9 und keine neue Pruning-Regel.
- Keine Auswahl einer SINDy-Konfiguration.
- Nichts, was den laufenden Kampagnenlauf berührt.
- Keine neue Planungsdatei. Report nach `codex/reports/REPORT_WP_C4a2.md`.

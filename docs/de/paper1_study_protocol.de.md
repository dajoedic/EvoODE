# Paper 1 - Studienprotokoll

Deutsche Lesefassung von `docs/paper1_study_protocol.md`.

Dieses Dokument ist das eigenständige Protokoll für Paper 1. Es dupliziert
bewusst Teile der Konfiguration aus `CLAUDE.md` (Systemliste, Hyperparameter,
Variantendefinitionen), damit es als selbstständiges Supplement dienen kann.
Wenn sich eine Konfiguration ändert, müssen dieses Dokument und `CLAUDE.md`
manuell synchron gehalten werden.

Jedes Ergebnis, das im Paper erscheint, muss auf eine hier definierte Hypothese,
ein hier definiertes Experiment und eine hier definierte Metrik zurückführbar sein.

Wenn ein Ergebnis nicht rückführbar ist, darf es nicht ins Paper.

---

## 0. Kernziel

Paper 1 handelt nicht davon, das beste ODE-Discovery-System zu bauen.

Das Paper untersucht:

> Staged growth als Mechanismus zur kontrollierten Komplexitätserhöhung in
> datengetriebener ODE-Discovery.

Der Beitrag ist ein **Designprinzip und seine empirische Validierung**, kein
State-of-the-art-Benchmarkresultat.

---

## 1. Kernclaims

### Hauptclaim

Gestufte Komplexitätsfreigabe mit stage-local stopping criteria verbessert
complexity efficiency, indem Stage-Overshoot und verschwendete Suchlevels
reduziert werden, ohne Recovery-Qualität zu opfern.

Im Protokoll bezeichnet **complexity efficiency** das gemeinsame Verhalten von
`stage_overshoot` und `wasted_levels`. Kontrollierte Komplexitätserhöhung
bedeutet niedrige Complexity-Efficiency-Kosten. Niedrigere Werte bedeuten eine
effizientere Nutzung des Suchbudgets.

### Subclaims

**C1 - Overshoot-Reduktion**
Stage-local plateau detection reduziert Stage-Overshoot gegenüber global plateau
detection und flat growth.

**C2 - Recovery-Qualität**
EvoGrow-Varianten mit staged release erreichen exact structure recovery auf einem
Niveau, das mit flat search (EvoGrow v1) und GP baseline vergleichbar ist, während
sie niedrigere Complexity-Efficiency-Kosten haben.

**C3 - Usage-Policy-Effekt (sekundär)**
Die Usage Policy nach Stage-Unlock (`hard`, `soft`, `passive`) hat einen messbaren,
aber sekundären Effekt auf die Recovery Rate in komplexeren Systemen.

Jeder Claim ist spezifisch, testbar und falsifizierbar. Ein Claim ist falsifiziert,
wenn die behauptete Richtung über die Mehrheit der Systeme und Seeds nicht hält.

---

## 2. Hypothesen

Jede Hypothese mappt genau auf einen Claim und ein messbares Outcome.

**H1** (zu C1)
Für exakte Systeme mit `expected_stage >= 2` zeigt EvoGrow v2.2
(`stage_local` progression) niedrigeren mittleren `stage_overshoot` als
EvoGrow v2.1 (`global_plateau`) und EvoGrow v1 (`flat`).

- Outcome: `mean_stage_overshoot` pro `(variant, system)`
- Systeme: exakte Systeme mit `expected_stage >= 2`
- System 2 wird ausgeschlossen, weil Overshoot ohne mögliche Promotion nicht definiert ist

**H2** (zu C2)
Für exakte Systeme erreicht EvoGrow v2.2 kompetitive `exact_match_rate` zusammen
mit demonstrierbar niedrigeren Complexity-Efficiency-Kosten (H1, H3).

Kompetitiv heißt: `exact_match_rate` zeigt keine systematische Verschlechterung
gegenüber GP baseline über die Mehrheit der exakten Systeme. Der Claim ist die
Kombination aus vergleichbarer Recovery und reduzierter Complexity-Efficiency-Kosten.

- Outcome: `exact_match_rate`, gemeinsam mit `mean_stage_overshoot` und `mean_wasted_levels`
- Systeme: alle 8 exakten Systeme
- Falsifiziert, wenn v2.2 auf der Mehrheit der exakten Systeme schlechter als GP ist und keine Complexity-Efficiency-Verbesserung gegenüber v1 zeigt

**H3** (zu C2)
Für exakte Systeme mit `expected_stage >= 2` zeigt EvoGrow v2.2 niedrigere
`mean_wasted_levels` als EvoGrow v1 und v2.1.

- Outcome: `mean_wasted_levels`
- Vergleich nur zwischen EvoGrow-Varianten
- GP ist ausgeschlossen, weil `wasted_levels` für Methoden ohne Stage-Struktur nicht definiert ist

**H4** (zu C3, sekundär)
Unter den EvoGrow-v2.2-Varianten erreicht `hard` usage policy höhere
`exact_match_rate` als `passive` auf Systemen, die `stage >= 3` benötigen.
`soft` liegt erwartungsgemäß dazwischen.

- Outcome: `exact_match_rate`
- Varianten: `evogrow_v2_2_stage_local`, `evogrow_v2_2_passive`, `evogrow_v2_2_soft`
- Systeme: exakte Systeme mit `expected_stage >= 3`
- H4 ist sekundär; unklare Ergebnisse schwächen C3, aber nicht C1/C2

---

## 3. Experiment Scope

### 3.1 Systeme

Es gibt 10 Systeme, strikt getrennt in zwei Evaluationskategorien.

#### Exakte Systeme

| ID | Name | Dim | Expected stage | Rolle |
|----|------|-----|----------------|-------|
| 2 | Population growth | 1 | 1 | Sanity check |
| 3 | Logistic growth | 1 | 2 | Mechanismusvisualisierung + quantitativ |
| 11 | Critical slowing down | 1 | 4 | quantitativ, hohe Komplexität |
| 24 | Harmonic oscillator | 2 | 1 | Sanity check |
| 26 | Lotka-Volterra competition | 2 | 3 | quantitativ |
| 31 | SIR model | 2 | 3 | quantitativ |
| 54 | Lorenz (periodic) | 3 | 3 | quantitativ, high dim |
| 63 | SEIR model | 4 | 3 | quantitativ, high dim |

Systeme 2 und 24 sind nur Sanity Checks. Sie prüfen, dass triviale Strukturen
gefunden werden, werden aber aus H1, H3 und H4 ausgeschlossen.

System 3 ist das primäre Mechanismus-Visualisierungssystem: einfachster
nicht-trivialer Fall, exakte Struktur bekannt, Stage Progression interpretierbar.

#### Surrogate-Systeme

| ID | Name | Dim | Expected stage | Rolle |
|----|------|-----|----------------|-------|
| 23 | Overdamped pendulum | 1 | 5 | nur Surrogate-Analyse |
| 37 | Van der Pol oscillator | 2 | 4 | nur Surrogate-Analyse |

Surrogate-Systeme werden separat bewertet:

- erreichte Stage
- ob die Zieltermklasse in der entdeckten Struktur auftaucht
- Fitqualität (`mean_loss`)

`exact_support_match` darf für Surrogate-Systeme nicht berichtet werden.
Surrogate-Ergebnisse dürfen in Appendix oder Diskussion erscheinen, aber nicht
zur Stützung von H1-H4 verwendet werden.

### 3.2 Varianten

| Label | Slug | Verwendet in | Hinweise |
|-------|------|--------------|----------|
| EvoGrow v1 (flat) | `evogrow_v1` | H2, H3 | Flat baseline |
| EvoGrow v2.1 | `evogrow_v2_1` | H1, H2, H3 | Global plateau baseline |
| EvoGrow v2.2 progression | `evogrow_v2_2_stage_local` | H1, H2, H3, H4 | primäre Variante |
| EvoGrow v2.2 passive | `evogrow_v2_2_passive` | H4 | Usage-policy comparison |
| EvoGrow v2.2 soft | `evogrow_v2_2_soft` | H4 | Usage-policy comparison |
| GP baseline | `gp_baseline` | H2 | Recovery-Vergleich, aus H3 ausgeschlossen |

Minimal nötig für H1-H3:

```text
evogrow_v1
evogrow_v2_1
evogrow_v2_2_stage_local
gp_baseline
```

Die drei v2.2-Usage-Varianten sind nur für H4 erforderlich.
GP nimmt nicht an H1 oder H4 teil, weil GP keine Stage-Struktur hat.

### 3.3 Seeds

Fünf Seeds pro `(variant, system)`:

```julia
[42, 123, 7, 99, 17]
```

Multi-seed ist für alle quantitativen Claims Pflicht. Single-seed-Ergebnisse
sind nur für Mechanismusvisualisierung erlaubt.

Keine quantitative Aussage darf auf weniger als 3 gültigen Runs beruhen.
Eine Zelle mit `n_valid < 3` wird berichtet, aber aus Hypothesenevaluationen
ausgeschlossen.

### 3.4 Budgets

```text
EvoGrow: n_levels = 20
GP:      n_generations = 20
```

Budgets sind über Methoden hinweg auf 20 Iterationen gleichgesetzt. Das ist eine
Approximation: ein EvoGrow-Level und eine GP-Generation sind rechnerisch nicht
identisch. Diese Approximation muss im Paper explizit genannt werden.

Keine Budgetanpassung post-hoc. Wenn eine Methode mehr Budget braucht, ist das
ein Ergebnis, kein Grund zum Re-run.

---

## 4. Metriken

### 4.1 Primäre Metriken

**`exact_match_rate`**

Anteil gültiger Runs in einer `(variant, system)`-Zelle, in denen die entdeckten
Termindizes exakt den Ground-Truth-Termindizes aller Gleichungen entsprechen.

- gültig: nur exakte Systeme
- nicht verwenden: Surrogate-Systeme
- Aggregation: Mittel über gültige Runs, `n_valid` mitberichten

**`mean_stage_overshoot`**

Mittel von `stage_overshoot = final_stage - expected_stage`.
Negative Werte bedeuten undershooting.

- gültig: EvoGrow-Varianten, exakte Systeme mit `expected_stage >= 2`
- nicht verwenden: GP, Systeme 2 und 24
- mit `std_stage_overshoot` berichten

**`mean_wasted_levels`**

Mittel der Levels, die in Stages oberhalb von `expected_stage` verbracht wurden.

- gültig: exakte Systeme mit `expected_stage >= 2`
- GP ausgeschlossen

### 4.2 Sekundäre Metriken

**`mean_loss`**

Mittlerer Simulation-MSE über gültige Runs. Dient zur Interpretation, nicht zum
primären Ranking.

**`mean_final_stage`**

Mittlere finale Stage über gültige EvoGrow-Runs. GP wird per Konvention als `-1`
kodiert und nicht als numerischer Mittelwert berichtet.

**`mean_elapsed_s`**

Mittlere Laufzeit in Sekunden. Nur Charakterisierung, kein primärer Claim.

**`mean_invalid_evals`**

Mittlere Anzahl NaN-/Failed-Simulation-Evaluierungen pro Run. Dient zur
Kontextualisierung von Suchstabilität, nicht als Ranking-Metrik.

### 4.3 Tertiäre Metriken

Nur explorativ:

- `total_loss_evals`
- Solver-Failure-Rate pro System

Diese dürfen nicht als Evidenz in Tabellen oder Figuren für Claims auftauchen.

### 4.4 Statistische Behandlung

Nur deskriptive Statistik. Keine Signifikanztests, keine p-Werte, keine
Konfidenzintervalle.

Pro `(variant, system)` berichten:

- `n_valid`
- Mittelwert und Standardabweichung

Bei `n_valid = 1`: Einzelwert berichten, `n=1` markieren, nicht vergleichen.
Bei `n_valid = 0`: als `-` berichten, aus Vergleichen ausschließen.

Claims werden durch konsistente Richtungen über mehrere Systeme und Seeds
gestützt, nicht durch einzelne Zellen.

---

## 5. Success- und Failure-Semantik

### Run-level

| Wert | Bedeutung |
|------|-----------|
| `queued` | noch nicht gestartet |
| `running` | gestartet; bei Prozessabbruch später `interrupted` |
| `finished` | ohne Exception abgeschlossen |
| `failed` | Exception vom Runner gefangen |
| `interrupted` | nur vom Aggregator abgeleitet |

`success=true` genau dann, wenn ein Run abgeschlossen ist, finite Loss verfügbar
ist und Result/Metrics erfolgreich geschrieben wurden.

`success` ist nur ein technisches Urteil. Es bedeutet nicht, dass die Struktur
korrekt oder wissenschaftlich sinnvoll ist.

`failure_reason` ist kontrolliert:

- `exception`
- `all_invalid`
- `write_failure`
- `unknown`

### Analysis-level Exclusions

Ein Run wird aus Metrikberechnung ausgeschlossen, wenn `loss` NaN ist. Alle
anderen gültigen Runs bleiben drin, unabhängig von Loss-Höhe.

Keine Runs wegen "Loss zu hoch" ausschließen. Hoher Loss ist ein wissenschaftliches
Ergebnis, kein Ausschlussgrund.

Failed Runs werden nicht versteckt. Tabellen berichten `n_valid` und `n_seeds`.

---

## 6. Erlaubte Evidenz

### Tabellen

**Table 1 - Main results (exact systems)**

- Zweck: H2 stützen
- Rows: Varianten in fixer Reihenfolge
- Columns: exakte Systeme nach `system_id`
- Cell: `exact_match_rate` und `mean_loss`
- Footnote: `n_valid`
- Quelle: `aggregate_by_variant_system.csv`

**Table 2 - Stage overshoot summary**

- Zweck: H1 und H3 stützen
- Rows: nur EvoGrow-Varianten
- Columns: exakte Systeme mit `expected_stage >= 2`
- Cell: `mean_stage_overshoot` und `mean_wasted_levels`
- Quelle: `aggregate_by_variant_system.csv`

Das sind die einzigen zwei Tabellen im Main Paper. Weitere Tabellen gehören ins
Supplement.

### Figuren

**Figure 1 - Exact match rate**

- Zweck: visuelle Zusammenfassung von H2
- Systeme: alle 8 exakten Systeme
- Varianten: alle 6
- y-Achse: `exact_match_rate`
- Skript: `scripts/plot/plot_exact_match_rates.py`

**Figure 2 - Stage overshoot**

- Zweck: H1 visualisieren
- Systeme: exakte Systeme mit `expected_stage >= 2`
- Varianten: nur EvoGrow
- y-Achse: `mean_stage_overshoot`
- Skript: `scripts/plot/plot_stage_overshoot.py`

**Figure 3 - Stage progression trace für System 3**

Qualitative Mechanismusillustration. Sie zeigt, wie sich stage-local und global
plateau detection im einfachsten nicht-trivialen System unterscheiden.

- Varianten: `evogrow_v1`, `evogrow_v2_1`, `evogrow_v2_2_stage_local`
- Seed: 42
- Single representative run
- Nicht als quantitative Evidenz interpretieren

Harte Figure-Regeln:

- maximal 3 Main-Paper-Figures
- jede Figure muss durch ein Skript in `analysis/scripts/plot/` erzeugt werden
- keine manuell zusammengesetzten Figures
- keine Surrogate-Ergebnisse als Strukturkorrektheits-Evidenz

---

## 7. Rolle der Generalization Study

`generalization_study.jl` ist **auxiliary evidence**, nicht Teil des Hauptbeitrags.

Erlaubter Claim:

> Eine von EvoGrow auf einem Parametersatz entdeckte Struktur kann auf ungesehene
> Parametersätze derselben ODE-Familie mit niedrigem Loss refittet werden, wenn
> die Struktur exakt ist.

Nicht erlaubt:

- EvoGrow generalisiert besser als GP oder SINDy
- entdeckte Strukturen sind out-of-distribution robust
- Generalization Performance ersetzt `exact_support_match`
- Loss unter einem Threshold impliziert strukturelle Korrektheit

Runs ohne `exact_support_match = true` werden aus der Generalization-Analyse
ausgeschlossen. Generalisierung ist nur sinnvoll interpretierbar, wenn die
entdeckte Struktur korrekt ist.

Output: eine Supplementary Table mit:

- `System`
- `n_exact_runs`
- `mean_refit_loss`
- `mean_fresh_loss`

Die Tabelle wird im Supplement platziert und im Discussion-Abschnitt mit genau
einem interpretierenden Satz referenziert.

---

## 8. Ausschlussregeln

Nicht Teil von Paper 1:

Algorithmisch:

- Pretuning als eigenständiger Beitrag
- Optimierungstricks, die nur Runtime verändern

Claim-Typen:

- Runtime Efficiency als Hauptclaim
- Large-scale Benchmark Claims
- Signifikanzclaims

Systeme:

- Surrogate-Systeme in Strukturkorrektheitsmetriken
- Systeme 2 und 24 in H1/H3/H4

Methoden:

- GP in Stage-Overshoot- oder Stage-Progression-Metriken
- SINDy-Vergleich, weil nicht implementiert/reproduziert

Experimente:

- Noise robustness
- Sampling density
- Dimensionality scaling
- Post-hoc-Experimente nach Ergebnisinspektion

Analyse:

- cherry-picked Seeds oder Runs
- Failed Runs ausschließen, ohne sie zu berichten
- Ergebnisse aus manuell editierten CSVs

---

## 9. Experimentelle Phasen

### Phase A - `paper1_phaseA_v1`

Status: primäre Evidenzquelle für Paper 1.

Scope: 10 Systeme x 6 Varianten x 5 Seeds = 300 Runs.

Rolle: erzeugt alle Main-Paper-Evidenzen für H1-H4.

Klassifikation: vordefiniertes, eingefrorenes Evaluationsprotokoll. Systeme,
Varianten, Seeds, Hyperparameter und Metriken wurden festgelegt, bevor aggregierte
Ergebnisse inspiziert wurden.

Phase A ist die einzige primäre Evidenzquelle für dieses Paper. Ergebnisse aus
Phase A sind final, sobald alle 300 Runs abgeschlossen sind.

Wenn einzelne Zellen nach Phase A `n_valid = 0` haben, kann eine gezielte Phase B
für genau diese Zellen gestartet werden.

### Phase B - gezielte Re-runs

Trigger: Zellen mit `n_valid = 0` nach Phase A.
Scope: nur betroffene `(variant, system, seed)`-Tripel.
Konfiguration: identisch zu Phase A.
Status: noch nicht gestartet.

### Phasen C und D

Nicht für Paper 1 definiert. Alles Weitere gehört zu einer anderen Forschungsfrage
oder einem Folgepaper.

---

## 10. Minimaler Ausführungsplan

1. Phase A abschließen: alle 300 Runs `finished` oder `failed`; dann `julia experiments/aggregate.jl paper1_phaseA_v1`.
2. Aggregieren: `python scripts/aggregate/aggregate_run_registry.py --config configs/paper1_phaseA_v1.json`.
3. Primäre Metrikanalyse: H1, H2, H3 direkt aus der Aggregate-CSV bewerten.
4. Conclusions einfrieren: kurzes internes Memo, welche Hypothesen gestützt, unklar oder falsifiziert sind.
5. Figures und Tables erzeugen: die drei Analyse-Skripte laufen lassen und Outputs gegen CSV prüfen.
6. Generalization Study auswerten: nur exakte Runs, Refit vs. Fresh Loss.
7. Finale Validierung: jedes Paper-Ergebnis muss auf Hypothese, Experiment und Metrik zurückführbar sein.

Freeze condition:

Das experimentelle Setup gilt als eingefroren, wenn Phase A vollständig ist und
Step 3 ausgeführt wurde. Danach keine neuen Experimente für Paper 1.

---

## 11. Offene Fragen vor Step 4

**Phase-B-Trigger:** Mindest-`n_valid` definieren, unterhalb dessen eine Zelle
Phase B auslöst. Vorschlag: `n_valid < 3`. Muss vor Abschluss von Step 2
bestätigt werden.


# CURRENT TASK: WP-P2.2b — Korrekturen an der Screening-Variante vor dem Vergleichslauf

**Language: Julia**

## Context

WP-P2.2 ist umgesetzt (`07aee5e`). Der Kern stimmt: finaler Refit auf vollem Budget vorhanden,
Stopplogik und Promotion arbeiten auf dem simulierten Loss, der Incumbent wird immer mitgezogen,
ungültige Screening-Fälle werden explizit markiert und gezählt, `pretune_parameters` bleibt
verhaltensgleich, und `evogrow.jl`, `evogrow_v3.jl`, `discover.jl` sowie `stopping.jl` sind
unangetastet.

Das Review hat drei Punkte gefunden, die vor einem Vergleichslauf behoben werden müssen, plus
vier kleinere.

## Required Content

### 1. Feldkollision bei `screening_budgets_active` (blockierend)

`EvoGrowScreening` gibt im Meta `screening_budgets_active = true` fest zurück. Dieses Feld wurde in
WP-P1b mit einer **anderen** Bedeutung eingeführt: „die reduzierten Solver-Budgets aus WP-P1 sind
aktiv" (`strategy.screening_optimizer !== nothing`). Der Regression-Record liest es aus dem Meta.

Folge: In `history.jsonl` lässt sich künftig nicht mehr unterscheiden, ob ein Record mit reduzierten
Solver-Budgets oder mit ableitungsbasiertem Screening gelaufen ist — beide melden `true`. Das ist
dieselbe Klasse von Defekt wie in WP-P1b (falsch etikettierte Records), nur unter anderem Namen.

Verschärfend: der Runner-Konstruktor der neuen Variante nimmt `screening_optimizer` entgegen und
verwirft ihn. Die Variante nutzt die Solver-Screening-Budgets also gar nicht — der korrekte Wert
für `screening_budgets_active` wäre `false`.

Zu tun:
- `screening_budgets_active` behält seine ursprüngliche Bedeutung und muss für diese Variante
  wahrheitsgemäß gesetzt werden.
- Ob die Variante ableitungsbasiertes Screening verwendet, gehört in ein **eigenes**, klar
  benanntes Feld, das ebenfalls in den Record wandert.
- Entscheide und dokumentiere, ob `EvoGrowScreening` die Solver-Screening-Budgets zusätzlich
  unterstützen soll (analog zu `EvoGrow`/`EvoGrowV3`). Falls ja: durchreichen und wahrheitsgemäß
  melden. Falls nein: der Runner-Konstruktor darf das Argument nicht stillschweigend
  entgegennehmen und verwerfen.

### 2. Polish-Budget-Erschöpfung wird mit dem falschen Zähler gemessen (blockierend)

Die Erkennung nutzt `optimizer_limit_hits > 0`. Dieser Zähler wird bei **jedem** Nicht-Success-
Retcode erhöht, also auch bei echten Konvergenzfehlern. Belegt am Benchmark-Lauf System 3:
`optimizer_failure_hits = 95` bei 210 Fits, `optimizer_iteration_limit_hits = 0`. Die Erkennung
würde also nahezu durchgängig „Budget erschöpft" melden, unabhängig vom tatsächlichen Budget.

Das ist genau die Kennzahl, die laut WP-P2.2 entscheidet, ob die Losses überhaupt mit dem
Simulationspfad vergleichbar sind. Sie muss auf den Zähler umgestellt werden, der das
Iterationslimit abbildet (`ReturnCode.MaxIters`). Echte Konvergenzfehler sind getrennt zu zählen
und getrennt zu berichten.

### 3. Die Rangübereinstimmung kann ihre Frage nicht beantworten (blockierend)

Spearman's rho wird ausschließlich über die **ausgewählten** Kandidaten berechnet. Diese Menge ist
per Konstruktion auf gute Screening-Scores eingeschränkt. Der Wert misst damit die Übereinstimmung
unter den Überlebenden — nicht das, wofür die Kennzahl gedacht war: **ob die Vorauswahl gute
Kandidaten verwirft.** Genau das ist das zentrale Methodenrisiko aus Abschnitt 6 der Design-Notiz.
So wie gebaut, könnte der Vergleichslauf durchlaufen und die Frage bliebe unbeantwortet.

Zu tun: eine Stichprobe **abgelehnter** Kandidaten muss ebenfalls poliert und simuliert werden,
damit messbar wird, wie oft ein verworfener Kandidat einen besseren simulierten Loss erreicht
hätte als der beste ausgewählte. Zahl der Stichproben pro Level konfigurierbar, Default klein
(Richtwert 2), Kosten im Kostenmodell entsprechend gering. Berichte pro Lauf, wie oft ein
abgelehnter Kandidat den besten ausgewählten geschlagen hätte.

Die Stichprobe darf die Suche **nicht** beeinflussen: abgelehnte Kandidaten werden nur gemessen,
nie in die Population übernommen. Andernfalls wäre es keine Diagnose mehr, sondern ein anderer
Algorithmus.

### 4. Population schrumpft still auf `screen_k`

`pop` wird aus `polished` gebildet, und `polished` hat höchstens `screen_k` Einträge. Mit dem
Default `screen_k = pop_size` unauffällig — bei jedem `screen_k < pop_size` kollabiert die
Population dauerhaft auf `screen_k`, und `pop_size` hat keine Wirkung mehr. Entweder absichern
oder die Population wieder auffüllen; stillschweigendes Schrumpfen ist nicht akzeptabel.

### 5. Struct-Defaults weichen von allen anderen Varianten ab

`EvoGrowScreening` hat `usage = StageUsagePolicy(mode = :soft)` als Default. `EvoGrow` und
`EvoGrowV3` verwenden den Struct-Default, und alle drei Varianten im Regression-Runner setzen
`:hard`. Ein abweichender Default ist eine Falle für andere Aufrufer (Benchmarks, Debug-Skripte).
Angleichen oder im Docstring ausdrücklich begründen.

### 6. Finaler Refit fehlt in den Kostensummen

Der abschließende Refit auf vollem Budget wird nicht über die Fit-Statistik verbucht;
`total_ode_solves` und `total_simulation_time_s` enthalten ihn nicht. `final_refit_time_s` wird
separat gemeldet, was in Ordnung ist — aber jeder Laufzeitvergleich muss ihn addieren. Entweder
mitzählen oder im Docstring unmissverständlich festhalten, dass die Summen ihn ausschließen.

### 7. Abweichendes Selektionsverhalten dokumentieren

Wird ein Elternteil durch das Nachpolieren schlechter, behält die Variante den vorherigen Wert.
`EvoGrow` kennt diesen Schutz nicht — dort überschreibt `_evaluate!` in place, auch nach unten.
Dadurch ist die Folge der besten Objectives hier monoton, bei `EvoGrow` nicht. Das wirkt sich auf
Plateau-Erkennung und damit auf Promotion aus. Die Abweichung ist vertretbar, muss aber im
Docstring als bewusste Entscheidung benannt werden, weil sie stromabwärts die Stopplogik berührt.

Ebenfalls festhalten: `vis_history` wird angelegt und zurückgegeben, aber nie gefüllt.

## Verification

Nur billige Zellen. **Kein** Volllauf, **nicht** System 26, 31 oder 63.

1. Der bestehende Simulationspfad bleibt bit-identisch zu Baseline v0: System 11, alle drei Seeds,
   v2.2 **und** v3 (Loss, `final_stage`, `pruned_match`).
2. Die neue Variante läuft auf System 3 und System 11 durch.
3. Auf System 11 (`-u1^3`, exakt darstellbar): findet die Variante die korrekte Struktur?
4. Berichte mit Zahlen: Laufzeit neue Variante vs. Simulationspfad auf denselben Zellen, Anteil
   erschöpfter Polish-Budgets nach dem **korrigierten** Zähler, Rangübereinstimmung, und wie oft
   ein abgelehnter Kandidat den besten ausgewählten geschlagen hätte.

Der letzte Punkt aus WP-P2.2 wurde nicht berichtet. Diesmal sind die gemessenen Zahlen Teil des
Deliverables, nicht „läuft durch".

## Constraints

- `evogrow.jl`, `evogrow_v3.jl`, `gp.jl`, `discover.jl`, `stopping.jl` bleiben unangetastet.
- Der bestehende Simulationspfad bleibt verhaltensgleich.
- Plateau, Stopplogik und Promotion laufen ausschließlich auf simuliertem Loss.
- Die Diagnose-Stichprobe abgelehnter Kandidaten darf die Suche nicht beeinflussen.
- Bestehende Record-Felder, Metrikdefinitionen und Baseline v0 bleiben unangetastet.
- Level-Budget der Regression-Suite bleibt bei 30.
- Keine neuen Abhängigkeiten.

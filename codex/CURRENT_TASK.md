# CURRENT TASK: WP-v3.4 — Pro-Gleichungs-Promotionsregel (EvoGrowV3)

**Language: Julia**

## Context

WP-v3.3 hat die gleichungs-bewusste Child-Generation geliefert
(`src/structure/evogrow_v3_childgen.jl`), die aber unter Lockstep ein bewiesenes No-Op ist: Solange
alle `eq_stages` gleich sind, delegiert sie an den v2.2-Pfad. WP-v3.4 ist der Schritt, der die
Stufen erst **divergieren** laesst und damit den v3-Mechanismus scharf schaltet.

Motivation aus WP-T2 (System 26): der Referenzpfad findet Gleichung 1 exakt, laesst Gleichung 2
falsch, und der **globale** Plateau-Mechanismus eskaliert trotzdem beide bis Stage 5 (8 verschwendete
Level, ~25 % der Integrationen). EvoGrow v3 ersetzt die globale Promotion durch eine
**pro-gleichungs-lokale**: jede Gleichung steigt nur, wenn ihr eigenes Residuum stagniert.

Umzusetzen ist die Designnotiz `docs/evogrow_v3_design.md`, Abschnitte 3 (Signal), 4 (Promotionsregel)
und 5 (globale Termination). Der aktuelle `EvoGrowV3` (`src/structure/evogrow_v3.jl`) traegt bereits
den Pro-Gleichungs-State (`eq_stages`, `eq_levels_in_stage`, `eq_plateau_histories`,
`eq_stage_histories`), promotet ihn aber synchron ueber `_lockstep_stage_progression_decision` +
`_apply_lockstep_stage_update!`. Diese Lockstep-Promotion wird durch die Pro-Gleichungs-Logik ersetzt.

**Wichtiger Verhaltenshinweis (kein No-Op, anders als WP-v3.3):** v3.4 wechselt das Plateau-Signal
von `best.objective` auf das Ableitungsresiduum `r_k`. Das aendert das Verhalten **auch auf skalaren
Systemen** (dim = 1, eine Gleichung), weil dort weiterhin ein anderes Signal plateaut. Bit-Identitaet
zu v2.2/Baseline v1 ist daher **nicht** das Pruefkriterium. Die Verifikation ist deterministische
Unit-Test-Logik plus ein billiger Lauf-Smoke, **nicht** ein Baseline-Vergleich (der braucht den
externen langen Lauf, siehe unten).

## Goal

`EvoGrowV3` promotet jede Gleichung unabhaengig anhand ihres eigenen Ableitungsresiduums `r_k`, sodass
Gleichungen auf verschiedenen Stufen stehen koennen. Die globale Termination folgt den drei
v3-Bedingungen (§5). Die gleichungs-bewusste Child-Generation aus WP-v3.3 wird dadurch im echten Lauf
erstmals wirksam. `EvoGrow`/v2.2 und die Child-Generation-Logik selbst bleiben unveraendert.

## Files

- **Aendern:** `src/structure/evogrow_v3.jl` (Promotions-/Terminationsblock im Level-Loop,
  Signal-Aufzeichnung, Rueckgabe-Metadaten).
- **Ergaenzen erlaubt:** eine neue Datei im Structure-Layer (z. B. `src/structure/evogrow_v3_promote.jl`)
  fuer das Residuum `r_k`, die Pro-Gleichungs-Promotionsentscheidung und die Termination; in
  `src/EvoODE.jl` **vor** `evogrow_v3.jl` einbinden.
- **Nicht anfassen (Verhalten):** `src/structure/evogrow.jl`, `src/structure/evogrow_v3_childgen.jl`,
  `src/structure/evogrow_screening.jl`, die Basis, `EvoGrow`/v2.2, die Regressions-Konfiguration.
- **Neue Tests:** unter `test/` (bestehendes Schema).

## Required Content

### 1. Pro-Gleichungs-Signal `r_k` (Designnotiz §3)

Fuer Gleichung `k` ist das Fortschrittssignal das **Ableitungsresiduum** auf der **beobachteten**
Trajektorie:

    r_k = mean_t ( dxk_dt_fd(t) - f_k(x_obs(t); params) )^2

- `dxk_dt_fd` ist die Finite-Differenzen-Schaetzung der Ableitung der beobachteten Trajektorie,
  konsistent mit der bereits in `src/optimize/pretune.jl` genutzten Ableitungsschaetzung. Diese
  Schaetzung soll wiederverwendet werden, nicht neu erfunden.
- `f_k(x_obs(t); params)` ist die `k`-te Komponente der gebauten RHS (`build_rhs(best.structure, basis)`),
  ausgewertet an den **beobachteten** Zustaenden `x_obs(t)` mit den Parametern des besten Individuums —
  **nicht** an der simulierten Trajektorie. Es ist keine ODE-Integration noetig.
- Der Mittelwert laeuft ueber alle Zeitpunkte.

`r_k` wird **einmal pro Level** auf dem besten Individuum berechnet (Designnotiz §9, offene Frage 1:
Level-Ende genuegt fuer Plateau-Detektion).

**Fallback (§3):** Falls die FD-Ableitungsschaetzung numerisch scheitert (nicht-finite Werte), auf das
pro-Dimension-**Trajektorienresiduum** ausweichen:

    r_k = mean_t ( xk_sim(t) - xk_obs(t) )^2

Da die FD-Schaetzung einmal auf der beobachteten Trajektorie erfolgt, ist der Fallback lauf-global.
Ein Boolean `derivative_residual_fallback` wird in den Rueckgabe-Metadaten gesetzt, damit die
Auswertung Ableitungs- von Trajektorien-getriebener Promotion unterscheiden kann.

### 2. Pro-Gleichungs-Promotionsregel (Designnotiz §4)

Am Ende jedes Levels prueft **jede** Gleichung ihre eigene Promotionsbedingung unabhaengig. Mehrere
Gleichungen koennen im selben Level promoten; nicht qualifizierte bleiben auf ihrer Stufe.

Gleichung `k` promotet von Stufe `s` auf `s + 1` **genau dann, wenn alle drei** gelten:

1. **Mindestbudget:** `eq_levels_in_stage[k] >= effective_min_per_stage`, mit
   `effective_min_per_stage = max(min_levels_per_stage, plateau_window + 1)`.
   `min_levels_per_stage` stammt aus `strategy.progression.min_levels_per_stage`, `plateau_window`
   aus `options.plateau_window`.
2. **Pro-Gleichungs-Plateau:** die letzten `plateau_window` Werte von `r_k` erfuellen
   `maximum(window) - minimum(window) < plateau_tol` (`options.plateau_tol`). Dasselbe absolute
   Plateau-Kriterium wie v2.2, aber pro Gleichung auf `r_k` statt global auf `best.objective`.
3. **Residuum ueber Ziel:** `r_k > loss_tol` (`options.loss_tol`). Ist `r_k` bereits nahe null,
   ist zusaetzliche Strukturkapazitaet unnoetig; die Gleichung promotet dann **nicht**, auch wenn
   Budget und Plateau erfuellt sind.

Zusaetzliche Grenzen: eine Gleichung, die bereits auf der maximalen Stufe des Basis (`_max_stage(basis)`)
steht, promotet nicht weiter.

**State-Update bei Promotion von Gleichung `k`:** `eq_stages[k] += 1`, `eq_levels_in_stage[k] = 0`,
`empty!(eq_plateau_histories[k])`. Der aggregierte `current_stage` bleibt als
`maximum(eq_stages)` definiert (fuer Logging, `_allowed_terms`-Abfragen und die aggregierten Metriken).

### 3. Globale Termination (Designnotiz §5)

Die harte Stopp-Semantik von v2.2 bleibt, nur die Stage-Erschoepfungsbedingung wird pro-gleichungs:

1. `global_loss < loss_tol`: harter Stopp, ausgewertet auf der **simulierten** Trajektorie (wie v2.2;
   nutze die bestehende `should_stop`-Logik / `options.loss_tol`, nicht `r_k`).
2. `total_levels >= max_levels`: harte Level-Obergrenze (`options.max_levels`), zusaetzlich zur
   `n_levels`-Schleifengrenze.
3. **Alle** Gleichungen auf maximaler Stufe **und alle** plateaut: keine Promotion mehr moeglich → Stopp.

Der Lauf laeuft weiter, solange mindestens eine Gleichung noch promoten oder sich auf ihrer Stufe noch
verbessern kann. Bedingung 3 ersetzt den v2.2-Pfad „keine weiteren Stufen verfuegbar". Die
`min_levels`-Untergrenze (`options.min_levels`) bleibt als Schutz vor zu fruehem Stopp erhalten.

### 4. Bookkeeping-Aenderungen im Level-Loop

- `_record_eq_stage_level!` (oder sein Ersatz) schreibt jetzt **`r_k[k]`** in `eq_plateau_histories[k]`,
  **nicht** mehr `best.objective`. `eq_levels_in_stage[k]` inkrementiert wie bisher pro Level;
  `eq_stage_histories[k]` protokolliert weiterhin die Stufe pro Level.
- Der bisherige globale `stage_histories[current_stage]`-Verlauf (auf `best.objective`) darf fuer die
  aggregierte Visualisierung erhalten bleiben; er treibt die Promotion nicht mehr.
- Der Aufruf von `_lockstep_stage_progression_decision` + `_apply_lockstep_stage_update!` wird durch
  die Pro-Gleichungs-Entscheidung (Punkt 2) und die globale Termination (Punkt 3) ersetzt.
- Nach der Promotionsphase wird `current_stage = maximum(eq_stages)` neu gesetzt; die
  `_push_vis_snapshot!`-Aufrufe mit `stage_transition = true` sollen feuern, wenn **irgendeine**
  Gleichung in diesem Level promotet hat (fuer die vorhandene Live-Beobachtbarkeit).

### 5. Minimale Beobachtbarkeits-Metadaten (Teil von v3.4)

In die Rueckgabe-`meta` aufnehmen (die restlichen §8-Metriken kommen in WP-v3.5):

- `eq_residual_log :: Vector{Vector{Float64}}` — `r_k` pro Gleichung und Level.
- `eq_promotion_levels :: Vector{Vector{Int}}` — Levelindizes, in denen jede Gleichung promotet hat.
- `derivative_residual_fallback :: Bool` — ob der Trajektorien-Fallback aus Punkt 1 aktiv war.

`eq_final_stages` und `eq_stage_histories` sind bereits vorhanden und bleiben. `final_stage` bleibt
`maximum(eq_stages)`. Die expected-stage-abhaengigen Felder (`eq_overshoot`, `eq_wasted_levels`)
gehoeren zu **WP-v3.5** und sind hier **nicht** umzusetzen.

### 6. Was unveraendert bleibt

Child-Generation-Logik (`evogrow_v3_childgen.jl`), `EvoGrow`/v2.2, die Basis, die
Kosten-Instrumentierung (Fits, Solves, Retcodes), das RNG-Seeding und alle bestehenden
Metadaten-Felder ausser den in Punkt 4/5 genannten.

## Verification

**Keinen langen Lauf und nicht die Regressions-Baseline starten.** Die Baseline v1 laeuft extern und
liefert spaeter die Referenz fuer die eigentliche Validierung (WP-v3.6). Codex fuehrt nur die folgenden
billigen, deterministischen Checks aus.

### A. Unit-Test: Promotionsentscheidung (Kern von §4)

Die Pro-Gleichungs-Promotionsentscheidung direkt mit **gebauten** `r_k`-Verlaeufen und State aufrufen
(kein Suchlauf), dim = 2. Faelle:

1. Gleichung 1 erfuellt alle drei Bedingungen (genug Budget, `r_1`-Fenster flach unter `plateau_tol`,
   `r_1 > loss_tol`), Gleichung 2 hat ein **nicht** flaches `r_2`-Fenster → **nur** Gleichung 1
   promotet, Gleichung 2 bleibt.
2. Gleichung 1 plateaut, aber `r_1 < loss_tol` (Bedingung 3 falsch) → Gleichung 1 promotet **nicht**.
3. Budget noch nicht erreicht (`eq_levels_in_stage[k] < effective_min_per_stage`) → keine Promotion,
   auch bei flachem Fenster.
4. Gleichung auf maximaler Stufe → keine Promotion.

### B. Unit-Test: Signal `r_k`

Auf einer kleinen konstruierten 2-D-Trajektorie und einer Struktur, die **eine** Gleichung exakt
trifft: `r_k` der getroffenen Gleichung ist nahe null, das der anderen deutlich groesser. Bestaetigt,
dass `r_k` pro Gleichung korrekt und auf den **beobachteten** Zustaenden ausgewertet wird.

### C. Skalar-Smoke (Sekunden)

`EvoGrowV3` end-to-end auf System 3 **und** 11 (dim = 1, wenige Sekunden). Bestaetigen, dass der Lauf
terminiert, eine gueltige Struktur liefert, und `eq_residual_log` / `eq_promotion_levels` gefuellt sind.
`final_stage` und `loss` protokollieren — sie duerfen von v2.2 **abweichen** (das Signal hat sich
geaendert); das ist erwartet und wird im Bericht notiert, **nicht** als Fehler gewertet.

### D. Optionaler Divergenz-Check nur, falls billig

Ein end-to-end-Nachweis divergierender Stufen auf einem gekoppelten System ist **nicht** verpflichtend
und darf **nicht** ueber ein teures System (26/31/63) laufen. Der deterministische Unit-Test A ist die
maszgebliche Evidenz, dass die Pro-Gleichungs-Promotion feuert.

### E. Abschlussbericht

Unit-Tests A und B bestanden (mit den geprueften Faellen), Skalar-Smoke C terminiert mit gefuellten
Pro-Gleichungs-Metadaten (Werte nennen), und Bestaetigung, dass `EvoGrow`/v2.2 und die
Child-Generation unveraendert sind. Zusaetzlich: den genauen Startbefehl fuer den spaeteren externen
Kopplungs-Validierungslauf **nicht** ausfuehren, aber im Bericht nennen, damit der Betreiber ihn
extern starten kann.

## Constraints

- Pro-Gleichungs-Promotion ersetzt die Lockstep-Promotion; `EvoGrow`/v2.2 und die Child-Generation
  bleiben unveraendert.
- Plateau-Signal ist `r_k` (Ableitungsresiduum, beobachtete Trajektorie), nicht `best.objective`.
- Kein neuer ODE-Solve fuer `r_k` im Normalpfad (nur RHS-Auswertung auf beobachteten Zustaenden);
  Integration nur im Fallback.
- Keine expected-stage-abhaengigen Metriken (gehoeren zu WP-v3.5).
- Keine neuen Abhaengigkeiten.
- Keinen langen Lauf und nicht die Regressions-Baseline ausfuehren; nur Unit-Tests A/B und der
  Sekunden-Smoke C auf skalaren Systemen sind erlaubt.

# CURRENT TASK: WP4 — Live Frame Rendering via Level Callback

## Goal

Frames sollen nicht mehr nach `discover()` in einem Batch gerendert werden,
sondern live nach jedem abgeschlossenen Level während der Suche.
So gehen keine Frames verloren, wenn der Prozess abbricht.

Zwei Dateien werden geändert:

1. `src/structure/evogrow.jl` — `level_callback`-Feld + Aufruf in `_push_vis_snapshot!`
2. `studies/visualization/animate_search.jl` — Callback-Closure + Post-hoc-Rendering entfernen

Keine anderen Dateien werden angefasst.

---

## Teil 1 — `src/structure/evogrow.jl`

### 1.1 Neues Feld in `EvoGrow`

Füge `level_callback` als letztes Feld in den `Base.@kwdef struct EvoGrow`-Block ein:

```julia
Base.@kwdef struct EvoGrow <: AbstractStructureSearch
    pop_size::Int = 20
    n_levels::Int = 5
    children_per_parent::Int = 2
    max_terms_per_eq::Int = 5
    λ::Float64 = 1e-3
    progression::StageProgressionPolicy = StageProgressionPolicy()
    usage::StageUsagePolicy = StageUsagePolicy()
    use_pretuning::Bool = true
    level_callback::Union{Nothing, Function} = nothing
end
```

### 1.2 Callback-Aufruf in `_push_vis_snapshot!`

Die lokale Closure `_push_vis_snapshot!` befindet sich ab Zeile 708.
Direkt nach dem `push!(vis_history, (...))` — also nach der schließenden `)` der
`push!`-Klammer, aber noch innerhalb der Closure — folgenden Block einfügen:

```julia
        if strategy.level_callback !== nothing
            strategy.level_callback(vis_history[end])
        end
```

Die Closure sieht danach so aus:

```julia
        function _push_vis_snapshot!(stage_trans, prev_s, new_s)
            push!(
                vis_history,
                (
                    level = level,
                    stage = level_stage_at_start,
                    candidates_structures = _vis_candidates_structures,
                    candidates_params = _vis_candidates_params,
                    candidates_loss = _vis_candidates_loss,
                    candidates_objective = _vis_candidates_objective,
                    best_structure = best.structure,
                    best_params = copy(best.params),
                    best_loss = best.loss,
                    best_objective = best.objective,
                    accepted_new_best = _vis_accepted_new_best,
                    stage_transition = stage_trans,
                    previous_stage = prev_s,
                    new_stage = new_s
                )
            )
            if strategy.level_callback !== nothing
                strategy.level_callback(vis_history[end])
            end
        end
```

Kein weiterer Eingriff in `evogrow.jl`.

---

## Teil 2 — `studies/visualization/animate_search.jl`

### 2.1 Callback-Zustand vor dem `discover()`-Aufruf

Direkt **vor** dem `discover(...)`-Aufruf (nach `basis, strategy, optimizer, loss_fn, options = make_demo_config(demo.dim)`)
folgende Variablen einfügen:

```julia
accumulated_candidates = Matrix{Float64}[]
frame_count = Ref(0)
n_skipped_live = Ref(0)
```

### 2.2 Callback-Closure

Direkt nach den drei Variablen die Closure definieren:

```julia
function on_level(snapshot)
    if CLEAR_ON_STAGE_TRANSITION && snapshot.stage_transition
        empty!(accumulated_candidates)
    end

    current_level_candidates = Matrix{Float64}[]
    limit = MAX_CANDIDATES_PER_LEVEL === nothing ?
        length(snapshot.candidates_structures) :
        min(MAX_CANDIDATES_PER_LEVEL, length(snapshot.candidates_structures))

    for i in 1:limit
        Yhat = _simulate_candidate(
            snapshot.candidates_structures[i],
            snapshot.candidates_params[i],
            basis,
            demo.traj,
        )
        if Yhat === nothing
            n_skipped_live[] += 1
        else
            push!(current_level_candidates, Yhat)
        end
    end

    frame_count[] += 1
    render_frame(
        frame_count[],
        snapshot,
        accumulated_candidates,
        current_level_candidates,
        demo.traj,
        basis;
        output_dir      = frames_dir,
        var_names       = demo.var_names,
        true_equations  = demo.true_equations,
        frame_width     = FRAME_WIDTH,
        frame_height    = FRAME_HEIGHT,
    )
    println("  Frame $(frame_count[]) - Level $(snapshot.level), Stage $(snapshot.stage), Loss $(@sprintf("%.3g", snapshot.best_loss))")

    append!(accumulated_candidates, current_level_candidates)
end
```

### 2.3 `level_callback` an `EvoGrow` übergeben

In `make_demo_config` wird `strategy` konstruiert. Diese Funktion kennt `on_level` nicht,
weil `on_level` erst danach definiert wird. Deshalb: `make_demo_config` **nicht** ändern.

Stattdessen nach dem Aufruf von `make_demo_config`:

```julia
basis, strategy, optimizer, loss_fn, options = make_demo_config(demo.dim)
```

Die lokale `strategy`-Variable durch eine neue ersetzen, die `level_callback` gesetzt hat:

```julia
strategy = EvoGrow(
    pop_size             = strategy.pop_size,
    n_levels             = strategy.n_levels,
    children_per_parent  = strategy.children_per_parent,
    max_terms_per_eq     = strategy.max_terms_per_eq,
    λ                    = strategy.λ,
    progression          = strategy.progression,
    usage                = strategy.usage,
    use_pretuning        = strategy.use_pretuning,
    level_callback       = on_level,
)
```

Diese Zeilen stehen **nach** der `on_level`-Closure und **vor** dem `discover(...)`-Aufruf.

### 2.4 `render_all_frames`-Block ersetzen

Den gesamten Block

```julia
println("Rendering frames to $frames_dir ...")
stats = render_all_frames(
    vis_history,
    demo.traj,
    basis;
    output_dir = frames_dir,
    var_names = demo.var_names,
    true_equations = demo.true_equations,
    frame_width = FRAME_WIDTH,
    frame_height = FRAME_HEIGHT,
    max_candidates_per_level = MAX_CANDIDATES_PER_LEVEL,
    clear_on_stage_transition = CLEAR_ON_STAGE_TRANSITION,
)
println("Rendered $(stats.n_frames) frames. Skipped simulations: $(stats.n_skipped_simulations)")
```

ersetzen durch:

```julia
println("Frames live gerendert: $(frame_count[]) Frames. Skipped simulations: $(n_skipped_live[])")
```

### 2.5 `summary.txt` anpassen

In der `summary.txt`-Schreibelogik die Felder `stats.n_frames` und `stats.n_skipped_simulations`
durch `frame_count[]` und `n_skipped_live[]` ersetzen:

```julia
println(io, "Levels rendered:       $(frame_count[])")
println(io, "Skipped simulations:   $(n_skipped_live[])")
```

---

## Reihenfolge im fertigen Skript

Nach den Änderungen sieht der Ablauf in `animate_search.jl` so aus:

```
1. Konstanten (DEMO_SYSTEM, RUN_ID, ...)
2. make_demo_system(...)
3. make_demo_config(...)  → basis, strategy (ohne callback), optimizer, loss_fn, options
4. accumulated_candidates, frame_count, n_skipped_live initialisieren
5. on_level-Closure definieren
6. strategy mit level_callback = on_level neu konstruieren
7. discover(...) — ruft on_level nach jedem Level auf, Frames werden live geschrieben
8. vis_history aus result.meta.structure.vis_history lesen (für Summary-Stats)
9. ffmpeg-Block (unverändert)
10. summary.txt schreiben (frame_count[], n_skipped_live[])
```

---

## Constraints

- `make_demo_config` darf nicht geändert werden.
- `search_animation.jl` wird nicht angefasst — `render_all_frames` bleibt erhalten.
- `render_frame` und `_simulate_candidate` werden unverändert aus `EvoODE` importiert.
- Der Callback darf keine Exception werfen — falls `render_frame` wirft, bricht `discover()` ab.
  Kein try/catch nötig, da Rendering-Fehler sichtbar sein sollen.
- `vis_history` in `result.meta.structure.vis_history` bleibt weiterhin befüllt
  (wird nur nicht mehr zum Rendern genutzt, aber für n_stages / n_transitions).

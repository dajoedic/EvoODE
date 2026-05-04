# CURRENT TASK: WP11 — CairoMakie-basierter Rebuild von `render_frame`

## Ziel

`src/plotting/search_animation.jl` wird auf CairoMakie umgebaut.
Nur `render_frame` und dessen Hilfsfunktionen werden geändert.
Alle anderen Funktionen (`structure_to_string`, `_simulate_candidate`,
`_format_elapsed`, `_stage_description`) bleiben **vollständig unverändert**.

Geänderte Dateien: **nur** `src/plotting/search_animation.jl`.

---

## Namespace-Regel (zwingend)

```julia
import CairoMakie as CM
```

Alle CairoMakie-Aufrufe werden mit `CM.`-Präfix geschrieben (`CM.Figure`,
`CM.Axis`, `CM.text!`, `CM.lines!`, `CM.poly!`, `CM.save`, etc.).
Kein `using CairoMakie`. Das verhindert Konflikte mit Plots.jl im Modul-Scope.

---

## Hilfsfunktionen

Die folgenden drei Hilfsfunktionen ersetzen die alten (`_frameless_panel!`,
`_format_equation`, `_render_eq_line!`).

### `_format_equation(eq)`

Unverändert übernehmen — Signatur und Body bleiben wie heute:

```julia
function _format_equation(eq::AbstractString)
    return replace(eq, "*" => " ")
end
```

### `_render_eq_line!(ax, eq, y, color, fontsize)`

Neu: nimmt eine CairoMakie-`Axis` statt einen Plots-`Subplot`.

```julia
function _render_eq_line!(ax::CM.Axis, eq::AbstractString, y::Float64, color, fontsize::Int)
    parts = split(eq, " = ", limit = 2)
    if length(parts) == 2
        CM.text!(ax, 0.05, y; text = strip(parts[1]),
            align = (:left, :center), fontsize = fontsize, color = color)
        CM.text!(ax, 0.40, y; text = "= " * strip(parts[2]),
            align = (:left, :center), fontsize = fontsize, color = color)
    else
        CM.text!(ax, 0.05, y; text = eq,
            align = (:left, :center), fontsize = fontsize, color = color)
    end
end
```

Die alte `_frameless_panel!` entfällt. Axis-Cleanup erfolgt direkt via
`CM.hidedecorations!` + `CM.hidespines!` (siehe unten).

---

## `render_frame` — Vollständige neue Implementierung

Signatur bleibt **unverändert**:

```julia
function render_frame(
    frame_idx::Int,
    snapshot::NamedTuple,
    accumulated_candidates::Vector{Matrix{Float64}},
    current_level_candidates::Vector{Matrix{Float64}},
    traj_truth::Trajectory,
    basis::AbstractBasis;
    output_dir::String,
    var_names::Union{Nothing, Vector{String}} = nothing,
    true_equations::Union{Nothing, String} = nothing,
    title::String = "EvoGrow Search",
    elapsed_s::Float64 = 0.0,
    frame_width::Int = 1920,
    frame_height::Int = 1080,
)::String
```

### Lokale Variablen

```julia
dim = size(traj_truth.x, 2)
t   = traj_truth.t
X   = traj_truth.x
```

### Figure und GridLayout

```julia
fig = CM.Figure(
    size            = (frame_width, frame_height),
    backgroundcolor = :white,
)

CM.rowsize!(fig.layout, 1, CM.Fixed(round(Int, frame_height * 0.08)))   # Header
CM.rowsize!(fig.layout, 3, CM.Fixed(round(Int, frame_height * 0.045)))  # Legende
CM.colsize!(fig.layout, 1, CM.Relative(0.28))                            # Info-Panel
```

---

### Header (`fig[1, 1:2]`)

```julia
ax_header = CM.Axis(fig[1, 1:2];
    backgroundcolor = :white,
    limits = ((0.0, 1.0), (0.0, 1.0)),
)
CM.hidedecorations!(ax_header)
CM.hidespines!(ax_header)

title_parts = split(title, " – ", limit = 2)
main_title  = title_parts[1]
sub_title   = length(title_parts) > 1 ? title_parts[2] : ""

CM.text!(ax_header, 0.02, 0.72;
    text = main_title, align = (:left, :center),
    fontsize = 26, color = CM.RGBf(0.10, 0.18, 0.36))
if !isempty(sub_title)
    CM.text!(ax_header, 0.02, 0.28;
        text = sub_title, align = (:left, :center),
        fontsize = 16, color = CM.RGBf(0.30, 0.38, 0.56))
end

# Vertikaler Trenner
CM.lines!(ax_header, [0.295, 0.295], [0.08, 0.92];
    color = CM.RGBf(0.80, 0.84, 0.90), linewidth = 1.0)

# Status-Zeile
stage_str   = snapshot.stage_transition ?
    "$(snapshot.previous_stage) → $(snapshot.new_stage)" :
    "$(snapshot.stage)"
loss_str    = @sprintf("%.6f", snapshot.best_loss)
n_terms     = length(snapshot.best_params)
time_str    = _format_elapsed(elapsed_s)
status_text = "Stage $stage_str     |     Level $(snapshot.level)     |     Loss $loss_str     |     Active terms $n_terms     |     Time $time_str"

CM.text!(ax_header, 0.31, 0.50;
    text = status_text, align = (:left, :center),
    fontsize = 13, color = CM.RGBf(0.05, 0.08, 0.20))
```

---

### Info-Panel (`fig[2, 1]`)

```julia
ax_info = CM.Axis(fig[2, 1];
    backgroundcolor = :white,
    limits = ((0.0, 1.0), (0.0, 1.0)),
)
CM.hidedecorations!(ax_info)
CM.hidespines!(ax_info)
```

#### Equations-Sektion

```julia
disc_str   = structure_to_string(
    snapshot.best_structure, basis, snapshot.best_params; var_names = var_names)
disc_lines = split(disc_str, "\n")
true_lines = true_equations !== nothing ? split(true_equations, "\n") : String[]

# eq_items: (text, color, fontsize, is_equation)
eq_items = Tuple{String, Any, Int, Bool}[]

if snapshot.stage_transition
    new_stage = snapshot.new_stage
    push!(eq_items, ("STAGE $new_stage UNLOCKED", :darkorange, 13, false))
    push!(eq_items, ("New terms: $(_stage_description(basis, new_stage, var_names))", :darkorange, 11, false))
    push!(eq_items, ("", :white, 10, false))   # spacer
end

push!(eq_items, ("DISCOVERED MODEL", CM.RGBf(0.00, 0.32, 0.80), 12, false))
for eq in disc_lines
    push!(eq_items, (_format_equation(eq), CM.RGBf(0.00, 0.32, 0.80), 11, true))
end

if !isempty(true_lines)
    push!(eq_items, ("", :white, 10, false))   # spacer
    push!(eq_items, ("GROUND TRUTH", :black, 12, false))
    for eq in true_lines
        push!(eq_items, (_format_equation(eq), CM.RGBf(0.05, 0.05, 0.05), 11, true))
    end
end

# Y-Positionen dynamisch (oben = 0.96, unten = 0.42)
n_eq      = length(eq_items)
y_top     = 0.96
y_bot     = 0.42
y_step    = (y_top - y_bot) / max(n_eq - 1, 1)

for (i, (text, color, fsize, is_eq)) in enumerate(eq_items)
    isempty(text) && continue
    y = y_top - (i - 1) * y_step
    if is_eq
        _render_eq_line!(ax_info, text, Float64(y), color, fsize)
    else
        CM.text!(ax_info, 0.05, y;
            text = text, align = (:left, :center),
            fontsize = fsize, color = color)
    end
end
```

#### Trennlinie

```julia
CM.lines!(ax_info, [0.04, 0.96], [0.40, 0.40];
    color = CM.RGBf(0.78, 0.82, 0.88), linewidth = 0.8)
```

#### Stage-Box (untere ~38% des Panels)

```julia
CM.poly!(ax_info,
    CM.Point2f[(0.04, 0.01), (0.96, 0.01), (0.96, 0.37), (0.04, 0.37)];
    color       = CM.RGBAf(0.94, 0.97, 1.00, 0.8),
    strokecolor = CM.RGBf(0.78, 0.82, 0.88),
    strokewidth = 0.8)

stage_desc = _stage_description(basis, snapshot.stage, var_names)
var_text   = var_names === nothing ? join(["u$i" for i in 1:dim], ", ") : join(var_names, ", ")
n_available = if basis isa StagedPolynomialBasis &&
                 snapshot.stage >= 1 &&
                 snapshot.stage <= length(basis.term_groups)
    length(vcat(basis.term_groups[1:snapshot.stage]...))
else
    basis_num_terms(basis)
end

CM.text!(ax_info, 0.07, 0.31;
    text = "Stage $(snapshot.stage) allows:", align = (:left, :center),
    fontsize = 11, color = :black)
CM.text!(ax_info, 0.19, 0.24;
    text = stage_desc, align = (:left, :center),
    fontsize = 10, color = CM.RGBf(0.00, 0.32, 0.80))
CM.text!(ax_info, 0.07, 0.16;
    text = "Variables:  $var_text", align = (:left, :center),
    fontsize = 10, color = :black)
CM.text!(ax_info, 0.07, 0.08;
    text = "Search space:  $n_available terms per equation", align = (:left, :center),
    fontsize = 10, color = :black)
```

---

### Trajektorien-Panels (`fig[2, 2]` als nested GridLayout)

```julia
plot_grid = CM.GridLayout(fig[2, 2])

Yhat_best = _simulate_candidate(snapshot.best_structure, snapshot.best_params, basis, traj_truth)

for k in 1:dim
    ax_k = CM.Axis(plot_grid[k, 1];
        backgroundcolor = :white,
        ylabel = var_names === nothing ? "u$k" : var_names[k],
    )

    y_lo  = minimum(X[:, k])
    y_hi  = maximum(X[:, k])
    pad   = max(0.3 * abs(y_hi - y_lo), 0.1)
    CM.ylims!(ax_k, y_lo - pad, y_hi + pad)

    if k < dim
        CM.hidexdecorations!(ax_k; grid = false)
    else
        ax_k.xlabel = "t"
    end

    # Search history (grey)
    for Yhat in accumulated_candidates
        CM.lines!(ax_k, t, Yhat[:, k]; color = (:gray, 0.18), linewidth = 0.5)
    end

    # Current level candidates (orange)
    for Yhat in current_level_candidates
        CM.lines!(ax_k, t, Yhat[:, k]; color = :darkorange, linewidth = 0.6)
    end

    # Ground truth (black)
    CM.lines!(ax_k, t, X[:, k]; color = :black, linewidth = 2.5)

    # Best fit (blue)
    if Yhat_best !== nothing
        CM.lines!(ax_k, t, Yhat_best[:, k]; color = :steelblue, linewidth = 2.5)
    end
end
```

---

### Legend-Panel (`fig[3, 1:2]`)

```julia
ax_legend = CM.Axis(fig[3, 1:2];
    backgroundcolor = :white,
    limits = ((0.0, 1.0), (0.0, 1.0)),
)
CM.hidedecorations!(ax_legend)
CM.hidespines!(ax_legend)

legend_items = [
    (0.05, :black,      2.5, 1.0, "Data (Ground Truth)"),
    (0.30, :steelblue,  2.5, 1.0, "Best (Current)"),
    (0.55, (:gray, 0.4), 0.8, 1.0, "Search History"),
    (0.75, :darkorange, 0.8, 1.0, "Current Level (Candidates)"),
]

for (x0, col, lw, _, lbl) in legend_items
    CM.lines!(ax_legend, [x0, x0 + 0.06], [0.5, 0.5]; color = col, linewidth = lw)
    CM.text!(ax_legend, x0 + 0.07, 0.5;
        text = lbl, align = (:left, :center), fontsize = 11, color = :black)
end
```

---

### Speichern und Rückgabe

```julia
filename = @sprintf("frame_%04d.png", frame_idx)
filepath = joinpath(output_dir, filename)
CM.save(filepath, fig; px_per_unit = 1)
return filepath
```

---

## Constraints

- `render_frame`-Signatur unverändert (kein Breaking Change).
- `render_all_frames` bleibt unverändert.
- `studies/visualization/animate_search.jl` wird nicht geändert.
- `structure_to_string`, `_simulate_candidate`, `_format_elapsed`, `_stage_description` bleiben vollständig unverändert.
- `import CairoMakie as CM` am Anfang der Datei einfügen (nicht `using`).
- Die alte `_frameless_panel!`-Funktion wird entfernt (nicht mehr benötigt).
- `_format_equation` bleibt erhalten (gleiche Signatur und Body).
- `_render_eq_line!` wird so angepasst, dass sie eine `CM.Axis` statt eines Plots-Subplots nimmt.

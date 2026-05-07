import CairoMakie as CM

"""
    structure_to_string(structure, basis, params; var_names=nothing, coef_tol=1e-8)

Convert a discovered structure and parameter vector into readable ODE equations.
"""
function structure_to_string(
    structure::StructureSpec,
    basis::AbstractBasis,
    params::Vector{Float64};
    var_names::Union{Nothing, Vector{String}} = nothing,
    coef_tol::Float64 = 1e-8
)
    if isempty(params)
        return "(not yet evaluated)"
    end

    lines = String[]
    param_idx = 1

    for k in 1:length(structure.active_idxs)
        lhs_name = var_names === nothing ? "u$k" : var_names[k]
        parts = String[]

        for term_idx in structure.active_idxs[k]
            raw = basis_term_name(basis, term_idx)
            term_name = raw

            if var_names !== nothing
                for i in length(var_names):-1:1
                    term_name = replace(term_name, "u$i" => var_names[i])
                end
            end

            c = params[param_idx]
            param_idx += 1

            if abs(c) < coef_tol
                continue
            end

            coef_str = @sprintf("%.3f", c)
            push!(parts, "$(coef_str)*$(term_name)")
        end

        rhs = isempty(parts) ? "0" : join(parts, " + ")
        push!(lines, "d$(lhs_name)/dt = $(rhs)")
    end

    return join(lines, "\n")
end

function _simulate_candidate(
    structure::StructureSpec,
    params::Vector{Float64},
    basis::AbstractBasis,
    traj::Trajectory
)::Union{Matrix{Float64}, Nothing}
    try
        if isempty(params)
            return nothing
        end

        f!, _, _ = build_rhs(structure, basis)
        Yhat = simulate(f!, params, traj)

        if any(isnan, Yhat) || any(isinf, Yhat)
            return nothing
        end

        return Yhat
    catch
        return nothing
    end
end

function _format_elapsed(elapsed_s::Float64)
    total_sec = floor(Int, elapsed_s)
    h = div(total_sec, 3600)
    m = div(total_sec % 3600, 60)
    s = total_sec % 60
    if h > 0
        return @sprintf("%02d:%02d:%02d", h, m, s)
    else
        return @sprintf("%02d:%02d", m, s)
    end
end

function _stage_description(basis::AbstractBasis, stage::Int, var_names::Union{Nothing, Vector{String}})
    if !(basis isa StagedPolynomialBasis)
        return "stage $stage terms"
    end
    if stage < 1 || stage > length(basis.term_groups)
        return "stage $stage terms"
    end

    semantic = if stage == 1
        "linear"
    elseif stage == 2
        "quadratic"
    elseif stage == 3
        "cross"
    elseif stage == 4
        "cubic"
    elseif stage == 5
        "trigonometric"
    else
        "stage $stage"
    end

    idxs = basis.term_groups[stage]
    names = [basis.term_names[i] for i in idxs]
    if var_names !== nothing
        names = map(names) do n
            for i in length(var_names):-1:1
                n = replace(n, "u$i" => var_names[i])
            end
            n
        end
    end
    n_show = min(3, length(names))
    example = join(names[1:n_show], ",  ")
    length(names) > 3 && (example *= ",  ...")

    return "$semantic terms  ($example)"
end

function _format_equation(eq::AbstractString)
    return replace(eq, "*" => " ")
end

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
    dim = size(traj_truth.x, 2)
    t   = traj_truth.t
    X   = traj_truth.x

    fig = CM.Figure(
        size            = (frame_width, frame_height),
        backgroundcolor = :white,
    )

    ax_header = CM.Axis(fig[1, 1:2];
        backgroundcolor = :white,
        limits = ((0.0, 1.0), (0.0, 1.0)),
    )
    CM.hidedecorations!(ax_header)
    CM.hidespines!(ax_header)

    stage_str = snapshot.stage_transition ?
        "$(snapshot.previous_stage) → $(snapshot.new_stage)" :
        "$(snapshot.stage)"
    loss_str    = @sprintf("%.6f", snapshot.best_loss)
    n_terms     = length(snapshot.best_params)
    time_str    = _format_elapsed(elapsed_s)
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

    CM.lines!(ax_header, [0.295, 0.295], [0.08, 0.92];
        color = CM.RGBf(0.80, 0.84, 0.90), linewidth = 1.0)

    status_text = "Stage $stage_str     |     Level $(snapshot.level)     |     Loss $loss_str     |     Active terms $n_terms     |     Time $time_str"
    CM.text!(ax_header, 0.31, 0.50;
        text = status_text, align = (:left, :center),
        fontsize = 13, color = CM.RGBf(0.05, 0.08, 0.20))

    ax_info = CM.Axis(fig[2, 1];
        backgroundcolor = :white,
        limits = ((0.0, 1.0), (0.0, 1.0)),
    )
    CM.hidedecorations!(ax_info)
    CM.hidespines!(ax_info)

    disc_str = structure_to_string(
        snapshot.best_structure,
        basis,
        snapshot.best_params;
        var_names = var_names,
    )
    disc_lines = split(disc_str, "\n")
    true_lines = true_equations !== nothing ? split(true_equations, "\n") : String[]

    eq_items = Tuple{String, Any, Int, Bool}[]

    if snapshot.stage_transition
        new_stage = snapshot.new_stage
        push!(eq_items, ("STAGE $new_stage UNLOCKED", :darkorange, 13, false))
        push!(eq_items, ("New terms: $(_stage_description(basis, new_stage, var_names))", :darkorange, 11, false))
        push!(eq_items, ("", :white, 10, false))
    end

    push!(eq_items, ("DISCOVERED MODEL", CM.RGBf(0.00, 0.32, 0.80), 12, false))
    for eq in disc_lines
        push!(eq_items, (_format_equation(eq), CM.RGBf(0.00, 0.32, 0.80), 11, true))
    end
    if !isempty(true_lines)
        push!(eq_items, ("", :white, 10, false))
        push!(eq_items, ("GROUND TRUTH", :black, 12, false))
        for eq in true_lines
            push!(eq_items, (_format_equation(eq), CM.RGBf(0.05, 0.05, 0.05), 11, true))
        end
    end

    n_eq   = length(eq_items)
    y_top  = 0.96
    y_bot  = 0.42
    y_step = (y_top - y_bot) / max(n_eq - 1, 1)

    for (i, (text, color, fsize, is_eq)) in enumerate(eq_items)
        isempty(text) && continue
        y = Float64(y_top - (i - 1) * y_step)
        if is_eq
            _render_eq_line!(ax_info, text, y, color, fsize)
        else
            CM.text!(ax_info, 0.05, y;
                text = text, align = (:left, :center),
                fontsize = fsize, color = color)
        end
    end

    CM.lines!(ax_info, [0.04, 0.96], [0.40, 0.40];
        color = CM.RGBf(0.78, 0.82, 0.88), linewidth = 0.8)

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

    plot_grid = CM.GridLayout(fig[2, 2])

    Yhat_best = _simulate_candidate(snapshot.best_structure, snapshot.best_params, basis, traj_truth)

    for k in 1:dim
        ax_k = CM.Axis(plot_grid[k, 1];
            backgroundcolor = :white,
            ylabel = var_names === nothing ? "u$k" : var_names[k],
        )

        y_lo = minimum(X[:, k])
        y_hi = maximum(X[:, k])
        pad  = max(0.3 * abs(y_hi - y_lo), 0.1)
        CM.ylims!(ax_k, y_lo - pad, y_hi + pad)

        if k < dim
            CM.hidexdecorations!(ax_k; grid = false)
        else
            ax_k.xlabel = "t"
        end

        for Yhat in accumulated_candidates
            CM.lines!(ax_k, t, Yhat[:, k]; color = (:gray, 0.18), linewidth = 0.5)
        end

        for Yhat in current_level_candidates
            CM.lines!(ax_k, t, Yhat[:, k]; color = :darkorange, linewidth = 0.6)
        end

        CM.lines!(ax_k, t, X[:, k]; color = :black, linewidth = 2.5)

        if Yhat_best !== nothing
            CM.lines!(ax_k, t, Yhat_best[:, k]; color = :steelblue, linewidth = 2.5)
        end
    end

    ax_legend = CM.Axis(fig[3, 1:2];
        backgroundcolor = :white,
        limits = ((0.0, 1.0), (0.0, 1.0)),
    )
    CM.hidedecorations!(ax_legend)
    CM.hidespines!(ax_legend)

    CM.rowsize!(fig.layout, 1, CM.Fixed(round(Int, frame_height * 0.08)))
    CM.rowsize!(fig.layout, 3, CM.Fixed(round(Int, frame_height * 0.045)))
    CM.colsize!(fig.layout, 1, CM.Relative(0.28))

    legend_items = [
        (0.05, :black,       2.5, 1.0, "Data (Ground Truth)"),
        (0.30, :steelblue,   2.5, 1.0, "Best (Current)"),
        (0.55, (:gray, 0.4), 0.8, 1.0, "Search History"),
        (0.75, :darkorange,  0.8, 1.0, "Current Level (Candidates)"),
    ]

    for (x0, col, lw, _, lbl) in legend_items
        CM.lines!(ax_legend, [x0, x0 + 0.06], [0.5, 0.5]; color = col, linewidth = lw)
        CM.text!(ax_legend, x0 + 0.07, 0.5;
            text = lbl, align = (:left, :center), fontsize = 11, color = :black)
    end

    filename = @sprintf("frame_%04d.png", frame_idx)
    filepath = joinpath(output_dir, filename)
    CM.save(filepath, fig; px_per_unit = 1)
    return filepath
end

function render_all_frames(
    vis_history::Vector{<:NamedTuple},
    traj_truth::Trajectory,
    basis::AbstractBasis;
    output_dir::String,
    var_names::Union{Nothing, Vector{String}} = nothing,
    true_equations::Union{Nothing, String} = nothing,
    title::String = "EvoGrow Search",
    frame_width::Int = 1920,
    frame_height::Int = 1080,
    max_candidates_per_level::Union{Nothing, Int} = nothing,
    clear_on_stage_transition::Bool = true,
)::NamedTuple
    mkpath(output_dir)
    accumulated_candidates = Matrix{Float64}[]
    n_skipped = 0
    n_frames = 0

    for snapshot in vis_history
        if clear_on_stage_transition && snapshot.stage_transition
            empty!(accumulated_candidates)
        end

        current_level_candidates = Matrix{Float64}[]
        limit = max_candidates_per_level === nothing ?
            length(snapshot.candidates_structures) :
            min(max_candidates_per_level, length(snapshot.candidates_structures))

        for i in 1:limit
            Yhat = _simulate_candidate(
                snapshot.candidates_structures[i],
                snapshot.candidates_params[i],
                basis,
                traj_truth,
            )

            if Yhat === nothing
                n_skipped += 1
            else
                push!(current_level_candidates, Yhat)
            end
        end

        n_frames += 1
        render_frame(
            n_frames,
            snapshot,
            accumulated_candidates,
            current_level_candidates,
            traj_truth,
            basis;
            output_dir = output_dir,
            var_names = var_names,
            true_equations = true_equations,
            title = title,
            elapsed_s = 0.0,
            frame_width = frame_width,
            frame_height = frame_height,
        )
        println("  Frame $n_frames/$(length(vis_history)) - Level $(snapshot.level), Stage $(snapshot.stage), Loss $(@sprintf("%.3g", snapshot.best_loss))")

        append!(accumulated_candidates, current_level_candidates)
    end

    return (n_frames = n_frames, n_skipped_simulations = n_skipped)
end

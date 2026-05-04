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
    t = traj_truth.t
    X = traj_truth.x

    l = @layout [
        a{0.05h}
        b{0.22h}
        grid(dim, 1)
        c{0.05h}
    ]
    plt = plot(
        layout = l,
        size = (frame_width, frame_height),
        background_color = :white,
        foreground_color = :black,
        left_margin = 8Plots.mm,
        bottom_margin = 3Plots.mm,
        right_margin = 8Plots.mm,
        top_margin = 2Plots.mm,
    )

    plot!(plt; plot_title = title, plot_titlefontsize = 16)

    plot!(
        plt[1];
        framestyle = :none,
        background_color_inside = :white,
        xlims = (0.0, 1.0),
        ylims = (0.0, 1.0),
        xaxis = false,
        yaxis = false,
        xticks = nothing,
        yticks = nothing,
        legend = false,
    )

    stage_str = snapshot.stage_transition ?
        "$(snapshot.previous_stage) → $(snapshot.new_stage)" :
        "$(snapshot.stage)"
    loss_str = @sprintf("%.6f", snapshot.best_loss)
    n_terms = length(snapshot.best_params)
    status_text = "Stage $stage_str   |   Level $(snapshot.level)   |   Loss $loss_str   |   Terms $n_terms"

    annotate!(plt[1], 0.03, 0.5, Plots.text(status_text, :left, :vcenter, 13, :black))

    plot!(
        plt[2];
        framestyle = :none,
        background_color_inside = :white,
        xlims = (0.0, 1.0),
        ylims = (0.0, 1.0),
        xaxis = false,
        yaxis = false,
        xticks = nothing,
        yticks = nothing,
        legend = false,
    )

    discovered_str = structure_to_string(
        snapshot.best_structure,
        basis,
        snapshot.best_params;
        var_names = var_names,
    )
    disc_lines = split(discovered_str, "\n")
    true_lines = true_equations !== nothing ? split(true_equations, "\n") : String[]

    items = Tuple{String, Int, Symbol}[]
    push!(items, ("DISCOVERED MODEL", 12, :black))
    for eq in disc_lines
        push!(items, (eq, 11, :steelblue))
    end
    if !isempty(true_lines)
        push!(items, ("", 10, :white))
        push!(items, ("GROUND TRUTH", 12, :black))
        for eq in true_lines
            push!(items, (eq, 11, :black))
        end
    end

    n_items = length(items)
    y_top = 0.93
    y_step = 0.88 / max(n_items - 1, 1)

    for (i, (text, fsize, color)) in enumerate(items)
        isempty(text) && continue
        y = y_top - (i - 1) * y_step
        annotate!(plt[2], 0.03, y, Plots.text(text, :left, :vcenter, fsize, color))
    end

    Yhat_best = _simulate_candidate(snapshot.best_structure, snapshot.best_params, basis, traj_truth)

    for k in 1:dim
        panel_idx = k + 2
        y_lo = minimum(X[:, k])
        y_hi = maximum(X[:, k])
        pad = max(0.3 * abs(y_hi - y_lo), 0.1)
        ylims_k = (y_lo - pad, y_hi + pad)

        plot!(
            plt[panel_idx],
            t,
            X[:, k];
            color = :black,
            linewidth = 2.5,
            label = false,
            ylims = ylims_k,
        )

        for Yhat in accumulated_candidates
            plot!(
                plt[panel_idx],
                t,
                Yhat[:, k];
                color = :gray,
                linewidth = 0.5,
                alpha = 0.18,
                label = false,
            )
        end

        for Yhat in current_level_candidates
            plot!(
                plt[panel_idx],
                t,
                Yhat[:, k];
                color = :darkorange,
                linewidth = 0.6,
                alpha = 1.0,
                label = false,
            )
        end

        if Yhat_best !== nothing
            plot!(
                plt[panel_idx],
                t,
                Yhat_best[:, k];
                color = :steelblue,
                linewidth = 2.5,
                label = false,
            )
        end

        ylabel!(plt[panel_idx], var_names === nothing ? "u$k" : var_names[k])

        if k == dim
            xlabel!(plt[panel_idx], "t")
        end
    end

    plot!(
        plt[dim + 3];
        framestyle = :none,
        background_color_inside = :white,
        xlims = (0.0, 1.0),
        ylims = (0.0, 1.0),
        xaxis = false,
        yaxis = false,
        xticks = nothing,
        yticks = nothing,
        legend = false,
    )

    legend_items = [
        (0.03, :black, 2.5, 1.0, "Data"),
        (0.27, :steelblue, 2.5, 1.0, "Best (current)"),
        (0.52, :gray, 0.8, 0.4, "Search history"),
        (0.76, :darkorange, 0.8, 1.0, "Current level"),
    ]

    for (x0, col, lw, al, lbl) in legend_items
        plot!(
            plt[dim + 3],
            [x0, x0 + 0.08],
            [0.5, 0.5];
            color = col,
            linewidth = lw,
            alpha = al,
            label = false,
        )
        annotate!(plt[dim + 3], x0 + 0.10, 0.5, Plots.text(lbl, :left, :vcenter, 12, :black))
    end

    filename = @sprintf("frame_%04d.png", frame_idx)
    filepath = joinpath(output_dir, filename)
    savefig(plt, filepath)
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

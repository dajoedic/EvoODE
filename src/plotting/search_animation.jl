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
    frame_width::Int = 1920,
    frame_height::Int = 1080,
)::String
    dim = size(traj_truth.x, 2)
    t = traj_truth.t
    X = traj_truth.x

    l = @layout [grid(dim, 1){0.68w} a{0.32w}]
    plt = plot(
        layout = l,
        size = (frame_width, frame_height),
        background_color = :white,
        foreground_color = :black,
        left_margin = 10Plots.mm,
        bottom_margin = 5Plots.mm,
        right_margin = 2Plots.mm,
    )

    stage_label = if snapshot.stage_transition
        "Stage $(snapshot.previous_stage) -> $(snapshot.new_stage)"
    else
        "Stage $(snapshot.stage)"
    end
    plot!(
        plt;
        plot_title = "EvoGrow Search  |  Level $(snapshot.level)  |  $stage_label",
        plot_titlefontsize = 13,
    )

    ylims_k_1 = (0.0, 1.0)
    Yhat_best = _simulate_candidate(snapshot.best_structure, snapshot.best_params, basis, traj_truth)

    for k in 1:dim
        y_lo = minimum(X[:, k])
        y_hi = maximum(X[:, k])
        pad = max(0.3 * abs(y_hi - y_lo), 0.1)
        ylims_k = (y_lo - pad, y_hi + pad)

        if k == 1
            ylims_k_1 = ylims_k
        end

        plot!(
            plt[k],
            t,
            X[:, k];
            color = :black,
            linewidth = 2.5,
            label = false,
            ylims = ylims_k,
        )

        for Yhat in accumulated_candidates
            plot!(
                plt[k],
                t,
                Yhat[:, k];
                color = :gray,
                linewidth = 0.5,
                alpha = 0.08,
                label = false,
            )
        end

        for Yhat in current_level_candidates
            plot!(
                plt[k],
                t,
                Yhat[:, k];
                color = :darkorange,
                linewidth = 0.6,
                alpha = 0.25,
                label = false,
            )
        end

        if Yhat_best !== nothing
            plot!(
                plt[k],
                t,
                Yhat_best[:, k];
                color = :steelblue,
                linewidth = 2.5,
                label = false,
            )
        end

        ylabel!(plt[k], var_names === nothing ? "u$k" : var_names[k])

        if k == dim
            xlabel!(plt[k], "t")
        end
    end

    plot!(
        plt[dim + 1];
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
    loss_str = @sprintf("%.6f", snapshot.best_loss)

    panel_text = "Level: $(snapshot.level)  Stage: $(snapshot.stage)\n"
    panel_text *= "Loss:  $loss_str\n"
    panel_text *= "\nDISCOVERED:\n$discovered_str"
    if true_equations !== nothing
        panel_text *= "\n\nTRUE SYSTEM:\n$true_equations"
    end

    annotate!(plt[dim + 1], 0.05, 0.97, Plots.text(panel_text, :left, :top, 10, :black))

    legend_items = [
        (:black, 2.5, 1.0, "Data"),
        (:steelblue, 2.5, 1.0, "Best (current)"),
        (:gray, 0.8, 0.4, "Search history"),
        (:darkorange, 0.8, 0.4, "Current level"),
    ]
    y_start = 0.18
    y_step = 0.055

    for (i, (col, lw, al, lbl)) in enumerate(legend_items)
        y = y_start - (i - 1) * y_step
        plot!(
            plt[dim + 1],
            [0.05, 0.22],
            [y, y];
            color = col,
            linewidth = lw,
            alpha = al,
            label = false,
        )
        annotate!(plt[dim + 1], 0.26, y, Plots.text(lbl, :left, :vcenter, 10, :black))
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
            frame_width = frame_width,
            frame_height = frame_height,
        )
        println("  Frame $n_frames/$(length(vis_history)) - Level $(snapshot.level), Stage $(snapshot.stage), Loss $(@sprintf("%.3g", snapshot.best_loss))")

        append!(accumulated_candidates, current_level_candidates)
    end

    return (n_frames = n_frames, n_skipped_simulations = n_skipped)
end

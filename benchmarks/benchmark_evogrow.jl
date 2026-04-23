# benchmarks/benchmark_evogrow.jl
#
# EvoGrow benchmark matrix for:
# - EvoGrow v2.1 baseline
# - EvoGrow v2.2 progression-only
# - EvoGrow v2.2 passive usage
# - EvoGrow v2.2 soft usage
# - GP baseline
#
# Phase 1 method-development benchmark:
# - full 10-system set
# - single seed per system
# - exact and surrogate systems reported separately

import Pkg
Pkg.activate(joinpath(@__DIR__, ".."))

using DifferentialEquations
using Plots
using Printf
using Statistics

include(joinpath(@__DIR__, "..", "src", "EvoODE.jl"))
using .EvoODE

# ============================================================
# Configuration
# ============================================================

const QUICK = get(ENV, "QUICK", "false") == "true" ||
              any(arg -> arg == "QUICK=true", ARGS)

const POP_SIZE = QUICK ? 5 : 10
const EVO_LEVELS = QUICK ? 8 : 20
const GP_GENERATIONS = QUICK ? 8 : 20
const BFGS_MAXITERS = QUICK ? 50 : 200
const VERBOSE = 1
const STAGE_MIN_LEVELS = 2
const SOFT_BIAS = 0.75
const SEEDS = QUICK ? [42, 123] : [42, 123, 7, 99, 17]

const OUT_DIR = joinpath(@__DIR__, "results")
mkpath(OUT_DIR)

# ============================================================
# Ground-truth ODE right-hand sides
# ============================================================

function rhs_02!(du, u, _, _)
    du[1] = 0.23 * u[1]
end

function rhs_03!(du, u, _, _)
    du[1] = 0.79 * u[1] * (1.0 - u[1] / 74.3)
end

function rhs_11!(du, u, _, _)
    du[1] = -u[1]^3
end

function rhs_23!(du, u, _, _)
    du[1] = 0.21 - sin(u[1])
end

function rhs_24!(du, u, _, _)
    du[1] = u[2]
    du[2] = -2.1 * u[1]
end

function rhs_26!(du, u, _, _)
    du[1] = u[1] * (3.0 - u[1] - 2.0 * u[2])
    du[2] = u[2] * (2.0 - u[1] - u[2])
end

function rhs_31!(du, u, _, _)
    du[1] = -0.4 * u[1] * u[2]
    du[2] = 0.4 * u[1] * u[2] - 0.314 * u[2]
end

function rhs_37!(du, u, _, _)
    du[1] = u[2]
    du[2] = -u[1] - 0.43 * (u[1]^2 - 1.0) * u[2]
end

function rhs_54!(du, u, _, _)
    du[1] = 5.1 * (u[2] - u[1])
    du[2] = 12.0 * u[1] - u[2] - u[1] * u[3]
    du[3] = u[1] * u[2] - 1.67 * u[3]
end

function rhs_63!(du, u, _, _)
    du[1] = -0.28 * u[1] * u[3]
    du[2] = 0.28 * u[1] * u[3] - 0.47 * u[2]
    du[3] = 0.47 * u[2] - 0.30 * u[3]
    du[4] = 0.30 * u[3]
end

# ============================================================
# Benchmark definitions
# ============================================================

Base.@kwdef struct BenchmarkSystem
    id::Int
    name::String
    dim::Int
    true_rhs!::Function
    u0::Vector{Float64}
    tspan::Tuple{Float64,Float64}
    T::Int
    true_structure::String
    representability::Symbol
    expected_stage::Int
    expected_terms::Union{Nothing,Vector{Vector{String}}} = nothing
    surrogate_target_terms::Vector{String} = String[]
    basis_note::String = ""
end

struct BenchmarkVariant
    name::String
    slug::String
    method_family::Symbol
    build_structure::Function
    build_basis::Function
end

const BENCHMARKS = BenchmarkSystem[
    BenchmarkSystem(
        id = 2,
        name = "Population growth (linear)",
        dim = 1,
        true_rhs! = rhs_02!,
        u0 = [4.78],
        tspan = (0.0, 12.0),
        T = 120,
        true_structure = "du1 = 0.23*u1",
        representability = :exact,
        expected_stage = 1,
        expected_terms = [["u1"]]
    ),
    BenchmarkSystem(
        id = 3,
        name = "Logistic growth",
        dim = 1,
        true_rhs! = rhs_03!,
        u0 = [7.3],
        tspan = (0.0, 20.0),
        T = 200,
        true_structure = "du1 = 0.79*u1 - 0.0106*u1^2",
        representability = :exact,
        expected_stage = 2,
        expected_terms = [["u1", "u1^2"]]
    ),
    BenchmarkSystem(
        id = 11,
        name = "Critical slowing down",
        dim = 1,
        true_rhs! = rhs_11!,
        u0 = [3.4],
        tspan = (0.0, 5.0),
        T = 100,
        true_structure = "du1 = -u1^3",
        representability = :exact,
        expected_stage = 4,
        expected_terms = [["u1^3"]]
    ),
    BenchmarkSystem(
        id = 23,
        name = "Overdamped pendulum",
        dim = 1,
        true_rhs! = rhs_23!,
        u0 = [-2.74],
        tspan = (0.0, 25.0),
        T = 250,
        true_structure = "du1 = 0.21 - sin(u1)",
        representability = :surrogate,
        expected_stage = 5,
        surrogate_target_terms = ["sin(u1)", "cos(u1)"],
        basis_note = "Constant offset is outside the current basis."
    ),
    BenchmarkSystem(
        id = 24,
        name = "Harmonic oscillator",
        dim = 2,
        true_rhs! = rhs_24!,
        u0 = [0.4, -0.03],
        tspan = (0.0, 15.0),
        T = 200,
        true_structure = "du1 = u2 | du2 = -2.1*u1",
        representability = :exact,
        expected_stage = 1,
        expected_terms = [["u2"], ["u1"]]
    ),
    BenchmarkSystem(
        id = 26,
        name = "Lotka-Volterra competition",
        dim = 2,
        true_rhs! = rhs_26!,
        u0 = [5.0, 4.3],
        tspan = (0.0, 10.0),
        T = 200,
        true_structure = "du1 = 3*u1 - u1^2 - 2*u1*u2 | du2 = 2*u2 - u1*u2 - u2^2",
        representability = :exact,
        expected_stage = 3,
        expected_terms = [["u1", "u1^2", "u1*u2"], ["u2", "u1*u2", "u2^2"]]
    ),
    BenchmarkSystem(
        id = 31,
        name = "SIR model",
        dim = 2,
        true_rhs! = rhs_31!,
        u0 = [7.2, 0.98],
        tspan = (0.0, 20.0),
        T = 200,
        true_structure = "du1 = -0.4*u1*u2 | du2 = 0.4*u1*u2 - 0.314*u2",
        representability = :exact,
        expected_stage = 3,
        expected_terms = [["u1*u2"], ["u1*u2", "u2"]]
    ),
    BenchmarkSystem(
        id = 37,
        name = "Van der Pol oscillator",
        dim = 2,
        true_rhs! = rhs_37!,
        u0 = [2.2, 0.0],
        tspan = (0.0, 20.0),
        T = 200,
        true_structure = "du1 = u2 | du2 = -u1 + 0.43*u2 - 0.43*u1^2*u2",
        representability = :surrogate,
        expected_stage = 4,
        surrogate_target_terms = ["u1^3", "u2^3"],
        basis_note = "Cubic cross term u1^2*u2 is outside the current basis."
    ),
    BenchmarkSystem(
        id = 54,
        name = "Lorenz (periodic)",
        dim = 3,
        true_rhs! = rhs_54!,
        u0 = [2.3, 8.1, 12.4],
        tspan = (0.0, 15.0),
        T = 300,
        true_structure = "du1 = -5.1*u1 + 5.1*u2 | du2 = 12*u1 - u2 - u1*u3 | du3 = u1*u2 - 1.67*u3",
        representability = :exact,
        expected_stage = 3,
        expected_terms = [["u1", "u2"], ["u1", "u2", "u1*u3"], ["u1*u2", "u3"]]
    ),
    BenchmarkSystem(
        id = 63,
        name = "SEIR model",
        dim = 4,
        true_rhs! = rhs_63!,
        u0 = [0.6, 0.3, 0.09, 0.01],
        tspan = (0.0, 30.0),
        T = 300,
        true_structure = "du1 = -0.28*u1*u3 | du2 = 0.28*u1*u3 - 0.47*u2 | du3 = 0.47*u2 - 0.30*u3 | du4 = 0.30*u3",
        representability = :exact,
        expected_stage = 3,
        expected_terms = [["u1*u3"], ["u1*u3", "u2"], ["u2", "u3"], ["u3"]]
    )
]

const VARIANTS = BenchmarkVariant[
    BenchmarkVariant(
        "EvoGrow v1 (flat)",
        "evogrow_v1",
        :evogrow,
        dim -> EvoGrow(
            pop_size = POP_SIZE,
            n_levels = EVO_LEVELS,
            children_per_parent = 2,
            max_terms_per_eq = 6,
            λ = 1e-3,
            progression = StageProgressionPolicy(mode = :global_plateau, min_levels_per_stage = STAGE_MIN_LEVELS),
            usage = StageUsagePolicy(mode = :hard, new_term_bias_prob = SOFT_BIAS)
        ),
        dim -> default_staged_polynomial_basis(dim)
    ),
    BenchmarkVariant(
        "EvoGrow v2.1 baseline",
        "evogrow_v2_1",
        :evogrow,
        dim -> EvoGrow(
            pop_size = POP_SIZE,
            n_levels = EVO_LEVELS,
            children_per_parent = 2,
            max_terms_per_eq = 6,
            λ = 1e-3,
            progression = StageProgressionPolicy(mode = :global_plateau, min_levels_per_stage = STAGE_MIN_LEVELS),
            usage = StageUsagePolicy(mode = :hard, new_term_bias_prob = SOFT_BIAS)
        ),
        dim -> default_staged_polynomial_basis(dim)
    ),
    BenchmarkVariant(
        "EvoGrow v2.2 progression-only",
        "evogrow_v2_2_progression",
        :evogrow,
        dim -> EvoGrow(
            pop_size = POP_SIZE,
            n_levels = EVO_LEVELS,
            children_per_parent = 2,
            max_terms_per_eq = 6,
            λ = 1e-3,
            progression = StageProgressionPolicy(mode = :stage_local, min_levels_per_stage = STAGE_MIN_LEVELS),
            usage = StageUsagePolicy(mode = :hard, new_term_bias_prob = SOFT_BIAS)
        ),
        dim -> default_staged_polynomial_basis(dim)
    ),
    BenchmarkVariant(
        "EvoGrow v2.2 passive usage",
        "evogrow_v2_2_passive",
        :evogrow,
        dim -> EvoGrow(
            pop_size = POP_SIZE,
            n_levels = EVO_LEVELS,
            children_per_parent = 2,
            max_terms_per_eq = 6,
            λ = 1e-3,
            progression = StageProgressionPolicy(mode = :stage_local, min_levels_per_stage = STAGE_MIN_LEVELS),
            usage = StageUsagePolicy(mode = :passive, new_term_bias_prob = SOFT_BIAS)
        ),
        dim -> default_staged_polynomial_basis(dim)
    ),
    BenchmarkVariant(
        "EvoGrow v2.2 soft usage",
        "evogrow_v2_2_soft",
        :evogrow,
        dim -> EvoGrow(
            pop_size = POP_SIZE,
            n_levels = EVO_LEVELS,
            children_per_parent = 2,
            max_terms_per_eq = 6,
            λ = 1e-3,
            progression = StageProgressionPolicy(mode = :stage_local, min_levels_per_stage = STAGE_MIN_LEVELS),
            usage = StageUsagePolicy(mode = :soft, new_term_bias_prob = SOFT_BIAS)
        ),
        dim -> default_staged_polynomial_basis(dim)
    ),
    BenchmarkVariant(
        "GP baseline",
        "gp_baseline",
        :gp,
        dim -> GPStructureSearch(
            pop_size = POP_SIZE,
            n_generations = GP_GENERATIONS,
            tournament_k = 3,
            p_crossover = 0.7,
            p_mutation = 0.3,
            max_terms_per_eq = 6,
            init_min_terms = 1,
            init_max_terms = 2,
            λ = 1e-3
        ),
        dim -> default_staged_polynomial_basis(dim)
    )
]

# ============================================================
# Helpers
# ============================================================

function generate_trajectory(sys::BenchmarkSystem)::Trajectory
    t_grid = collect(range(sys.tspan[1], sys.tspan[2]; length = sys.T))
    prob = ODEProblem(sys.true_rhs!, copy(sys.u0), sys.tspan, nothing)
    sol = solve(prob, Tsit5(); saveat = t_grid, abstol = 1e-9, reltol = 1e-9)

    if length(sol.t) != sys.T
        error("Ground-truth solver returned $(length(sol.t)) points for system $(sys.name)")
    end

    return Trajectory(t_grid, Array(sol)')
end

function basis_name_to_idx(basis::AbstractBasis)
    return Dict(basis_term_name(basis, i) => i for i in 1:basis_num_terms(basis))
end

function expected_active_idxs(sys::BenchmarkSystem, basis::AbstractBasis)
    sys.expected_terms === nothing && return nothing
    name_to_idx = basis_name_to_idx(basis)
    return [sort([name_to_idx[name] for name in eq_terms]) for eq_terms in sys.expected_terms]
end

function support_match(structure::StructureSpec, expected_idxs::Vector{Vector{Int}})
    if length(structure.active_idxs) != length(expected_idxs)
        return false
    end
    for (got, expected) in zip(structure.active_idxs, expected_idxs)
        if sort(unique(got)) != sort(unique(expected))
            return false
        end
    end
    return true
end

function structure_uses_indices(structure::StructureSpec, term_idxs::Vector{Int})
    term_set = Set(term_idxs)
    for eq_terms in structure.active_idxs
        for idx in eq_terms
            if idx in term_set
                return true
            end
        end
    end
    return false
end

function structure_uses_term_names(structure::StructureSpec, basis::AbstractBasis, term_names::Vector{String})
    isempty(term_names) && return false
    name_to_idx = basis_name_to_idx(basis)
    target_idxs = [name_to_idx[name] for name in term_names if haskey(name_to_idx, name)]
    isempty(target_idxs) && return false
    return structure_uses_indices(structure, target_idxs)
end

function safe_name(name::String)
    return replace(lowercase(name), " " => "_", "(" => "", ")" => "", "/" => "_")
end

function variant_options(seed::Int)
    return DiscoveryOptions(
        rng_seed = seed,
        verbose = VERBOSE,
        min_levels = 2,
        max_levels = 50,
        loss_tol = 1e-8,
        plateau_window = 3,
        plateau_tol = 1e-4,
        plateau_relative = false,
        plateau_rtol = 1e-3
    )
end

function assess_result(sys::BenchmarkSystem,
                       variant::BenchmarkVariant,
                       result::DiscoveryResult,
                       basis::AbstractBasis)

    final_stage = haskey(result.meta.structure, :final_stage) ? result.meta.structure.final_stage : -1
    total_invalid_evals = haskey(result.meta.structure, :total_invalid_evals) ? result.meta.structure.total_invalid_evals : 0
    total_loss_evals = haskey(result.meta.structure, :total_loss_evals) ? result.meta.structure.total_loss_evals : 0
    stage_level_counts = haskey(result.meta.structure, :stage_level_counts) ? result.meta.structure.stage_level_counts : Int[]
    stage_first_use_level = haskey(result.meta.structure, :stage_first_use_level) ? result.meta.structure.stage_first_use_level : Int[]
    termination_reason = haskey(result.meta.structure, :termination_reason) ? result.meta.structure.termination_reason : :unknown

    exact_support_match = false
    used_expected_stage_terms = false
    used_target_terms = false
    reached_expected_stage = false
    recovery_label = "unscored"

    if sys.representability == :exact
        expected_idxs = expected_active_idxs(sys, basis)
        exact_support_match = expected_idxs === nothing ? false : support_match(result.structure, expected_idxs)
        reached_expected_stage = final_stage >= sys.expected_stage
        used_expected_stage_terms = basis isa StagedPolynomialBasis ? structure_uses_indices(result.structure, basis.term_groups[sys.expected_stage]) : false
        recovery_label = exact_support_match ? "exact_recovery" : "surrogate_fit"
    else
        reached_expected_stage = final_stage >= sys.expected_stage
        used_expected_stage_terms = basis isa StagedPolynomialBasis ? structure_uses_indices(result.structure, basis.term_groups[sys.expected_stage]) : false
        used_target_terms = structure_uses_term_names(result.structure, basis, sys.surrogate_target_terms)
        recovery_label = (reached_expected_stage && (used_expected_stage_terms || used_target_terms)) ? "meaningful_surrogate" : "weak_surrogate"
    end

    stage_overshoot = final_stage >= 0 ? final_stage - sys.expected_stage : -999
    expected_stage_first_use = (!isempty(stage_first_use_level) && sys.expected_stage <= length(stage_first_use_level)) ? stage_first_use_level[sys.expected_stage] : -1
    stage_budget_string = isempty(stage_level_counts) ? "NA" : join(stage_level_counts, "|")
    wasted_levels = isempty(stage_level_counts) ? 0 :
                    sum(stage_level_counts[sys.expected_stage + 1:end]; init = 0)

    return (
        representability = sys.representability,
        expected_stage = sys.expected_stage,
        final_stage = final_stage,
        stage_overshoot = stage_overshoot,
        exact_support_match = exact_support_match,
        reached_expected_stage = reached_expected_stage,
        used_expected_stage_terms = used_expected_stage_terms,
        used_target_terms = used_target_terms,
        recovery_label = recovery_label,
        total_invalid_evals = total_invalid_evals,
        total_loss_evals = total_loss_evals,
        stage_budget_string = stage_budget_string,
        wasted_levels = wasted_levels,
        expected_stage_first_use = expected_stage_first_use,
        termination_reason = termination_reason
    )
end

function run_one(sys::BenchmarkSystem, variant::BenchmarkVariant; seed::Int = SEEDS[1])
    sep = "=" ^ 84
    @printf("\n%s\n", sep)
    @printf("  [%s] ID %-3d | %s (dim=%d)\n", variant.slug, sys.id, sys.name, sys.dim)
    @printf("  Category: %s | expected stage: %d\n", string(sys.representability), sys.expected_stage)
    if sys.representability == :surrogate
        @printf("  Note: %s\n", sys.basis_note)
    end
    @printf("%s\n", sep)

    traj = generate_trajectory(sys)
    basis = variant.build_basis(sys.dim)
    structure = variant.build_structure(sys.dim)
    opts = variant_options(seed)

    t0 = time()
    result = discover(
        traj;
        structure = structure,
        optimizer = BFGSOptimizer(maxiters = BFGS_MAXITERS),
        basis = basis,
        loss = MSELoss(),
        options = opts
    )
    elapsed = time() - t0

    assessment = assess_result(sys, variant, result, basis)

    @printf("  Loss:         %.4e\n", result.loss)
    @printf("  Objective:    %.4e\n", result.objective)
    @printf("  n_params:     %d\n", length(result.params))
    @printf("  Final stage:  %s\n", assessment.final_stage >= 0 ? string(assessment.final_stage) : "NA")
    @printf("  Recovery:     %s\n", assessment.recovery_label)
    @printf("  Invalid evals:%d\n", assessment.total_invalid_evals)
    @printf("  Time:         %.1f s\n", elapsed)

    variant_dir = joinpath(OUT_DIR, variant.slug)
    mkpath(variant_dir)
    base = @sprintf("%s_%02d_%s", variant.slug, sys.id, safe_name(sys.name))

    f!, _, _ = build_rhs(result.structure, basis)
    plot_file = joinpath(variant_dir, base * ".png")
    solve_and_save_plot(
        f!,
        result.params,
        traj;
        filename = plot_file,
        title = "$(variant.slug) | ID $(sys.id) | MSE=$(round(result.loss, sigdigits = 3))"
    )

    hist_file = ""
    if haskey(result.meta.structure, :best_J_hist) && length(result.meta.structure.best_J_hist) >= 2
        hist_file = joinpath(variant_dir, base * "_history.png")
        levels = 1:length(result.meta.structure.best_J_hist)
        p_hist = plot(
            levels,
            result.meta.structure.best_J_hist;
            xlabel = "Level",
            ylabel = "Best objective",
            title = "$(variant.slug) convergence",
            yscale = :log10,
            marker = :circle,
            legend = false,
            linewidth = 2
        )
        savefig(p_hist, hist_file)
    end

    csv_file = joinpath(variant_dir, base * ".csv")
    save_comparison_csv(traj.t, traj.x, result.meta.prediction.Yhat; filename = csv_file)

    discovered_str = replace(result.meta.structure.best_structure_pretty, '\n' => " | ")

    return (
        variant = variant.name,
        variant_slug = variant.slug,
        method_family = variant.method_family,
        id = sys.id,
        name = sys.name,
        dim = sys.dim,
        representability = assessment.representability,
        expected_stage = assessment.expected_stage,
        final_stage = assessment.final_stage,
        stage_overshoot = assessment.stage_overshoot,
        exact_support_match = assessment.exact_support_match,
        reached_expected_stage = assessment.reached_expected_stage,
        used_expected_stage_terms = assessment.used_expected_stage_terms,
        used_target_terms = assessment.used_target_terms,
        recovery_label = assessment.recovery_label,
        loss = result.loss,
        objective = result.objective,
        n_params = length(result.params),
        elapsed_s = elapsed,
        total_invalid_evals = assessment.total_invalid_evals,
        total_loss_evals = assessment.total_loss_evals,
        stage_budget_string = assessment.stage_budget_string,
        wasted_levels = assessment.wasted_levels,
        expected_stage_first_use = assessment.expected_stage_first_use,
        termination_reason = string(assessment.termination_reason),
        discovered_structure = discovered_str,
        plot_file = plot_file,
        history_file = hist_file,
        csv_file = csv_file
    )
end

function print_summary(records)
    @printf("\n\n%s\n", "=" ^ 130)
    @printf("  BENCHMARK SUMMARY - PHASE 1 METHOD DEVELOPMENT\n")
    @printf("%s\n", "=" ^ 130)
    @printf("  %-22s  %-3s  %-10s  %-11s  %-10s  %-6s  %-5s  %-8s  %-6s  %-10s\n",
            "Variant", "ID", "Category", "Recovery", "Loss", "Param", "Stage", "Wasted", "Time", "Invalid")
    @printf("%s\n", "-" ^ 130)

    for r in records
        loss_str = isnan(r.loss) ? "ERROR" : @sprintf("%.3e", r.loss)
        stage_str = r.final_stage < 0 ? "NA" : string(r.final_stage)
        time_str = isnan(r.elapsed_s) ? "ERR" : @sprintf("%.1f", r.elapsed_s)
        @printf("  %-22s  %-3d  %-10s  %-11s  %-10s  %-6d  %-5s  %-8d  %-6s  %-10d\n",
                r.variant_slug,
                r.id,
                string(r.representability),
                r.recovery_label,
                loss_str,
                r.n_params,
                stage_str,
                r.wasted_levels,
                time_str,
                r.total_invalid_evals)
    end

    @printf("%s\n", "=" ^ 130)
end

function _summary_csv_header_line()
    return join([
        "variant",
        "variant_slug",
        "method_family",
        "id",
        "name",
        "dim",
        "representability",
        "expected_stage",
        "final_stage",
        "stage_overshoot",
        "exact_support_match",
        "reached_expected_stage",
        "used_expected_stage_terms",
        "used_target_terms",
        "recovery_label",
        "loss",
        "objective",
        "n_params",
        "elapsed_s",
        "total_invalid_evals",
        "total_loss_evals",
        "stage_budget_string",
        "wasted_levels",
        "expected_stage_first_use",
        "termination_reason",
        "discovered_structure",
        "plot_file",
        "history_file",
        "csv_file"
    ], ";")
end

function _summary_csv_row_line(r)
    return join([
        "\"$(r.variant)\"",
        "\"$(r.variant_slug)\"",
        string(r.method_family),
        string(r.id),
        "\"$(r.name)\"",
        string(r.dim),
        string(r.representability),
        string(r.expected_stage),
        string(r.final_stage),
        string(r.stage_overshoot),
        string(r.exact_support_match),
        string(r.reached_expected_stage),
        string(r.used_expected_stage_terms),
        string(r.used_target_terms),
        "\"$(r.recovery_label)\"",
        @sprintf("%.6e", r.loss),
        @sprintf("%.6e", r.objective),
        string(r.n_params),
        @sprintf("%.2f", r.elapsed_s),
        string(r.total_invalid_evals),
        string(r.total_loss_evals),
        "\"$(r.stage_budget_string)\"",
        string(r.wasted_levels),
        string(r.expected_stage_first_use),
        "\"$(r.termination_reason)\"",
        "\"$(r.discovered_structure)\"",
        "\"$(r.plot_file)\"",
        "\"$(r.history_file)\"",
        "\"$(r.csv_file)\""
    ], ";")
end

function write_summary_csv(records)
    summary_file = joinpath(OUT_DIR, "summary.csv")
    open(summary_file, "w") do io
        println(io, _summary_csv_header_line())

        for r in records
            println(io, _summary_csv_row_line(r))
        end
    end
    return summary_file
end

function aggregate_records(records)
    groups = Dict{Tuple{String,Int}, Vector{NamedTuple}}()
    for r in records
        key = (r.variant_slug, r.id)
        if !haskey(groups, key)
            groups[key] = NamedTuple[]
        end
        push!(groups[key], r)
    end

    agg = NamedTuple[]
    for ((vs, sid), group) in sort(collect(groups), by = x -> (x[1][1], x[1][2]))
        valid = filter(r -> !isnan(r.loss), group)
        n_total = length(group)
        n_valid = length(valid)

        mean_loss           = n_valid > 0 ? mean(r.loss for r in valid) : NaN
        std_loss            = n_valid > 1 ? std(r.loss for r in valid) : NaN
        exact_match_rate    = n_valid > 0 ? mean(Float64(r.exact_support_match) for r in valid) : NaN
        mean_final_stage    = n_valid > 0 ? mean(Float64(r.final_stage) for r in valid) : NaN
        mean_wasted_levels  = n_valid > 0 ? mean(Float64(r.wasted_levels) for r in valid) : NaN
        mean_elapsed_s      = n_valid > 0 ? mean(r.elapsed_s for r in valid) : NaN
        mean_invalid_evals  = n_valid > 0 ? mean(Float64(r.total_invalid_evals) for r in valid) : NaN

        first_r = group[1]
        push!(agg, (
            variant             = first_r.variant,
            variant_slug        = first_r.variant_slug,
            method_family       = first_r.method_family,
            id                  = first_r.id,
            name                = first_r.name,
            dim                 = first_r.dim,
            representability    = first_r.representability,
            expected_stage      = first_r.expected_stage,
            n_seeds             = n_total,
            n_valid             = n_valid,
            mean_loss           = mean_loss,
            std_loss            = std_loss,
            exact_match_rate    = exact_match_rate,
            mean_final_stage    = mean_final_stage,
            mean_wasted_levels  = mean_wasted_levels,
            mean_elapsed_s      = mean_elapsed_s,
            mean_invalid_evals  = mean_invalid_evals
        ))
    end
    return agg
end

function print_aggregate_summary(agg)
    @printf("\n\n%s\n", "=" ^ 130)
    @printf("  AGGREGATE SUMMARY (%d seeds per cell)\n", length(SEEDS))
    @printf("%s\n", "=" ^ 130)
    @printf("  %-22s  %-3s  %-10s  %-11s  %-12s  %-12s  %-6s  %-5s  %-8s  %-8s\n",
            "Variant", "ID", "Category", "ExactRate", "MeanLoss", "StdLoss",
            "Params", "Stage", "Wasted", "Time(s)")
    @printf("%s\n", "-" ^ 130)
    for r in agg
        loss_str  = isnan(r.mean_loss)        ? "ERROR" : @sprintf("%.3e", r.mean_loss)
        std_str   = isnan(r.std_loss)         ? "NA"    : @sprintf("%.3e", r.std_loss)
        rate_str  = isnan(r.exact_match_rate) ? "NA"    : @sprintf("%.2f", r.exact_match_rate)
        stage_str = isnan(r.mean_final_stage) ? "NA"    : @sprintf("%.1f", r.mean_final_stage)
        waste_str = isnan(r.mean_wasted_levels) ? "NA"  : @sprintf("%.1f", r.mean_wasted_levels)
        time_str  = isnan(r.mean_elapsed_s)   ? "ERR"   : @sprintf("%.1f", r.mean_elapsed_s)
        @printf("  %-22s  %-3d  %-10s  %-11s  %-12s  %-12s  %-6s  %-5s  %-8s  %-8s\n",
                r.variant_slug, r.id, string(r.representability),
                rate_str, loss_str, std_str, "$(r.n_valid)/$(r.n_seeds)",
                stage_str, waste_str, time_str)
    end
    @printf("%s\n", "=" ^ 130)
end

function write_aggregate_csv(agg)
    agg_file = joinpath(OUT_DIR, "summary_aggregate.csv")
    open(agg_file, "w") do io
        println(io, join([
            "variant", "variant_slug", "method_family",
            "id", "name", "dim", "representability", "expected_stage",
            "n_seeds", "n_valid",
            "mean_loss", "std_loss", "exact_match_rate",
            "mean_final_stage", "mean_wasted_levels",
            "mean_elapsed_s", "mean_invalid_evals"
        ], ";"))
        for r in agg
            println(io, join([
                "\"$(r.variant)\"",
                "\"$(r.variant_slug)\"",
                string(r.method_family),
                string(r.id),
                "\"$(r.name)\"",
                string(r.dim),
                string(r.representability),
                string(r.expected_stage),
                string(r.n_seeds),
                string(r.n_valid),
                isnan(r.mean_loss)          ? "NA" : @sprintf("%.6e", r.mean_loss),
                isnan(r.std_loss)           ? "NA" : @sprintf("%.6e", r.std_loss),
                isnan(r.exact_match_rate)   ? "NA" : @sprintf("%.4f", r.exact_match_rate),
                isnan(r.mean_final_stage)   ? "NA" : @sprintf("%.2f", r.mean_final_stage),
                isnan(r.mean_wasted_levels) ? "NA" : @sprintf("%.2f", r.mean_wasted_levels),
                isnan(r.mean_elapsed_s)     ? "NA" : @sprintf("%.2f", r.mean_elapsed_s),
                isnan(r.mean_invalid_evals) ? "NA" : @sprintf("%.2f", r.mean_invalid_evals)
            ], ";"))
        end
    end
    return agg_file
end

# ============================================================
# Main
# ============================================================

@printf("\nPhase 1 benchmark matrix\n")
@printf("Systems: %d | Variants: %d | quick=%s | seeds=%d\n",
        length(BENCHMARKS), length(VARIANTS), QUICK, length(SEEDS))
@printf("Output: %s\n", OUT_DIR)

records = NamedTuple[]
summary_file = joinpath(OUT_DIR, "summary.csv")
summary_io = open(summary_file, "w")
println(summary_io, _summary_csv_header_line())
flush(summary_io)

for variant in VARIANTS
    for sys in BENCHMARKS
        for seed in SEEDS
            try
                record = run_one(sys, variant; seed = seed)
                push!(records, record)
                println(summary_io, _summary_csv_row_line(record))
                flush(summary_io)
            catch e
                @printf("\nERROR on variant=%s system=%d seed=%d (%s): %s\n",
                        variant.slug, sys.id, seed, sys.name, sprint(showerror, e))
                record = (
                    variant = variant.name,
                    variant_slug = variant.slug,
                    method_family = variant.method_family,
                    id = sys.id,
                    name = sys.name,
                    dim = sys.dim,
                    representability = sys.representability,
                    expected_stage = sys.expected_stage,
                    final_stage = -1,
                    stage_overshoot = -999,
                    exact_support_match = false,
                    reached_expected_stage = false,
                    used_expected_stage_terms = false,
                    used_target_terms = false,
                    recovery_label = "error",
                    loss = NaN,
                    objective = NaN,
                    n_params = -1,
                    elapsed_s = NaN,
                    total_invalid_evals = -1,
                    total_loss_evals = -1,
                    stage_budget_string = "NA",
                    wasted_levels = 0,
                    expected_stage_first_use = -1,
                    termination_reason = "error",
                    discovered_structure = "ERROR",
                    plot_file = "",
                    history_file = "",
                    csv_file = ""
                )
                push!(records, record)
                println(summary_io, _summary_csv_row_line(record))
                flush(summary_io)
            end
        end
    end
end
close(summary_io)

agg_records  = aggregate_records(records)
print_aggregate_summary(agg_records)
agg_file     = write_aggregate_csv(agg_records)
@printf("\nIndividual runs -> %s\n", joinpath(OUT_DIR, "summary.csv"))
@printf("Aggregate       -> %s\n", agg_file)
@printf("Done.\n")

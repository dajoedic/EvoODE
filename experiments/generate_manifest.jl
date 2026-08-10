import Pkg
Pkg.activate(joinpath(@__DIR__, ".."))

using Dates
using JSON3
using Printf

include(joinpath(@__DIR__, "..", "src", "EvoODE.jl"))
using .EvoODE

# ============================================================
# Phase A configuration
# ============================================================

const EXPERIMENT_ID = "paper1_phaseA_v1"
const PHASE = "A"
const HYPOTHESIS = "H1_staged_growth_efficiency"
const RUN_TYPE = "exploratory"
const INCLUDE_IN_PAPER = false

const POP_SIZE = 10
const EVO_LEVELS = 20
const GP_GENERATIONS = 20
const BFGS_MAXITERS = 200
const BFGS_ABSTOL = 1e-6
const BFGS_RELTOL = 1e-6
const BFGS_MAXITERS_SOLVE = 10^6
const BFGS_MAX_LOSS_EVALS = 100_000
const BFGS_CLAMP_VAL = 10.0
const STAGE_MIN_LEVELS = 2
const SOFT_BIAS = 0.75
const SEEDS = [42, 123, 7, 99, 17]

# ============================================================
# Local copies of benchmark systems
# ============================================================

Base.@kwdef struct ManifestSystem
    id::Int
    name::String
    dim::Int
    u0::Vector{Float64}
    tspan::Tuple{Float64,Float64}
    T::Int
    true_structure::String
    representability::Symbol
    expected_stage::Int
end

struct ManifestVariant
    name::String
    slug::String
    method_family::Symbol
    build_strategy::Function
end

const SYSTEMS = ManifestSystem[
    ManifestSystem(
        id = 2,
        name = "Population growth (linear)",
        dim = 1,
        u0 = [4.78],
        tspan = (0.0, 12.0),
        T = 120,
        true_structure = "du1 = 0.23*u1",
        representability = :exact,
        expected_stage = 1
    ),
    ManifestSystem(
        id = 3,
        name = "Logistic growth",
        dim = 1,
        u0 = [7.3],
        tspan = (0.0, 20.0),
        T = 200,
        true_structure = "du1 = 0.79*u1 - 0.0106*u1^2",
        representability = :exact,
        expected_stage = 2
    ),
    ManifestSystem(
        id = 11,
        name = "Critical slowing down",
        dim = 1,
        u0 = [3.4],
        tspan = (0.0, 5.0),
        T = 100,
        true_structure = "du1 = -u1^3",
        representability = :exact,
        expected_stage = 4
    ),
    ManifestSystem(
        id = 23,
        name = "Overdamped pendulum",
        dim = 1,
        u0 = [-2.74],
        tspan = (0.0, 25.0),
        T = 250,
        true_structure = "du1 = 0.21 - sin(u1)",
        representability = :surrogate,
        expected_stage = 5
    ),
    ManifestSystem(
        id = 24,
        name = "Harmonic oscillator",
        dim = 2,
        u0 = [0.4, -0.03],
        tspan = (0.0, 15.0),
        T = 200,
        true_structure = "du1 = u2 | du2 = -2.1*u1",
        representability = :exact,
        expected_stage = 1
    ),
    ManifestSystem(
        id = 26,
        name = "Lotka-Volterra competition",
        dim = 2,
        u0 = [5.0, 4.3],
        tspan = (0.0, 10.0),
        T = 200,
        true_structure = "du1 = 3*u1 - u1^2 - 2*u1*u2 | du2 = 2*u2 - u1*u2 - u2^2",
        representability = :exact,
        expected_stage = 3
    ),
    ManifestSystem(
        id = 31,
        name = "SIR model",
        dim = 2,
        u0 = [7.2, 0.98],
        tspan = (0.0, 20.0),
        T = 200,
        true_structure = "du1 = -0.4*u1*u2 | du2 = 0.4*u1*u2 - 0.314*u2",
        representability = :exact,
        expected_stage = 3
    ),
    ManifestSystem(
        id = 37,
        name = "Van der Pol oscillator",
        dim = 2,
        u0 = [2.2, 0.0],
        tspan = (0.0, 20.0),
        T = 200,
        true_structure = "du1 = u2 | du2 = -u1 + 0.43*u2 - 0.43*u1^2*u2",
        representability = :surrogate,
        expected_stage = 4
    ),
    ManifestSystem(
        id = 54,
        name = "Lorenz (periodic)",
        dim = 3,
        u0 = [2.3, 8.1, 12.4],
        tspan = (0.0, 15.0),
        T = 300,
        true_structure = "du1 = -5.1*u1 + 5.1*u2 | du2 = 12*u1 - u2 - u1*u3 | du3 = u1*u2 - 1.67*u3",
        representability = :exact,
        expected_stage = 3
    ),
    ManifestSystem(
        id = 63,
        name = "SEIR model",
        dim = 4,
        u0 = [0.6, 0.3, 0.09, 0.01],
        tspan = (0.0, 30.0),
        T = 300,
        true_structure = "du1 = -0.28*u1*u3 | du2 = 0.28*u1*u3 - 0.47*u2 | du3 = 0.47*u2 - 0.30*u3 | du4 = 0.30*u3",
        representability = :exact,
        expected_stage = 3
    )
]

const VARIANTS = ManifestVariant[
    ManifestVariant(
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
            usage = StageUsagePolicy(mode = :hard, new_term_bias_prob = SOFT_BIAS),
            use_pretuning = true
        )
    ),
    ManifestVariant(
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
            usage = StageUsagePolicy(mode = :hard, new_term_bias_prob = SOFT_BIAS),
            use_pretuning = true
        )
    ),
    ManifestVariant(
        "EvoGrow v2.2 progression-only",
        "evogrow_v2_2_stage_local",
        :evogrow,
        dim -> EvoGrow(
            pop_size = POP_SIZE,
            n_levels = EVO_LEVELS,
            children_per_parent = 2,
            max_terms_per_eq = 6,
            λ = 1e-3,
            progression = StageProgressionPolicy(mode = :stage_local, min_levels_per_stage = STAGE_MIN_LEVELS),
            usage = StageUsagePolicy(mode = :hard, new_term_bias_prob = SOFT_BIAS),
            use_pretuning = true
        )
    ),
    ManifestVariant(
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
            usage = StageUsagePolicy(mode = :passive, new_term_bias_prob = SOFT_BIAS),
            use_pretuning = true
        )
    ),
    ManifestVariant(
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
            usage = StageUsagePolicy(mode = :soft, new_term_bias_prob = SOFT_BIAS),
            use_pretuning = true
        )
    ),
    ManifestVariant(
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
        )
    )
]

# ============================================================
# Helpers
# ============================================================

function iso_timestamp()
    return Dates.format(now(), dateformat"yyyy-mm-ddTHH:MM:SS")
end

function current_git_hash()
    try
        return strip(read(`git rev-parse HEAD`, String))
    catch
        return "unknown"
    end
end

function write_json(path::String, obj)
    open(path, "w") do io
        JSON3.write(io, obj)
    end
    return path
end

function run_id_for(sys::ManifestSystem, variant::ManifestVariant, seed::Int)
    return "$(sys.id)_$(variant.slug)_seed$(seed)"
end

function bfgs_config()
    return Dict(
        "bfgs_maxiters" => BFGS_MAXITERS,
        "bfgs_abstol" => BFGS_ABSTOL,
        "bfgs_reltol" => BFGS_RELTOL,
        "bfgs_maxiters_solve" => BFGS_MAXITERS_SOLVE,
        "bfgs_max_loss_evals" => BFGS_MAX_LOSS_EVALS,
        "bfgs_clamp_val" => BFGS_CLAMP_VAL
    )
end

function algorithm_parameters(strategy)
    if strategy isa EvoGrow
        params = Dict(
            "pop_size" => strategy.pop_size,
            "n_levels" => strategy.n_levels,
            "children_per_parent" => strategy.children_per_parent,
            "max_terms_per_eq" => strategy.max_terms_per_eq,
            "lambda" => getproperty(strategy, :λ),
            "progression_mode" => String(strategy.progression.mode),
            "min_levels_per_stage" => strategy.progression.min_levels_per_stage,
            "usage_mode" => String(strategy.usage.mode),
            "new_term_bias_prob" => strategy.usage.new_term_bias_prob,
            "use_pretuning" => strategy.use_pretuning
        )
        merge!(params, bfgs_config())
        return params
    end

    params = Dict(
        "pop_size" => getproperty(strategy, :pop_size),
        "n_levels" => getproperty(strategy, :n_generations),
        "children_per_parent" => nothing,
        "max_terms_per_eq" => getproperty(strategy, :max_terms_per_eq),
        "lambda" => getproperty(strategy, :λ),
        "progression_mode" => nothing,
        "min_levels_per_stage" => nothing,
        "usage_mode" => nothing,
        "new_term_bias_prob" => nothing,
        "use_pretuning" => nothing
    )
    merge!(params, bfgs_config())
    return params
end

# ============================================================
# Main
# ============================================================

created_at = iso_timestamp()
git_hash = current_git_hash()

experiments_root = joinpath(@__DIR__)
experiment_dir = joinpath(experiments_root, EXPERIMENT_ID)
manifest_path = joinpath(experiment_dir, "manifest.json")
runs_root = joinpath(experiment_dir, "runs")

if isfile(manifest_path)
    error("Refusing to overwrite existing manifest at $(manifest_path)")
end

mkpath(experiment_dir)

notes_path = joinpath(experiment_dir, "notes.md")
open(notes_path, "w") do io
    println(io, "<!-- $(EXPERIMENT_ID) created $(created_at) -->")
end

run_specs = NamedTuple[]
run_ids = String[]
for sys in SYSTEMS
    for variant in VARIANTS
        for seed in SEEDS
            run_id = run_id_for(sys, variant, seed)
            push!(run_ids, run_id)
            push!(run_specs, (run_id = run_id, system = sys, variant = variant, seed = seed))
        end
    end
end

manifest_obj = Dict(
    "experiment_id" => EXPERIMENT_ID,
    "phase" => PHASE,
    "hypothesis" => HYPOTHESIS,
    "run_type" => RUN_TYPE,
    "include_in_paper" => INCLUDE_IN_PAPER,
    "created_at" => created_at,
    "git_hash" => git_hash,
    "n_systems" => length(SYSTEMS),
    "n_variants" => length(VARIANTS),
    "n_seeds" => length(SEEDS),
    "n_runs_total" => length(run_specs),
    "run_ids" => run_ids
)
write_json(manifest_path, manifest_obj)

mkpath(runs_root)

for spec in run_specs
    sys = spec.system
    variant = spec.variant
    strategy = variant.build_strategy(sys.dim)

    run_dir = joinpath(runs_root, spec.run_id)
    mkpath(run_dir)

    config_obj = Dict(
        "run_id" => spec.run_id,
        "experiment_id" => EXPERIMENT_ID,
        "phase" => PHASE,
        "hypothesis" => HYPOTHESIS,
        "run_type" => RUN_TYPE,
        "include_in_paper" => INCLUDE_IN_PAPER,
        "system_id" => sys.id,
        "system_name" => sys.name,
        "system_dim" => sys.dim,
        "system_u0" => sys.u0,
        "system_tspan" => [sys.tspan[1], sys.tspan[2]],
        "system_T" => sys.T,
        "system_true_structure" => sys.true_structure,
        "system_representability" => String(sys.representability),
        "system_expected_stage" => sys.expected_stage,
        "variant" => variant.slug,
        "variant_name" => variant.name,
        "seed" => spec.seed,
        "git_hash" => git_hash
    )

    merge!(config_obj, algorithm_parameters(strategy))

    status_obj = Dict(
        "status" => "queued",
        "success" => nothing,
        "failure_reason" => nothing,
        "failure_detail" => nothing,
        "started_at" => nothing,
        "finished_at" => nothing,
        "git_hash" => git_hash
    )

    write_json(joinpath(run_dir, "config.json"), config_obj)
    write_json(joinpath(run_dir, "status.json"), status_obj)
end

manifest_check = JSON3.read(read(manifest_path, String))
run_dir_count = count(name -> isdir(joinpath(runs_root, name)), readdir(runs_root))

@printf("Experiment ID: %s\n", EXPERIMENT_ID)
@printf("Total runs:    %d\n", length(run_specs))
@printf("Directory:     %s\n", experiment_dir)
@printf("Verification:  run folders=%d | manifest n_runs_total=%d\n",
        run_dir_count,
        Int(manifest_check.n_runs_total))

if run_dir_count != Int(manifest_check.n_runs_total)
    error("Run-folder count mismatch after manifest generation")
end

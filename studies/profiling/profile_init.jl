import Pkg
Pkg.activate(dirname(dirname(@__DIR__)))

using DifferentialEquations
using Dates
using Printf

include(joinpath(dirname(dirname(@__DIR__)), "src", "EvoODE.jl"))
using .EvoODE
include(joinpath(dirname(@__DIR__), "output_path_guard.jl"))

# ============================================================
# Configuration
# ============================================================

const POP_SIZE = 5
const N_LEVELS = 20
const CHILDREN_PER_PARENT = 2
const MAX_TERMS_PER_EQ = 5
const BFGS_MAXITERS = 100
const SEEDS = [42, 123, 7]
const INIT_MODES = [:random, :pretune]
const OUT_DIR = study_resolve_output_dir(joinpath(dirname(dirname(@__DIR__)), "outputs", "studies", "profiling"), ARGS)

# ============================================================
# Local system definitions
# ============================================================

Base.@kwdef struct ProfileSystem
    name::String
    slug::String
    dim::Int
    rhs!::Function
    u0::Vector{Float64}
    tspan::Tuple{Float64,Float64}
    T::Int
end

function rhs_lotka_competition!(du, u, _, _)
    du[1] = u[1] * (3.0 - u[1] - 2.0 * u[2])
    du[2] = u[2] * (2.0 - u[1] - u[2])
end

function rhs_lorenz_periodic!(du, u, _, _)
    sigma = 10.0
    rho = 28.0
    beta = 8.0 / 3.0
    du[1] = sigma * (u[2] - u[1])
    du[2] = u[1] * (rho - u[3]) - u[2]
    du[3] = u[1] * u[2] - beta * u[3]
end

const SYSTEMS = ProfileSystem[
    ProfileSystem(
        name = "Lotka-Volterra competition",
        slug = "lotka_competition",
        dim = 2,
        rhs! = rhs_lotka_competition!,
        u0 = [5.0, 4.3],
        tspan = (0.0, 10.0),
        T = 200
    ),
    ProfileSystem(
        name = "Lorenz periodic",
        slug = "lorenz_periodic",
        dim = 3,
        rhs! = rhs_lorenz_periodic!,
        u0 = [1.0, 1.0, 1.0],
        tspan = (0.0, 5.0),
        T = 200
    )
]

# ============================================================
# Helpers
# ============================================================

function generate_trajectory(sys::ProfileSystem)
    t_grid = collect(range(sys.tspan[1], sys.tspan[2]; length = sys.T))
    prob = ODEProblem(sys.rhs!, copy(sys.u0), sys.tspan, nothing)
    sol = solve(prob, Tsit5(); saveat = t_grid, abstol = 1e-9, reltol = 1e-9)
    return Trajectory(t_grid, Array(sol)')
end

function open_csv_append(path::String, header::String)
    needs_header = !isfile(path) || filesize(path) == 0
    io = open(path, "a")
    if needs_header
        println(io, header)
        flush(io)
    end
    return io
end

function format_stage_level_counts(stage_level_counts)
    isempty(stage_level_counts) && return ""
    return join(stage_level_counts, "|")
end

function format_float_or_na(x)
    return isfinite(x) ? @sprintf("%.6e", x) : "NA"
end

function format_elapsed(x)
    return isfinite(x) ? @sprintf("%.4f", x) : "NA"
end

function summary_csv_line(system_name::String,
                          seed::Int,
                          init_mode::Symbol,
                          result,
                          elapsed_s::Float64)
    meta = result.meta.structure
    final_stage = haskey(meta, :final_stage) ? meta.final_stage : -1
    termination_reason = haskey(meta, :termination_reason) ? string(meta.termination_reason) : "unknown"
    total_loss_evals = haskey(meta, :total_loss_evals) ? meta.total_loss_evals : -1
    total_invalid_evals = haskey(meta, :total_invalid_evals) ? meta.total_invalid_evals : -1
    stage_level_counts = haskey(meta, :stage_level_counts) ? meta.stage_level_counts : Int[]

    return join([
        "\"$(system_name)\"",
        string(seed),
        string(init_mode),
        format_float_or_na(result.loss),
        format_float_or_na(result.objective),
        string(final_stage),
        "\"$(termination_reason)\"",
        string(total_loss_evals),
        string(total_invalid_evals),
        "\"$(format_stage_level_counts(stage_level_counts))\"",
        format_elapsed(elapsed_s)
    ], ";")
end

function level_csv_lines(system_name::String,
                         seed::Int,
                         init_mode::Symbol,
                         level_log)
    lines = String[]
    for entry in level_log
        push!(lines, join([
            "\"$(system_name)\"",
            string(seed),
            string(init_mode),
            string(entry.level),
            string(entry.stage),
            format_float_or_na(entry.best_loss),
            format_float_or_na(entry.best_objective),
            string(entry.n_params),
            format_elapsed(entry.elapsed_s)
        ], ";"))
    end
    return lines
end

# ============================================================
# Main experiment
# ============================================================

mkpath(OUT_DIR)
_log_io = open(joinpath(OUT_DIR, "run.log"), "a")

function log_println(msg::String)
    println(msg)
    println(_log_io, msg)
    flush(_log_io)
end

macro logf(fmt, args...)
    return esc(:(log_println(@sprintf($fmt, $(args...)))))
end

log_println("=== Started at $(Dates.format(now(), "yyyy-mm-dd HH:MM:SS")) ===")
set_level(INFO)

summary_path = joinpath(OUT_DIR, "profile_init_summary.csv")
levels_path = joinpath(OUT_DIR, "profile_init_levels.csv")

summary_io = open_csv_append(
    summary_path,
    "system;seed;init_mode;final_loss;final_objective;final_stage;termination_reason;total_loss_evals;total_invalid_evals;stage_level_counts;elapsed_s"
)

levels_io = open_csv_append(
    levels_path,
    "system;seed;init_mode;level;stage;best_loss;best_objective;n_params;elapsed_s"
)

trajectories = Dict(sys.slug => generate_trajectory(sys) for sys in SYSTEMS)

log_println("Running pretuning profiling experiment...")
log_println("Systems=$(length(SYSTEMS)) | Seeds=$(length(SEEDS)) | Init modes=$(length(INIT_MODES))")
log_println("Output directory: $OUT_DIR")

try
    for sys in SYSTEMS
        traj = trajectories[sys.slug]
        basis = default_staged_polynomial_basis(sys.dim)

        for seed in SEEDS
            for init_mode in INIT_MODES
                use_pretuning = init_mode == :pretune
                log_file = joinpath(OUT_DIR, @sprintf("profile_%s_seed%d_%s.log", sys.slug, seed, String(init_mode)))

                log_println("")
                @logf("[%s] seed=%d | init=%s", sys.name, seed, String(init_mode))

                set_log_file(log_file)
                reset_timer()

                result = nothing
                elapsed_s = NaN

                try
                    t0 = time()
                    result = discover(
                        traj;
                        structure = EvoGrow(
                            pop_size = POP_SIZE,
                            n_levels = N_LEVELS,
                            children_per_parent = CHILDREN_PER_PARENT,
                            max_terms_per_eq = MAX_TERMS_PER_EQ,
                            use_pretuning = use_pretuning,
                            progression = StageProgressionPolicy(mode = :stage_local, min_levels_per_stage = 2),
                            usage = StageUsagePolicy(mode = :hard, new_term_bias_prob = 0.75)
                        ),
                        optimizer = BFGSOptimizer(maxiters = BFGS_MAXITERS),
                        basis = basis,
                        loss = MSELoss(),
                        options = DiscoveryOptions(
                            rng_seed = seed,
                            verbose = 1,
                            min_levels = 2,
                            max_levels = 50,
                            loss_tol = 1e-8,
                            plateau_window = 3,
                            plateau_tol = 1e-4,
                            plateau_relative = false,
                            plateau_rtol = 1e-3
                        )
                    )
                    elapsed_s = time() - t0
                finally
                    close_log_file()
                end

                println(summary_io, summary_csv_line(sys.name, seed, init_mode, result, elapsed_s))
                flush(summary_io)

                for line in level_csv_lines(sys.name, seed, init_mode, result.meta.structure.level_log)
                    println(levels_io, line)
                end
                flush(levels_io)

                @logf("  final_loss=%.4e | final_stage=%d | elapsed=%.2fs",
                        result.loss,
                        result.meta.structure.final_stage,
                        elapsed_s)
                log_println("  log=$(log_file)")
            end
        end
    end
finally
    close(summary_io)
    close(levels_io)
end

log_println("")
log_println("Pretuning profiling experiment finished.")
log_println("Summary CSV: $summary_path")
log_println("Levels CSV:  $levels_path")
log_println("=== Finished at $(Dates.format(now(), "yyyy-mm-dd HH:MM:SS")) ===")
close(_log_io)

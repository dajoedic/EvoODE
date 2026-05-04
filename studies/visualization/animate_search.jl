using Pkg
Pkg.activate(joinpath(@__DIR__, "..", ".."))
using EvoODE
import EvoODE: _simulate_candidate
using DifferentialEquations
using Printf

# ============================================================
# DEMO CONFIGURATION
# ============================================================
const DEMO_SYSTEM = :lorenz_3d
const RUN_ID = "lorenz_stage_animation"
const FPS = 10
const FRAME_WIDTH = 1920
const FRAME_HEIGHT = 1080
const MAX_CANDIDATES_PER_LEVEL = nothing
const CLEAR_ON_STAGE_TRANSITION = true
const QUICK_TEST = false

function make_demo_system(name::Symbol)
    if name == :logistic
        dim = 1
        var_names = ["u"]
        u0 = [0.1]
        t_grid = range(0.0, 10.0, length = 100)
        system_label = "Logistic Growth"
        true_equations = "du/dt = 0.79*u - 0.0106*u^2"
        ode! = (du, u, p, t) -> (du[1] = 0.79 * u[1] - 0.0106 * u[1]^2; nothing)
    elseif name == :sir_2d
        dim = 2
        var_names = ["S", "I"]
        u0 = [0.99, 0.01]
        t_grid = range(0.0, 30.0, length = 150)
        system_label = "SIR Model"
        true_equations = "dS/dt = -0.4*S*I\ndI/dt =  0.4*S*I - 0.314*I"
        ode! = (du, u, p, t) -> (du[1] = -0.4 * u[1] * u[2];
                                  du[2] =  0.4 * u[1] * u[2] - 0.314 * u[2]; nothing)
    elseif name == :lotka_volterra
        dim = 2
        var_names = ["x", "y"]
        u0 = [0.9, 0.9]
        t_grid = range(0.0, 10.0, length = 100)
        system_label = "Lotka-Volterra"
        true_equations = "dx/dt = 3*x - x^2 - 2*x*y\ndy/dt = 2*y - x*y - y^2"
        ode! = (du, u, p, t) -> (du[1] = 3.0 * u[1] - u[1]^2 - 2.0 * u[1] * u[2];
                                  du[2] = 2.0 * u[2] - u[1] * u[2] - u[2]^2; nothing)
    elseif name == :lorenz_3d
        dim = 3
        var_names = ["x", "y", "z"]
        u0 = [2.3, 8.1, 12.4]
        t_grid = range(0.0, 15.0, length = 300)
        system_label = "Lorenz 3D"
        true_equations = "dx/dt =  5.1*(y - x)\ndy/dt = 12*x - y - x*z\ndz/dt =  x*y - 1.67*z"
        ode! = (du, u, p, t) -> (du[1] =  5.1 * (u[2] - u[1]);
                                  du[2] = 12.0 * u[1] - u[2] - u[1] * u[3];
                                  du[3] =  u[1] * u[2] - 1.67 * u[3]; nothing)
    else
        error("Unknown demo system: $name")
    end

    prob = ODEProblem(ode!, u0, (t_grid[1], t_grid[end]), nothing)
    sol = solve(prob, Tsit5(); saveat = collect(t_grid), abstol = 1e-9, reltol = 1e-9)
    traj = Trajectory(collect(t_grid), Array(sol)')

    return (
        traj = traj,
        dim = dim,
        var_names = var_names,
        true_equations = true_equations,
        system_label = system_label,
    )
end

# ============================================================
# DEMO SETTINGS - NOT Paper 1 settings
# ============================================================
function make_demo_config(dim::Int)
    basis = default_staged_polynomial_basis(dim)
    if QUICK_TEST
        strategy = EvoGrow(
            pop_size = 5,
            n_levels = 5,
            children_per_parent = 2,
            max_terms_per_eq = 3,
            λ = 1e-3,
            progression = StageProgressionPolicy(
                mode = :stage_local,
                min_levels_per_stage = 2,
            ),
            usage = StageUsagePolicy(mode = :hard),
            use_pretuning = true,
        )
        optimizer = BFGSOptimizer(maxiters = 50, time_limit_s = 10.0)
    else
        strategy = EvoGrow(
            pop_size = 10,
            n_levels = 30,
            children_per_parent = 3,
            max_terms_per_eq = 5,
            λ = 1e-3,
            progression = StageProgressionPolicy(
                mode = :stage_local,
                min_levels_per_stage = 3,
            ),
            usage = StageUsagePolicy(mode = :hard),
            use_pretuning = true,
        )
        optimizer = BFGSOptimizer(maxiters = 200, time_limit_s = 120.0)
    end
    loss_fn = MSELoss()
    options = DiscoveryOptions(
        rng_seed = 42,
        verbose = 1,
        min_levels = 3,
        max_levels = 60,
        loss_tol = 1e-10,
        plateau_window = 3,
        plateau_tol = 1e-4,
    )
    return basis, strategy, optimizer, loss_fn, options
end

out_root = joinpath(@__DIR__, "..", "..", "outputs", "studies", "visualization", RUN_ID)
frames_dir = joinpath(out_root, "frames")
mkpath(frames_dir)

demo = make_demo_system(DEMO_SYSTEM)
t_start = time()
frame_title = "EvoGrow - $(demo.system_label)"
basis, strategy, optimizer, loss_fn, options = make_demo_config(demo.dim)

accumulated_candidates = Matrix{Float64}[]
frame_count = Ref(0)
n_skipped_live = Ref(0)

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
        output_dir = frames_dir,
        var_names = demo.var_names,
        true_equations = demo.true_equations,
        title = frame_title,
        elapsed_s = time() - t_start,
        frame_width = FRAME_WIDTH,
        frame_height = FRAME_HEIGHT,
    )
    println("  Frame $(frame_count[]) - Level $(snapshot.level), Stage $(snapshot.stage), Loss $(@sprintf("%.3g", snapshot.best_loss))")

    append!(accumulated_candidates, current_level_candidates)
end

strategy = EvoGrow(
    pop_size = strategy.pop_size,
    n_levels = strategy.n_levels,
    children_per_parent = strategy.children_per_parent,
    max_terms_per_eq = strategy.max_terms_per_eq,
    λ = strategy.λ,
    progression = strategy.progression,
    usage = strategy.usage,
    use_pretuning = strategy.use_pretuning,
    level_callback = on_level,
)

println("Running EvoGrow on $DEMO_SYSTEM ...")
result = discover(
    demo.traj;
    structure = strategy,
    optimizer = optimizer,
    basis = basis,
    loss = loss_fn,
    options = options,
)

vis_history = result.meta.structure.vis_history
println("Search done. Levels: $(length(vis_history)), final loss: $(result.loss)")

println("Frames live gerendert: $(frame_count[]) Frames. Skipped simulations: $(n_skipped_live[])")

mp4_path = joinpath(out_root, "search_animation.mp4")
mp4_created = false

if Sys.which("ffmpeg") !== nothing
    println("Running ffmpeg ...")
    run(`ffmpeg -y -framerate $FPS -i $(joinpath(frames_dir, "frame_%04d.png")) -c:v libx264 -pix_fmt yuv420p $mp4_path`)
    global mp4_created = true
    println("MP4 saved: $mp4_path")
else
    println("ffmpeg not found - frames saved to $frames_dir")
    println("Manual command:")
    println("  ffmpeg -y -framerate $FPS -i '$(joinpath(frames_dir, "frame_%04d.png"))' \\")
    println("    -c:v libx264 -pix_fmt yuv420p '$mp4_path'")
end

n_stages = maximum(s.stage for s in vis_history; init = 1)
n_transitions = count(s.stage_transition for s in vis_history)
final_struct = structure_to_string(
    result.structure,
    basis,
    result.params;
    var_names = demo.var_names,
)

summary_path = joinpath(out_root, "summary.txt")
open(summary_path, "w") do io
    println(io, "Demo system:           $DEMO_SYSTEM")
    println(io, "Run ID:                $RUN_ID")
    println(io, "Seed:                  $(options.rng_seed)")
    println(io, "Levels rendered:       $(frame_count[])")
    println(io, "Stages reached:        $n_stages")
    println(io, "Stage transitions:     $n_transitions")
    println(io, "Final loss:            $(result.loss)")
    println(io, "Frames directory:      $frames_dir")
    println(io, "MP4 created:           $mp4_created")
    println(io, "Skipped simulations:   $(n_skipped_live[])")
    println(io, "")
    println(io, "Final structure:")
    println(io, final_struct)
end
println("Summary written to $summary_path")

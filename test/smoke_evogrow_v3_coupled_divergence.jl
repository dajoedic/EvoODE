include(joinpath(@__DIR__, "..", "src", "EvoODE.jl"))
using .EvoODE

struct FastDerivativeOptimizer <: EvoODE.AbstractOptimizer end

function EvoODE.fit_parameters(
    ::FastDerivativeOptimizer,
    f!::Function,
    traj::Trajectory,
    n_params::Int,
    loss::EvoODE.AbstractLoss,
    options::DiscoveryOptions;
    p0 = nothing
)
    params = p0 === nothing ? zeros(n_params) : Vector{Float64}(p0)
    if length(params) != n_params
        params = zeros(n_params)
    end

    dX = EvoODE.estimate_derivatives(traj)
    T, dim = size(traj.x)
    du = zeros(Float64, dim)
    residual = 0.0
    for row in 1:T
        f!(du, view(traj.x, row, :), params, traj.t[row])
        residual += sum(abs2, dX[row, :] .- du)
    end
    residual /= T * dim

    return params, residual, (
        optimizer = :fast_derivative,
        loss_evals = 1,
        invalid_evals = 0,
        ode_solves = 0,
        invalid_solves = 0,
        diverged_solves = 0,
        nonfinite_solves = 0,
        step_limit_solves = 0,
        solver_unstable_solves = 0,
        optimizer_limit_hits = 0,
        optimizer_iteration_limit_hits = 0,
        optimizer_safety_limit_hits = 0,
        optimizer_failure_hits = 0,
        optimizer_unknown_retcode_hits = 0,
        fit_time_s = 0.0,
        solve_time_s = 0.0,
        solver_retcodes = String[],
        optimizer_retcodes = String["Success"],
    )
end

function _synthetic_coupled_trajectory()
    t = collect(range(0.0, 1.0; length = 25))
    u1 = exp.(-0.5 .* t)
    u2 = 1.0 ./ (1.0 .+ t)
    return Trajectory(t, hcat(u1, u2))
end

traj = _synthetic_coupled_trajectory()
strategy = EvoGrowV3(
    pop_size = 4,
    n_levels = 5,
    children_per_parent = 1,
    max_terms_per_eq = 4,
    progression = StageProgressionPolicy(mode = :stage_local, min_levels_per_stage = 2),
    usage = StageUsagePolicy(mode = :hard),
    use_pretuning = true,
)
options = DiscoveryOptions(
    rng_seed = 42,
    verbose = 0,
    min_levels = 2,
    max_levels = 5,
    loss_tol = 1e-4,
    plateau_window = 2,
    plateau_tol = 1e-3,
)

result = discover(
    traj;
    structure = strategy,
    optimizer = FastDerivativeOptimizer(),
    basis = default_staged_polynomial_basis(2),
    loss = MSELoss(),
    options = options,
)

meta = result.meta.structure
expected_stage = 1
local_eq_overshoot = eq_overshoot(meta.eq_final_stages, expected_stage)
local_eq_wasted_levels = eq_wasted_levels(meta.eq_stage_histories, expected_stage)

if length(unique(meta.eq_final_stages)) == 1
    error("EvoGrowV3 coupled smoke did not diverge: eq_final_stages=$(meta.eq_final_stages)")
end
if maximum(local_eq_overshoot) != max(0, maximum(meta.eq_final_stages) - expected_stage)
    error("eq_overshoot is inconsistent with final_stage")
end
for k in eachindex(meta.eq_stage_histories)
    expected = count(stage -> stage > expected_stage, meta.eq_stage_histories[k])
    if local_eq_wasted_levels[k] != expected
        error("eq_wasted_levels mismatch for equation $k")
    end
end

println(
    "coupled_divergence: loss=", result.loss,
    " final_stage=", meta.final_stage,
    " eq_final_stages=", meta.eq_final_stages,
    " eq_overshoot=", local_eq_overshoot,
    " eq_wasted_levels=", local_eq_wasted_levels,
    " eq_stage_histories=", meta.eq_stage_histories,
    " structure=", result.structure.active_idxs
)

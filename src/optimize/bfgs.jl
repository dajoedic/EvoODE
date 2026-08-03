# src/optimize/bfgs.jl

using DifferentialEquations
using SciMLBase
using Optimization, OptimizationOptimJL
using Logging
using Random

"""
    BFGSOptimizer(; maxiters=300, abstol=1e-6, reltol=1e-6, maxiters_solve=10^6,
                  clamp_val=10.0, max_loss_evals=typemax(Int), time_limit_s=Inf,
                  reject_nonfinite=false, divergence_limit=Inf)

Parameter optimizer for fixed-structure models.

Deterministic budget parameters:
- `maxiters`: optimizer iteration limit.
- `max_loss_evals`: deterministic objective-evaluation safety budget for one
  parameter fit.
- `abstol`, `reltol`, `maxiters_solve`: ODE solver tolerances and step limit.
- `clamp_val`: deterministic parameter clamp before simulation.
- `reject_nonfinite`, `divergence_limit`: deterministic early-rejection rules.
  When enabled, these are passed through `unstable_check`; relative to the
  solver default, the added condition is the finite `divergence_limit`.

Legacy non-deterministic safety parameter:
- `time_limit_s`: optional wall-clock safety brake passed to Optim.jl. It is
  disabled by default; reproducible result paths should leave it at `Inf`.
"""
Base.@kwdef struct BFGSOptimizer <: AbstractOptimizer
    maxiters::Int = 300
    abstol::Float64 = 1e-6
    reltol::Float64 = 1e-6
    maxiters_solve::Int = 10^6
    clamp_val::Float64 = 10.0
    max_loss_evals::Int = typemax(Int)
    time_limit_s::Float64 = Inf
    reject_nonfinite::Bool = false
    divergence_limit::Float64 = Inf
end

struct BFGSLossEvalBudgetExceeded <: Exception
    limit::Int
    count::Int
end

function _empty_solve_stats()
    return Dict{Symbol, Any}(
        :ode_solves => 0,
        :invalid_solves => 0,
        :diverged_solves => 0,
        :nonfinite_solves => 0,
        :step_limit_solves => 0,
        :solver_unstable_solves => 0,
        :solve_time_s => 0.0,
        :solver_retcodes => String[],
    )
end

function _retcode_string(retcode)
    return string(retcode)
end

function _record_retcode!(stats::Dict{Symbol, Any}, retcode)
    text = _retcode_string(retcode)
    retcodes = stats[:solver_retcodes]
    if !(text in retcodes)
        push!(retcodes, text)
    end
    return nothing
end

function _retcode_is_step_limit(retcode)
    return retcode == SciMLBase.ReturnCode.MaxIters ||
           retcode == SciMLBase.ReturnCode.DtLessThanMin ||
           retcode == SciMLBase.ReturnCode.DtNaN
end

function _retcode_is_unstable(retcode)
    return retcode == SciMLBase.ReturnCode.Unstable ||
           retcode == SciMLBase.ReturnCode.FloatingPointLimit
end

function _state_exceeds_limit(u, divergence_limit::Float64)
    for value in u
        if !isfinite(value)
            return true
        end
        if isfinite(divergence_limit) && abs(value) > divergence_limit
            return true
        end
    end
    return false
end

function _optimizer_retcode_category(retcode)
    if retcode == SciMLBase.ReturnCode.Success ||
       retcode == SciMLBase.ReturnCode.StalledSuccess
        return :success
    elseif retcode == SciMLBase.ReturnCode.MaxTime
        return :safety_limit
    elseif retcode == SciMLBase.ReturnCode.MaxIters
        return :iteration_limit
    elseif retcode in (
        SciMLBase.ReturnCode.ConvergenceFailure,
        SciMLBase.ReturnCode.Failure,
        SciMLBase.ReturnCode.InitialFailure,
        SciMLBase.ReturnCode.InternalLineSearchFailed,
        SciMLBase.ReturnCode.InternalLinearSolveFailed,
        SciMLBase.ReturnCode.Stalled,
    )
        return :failure
    else
        return :unknown
    end
end

"""
    _predict_traj(f!, traj, p, opt; stats = solve_stats)

Returns:
- Ŷ :: Matrix{Float64} with shape (T × dim) on success
- NaN-filled array on failure

No noisy logging here by default. This function is called many times inside the optimizer.
Detailed solve timing is only logged in DEBUG mode.
"""
function _predict_traj(f!,
                       traj::Trajectory,
                       p::Vector{Float64},
                       opt::BFGSOptimizer;
                       stats::Union{Nothing, Dict{Symbol, Any}} = nothing)

    t = traj.t
    X = traj.x
    u0 = collect(X[1, :])
    tspan = (t[1], t[end])

    # Clamp parameters for numerical stability
    p_clamped = Base.clamp.(p, -opt.clamp_val, opt.clamp_val)

    prob = ODEProblem(f!, u0, tspan, p_clamped)

    local sol
    if stats !== nothing
        stats[:ode_solves] += 1
    end
    solve_t0 = time()
    solve_done = nothing
    if current_level() <= DEBUG
        solve_done = time_block(
            "_predict_traj solve",
            level = DEBUG,
            context = Dict(
                :n_params => length(p),
                :t0 => t[1],
                :t1 => t[end]
            )
        )
    end

    try
        sol = with_logger(SimpleLogger(stderr, Logging.Error)) do
            solve_kwargs = (
                saveat = t,
                abstol = opt.abstol,
                reltol = opt.reltol,
                maxiters = opt.maxiters_solve,
                verbose = false,
            )
            if opt.reject_nonfinite
                solve(prob, Tsit5();
                      solve_kwargs...,
                      unstable_check = (_, u, _, _) -> _state_exceeds_limit(u, opt.divergence_limit))
            else
                solve(prob, Tsit5(); solve_kwargs...)
            end
        end
    catch
        if stats !== nothing
            stats[:invalid_solves] += 1
            stats[:solve_time_s] += time() - solve_t0
        end
        if solve_done !== nothing
            solve_done()
        end
        return fill(NaN, size(X))
    end

    if stats !== nothing
        stats[:solve_time_s] += time() - solve_t0
    end

    if solve_done !== nothing
        solve_done()
    end

    if stats !== nothing
        _record_retcode!(stats, sol.retcode)
    end

    if sol.retcode != SciMLBase.ReturnCode.Success
        if stats !== nothing
            stats[:invalid_solves] += 1
            if _retcode_is_unstable(sol.retcode)
                stats[:solver_unstable_solves] += 1
                stats[:diverged_solves] += 1
            elseif _retcode_is_step_limit(sol.retcode)
                stats[:step_limit_solves] += 1
            else
                stats[:diverged_solves] += 1
            end
        end
        return fill(NaN, size(X))
    end

    if length(sol.t) != length(t)
        if stats !== nothing
            stats[:invalid_solves] += 1
            stats[:step_limit_solves] += 1
        end
        return fill(NaN, size(X))
    end

    Yhat = Array(sol)'  # (T x dim)
    if any(!isfinite, Yhat)
        if stats !== nothing
            stats[:nonfinite_solves] += 1
        end
        if opt.reject_nonfinite
            if stats !== nothing
                stats[:invalid_solves] += 1
            end
            return fill(NaN, size(X))
        end
    end
    if opt.reject_nonfinite && _state_exceeds_limit(Yhat, opt.divergence_limit)
        if stats !== nothing
            stats[:invalid_solves] += 1
            stats[:diverged_solves] += 1
        end
        return fill(NaN, size(X))
    end

    return Yhat
end

function fit_parameters(opt::BFGSOptimizer,
                        f!::Function,
                        traj::Trajectory,
                        n_params::Int,
                        loss::AbstractLoss,
                        options::DiscoveryOptions;
                        p0=nothing)

    fit_t0 = time()
    X = traj.x
    p0_use = if p0 === nothing
        0.1 .* randn(n_params)
    elseif length(p0) == n_params
        Vector{Float64}(p0)
    else
        log_warn(
            "Ignoring warm-start parameter vector due to size mismatch",
            context = Dict(
                :expected => n_params,
                :got => length(p0)
            )
        )
        0.1 .* randn(n_params)
    end

    # aggregated diagnostics for this fit
    loss_eval_count = Ref(0)
    invalid_eval_count = Ref(0)
    solve_stats = _empty_solve_stats()
    optimizer_limit_hits = Ref(0)
    optimizer_safety_limit_hits = Ref(0)
    optimizer_eval_budget_limit_hits = Ref(0)
    optimizer_iteration_limit_hits = Ref(0)
    optimizer_failure_hits = Ref(0)
    optimizer_unknown_retcode_hits = Ref(0)
    optimizer_retcodes = String[]

    if options.verbose >= 3
        log_debug(
            "fit_parameters start",
            context = Dict(
                :optimizer => "BFGSOptimizer",
                :n_params => n_params,
                :maxiters => opt.maxiters,
                :abstol => opt.abstol,
                :reltol => opt.reltol,
                :maxiters_solve => opt.maxiters_solve,
                :max_loss_evals => opt.max_loss_evals,
                :clamp_val => opt.clamp_val
            )
        )
    end

    function loss_only(p)
        if loss_eval_count[] >= opt.max_loss_evals
            throw(BFGSLossEvalBudgetExceeded(opt.max_loss_evals, loss_eval_count[]))
        end
        loss_eval_count[] += 1
        Ŷ = _predict_traj(f!, traj, p, opt; stats = solve_stats)

        if any(isnan, Ŷ)
            invalid_eval_count[] += 1
        end

        return evaluate_loss(loss, Ŷ, X)
    end

    loss_fun = OptimizationFunction((p, _) -> loss_only(p), Optimization.AutoFiniteDiff())
    optprob = OptimizationProblem(loss_fun, p0_use)

    p_best = copy(p0_use)
    l_best = 1e6
    method_used = "none"
    retcode_used = "none"

    # -----------------------
    # BFGS attempt
    # -----------------------
    bfgs_done = nothing
    if options.verbose >= 2
        bfgs_done = time_block(
            "BFGS solve",
            level = INFO,
            context = Dict(:n_params => n_params, :maxiters => opt.maxiters)
        )
    end

    try
        res = Optimization.solve(optprob, OptimizationOptimJL.BFGS();
                                 maxiters = opt.maxiters,
                                 time_limit = opt.time_limit_s)
        retcode_text = _retcode_string(res.retcode)
        if !(retcode_text in optimizer_retcodes)
            push!(optimizer_retcodes, retcode_text)
        end
        retcode_category = _optimizer_retcode_category(res.retcode)
        if retcode_category != :success
            optimizer_limit_hits[] += 1
            if retcode_category == :safety_limit
                optimizer_safety_limit_hits[] += 1
            elseif retcode_category == :iteration_limit
                optimizer_iteration_limit_hits[] += 1
            elseif retcode_category == :failure
                optimizer_failure_hits[] += 1
            else
                optimizer_unknown_retcode_hits[] += 1
            end
        end
        if isfinite(res.minimum)
            p_best = res.u
            l_best = res.minimum
            method_used = "BFGS"
            retcode_used = retcode_text

            timed_out = (res.retcode != SciMLBase.ReturnCode.Success)
            if options.verbose >= 2
                if timed_out
                    log_warn(
                        "BFGS hit optimizer limit",
                        context = Dict(
                            :n_params => n_params,
                            :time_limit_s => opt.time_limit_s,
                            :retcode => retcode_text,
                            :minimum => res.minimum,
                            :loss_evals => loss_eval_count[],
                            :invalid_evals => invalid_eval_count[]
                        )
                    )
                else
                    log_info(
                        "BFGS finished",
                        context = Dict(
                            :n_params => n_params,
                            :minimum => res.minimum,
                            :method => method_used,
                            :retcode => retcode_text,
                            :loss_evals => loss_eval_count[],
                            :invalid_evals => invalid_eval_count[]
                        )
                    )
                end
            end
        else
            if options.verbose >= 2
                log_warn(
                    "BFGS returned non-finite minimum",
                    context = Dict(
                        :n_params => n_params,
                        :loss_evals => loss_eval_count[],
                        :invalid_evals => invalid_eval_count[]
                    )
                )
            end
        end
    catch err
        if err isa BFGSLossEvalBudgetExceeded
            optimizer_limit_hits[] += 1
            optimizer_eval_budget_limit_hits[] += 1
            if !("MaxLossEvals" in optimizer_retcodes)
                push!(optimizer_retcodes, "MaxLossEvals")
            end
            method_used = "loss_eval_budget"
            retcode_used = "MaxLossEvals"
            if options.verbose >= 2
                log_warn(
                    "BFGS hit deterministic loss-evaluation budget",
                    context = Dict(
                        :n_params => n_params,
                        :max_loss_evals => opt.max_loss_evals,
                        :loss_evals => loss_eval_count[],
                        :invalid_evals => invalid_eval_count[]
                    )
                )
            end
        else
            if options.verbose >= 2
                log_warn(
                    "BFGS failed, trying Nelder-Mead fallback",
                    context = Dict(
                        :n_params => n_params,
                        :exception_type => typeof(err),
                        :exception => sprint(showerror, err),
                        :loss_evals => loss_eval_count[],
                        :invalid_evals => invalid_eval_count[]
                    )
                )
            end
        end
    end

    if bfgs_done !== nothing
        bfgs_done()
    end

    # -----------------------
    # Nelder-Mead fallback
    # -----------------------
    if method_used == "none"
        nm_done = nothing
        if options.verbose >= 2
            nm_done = time_block(
                "Nelder-Mead solve",
                level = INFO,
                context = Dict(:n_params => n_params, :maxiters => opt.maxiters)
            )
        end

        try
            res2 = Optimization.solve(optprob, OptimizationOptimJL.NelderMead();
                                      maxiters = opt.maxiters,
                                      time_limit = opt.time_limit_s)
            retcode_text2 = _retcode_string(res2.retcode)
            if !(retcode_text2 in optimizer_retcodes)
                push!(optimizer_retcodes, retcode_text2)
            end
            retcode_category2 = _optimizer_retcode_category(res2.retcode)
            if retcode_category2 != :success
                optimizer_limit_hits[] += 1
                if retcode_category2 == :safety_limit
                    optimizer_safety_limit_hits[] += 1
                elseif retcode_category2 == :iteration_limit
                    optimizer_iteration_limit_hits[] += 1
                elseif retcode_category2 == :failure
                    optimizer_failure_hits[] += 1
                else
                    optimizer_unknown_retcode_hits[] += 1
                end
            end
            if isfinite(res2.minimum)
                p_best = res2.u
                l_best = res2.minimum
                method_used = "NelderMead"
                retcode_used = retcode_text2

                if options.verbose >= 2
                    timed_out2 = (res2.retcode != SciMLBase.ReturnCode.Success)
                    if timed_out2
                        log_warn(
                            "Nelder-Mead hit optimizer limit",
                            context = Dict(
                                :n_params => n_params,
                                :time_limit_s => opt.time_limit_s,
                                :retcode => retcode_text2,
                                :minimum => res2.minimum,
                                :loss_evals => loss_eval_count[],
                                :invalid_evals => invalid_eval_count[]
                            )
                        )
                    else
                        log_info(
                            "Nelder-Mead finished",
                            context = Dict(
                                :n_params => n_params,
                                :minimum => res2.minimum,
                                :method => method_used,
                                :retcode => retcode_text2,
                                :loss_evals => loss_eval_count[],
                                :invalid_evals => invalid_eval_count[]
                            )
                        )
                    end
                end
            else
                if options.verbose >= 2
                    log_warn(
                        "Nelder-Mead returned non-finite minimum",
                        context = Dict(
                            :n_params => n_params,
                            :loss_evals => loss_eval_count[],
                            :invalid_evals => invalid_eval_count[]
                        )
                    )
                end
            end
        catch err
            if err isa BFGSLossEvalBudgetExceeded
                optimizer_limit_hits[] += 1
                optimizer_eval_budget_limit_hits[] += 1
                if !("MaxLossEvals" in optimizer_retcodes)
                    push!(optimizer_retcodes, "MaxLossEvals")
                end
                method_used = "loss_eval_budget"
                retcode_used = "MaxLossEvals"
                if options.verbose >= 2
                    log_warn(
                        "Nelder-Mead hit deterministic loss-evaluation budget",
                        context = Dict(
                            :n_params => n_params,
                            :max_loss_evals => opt.max_loss_evals,
                            :loss_evals => loss_eval_count[],
                            :invalid_evals => invalid_eval_count[]
                        )
                    )
                end
            else
                method_used = "failed"
                if options.verbose >= 2
                    log_error(
                        "Nelder-Mead failed",
                        context = Dict(
                            :n_params => n_params,
                            :exception_type => typeof(err),
                            :exception => sprint(showerror, err),
                            :loss_evals => loss_eval_count[],
                            :invalid_evals => invalid_eval_count[]
                        )
                    )
                end
            end
        end

        if nm_done !== nothing
            nm_done()
        end
    end

    # Ensure returned params match the ones actually evaluated in the loss
    p_best = Base.clamp.(p_best, -opt.clamp_val, opt.clamp_val)

    # aggregated warning only once per fit
    if options.verbose >= 2 && invalid_eval_count[] > 0
        log_warn(
            "Invalid trajectory evaluations occurred during fit",
            context = Dict(
                :n_params => n_params,
                :method => method_used,
                :invalid_evals => invalid_eval_count[],
                :loss_evals => loss_eval_count[],
                :best_loss => l_best
            )
        )
    end

    if options.verbose >= 3
        log_debug(
            "fit_parameters result",
            context = Dict(
                :method => method_used,
                :best_loss => l_best,
                :n_params => n_params,
                :loss_evals => loss_eval_count[],
                :invalid_evals => invalid_eval_count[]
            )
        )
    end

    return p_best, l_best, (
        method = method_used,
        retcode = retcode_used,
        loss_evals = loss_eval_count[],
        invalid_evals = invalid_eval_count[],
        ode_solves = Int(solve_stats[:ode_solves]),
        invalid_solves = Int(solve_stats[:invalid_solves]),
        diverged_solves = Int(solve_stats[:diverged_solves]),
        nonfinite_solves = Int(solve_stats[:nonfinite_solves]),
        step_limit_solves = Int(solve_stats[:step_limit_solves]),
        solver_unstable_solves = Int(solve_stats[:solver_unstable_solves]),
        optimizer_limit_hits = optimizer_limit_hits[],
        optimizer_iteration_limit_hits = optimizer_iteration_limit_hits[],
        optimizer_safety_limit_hits = optimizer_safety_limit_hits[],
        optimizer_eval_budget_limit_hits = optimizer_eval_budget_limit_hits[],
        optimizer_failure_hits = optimizer_failure_hits[],
        optimizer_unknown_retcode_hits = optimizer_unknown_retcode_hits[],
        solver_retcodes = copy(solve_stats[:solver_retcodes]),
        optimizer_retcodes = copy(optimizer_retcodes),
        solve_time_s = Float64(solve_stats[:solve_time_s]),
        fit_time_s = time() - fit_t0
    )
end

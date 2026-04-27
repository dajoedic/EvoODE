# src/optimize/bfgs.jl

using DifferentialEquations
using SciMLBase
using Optimization, OptimizationOptimJL
using Logging
using Random

"""
    BFGSOptimizer(; maxiters=300, abstol=1e-6, reltol=1e-6, maxiters_solve=10^6, clamp_val=10.0, time_limit_s=300.0)

Parameter optimizer for fixed-structure models.

Uses:
  - DifferentialEquations.jl to simulate the ODE
  - Optimization.jl (with AutoFiniteDiff) for gradients
  - BFGS (and NelderMead as fallback) for optimization

`time_limit_s` sets a wall-clock ceiling per `fit_parameters` call (passed to Optim.jl).
When the limit is hit, Optim returns the best result found so far rather than throwing.
The default (300s) is ~100× the median per-call time and only fires on runaway solves.
"""
Base.@kwdef struct BFGSOptimizer <: AbstractOptimizer
    maxiters::Int = 300
    abstol::Float64 = 1e-6
    reltol::Float64 = 1e-6
    maxiters_solve::Int = 10^6
    clamp_val::Float64 = 10.0
    time_limit_s::Float64 = 300.0
end

"""
    _predict_traj(f!, traj, p, opt)

Returns:
- Ŷ :: Matrix{Float64} with shape (T × dim) on success
- NaN-filled array on failure

No noisy logging here by default. This function is called many times inside the optimizer.
Detailed solve timing is only logged in DEBUG mode.
"""
function _predict_traj(f!,
                       traj::Trajectory,
                       p::Vector{Float64},
                       opt::BFGSOptimizer)

    t = traj.t
    X = traj.x
    u0 = collect(X[1, :])
    tspan = (t[1], t[end])

    # Clamp parameters for numerical stability
    p_clamped = Base.clamp.(p, -opt.clamp_val, opt.clamp_val)

    prob = ODEProblem(f!, u0, tspan, p_clamped)

    local sol
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
            solve(prob, Tsit5();
                  saveat   = t,
                  abstol   = opt.abstol,
                  reltol   = opt.reltol,
                  maxiters = opt.maxiters_solve,
                  verbose  = false)
        end
    catch
        if solve_done !== nothing
            solve_done()
        end
        return fill(NaN, size(X))
    end

    if solve_done !== nothing
        solve_done()
    end

    if sol.retcode != SciMLBase.ReturnCode.Success || length(sol.t) != length(t)
        return fill(NaN, size(X))
    end

    return Array(sol)'  # (T × dim)
end

function fit_parameters(opt::BFGSOptimizer,
                        f!::Function,
                        traj::Trajectory,
                        n_params::Int,
                        loss::AbstractLoss,
                        options::DiscoveryOptions;
                        p0=nothing)

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
                :clamp_val => opt.clamp_val
            )
        )
    end

    function loss_only(p)
        loss_eval_count[] += 1
        Ŷ = _predict_traj(f!, traj, p, opt)

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
        if isfinite(res.minimum)
            p_best = res.u
            l_best = res.minimum
            method_used = "BFGS"

            timed_out = (res.retcode != SciMLBase.ReturnCode.Success)
            if options.verbose >= 2
                if timed_out
                    log_warn(
                        "BFGS hit time_limit",
                        context = Dict(
                            :n_params => n_params,
                            :time_limit_s => opt.time_limit_s,
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
            if isfinite(res2.minimum)
                p_best = res2.u
                l_best = res2.minimum
                method_used = "NelderMead"

                if options.verbose >= 2
                    timed_out2 = (res2.retcode != SciMLBase.ReturnCode.Success)
                    if timed_out2
                        log_warn(
                            "Nelder-Mead hit time_limit",
                            context = Dict(
                                :n_params => n_params,
                                :time_limit_s => opt.time_limit_s,
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
        loss_evals = loss_eval_count[],
        invalid_evals = invalid_eval_count[]
    )
end

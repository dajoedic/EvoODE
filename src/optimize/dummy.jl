# src/optimize/dummy.jl

"""
    DummyOptimizer()

Placeholder optimizer for pipeline testing.

Does not optimize — returns zero parameters and evaluates the resulting loss.
Useful for smoke-testing the full `discover()` pipeline without running BFGS.
"""
struct DummyOptimizer <: AbstractOptimizer end

"""
    fit_parameters(::DummyOptimizer, f!, traj, n_params, loss, options)

Returns zero-initialized parameters of length `n_params` and evaluates the loss
on the resulting (typically constant) trajectory.
"""
function fit_parameters(::DummyOptimizer,
                        f!::Function,
                        traj::Trajectory,
                        n_params::Int,
                        loss::AbstractLoss,
                        options::DiscoveryOptions)

    params = zeros(n_params)
    Ŷ = simulate(f!, params, traj; options=options)
    l = evaluate_loss(loss, Ŷ, traj.x)

    return params, l, (optimizer = :dummy,)
end

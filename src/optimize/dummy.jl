# src/optimize/dummy.jl

"""
    DummyOptimizer()

Placeholder optimizer.
Does not optimize – returns zero parameters.
"""
struct DummyOptimizer <: AbstractOptimizer end

"""
    fit_parameters(::DummyOptimizer, model_builder, traj; loss, options, init_params)
"""
function fit_parameters(::DummyOptimizer,
                        model_builder,
                        traj::Trajectory;
                        loss,
                        options,
                        init_params = nothing)

    # One dummy parameter
    p = zeros(1)

    Ŷ = model_builder(p, traj)
    l = evaluate_loss(loss, Ŷ, traj.x)

    return FitResult(
        p,
        l,
        (optimizer = :dummy,)
    )
end

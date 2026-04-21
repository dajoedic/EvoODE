import Pkg
Pkg.activate(@__DIR__)

using EvoODE
using Random

function make_stage_plateau_traj()
    t = collect(range(0.0, 4.0; length = 40))
    x = reshape(sin.(t) .+ 1.5, length(t), 1)
    return Trajectory(t, x)
end

function assert_stage_local_budget_behavior()
    traj = make_stage_plateau_traj()
    basis = default_staged_polynomial_basis(1)

    strategy = EvoGrow(
        pop_size = 4,
        n_levels = 5,
        children_per_parent = 1,
        max_terms_per_eq = 3,
        λ = 1e-3,
        progression = StageProgressionPolicy(mode = :stage_local, min_levels_per_stage = 2),
        usage = StageUsagePolicy(mode = :hard, new_term_bias_prob = 0.75)
    )

    result = discover(
        traj;
        structure = strategy,
        optimizer = DummyOptimizer(),
        basis = basis,
        loss = MSELoss(),
        options = DiscoveryOptions(
            rng_seed = 42,
            verbose = 0,
            max_levels = 5,
            loss_tol = -1.0,
            plateau_window = 1,
            plateau_tol = 1e-12,
            plateau_relative = false
        )
    )

    meta = result.meta.structure
    @assert meta.final_stage == 3
    @assert meta.stage_level_counts[1] == 2
    @assert meta.stage_level_counts[2] == 2
    @assert meta.stage_level_counts[3] == 1
    @assert length(meta.promotion_log) == 2
    @assert meta.termination_reason == :max_levels
end

function child_uses_stage_terms(child, stage_terms)
    for eq_terms in child.structure.active_idxs
        for term in eq_terms
            if term in stage_terms
                return true
            end
        end
    end
    return false
end

function assert_usage_policy_behavior()
    basis = default_staged_polynomial_basis(3)
    allowed_terms = vcat(basis.term_groups[1], basis.term_groups[2])
    current_stage_terms = basis.term_groups[2]

    ind = EvoODE.Individual(
        StructureSpec([[1], [2], [3]]),
        Float64[],
        Inf,
        Inf
    )

    Random.seed!(7)
    hard_children = EvoODE._expand_with_usage_policy(
        ind,
        3,
        allowed_terms,
        current_stage_terms,
        StageUsagePolicy(mode = :hard, new_term_bias_prob = 0.75);
        n_children = 12,
        max_terms_per_eq = 4
    )
    @assert all(child_uses_stage_terms(child, current_stage_terms) for child in hard_children)

    Random.seed!(7)
    passive_children = EvoODE._expand_with_usage_policy(
        ind,
        3,
        allowed_terms,
        current_stage_terms,
        StageUsagePolicy(mode = :passive, new_term_bias_prob = 0.75);
        n_children = 12,
        max_terms_per_eq = 4
    )
    @assert any(!child_uses_stage_terms(child, current_stage_terms) for child in passive_children)

    Random.seed!(7)
    soft_children = EvoODE._expand_with_usage_policy(
        ind,
        3,
        allowed_terms,
        current_stage_terms,
        StageUsagePolicy(mode = :soft, new_term_bias_prob = 1.0);
        n_children = 12,
        max_terms_per_eq = 4
    )
    @assert all(child_uses_stage_terms(child, current_stage_terms) for child in soft_children)
end

assert_stage_local_budget_behavior()
assert_usage_policy_behavior()

println("v2.2 semantics checks passed.")

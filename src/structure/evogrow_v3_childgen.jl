# src/structure/evogrow_v3_childgen.jl

function _evogrow_v3_uniform_stages(eq_stages::Vector{Int})
    return all(==(eq_stages[1]), eq_stages)
end

function _evogrow_v3_term_stage(basis::StagedPolynomialBasis, term_idx::Int)
    for (stage, group) in pairs(basis.term_groups)
        if term_idx in group
            return stage
        end
    end
    error("Term index $term_idx is not present in StagedPolynomialBasis.term_groups")
end

function _evogrow_v3_term_vars(basis::StagedPolynomialBasis, term_idx::Int)
    name = basis_term_name(basis, term_idx)
    vars = Int[]
    for m in eachmatch(r"u(\d+)", name)
        push!(vars, parse(Int, m.captures[1]))
    end
    return sort!(unique(vars))
end

function _evogrow_v3_term_available(
    basis::StagedPolynomialBasis,
    eq_stages::Vector{Int},
    eq_idx::Int,
    term_idx::Int;
    stage_caps = nothing,
    coupling_coherence::Bool = true
)
    stage = _evogrow_v3_term_stage(basis, term_idx)
    if stage > eq_stages[eq_idx]
        return false
    end

    vars = _evogrow_v3_term_vars(basis, term_idx)
    if !coupling_coherence || length(vars) < 2
        return true
    end

    for v in vars
        if stage_caps !== nothing && stage_caps[v] !== nothing && Int(stage_caps[v]) < stage
            continue
        end
        if eq_stages[v] < stage
            return false
        end
    end

    return true
end

function _evogrow_v3_equation_terms(
    basis::StagedPolynomialBasis,
    eq_stages::Vector{Int};
    stage_caps = nothing,
    coupling_coherence::Bool = true
)
    dim = length(eq_stages)
    allowed_by_eq = [Int[] for _ in 1:dim]
    current_by_eq = [Int[] for _ in 1:dim]

    for k in 1:dim
        for term_idx in 1:basis_num_terms(basis)
            if _evogrow_v3_term_available(
                basis,
                eq_stages,
                k,
                term_idx;
                stage_caps = stage_caps,
                coupling_coherence = coupling_coherence,
            )
                push!(allowed_by_eq[k], term_idx)
                if _evogrow_v3_term_stage(basis, term_idx) == eq_stages[k]
                    push!(current_by_eq[k], term_idx)
                end
            end
        end
    end

    return allowed_by_eq, current_by_eq
end

function _evogrow_v3_equation_terms(
    basis::AbstractBasis,
    eq_stages::Vector{Int};
    stage_caps = nothing,
    coupling_coherence::Bool = true
)
    terms = collect(1:basis_num_terms(basis))
    return [copy(terms) for _ in eq_stages], [copy(terms) for _ in eq_stages]
end

function _evogrow_v3_effective_current_terms(
    allowed_by_eq::Vector{Vector{Int}},
    current_by_eq::Vector{Vector{Int}}
)
    effective = Vector{Vector{Int}}(undef, length(current_by_eq))
    for k in eachindex(current_by_eq)
        if isempty(current_by_eq[k]) || current_by_eq[k] == allowed_by_eq[k]
            effective[k] = Int[]
        else
            effective[k] = current_by_eq[k]
        end
    end
    return effective
end

function _expand_equation_aware_passive(
    ind::Individual,
    dim::Int,
    allowed_by_eq::Vector{Vector{Int}};
    n_children::Int,
    max_terms_per_eq::Int
)
    children = Individual[]

    for _ in 1:n_children
        new_idxs = [copy(v) for v in ind.structure.active_idxs]
        k = rand(1:dim)

        existing = new_idxs[k]
        candidates = setdiff(allowed_by_eq[k], existing)

        if !isempty(candidates) && length(existing) < max_terms_per_eq
            push!(new_idxs[k], rand(candidates))
            new_idxs[k] = sort!(unique(new_idxs[k]))
        end

        push!(children, Individual(StructureSpec(new_idxs), Float64[], Inf, Inf))
    end

    return children
end

function _expand_equation_aware_hard(
    ind::Individual,
    dim::Int,
    allowed_by_eq::Vector{Vector{Int}},
    current_by_eq::Vector{Vector{Int}};
    n_children::Int,
    max_terms_per_eq::Int
)
    children = Individual[]
    effective_current_by_eq = _evogrow_v3_effective_current_terms(allowed_by_eq, current_by_eq)

    for _ in 1:n_children
        new_idxs = [copy(v) for v in ind.structure.active_idxs]
        growable_eqs = [k for k in 1:dim if length(new_idxs[k]) < max_terms_per_eq]

        if isempty(growable_eqs)
            push!(children, Individual(StructureSpec(new_idxs), Float64[], Inf, Inf))
            continue
        end

        eqs_with_new_terms = Int[]
        for k in growable_eqs
            candidates_new = setdiff(effective_current_by_eq[k], new_idxs[k])
            if !isempty(candidates_new)
                push!(eqs_with_new_terms, k)
            end
        end

        if !isempty(eqs_with_new_terms)
            k = rand(eqs_with_new_terms)
            candidates_new = setdiff(effective_current_by_eq[k], new_idxs[k])
            push!(new_idxs[k], rand(candidates_new))
            new_idxs[k] = sort!(unique(new_idxs[k]))
        else
            k = rand(growable_eqs)
            candidates = setdiff(allowed_by_eq[k], new_idxs[k])
            if !isempty(candidates)
                push!(new_idxs[k], rand(candidates))
                new_idxs[k] = sort!(unique(new_idxs[k]))
            end
        end

        push!(children, Individual(StructureSpec(new_idxs), Float64[], Inf, Inf))
    end

    return children
end

function _expand_equation_aware_soft(
    ind::Individual,
    dim::Int,
    allowed_by_eq::Vector{Vector{Int}},
    current_by_eq::Vector{Vector{Int}};
    n_children::Int,
    max_terms_per_eq::Int,
    bias_prob::Float64
)
    children = Individual[]
    effective_current_by_eq = _evogrow_v3_effective_current_terms(allowed_by_eq, current_by_eq)

    for _ in 1:n_children
        new_idxs = [copy(v) for v in ind.structure.active_idxs]
        growable_eqs = [k for k in 1:dim if length(new_idxs[k]) < max_terms_per_eq]

        if isempty(growable_eqs)
            push!(children, Individual(StructureSpec(new_idxs), Float64[], Inf, Inf))
            continue
        end

        try_new_stage = rand() < bias_prob
        if try_new_stage
            eqs_with_new_terms = Int[]
            for k in growable_eqs
                candidates_new = setdiff(effective_current_by_eq[k], new_idxs[k])
                if !isempty(candidates_new)
                    push!(eqs_with_new_terms, k)
                end
            end

            if !isempty(eqs_with_new_terms)
                k = rand(eqs_with_new_terms)
                candidates_new = setdiff(effective_current_by_eq[k], new_idxs[k])
                push!(new_idxs[k], rand(candidates_new))
                new_idxs[k] = sort!(unique(new_idxs[k]))

                push!(children, Individual(StructureSpec(new_idxs), Float64[], Inf, Inf))
                continue
            end
        end

        k = rand(growable_eqs)
        candidates = setdiff(allowed_by_eq[k], new_idxs[k])
        if !isempty(candidates)
            push!(new_idxs[k], rand(candidates))
            new_idxs[k] = sort!(unique(new_idxs[k]))
        end

        push!(children, Individual(StructureSpec(new_idxs), Float64[], Inf, Inf))
    end

    return children
end

function _expand_equation_aware_with_usage_policy(
    ind::Individual,
    dim::Int,
    basis::AbstractBasis,
    eq_stages::Vector{Int},
    allowed_terms::Vector{Int},
    current_stage_terms::Vector{Int},
    usage::StageUsagePolicy;
    n_children::Int,
    max_terms_per_eq::Int,
    stage_caps = nothing,
    coupling_coherence::Bool = true
)
    if _evogrow_v3_uniform_stages(eq_stages)
        return _expand_with_usage_policy(
            ind,
            dim,
            allowed_terms,
            current_stage_terms,
            usage;
            n_children = n_children,
            max_terms_per_eq = max_terms_per_eq
        )
    end

    allowed_by_eq, current_by_eq = _evogrow_v3_equation_terms(
        basis,
        eq_stages;
        stage_caps = stage_caps,
        coupling_coherence = coupling_coherence,
    )

    if usage.mode == :passive
        return _expand_equation_aware_passive(
            ind,
            dim,
            allowed_by_eq;
            n_children = n_children,
            max_terms_per_eq = max_terms_per_eq
        )
    elseif usage.mode == :hard
        return _expand_equation_aware_hard(
            ind,
            dim,
            allowed_by_eq,
            current_by_eq;
            n_children = n_children,
            max_terms_per_eq = max_terms_per_eq
        )
    else
        return _expand_equation_aware_soft(
            ind,
            dim,
            allowed_by_eq,
            current_by_eq;
            n_children = n_children,
            max_terms_per_eq = max_terms_per_eq,
            bias_prob = usage.new_term_bias_prob
        )
    end
end

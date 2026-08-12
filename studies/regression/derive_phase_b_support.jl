# studies/regression/derive_phase_b_support.jl
#
# Derives the true support of every Phase B system from the dataset RHS and
# writes it to studies/regression/phase_b_support.json.
#
# Why this is precomputed rather than derived at run time: the derivation costs
# minutes across all 63 systems, and every one of the 756 campaign jobs would
# otherwise repeat it. The generated file is committed, inspectable by eye, and
# regenerated only when the dataset or the basis changes.
#
# Why the support is derived rather than hand-listed: a hand-maintained table
# existed for five diagnostic systems and did not scale to 63. This script
# reproduces those five exactly, which is the acceptance criterion.
#
# Usage:
#   julia --project=. studies/regression/derive_phase_b_support.jl
#   julia --project=. studies/regression/derive_phase_b_support.jl --check
#
# --check verifies the committed file against a fresh derivation without
# rewriting it, and exits non-zero on any disagreement.

using EvoODE
using JSON3
using LinearAlgebra
using Printf
using Random

include(joinpath(@__DIR__, "diagnostic_systems.jl"))
include(joinpath(@__DIR__, "phase_b_config.jl"))

const SUPPORT_PATH = joinpath(@__DIR__, "phase_b_support.json")

# Points at which the RHS and the basis are compared. A single trajectory leaves
# basis columns collinear, which makes the least-squares support non-unique; both
# IC trajectories plus scattered points inside the visited box break that.
# The scatter stays strictly inside the box because leaving it can exit the
# domain of the RHS (log, sqrt).
const SUPPORT_N_SCATTER = 400
const SUPPORT_SCATTER_SEED = 20260812
const SUPPORT_ATOL = 1e-9
const SUPPORT_RTOL = 1e-9

function _support_eval_points(row, dim::Int)
    states = Matrix{Float64}[]
    for ic in PHASE_B_IC_SETS
        push!(states, _phase_b_solution_trajectory(row, ic).x)
    end
    X = reduce(vcat, states)
    lo = vec(minimum(X; dims = 1))
    hi = vec(maximum(X; dims = 1))
    rng = MersenneTwister(SUPPORT_SCATTER_SEED)
    S = zeros(Float64, SUPPORT_N_SCATTER, dim)
    for i in 1:SUPPORT_N_SCATTER, j in 1:dim
        S[i, j] = lo[j] + rand(rng) * (hi[j] - lo[j])
    end
    return vcat(X, S)
end

function _support_design_and_rhs(rhs!, X::Matrix{Float64}, dim::Int)
    basis = default_staged_polynomial_basis(dim)
    p = basis_num_terms(basis)
    n = size(X, 1)
    phi = zeros(Float64, n, p)
    rhs = zeros(Float64, n, dim)
    du = zeros(Float64, dim)
    valid = trues(n)
    for r in 1:n
        u = view(X, r, :)
        ok = true
        try
            for c in 1:p
                phi[r, c] = basis_term_func(basis, c)(u, 0.0)
            end
            rhs!(du, u, nothing, 0.0)
            rhs[r, :] .= du
        catch
            ok = false
        end
        valid[r] = ok && all(isfinite, view(phi, r, :)) && all(isfinite, du)
    end
    return phi[valid, :], rhs[valid, :]
end

"""
    derive_true_support(rhs!, X, dim) -> (support, status)

`support` is a `Vector{Vector{Int}}` of basis term indices per equation, or
`nothing` when no exact support exists or it cannot be established uniquely.

The support is both *exact* (it reproduces the RHS to tolerance) and *minimal*
(no term can be dropped without breaking that). Minimality matters: a plain
threshold on least-squares coefficients spreads a representable RHS across many
basis terms on an ill-conditioned design and reports a support that is not the
true one.
"""
function derive_true_support(rhs!, X::Matrix{Float64}, dim::Int)
    phi, rhs = _support_design_and_rhs(rhs!, X, dim)
    size(phi, 1) >= size(phi, 2) || return (nothing, "too_few_valid_points")
    all(isfinite, phi) || return (nothing, "nonfinite_design")
    all(isfinite, rhs) || return (nothing, "nonfinite_rhs")
    rank(phi) == size(phi, 2) || return (nothing, "rank_deficient")

    support = Vector{Vector{Int}}()
    for eq in 1:dim
        target = rhs[:, eq]
        tol = SUPPORT_ATOL + SUPPORT_RTOL * max(norm(target), 1.0)

        coefs = phi \ target
        norm(phi * coefs - target) <= tol || return (nothing, "eq$(eq)_not_representable")

        keep = collect(1:size(phi, 2))
        for cand in sort(keep; by = i -> abs(coefs[i]))
            trial = filter(!=(cand), keep)
            if isempty(trial)
                norm(target) <= tol && (keep = trial)
                continue
            end
            sub = @view phi[:, trial]
            if norm(sub * (sub \ target) - target) <= tol
                keep = trial
            end
        end
        push!(support, sort(keep))
    end
    return (support, "ok")
end

function derive_all()
    systems = phase_b_systems()
    rows = Dict(Int(r["id"]) => r for r in _phase_b_dataset_rows())
    entries = Dict{String, Any}[]
    for s in systems
        sid = Int(s[:system_id])
        dim = Int(s[:dim])
        X = _support_eval_points(rows[sid], dim)
        support, status = derive_true_support(s[:rhs!], X, dim)
        basis = default_staged_polynomial_basis(dim)
        push!(entries, Dict{String, Any}(
            "system_id" => sid,
            "dim" => dim,
            "status" => status,
            "representability" => support === nothing ? "surrogate" : "exact",
            "support_idxs" => support === nothing ? nothing : support,
            "support_terms" => support === nothing ? nothing :
                [[basis_term_name(basis, i) for i in eq] for eq in support],
        ))
    end
    return entries
end

function load_support_table()
    isfile(SUPPORT_PATH) || error("Missing $(SUPPORT_PATH); run derive_phase_b_support.jl")
    raw = JSON3.read(read(SUPPORT_PATH, String))
    table = Dict{Int, Any}()
    for e in raw["systems"]
        sid = Int(e["system_id"])
        idxs = e["support_idxs"]
        table[sid] = (
            representability = String(e["representability"]),
            status = String(e["status"]),
            support = idxs === nothing ? nothing :
                      [Int[Int(i) for i in eq] for eq in idxs],
        )
    end
    return table
end

function _print_table(entries)
    @printf("%-5s %-4s %-10s %-24s %s\n", "sys", "dim", "class", "status", "support")
    for e in entries
        txt = e["support_terms"] === nothing ? "-" :
              join(["[" * join(t, ", ") * "]" for t in e["support_terms"]], " ")
        @printf("%-5d %-4d %-10s %-24s %s\n", e["system_id"], e["dim"],
                e["representability"], e["status"],
                length(txt) > 80 ? txt[1:80] * " ..." : txt)
    end
    n_exact = count(e -> e["representability"] == "exact", entries)
    @printf("\nexact: %d   surrogate: %d   total: %d\n",
            n_exact, length(entries) - n_exact, length(entries))
end

# The five diagnostic systems carry a hand-encoded support. The derivation must
# reproduce them exactly; disagreement means either the derivation or the table
# is wrong, and that has to be resolved rather than papered over.
function _cross_check(entries)
    failures = String[]
    for e in entries
        sid = e["system_id"]
        hand = try
            expected_terms_for(sid)
        catch
            continue
        end
        hand === nothing && continue
        got = e["support_terms"]
        if got === nothing
            push!(failures, "system $(sid): hand-encoded support exists, derivation returned nothing ($(e["status"]))")
            continue
        end
        h = [sort(String.(eq)) for eq in hand]
        g = [sort(String.(eq)) for eq in got]
        h == g || push!(failures, "system $(sid): hand=$(h) derived=$(g)")
    end
    return failures
end

function main()
    check_only = "--check" in ARGS
    entries = derive_all()
    _print_table(entries)

    failures = _cross_check(entries)
    println("\n--- cross-check against hand-encoded diagnostic systems ---")
    if isempty(failures)
        println("all hand-encoded systems reproduced exactly")
    else
        for f in failures
            println("MISMATCH: ", f)
        end
        error("Support derivation disagrees with hand-encoded systems")
    end

    payload = Dict{String, Any}(
        "generated_by" => "studies/regression/derive_phase_b_support.jl",
        "n_scatter" => SUPPORT_N_SCATTER,
        "scatter_seed" => SUPPORT_SCATTER_SEED,
        "atol" => SUPPORT_ATOL,
        "rtol" => SUPPORT_RTOL,
        "systems" => entries,
    )

    if check_only
        isfile(SUPPORT_PATH) || error("--check requested but $(SUPPORT_PATH) does not exist")
        committed = JSON3.read(read(SUPPORT_PATH, String))
        fresh = JSON3.read(JSON3.write(payload))
        if JSON3.write(committed["systems"]) != JSON3.write(fresh["systems"])
            error("Committed support table differs from a fresh derivation")
        end
        println("\n--check: committed table matches a fresh derivation")
    else
        open(SUPPORT_PATH, "w") do io
            JSON3.pretty(io, payload)
        end
        println("\nwrote ", SUPPORT_PATH)
    end
end

main()

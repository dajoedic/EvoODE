# main_benchmark.jl
#
# Benchmark EvoGrow on multiple systems from strogatz_extended.json
# with different noise levels and sampling rates.

push!(LOAD_PATH, joinpath(@__DIR__, "src"))
using EvoODE
using Random
using Statistics
using Printf
using Dates

# -----------------------------
# Helpers
# -----------------------------

# Create noisy / subsampled variants of a trajectory
function make_variant(traj::Trajectory; noise_std::Float64 = 0.0, stride::Int = 1)
    t_sub = traj.t[1:stride:end]
    X_sub = traj.x[1:stride:end, :]

    if noise_std > 0
        σ = std(X_sub; dims = 1)
        noise = noise_std .* (σ .* randn(size(X_sub)))
        X_noisy = X_sub .+ noise
    else
        X_noisy = X_sub
    end

    return Trajectory(t_sub, X_noisy)
end

# Small helper to stringify the best structure (for logging)
function structure_to_string(structure::StructureSpec,
                             basis::BasisLibrary,
                             params::Vector{Float64})
    buf = IOBuffer()
    idx = 1
    for eq_index in 1:length(structure.active_idxs)
        active_terms = structure.active_idxs[eq_index]
        terms_with_params = String[]
        for term_idx in active_terms
            coef = params[idx]
            name = basis[term_idx].name
            push!(terms_with_params,
                  @sprintf("(%0.4f)*%s", coef, name))
            idx += 1
        end
        println(buf, "du_$eq_index = " * join(terms_with_params, " + "))
    end
    return String(take!(buf))
end

# -----------------------------
# Config
# -----------------------------

data_path = joinpath(@__DIR__, "data", "strogatz_extended.json")

n_systems      = 15
noise_levels   = [0.0, 0.01, 0.05]       # relative noise levels
strides        = [1, 2, 4]               # subsampling factors
maxiters_fit   = 200
strategy = EvoGrow(
    20,     # pop_size
    5,      # n_levels
    2,      # children_per_parent
    5,      # max_terms_per_eq
    1e-3,   # λ
)

Random.seed!(42)

println("Loading systems...")
systems = load_2d_systems(data_path; n = n_systems)
println("Loaded $(length(systems)) 2D systems.")

# -----------------------------
# Run benchmark
# -----------------------------

out_path = joinpath(@__DIR__, "benchmark_results.csv")
plots_dir = joinpath(@__DIR__, "benchmark_plots")

open(out_path, "w") do io
    # CSV header
    println(io, "sys_id,dim,eq,eq_description,noise,stride,n_points,loss,objective,n_params,elapsed_sec,structure")

    for sys in systems
        base_traj = sys.traj
        dim = sys.dim
        basis = default_basis_library(dim)

        # --- log system + ground truth once per system ---
        println()
        println("==============================================")
        println("System id=$(sys.id), dim=$dim")
        println("Description:  $(sys.eq_description)")
        println("Ground truth: $(sys.eq)")
        println("==============================================")

        # escape text fields for CSV once per system
        eq_str   = replace(sys.eq, "\"" => "''")
        desc_str = replace(sys.eq_description, "\"" => "''")

        for noise in noise_levels
            for stride in strides
                variant = make_variant(base_traj; noise_std = noise, stride = stride)
                n_points = size(variant.x, 1)

                println()
                println("Variant: noise=$(noise), stride=$(stride), n_points=$n_points")

                t_start = time()
                result = search_structure(strategy, variant, basis; maxiters = maxiters_fit)
                elapsed = time() - t_start
				
				f!, _ = build_model(result.structure, result.basis)

				solve_and_save_plot(
					f!,
					result.params,
					variant;
					filename = "plots/sys$(sys.id)_noise$(noise)_stride$(stride).png",
					title = "System $(sys.id), noise=$(noise), stride=$(stride)"
				)

                n_params = length(result.params)
                struct_str = replace(
                    structure_to_string(result.structure,
                                        result.basis,
                                        result.params),
                    '\n' => ' '
                )

                # Escape double quotes in text fields
                struct_csv = replace(struct_str, "\"" => "''")

                @printf(io,
                        "%d,%d,\"%s\",\"%s\",%0.4f,%d,%d,%0.8g,%0.8g,%d,%0.3f,\"%s\"\n",
                        sys.id,
                        dim,
                        eq_str,
                        desc_str,
                        noise,
                        stride,
                        n_points,
                        result.loss,
                        result.objective,
                        n_params,
                        elapsed,
                        struct_csv)

                # ensure line is flushed to disk after each run
                flush(io)
            end
        end
    end
end

println("Benchmark finished.")
println("Results written to: $out_path")

using Test

include(joinpath(@__DIR__, "..", "studies", "regression", "wp_t1f_warm_neighbourhood.jl"))

@testset "WP-T1f warm-start vectors" begin
    coefficients = load_t1f_true_coefficients()
    system = first(phase_c_exact_dim23_systems())
    basis = phase_c_basis(Int(system[:dim]))
    true_terms = canonical_support_terms(system[:expected_support])
    system_coefficients = coefficients_for_system(coefficients, Int(system[:system_id]))
    neighbours = neighbourhood(true_terms, basis)

    for klass in ("add_one", "remove_one", "swap_one")
        neighbour = first(row for row in neighbours if String(row["neighbor_class"]) == klass)
        params = true_parameter_vector(neighbour["neighbor_terms"], basis, system_coefficients; default_new = 0.0)
        ordered_terms = parameter_terms(neighbour["neighbor_terms"], basis)
        lookup = coefficient_lookup(system_coefficients)
        for (idx, (eq_idx, _, term_name)) in enumerate(ordered_terms)
            @test params[idx] == get(lookup, (eq_idx, term_name), 0.0)
        end
        if klass in ("add_one", "swap_one")
            added = basis_term_name(basis, Int(neighbour["added_term"]))
            added_eq = Int(neighbour["equation_idx"])
            added_pos = findfirst(
                item -> item[1] == added_eq && item[3] == added,
                ordered_terms,
            )
            @test added_pos !== nothing
            @test params[added_pos] == 0.0
        end
    end
end

@testset "WP-T1f control abort and attempt metadata" begin
    @test assert_t1f_control_loss_ok(1e-5, 24, 1; control_loss_optimizer_tolerance = 1e-2)
    @test_throws ErrorException assert_t1f_control_loss_ok(1.1e-4, 24, 1)
    @test t1f_floor_to_control_optimizer_ratio(2e-8, 1e-8) == 2.0
    @test t1f_floor_to_control_optimizer_ratio(2e-8, 0.0) === nothing

    fit_result = Dict{String, Any}(
        "fit_meta" => (
            accepted_attempt = 2,
            fit_attempts = 3,
            loss_evals = 17,
        ),
    )
    @test fit_winning_attempt(fit_result) == 2
    @test fit_attempt_count(fit_result) == 3
    @test fit_loss_evals(fit_result) == 17
end

@testset "WP-T1f optimizer is Phase-C reference except clamp" begin
    reference = build_reference_optimizer(max_fit_attempts = PHASE_C_MAX_FIT_ATTEMPTS)
    unclamped = build_t1f_unclamped_optimizer(max_fit_attempts = PHASE_C_MAX_FIT_ATTEMPTS)
    @test unclamped.clamp_val == Inf
    for field in fieldnames(BFGSOptimizer)
        field == :clamp_val && continue
        @test getfield(unclamped, field) == getfield(reference, field)
    end
    @test assert_t1f_optimizer_matches_reference_except_clamp()
end

@testset "WP-T1f raw identity fields" begin
    system = first(phase_c_exact_dim23_systems())
    optimizer = build_t1f_unclamped_optimizer(max_fit_attempts = PHASE_C_MAX_FIT_ATTEMPTS)
    git = (git_hash = "test-git",)
    row = base_raw_row(system, 1, "trajectory-sha", "fixture", git, "phase-c-fingerprint", optimizer)
    @test row["phase_c_config_fingerprint"] == "phase-c-fingerprint"
    @test row["optimizer_variant"] == "phase_c_reference_unclamped"
    @test row["clamp_val"] == "Inf"
    @test haskey(row, "wp_t1f_config_fingerprint")
    @test !haskey(row, "config_fingerprint")
end

@testset "WP-T1f loss comparison ignores budget exhaustion but not sentinels" begin
    exhausted_floor = t1f_loss_comparison(
        1e-14,
        1e-12;
        neighbor_budget_exhausted = false,
        floor_budget_exhausted = true,
    )
    @test exhausted_floor["comparison_budget_stratum"] == "floor_exhausted"
    @test isapprox(exhausted_floor["log10_loss_ratio"], -2.0)
    @test exhausted_floor["beats_floor"] === true

    sentinel = t1f_loss_comparison(
        WP_T1D_SENTINEL_LOSS,
        1e-12;
        neighbor_budget_exhausted = true,
        floor_budget_exhausted = true,
    )
    @test sentinel["comparison_budget_stratum"] == "both_exhausted"
    @test sentinel["log10_loss_ratio"] === nothing
    @test sentinel["beats_floor"] === false
end

@testset "WP-T1f aggregate-only keeps neighbour classes separate" begin
    raw_rows = Dict{String, Any}[
        Dict(
            "fit_role" => "neighbour_warm",
            "variant" => "warm_reference",
            "dimension" => 2,
            "system_id" => 24,
            "initial_condition_set" => 1,
            "neighbor_class" => "add_one",
            "loss" => 1e-14,
            "floor_loss" => 1e-12,
            "budget_exhausted" => false,
            "floor_budget_exhausted" => true,
            "warm_start_from_attempt_1" => true,
        ),
        Dict(
            "fit_role" => "neighbour_warm",
            "variant" => "warm_reference",
            "dimension" => 2,
            "system_id" => 24,
            "initial_condition_set" => 1,
            "neighbor_class" => "swap_one",
            "loss" => 2e-12,
            "floor_loss" => 1e-12,
            "budget_exhausted" => false,
            "floor_budget_exhausted" => false,
            "warm_start_from_attempt_1" => false,
        ),
        Dict(
            "system_id" => 24,
            "dimension" => 2,
            "initial_condition_set" => 1,
            "neighbor_class" => "remove_one",
            "loss_true" => 1e-2,
            "loss_neighbor" => 2e-2,
            "log10_loss_ratio" => -99.0,
            "budget_exhausted_true" => false,
            "budget_exhausted_neighbor" => true,
            "config_fingerprint" => "old-phase-c-fingerprint",
        ),
        Dict(
            "fit_role" => "control",
            "system_id" => 24,
            "dimension" => 2,
            "initial_condition_set" => 1,
            "loss" => 1e-10,
            "control_loss_data_tolerance" => 1e-10,
            "control_loss_optimizer_tolerance" => 1e-5,
        ),
        Dict(
            "fit_role" => "floor",
            "system_id" => 24,
            "dimension" => 2,
            "initial_condition_set" => 1,
            "loss" => 2e-5,
            "control_loss_data_tolerance" => 1e-10,
            "control_loss_optimizer_tolerance" => 1e-5,
        ),
        Dict(
            "fit_role" => "truth_cold",
            "system_id" => 24,
            "dimension" => 2,
            "initial_condition_set" => 1,
            "loss" => 1e-9,
            "sentinel_loss" => false,
        ),
    ]

    summary, thresholds, quantiles, cell_losses, cold_summary, cold_rates, retry, budget_strata =
        aggregate_t1f_rows(raw_rows)

    summary_keys = Set((row["variant"], row["dimension"], row["neighbor_class"], row["comparison_scope"]) for row in summary)
    @test ("warm_reference", 2, "add_one", "all_comparable") in summary_keys
    @test ("warm_reference", 2, "add_one", "neither_exhausted") in summary_keys
    @test ("warm_reference", 2, "swap_one", "all_comparable") in summary_keys
    @test ("cold_reference", 2, "remove_one", "all_comparable") in summary_keys
    @test !any(row -> row["neighbor_class"] == "", summary)
    @test length(thresholds) == 3 * 2 * length(WP_T1D_MARGIN_FACTORS)
    @test length(quantiles) == 3 * 2 * length(WP_T1D_QUANTILES)
    @test any(row ->
        row["variant"] == "warm_reference" &&
        row["neighbor_class"] == "add_one" &&
        row["comparison_scope"] == "all_comparable" &&
        row["n_valid_margins"] == 1,
        summary,
    )
    @test any(row ->
        row["variant"] == "warm_reference" &&
        row["neighbor_class"] == "add_one" &&
        row["comparison_scope"] == "neither_exhausted" &&
        row["n_valid_margins"] == 0,
        summary,
    )
    @test any(row ->
        row["variant"] == "cold_reference" &&
        row["neighbor_class"] == "remove_one" &&
        row["comparison_scope"] == "all_comparable" &&
        row["n_neighbors_below_floor"] == 0,
        summary,
    )
    @test any(row ->
        row["variant"] == "warm_reference" &&
        row["neighbor_class"] == "add_one" &&
        row["comparison_budget_stratum"] == "floor_exhausted" &&
        row["n_rows"] == 1,
        budget_strata,
    )
    @test any(row ->
        row["variant"] == "cold_reference" &&
        row["neighbor_class"] == "remove_one" &&
        row["comparison_budget_stratum"] == "neighbour_exhausted" &&
        row["n_rows"] == 1,
        budget_strata,
    )
    @test length(cell_losses) == 1
    @test only(cell_losses)["control_loss_data_tolerance"] == 1e-10
    @test only(cell_losses)["control_loss_optimizer_tolerance"] == 1e-5
    @test only(cell_losses)["floor_loss"] == 2e-5
    @test only(cell_losses)["floor_to_control_optimizer_tolerance_ratio"] == 2.0
    @test only(cold_summary)["n_loss_lt_1e_8"] == 1
    @test only(cold_rates)["single_start_hit_rate"] == 1.0
    @test any(row -> row["neighbor_class"] == "swap_one" && row["n_not_from_warm_attempt"] == 1, retry)
    normalised = normalised_neighbour_rows(raw_rows)
    cold = only([row for row in normalised if row["variant"] == "cold_reference"])
    @test cold["phase_c_config_fingerprint"] == "old-phase-c-fingerprint"
end

@testset "WP-T1f analysis labels ignore trailing path separators" begin
    root = joinpath("analysis", "data", "wp_t1d_neighbourhood")
    plain = t1f_analysis_dir_for(joinpath("outputs", "wp_t1d_neighbourhood", "orion_5a87efb"), root)
    slash = t1f_analysis_dir_for(joinpath("outputs", "wp_t1d_neighbourhood", "orion_5a87efb") * "/", root)
    backslash = t1f_analysis_dir_for(joinpath("outputs", "wp_t1d_neighbourhood", "orion_5a87efb") * "\\", root)
    @test slash == plain
    @test backslash == plain
    @test basename(plain) == "orion_5a87efb"
end

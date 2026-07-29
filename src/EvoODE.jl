module EvoODE

"""
    module EvoODE

Lightweight research framework for data-driven discovery of interpretable ODEs.
"""

# ------------------------
# Public API – Core types
# ------------------------
export Trajectory, DiscoveryOptions, DiscoveryResult

# ------------------------
# Public API – Main entry
# ------------------------
export discover

# ------------------------
# Public API – Interfaces
# ------------------------
export AbstractStructureSearch, AbstractBasis, AbstractLoss, AbstractOptimizer
export StructureSpec
export search_structure
export build_rhs
export basis_num_terms, basis_term_name, basis_term_func
export evaluate_loss
export fit_parameters

# ------------------------
# Public API – Implementations
# ------------------------
export EvoGrow, EvoGrowScreening, EvoGrowV3
export GPStructureSearch
export StageProgressionPolicy, StageUsagePolicy

export PolynomialBasis, default_polynomial_basis
export StagedPolynomialBasis, default_staged_polynomial_basis

export MSELoss

export BFGSOptimizer
export DummyOptimizer

# ------------------------
# Public API – Logging
# ------------------------
export DEBUG, INFO, WARN, ERROR
export set_level, current_level, level_name, reset_timer
export set_log_file, close_log_file
export log_debug, log_info, log_warn, log_error, log_exception
export time_block

# ------------------------
# Public API – Stopping / Simulation / Plotting
# ------------------------
export should_stop
export simulate
export save_comparison_csv
export solve_and_save_plot
export render_all_frames, render_frame, structure_to_string

# ============================================================
# Core types first
# ============================================================
include("core/types.jl")

# ============================================================
# Logging utilities
# ============================================================
include("utils/logging.jl")
using .EvoLogger

# ============================================================
# Interfaces
# ============================================================
include("structure/interface.jl")
include("basis/interface.jl")
include("loss/interface.jl")
include("optimize/interface.jl")

# ============================================================
# Core logic that depends on types/options
# ============================================================
include("core/stopping.jl")

# ============================================================
# Shared utilities
# ============================================================
include("structure/utils.jl")

# ============================================================
# Basis libraries
# ============================================================
include("basis/polynomial.jl")
include("basis/staged_polynomial.jl")

# ============================================================
# Losses
# ============================================================
include("loss/mse.jl")

# ============================================================
# Optimizers
# ============================================================
include("optimize/bfgs.jl")
include("optimize/dummy.jl")
include("optimize/pretune.jl")

# ============================================================
# Simulation / Plotting
# ============================================================
include("simulate/solve.jl")
include("simulate/export.jl")
include("plotting/plot_solution.jl")
include("plotting/search_animation.jl")

# ============================================================
# Structure search algorithms
# ============================================================
include("structure/evogrow.jl")
include("structure/evogrow_screening.jl")
include("structure/evogrow_v3_childgen.jl")
include("structure/evogrow_v3.jl")
include("structure/gp.jl")

# ============================================================
# Orchestration
# ============================================================
include("core/discover.jl")

end # module EvoODE

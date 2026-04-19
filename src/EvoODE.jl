module EvoODE

"""
    module EvoODE

Lightweight framework for data-driven ODE discovery.

Core entry point:
- `discover(...)`: run structure search + parameter fitting to identify an ODE model from time series data.
"""

# ------------------------
# Public API – Types / I/O
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

# ------------------------
# Public API – Implementations (Phase 1)
# ------------------------
export EvoGrow
export PolynomialBasis, default_polynomial_basis
export MSELoss
export BFGSOptimizer
export simulate
export solve_and_save_plot
export build_rhs
export GPStructureSearch


# --- Core types first ---
include("core/types.jl")

# --- Interfaces (must be loaded before implementations) ---
include("structure/interface.jl")
include("basis/interface.jl")
include("loss/interface.jl")
include("optimize/interface.jl")

# --- Implementations ---
include("basis/polynomial.jl")
include("loss/mse.jl")
include("optimize/bfgs.jl")
include("simulate/solve.jl")
include("plotting/plot_solution.jl")
include("structure/utils.jl")
include("structure/evogrow.jl")
include("structure/gp.jl")

# --- Orchestration last ---
include("core/discover.jl")

end # module EvoODE

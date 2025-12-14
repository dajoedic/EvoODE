module EvoODE

"""
    module EvoODE

Lightweight framework for data-driven ODE discovery.

This package provides:

- Data types and loaders for benchmark systems (`Trajectory`, `SystemData`, `load_2d_systems`)
- Simple fixed-structure ODE models and parameter fitting (`make_model`, `fit_parameters`)
- Structure search via an evolutionary / incremental basis construction (`EvoGrow`, `search_structure`)
- A small DSL for basis functions (`BasisTerm`, `BasisLibrary`, `StructureSpec`, `Individual`)
"""

########################
# Public API – Data I/O
########################

# Time series data and system metadata:
# - `Trajectory`: holds simulated / measured trajectories
# - `SystemData`: metadata + ground-truth system definition
# - `load_2d_systems`: convenience loader for bundled 2D benchmark systems
export Trajectory, SystemData, load_2d_systems

#########################################
# Public API – Fixed-structure modelling
#########################################

# Simple ODE model constructor and parameter fitting:
# - `make_model`: build an ODE RHS function from a basis and parameters
# - `fit_parameters`: fit parameters for a *given* structure to a trajectory
export fit_parameters

#########################################
# Public API – Structure search / grammar
#########################################

# Symbolic / structural building blocks:
# - `BasisTerm`: a single basis function (e.g. u1, u1^2, u1*u2, sin(u1), …)
# - `BasisLibrary`: collection of basis terms for all state dimensions
# - `StructureSpec`: compact representation of which terms are active per equation
# - `Individual`: one candidate structure + parameters in the search
export BasisTerm, BasisLibrary, StructureSpec, Individual

# Convenience helpers:
# - `default_basis_library`: default set of basis functions (e.g. polynomials up to some order)
# - `build_model`: construct an ODE RHS from a `StructureSpec` and `BasisLibrary`
export default_basis_library, build_model

# Main structure search entry points:
# - `EvoGrow`: configuration / strategy type for evolutionary growth search
# - `search_structure`: run the search given data and a basis library
export EvoGrow, search_structure

#########################################
# Public API – Evaluation & Plotting
#########################################

# Evaluation and visualization helpers:
# - `solve_and_save_plot`: simulate a discovered ODE and
#   compare it to the observed trajectory
export solve_and_save_plot

########################
# Internal implementation
########################
# The following files implement the functionality behind the public API.
# They are kept small and focused to make it easier to navigate the codebase.

include("data.jl")       # Trajectory, SystemData, loaders
include("loss.jl")       # loss functions and evaluation helpers
include("optimize.jl")   # parameter fitting / optimization wrappers
include("structure.jl")  # structure search, EvoGrow, basis handling
include("plotting.jl")   # plotting + re-simulation helpers

end # module EvoODE

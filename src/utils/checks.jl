# src/utils/checks.jl
# Reserved for input validation utilities (not yet implemented).
#
# Intended future use:
#   - validate_trajectory(traj): check for NaNs, monotone time, shape consistency
#   - validate_basis(basis, dim): check that basis was built for the right dimension
#   - validate_options(options): check parameter ranges and consistency
#
# These are not yet needed because discover() validates inputs implicitly through
# the ODE solver and loss function. Implement here when systematic error messages
# become necessary (e.g., before public release or benchmarking).

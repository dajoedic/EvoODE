module EvoODE

export Trajectory, SystemData, load_2d_systems
export make_model, fit_parameters

include("data.jl")
include("model.jl")
include("loss.jl")
include("optimize.jl")

end

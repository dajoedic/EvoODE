function clamp_val_json(value::Real)
    numeric = Float64(value)
    return isfinite(numeric) ? numeric : "Inf"
end

function parse_clamp_val(value)
    if value isa AbstractString
        stripped = strip(value)
        lowercase(stripped) == "inf" && return Inf
        return parse(Float64, stripped)
    end
    return Float64(value)
end

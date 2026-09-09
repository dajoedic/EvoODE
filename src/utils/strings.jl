# src/utils/strings.jl

function _append_unique_strings!(target::Vector{String}, values)
    for value in values
        text = String(value)
        if !(text in target)
            push!(target, text)
        end
    end
    return nothing
end

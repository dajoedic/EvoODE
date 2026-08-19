using Dates

if !(@isdefined study_arg_value)

function study_arg_value(args::Vector{String}, name::String)
    idx = findfirst(==(name), args)
    idx === nothing && return nothing
    idx == length(args) && error("Missing value for $(name)")
    return args[idx + 1]
end

function study_timestamp_suffix()
    return Dates.format(now(), dateformat"yyyymmdd_HHMMSS")
end

function study_unique_path(path::AbstractString)
    dir = dirname(path)
    base = basename(path)
    stem, ext = splitext(base)
    for attempt in 0:999
        suffix = attempt == 0 ? study_timestamp_suffix() : "$(study_timestamp_suffix())_$(attempt)"
        candidate = joinpath(dir, "$(stem)_$(suffix)$(ext)")
        ispath(candidate) || return candidate
    end
    error("Could not find a free output path near $(path)")
end

function study_unique_dir(path::AbstractString)
    for attempt in 0:999
        suffix = attempt == 0 ? study_timestamp_suffix() : "$(study_timestamp_suffix())_$(attempt)"
        candidate = "$(path)_$(suffix)"
        ispath(candidate) || return candidate
    end
    error("Could not find a free output directory near $(path)")
end

function study_dir_has_content(path::AbstractString)
    return isdir(path) && !isempty(readdir(path))
end

function study_resolve_output_dir(default_dir::AbstractString, args::Vector{String} = ARGS;
                                  flag::String = "--output-dir", allow_append::Bool = false)
    explicit = study_arg_value(args, flag)
    explicit !== nothing && return normpath(explicit)
    allow_append && ("--append" in args) && return normpath(default_dir)
    return study_dir_has_content(default_dir) ? normpath(study_unique_dir(default_dir)) : normpath(default_dir)
end

function study_resolve_output_path(default_path::AbstractString, args::Vector{String} = ARGS;
                                   flag::String = "--output")
    explicit = study_arg_value(args, flag)
    explicit !== nothing && return normpath(explicit)
    return ispath(default_path) ? normpath(study_unique_path(default_path)) : normpath(default_path)
end

end

function _arg_values(args::Vector{String}, name::String)
    values = String[]
    idx = 1
    while idx <= length(args)
        if args[idx] == name
            idx == length(args) && error("Missing value for $(name)")
            push!(values, args[idx + 1])
            idx += 2
        else
            idx += 1
        end
    end
    return values
end

function _arg_value(args::Vector{String}, name::String; default = nothing)
    values = _arg_values(args, name)
    length(values) > 1 && error("Expected at most one $(name), got $(length(values))")
    isempty(values) && return default
    return only(values)
end

function _require_arg(args::Vector{String}, name::String)
    value = _arg_value(args, name)
    value === nothing && error("Missing required argument $(name)")
    return value
end

function _parse_int_list(value::AbstractString)
    items = split(value, ",")
    isempty(items) && error("Expected at least one integer")
    return [parse(Int, strip(item)) for item in items if !isempty(strip(item))]
end

function _parse_cell_specs(value::AbstractString)
    cells = NamedTuple[]
    for item in split(value, ",")
        spec = strip(item)
        isempty(spec) && continue
        parts = split(spec, ":")
        length(parts) == 3 || error("Cell spec $(spec) must be system:initial_condition_set:clamp_val")
        push!(
            cells,
            (
                system_id = parse(Int, strip(parts[1])),
                initial_condition_set = parse(Int, strip(parts[2])),
                clamp_val = strip(parts[3]),
            ),
        )
    end
    isempty(cells) && error("Expected at least one cell spec")
    return cells
end

function _parse_csv_line(line::AbstractString)
    # Phase-C manifests are generated without quoted fields.
    return String.(split(chomp(line), ",", keepempty = true))
end

function read_manifest(path::AbstractString)
    lines = readlines(path)
    isempty(lines) && error("Empty CSV: $(path)")
    header = _parse_csv_line(first(lines))
    rows = Vector{Dict{String, String}}()
    for (line_no, line) in enumerate(lines[2:end])
        isempty(strip(line)) && continue
        values = _parse_csv_line(line)
        length(values) == length(header) ||
            error("CSV $(path) line $(line_no + 1) has $(length(values)) fields, expected $(length(header))")
        push!(rows, Dict(header .=> values))
    end
    return header, rows
end

function write_manifest(path::AbstractString, header::Vector{String}, rows)
    mkpath(dirname(path))
    open(path, "w") do io
        println(io, join(header, ","))
        for row in rows
            println(io, join((row[column] for column in header), ","))
        end
    end
end

function write_indices(path::AbstractString, count::Integer)
    mkpath(dirname(path))
    open(path, "w") do io
        for idx in 1:count
            println(io, idx)
        end
    end
end

function selected_row(rows, path::AbstractString; system_id::Integer, variant::AbstractString,
                      condition::AbstractString, initial_condition_set::Integer, seed::Integer,
                      clamp_val = nothing)
    matches = [
        row for row in rows
        if row["system_id"] == string(system_id) &&
           row["variant"] == variant &&
           row["condition"] == condition &&
           row["initial_condition_set"] == string(initial_condition_set) &&
           row["seed"] == string(seed) &&
           (clamp_val === nothing || row["clamp_val"] == string(clamp_val))
    ]
    length(matches) == 1 ||
        error("$(path): expected one match for system $(system_id), got $(length(matches))")
    return copy(only(matches))
end

function matching_rows(rows; system_id::Integer, variant::AbstractString,
                       condition::AbstractString, initial_condition_set::Integer, seed::Integer,
                       clamp_val = nothing)
    return [
        row for row in rows
        if row["system_id"] == string(system_id) &&
           row["variant"] == variant &&
           row["condition"] == condition &&
           row["initial_condition_set"] == string(initial_condition_set) &&
           row["seed"] == string(seed) &&
           (clamp_val === nothing || row["clamp_val"] == string(clamp_val))
    ]
end

function _load_sources(sources)
    header = nothing
    loaded = Tuple{String, Vector{Dict{String, String}}}[]
    for source in sources
        source_header, rows = read_manifest(source)
        if header === nothing
            header = source_header
        elseif source_header != header
            error("Header mismatch in $(source)")
        end
        push!(loaded, (source, rows))
    end
    return header::Vector{String}, loaded
end

function select_stage2_rows(sources, systems; variant::AbstractString, condition::AbstractString,
                            initial_condition_set::Integer, seed::Integer)
    selected = Dict{String, String}[]
    header, loaded = _load_sources(sources)
    for system_id in systems
        for (source, rows) in loaded
            push!(
                selected,
                selected_row(
                    rows,
                    source;
                    system_id = system_id,
                    variant = variant,
                    condition = condition,
                    initial_condition_set = initial_condition_set,
                    seed = seed,
                ),
            )
        end
    end
    return header::Vector{String}, selected
end

function select_explicit_stage2_rows(sources, cells; variant::AbstractString,
                                     condition::AbstractString, seed::Integer)
    selected = Dict{String, String}[]
    header, loaded = _load_sources(sources)
    for cell in cells
        matches = Dict{String, String}[]
        for (source, rows) in loaded
            source_matches = matching_rows(
                rows;
                system_id = cell.system_id,
                variant = variant,
                condition = condition,
                initial_condition_set = cell.initial_condition_set,
                seed = seed,
                clamp_val = cell.clamp_val,
            )
            length(source_matches) <= 1 ||
                error("$(source): expected at most one match for cell $(cell.system_id):$(cell.initial_condition_set):$(cell.clamp_val), got $(length(source_matches))")
            isempty(source_matches) || push!(matches, copy(only(source_matches)))
        end
        length(matches) == 1 ||
            error("Expected one match for cell $(cell.system_id):$(cell.initial_condition_set):$(cell.clamp_val), got $(length(matches))")
        push!(selected, only(matches))
    end
    return header, selected
end

function select_smoke_row(source::AbstractString; system_id::Integer, variant::AbstractString,
                          condition::AbstractString, initial_condition_set::Integer, seed::Integer)
    header, rows = read_manifest(source)
    row = selected_row(
        rows,
        source;
        system_id = system_id,
        variant = variant,
        condition = condition,
        initial_condition_set = initial_condition_set,
        seed = seed,
    )
    return header, row
end

function renumber!(rows)
    for (idx, row) in enumerate(rows)
        row["index"] = string(idx)
    end
    return rows
end

function main(args = ARGS)
    sources = _arg_values(args, "--source")
    isempty(sources) && error("At least one --source is required")
    stage2_output = _require_arg(args, "--stage2-output")
    stage2_indices = _require_arg(args, "--stage2-indices")
    smoke_output = _require_arg(args, "--smoke-output")
    smoke_indices = _require_arg(args, "--smoke-indices")
    stage2_cells_value = _arg_value(args, "--stage2-cells")
    stage2_systems = stage2_cells_value === nothing ? _parse_int_list(_require_arg(args, "--stage2-systems")) : Int[]
    smoke_system = parse(Int, _arg_value(args, "--smoke-system"; default = "1"))
    variant = _arg_value(args, "--variant"; default = "evogrow_v2_2_stage_capped")
    condition = _arg_value(args, "--condition"; default = "capped")
    initial_condition_set = parse(Int, _arg_value(args, "--initial-condition-set"; default = "1"))
    seed = parse(Int, _arg_value(args, "--seed"; default = "42"))

    header, stage2_rows = if stage2_cells_value === nothing
        select_stage2_rows(
            sources,
            stage2_systems;
            variant = variant,
            condition = condition,
            initial_condition_set = initial_condition_set,
            seed = seed,
        )
    else
        select_explicit_stage2_rows(
            sources,
            _parse_cell_specs(stage2_cells_value);
            variant = variant,
            condition = condition,
            seed = seed,
        )
    end
    smoke_header, smoke_row = select_smoke_row(
        first(sources);
        system_id = smoke_system,
        variant = variant,
        condition = condition,
        initial_condition_set = initial_condition_set,
        seed = seed,
    )
    smoke_header == header || error("Smoke source header differs from stage-2 sources")

    renumber!(stage2_rows)
    smoke_row["index"] = "1"

    write_manifest(stage2_output, header, stage2_rows)
    write_indices(stage2_indices, length(stage2_rows))
    write_manifest(smoke_output, header, [smoke_row])
    write_indices(smoke_indices, 1)

    println("stage2_manifest=$(stage2_output)")
    println("stage2_rows=$(length(stage2_rows))")
    println("smoke_manifest=$(smoke_output)")
    println("smoke_rows=1")
end

if abspath(PROGRAM_FILE) == @__FILE__
    main()
end

using Test

include(joinpath(@__DIR__, "..", "studies", "regression", "analyze_wasted_search_levels.jl"))

const WP_C5_REPO_ROOT = normpath(joinpath(@__DIR__, ".."))
const WP_C5_FIXTURE_ROOT = joinpath(WP_C5_REPO_ROOT, "outputs")

function _legacy_read_heartbeat(path::AbstractString)
    levels = LevelEvent[]
    start_time = missing
    first_level_row = nothing
    malformed = 0
    open(path, "r") do io
        for line in eachline(io)
            isempty(strip(line)) && continue
            try
                row = JSON3.read(line)
                haskey(row, :timestamp) || continue
                event = String(get(row, :event, ""))
                if event == "start"
                    start_time = parse_timestamp(String(row[:timestamp]))
                elseif event == "level"
                    first_level_row === nothing && (first_level_row = row)
                    stage = haskey(row, :stage) && row[:stage] !== nothing ? Int(row[:stage]) : missing
                    push!(levels, LevelEvent(Int(row[:level]), stage, Float64(row[:best_loss]), parse_timestamp(String(row[:timestamp]))))
                end
            catch
                malformed += 1
            end
        end
    end
    sort!(levels; by = x -> x.level)
    return start_time, levels, first_level_row, malformed
end

function _heartbeat_counts(path::AbstractString)
    starts = 0
    levels = 0
    open(path, "r") do io
        for line in eachline(io)
            isempty(strip(line)) && continue
            row = JSON3.read(line)
            event = String(get(row, :event, ""))
            starts += event == "start" ? 1 : 0
            levels += event == "level" ? 1 : 0
        end
    end
    return starts, levels
end

function _level_signature(levels)
    return [(ev.level, ev.stage, ev.best_loss, ev.timestamp) for ev in levels]
end

function _first_level_signature(row)
    row === nothing && return nothing
    return (Int(row[:level]), Float64(row[:best_loss]), String(row[:timestamp]))
end

function _real_single_segment_heartbeats(limit::Int)
    paths = String[]
    skipped_unreadable = Ref(0)
    on_walk_error = _ -> begin
        skipped_unreadable[] += 1
        nothing
    end
    for (root, _, files) in walkdir(WP_C5_FIXTURE_ROOT; onerror = on_walk_error)
        for file in files
            endswith(file, ".heartbeat.jsonl") || continue
            path = joinpath(root, file)
            starts, levels = _heartbeat_counts(path)
            if starts == 1 && levels >= 3
                push!(paths, path)
            end
        end
    end
    println("WP-C5 fixture search skipped $(skipped_unreadable[]) unreadable directories")
    sort!(paths)
    length(paths) >= limit || error("Need $(limit) real single-segment heartbeat fixtures, found $(length(paths))")
    return paths[1:limit]
end

function _write_without_start(src::AbstractString, dest::AbstractString)
    open(dest, "w") do out
        open(src, "r") do input
            for line in eachline(input)
                isempty(strip(line)) && continue
                row = JSON3.read(line)
                String(get(row, :event, "")) == "start" && continue
                println(out, line)
            end
        end
    end
end

function _append_first_start(src::AbstractString, dest::AbstractString)
    open(dest, "a") do out
        open(src, "r") do input
            for line in eachline(input)
                isempty(strip(line)) && continue
                row = JSON3.read(line)
                if String(get(row, :event, "")) == "start"
                    println(out, line)
                    return
                end
            end
        end
    end
end

function _write_first_start_only(src::AbstractString, dest::AbstractString)
    found_start = false
    open(dest, "w") do out
        open(src, "r") do input
            for line in eachline(input)
                isempty(strip(line)) && continue
                row = JSON3.read(line)
                if String(get(row, :event, "")) == "start"
                    println(out, line)
                    found_start = true
                    break
                end
            end
        end
    end
    found_start && return nothing
    error("Source heartbeat has no start event: $(src)")
end

function _write_concatenated_streams(dest::AbstractString, paths::AbstractString...)
    open(dest, "w") do out
        for path in paths
            text = read(path, String)
            write(out, text)
            endswith(text, "\n") || write(out, "\n")
        end
    end
end

@testset "WP-C5 heartbeat restart segmentation" begin
    first_path, second_path = _real_single_segment_heartbeats(2)

    @testset "single segment matches legacy reader" begin
        old_start, old_levels, old_first, old_malformed = _legacy_read_heartbeat(first_path)
        start, levels, first_row, malformed, segment_info = read_heartbeat(first_path)

        @test start == old_start
        @test _level_signature(levels) == _level_signature(old_levels)
        @test _first_level_signature(first_row) == _first_level_signature(old_first)
        @test malformed == old_malformed
        @test segment_info.total_segments == 1
        @test segment_info.selected_segment == 1
        @test segment_info.discarded_segments == 0
        @test segment_info.discarded_level_events == 0
    end

    @testset "concatenated real streams select only the second segment" begin
        mktempdir() do dir
            concatenated = joinpath(dir, "two_real_streams.heartbeat.jsonl")
            _write_concatenated_streams(concatenated, first_path, second_path)

            expected_start, expected_levels, expected_first, expected_malformed = _legacy_read_heartbeat(second_path)
            start, levels, first_row, malformed, segment_info = read_heartbeat(concatenated)
            _, first_level_count = _heartbeat_counts(first_path)

            @test start == expected_start
            @test _level_signature(levels) == _level_signature(expected_levels)
            @test _first_level_signature(first_row) == _first_level_signature(expected_first)
            @test malformed == expected_malformed
            @test segment_info.total_segments == 2
            @test segment_info.selected_segment == 2
            @test segment_info.discarded_segments == 1
            @test segment_info.discarded_level_events == first_level_count
        end
    end

    @testset "start-less stream remains analyzable" begin
        mktempdir() do dir
            no_start = joinpath(dir, "no_start.heartbeat.jsonl")
            _write_without_start(first_path, no_start)

            _, expected_levels, expected_first, expected_malformed = _legacy_read_heartbeat(no_start)
            start, levels, first_row, malformed, segment_info = read_heartbeat(no_start)

            @test start === missing
            @test _level_signature(levels) == _level_signature(expected_levels)
            @test _first_level_signature(first_row) == _first_level_signature(expected_first)
            @test malformed == expected_malformed
            @test segment_info.total_segments == 1
            @test segment_info.selected_segment == 1
            @test segment_info.discarded_segments == 0
            @test segment_info.discarded_level_events == 0
        end
    end

    @testset "empty trailing segment does not erase the last non-empty segment" begin
        mktempdir() do dir
            trailing_empty = joinpath(dir, "trailing_empty.heartbeat.jsonl")
            write(trailing_empty, read(first_path, String))
            _append_first_start(second_path, trailing_empty)

            expected_start, expected_levels, expected_first, expected_malformed = _legacy_read_heartbeat(first_path)
            start, levels, first_row, malformed, segment_info = read_heartbeat(trailing_empty)

            @test start == expected_start
            @test _level_signature(levels) == _level_signature(expected_levels)
            @test _first_level_signature(first_row) == _first_level_signature(expected_first)
            @test malformed == expected_malformed
            @test segment_info.total_segments == 2
            @test segment_info.selected_segment == 1
            @test segment_info.discarded_segments == 1
            @test segment_info.discarded_level_events == 0
        end
    end

    @testset "stream without evaluable level events returns empty result" begin
        mktempdir() do dir
            start_only = joinpath(dir, "start_only.heartbeat.jsonl")
            _write_first_start_only(first_path, start_only)

            start, levels, first_row, malformed, segment_info = read_heartbeat(start_only)

            @test start === missing
            @test isempty(levels)
            @test first_row === nothing
            @test malformed == 0
            @test segment_info.total_segments == 1
            @test segment_info.selected_segment === missing
            @test segment_info.discarded_segments == 1
            @test segment_info.discarded_level_events == 0
        end
    end
end

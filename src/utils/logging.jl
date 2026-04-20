module EvoLogger

using Dates

export DEBUG, INFO, WARN, ERROR
export set_level, current_level, level_name, reset_timer
export log_debug, log_info, log_warn, log_error, log_exception
export time_block

# -----------------------
# Log Levels
# -----------------------
const DEBUG = 10
const INFO  = 20
const WARN  = 30
const ERROR = 40

const LEVEL_NAMES = Dict(
    DEBUG => "DEBUG",
    INFO  => "INFO ",
    WARN  => "WARN ",
    ERROR => "ERROR"
)

# -----------------------
# Global State
# -----------------------
mutable struct LoggerState
    level::Int
    start_time::Float64
end

const LOGGER = LoggerState(INFO, time())

# -----------------------
# Utilities
# -----------------------
function level_name(level::Int)
    return get(LEVEL_NAMES, level, "UNKWN")
end

function current_level()
    return LOGGER.level
end

function _normalize_level(level)
    if level isa Int
        return level
    elseif level isa Symbol
        return _normalize_level(String(level))
    elseif level isa AbstractString
        s = lowercase(strip(level))
        if s == "debug"
            return DEBUG
        elseif s == "info"
            return INFO
        elseif s == "warn" || s == "warning"
            return WARN
        elseif s == "error"
            return ERROR
        else
            error("Unknown log level: $level")
        end
    else
        error("Unsupported log level type: $(typeof(level))")
    end
end

function _format_context(context)
    isempty(context) && return ""
    parts = String[]
    for (k, v) in context
        push!(parts, "$(k)=$(v)")
    end
    return " | " * join(parts, ", ")
end

# -----------------------
# Config
# -----------------------
function set_level(level)
    LOGGER.level = _normalize_level(level)
end

function reset_timer(; log_reset::Bool=false)
    LOGGER.start_time = time()
    if log_reset
        log_info("Logger timer reset")
    end
end

# -----------------------
# Core Logging
# -----------------------
function _log(level::Int, msg::AbstractString; context=Dict())
    if level < LOGGER.level
        return
    end

    t = time()
    elapsed = t - LOGGER.start_time
    timestamp = Dates.format(now(), "HH:MM:SS")
    ctx_str = _format_context(context)

    println("[$timestamp | $(round(elapsed, digits=1))s | $(level_name(level))] $msg$ctx_str")
end

# -----------------------
# Public API
# -----------------------
log_debug(msg; context=Dict()) = _log(DEBUG, msg; context=context)
log_info(msg;  context=Dict()) = _log(INFO,  msg; context=context)
log_warn(msg;  context=Dict()) = _log(WARN,  msg; context=context)
log_error(msg; context=Dict()) = _log(ERROR, msg; context=context)

function log_exception(msg, err; context=Dict())
    merged = Dict(context)
    merged[:exception_type] = typeof(err)
    merged[:exception] = sprint(showerror, err)
    _log(ERROR, msg; context=merged)
end

# -----------------------
# Timing Helper
# -----------------------
"""
    time_block(msg; level=INFO, context=Dict())

Create a closure-based timer.

Example:
    done = time_block("child 5", level=DEBUG, context=Dict(:stage=>2))
    ...
    done()
"""
function time_block(msg; level=INFO, context=Dict())
    lvl = _normalize_level(level)
    t0 = time()
    _log(lvl, "START: $msg"; context=context)

    return () -> begin
        dt = time() - t0
        _log(lvl, "DONE: $msg (t=$(round(dt, digits=2))s)"; context=context)
    end
end

end
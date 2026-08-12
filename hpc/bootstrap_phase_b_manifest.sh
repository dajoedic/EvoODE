#!/usr/bin/env bash
# Build the Phase B manifest and per-dimension index lists inside the image.

set -euo pipefail

: "${EVOODE_IMAGE:?Set EVOODE_IMAGE to the Apptainer image path}"
: "${EVOODE_OUTPUT_ROOT:?Set EVOODE_OUTPUT_ROOT to a writable throwaway or campaign output directory}"

mkdir -p "${EVOODE_OUTPUT_ROOT}"

apptainer exec \
    --cleanenv \
    --bind "${EVOODE_OUTPUT_ROOT}:/outputs" \
    "${EVOODE_IMAGE}" \
    julia --project=/opt/EvoODE /opt/EvoODE/studies/regression/generate_phase_b_manifest.jl \
        --output /outputs/manifest.csv \
        --all-dimensions

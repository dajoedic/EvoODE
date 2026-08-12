#!/usr/bin/env bash
# Tiny Phase B smoke array. Submit as 1-3 tasks against the 1D index list only.
#
# Example:
#   sbatch --array=1-3 --time=01:00:00 hpc/slurm_phase_b_smoke.sh

#SBATCH --job-name=evoode-smoke
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --output=logs/evoode_smoke_%A_%a.out
#SBATCH --error=logs/evoode_smoke_%A_%a.err

set -euo pipefail

: "${EVOODE_IMAGE:?Set EVOODE_IMAGE to the Apptainer image path}"
: "${EVOODE_OUTPUT_ROOT:?Set EVOODE_OUTPUT_ROOT to a writable throwaway output directory}"

MANIFEST="${EVOODE_OUTPUT_ROOT}/manifest.csv"
INDEX_LIST="${EVOODE_OUTPUT_ROOT}/indices_dim1.txt"
TASK_DIR="${EVOODE_OUTPUT_ROOT}/tasks"

mkdir -p "${TASK_DIR}" "${EVOODE_OUTPUT_ROOT}/logs" logs

CELL_INDEX="$(sed -n "${SLURM_ARRAY_TASK_ID}p" "${INDEX_LIST}")"
if [[ -z "${CELL_INDEX}" ]]; then
    echo "No 1D manifest index for SLURM_ARRAY_TASK_ID=${SLURM_ARRAY_TASK_ID} in ${INDEX_LIST}" >&2
    exit 2
fi

apptainer exec \
    --cleanenv \
    --bind "${EVOODE_OUTPUT_ROOT}:/outputs" \
    "${EVOODE_IMAGE}" \
    julia --project=/opt/EvoODE /opt/EvoODE/studies/regression/run_batch_cell.jl \
        --manifest /outputs/manifest.csv \
        --output-dir /outputs/tasks \
        "${CELL_INDEX}"

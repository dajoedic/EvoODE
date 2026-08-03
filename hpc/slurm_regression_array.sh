#!/usr/bin/env bash
# Example Slurm array worker for one dimension class.
#
# Submit one class at a time with a class-specific array range and walltime, for example:
#   sbatch --array=1-48%8 --time=01:00:00 --export=ALL,DIM=1 hpc/slurm_regression_array.sh
#   sbatch --array=1-48%8 --time=12:00:00 --export=ALL,DIM=2 hpc/slurm_regression_array.sh
#   sbatch --array=1-24%4 --time=48:00:00 --export=ALL,DIM=4 hpc/slurm_regression_array.sh
#
# The manifest is global; DIM selects an index-list file generated from it.

#SBATCH --job-name=evoode-regression
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --output=logs/evoode_regression_%A_%a.out
#SBATCH --error=logs/evoode_regression_%A_%a.err

set -euo pipefail

: "${DIM:?Set DIM to the system dimension class, e.g. 1, 2, or 4}"
: "${EVOODE_IMAGE:?Set EVOODE_IMAGE to the Apptainer image path}"
: "${EVOODE_OUTPUT_ROOT:?Set EVOODE_OUTPUT_ROOT to a writable output directory}"

MANIFEST="${EVOODE_OUTPUT_ROOT}/manifest.csv"
INDEX_LIST="${EVOODE_OUTPUT_ROOT}/indices_dim${DIM}.txt"
TASK_DIR="${EVOODE_OUTPUT_ROOT}/tasks"

mkdir -p "${EVOODE_OUTPUT_ROOT}/tasks" "${EVOODE_OUTPUT_ROOT}/logs" logs

CELL_INDEX="$(sed -n "${SLURM_ARRAY_TASK_ID}p" "${INDEX_LIST}")"
if [[ -z "${CELL_INDEX}" ]]; then
    echo "No manifest index for SLURM_ARRAY_TASK_ID=${SLURM_ARRAY_TASK_ID} in ${INDEX_LIST}" >&2
    exit 2
fi

apptainer exec \
    --cleanenv \
    --bind "${EVOODE_OUTPUT_ROOT}:/outputs" \
    "${EVOODE_IMAGE}" \
    julia --project=/opt/EvoODE /opt/EvoODE/studies/regression/run_batch_cell.jl \
        --manifest "${MANIFEST}" \
        --output-dir "${TASK_DIR}" \
        "${CELL_INDEX}"

FROM julia:1.12.6-bookworm

ENV JULIA_NUM_THREADS=1 \
    OPENBLAS_NUM_THREADS=1 \
    JULIA_CPU_TARGET="generic;znver3,clone_all" \
    JULIA_DEPOT_PATH=/opt/julia_depot \
    EVO_BATCH_MANIFEST=/outputs/manifest.csv \
    EVO_BATCH_OUTPUT_DIR=/outputs/tasks \
    HOME=/tmp

WORKDIR /opt/EvoODE

COPY Project.toml /opt/EvoODE/Project.toml
COPY Manifest.toml /opt/EvoODE/Manifest.toml
COPY src /opt/EvoODE/src
COPY studies /opt/EvoODE/studies
COPY benchmarks /opt/EvoODE/benchmarks

RUN set -eu; \
    mkdir -p /opt/julia_depot /outputs; \
    julia_version="$(julia --version | awk '{print $3}')"; \
    project_sha256="$(sha256sum Project.toml | awk '{print $1}')"; \
    manifest_sha256="$(sha256sum Manifest.toml | awk '{print $1}')"; \
    printf '{"julia_version":"%s","project_toml_sha256":"%s","manifest_toml_sha256":"%s"}\n' \
        "$julia_version" "$project_sha256" "$manifest_sha256" \
        > /opt/EvoODE/build_provenance.json; \
    julia --project=. -e 'import Pkg; Pkg.instantiate(); Pkg.precompile()'; \
    chgrp -R 0 /opt/EvoODE /opt/julia_depot /outputs; \
    chmod -R g=u /opt/EvoODE /opt/julia_depot /outputs

ENTRYPOINT ["julia", "--project=/opt/EvoODE", "/opt/EvoODE/studies/regression/run_batch_cell.jl"]

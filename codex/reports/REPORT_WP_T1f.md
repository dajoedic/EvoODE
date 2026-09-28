# WP-T1f Report

## Status

Implemented WP-T1f as a repair of WP-T1d with warm starts from the true coefficients.

Julia was not executed in this Codex environment, per `codex/CODEX_PROTOCOL.md` and the task text.
This package is therefore reported as `blocked`: Python export/tests and YAML parsing were run, but
Claude must run the Julia acceptance checks.

## Changed Files

- `studies/regression/export_wp_t1f_true_coefficients.py`
- `studies/regression/wp_t1f_true_coefficients.json`
- `studies/regression/wp_t1d_neighbourhood_loss.jl`
- `studies/regression/wp_t1f_warm_neighbourhood.jl`
- `analysis/tests/test_wp_t1f_true_coefficients.py`
- `test/test_wp_t1f_warm_neighbourhood.jl`
- `k8s/wp_t1f_bootstrap_index_job.yaml`
- `k8s/wp_t1f_indexed_smoke_job.yaml`
- `k8s/wp_t1f_indexed_campaign_job.yaml`
- `SCRIPTS.md`
- `codex/reports/REPORT_WP_T1f.md`
- `codex/STATUS.md`

## Implementation Notes

- The coefficient export reuses the WP-N26 extraction function
  `true_coefficients_for_phasec_terms` from `aggregate_phaseb_structure_metrics.py`.
- The exporter hard-checks `phase_c_support.json` against the classification
  `matched_basis_terms` before writing coefficients. Exact dim-2/dim-3 systems exported: 18.
- `wp_t1d_neighbourhood_loss.jl` only received defaulted `p0` and `max_fit_attempts` parameters in
  `fit_fixed_structure_phase_c`; existing T1d calls keep the previous defaults.
- `wp_t1f_warm_neighbourhood.jl` includes T1d and adds control/floor/neighbour-warm/truth-cold
  roles, control abort at `1e-4`, `m = 10` cold truth starts, smoke limits of 5 neighbours per
  class and 2 cold starts, and aggregate-only support for both T1f rows and old T1d rows as
  `cold_reference`.
- The campaign manifest uses `completions: 36`, `parallelism: 6`, `EVO_T1F_*` environment names,
  and `activeDeadlineSeconds: "<DEADLINE_SECONDS>"`.

## Commands Run

```powershell
python studies/regression/export_wp_t1f_true_coefficients.py
```

Result: wrote `studies/regression/wp_t1f_true_coefficients.json`.

```powershell
python -m pytest analysis/tests/test_wp_t1f_true_coefficients.py -q --basetemp .pytest_tmp_t1f
```

Result: 2 passed in 1.21 s.

```powershell
python -c "import yaml; paths=['k8s/wp_t1f_bootstrap_index_job.yaml','k8s/wp_t1f_indexed_smoke_job.yaml','k8s/wp_t1f_indexed_campaign_job.yaml']; [yaml.safe_load(open(p, encoding='utf-8')) for p in paths]; print('\n'.join('parsed '+p for p in paths))"
```

Result: all three WP-T1f YAML files parsed.

Static checks:

```powershell
rg -n "\b(true|false|nothing)\s*=" studies/regression/wp_t1f_warm_neighbourhood.jl test/test_wp_t1f_warm_neighbourhood.jl studies/regression/wp_t1d_neighbourhood_loss.jl
```

Result: no matches.

```powershell
rg -n "WP_T1D_REFERENCE_SECONDS_PER_FIT|phase_b_reference|reference_seconds" studies/regression/wp_t1f_warm_neighbourhood.jl
```

Result: no matches.

## Julia Commands for Claude

Run in this order:

```text
julia --project=. test/test_wp_t1f_warm_neighbourhood.jl
```

```text
julia --project=. studies/regression/wp_t1f_warm_neighbourhood.jl --self-test --fresh
```

```text
julia --project=. studies/regression/wp_t1f_warm_neighbourhood.jl --smoke --fresh
```

```text
julia --project=. studies/regression/wp_t1f_warm_neighbourhood.jl --aggregate-only --input-dir outputs/wp_t1d_neighbourhood/orion_5a87efb/
```

## Deviations

None intentional from the WP-T1f design. The only change to WP-T1d is the defaulted optional
parameter plumbing needed by WP-T1f.

## Not Run

- No Julia tests, self-test, smoke, aggregate-only, local campaign, Docker, Git, or Orion command was
  run by Codex.
- The pytest temporary directory cleanup command was rejected by the command policy after tests; no
  evidence files depend on that directory.

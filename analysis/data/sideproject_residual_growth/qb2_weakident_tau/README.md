# Q-B B2 — WeakIdent τ grid on the Q9 cells (laptop, 2026-11-08/09)

Protocol `docs/sideproject_residual_growth_protocol_qb.md`, amendment 5 (`4b1b388`, user-approved, written after a
first look at τ = 0.05, declared as such). Adapter `baselines/run_weakident_c6.py` at `09491e3`, `--taus grid`,
10 shards, `OPENBLAS_NUM_THREADS=OMP_NUM_THREADS=1`, 2026-11-08 21:09:58 → 2026-11-09 03:09:19.

- `details.csv.gz` (gzip, one header): 59,976 rows = 4,284 Q9 cells × {`weakident_native`, `weakident_trig`} ×
  τ ∈ {0, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2}. Per arm and τ: dims 1–3 4,148 `success`, 0 failures; dim 4 136 "not
  supported by the reference implementation". Library ids `qb2_weakident_v1_poly3_{native|trig}_tau<τ>`; τ = 0.05 keeps
  the first run's id. 0 duplicate keys. One environment over all shards (`environment.json`).
- Dictionary built once per cell, identification run per τ with the same per-cell CV seed. 41,698 rows carry
  `weakident_evaluation_reused_from_tau`: their identified model (coefficients and term names) equals that of an
  earlier τ of the same cell, so the evaluation was copied, not recomputed.
- **Control:** the τ = 0.05 rows equal `../qb2_weakident/details.csv` in all 8,568 rows on every field except
  `fit_elapsed_s_context`, `weakident_tau` (new) and `weakident_evaluation_reused_from_tau` (new): 0 differences.

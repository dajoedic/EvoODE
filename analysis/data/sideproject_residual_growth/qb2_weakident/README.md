# Q-B B2 — WeakIdent on the Q9 cells (laptop, 2026-11-08)

Protocol `docs/sideproject_residual_growth_protocol_qb.md` (frozen `4309870`, technical amendments 1–4).
Adapter `baselines/run_weakident_c6.py` at `8d2ccb5`, 8 shards, `OPENBLAS_NUM_THREADS=OMP_NUM_THREADS=1`.

- `details.csv`: 8,568 rows = 4,284 Q9 cells × {`weakident_native` (B2a), `weakident_trig` (B2b)}.
  dims 1–3 `fit_status = success` (4,148 per arm, 0 failures); dim 4 (136 per arm) "not supported by the reference
  implementation" (amendment 3). Observed-data hashes checked against the Q9 path file and interpolated-input hashes
  against the W1-interp manifest on every cell (a mismatch aborts; none occurred). One environment over all shards
  (`environment.json`).
- Merge note: the shard writer at `8d2ccb5` emitted the three `q5w_interpolat*` fields only on ρ = 0.5 rows, so a
  shard's header followed its first row. The fields were always trailing and the 65 leading columns identical in every
  row, so the merge pads ρ = 0 rows with empty values — no value changed. The adapter now always emits the fields.

# Q9 data freeze, 2026-11-23

Final WISP run Q9 (image `cdfaa7d`, arm C1000), complete: 4,284 / 4,284 cells; 4,270 record files on the NFS plus the
14 empty-pool cells (system 9, IC 2, sigma >= 0.03; nothing to fit, scored as misses as in Q7/Q8).

- `cells/`: `build_wisp_paper_cells.py --protocol Q9` with references WP-N47, WSINDy, WeakIdent, B1 (`ca849b4`) and
  B3 ODEFormer (`ca849b4`); `complete_cells = 4284`, one settings fingerprint. `reference_cells.csv` is gzipped.
- `claims/`: `q9a_claims.py --strict` (protocol Q9-A, frozen `b7bb398`). C1, C2, C4-C8 hold; C3 and C9 fail.
- Against the non-strict 2026-11-19 build (4,280 cells): claims and all 670 macros identical; only the dim-3 feasible
  sigma = 0 / rho = 0.5 rec/gen subgroup rates (0.25 -> 0.5, 2 units) and noise-free dim-3 cost quantiles move.
- Raw records: `outputs/sideproject_q9_cdfaa7d…/q9_final_2026-11-23.tgz` (gitignored), hash in `RAW_SHA256.txt`.

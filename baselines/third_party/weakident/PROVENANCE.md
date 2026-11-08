# WeakIdent — provenance

- Source: https://github.com/sunghakang/WeakIdent (official repository named in Tang, Liao, Kuske, Kang 2023,
  J. Comput. Phys. 483:112069)
- Commit: `be14358b38f9cdb40ce1a0aeb127039f91d1410e` (2023-03-31 00:24:37 −0400), cloned 2026-11-08
- Licence: Apache-2.0 (`LICENSE`, copied unchanged)
- Copied unchanged from `WeakIdent-Python/`: `main.py`, `model.py`, `README.md`, `environment.yml`, `utils/`,
  `configs/config_8.yaml` (2D linear ODE), `configs/config_11.yaml` (Lotka–Volterra ODE), and the matching example data
  `dataset-Python/Linear2d.npy`, `dataset-Python/LotkaVolterra.npy`. Other datasets (PDE examples, ~46 MB) not copied.
- Modifications: **none** in this folder. The B2b dictionary extension (sin/cos) of protocol Q-B lives outside this
  folder, in the adapter, and is documented there.

Authors' ODE settings (all ODE configs 8–12 of the repository agree): `Tau = 0.05`, `max_dt = 1`, `max_dx = 0`,
`use_cross_der = False`; `max_poly` varies by example (3–6) — Q-B fixes `max_poly = 3`. `sigma_SNR` and `stride_*`
are the repository's own data corruption and subsampling of its example data; on our already noisy C-6 data they are
set to 0 noise and stride 1.

## B2b extension (outside this folder)

`baselines/run_weakident_c6.py:build_dictionary` is the only B2b dictionary
extension. It appends `sin(u_i)` and `cos(u_i)` weak columns to the native
degree-3 polynomial dictionary, using the reference ODE FFT test function,
convolution and sample indices. The ODE scale matrix remains a copy of the
feature matrix. Dynamic-region selection uses the native columns; narrow-fit,
trimming, sparsity limits and cross-validation are the unmodified reference
functions. With the extension disabled, dictionary construction takes the
native path. No implementation file in this folder is modified.

The adapter calls feature construction and identification directly, bypassing
example-data loading/noise injection and quality-table generation. ODE settings
are `max_dx=0`, `max_poly=3`, skips 1, `use_cross_der=False`, `tau=0.05`; the
reference uses temporal derivative order 1 internally. Dimension 4 is marked
unsupported without fitting, per protocol amendment 3.

The authors' cross-validation also calls `np.random.permutation`
(`utils/calculations.py:290`) independently of noise injection. The Q-B2 probe
found a repeated-cell difference with noise off. Resolved (protocol Q-B, technical
amendment 4): the adapter seeds the global NumPy RNG before every fit with a
per-cell seed (SHA-256 of the cell key, as for E-SINDy/Weak-SINDy), identical for
both arms and recorded per row as `weakident_cv_seed`. Repeat and no-trig identity
controls then pass on all probe cells.

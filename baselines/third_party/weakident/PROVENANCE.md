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

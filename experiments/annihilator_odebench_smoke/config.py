"""Frozen configuration for the ODEBench smoke test."""

from __future__ import annotations

from pathlib import Path

from experiments.annihilator_gate2a_v3.config import CLASSES, Settings


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
CATALOG = Path("benchmarks/data/strogatz_extended.json")

SYSTEM_IDS = (3, 7, 19, 21)
ETA_LEVELS = (0.0, 0.01)
CLEAN_SEEDS = (0,)
NOISY_SEEDS = (60000, 60001, 60002, 60003, 60004)
METHODS = ("annihilator", "sindy", "wsindy")

N_TIME = 512
T0 = 0.0
T1 = 10.0
TRAINING_TRAJECTORIES = 2
TEST_TRAJECTORIES = 3

ORACLE_DIGITS = 100
ORACLE_POINTS = 220
ORACLE_REL_TOL = 1e-60

SEARCH_SETTINGS = Settings(ell_max=4, sigma_floor_factor=3.386508e-7, boot_reps=50)

STRUCT_NRMSE_F_MAX = 0.05
SINDY_THRESHOLDS = tuple(float(10 ** (-3 + 3 * i / 19)) for i in range(20))
SINDY_LIBRARY_TERMS = ("1", "x", "x^2", "x^3", "log(x)", "x log(x)", "exp(-x)", "sin(x)", "cos(x)")

TRUE_BASELINE_TERMS = {
    3: {"x", "x^2"},
    7: {"x", "x log(x)"},
    21: {"1", "x", "exp(-x)"},
    19: None,
}


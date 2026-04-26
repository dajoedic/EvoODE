import matplotlib as mpl


VARIANT_COLORS: dict[str, str] = {
    "evogrow_v1": "#0072B2",
    "evogrow_v2_1": "#009E73",
    "evogrow_v2_2_progression": "#D55E00",
    "evogrow_v2_2_passive": "#CC79A7",
    "evogrow_v2_2_soft": "#E69F00",
    "gp_baseline": "#56B4E9",
}

VARIANT_LABELS: dict[str, str] = {
    "evogrow_v1": "EvoGrow v1 (flat)",
    "evogrow_v2_1": "EvoGrow v2.1",
    "evogrow_v2_2_progression": "EvoGrow v2.2 (progression)",
    "evogrow_v2_2_passive": "EvoGrow v2.2 (passive)",
    "evogrow_v2_2_soft": "EvoGrow v2.2 (soft)",
    "gp_baseline": "GP baseline",
}


def apply_style() -> None:
    mpl.rcParams.update(
        {
            "font.size": 10,
            "figure.dpi": 150,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "figure.autolayout": True,
        }
    )

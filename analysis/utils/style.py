import matplotlib as mpl


VARIANT_COLORS: dict[str, str] = {
    "evogrow_v1": "#0072B2",
    "evogrow_v2_1": "#009E73",
    "evogrow_v2_2_stage_local": "#D55E00",
    "evogrow_v2_2_stage_capped": "#6F4E7C",
    "evogrow_v2_2_passive": "#CC79A7",
    "evogrow_v2_2_soft": "#E69F00",
    "evogrow_v3": "#44AA99",
    "evogrow_v3_stage_capped": "#882255",
    "gp_baseline": "#56B4E9",
}

VARIANT_LABELS: dict[str, str] = {
    "evogrow_v1": "EvoGrow v1 (flat)",
    "evogrow_v2_1": "EvoGrow v2.1",
    "evogrow_v2_2_stage_local": "EvoGrow v2.2 (progression)",
    "evogrow_v2_2_stage_capped": "EvoGrow v2.2 (stage capped)",
    "evogrow_v2_2_passive": "EvoGrow v2.2 (passive)",
    "evogrow_v2_2_soft": "EvoGrow v2.2 (soft)",
    "evogrow_v3": "EvoGrow v3",
    "evogrow_v3_stage_capped": "EvoGrow v3 (stage capped)",
    "gp_baseline": "GP baseline",
}

FALLBACK_VARIANT_COLORS = [
    "#332288",
    "#117733",
    "#999933",
    "#88CCEE",
    "#DDCC77",
    "#AA4499",
]


def ordered_variants(observed_variants, preferred_order: list[str]) -> list[str]:
    observed = [str(variant) for variant in observed_variants]
    observed_set = set(observed)
    ordered = [variant for variant in preferred_order if variant in observed_set]
    extras = sorted(observed_set.difference(preferred_order))
    return ordered + extras


def variant_label(variant_slug: str) -> str:
    return VARIANT_LABELS.get(variant_slug, variant_slug)


def variant_color(variant_slug: str) -> str:
    if variant_slug in VARIANT_COLORS:
        return VARIANT_COLORS[variant_slug]
    index = sum(ord(char) for char in variant_slug) % len(FALLBACK_VARIANT_COLORS)
    return FALLBACK_VARIANT_COLORS[index]


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

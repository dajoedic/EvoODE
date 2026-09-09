from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd

from utils.metrics import check_required_columns


RAW_SUPPORT_MATCH = "raw_support_terms_exact_match"
PRUNED_SUPPORT_MATCH = "pruned_support_terms_exact_match"


@dataclass(frozen=True)
class RegistrySupportMatchDefinition:
    source: str
    definition: str


def _unique_text_values(df: pd.DataFrame, column: str) -> set[str]:
    if column not in df.columns:
        return set()
    values = df[column].dropna().astype(str).str.strip().str.lower()
    return {value for value in values if value}


def infer_exact_support_match_definition(
    registry: pd.DataFrame, source: str | Path = "<registry>"
) -> RegistrySupportMatchDefinition:
    """Infer the semantic definition of exact_support_match from registry metadata."""
    check_required_columns(registry, ["exact_support_match"])
    source_text = str(source)

    explicit = _unique_text_values(registry, "exact_support_match_definition")
    if explicit:
        if len(explicit) != 1:
            raise ValueError(
                f"{source_text} mixes exact_support_match definitions: {sorted(explicit)}"
            )
        value = next(iter(explicit))
        if value in {RAW_SUPPORT_MATCH, "raw", "raw_support_match"}:
            return RegistrySupportMatchDefinition(source_text, RAW_SUPPORT_MATCH)
        if value in {PRUNED_SUPPORT_MATCH, "pruned", "pruned_match"}:
            return RegistrySupportMatchDefinition(source_text, PRUNED_SUPPORT_MATCH)
        raise ValueError(
            f"{source_text} has unknown exact_support_match definition: {value}"
        )

    experiment_ids = _unique_text_values(registry, "experiment_id")
    phases = _unique_text_values(registry, "phase")
    run_types = _unique_text_values(registry, "run_type")

    phase_b = (
        experiment_ids == {"paper1_phaseb_v1"}
        or phases == {"b"}
        or run_types == {"campaign_cell"}
    )
    phase_a = (
        experiment_ids == {"paper1_phasea_v1"}
        or phases == {"a"}
        or any(value.startswith("paper1_phasea") for value in experiment_ids)
    )

    if phase_a and phase_b:
        raise ValueError(
            f"{source_text} contains conflicting Phase-A and Phase-B metadata"
        )
    if phase_b:
        return RegistrySupportMatchDefinition(source_text, PRUNED_SUPPORT_MATCH)
    if phase_a:
        return RegistrySupportMatchDefinition(source_text, RAW_SUPPORT_MATCH)

    raise ValueError(
        f"{source_text} does not carry enough metadata to define exact_support_match"
    )


def require_compatible_exact_support_match_definitions(
    registries: Iterable[tuple[pd.DataFrame, str | Path]]
) -> RegistrySupportMatchDefinition:
    definitions = [
        infer_exact_support_match_definition(registry, source)
        for registry, source in registries
    ]
    if not definitions:
        raise ValueError("No registries were provided")

    unique = {definition.definition for definition in definitions}
    if len(unique) != 1:
        details = ", ".join(
            f"{definition.source}={definition.definition}"
            for definition in definitions
        )
        raise ValueError(f"Conflicting exact_support_match definitions: {details}")
    return definitions[0]

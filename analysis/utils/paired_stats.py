import math
import random
from collections.abc import Callable, Iterable
from typing import Any

import pandas as pd


BOOTSTRAP_ALPHA = 0.05


def fail(message: str) -> None:
    raise ValueError(message)


def coerce_bool(value: Any) -> int | None:
    if pd.isna(value):
        return None
    if isinstance(value, bool):
        return int(value)
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "y"}:
        return 1
    if text in {"false", "0", "no", "n"}:
        return 0
    return None


def median(values: list[float]) -> float:
    if not values:
        fail("cannot compute median of an empty value set")
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return float(ordered[mid])
    return float((ordered[mid - 1] + ordered[mid]) / 2.0)


def mean(values: list[float]) -> float:
    if not values:
        fail("cannot compute mean of an empty value set")
    return float(sum(values) / len(values))


def share(values: list[float]) -> float:
    if not values:
        fail("cannot compute share of an empty value set")
    return float(sum(values) / len(values))


def percentile(values: list[float], probability: float) -> float:
    if not values:
        fail("cannot compute percentile of an empty value set")
    ordered = sorted(values)
    if len(ordered) == 1:
        return float(ordered[0])
    position = probability * (len(ordered) - 1)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return float(ordered[lower])
    fraction = position - lower
    return float(ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction)


def exact_binomial_two_sided(discordant: int, off_only: int) -> float:
    if discordant == 0:
        return 1.0
    tail = min(off_only, discordant - off_only)
    probability = sum(math.comb(discordant, k) for k in range(tail + 1)) / (2**discordant)
    return min(1.0, 2.0 * probability)


def cluster_values(df: pd.DataFrame, diff_column: str) -> dict[int, list[float]]:
    clusters: dict[int, list[float]] = {}
    for system_id, group in df.groupby("system_id", sort=True):
        clusters[int(system_id)] = [float(value) for value in group[diff_column].tolist()]
    if not clusters:
        fail(f"no clusters available for {diff_column}")
    return clusters


def cluster_bootstrap_ci(
    clusters: dict[int, list[float]],
    statistic: Callable[[list[float]], float],
    rng: random.Random,
    replicates: int,
) -> tuple[float, float]:
    system_ids = list(clusters)
    if not system_ids:
        fail("no clusters available for bootstrap")
    estimates = []
    for _ in range(replicates):
        sampled_values: list[float] = []
        for _ in system_ids:
            sampled_values.extend(clusters[rng.choice(system_ids)])
        estimates.append(statistic(sampled_values))
    return (
        percentile(estimates, BOOTSTRAP_ALPHA / 2.0),
        percentile(estimates, 1.0 - BOOTSTRAP_ALPHA / 2.0),
    )


def cluster_permutation_p(
    clusters: dict[int, list[float]],
    statistic: Callable[[list[float]], float],
    rng: random.Random,
    permutations: int,
) -> float:
    observed_values = [value for values in clusters.values() for value in values]
    observed = statistic(observed_values)
    threshold = abs(observed)
    extreme = 0
    system_items = list(clusters.items())
    for _ in range(permutations):
        permuted_values: list[float] = []
        for _, values in system_items:
            sign = -1.0 if rng.random() < 0.5 else 1.0
            permuted_values.extend(sign * value for value in values)
        if abs(statistic(permuted_values)) >= threshold - 1e-15:
            extreme += 1
    return (extreme + 1.0) / (permutations + 1.0)


def contingency_table(
    df: pd.DataFrame,
    off_column: str = "exact_support_match_off",
    on_column: str = "exact_support_match_on",
) -> dict[str, int]:
    pairs = df[[off_column, on_column]].dropna()
    return {
        "off_0_on_0": int(((pairs[off_column] == 0) & (pairs[on_column] == 0)).sum()),
        "off_0_on_1": int(((pairs[off_column] == 0) & (pairs[on_column] == 1)).sum()),
        "off_1_on_0": int(((pairs[off_column] == 1) & (pairs[on_column] == 0)).sum()),
        "off_1_on_1": int(((pairs[off_column] == 1) & (pairs[on_column] == 1)).sum()),
    }


def normalize_pair_value(value: Any) -> Any:
    if pd.isna(value):
        return None
    return value


def format_pair_key(key_columns: Iterable[str], key: Any) -> str:
    values = key if isinstance(key, tuple) else (key,)
    return ", ".join(
        f"{column}={value}" for column, value in zip(key_columns, values, strict=True)
    )


def pair_registry_by_conditions(
    registry: pd.DataFrame,
    *,
    key_columns: list[str],
    condition_column: str,
    left_condition: str,
    right_condition: str,
    expected_total_pairs: int,
    allowed_difference_columns: set[str] | None = None,
    enforce_condition_equality: bool = False,
) -> list[tuple[Any, pd.Series, pd.Series]]:
    pairs: list[tuple[Any, pd.Series, pd.Series]] = []
    for key, group in registry.groupby(key_columns, sort=True, dropna=False):
        by_condition = {row[condition_column]: row for _, row in group.iterrows()}
        expected_conditions = {left_condition, right_condition}
        if set(by_condition) != expected_conditions or len(group) != 2:
            fail(f"incomplete or duplicate pair for {format_pair_key(key_columns, key)}")
        left = by_condition[left_condition]
        right = by_condition[right_condition]
        if allowed_difference_columns is not None:
            assert_allowed_pair_differences(
                left,
                right,
                key_columns=key_columns,
                key=key,
                condition_column=condition_column,
                allowed_difference_columns=allowed_difference_columns,
                enforce_condition_equality=enforce_condition_equality,
            )
        pairs.append((key, left, right))
    if len(pairs) != expected_total_pairs:
        fail(f"total pairs expected {expected_total_pairs}, got {len(pairs)}")
    return pairs


def assert_allowed_pair_differences(
    left: pd.Series,
    right: pd.Series,
    *,
    key_columns: list[str],
    key: Any,
    condition_column: str,
    allowed_difference_columns: set[str],
    enforce_condition_equality: bool = False,
) -> None:
    allowed = set(allowed_difference_columns)
    if not enforce_condition_equality:
        allowed.add(condition_column)
    columns = sorted(set(left.index) | set(right.index))
    pair_label = format_pair_key(key_columns, key)
    for column in columns:
        if column in allowed:
            continue
        left_value = normalize_pair_value(left.get(column))
        right_value = normalize_pair_value(right.get(column))
        if left_value != right_value:
            fail(
                "unexpected condition mismatch within pair "
                f"{pair_label}: column {column!r} has "
                f"{left_value!r} vs {right_value!r}"
            )

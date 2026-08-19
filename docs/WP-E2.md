# WP-E2 - Frozen Phase A Artifact Protection

## Inventory

Frozen criteria used: `CLAUDE.md` marks `paper1_phaseA_v1` as frozen, and
`docs/paper1_study_protocol.md` states that Phase A is a frozen historical
protocol and that Phase A results are final. Therefore writes to Phase A freeze
memo and H1-H4 diagnostics are frozen writes.

| Script | Target | Frozen |
|---|---|---|
| `analysis/scripts/aggregate/aggregate_run_registry.py` | `analysis/data/<experiment_id>/aggregate_by_variant_system.csv` from config `output_dir` | no |
| `analysis/scripts/aggregate/classify_odebench_systems.py` | CLI `--output` CSV and CLI `--report` Markdown | no |
| `analysis/scripts/aggregate/convert_campaign_history_to_run_registry.py` | CLI `--output` run registry CSV | no |
| `analysis/scripts/aggregate/evaluate_hypotheses.py` | config `diagnostics_path`, for Phase A `analysis/data/paper1_phaseA_v1/h1_h4_diagnostics.json` | yes |
| `analysis/scripts/aggregate/evaluate_hypotheses.py` | config `freeze_memo_path`, for Phase A `docs/paper1_freeze_memo_phaseA.md` | yes |
| `analysis/scripts/aggregate/phase1_diagnostic.py` | CLI `--output` Markdown | no |
| `analysis/scripts/plot/plot_exact_match_rates.py` | `analysis/figures/<experiment_id>/exact_match_rates.pdf` and `.png` | no |
| `analysis/scripts/plot/plot_stage_overshoot.py` | `analysis/figures/<experiment_id>/stage_overshoot_by_variant.pdf` and `.png` | no |
| `analysis/scripts/plot/table_main_results.py` | `analysis/tables/<experiment_id>/main_results.tex` and `.csv` | no |

## Implementation

`analysis/scripts/aggregate/evaluate_hypotheses.py` now detects frozen experiment
IDs. `paper1_phaseA_v1` is the frozen ID. If its configured memo and diagnostics
targets already exist, the default run writes recomputed outputs to:

`outputs/analysis/evaluate_hypotheses_reproduction/paper1_phaseA_v1/`

It then compares those recomputed outputs against the frozen artifacts and prints
the result. The frozen targets are not opened for writing in this mode.

Explicit rebuild from scratch remains possible with:

```text
python analysis/scripts/aggregate/evaluate_hypotheses.py --config analysis/configs/paper1_phaseA_v1.json --force-frozen-overwrite
```

## Comparison Exclusions

Excluded fields:

| Artifact | Excluded field | Reason |
|---|---|---|
| `analysis/data/paper1_phaseA_v1/h1_h4_diagnostics.json` | top-level `generated_at` | Run timestamp, changes on every recomputation, not scientific content |
| `docs/paper1_freeze_memo_phaseA.md` | line beginning `Generated: ` | Run timestamp, changes on every recomputation, not scientific content |

No hypothesis verdicts, metrics, warnings, auxiliary results, table rows, or memo
text are excluded.

## Phase A Verification

Command:

```text
python analysis/scripts/aggregate/evaluate_hypotheses.py --config analysis/configs/paper1_phaseA_v1.json
```

Observed output included:

```text
Frozen artifact mode: protected
Excluded comparison fields: diagnostics.generated_at; memo Generated line
Frozen artifacts unchanged: yes
Reproduction matches frozen diagnostics excluding generated_at: yes
Reproduction matches frozen memo excluding Generated line: yes
```

Checksums before and after the run:

| Artifact | Before SHA256 | After SHA256 |
|---|---|---|
| `docs/paper1_freeze_memo_phaseA.md` | `2B8638B710B0AEB2A0B18FB3C2BB24642D870F9BF3BCF62CE842FC6BAAA2B2DA` | `2B8638B710B0AEB2A0B18FB3C2BB24642D870F9BF3BCF62CE842FC6BAAA2B2DA` |
| `analysis/data/paper1_phaseA_v1/h1_h4_diagnostics.json` | `0CDDFBAF1AF904CD592D6941B4A687CBDD44FB19BBE84F3AC799CD2715CB44AE` | `0CDDFBAF1AF904CD592D6941B4A687CBDD44FB19BBE84F3AC799CD2715CB44AE` |

## Tests

Commands run:

```text
pytest tests/test_evaluate_hypotheses_dataset_classification.py -q --basetemp=.pytest_tmp_wp_e2
pytest tests -q --basetemp=.pytest_tmp_wp_e2_all
```

Results:

```text
3 passed in 1.77s
4 passed in 2.88s
```

New test:

`tests/test_evaluate_hypotheses_dataset_classification.py::test_phase_a_evaluation_does_not_overwrite_frozen_artifacts`

Why it fails against the old implementation: the old script wrote directly to
the configured `diagnostics_path` and `freeze_memo_path` on every Phase A run.
The new test records both SHA256 checksums before the subprocess run and asserts
that both checksums are unchanged afterward; it also asserts the protected-mode
reproduction match messages in stdout. The old implementation neither preserved
the timestamp-bearing artifacts nor emitted those protected-mode messages.

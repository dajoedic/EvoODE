# WP-A3 - Hypothesis Evaluation Scope Guard

## Scope Review

`docs/paper1_study_protocol.md` defines H1-H4 for the historical Phase A experiment
`paper1_phaseA_v1`: 10 systems x 6 variants x 5 seeds. The campaign bridge data in
`analysis/data/wp_a1_campaign_bridge_probe/aggregate_by_variant_system.csv` has 15
aggregate rows, 5 systems, and 4 variants. It compares stage-capped campaign variants
and does not contain the Phase A baseline set.

| Hypothesis | Transferable to campaign? | Reason |
|---|---|---|
| H1 | no | H1 requires `evogrow_v1`, `evogrow_v2_1`, and `evogrow_v2_2_stage_local`; the campaign bridge lacks the first two Phase A baselines and instead includes stage-capped variants. |
| H2 | no | H2 requires all exact systems and the `gp_baseline` recovery comparison; the campaign bridge lacks `gp_baseline` and several Phase A exact systems. |
| H3 | no | H3 compares wasted levels for `evogrow_v1`, `evogrow_v2_1`, and `evogrow_v2_2_stage_local`; the campaign bridge lacks the Phase A v1 and v2.1 baselines. |
| H4 | no | H4 compares v2.2 hard, soft, and passive usage policies on high-stage systems; the campaign bridge lacks `evogrow_v2_2_soft` and `evogrow_v2_2_passive`. |

No new hypotheses or metric definitions were introduced.

## Implementation

Changed `analysis/scripts/aggregate/evaluate_hypotheses.py` only.

The script now classifies an aggregate before Phase A validation:

- `phase_a` if all six Phase A variants are present.
- `campaign` if campaign-specific evidence is present: `campaign` or `condition`
  columns, stage-capped or pretuning variant markers, or `campaign` in the experiment
  id / aggregate path.
- `unknown` otherwise; this falls through to the existing hard Phase A validation.

For Phase A data, the existing validation and H1-H4 evaluation path is unchanged.
For campaign data, the script prints a scope explanation and exits successfully without
writing Phase A diagnostics or memo outputs.

## Evidence

Phase A command:

```text
python analysis/scripts/aggregate/evaluate_hypotheses.py --config analysis/configs/paper1_phaseA_v1.json
```

Phase A printed verdicts before and after:

```text
H1: PARTIAL (1/6)
H2: SUPPORTED (7/8)
H3: PARTIAL (2/6)
H4: VACUOUS
Generalization: OMIT
```

Normalized value checksums, with generated timestamps replaced by `<generated_at>`:

| Artifact | Before | After |
|---|---|---|
| `analysis/data/paper1_phaseA_v1/h1_h4_diagnostics.json` | `c7c9fc90bb09b7cd4534655a84ce7bdde2fdff7b88ccbeeaf044122fac01af83` | `c7c9fc90bb09b7cd4534655a84ce7bdde2fdff7b88ccbeeaf044122fac01af83` |
| `docs/paper1_freeze_memo_phaseA.md` | `b51a4c69c27c49c9d62ef5bfec8d711dbcbd7f3b8a77f8874c1121b41c9e50a6` | `b51a4c69c27c49c9d62ef5bfec8d711dbcbd7f3b8a77f8874c1121b41c9e50a6` |

Byte checksums changed because both files contain generated timestamps:

| Artifact | Before byte SHA-256 | After byte SHA-256 |
|---|---|---|
| `analysis/data/paper1_phaseA_v1/h1_h4_diagnostics.json` | `485db8d40e7f2ccd4fb1448644c09649140d126c58703c51731092d5ecb64d27` | `471f9d179394ce88e69843f3c2812582f0cac114b5923e95d3718f45874bdc12` |
| `docs/paper1_freeze_memo_phaseA.md` | `e130d486790a90a9374187ca646d9bca69b69acefef0202aefd80e57bd9e6183` | `a9063fc04ff821954196015064ecfd82373b37c604ca374cfb150be735e694d2` |

Campaign bridge command:

```text
python analysis/scripts/aggregate/evaluate_hypotheses.py --config analysis/configs/wp_a2_campaign_bridge_probe.json
```

Campaign bridge result:

```text
Dataset classification: campaign
Experiment: wp_a2_campaign_bridge_probe
Aggregate: C:\Users\joedicke\Documents\reps\EvoODE\analysis\data\wp_a1_campaign_bridge_probe\aggregate_by_variant_system.csv
Reason: campaign variant markers present: evogrow_v2_2_stage_capped, evogrow_v3_stage_capped; experiment id or aggregate path contains 'campaign'
Found variants: evogrow_v2_2_stage_capped, evogrow_v2_2_stage_local, evogrow_v3, evogrow_v3_stage_capped
Found systems: 3, 11, 26, 31, 63
Action: H1-H4 are Phase A hypotheses from docs/paper1_study_protocol.md.
They compare evogrow_v1, evogrow_v2_1, v2.2 usage modes, and gp_baseline.
This dataset does not define that comparison, so no Phase A hypothesis evaluation was written.
Missing Phase A variants are expected for campaign data: evogrow_v1, evogrow_v2_1, evogrow_v2_2_passive, evogrow_v2_2_soft, gp_baseline
```

The campaign output does not contain the old `Missing expected variants` failure text.

## Tests

Command:

```text
pytest tests/test_evaluate_hypotheses_dataset_classification.py tests/test_analysis_variant_visibility.py -q --basetemp=.pytest_tmp_wp_a3
```

Result:

```text
3 passed in 0.95s
```

The new test file covers:

- Phase A data is classified as `phase_a` and still passes the existing validation.
- Campaign bridge data is classified as `campaign` and reports non-applicable Phase A
  hypotheses without the old `Missing expected variants` text.

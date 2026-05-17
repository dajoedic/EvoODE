# Paper 1 — Fahrplan (Stand 2026-05-17)

Autoritative Quelle für Phasen, Ziele und Entscheidungen: `PAPER_1.md`.
Dieses Dokument ist die schnell lesbare Übersicht für die tägliche Arbeit.

---

## Block 1 — Phase 0 abschließen (sofort)

| WP | Was | Sprache | Wer | Output | Status |
|----|-----|---------|-----|--------|--------|
| WP-0.1 | H4-Claim in `evaluate_hypotheses.py` korrigieren, Freeze Memo + Diagnostics JSON neu generieren | Python | Codex | Korrigiertes `paper1_freeze_memo_phaseA.md` + `h1_h4_diagnostics.json` | **offen** |
| WP-0.2 | Generalisierungspfad in Config korrigieren | Python/Config | Claude | `paper1_phaseA_v1.json` mit korrektem Pfad | **erledigt** ✓ |

**Freigabe für Block 2:** WP-0.1 done.

---

## Block 2 — Phase 1: Metric Repair + v2.2 Diagnose

| WP | Was | Sprache | Wer | Output |
|----|-----|---------|-----|--------|
| WP-1.1 | Coefficient-threshold Pruning für `exact_support_match` implementieren — nur für Evaluation, nicht im Search | Julia | Codex | `exact_support_match_raw` + `exact_support_match_pruned` in metrics |
| WP-1.2 | Phase-A-Daten mit geprunter Metrik neu auswerten — war System 11 ein Metrik-Fehler? | Python | Codex | Diagnostic-Report (md oder JSON) |
| WP-1.3 | v2.2 Diagnose-Run auf Problem-Systemen 26, 31, 63 + Kontrollsystem | Julia | Codex | Kleine Run-Serie, Stage-Histories, Loss-Kurven |
| WP-1.4 | Diagnose-Bericht: Was schlägt fehl und warum? (Metrik-Artefakt / Fitting / Basis / System-weites Staging?) | — | Claude + du | Schriftliche Gate-1-Entscheidung in `PAPER_1.md` |

### Gate 1 — Entscheidung nach Phase 1

| Ergebnis | Konsequenz |
|----------|-----------|
| v2.2 ist nach Metrik-Repair paper-ready | → direkt zu Block 4 (Phase 3) |
| v2.2 versagt wegen system-weitem Staging | → Block 3 (Phase 2, v3) |
| v2.2 versagt aus anderem Grund | → Paper-Plan neu bewerten |

---

## Block 3 — Phase 2: EvoGrow v3 (nur wenn Gate 1 es triggert)

| WP | Was | Sprache | Wer | Output |
|----|-----|---------|-----|--------|
| WP-v3.1 | Design-Note: per-equation Progress-Signal und Promotion-Regel | — | Claude | Schriftliches Design-Doc, vor jeder Implementierung |
| WP-v3.2 | `EvoGrowV3` Struct mit `eq_stages::Vector{Int}` | Julia | Codex | Neues Struct, kein alter Code angefasst |
| WP-v3.3 | Equation-aware Child Generation | Julia | Codex | Erweiterte Child-Sampling-Logik |
| WP-v3.4 | Per-equation Plateau Detection + Promotion | Julia | Codex | Stage-Promotion funktioniert pro Gleichung |
| WP-v3.5 | Neue v3-Metriken in `result.json` (`eq_final_stages` etc.) | Julia | Codex | Erweiterte Metrik-Ausgabe |
| WP-v3.6 | Validation-Run: v3 vs. v2.2 auf 3–5 Diagnosesystemen | Julia | Codex | Run-Ergebnisse + Vergleich |

### Gate 2 — Entscheidung nach Phase 2

| Ergebnis | Konsequenz |
|----------|-----------|
| v3 zeigt bessere Komplexitätsallokation | → v3 als finaler Variant |
| v3 nicht besser oder instabil | → v2.2 mit ehrlicher Limitierungsanalyse |

---

## Block 4 — Phase 3: ODEBench-Protokoll + Systemklassifikation

| WP | Was | Sprache | Wer | Output |
|----|-----|---------|-----|--------|
| WP-3.1 | Alle 63 Systeme klassifizieren: exact vs. surrogate, expected_stage | Python | Codex | `system_classification.csv` |
| WP-3.2 | R²-Metrik implementieren + Test auf Phase-A-Daten | Python | Codex | `analysis/utils/r2.py` |
| WP-3.3 | Run-Schema validieren: `use_pretuning=false` fix, Timeout-Handling, alle Pflichtfelder | Julia | Codex | Schema-Check-Skript, ggf. Runner-Erweiterung |
| WP-3.4 | ODEBench-Protokoll-Alignment-Audit: EvoGrow vs. publizierte Methoden | Python/Docs | Codex + Claude | `docs/paper1_odebench_protocol_alignment.md` |

**Freigabe für Block 5:** Alle WPs aus Block 4 done, finaler Variant aus Gate 1/2 bekannt.

---

## Block 5 — Phase 4: Kleiner Validierungsrun (lokal)

| Schritt | Was | Systeme | Seeds | Wer |
|---------|-----|---------|-------|-----|
| Manifest erstellen | `generate_manifest.jl` für 5 Systeme | 1D, 2D, 3D, 4D, Surrogate | 3 | Codex |
| Run ausführen | `run_experiment.jl` lokal | — | — | du |
| Schema-Validierung | Alle Output-Dateien checken, R² berechnen, Timeouts testen | — | — | Codex |
| Runtime-Schätzung | Basis für Cluster-Planung | — | — | Claude + du |

---

## Block 6 — Phase 5: Vollständiger Cluster-Run

| Schritt | Was | Umfang | Wer |
|---------|-----|--------|-----|
| Manifest | 63 Systeme × 1 Variant × 3 Seeds = 189 Runs | `paper1_phaseB_v1` | Codex |
| Cluster-Runner-Test | ≥10 parallele Runs, Race-Condition-Check | lokal | Codex + du |
| Cluster-Ausführung | Vollständiger Run | 189 Runs | du (Infrastruktur) |
| Aggregation | `aggregate.jl` → `run_registry.csv` | — | Codex |

---

## Block 7 — Phase 6: Analyse + Paper

| Schritt | Was | Wer |
|---------|-----|-----|
| Primäranalyse | R², Accuracy, Loss über alle 63 Systeme | Codex (Python-Pipeline) |
| Strukturanalyse | `exact_support_match_pruned`, Stage-Metriken, Wasted Levels (exact systems) | Codex |
| Surrogate-Analyse | R², Basis-Mismatch, Stage-Verhalten | Codex |
| Failure-Mode-Analyse | Timeout-Rate, Solver-Failures, Instabilität | Codex + Claude |
| Figures + Tables | Plot-Skripte, LaTeX-Tabellen | Codex |
| Paper Draft | Sections 1–8 nach Struktur in `PAPER_1.md` | du + Claude |
| Referenz-Alignment | Publizierte ODEBench-Zahlen einordnen | Claude + du |

---

## Abhängigkeitskette

```
WP-0.1
  └─► Phase 1 (WP-1.1 bis WP-1.4)
        └─► Gate 1
              ├─► [v2.2 ok] ──────────────────────────────► Phase 3
              └─► [v3 nötig] ── Phase 2 (WP-v3.1–v3.6) ──► Gate 2
                                                                └─► Phase 3
                                                                      └─► Phase 4 (Validation)
                                                                            └─► Phase 5 (Cluster)
                                                                                  └─► Phase 6 (Paper)
```

**Kritischer Pfad:** WP-0.1 → Phase 1 → Gate 1. Alles andere hängt daran.

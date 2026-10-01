# WP-N35 — Beste Struktur je Level im Heartbeat (Track S, S-02), verhaltensneutral
**Language: Julia** (plus Python-Test)

Backlog: `CLAUDE.md`, „Backlog Paper 1“, Track S, S-02. Vom Nutzer freigegeben am 2026-10-01.
Anlass: die Rückschau auf das Abbruchkriterium (`DIARY.md` 2026-10-01). Die Heartbeats tragen je
Level nur `best_loss` und `stage`, nicht die Struktur. Ohne Struktur je Level lässt sich nicht prüfen,
welche Struktur eine Abbruchregel zurückgegeben hätte.

## Ausgangslage

Der Level-Snapshot, den `src/structure/evogrow.jl` (ab Zeile ~979) an `level_callback` übergibt,
enthält schon `best_structure`, `best_params`, `best_loss`, `best_objective`,
`accepted_new_best`, `stage_transition`, `previous_stage` und `new_stage`. Der Heartbeat in
`studies/regression/run_regression.jl` (`level_callback`, ab Zeile ~827) schreibt davon nur
`level`, `stage` und `best_loss`.

## Umsetzung

Der Level-Heartbeat bekommt zusätzlich:
- `best_terms`: aktive Termnamen je Gleichung. Verwende dieselbe Funktion wie `support_terms` im
  Record (`active_term_names` o. ä.), keine zweite.
- `best_params`: die Koeffizienten der besten Struktur, im selben Format wie `model_terms` im Record
  (Term, Termindex, Koeffizient).
- `best_objective`, `accepted_new_best`, `stage_transition`, `previous_stage`, `new_stage`.

**Nur in `studies/regression/run_regression.jl`.** `src/` wird nicht angefasst. Die Suche, der
Record, die Fingerprints und die Zufallsströme bleiben unverändert. Gelesen wird ausschließlich
aus dem Snapshot, der ohnehin existiert.

## Verboten

`src/` ändern; Record-Felder, Fingerprints oder Manifeste ändern; Läufe über 15 Minuten; Git;
`codex/CURRENT_TASK.md` bearbeiten; `docs/` ändern.

## Abnahme

1. Ein Python-Test prüft die neuen Heartbeat-Felder an einer Fixture, die aus einer echten
   Heartbeat-Datei abgeleitet ist (`outputs/stage1/s0.05_r0.5/tasks/cell_000001.heartbeat.jsonl`
   als Grundlage, um die neuen Felder erweitert).
2. Für Claude im Report, mit erwarteter Dauer:
   - (a) die Stufe-0-Kontrolle neu fahren (System 1, Seed 42, IC 1 und 2, (0, 0, 10)) und mit
     `compare_phasec_controls.py` gegen C-1 vergleichen. **Bitgleich**, sonst ist das Paket nicht
     verhaltensneutral;
   - (b) eine Stufe-1-Zelle neu fahren, (0,05; 0,5) auf System 1, und zeigen, dass der Record
     bitgleich zu `outputs/stage1/s0.05_r0.5/tasks/cell_000001.jsonl` ist und der Heartbeat die neuen
     Felder trägt.
3. Report `codex/reports/REPORT_WP_N35.md`, `STATUS.md` nach Protokoll. Weil Julia nicht ausführbar
   ist, ist `blocked` mit dem Vermerk *Umgebung, nicht Sache* der erwartete Abschluss.

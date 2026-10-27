# WP-N48b — PySR auf Orion mit einem Seed-Label je Zelle
**Language: Python**

Stand 2026-10-21. Nachtrag zu WP-N48 (`837d751`, Report `codex/reports/REPORT_WP_N48.md`).

## Entscheidung des Nutzers (2026-10-21)

Der volle PySR-Lauf auf dem C-6-Export rechnet **nur das Seed-Label 1** je Zelle, nicht 1, 2, 3. Begründung: PySR läuft
ohne `random_state` (WP-N39 §A.4), die Labels sind also reine Wiederholungen. Wiederholungen pro Bedingung gibt es
schon über die drei Rauschrealisierungen, und EvoGrow rechnet in C-6 ebenfalls einen Lauf je Zelle. Erwarteter
Umfang: 4.536 Zellen × 2 Varianten × 1 Label = **9.072 Records**.

**ODEFormer bleibt unverändert** (4 Konfigurationen × 3 Wiederholungen, 54.432 Records, Manifest und Shards wie in
WP-N48).

## Umfang

1. Die Seed-Labels für PySR im Plattformmodus ausdrücklich festlegen: im Shard-Einstieg
   (`analysis/scripts/aggregate/run_k8s_symbolic_shard.py`) und im Zusammenführen
   (`aggregate_c6_symbolic_baselines.py`), z. B. über ein Argument oder eine Umgebungsvariable, die das Manifest setzt.
   Die Label-Menge gehört in den Kontext, den der Einstieg prüft (WP-N48 „context binds … settings“). Ein Ergebnisordner
   mit anderer Label-Menge wird abgelehnt.
   Das lokale Standardverhalten von `run_pysr_noise.py` (Labels 1, 2, 3) bleibt unverändert. Die PySR-Konfigurationsdatei
   wird **nicht** geändert.
2. `k8s/phase_c_c6_pysr_job.yaml`: Label 1 setzen, Kostenkommentar aktualisieren (1 Label: ≥ 1.233 Kern-h, ≥ 1.850 €,
   ≥ ~6,4 Tage bei 8 Pods, Untergrenze). Shard-Zahl nach der WP-N48-Regel neu wählen: ein Shard soll nach der
   Planungsschätzung ≤ ~3 h brauchen. Mit einem Label passen voraussichtlich mehrere Zellen in einen Shard, weil so
   weniger Pods starten müssen. Die Reihenfolge dim 1/2 vor dim 3/4 bleibt. Das Smoke-Manifest hat schon nur Label 1;
   prüfe, ob es konsistent ist.
3. Erwartete Anzahl beim Zusammenführen: 9.072. Die Pass-Kriterien und Befehle im Report anpassen.
4. Tests: Die Label-Menge wirkt auf Zuordnung, Wiederaufnahme-Kontext und erwartete Schlüssel. Ein Ordner mit anderer
   Label-Menge wird abgelehnt. Das lokale Standardverhalten bleibt bei 1, 2, 3.
5. Den Report `codex/reports/REPORT_WP_N48.md` um einen Abschnitt „WP-N48b“ ergänzen: was sich geändert hat, neue
   Shard-Zahl, neue Kosten, geänderte Befehle (Schritte 7 und 8).

## Verboten

Wie WP-N48: keine Läufe außer Unit-Tests, keine Cluster- oder Git-Befehle, nicht committen. Keine Änderung an Methode,
Varianten, Hyperparameter-Grid, Iterationen, Versionen oder ODEFormer-Teilen. Kein `random_state`. Keine Timeouts.
Keine EvoGrow-C-6-Ergebnisse lesen.

## Abnahme

Neue und bestehende Tests grün (bekannt: nur der Phase-A-Fehler). Die Manifeste parsen, `parallelism ≤ 8`, kein
`activeDeadlineSeconds`. `codex/STATUS.md` mit `status: done | blocked`, `task: WP-N48b`, Report-Pfad.

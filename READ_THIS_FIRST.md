# READ_THIS_FIRST.md — Sitzungsübergabe

**Was dieses Dokument ist:** der flüchtige Zustand *zwischen* zwei Chat-Sitzungen — was gerade läuft,
was uncommittet im Working Tree liegt, welche Entscheidung als Nächstes ansteht. Nichts weiter.

**Was es ausdrücklich nicht ist:** ein Planungs- oder Statusdokument. `CLAUDE.md` verbietet ein
zweites davon. Alles Dauerhafte gehört dorthin, nach `PAPER_1.md` oder ins `DIARY.md` —
**nicht hierher.**

**Regeln:** wird immer **vollständig überschrieben**, nie angehängt. Was älter als ein paar Tage
ist, ist vermutlich falsch — dann gilt `CLAUDE.md`.

**Stand: 2026-09-26, 01:20.** Nachtschicht von Claude läuft. Dieses Dokument wird bei jedem Schritt
neu geschrieben; die Uhrzeit oben sagt, wie aktuell es ist.

---

## 0. Freigabe für die Nacht 25./26.09. (einmalig, vom Nutzer: "A")

Claude darf **heute Nacht** selbst: WP-N27c committen und nach `origin` + `gitlab` **pushen**, auf
den Image-Bau warten, den ODEFormer-Smoke per `oc apply` starten und prüfen, und **nur wenn der
Smoke sauber ist** (inklusive einer `_opt`-Zelle mit `odeformer_optimization_status = success`) den
Grid-Job `k8s/odeformer_reference_grid_job.yaml` starten. Sonst gilt weiter: Push und `oc apply`
macht der Nutzer. Die Freigabe erlischt morgen früh.

## 1. Was läuft

| Lauf | Wo | Stand | Anmerkung |
|---|---|---|---|
| C-1/C-2 | Orion, `221a3a7` | 731 / 756 (25.09. abends) | nur noch Nachzügler |
| C-3 | Orion, `221a3a7` | 172 / 180 | 8 × dim 3 (Lorenz, System 59), ~20–25 h pro Level |
| WP-T1d | Orion, `5a87efb` | 34 / 36 | |
| ODEFormer-Referenzraster | Orion, noch nicht gestartet | WP-N27c gepusht (`55e9c75`), CI baut; Smoke 3 startet automatisch ~01:55 | 126 Pods, 3 Wdh. × 42 Shards |
| Codex WP-N28 | Laptop | läuft seit 01:15 | |

## 2. ODEFormer-Referenzraster — der Weg bis zum Start

- **Entscheidung 25.09.:** kanonisch `faithful` (1 s), drei Wiederholungen, Rate mit Streuung
  (`docs/paper1_phaseC_benchmark_plan.md`). Messung: jede nicht wiederholbare Zelle hat einen
  Timeout; 10 s beseitigt es nicht (DIARY 25.09.).
- **Smoke 1 (Image `9ff548e`):** hing mit 0 CPU. Ursache: `join()` vor `get()` in
  `run_cell_with_hard_timeout` → Pipe-Deadlock. Behoben mit **WP-N27b** (`3ca31bb`).
- **Smoke 2 (Image `3ca31bb`):** lief in 53 s durch, aber `beam10_opt` endete mit
  `ModuleNotFoundError: param_optimizer`. Die Konstantenoptimierung kam lokal aus
  `outputs/third_party/odeformer` (gitignored) und fehlt im CI-Image. Der Record sah gültig aus.
  → **WP-N27c** (`55e9c75`, gepusht): Quellbaum ins Image, ein fehlendes Modul führt zum harten
  Abbruch, Hash-Prüfung über LF-normalisierten Inhalt (mein erster Sollwert war ein CRLF-Hash aus
  der Windows-Kopie). Lokal gebautes Image **ohne** eingebundene Ordner: `_opt` = `success`,
  bitgleich zum lokalen Lauf. Tests im Linux-Container 38 grün, dazu die 2 bekannten Altlasten.
  Trajektorien unter `odeformer_grid_55e9c75…/trajectory_export`, per Hash geprüft.
- Trajektorien liegen auf dem NFS unter `odeformer_grid_<SHA>/trajectory_export`, jeweils per Hash
  geprüft. Für den neuen SHA müssen sie neu hingelegt werden.
- Befehle (mit `<SHA>` des gebauten Commits):
  `oc delete job evoode-odeformer-reference-grid-smoke`, dann
  `(Get-Content k8s\odeformer_reference_grid_smoke_job.yaml) -replace '<COMMIT_SHA>','<SHA>' | oc apply -f -`,
  dasselbe mit `odeformer_reference_grid_job.yaml` für den Grid.

## 3. Warteschlange Codex (eine nach der anderen)

1. ~~WP-N27c~~ erledigt.
2. **WP-N28 (läuft), Auswertungskette Phase C schließen.** Befunde der Generalprobe vom 25.09.:
   Strukturmetriken nicht in die Registry eingemischt; Cap-Ablation braucht einen C-1/C-2-Filter und
   kommt mit exakt-only-Metriken bei Surrogaten nicht klar; SINDy-Paarung verlangt C-3 für alle
   Systeme; Pretuning-Collapse hat die Phase-B-Variantennamen fest verdrahtet. **Entschieden:
   `structural_f1` = micro als Hauptzahl, macro daneben.**
3. **WP-N25c:** `--estimate-cost` der C-5-Skripte nimmt `total_parameter_optimization_time_s`,
   das die ODE-Integrationen **nicht** enthält; richtig ist `elapsed_s / total_loss_evals`.
   Korrigierte Schranke: Oracle ~92 h, Restart-Kurve ~305 h → Orion.

## 4. Heute erledigt (25.09.), alles committet

WP-N24-Auswertung (DIARY), Entscheidung für den ODEFormer-Modus, WP-N25/N25b (C-5 auf Phase C),
WP-N26 (Phase-C-Wahrheit, Koeffizientenfehler, Heartbeat-Schutz), WP-N27/N27b (Orion-Grid,
Deadlock), CHANGELOG E7 (wandb-Befund), Plan-Korrekturen (Determinismus-Satz, C-5-Kosten).

## 5. Git

Uncommittet: nur die beiden `_wp_n23`-Datenordner (absichtlich) und was Codex gerade schreibt.
Gepusht bis `55e9c75`.

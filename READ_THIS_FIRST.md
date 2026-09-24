# READ_THIS_FIRST.md — Sitzungsübergabe

**Was dieses Dokument ist:** der flüchtige Zustand *zwischen* zwei Chat-Sitzungen — was gerade läuft,
was uncommittet im Working Tree liegt, welche Entscheidung als Nächstes ansteht. Nichts weiter.

**Was es ausdrücklich nicht ist:** ein Planungs- oder Statusdokument. `CLAUDE.md` verbietet ein
zweites davon. Alles Dauerhafte gehört dorthin, nach `PAPER_1.md` oder ins `DIARY.md` —
**nicht hierher.**

**Regeln:** wird immer **vollständig überschrieben**, nie angehängt. Was älter als ein paar Tage
ist, ist vermutlich falsch — dann gilt `CLAUDE.md`.

**Stand: 2026-09-24, 17:05.** Nutzer für heute fertig. Auf dem Laptop läuft der
ODEFormer-Wiederholbarkeitslauf (WP-N24), auf Orion die drei bekannten Jobs.

---

## 1. Was gerade läuft

| Lauf | Wo | Stand 24.09. 17:05 | Anmerkung |
|---|---|---|---|
| C-1/C-2 | Orion, `221a3a7` | 349 / 756, 64 aktiv, 0 Fehler | letzte dim-3-Zellen, dann dim 4 und dim 1 |
| C-3 | Orion, `221a3a7` | 172 / 180, 8 aktiv, 0 Fehler | letzte 8 sind dim 3 inkl. Lorenz |
| WP-T1d | Orion, `5a87efb` | 24 / 36, 8 aktiv | `parallelism` 8, keine Deadline |
| **ODEFormer-Wiederholbarkeit (WP-N24)** | Laptop, PowerShell-Schleife des Nutzers, Docker | gestartet 16:50, Lauf 1 von 6 (`reference_faithful_4`), 40 Records um 17:04 | 6 Läufe strikt nacheinander: je Umgebung `faithful_4`, `faithful_1`, `lifted_4`; jeder durch `--max-hours 7` begrenzt. Ausgabe `outputs/odeformer_repeatability/<env>_<mode>_<shards>/` |

```powershell
oc get jobs -o custom-columns="NAME:.metadata.name,PAR:.spec.parallelism,SUCC:.status.succeeded,ACTIVE:.status.active,FAILED:.status.failed"
docker ps --format "{{.Image}} {{.Status}}"
```

Records Phase C: `S:/BigDataOrion/data-science/joedicke/phase_c_campaign_221a3a7…/tasks/`; WP-T1d:
`wp_t1e_campaign_5a87efb…/cell_*/neighbour_rows.csv`. Statusseite (Version 10):
https://claude.ai/artifact/4sq6HhRsnxgrFVqVF2trBx — führt **alle** Läufe, bei Statuswechsel neu
veröffentlichen. Lokale Arbeitskopie: das Scratchpad der Sitzung vom 24.09. (`orion_status.html`),
sonst per `Artifact read` holen.

## 2. Der ODEFormer-Befund von heute (DIARY 2026-09-24)

- Die WP-N23-Neuberechnung (`reference_wp_n23/`, `candidate_wp_n23/`) ist **nicht bitgleich** mit
  dem ersten Raster: 18 + 12 Zellen weichen ab, 10 davon schon beim Rohmodell. Die R²>0.9-Raten
  bewegen sich kaum (364 → 363 bzw. 326 → 324). **Die `_wp_n23`-Ordner sind absichtlich untracked**
  und ersetzen die alten noch nicht.
- Ursache: ODEFormers `_integrate_ode` hat einen **1-s-Wall-Clock-Timeout** (`SIGALRM`). Er wirkt in
  der Kandidatenauswahl, in unserer Auswertung und in der Konstantenoptimierung, und das nackte
  `except` im `solve_ivp`-Zweig verschluckt ihn. WP-N24/b/c (`3e98e31`) zählt die Timeouts jetzt im
  Handler und macht die Grenze steuerbar.
- Rauchtest, Kandidat System 11: bei 1 s 6–7 Timeouts und R² 0,517; bei 10 s 0 Timeouts, R² 0,983,
  bitgleich. Referenz System 2: 0 Timeouts, bitgleich.
- Altlast, **nicht** von WP-N24: `test_smoke_writes_sindy_and_odeformer_records` und
  `test_odeformer_grid_resumes_complete_records_from_real_export` scheitern im Linux-Container schon
  auf HEAD vor WP-N24 (unter Windows werden sie übersprungen).

## 3. Wenn der Wiederholbarkeitslauf fertig ist

Die PowerShell des Nutzers steht dann wieder am Prompt. Der `--compare-modes`-Befehl lief **nicht**
mit, den startet Claude:

```bash
MSYS_NO_PATHCONV=1 docker run --rm --entrypoint python -v "$(pwd -W)/baselines:/workspace/EvoODE/baselines" -v "$(pwd -W)/outputs:/workspace/EvoODE/outputs" -v "$(pwd -W)/analysis:/workspace/EvoODE/analysis" evoode/odeformer-candidate:wp-n21 -m baselines.run_odeformer_repeatability --compare-modes --output-dir outputs/odeformer_repeatability
```

Prüfen: (a) jede `collect`-Zeile hat `present` = `expected` und kein `not_run_global_time_limit`;
(b) unter `lifted` sind alle Zellen bitgleich, mit `handler_timeout_count_max = 0`; (c) unter
`faithful` fällt die Streuung mit streuenden Timeout-Zählern zusammen; (d) die Timeouts hängen von
der Shardzahl ab (1 gegen 4). Danach DIARY und Statusseite nachziehen.

**Dann entscheidet der Nutzer**, welche Integrationsgrenze für Claim D kanonisch ist. 1 s entspricht
ODEFormers Protokoll und den publizierten Zahlen, ist aber hardwareabhängig. Eine angehobene Grenze
ist reproduzierbar und begünstigt ODEFormer vermutlich, ist für uns also die konservative Wahl. Erst
danach das ganze Raster im gewählten Modus neu rechnen (Laufzeit-Obergrenze vorher aus den Schranken
herleiten, 8-h-Regel) und entscheiden, was mit den `_wp_n23`-Ordnern passiert.

## 4. Was sonst ansteht — der Reihe nach, keine neuen Themen

1. ODEFormer abschließen (§3).
2. **WP-T1d vollständig** → neuen Maßstab entscheiden (Orakelstart + symmetrischer Mehrfachstart;
   Vorschlag im DIARY vom 23.09.). Wartet auf Zustimmung des Nutzers.
3. **Kampagne fertig** → Phase-C-Auswertung → gepaarter Vergleich EvoGrow / SINDy / ODEFormer
   (Claim D) → prädiktives Kappen-Kriterium → Namespace-Umzug samt Image-Härtung.

Zurückgestellt, bewusst: Rauschen (bis Phase C trägt). Vorgemerkt: WP-T2a (hängt an WP-T1d).

## 5. Git

Alles committet bis auf die beiden `_wp_n23`-Datenordner (absichtlich, siehe §2). **Nichts
gepusht.** Ein Push baut das Kampagnen-Image neu (der Digest-Pin testet sich dabei zum ersten Mal);
die laufenden Jobs hängen an festen SHAs. `codex/CURRENT_TASK.md` enthält noch die erledigte
WP-N24c-Spezifikation; `codex/STATUS.md` steht auf `done`.

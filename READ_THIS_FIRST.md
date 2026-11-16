# READ_THIS_FIRST.md — Sitzungsübergabe

**Was dieses Dokument ist:** der flüchtige Zustand *zwischen* zwei Chat-Sitzungen — was gerade läuft,
was uncommittet im Working Tree liegt, welche Entscheidung als Nächstes ansteht. Nichts weiter.

**Was es ausdrücklich nicht ist:** ein Planungs- oder Statusdokument. `CLAUDE.md` verbietet ein
zweites davon. Alles Dauerhafte gehört dorthin, nach `PAPER_1.md` oder ins `DIARY.md` —
**nicht hierher.**

**Regeln:** wird immer **vollständig überschrieben**, nie angehängt. Was älter als ein paar Tage
ist, ist vermutlich falsch — dann gilt `CLAUDE.md`.

**Stand: 2026-11-16, ~13:30 (Q9 läuft mit 40 Pods, 97,7 % der Plan-Kosten durch; Q8 fertig und offiziell aggregiert `231d59c`) — WISP-Plan bis 31.12.
(CLAUDE.md, „WISP paper — the fixed plan“; Arbeitsreihenfolge vom 12.11. dort).**

## 1. Was läuft

**Orion, geprüft 16.11. ~13:30** (Statusseite https://claude.ai/artifact/9zzJsoGCBahPsuNkaaf3DN, Version 20):

| Lauf | Stand | Wenn fertig |
|---|---|---|
| **W-4 = Q9-Gitter** (`cdfaa7d`, 4.284 Shards, C1000) | 1.176/4.284, 0 Fehler, Parallelität 40; **97,7 % der Plan-Kosten** | 3.068 offene Shards mit nur 148 Plan-Kern-h (Median 5 s) ≈ 1 Tag; Ende bestimmen Nachzügler; 21-Tage-Regel endet 28.11. |
| **W-2 = Q8-Gitter** (`512dd5b`) | 3.540/3.540, Job entfernt, aggregiert 12.11. | — |
| **C-6 gekappt** | 1.435/3.366, Parallelität 0 | nach W-4 zurück auf 24 |

**Q9 je Dimension (16.11. 12:30 UTC):** dim 1 0/1.564 · dim 2 553/1.904 (16 laufend) · dim 3 488/680 (23 laufend) ·
dim 4 135/136 (1 laufend). Fertige Shards brauchten Ist/Plan 0,59 (8.153 statt 13.767 Kern-h); kleine Shards liegen weit
unter Plan (Pod-Minimum ~40–60 s). **Nachzügler über Plan:** sys 62 (dim 4) IC1 σ0 ρ0.5 n1 227 h (Plan 91 h), sys 56 (dim 3)
135 h (Plan 29 h), sys 37 57 h (Plan 10 h), sys 58 55 h (Plan 8 h); sys-55-Nachzügler fertig. Bei jedem Cluster-Check:
`python analysis/scripts/aggregate/q9_progress.py --json` → Tabelle im Chat und Abschnitt auf der Statusseite nachziehen. Lokale Quelle der Statusseite: Scratchpad der Sitzung
`evoode_orion.html` (geht verloren → vorher Artifact `read`).

**Kerne:** 40 Q9 = 40. Änderungen an der Parallelität führt der Nutzer aus (`oc patch`, Auto-Modus blockiert es für Claude).
**NFS-Zugriff:** `MSYS_NO_PATHCONV=1 oc exec <laufender-pod> -- tar czf - -C /outputs/<lauf> out > ….tgz` (komprimiert).
**Rückweg C-6 nach W-4:** `oc patch job evoode-phase-c-c6-grid-capped -n scch-das -p '{"spec":{"parallelism":24}}'` (Git Bash).
Für eine neue Q9-Hochrechnung: Plankosten je Zelle in `q9_paths.json` (`planned_seconds`, Schlüssel `shard_id`).

## 2. WISP-Prozessseite (W-X) — für den Termin am 10.11. fertig

Vorschau https://claude.ai/artifact/Rp4K8dBdWCFzzwQ44Tnfnk **Version 22** (letzter Commit `d041885`). Quelle
`explainer/wisp/process/`, Build `python analysis/scripts/explainer/build_wisp_process.py` → `explainer/wisp/dist/wisp_process.html`,
Kern-Prüfung `node explainer/wisp/process/check_core.cjs`. Stand 10.11.:
- Titelseite: Teaser-Animation rechts (echter Pfad System 3: „?“ → jeder freie Term orange mit fetter Kurve, gewählter
  grün, Entfernen rot durchgestrichen, Stopp, Refit, wahre Kurve). Alternativen im Browser gerechnet (RK4 trifft die
  gespeicherten Kandidatenkurven auf 5·10⁻⁵).
- Szene 01 du/dt als Bruch; 02 festes Layout mit Einblenden; 03 Zoom auf 8 Nachbarpaare + Lauf über die ganze Reihe
  (1,6× Tempo); 09 Backward-Balken ausgerichtet.
- Jede Szene hat feste Grafik- und Schritttexthöhe (alle Schritte einmal vermessen) → nichts springt; für alle 21 Szenen
  im Browser nachgemessen.
- Version 26 des alten Explorables (https://claude.ai/artifact/XsxgvgYGZdqPkpnzVd2YMQ) und `story/` unangetastet bzw. verworfen.
- Offen: weitere Nutzer-Wünsche; nach W-4 Datentausch auf Q9.

## 3. Als Nächstes

1. Q9 beobachten (je Dimension, s. o.): Hochrechnung, sobald die erste dim-3/4-Welle durch ist; >21 Tage → Nutzer entscheidet.
2. ~~Q8-Nachzügler, Q9 auf 40, offizielle Q8-Aggregation~~ erledigt (11./12.11., `231d59c`).
3. Q-B: B1 (SINDy-Familie, WISP-Bibliothek, `a68968c`) braucht Image-Neubau (Nutzer pusht), Orion nach Q9; ODEFormer nach Q9.
   WeakIdent fertig (`65b467f`, τ-Raster `a41f2bd`).
4. Paperentwurf `paper/wisp/` (uncommittet, Q8-Stand) → nach W-4 `make_data.py` auf Q9 umstellen und committen.
4b. **WISP.jl (12.11., vom Nutzer vorgezogen):** Paket steht, privat auf `github.com/dajoedic/WISP.jl`, lokal
   `..\WISP.jl` (`72e84ad`); Abnahme A1–A7 erfüllt (`docs/wisp_package_spec.md`). Claude darf in dieses Repo pushen.
   Offen: Tag `v0.1.0`, Namensprüfung vor Registrierung. Python-Test: venv + `PYTHON_JULIACALL_EXE`/`_PROJECT`
   auf eine Kopie von `validation/` mit PythonCall 0.9.37 (Python 3.12 hat OpenSSL 3.0 → juliapkg erlaubt nur Julia ≤ 1.11).
   Fremde Änderung um 13:39 an `analysis/scripts/aggregate/build_sideproject_q3_weak_starts.py` (sha256-Cache) und
   `aggregate_sideproject_q8.py` — nicht von dieser Sitzung, vermutlich die Q8-Auswertung.
5. Termin-Ergebnisse vom 10.11. (Professor) nachtragen, sobald der Nutzer berichtet.

> **BLINDREGEL C-6** gilt unverändert: keine C-6-EvoGrow-Ergebnisse ansehen, nur technische Prüfung.

**Feste Regeln:** Claude pusht nie nach GitLab, nach GitHub nur mit ausdrücklicher Erlaubnis. Keine harten Zeit-Cuts.
MATLAB nur MATLAB (kein Octave). Orion-Login abgelaufen → `oc login --web https://api.orion.scch.at:6443`.
Codex: `codex exec -s workspace-write -c 'windows.sandbox="unelevated"' "Lies codex/CODEX_PROTOCOL.md und arbeite den
Auftrag in codex/CURRENT_TASK.md ab." < /dev/null` (Hintergrund). Claude darf auch selbst implementieren (03.11.).
**Uncommittet, nicht von Claude:** WP-N48b-Dateien (PySR, pausiert nach §9.4d), `codex/`-Dateien, `explainer/wisp/src/lv/`,
LV-/Intro-Tests und -Berichte, `WISP_Visualisierungsbriefing_Prozess.md` (gehört dem Nutzer), `paper/wisp/`, `output/`.

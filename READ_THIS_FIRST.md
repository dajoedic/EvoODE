# READ_THIS_FIRST.md — Sitzungsübergabe

**Was dieses Dokument ist:** der flüchtige Zustand *zwischen* zwei Chat-Sitzungen — was gerade läuft,
was uncommittet im Working Tree liegt, welche Entscheidung als Nächstes ansteht. Nichts weiter.

**Was es ausdrücklich nicht ist:** ein Planungs- oder Statusdokument. `CLAUDE.md` verbietet ein
zweites davon. Alles Dauerhafte gehört dorthin, nach `PAPER_1.md` oder ins `DIARY.md` —
**nicht hierher.**

**Regeln:** wird immer **vollständig überschrieben**, nie angehängt. Was älter als ein paar Tage
ist, ist vermutlich falsch — dann gilt `CLAUDE.md`.

**Stand: 2026-11-17, ~12:20 (Q9 4.275/4.284, nur noch 9 Nachzügler, 31 Kerne frei; Q8 fertig und offiziell aggregiert `231d59c`) — WISP-Plan bis 31.12.
(CLAUDE.md, „WISP paper — the fixed plan“; Arbeitsreihenfolge vom 12.11. dort).**

## 1. Was läuft

**Orion, geprüft 17.11. ~19:00** (Statusseite https://claude.ai/artifact/9zzJsoGCBahPsuNkaaf3DN, Version 23):

| Lauf | Stand | Wenn fertig |
|---|---|---|
| **W-4 = Q9-Gitter** (`cdfaa7d`, 4.284 Shards, C1000) | 4.276/4.284, 0 Fehler, keine offenen Shards, 8 Pods laufen | Ende bestimmen Nachzügler; dann einsammeln + offizielle Q9-Aggregation |
| **W-2 = Q8-Gitter** (`512dd5b`) | 3.540/3.540, Job entfernt, aggregiert 12.11. | — |
| **Q-B B1** SINDy/Weak-SINDy/E-SINDy (`qb1-sindy:ca849b4`, Job `evoode-sideproject-qb1-sindy`) | 0/240, 8 Pods, gestartet 17.11. 18:52 | ~43 Kern-h (~5–6 h); einsammeln, dann Q-B-Aggregation |
| **Q-B B3** ODEFormer (`odeformer-reference:ca849b4`, Job `evoode-phase-c-c6-odeformer`) | 0/1.512, 23 Pods, gestartet 17.11. ~19:00; Smoke 2/2 PASS (sauber, verrauscht, Vollständigkeit) | 326–349 Kern-h (~15 h); NFS-Dateien wie `plan.json` sind 0600 root → per `oc exec … tar` über einen Pod holen, nicht über S: |
| **C-6 gekappt** | 1.435/3.366, Parallelität 0 | bekommt keine Kerne mehr (Paper 1 erledigt) |

**Kerne 39/40:** 8 Q9 + 8 B1 + 23 B3. **Q9 je Dimension (17.11. 17:59 UTC):** dim 1 1.564/1.564 · dim 2 1.901/1.904 (3 laufend) · dim 3 675/680 (5 laufend) ·
dim 4 136/136. Ist/Plan der fertigen Shards 0,65 (9.154 statt 14.080 Kern-h). **Nachzügler:** sys 58 (dim 3) 78 h (Plan 8 h),
sys 51 46 h (Plan 3 h), sys 59 26 h, vier Shards von sys 52 und einer von sys 28 je 14–15 h (Plan < 1 h); 62 und 56 fertig.
Bei jedem Cluster-Check: `python analysis/scripts/aggregate/q9_progress.py --json` → Tabelle im Chat und Abschnitt auf der Statusseite nachziehen. Lokale Quelle der Statusseite: Scratchpad der Sitzung
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

1. Q9 beobachten: nur noch 9 Nachzügler (17.11.); danach einsammeln und offizielle Q9-Aggregation.
2. ~~Q8-Nachzügler, Q9 auf 40, offizielle Q8-Aggregation~~ erledigt (11./12.11., `231d59c`).
3. **Q-B läuft seit 17.11. abends:** Images geprüft (`qb1-sindy` `sha256:4777784f…`, `odeformer-reference`
   `sha256:42995f4f…`, beide `ca849b4`). B1 8 Pods, B3 23 Pods nach bestandenem Smoke (Ausgabe lokal
   `outputs/qb_b3_smoke_ca849b4…/`). Nach Ende: B1 und B3 einsammeln, B3-Merge mit
   `aggregate_c6_symbolic_baselines --method odeformer --n-shards 1512` (REPORT_WP_N48 Schritt 5), dann Q-B-Aggregation
   (bestes λ / beste Konfiguration je Stratum × σ × Metrik zugunsten der Referenz) ins Paper. B2 WeakIdent fertig
   (`65b467f`, τ-Raster `a41f2bd`). C-6 bekommt keine Kerne.
4. Paperentwurf `paper/wisp/` (uncommittet, Q8-Stand) → nach W-4 `make_data.py` auf Q9 umstellen und committen.
4b. **WISP.jl (12.11., vom Nutzer vorgezogen):** Paket steht, privat auf `github.com/dajoedic/WISP.jl`, lokal
   `..\WISP.jl` (`72e84ad`); Abnahme A1–A7 erfüllt (`docs/wisp_package_spec.md`). Claude darf in dieses Repo pushen.
   Offen: Tag `v0.1.0`, Namensprüfung vor Registrierung. Python-Test: venv + `PYTHON_JULIACALL_EXE`/`_PROJECT`
   auf eine Kopie von `validation/` mit PythonCall 0.9.37 (Python 3.12 hat OpenSSL 3.0 → juliapkg erlaubt nur Julia ≤ 1.11).
   Fremde Änderung um 13:39 an `analysis/scripts/aggregate/build_sideproject_q3_weak_starts.py` (sha256-Cache) und
   `aggregate_sideproject_q8.py` — nicht von dieser Sitzung, vermutlich die Q8-Auswertung.
5. Termin-Ergebnisse vom 10.11. (Professor) nachtragen, sobald der Nutzer berichtet.

> **Blindregel C-6 aufgehoben (17.11., Nutzer: Paper 1 erledigt).** Vergleich C-6 vs WISP Q9: `DIARY.md` 2026-11-17.

**Feste Regeln:** Claude pusht nie nach GitLab, nach GitHub nur mit ausdrücklicher Erlaubnis. Keine harten Zeit-Cuts.
MATLAB nur MATLAB (kein Octave). Orion-Login abgelaufen → `oc login --web https://api.orion.scch.at:6443`.
Codex: `codex exec -s workspace-write -c 'windows.sandbox="unelevated"' "Lies codex/CODEX_PROTOCOL.md und arbeite den
Auftrag in codex/CURRENT_TASK.md ab." < /dev/null` (Hintergrund). Claude darf auch selbst implementieren (03.11.).
**Uncommittet, nicht von Claude:** WP-N48b-Dateien (PySR, pausiert nach §9.4d), `codex/`-Dateien, `explainer/wisp/src/lv/`,
LV-/Intro-Tests und -Berichte, `WISP_Visualisierungsbriefing_Prozess.md` (gehört dem Nutzer), `paper/wisp/`, `output/`.

# READ_THIS_FIRST.md — Sitzungsübergabe

**Was dieses Dokument ist:** der flüchtige Zustand *zwischen* zwei Chat-Sitzungen — was gerade läuft,
was uncommittet im Working Tree liegt, welche Entscheidung als Nächstes ansteht. Nichts weiter.

**Was es ausdrücklich nicht ist:** ein Planungs- oder Statusdokument. `CLAUDE.md` verbietet ein
zweites davon. Alles Dauerhafte gehört dorthin, nach `PAPER_1.md` oder ins `DIARY.md` —
**nicht hierher.**

**Regeln:** wird immer **vollständig überschrieben**, nie angehängt. Was älter als ein paar Tage
ist, ist vermutlich falsch — dann gilt `CLAUDE.md`.

**Stand: 2026-10-03, ~22:00. Paper-1-Spur im WARTEZUSTAND: alles läuft, nichts ist offen, nichts muss angefasst werden.**

**Feste Regeln:** Claude pusht **nie** nach GitLab und nach GitHub nur mit ausdrücklicher Erlaubnis.
**Keine harten Zeit-Cuts.** Orion-Ergebnisse unter `S:\BigDataOrion\data-science\joedicke\` (nur mit VPN).
**Codex startet Claude selbst:** `codex exec -C "C:/Users/joedicke/Documents/reps/EvoODE" -s workspace-write "Lies codex/CODEX_PROTOCOL.md und arbeite den Auftrag in codex/CURRENT_TASK.md ab." < /dev/null`
(`run_in_background`). **Vor jedem Docker-Build `df -h /c` (< 30 GB → erst aufräumen).** Diese Datei bei
jedem Statuswechsel aktualisieren.

---

## 1. Was läuft (Paper 1), alles auf Orion, Image `5dd1df8` außer C-3/T1f

| Lauf | Stand 03.10. 22:00 | Erwartetes Ende | Wenn fertig |
|---|---|---|---|
| **C-6-Raster gekappt** (3.366 Zellen, 24 Pods) | 5 | Mitte/Ende Nov. | einsammeln (NFS `phase_c_c6_grid_<SHA>/tasks`), Clean-Auswertung, Aggregation |
| **C-6-Raster ungekappt, Seed 42** (461, 8 Pods) | 4 | ähnlich | danach entscheidet der Nutzer über Seed 123/7 (Plan §9.4c Punkt 5) |
| **B-04-Rest + B-05** (10 Zellen) | 3/10 | 57: 1–3 Tage je Zelle | Tor B5. Bisher: gleiches Ergebnis wie C-1 (24 ∞, 52/1000) |
| C-3 | 179/180 | offen (Lorenz) | P-02: endgültige Phase-C-Auswertung |
| WP-T1f | 31/36 | offen (58 IC1) | `--aggregate-only`, Tor 3 Paper 2 |

Lokal läuft nichts. 55 GB frei. Working Tree sauber, ~56 Commits nicht gepusht (pusht der Nutzer).

## 2. Fertig liegt (zum Weitermachen, wenn Ergebnisse kommen)

- Baseline-Export des Rasters auf dem NFS: `phase_c_c6_data_conditions_<SHA>/` (4.536 Zellen, vollständig).
- Harness für SINDy/Weak-SINDy (WP-N34), ODEFormer (WP-N38), PySR 0.19.4 (WP-N39, gewählt). **Noch nicht
  auf dem Raster gestartet.** ODEFormer auf Orion bräuchte ein neues Image (Push durch den Nutzer).
- Auswertungsskripte: `robustness_stage_report.py`, `aggregate_c8_oracle_bounds.py`, Clean-Eval (WP-N33a).

## 3. Offene Paper-1-Punkte, nicht eilig

- Baselines auf dem Raster starten (SINDy/Weak-SINDy billig und lokal).
- Restart-Kurve (P-04), Claim-Tracing-Audit, `paper/` neu schreiben, Story-Entscheidung (Gespräch).
- Einschätzung (Gespräch 03.10.): Das Versuchsdesign hält. Ob die Methode überzeugt, ist offen. Der einzige
  strukturelle Vorteil ist „integrieren statt differenzieren“ unter Rauschen.

## 4. Neue Spur ab 03.10. (Nutzer): Methode radikal verbessern. DENKPAUSE, nichts gebaut

**Der Nutzer denkt in Ruhe nach. Nichts starten, bis er sich meldet.** Der vollständige Denkstand steht in
**`docs/evogrow_next.md`**: woran die Methode krankt, die Fenster-Idee („Random Forest für ODEs“),
warum sie als E-SINDy/E-WSINDy schon existiert, was davon offen bleibt (Invarianz der Koeffizienten
über Zeitfenster als Auswahlkriterium; kurze Fenster integrieren auch für Terme, die nichtlinear in
den Parametern sind), was der Nutzer will (genial einfach, schnell, genau; kein GP, nichts mit
Kronberger) und die zwei billigen Tests, sobald es losgeht (Multiple-Shooting-Orakel, entschieden
als erster Test; Invarianztest).

**Neue Idee 04.10.:** strukturelle Diagnostik über Differentialrelationen vor der Suche, festgehalten in `docs/idea_structural_diagnostics.md` (noch nicht bewertet).

Systeme: Entwicklung 7 / 40 / 56 / 63, verschlossenes Prüfset 4 / 49 / 59 / 62.
Organisation, wenn es losgeht: Worktree `..\EvoODE-next`, Branch `evogrow-next`, eigenes VS-Code-Fenster.
`codex/CURRENT_TASK.md` auf `main`: „Kein aktiver Task“.

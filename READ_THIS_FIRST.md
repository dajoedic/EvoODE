# READ_THIS_FIRST.md — Sitzungsübergabe

**Was dieses Dokument ist:** der flüchtige Zustand *zwischen* zwei Chat-Sitzungen — was gerade läuft,
was uncommittet im Working Tree liegt, welche Entscheidung als Nächstes ansteht. Nichts weiter.

**Was es ausdrücklich nicht ist:** ein Planungs- oder Statusdokument. `CLAUDE.md` verbietet ein
zweites davon. Alles Dauerhafte gehört dorthin, nach `PAPER_1.md` oder ins `DIARY.md` —
**nicht hierher.**

**Regeln:** wird immer **vollständig überschrieben**, nie angehängt. Was älter als ein paar Tage
ist, ist vermutlich falsch — dann gilt `CLAUDE.md`.

**Stand: 2026-10-05, 12:35. Phase C abgeschlossen. Heute: SINDy/Weak-SINDy auf den C-6-Daten läuft lokal, WP-N43 (§9.3-Hierarchie) committet, Entscheidungsregel für Story-Linie (b) wartet auf den Nutzer. Nächste Schritte in `docs/status_2026-10-05.md`.**

**Feste Regeln:** Claude pusht **nie** nach GitLab und nach GitHub nur mit ausdrücklicher Erlaubnis.
**Keine harten Zeit-Cuts — auch keine Tool-Zeitlimits** (Nutzer 05.10.: lange Läufe abgekoppelt starten, Abbruch nur gemeinsam). Orion-Ergebnisse unter `S:\BigDataOrion\data-science\joedicke\` (nur mit VPN).
**Codex startet Claude selbst:** `codex exec -C "C:/Users/joedicke/Documents/reps/EvoODE" -s workspace-write "Lies codex/CODEX_PROTOCOL.md und arbeite den Auftrag in codex/CURRENT_TASK.md ab." < /dev/null`
(`run_in_background`). **Vor jedem Docker-Build `df -h /c` (< 30 GB → erst aufräumen).** Diese Datei bei
jedem Statuswechsel aktualisieren.

---

## 1. Was läuft (Paper 1), alles auf Orion, Image `5dd1df8` außer C-3/T1f

| Lauf | Stand 05.10. 09:15 | Erwartetes Ende | Wenn fertig |
|---|---|---|---|
| **C-6-Raster gekappt** (3.366 Zellen, 24 Pods) | 216 | Mitte/Ende Nov. | einsammeln (NFS `phase_c_c6_grid_<SHA>/tasks`), Clean-Auswertung, Aggregation |
| **C-6-Raster ungekappt, Seed 42** (461, 8 Pods) | 42 | ähnlich | danach entscheidet der Nutzer über Seed 123/7 (Plan §9.4c Punkt 5) |
| **B-04-Rest + B-05** (10 Zellen) | 6/10 | 57: 1–3 Tage je Zelle | Tor B5. Bisher: gleiches Ergebnis wie C-1 (24 ∞, 52/1000) |
| C-3 | **180/180, fertig 05.10.** | — | **P-01/P-02 erledigt 05.10. (`ac64ccc`)**: strikt 936/936, C-1/C-2 identisch; offen: §9.3-Hierarchie |
| WP-T1f | 35/36 | offen (58 IC1) | `--aggregate-only`, Tor 3 Paper 2 |

**Lokal läuft (05.10., gestartet ~11:40): SINDy/Weak-SINDy auf allen 4.536 C-6-Exportzellen**, 10 Shards
parallel, Ausgabe `outputs/c6_sindy_baselines_5dd1df8/shard_<k>/`, Shard 9 trägt die (0,0)-Kontrolle gegen C-4
(126 Zellen). ~50 min je Shard; erwartetes Ende ~12:45–13:10. Hängt noch an einem Tool-Prozess mit 2-h-Limit
(~13:40) — falls nicht fertig, vorher mit dem Nutzer entscheiden. Ein erster Versuch mit 6 Shards wurde nach
30 min vom Tool-Limit ohne Ergebnis beendet. Danach: Shards zusammenführen, Kontrolle prüfen.

55 GB frei. Working Tree sauber bis auf `output/`, `tmp/` (ungetrackt). Commits nicht gepusht (pusht der Nutzer).

## 2. Fertig liegt (zum Weitermachen, wenn Ergebnisse kommen)

- Baseline-Export des Rasters auf dem NFS: `phase_c_c6_data_conditions_<SHA>/` (4.536 Zellen, vollständig).
- Harness für SINDy/Weak-SINDy (WP-N34), ODEFormer (WP-N38), PySR 0.19.4 (WP-N39, gewählt). **Noch nicht
  auf dem Raster gestartet.** ODEFormer auf Orion bräuchte ein neues Image (Push durch den Nutzer).
- Auswertungsskripte: `robustness_stage_report.py`, `aggregate_c8_oracle_bounds.py`, Clean-Eval (WP-N33a).

## 3. Heute begonnen / als Nächstes

- **WP-N43 committet (`60a4393`)**: Aggregation nach Plan §9.3 für EvoGrow, SINDy, ODEFormer; Kontrollen 529/529,
  reproduziert 82,3 / 37,3 % exakt. **Lücke:** varianzgewichtete Generalisierung fehlt für EvoGrow und SINDy.
- **WP-N43b (als Nächstes, Codex):** EvoGrow-Wert aus `outputs/wp_n5_ic_generalization_phase_c/shard_001_of_001/results.jsonl`
  (`generalization_r2_by_dim`, 337/378; Rest divergiert) plus Varianzgewichte aus dem Trajektorien-Export;
  SINDy aus der (0,0)-Bedingung des C-6-SINDy-Laufs (hat by-dim, varianzgewichtet, F1), sofern dessen C-4-Kontrolle hält.
- **Story-Entscheidung vorbereitet:** Claude hat eine Entscheidungsregel für Linie (b) vorgeschlagen (Endpunkt
  Generalisierung R² > 0,9 varianzgewichtet auf dim 1/2; B1: ≥ 10 pp vor der besten Konfiguration jeder Baseline,
  Cluster-p < 0,05; B2: flacherer Abfall σ 0 → 0,05; (b) Hauptbotschaft bei B1 in ≥ 4 von 6 Bedingungen mit σ ≥ 0,03
  und B2). **Wartet auf den Nutzer;** danach als §9.4d im Plan einfrieren, **bevor** C-6-Ergebnisse vorliegen.
- Später (Nutzer): PySR-Freigabe, ODEFormer-Image; Restart-Kurve (P-04), Claim-Tracing-Audit, `paper/` neu schreiben.

## 4. Annihilator-Spur: getrennt (Nutzer, 05.10.)

Die Methodenspur „Idee #1“ lebt **nur** im Ordner `..\EvoODE-next` (Branch `annihilator-discovery`), als eigenes
VS-Code-Projekt mit eigener `CLAUDE.md`, eigenem `READ_THIS_FIRST.md` und eigenem `DIARY.md`. Sie wird in Sitzungen
dieses Ordners nicht bearbeitet. Stand dort: Gate 2A v3, K6 würde auslösen, die Grundsatzentscheidung des Nutzers
ist offen.

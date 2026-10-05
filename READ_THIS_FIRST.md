# READ_THIS_FIRST.md — Sitzungsübergabe

**Was dieses Dokument ist:** der flüchtige Zustand *zwischen* zwei Chat-Sitzungen — was gerade läuft,
was uncommittet im Working Tree liegt, welche Entscheidung als Nächstes ansteht. Nichts weiter.

**Was es ausdrücklich nicht ist:** ein Planungs- oder Statusdokument. `CLAUDE.md` verbietet ein
zweites davon. Alles Dauerhafte gehört dorthin, nach `PAPER_1.md` oder ins `DIARY.md` —
**nicht hierher.**

**Regeln:** wird immer **vollständig überschrieben**, nie angehängt. Was älter als ein paar Tage
ist, ist vermutlich falsch — dann gilt `CLAUDE.md`.

**Stand: 2026-10-05, nachmittags. PAUSE bis alles auf Orion durch ist (Nutzer, 05.10.). Phase C abgeschlossen; heute SINDy/Weak-SINDy auf C-6 und §9.3-Hierarchie erledigt.**

> **BLINDREGEL C-6 (Nutzer, 05.10., „Weg 2“):** Bis die Entscheidungsregel für Story-Linie (b) mit dem Nutzer
> festgelegt und als Plan §9.4d eingefroren ist, sieht sich Claude **keine C-6-EvoGrow-Ergebnisse** an — weder
> R², noch Struktur, noch Vergleiche mit SINDy. Erlaubt ist nur Einsammeln und **technische** Prüfung (Zellenzahl,
> `error`/`failure_reason`, Fingerprint, Daten-Hashes). Die Story-Diskussion folgt, wenn **alles** vom Cluster
> durchgelaufen ist; zuerst die Regel festlegen, dann die Zahlen öffnen.

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

Lokal läuft nichts. **SINDy/Weak-SINDy auf C-6 fertig** (4.536 Zellen × 10 Konf., 40 min, 10 Shards; (0,0)-Kontrolle
gegen WP-C4c 2.520/2.520). Getrackt unter `analysis/data/paper1_phaseC_v1/c6_sindy_5dd1df8/`, `details.csv` (236 MB)
in `outputs/c6_sindy_baselines_5dd1df8/merged/`. Der Vergleich mit EvoGrow unter Rauschen wartet auf die C-6-EvoGrow-Zellen.

55 GB frei. Working Tree sauber bis auf `output/`, `tmp/` (ungetrackt). Commits nicht gepusht (pusht der Nutzer).

## 2. Fertig liegt (zum Weitermachen, wenn Ergebnisse kommen)

- Baseline-Export des Rasters auf dem NFS: `phase_c_c6_data_conditions_<SHA>/` (4.536 Zellen, vollständig).
- Harness für SINDy/Weak-SINDy (WP-N34), ODEFormer (WP-N38), PySR 0.19.4 (WP-N39, gewählt). **Noch nicht
  auf dem Raster gestartet.** ODEFormer auf Orion bräuchte ein neues Image (Push durch den Nutzer).
- Auswertungsskripte: `robustness_stage_report.py`, `aggregate_c8_oracle_bounds.py`, Clean-Eval (WP-N33a).

## 3. Heute erledigt / als Nächstes

- **WP-N43 + N43b committet (`60a4393`, `27673c1`)**: §9.3-Hierarchie, eine Tabelle für EvoGrow, SINDy, ODEFormer,
  `analysis/data/paper1_phaseC_v1/hierarchy_n43b/`. Generalisierung varianzgewichtet: EvoGrow 41,4 %, SINDy 27,0–42,9 %,
  ODEFormer 27,0–33,6 %. Struktur: SINDy besser (gepruned exakt bis 43,3 % vs. EvoGrow 29,4 %). Zahlen in `DIARY.md` 05.10.
- **Quellenfehler gefunden und behoben:** WP-N30/N31 lasen die alte, selbst integrierte SINDy-Datei; 4 R²-Urteile,
  2 Strukturtreffer anders. In `SCRIPTS.md` als überholt markiert.
- **Entscheidungsregel für Linie (b): vertagt bis nach dem Cluster (Blindregel oben). Entwurf zum Wiedervorlegen:** (Endpunkt Generalisierung R² > 0,9 varianzgewichtet auf
  dim 1/2; B1: ≥ 10 pp vor der besten Konfiguration jeder Baseline, Cluster-p < 0,05; B2: flacherer Abfall σ 0 → 0,05;
  (b) Hauptbotschaft bei B1 in ≥ 4 von 6 Bedingungen mit σ ≥ 0,03 und B2). Danach als §9.4d einfrieren, **bevor**
  C-6-Ergebnisse vorliegen.
- B-05 (Tor B5) und WP-T1f (Paper 2) werden früher fertig; ob ihre Tore einzeln oder erst am Ende angesehen werden, hat der Nutzer noch nicht gesagt — bei Fertigstellung fragen.
- Später (Nutzer): PySR-Freigabe, ODEFormer-Image; Restart-Kurve (P-04), Claim-Tracing-Audit, `paper/` neu schreiben.

## 4. Annihilator-Spur: getrennt (Nutzer, 05.10.)

Die Methodenspur „Idee #1“ lebt **nur** im Ordner `..\EvoODE-next` (Branch `annihilator-discovery`), als eigenes
VS-Code-Projekt mit eigener `CLAUDE.md`, eigenem `READ_THIS_FIRST.md` und eigenem `DIARY.md`. Sie wird in Sitzungen
dieses Ordners nicht bearbeitet. Stand dort: Gate 2A v3, K6 würde auslösen, die Grundsatzentscheidung des Nutzers
ist offen.

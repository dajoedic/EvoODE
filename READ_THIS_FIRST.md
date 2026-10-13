# READ_THIS_FIRST.md — Sitzungsübergabe

**Was dieses Dokument ist:** der flüchtige Zustand *zwischen* zwei Chat-Sitzungen — was gerade läuft,
was uncommittet im Working Tree liegt, welche Entscheidung als Nächstes ansteht. Nichts weiter.

**Was es ausdrücklich nicht ist:** ein Planungs- oder Statusdokument. `CLAUDE.md` verbietet ein
zweites davon. Alles Dauerhafte gehört dorthin, nach `PAPER_1.md` oder ins `DIARY.md` —
**nicht hierher.**

**Regeln:** wird immer **vollständig überschrieben**, nie angehängt. Was älter als ein paar Tage
ist, ist vermutlich falsch — dann gilt `CLAUDE.md`.

**Stand: 2026-10-13, 01:10. Paper-1-Pause gelockert: Auswertungen, die nicht C-6-EvoGrow betreffen, laufen (Nutzer 12./13.10.).**

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

## 1. Was läuft — Orion, Image `5dd1df8`, **40 Kerne belegt = Limit (Nutzer 13.10.)**

| Lauf | Stand | Erwartetes Ende | Wenn fertig |
|---|---|---|---|
| **C-6-Raster gekappt** (3.366 Zellen, 24 Pods) | **670** (13.10. 01:10) | zuletzt ~31/Tag → evtl. erst ~Jan.; beobachten | einsammeln (NFS `phase_c_c6_grid_<SHA>/tasks`), Clean-Auswertung, Aggregation |
| **C-6-Raster ungekappt, Seed 42** (461, 8 Pods) | **180** | ~16/Tag → ~Ende Okt. | Nutzer entscheidet über Seed 123/7 (Plan §9.4c Punkt 5); 8 Kerne werden frei |
| ~~P-04 Restart-Kurve~~ | **fertig 13.10.**, eingesammelt und ausgewertet (DIARY 13.10.): Kontrolle 159/159 bitgleich; k=3 64 % → k=10 80 %, dim 2 33 % → 65 % | — | 8 Kerne wieder frei (32 belegt) |
| **WP-T2a S1** (Orakel-Prior, dim 2, Seed 42, 20 Zellen, 8 Pods) | gestartet 13.10. abends, Image `e483f83` | erwartet ~50–60 h (2–3 Zellen ~50 h in C-1) | einsammeln von NFS `paper2_t2a_s1_e483f83…/tasks`; Tor T2a-1 nur auf fittbaren dim-2-Zellen (P-04: 39/60) |

**Kern-Limit:** EvoODE max. **40 Kerne gesamt** (vorher 32). Kein Kern mehr. Laufende Jobs nie herunterdrehen (tötet
Pods); neue Jobs warten auf frei werdende Kerne. Wenn P-04 endet, sind 8 Kerne frei (Kandidat: WP-T2a S1, braucht
erst Implementierung + Image).

**Lokal:** nichts läuft. **WP-T2a S1 läuft** (Eingaben auf dem NFS unter `paper2_t2a_pilot_v1_e483f83…/`, bytegleich geprüft). Weak-SINDy (mit Seed) + E-SINDy fertig,
saubere §9.3-Tabelle mit allen fünf Verfahren committet (`021a654`): Weak-SINDy schlägt EvoGrow bei Struktur und bei
bester Generalisierung → Claim D umformulieren.

**Fertig, eingesammelt und ausgewertet am 12.10. (`DIARY.md` 12.10.):**
- **B-05 (Tor B5):** 1/24/52 gleicher Support wie C-1; 57 wechselt den Support, findet die Wahrheit aber mit keiner
  Grenze, obwohl das Orakel sie ohne Grenze fittet → Suchversagen. `[-1000, 1000]` bleibt Start der nächsten Version.
  Tabelle `analysis/data/paper1_phaseC_v1/c8_search_b04_b05/`.
- **WP-T1f (Tor 3 Paper 2):** 0 von 2.479 Swaps und 0 von 179 Removes unter dem Boden, Abstand ≥ 5 Größenordnungen →
  wahrer Support ist lokales Optimum, Stopp-Regel greift nicht. Nächster Schritt des Zweigs wäre der WP-T2a-Pilot
  (Paper 2, nicht Paper 1) — Nutzer entscheidet, wann.

**13.10.:** P-04 und WP-T2a-Pilot eingefroren (Plan §9.8, `docs/phd_thesis_arc.md` §5 Schritt 4; ε = 0,2, P ∝ 1/Rang,
S2 nur über Tor T2a-1). E-SINDy + Weak-SINDy Pflicht in Paper 1 (Plan §9.5a). WP-T2a-Implementierung (Codex, Julia,
neues Image) ist der nächste Auftrag nach WP-N45.

0 fehlgeschlagene Pods am 12.10.

Lokal läuft nichts. **SINDy/Weak-SINDy auf C-6 fertig** (4.536 Zellen × 10 Konf., 40 min, 10 Shards; (0,0)-Kontrolle
gegen WP-C4c 2.520/2.520). Getrackt unter `analysis/data/paper1_phaseC_v1/c6_sindy_5dd1df8/`, `details.csv` (236 MB)
in `outputs/c6_sindy_baselines_5dd1df8/merged/`. Der Vergleich mit EvoGrow unter Rauschen wartet auf die C-6-EvoGrow-Zellen.

**Nur noch 27 GB frei (10.10.) — vor dem nächsten Docker-Build aufräumen.** Working Tree sauber bis auf `output/`, `tmp/` (ungetrackt). Commits nicht gepusht (pusht der Nutzer).

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
- B-05 (Tor B5) und WP-T1f (Paper 2) werden früher fertig; ob ihre Tore einzeln oder erst am Ende angesehen werden, hat der Nutzer noch nicht gesagt — am 10.10. erneut gefragt, zusammen mit der Frage, ob die 9-Tage-Zelle von WP-T1f weiterlaufen soll.
- Später (Nutzer): PySR-Freigabe, ODEFormer-Image; Restart-Kurve (P-04), Claim-Tracing-Audit, `paper/` neu schreiben.

## 4. Annihilator-Spur: getrennt (Nutzer, 05.10.)

Die Methodenspur „Idee #1“ lebt **nur** im Ordner `..\EvoODE-next` (Branch `annihilator-discovery`), als eigenes
VS-Code-Projekt mit eigener `CLAUDE.md`, eigenem `READ_THIS_FIRST.md` und eigenem `DIARY.md`. Sie wird in Sitzungen
dieses Ordners nicht bearbeitet. Stand dort: Gate 2A v3, K6 würde auslösen, die Grundsatzentscheidung des Nutzers
ist offen.

# READ_THIS_FIRST.md — Sitzungsübergabe

**Was dieses Dokument ist:** der flüchtige Zustand *zwischen* zwei Chat-Sitzungen — was gerade läuft,
was uncommittet im Working Tree liegt, welche Entscheidung als Nächstes ansteht. Nichts weiter.

**Was es ausdrücklich nicht ist:** ein Planungs- oder Statusdokument. `CLAUDE.md` verbietet ein
zweites davon. Alles Dauerhafte gehört dorthin, nach `PAPER_1.md` oder ins `DIARY.md` —
**nicht hierher.**

**Regeln:** wird immer **vollständig überschrieben**, nie angehängt. Was älter als ein paar Tage
ist, ist vermutlich falsch — dann gilt `CLAUDE.md`.

**Stand: 2026-10-12, 23:50. PAUSE bis alles auf Orion durch ist (Nutzer, 05.10.). Phase C abgeschlossen; seit 05.10. nur Statusabfragen.**

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

## 1. Was läuft (Paper 1), alles auf Orion, Image `5dd1df8`

| Lauf | Stand 12.10. 23:36 (10.10. 13:05) | Erwartetes Ende | Wenn fertig |
|---|---|---|---|
| **C-6-Raster gekappt** (3.366 Zellen, 24 Pods) | **666** (591) | zuletzt nur ~31/Tag (davor ~75/Tag) → bei diesem Tempo ~Jan.; zwei Tage sind noch kein Trend | einsammeln (NFS `phase_c_c6_grid_<SHA>/tasks`), Clean-Auswertung, Aggregation |
| **C-6-Raster ungekappt, Seed 42** (461, 8 Pods) | **180** (141) | ~16/Tag → ~Ende Okt. | danach entscheidet der Nutzer über Seed 123/7 (Plan §9.4c Punkt 5) |

**Fertig, eingesammelt und ausgewertet am 12.10. (`DIARY.md` 12.10.):**
- **B-05 (Tor B5):** 1/24/52 gleicher Support wie C-1; 57 wechselt den Support, findet die Wahrheit aber mit keiner
  Grenze, obwohl das Orakel sie ohne Grenze fittet → Suchversagen. `[-1000, 1000]` bleibt Start der nächsten Version.
  Tabelle `analysis/data/paper1_phaseC_v1/c8_search_b04_b05/`.
- **WP-T1f (Tor 3 Paper 2):** 0 von 2.479 Swaps und 0 von 179 Removes unter dem Boden, Abstand ≥ 5 Größenordnungen →
  wahrer Support ist lokales Optimum, Stopp-Regel greift nicht. Nächster Schritt des Zweigs wäre der WP-T2a-Pilot
  (Paper 2, nicht Paper 1) — Nutzer entscheidet, wann.

**13.10. — neu in Arbeit:**
- **P-04 Restart-Kurve startbereit** (Plan §9.8, eingefroren): WP-N44 committet (`f6e0887`), Laptop-Smoke auf 2 Zellen
  bitgleich gegen C-5, Eingabe liegt auf dem NFS (`phase_c_c5_restart_curve_5dd1df8…/input/history.jsonl`, sha
  identisch zur C-5-Eingabe). **Start durch den Nutzer** mit `k8s/phase_c_c5_restart_curve_job.yaml`, Image `5dd1df8`,
  ~130 Kernstunden erwartet (Schranke 338 h).
  **Pod-Limit (Nutzer 13.10.): EvoODE max. 32 Pods gesamt — C-6 belegt alle 32.** P-04 (`parallelism: 8`) startet erst,
  wenn Slots frei werden (ungekapptes C-6-Raster, ~Ende Okt.); laufende Jobs nicht herunterdrehen (tötet Pods).
- **WP-T2a-Pilot** spezifiziert und eingefroren (`docs/phd_thesis_arc.md` §5 Schritt 4): wartet auf P-04.
- **E-SINDy + Weak-SINDy Pflicht in Paper 1** (Nutzer, Plan §9.5a). **WP-N45 läuft bei Codex** (E-SINDy-Arm,
  beide in der §9.3-Hierarchie); den vollen E-SINDy-Lauf macht danach Claude lokal.

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

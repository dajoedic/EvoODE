# READ_THIS_FIRST.md — Sitzungsübergabe

**Was dieses Dokument ist:** der flüchtige Zustand *zwischen* zwei Chat-Sitzungen — was gerade läuft,
was uncommittet im Working Tree liegt, welche Entscheidung als Nächstes ansteht. Nichts weiter.

**Was es ausdrücklich nicht ist:** ein Planungs- oder Statusdokument. `CLAUDE.md` verbietet ein
zweites davon. Alles Dauerhafte gehört dorthin, nach `PAPER_1.md` oder ins `DIARY.md` —
**nicht hierher.**

**Regeln:** wird immer **vollständig überschrieben**, nie angehängt. Was älter als ein paar Tage
ist, ist vermutlich falsch — dann gilt `CLAUDE.md`.

**Stand: 2026-10-05 morgens. Paper-1-Spur im WARTEZUSTAND (Tabelle Stand 03.10.). Methodenspur: **Gate 2A v2 an K-c gescheitert (FNS-Fehler), v3 freigegeben, Codex baut WP-G2A3-a** (§4).**

**Feste Regeln:** Claude pusht **nie** nach GitLab und nach GitHub nur mit ausdrücklicher Erlaubnis.
**Keine harten Zeit-Cuts.** Orion-Ergebnisse unter `S:\BigDataOrion\data-science\joedicke\` (nur mit VPN).
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

## 4. Methodenspur „Idee #1 – Annihilator-Discovery“: Stand 04.10.

**Eigener Branch `annihilator-discovery`, Worktree `..\EvoODE-next`** (eigenes VS-Code-Fenster). `main` bleibt hier
für die Paper-1-Ergebnisse. Der Name `evogrow-next` ist verworfen, weil die Methode keine EvoGrow-Weiterentwicklung ist.

- Leitdokument `docs/IDEA_01_ANNIHILATOR_DISCOVERY.md` (nur auf dem Branch). Löst `idea_structural_diagnostics.md` ab.
- **`docs/GATE_2A.md` eingefroren**, vom Nutzer abgenommen (E1–E4). Dazu die exakte Vorab-Kontrolle der
  Referenzklassen (DIARY auf dem Branch, 04.10.).
- **Stand Gate 2A, 04.10. ~03:00: Implementierung committet (Branch `9d6a4d0`), Abnahme `blocked`, Gate-Lauf NICHT
  gestartet. Der Nutzer entscheidet.**
  - Bestanden: Orakel (60 Stellen, alle 20 Referenzklassen), Transfer, Determinismus. F2 besteht auch das
    Kovarianz-Monte-Carlo exakt.
  - Nicht bestanden: F4 (log x) und F9 (x²+eˣ). Drei Ursachen (Diagnose im DIARY auf dem Branch, 04.10.):
    (1) Die Weak-Matrix ist zu ungenau für hohe Ableitungsordnungen (F9 ~1e-4). Der Clean-Boden 1e-8 ist nicht
    erreichbar, F2 clean wird AMBIGUOUS. (2) Die SVD-Schätzung ist bei heteroskedastischem Rauschen verzerrt
    (F4: Bias = 47 × Streuung). (3) Schmale Testfunktionen verstärken das Rauschen so stark, dass F9 bei 1 % nicht
    identifizierbar ist.
  - **04.10.: v2 eingefroren und vom Nutzer abgenommen** (`docs/GATE_2A_v2.md`, Begründung `docs/GATE_2A_v2_RATIONALE.md`,
    Branch `7609529`). Vor dem Einfrieren auf K5 gemessen: Der Matrixfehler hatte zwei Ursachen, Rundung der Monomdarstellung
    und Quadratur. Beide sind in v2 behoben.
  - **Externes Review 04.10. eingearbeitet, vor jedem Lauf** (Branch `50bdf57`): FNS/AML-Begriffe, A3 als projektive
    Winkelunsicherheit, Kalibrier-Set um K7/K8 (Ordnung 5/6) erweitert, Hold-out-Hinweis. Codex wurde dafür angehalten und neu gestartet.
  - **05.10. vormittags: Methodenspur faktisch am Kill-Kriterium K6.** Anhang A von v3 besteht nicht (K6-Kovarianz,
    K7 schmal `WRONG`). Anhang B als Diagnose (Nutzer: Option A): Bei 1 % breit sind F4, F5, F8, F9 und F10 N1, **K6 würde
    auslösen** (3 > 1). Bei 1 % unterscheiden die Daten polynomiale nicht von konstanten Koeffizienten. **Lies
    `docs/GATE_2A_v3_STAGE_K_RESULT.md` auf dem Branch (Nachtrag 1).** Entscheidung beim Nutzer: Spur beenden oder
    grundsätzlich neu bewerten (Messdesign, nicht Schätzer).
  - **05.10. nachts:** v2-Stufe K: K-a/K-b bestanden ($\ell_{\max}=4$, $\tau=3.4\cdot10^{-7}$), **K-c gescheitert**, weil FNS
    Sattelpunkte findet statt Minima. Mit L-BFGS sind Ordnung 1–3 repariert. Ab Ordnung 4 sind die Koeffizienten bei 1 % nicht
    identifizierbar. Airy/Bessel sind schon breit N1, **bei F4/F5 droht K6**. **v3 vom Nutzer freigegeben** (`docs/GATE_2A_v3.md`,
    Branch `140430a`). Codex baut WP-G2A3-a. Danach startet Claude Stufe K ohne Zeitgrenze (Nutzer), dann Abnahme Anhang A durch
    den Nutzer, dann Anhang B (erstes echtes Signal zu K6).
  - **04.10. mittags: Codex-Nutzungslimit erreicht** (wieder frei ab 15:02). WP-G2A2-a ist angefangen, der Code liegt uncommittet unter
    `experiments/annihilator_gate2a_v2/`, noch kein Lauf. Danach denselben `codex exec`-Befehl im Worktree `EvoODE-next` neu starten.
  - **Angehalten: Codex WP-G2A2-a** im Worktree `EvoODE-next`: Code unter `experiments/annihilator_gate2a_v2/`, Orakel mit 100
    Stellen, Stufe K → Anhang A, dann Stopp. **Nächster Schritt danach: Der Nutzer nimmt Anhang A ab.** Erst dann Abnahme
    auf F1–F10 und Gate-Lauf (eigenes Arbeitspaket).
- Kein Gate 2B, bevor 2A bestanden ist. Multiple Shooting und Invarianztest bleiben geparkt (`docs/evogrow_next.md`).

**Regeln dieser Spur:** von einfach zu komplex; kein GP; nichts mit Gabriel Kronberger (Autorenschaft prüfen).
Systeme für spätere Gates: Entwicklung 7 / 40 / 56 / 63, verschlossenes Prüfset 4 / 49 / 59 / 62.
`codex/CURRENT_TASK.md` auf `main`: „Kein aktiver Task“. Der aktive Auftrag liegt auf dem Branch.

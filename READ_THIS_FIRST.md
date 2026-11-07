# READ_THIS_FIRST.md — Sitzungsübergabe

**Was dieses Dokument ist:** der flüchtige Zustand *zwischen* zwei Chat-Sitzungen — was gerade läuft,
was uncommittet im Working Tree liegt, welche Entscheidung als Nächstes ansteht. Nichts weiter.

**Was es ausdrücklich nicht ist:** ein Planungs- oder Statusdokument. `CLAUDE.md` verbietet ein
zweites davon. Alles Dauerhafte gehört dorthin, nach `PAPER_1.md` oder ins `DIARY.md` —
**nicht hierher.**

**Regeln:** wird immer **vollständig überschrieben**, nie angehängt. Was älter als ein paar Tage
ist, ist vermutlich falsch — dann gilt `CLAUDE.md`.

**Stand: 2026-11-07, ~01:30 (G2 entschieden: WISP = C1000, erklärte Abweichung von R2) — WISP-Plan bis 31.12. (CLAUDE.md, „WISP paper — the fixed plan“).**

## 1. Was läuft (Orion, Stand 07.11. ~01:20)

| Lauf | Stand | Wenn fertig |
|---|---|---|
| **W-2 = Q8-Gitter** (`512dd5b`, 3.540 Shards) | **3.533/3.540**, 0 Fehler, 7 Nachzügler (Lorenz 55 A/C1000 ~10 Fits zu 3–9 h → 1,5–4 Tage; 61 IC 2 ×3; 40/48 A1000; 48 Zufallsstart sauber) | offizielle Aggregation `aggregate_sideproject_q8.py` (braucht 3.540/3.540; kann keine Regel mehr kippen) |
| **C-6 gekappt** | 1.435/3.366, **Parallelität 0** (leergezogen, kein Pod getötet) | nach W-4 zurück auf 24 |

**Kerne: ~32 von 40 frei seit 06.11. ~17 Uhr** (Q8-Parallelität 40, nur 7 aktiv). Nutzer-Entscheidung offen: leer lassen bis Q9 oder C-6 vorübergehend hoch.
**NFS-Zugriff:** S: hing 07.11. (Semaphore-Timeout). Schnellweg: `MSYS_NO_PATHCONV=1 oc exec <laufender-q8-pod> -- tar czf - -C /outputs/sideproject_q8_512dd5bd534530327b1f5fed3e7892a1e0950016 out > ….tgz` (12,7 MB, 7 s; unkomprimiert bricht der Strom bei ~250 MB ab).
**Rückweg C-6 nach W-4:** `oc patch job evoode-phase-c-c6-grid-capped -n scch-das -p '{"spec":{"parallelism":24}}'`.

## 2. WISP-Explorable (W-X)

- Preview https://claude.ai/artifact/XsxgvgYGZdqPkpnzVd2YMQ **Version 26** (05.11. nachts, `a7cd868`) — **inhaltlich
  vollständig**: Einführung + Kap. 1 (11) · 2 Hinzufügen (5) · 3 Aufräumen/FoBa (7) · 4 Aufhören/Q7 (5) · 5 Fitten +
  Wählen/BIC (6) · 6 Zwei Gleichungen (System 27) · 7 Wenn es schiefgeht (System 3 ab 21) · 8 Gegenprobe · 9 Wie oft
  klappt das? (Q7-Ergebnisse vorläufig, SINDy/Weak-SINDy/E-SINDy, MATLAB-WSINDy JKU-bestätigt, Explorer, Glossar).
  Browser-Check und volle `-k wisp`-Sammlung (77) grün.
- **Offen:** (1) Nutzer-Idee zur Darstellung der Spiegelung Hinzufügen/Aufräumen (bis dahin schlicht gebaut, Kap. 3/4);
  (2) Nutzer-Review der neuen Kapitel 5–9; (3) nach G2: Fit-Einstellungen in Kap. 5 über `gates.json`; (4) nach W-4:
  Datentausch auf Q9 (`results.json`, Julia-Display-Export, `data-claim`-Sätze nachlesen).
- **Tests:** schnelle Darstellungstests (`test_wisp_explainer_x*.py` ohne `_x2`) + `check_wisp_explainer_js.py` beim
  Iterieren; volle `-k wisp` (~3–5 min) bei Daten-/Exportänderung; Browser-Check `check_wisp_explainer_fit.py` startet
  Claude (Codex-Sandbox kann keinen Browser). Im Fit-JSON sind `exponent`/`rawNames` Fehler-Flags (`false` = ok).
  Julia-Display-Export der Ergebnisse: `--q7-results` (~3 min, 814 Auswertungen).

## 3. Als Nächstes

1. ~~Q7 / G-Q7~~ erledigt 05.11. ~~G2~~ **entschieden 07.11.: C1000 + Q7-Stopp** (`DIARY.md` 07.11., CLAUDE.md W-3).
   Zwischenauswertung: Scratchpad-Skripte `q8_sneak.py`/`q8_decide.py` der Sitzung `74de8444…`, Daten
   `outputs/sideproject_q8_512dd5b…/out_sneak_2026-11-07/`.
2. **W-4 / Q9 vorbereiten:** Q9-Protokoll (C1000, alle 63 Systeme, 11 Bedingungen × 3 Realisierungen), **Laufzeit-
   Hochrechnung mit 54–59 unter 1000 gegen die 21-Tage-Grenze vor dem Start**, Image (Nutzer pusht).
3. Offizielle Q8-Aggregation, sobald 3.540/3.540.
4. **Termin mit dem Professor Di 10.11., 30 min.** Folien https://claude.ai/artifact/Fi25YcnmvhWFo4yRC7yc1i (privat):
   Folien „von nichts zu WISP“ → **WISP live im Explorable (Kern, ~12 min)** → Folien „von WISP zum PhD“ (Plan, Journal,
   Promotion, drei Entscheidungen); Methoden-/Ergebnisfolien als Reserve am Ende. Explorable bis Dienstag: Kapitel 3
   Aufräumen, 4 Aufhören, 5 Fitten/Wählen, 6 Ergebnisse — Nutzer kümmert sich. Lücke Folie „Weg zur Promotion“:
   Vorgabe Doktoratsstudium und Zielzeitpunkt.

> **BLINDREGEL C-6** gilt unverändert: keine C-6-EvoGrow-Ergebnisse ansehen, nur technische Prüfung.

**Feste Regeln:** Claude pusht nie nach GitLab, nach GitHub nur mit ausdrücklicher Erlaubnis. Keine harten Zeit-Cuts.
MATLAB nur MATLAB (kein Octave): `C:\Program Files\MATLAB\R2026b\bin\matlab.exe`. Orion-Login abgelaufen →
`oc login --web https://api.orion.scch.at:6443`. Orion-Ergebnisse unter `S:\BigDataOrion\data-science\joedicke\` (VPN).
Codex: `codex exec -s workspace-write -c 'windows.sandbox="unelevated"' "Lies codex/CODEX_PROTOCOL.md und arbeite den
Auftrag in codex/CURRENT_TASK.md ab." < /dev/null` (Hintergrund); ein per TaskStop angehaltener Lauf kann als
verwaister Prozess weiterlaufen — prüfen und dessen halbe Änderungen zurücksetzen. Nutzer erlaubt Claude auch, selbst zu
implementieren (03.11.).
**Uncommittet, nicht von Claude:** WP-N48b-Dateien (PySR, pausiert nach §9.4d) und `output/`.

**Statusseite „EvoODE auf Orion“:** https://claude.ai/artifact/9zzJsoGCBahPsuNkaaf3DN — Version 13 (05.11., ~10:00).

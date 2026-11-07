# READ_THIS_FIRST.md — Sitzungsübergabe

**Was dieses Dokument ist:** der flüchtige Zustand *zwischen* zwei Chat-Sitzungen — was gerade läuft,
was uncommittet im Working Tree liegt, welche Entscheidung als Nächstes ansteht. Nichts weiter.

**Was es ausdrücklich nicht ist:** ein Planungs- oder Statusdokument. `CLAUDE.md` verbietet ein
zweites davon. Alles Dauerhafte gehört dorthin, nach `PAPER_1.md` oder ins `DIARY.md` —
**nicht hierher.**

**Regeln:** wird immer **vollständig überschrieben**, nie angehängt. Was älter als ein paar Tage
ist, ist vermutlich falsch — dann gilt `CLAUDE.md`.

**Stand: 2026-11-07, ~02:40 (Q9 läuft; G2 = C1000) — WISP-Plan bis 31.12. (CLAUDE.md, „WISP paper — the fixed plan“).**

## 1. Was läuft (Orion, Stand 07.11. ~02:30)

| Lauf | Stand | Wenn fertig |
|---|---|---|
| **W-4 = Q9-Gitter** (`cdfaa7d`, 4.284 Shards, C1000) | **gestartet 02:29**, 31→32 Pods; Probe (9 Shards) technisch sauber, Rest der Probe läuft aus | Hochrechnung aus den ersten langen Shards (Lorenz 55/56, 61); 21-Tage-Regel |
| **W-2 = Q8-Gitter** (`512dd5b`) | 3.533/3.540, 6 Nachzügler (Lorenz 55 ×2, 61 ×3, 48-Ablation) | offizielle Aggregation `aggregate_sideproject_q8.py` bei 3.540/3.540 |
| **C-6 gekappt** | 1.435/3.366, **Parallelität 0** | nach W-4 zurück auf 24 |

**Kerne:** Q9 = 40 − aktive Q8- und Probe-Pods. Lokal läuft `q9_shift.sh` (Scratchpad der Sitzung `74de8444…`, detached,
Log `q9_shift.log` daneben): alle 10 min Q9-Parallelität anheben, nie senken, endet bei 40. Braucht Laptop + VPN +
gültigen oc-Login; fällt es aus, verschenkt Q9 nur Kerne, nichts geht kaputt. Neu starten (Git Bash):
`/c/Users/joedicke/AppData/Local/Temp/claude/4da8ff96f3389fae/74de8444-749b-46d9-b373-f84449c9b174/scratchpad/q9_shift.sh >> …/q9_shift.log 2>&1 & disown`
**NFS-Zugriff:** S: hing 07.11. Schnellweg: `MSYS_NO_PATHCONV=1 oc exec <laufender-pod> -- tar czf - -C /outputs/<lauf> out > ….tgz`
(komprimiert; unkomprimiert bricht der Strom bei ~250 MB ab). Technische Probe-Prüfung: Scratchpad `q9_probe_check.py`.
**Rückweg C-6 nach W-4:** `oc patch job evoode-phase-c-c6-grid-capped -n scch-das -p '{"spec":{"parallelism":24}}'`.

## 2. WISP-Explorable (W-X)

- **NEU 07.11. abends: Neustart als LV-Geschichte nach Konzept** `explainer/wisp/CONCEPT.md` (vom Nutzer abgenommen).
  Quelle `explainer/wisp/story/`, Build `python analysis/scripts/explainer/build_wisp_story.py` → `dist/wisp_story.html`,
  Vorschau https://claude.ai/artifact/M7vvNRbcV1LA344CrmS82u (Version 1, `01a750c`). 15 Seiten A/B/C, DE/EN, hell/dunkel,
  Screenshots Desktop+Handy geprüft (Scratchpad-Skript `shoot.py`, Playwright mit `channel='msedge'`). Ziel Di 10.11.;
  **Mo abends Entscheidung**: steht's, sonst Version 26. Offen: Nutzer-Review; Explorer (Konzept C2) fehlt noch.
  Claude baut selbst; die Codex-Fassung `src/lv/` und die alten Kapitel unten sind Altbestand.
- Alt: Preview https://claude.ai/artifact/XsxgvgYGZdqPkpnzVd2YMQ **Version 26** (05.11. nachts, `a7cd868`) — **inhaltlich
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

1. ~~G2~~ **entschieden 07.11.: C1000 + Q7-Stopp** (`DIARY.md`). ~~Q9 bauen und starten~~ **läuft seit 07.11. 02:29.**
2. Q9 beobachten: Hochrechnung aus den ersten langen Shards; >21 Tage → Nutzer entscheidet (Plan W-4).
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

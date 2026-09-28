# READ_THIS_FIRST.md — Sitzungsübergabe

**Was dieses Dokument ist:** der flüchtige Zustand *zwischen* zwei Chat-Sitzungen — was gerade läuft,
was uncommittet im Working Tree liegt, welche Entscheidung als Nächstes ansteht. Nichts weiter.

**Was es ausdrücklich nicht ist:** ein Planungs- oder Statusdokument. `CLAUDE.md` verbietet ein
zweites davon. Alles Dauerhafte gehört dorthin, nach `PAPER_1.md` oder ins `DIARY.md` —
**nicht hierher.**

**Regeln:** wird immer **vollständig überschrieben**, nie angehängt. Was älter als ein paar Tage
ist, ist vermutlich falsch — dann gilt `CLAUDE.md`.

**Stand: 2026-09-28, 22:30.** Push und `oc apply` macht der Nutzer. Die einmalige Freigabe vom
28.09. für den WP-T1f-Start ist verbraucht.

---

## 1. Was läuft

| Lauf | Wo | Stand 28.09. 22:00 | Anmerkung |
|---|---|---|---|
| C-1/C-2 | Orion, `221a3a7` | 755 / 756 | Zelle 474 (System 40, ungekappt), Level 29/30 |
| C-3 | Orion, `221a3a7` | 175 / 180 | 5 × Lorenz 55/56 `pretune_on`, Level 26–27/30, ~20–25 h/Level → Ende ~1./2.10. |
| WP-T1f | Orion, `1db1193` | 13 / 36 | ohne Kappung, `parallelism: 6`, Deadline 14 Tage; dim-3-Zellen zuletzt, Ende ~3./4.10. |

Fertig, noch nicht eingesammelt: **ODEFormer-Kandidatenraster** (`8e0e699`, 126/126). Einsammeln
mit `--collect` für `…/candidate`, Befehl in `SCRIPTS.md`, Abschnitt ODEFormer auf Orion.

Status lesen ohne eigenen Pod: `oc exec` in einen laufenden Kampagnen-Pod, NFS unter `/outputs`.
Die Online-Statusseite „EvoODE auf Orion“ (https://claude.ai/artifact/4sq6HhRsnxgrFVqVF2trBx)
steht auf 28.09. 22:00 und ist bei jedem Statuswechsel neu zu veröffentlichen.

## 2. Nächster Meilenstein: Statusgespräch

Wenn C-1/C-2, C-3 und WP-T1f fertig sind (~3./4.10.) und der Cluster leer ist. **Bis dahin nichts
Neues starten, insbesondere nicht C-5.** Themen:

1. Parameter-Kappung (DIARY 28.09., CLAUDE.md Known Gaps): dim-3-Auswertung (erreichbar 52/61 vs.
   unerreichbar 54–59), ob der C-5-Orakel-Arm mit Kappung läuft, Claim D, Deutung des „dim-3-Kollapses“.
2. Phase C vollständig auswerten.
3. WP-T1f-Tor. Zwischenbild dim 2: 0/351 Swaps, 0/35 Removes unter dem Boden; Kaltstarts treffen die
   Wahrheit selten (1–11 von 20 je System).
4. ODEFormer-Kandidat (torch-Sensitivität für Claim D).
5. Reihenfolge C-5, WP-T2a.
6. `CLAUDE.md` eindampfen (983 Zeilen) zusammen mit dem Claim-Tracing-Audit; dabei den Start der
   Phase-C-Kampagne in `SCRIPTS.md` nachtragen und prüfen, ob sich ältere DIARY-Monate auslagern lassen.

## 3. Vorbereitung bis dahin (ohne Rechenlast)

- ODEFormer-Kandidat einsammeln.
- `analysis/configs/paper1_phaseC_v1.json` zeigt noch auf die Probe `outputs/phase_c_dryrun_2026-09-25/`;
  nach dem Ende von C-1/C-2/C-3 auf die vollständige Registry umstellen (ohne `--allow-incomplete`).
- WP-T1f nach dem Ende einsammeln (tar über `oc exec`, Befehl in `SCRIPTS.md`) und mit
  `--aggregate-only` auswerten.

## 4. Offen, klein

- `codex/STATUS.md` zeigt noch die letzte Codex-Meldung (WP-T1f-d `blocked`). Das ist korrekt
  historisch, weil nur Codex hineinschreibt; `CURRENT_TASK.md` steht auf „Kein aktiver Task“.
  Angebot an den Nutzer: Protokollregel „leerer CURRENT_TASK ⇒ STATUS.md abgeschlossen“.

## 5. Git

Working Tree sauber. Gepusht bis `1db1193` (beide Remotes). Lokal, **nicht gepusht**: `14dc9b5`,
`8bf7769`, `d97ceaf` und der Commit dieser Datei — nur Dokumentation.

# READ_THIS_FIRST.md — Sitzungsübergabe

**Was dieses Dokument ist:** der flüchtige Zustand *zwischen* zwei Chat-Sitzungen — was gerade läuft,
was uncommittet im Working Tree liegt, welche Entscheidung als Nächstes ansteht. Nichts weiter.

**Was es ausdrücklich nicht ist:** ein Planungs- oder Statusdokument. `CLAUDE.md` verbietet ein
zweites davon. Alles Dauerhafte gehört dorthin, nach `PAPER_1.md` oder ins `DIARY.md` —
**nicht hierher.**

**Regeln:** wird immer **vollständig überschrieben**, nie angehängt. Was älter als ein paar Tage
ist, ist vermutlich falsch — dann gilt `CLAUDE.md`.

**Stand: 2026-10-02, ~13:00.** Arbeitsreihenfolge: Backlog in `CLAUDE.md` („Backlog Paper 1“).

**Feste Regeln:** Claude pusht **nie** nach GitLab und nach GitHub nur mit ausdrücklicher Erlaubnis,
beides macht der Nutzer. **Keine harten Zeit-Cuts.** `codex exec` immer mit `< /dev/null`.
Orion-Ergebnisse liegen lokal lesbar unter `S:\BigDataOrion\data-science\joedicke\` (Git Bash:
`/s/BigDataOrion/...`). Einsammeln geht ohne `oc exec`, der Jobstatus braucht `oc login`.

---

## 1. Was läuft

| Lauf | Wo | Image | Stand | Anmerkung |
|---|---|---|---|---|
| C-3 | Orion | `221a3a7` | 178/180 | 2 Lorenz-Nachzügler (Index 14, 22), seit 14 d |
| WP-T1f | Orion | `1db1193` | 28/36 | 6 Pods laufen, 58 IC1 langsam |

Lokal läuft nichts.

**Fertig und eingesammelt am 02.10.:** Stufe 2 gekappt (`outputs/phase_c_robustness_stage2_5dd1df8/`,
Clean-Auswertung je Bedingung unter `clean_eval/`), B-02 (`outputs/phase_c_c8_oracle_b02_5dd1df8/`),
R-05b lokal (`outputs/uncapped_noise/`). Zahlen im DIARY 02.10. Die vorläufige B-02-Auswertung kommt
aus einem Wegwerf-Skript, nicht aus dem Repo. Für das Tor B3 braucht es ein richtiges Skript
(Codex-WP).

## 2. Wartet auf den Nutzer

- **Ungekappter Arm für 18/24 auf Orion: laufen lassen oder streichen?** Die Kappe ist dort unter
  Rauschen `nothing`, das Ergebnis wäre per Konstruktion identisch. Empfehlung: streichen.
- **Tor S2** (Stufe 2 komplett): weiter zu Stufe 3 (System 41)?
- **Tor B2:** weiter zu B-03 (Orakel dim 3/4)? Vorläufig auf dim 1/2: Inf reißt das Aufwandskriterium
  (×1,61), 1000 hält knapp (×1,47).
- `codex/reports/Manifest_WP_N36_before.toml` untracked: archivieren oder löschen?

## 3. Nächste Schritte (Claude)

1. Nach den Toren: Manifeste für Stufe 3 bzw. B-03.
2. Arbeitspakete: B-02/B-03-Auswertungsskript nach §9.6, ODEFormer auf Rausch-Daten (R-09), PySR (R-10).
3. Statusseite „EvoODE auf Orion“ nach jedem Statuswechsel neu veröffentlichen.
4. Wenn C-3 fertig ist: endgültige Phase-C-Auswertung (P-02).

## 4. Git

GitHub und GitLab stehen auf `5dd1df8`. Lokal liegen darüber nur Doku- und Spec-Commits.

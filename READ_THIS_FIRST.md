# READ_THIS_FIRST.md — Sitzungsübergabe

**Was dieses Dokument ist:** der flüchtige Zustand *zwischen* zwei Chat-Sitzungen — was gerade läuft,
was uncommittet im Working Tree liegt, welche Entscheidung als Nächstes ansteht. Nichts weiter.

**Was es ausdrücklich nicht ist:** ein Planungs- oder Statusdokument. `CLAUDE.md` verbietet ein
zweites davon. Alles Dauerhafte gehört dorthin, nach `PAPER_1.md` oder ins `DIARY.md` —
**nicht hierher.**

**Regeln:** wird immer **vollständig überschrieben**, nie angehängt. Was älter als ein paar Tage
ist, ist vermutlich falsch — dann gilt `CLAUDE.md`.

**Stand: 2026-10-02, ~01:45.** Arbeitsreihenfolge: Backlog in `CLAUDE.md` („Backlog Paper 1“).

**Feste Regeln seit dieser Nacht:** Claude pusht **nie** nach GitLab und nach GitHub nur mit
ausdrücklicher Erlaubnis, beides macht der Nutzer. **Keine harten Zeit-Cuts** (kein `timeout`, kein
`activeDeadlineSeconds`). Stattdessen gibt es eine erwartete Laufzeit, und wird sie deutlich
überschritten, wird diskutiert. `codex exec` wird immer mit `< /dev/null` gestartet.

---

## 1. Was läuft

| Lauf | Wo | Image | Stand | Anmerkung |
|---|---|---|---|---|
| C-3 | Orion | `221a3a7` | 177/180 | 3 Lorenz-Nachzügler, Ende ~2.–5.10. |
| WP-T1f | Orion | `1db1193` | 28/36 | Deadline entfernt (01.10.). 58 IC1 läuft langsam, das kann Tage dauern |
| B-02 (Grenzen-Orakel dim 1/2) | Orion | `5dd1df8` | fast fertig | 3 Jobs × 18 Shards, viel schneller als die Obergrenze |
| Stufe 2, gekappt (System 18, 24) | Orion | `5dd1df8` | 4 Zellen gestartet 02.10. ~01:30 | Smoke bitgleich zur lokalen Zelle. Erwartet: Stunden je Zelle |
| Ungekappt unter Rauschen, System 1 und 17 | Laptop | lokal | 1 von 4 fertig | R-05b |

Das schlanke Image `5dd1df8` (WP-N36: 202 statt 443 Pakete, bitgleich) baut in **13 min** statt bis zu ~3 h.

## 2. Nächste Schritte (Claude)

1. Lokale Zellen ohne Kappe fertig rechnen, saubere Auswertung, Tor-Bericht.
2. **Manifest für die ungekappten Zellen von System 18 und 24** auf Orion (R-05b), dann `apply` durch den Nutzer.
3. **B-02 einsammeln und auswerten** (Tor B2, Stabilitätskriterien §9.6 auf dim 1/2), danach B-04 (Suche 1 und 24, lokal).
4. Arbeitspakete schreiben: ODEFormer auf den Rausch-Daten (R-09), PySR (R-10).
5. Wenn C-3 fertig ist: endgültige Phase-C-Auswertung mit der neuen Aggregation (P-02).

## 3. Wartet auf den Nutzer

- Tor S2, sobald System 18 und 24 (gekappt und ungekappt) fertig sind.
- Pushes, wenn Claude sie als fällig meldet. Lokal sind derzeit nur Doku- und Spec-Commits, sie brauchen kein Image.

## 4. Befunde dieser Nacht (alle im DIARY 01./02.10.)

- **S-04:** Die Kappe schneidet unter Rauschen in 17 % der Gleichungen wahre Terme ab, schon bei σ = 0,01.
  Deshalb gibt es den Vergleichsarm ohne Kappe (§9.4b).
- **Weak-SINDy** ist auf System 1 unter Rauschen stark. Auf System 17 liegt EvoGrow vorn.
- **Abbruchkriterium:** Ein Stopp am Rauschboden hätte überall Level gespart. Design-Notiz: `docs/design_stopping_criterion.md`.

## 5. Git

GitHub und GitLab stehen auf `5dd1df8`. Lokal liegen darüber nur Doku- und Spec-Commits.

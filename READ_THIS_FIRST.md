# READ_THIS_FIRST.md — Sitzungsübergabe

**Was dieses Dokument ist:** der flüchtige Zustand *zwischen* zwei Chat-Sitzungen — was gerade läuft,
was uncommittet im Working Tree liegt, welche Entscheidung als Nächstes ansteht. Nichts weiter.

**Was es ausdrücklich nicht ist:** ein Planungs- oder Statusdokument. `CLAUDE.md` verbietet ein
zweites davon. Alles Dauerhafte gehört dorthin, nach `PAPER_1.md` oder ins `DIARY.md` —
**nicht hierher.**

**Regeln:** wird immer **vollständig überschrieben**, nie angehängt. Was älter als ein paar Tage
ist, ist vermutlich falsch — dann gilt `CLAUDE.md`.

**Stand: 2026-10-01, spät.** Push und `oc apply` macht der Nutzer. Die Reihenfolge der Arbeit steht
im Backlog in `CLAUDE.md` („Backlog Paper 1“). Laufort: unter 1 h auf dem Laptop, unter 24 h auf
Orion, darüber nur auf ausdrückliche Entscheidung.

---

## 1. Was läuft

| Lauf | Wo | Stand | Anmerkung |
|---|---|---|---|
| C-3 | Orion, `221a3a7` | 177 / 180 | 897 (Level 28), 899 (29), 905 (28); Ende ~2.–5.10. |
| WP-T1f | Orion, `1db1193` | 28 / 36 | **58 IC1 steht fast still (30/185)** → erreicht die Deadline 12.10. voraussichtlich nicht; die Zeilen bleiben erhalten. 61 ×2 wartet |

Statusseite „EvoODE auf Orion“: https://claude.ai/artifact/4sq6HhRsnxgrFVqVF2trBx (Version 21).

## 2. Seit heute Abend erledigt (alles committet, nicht gepusht)

WP-N32 (Datenbedingung, `clamp_val`), WP-N33a/a2/a3 (Auswertung gegen die saubere Wahrheit,
Tor-Bericht, CSV-Fix), WP-N33b (Orion-Manifeste, **nicht gestartet**), WP-N34/N34b (SINDy und
Weak-SINDy auf Rausch-Daten). Stufe 0 und B-01 sind bestanden, Stufe 1 ist gelaufen. Alle Zahlen
stehen im DIARY vom 01.10.

## 3. Wartet auf den Nutzer

1. **Tor S1:** Startet Stufe 2? Vorschlag: 17 und 24 auf dem Laptop, 18 per
   `k8s/phase_c_robustness_stage2_system18_job.yaml`.
2. **Push auf GitLab** (Commit ≥ `49b0613`). Erst danach baut die CI das Image, das Stufe 2 / System
   18 und B-02 (`k8s/phase_c_c8_oracle_b02_job.yaml`, Obergrenze ~74 h über drei Grenzen) brauchen.
   B-02 hat vorab kein Tor. Es kann starten, sobald das Image da ist und die Eingabe auf dem NFS
   liegt (`SCRIPTS.md`).
3. **WP-T1f 58 IC1:** Teildaten hinnehmen, oder etwas anderes?
4. **Track S (Abbruchkriterium):** S-02 (Struktur je Level in den Heartbeat, verhaltensneutral)
   freigeben?

## 4. Was auf den Tisch muss

**Weak-SINDy ist auf System 1 unter Rauschen der stärkste Gegner.** Bei (0,05; 0,5) trifft es in 5
von 10 Konfigurationen die Struktur, EvoGrow nicht. Die Generalisierung ist bei beiden gut. Gegen
normales SINDy trägt die Robustheits-These, gegen Weak-SINDy auf diesem System nicht. Ein System
entscheidet nichts, aber Stufe 2 muss genau das klären.

## 5. Git

Gepusht bis `1db1193`. Lokal sind alle Commits seit `14dc9b5`, zuletzt die WP-N32- bis
WP-N34b-Arbeit vom 01.10.

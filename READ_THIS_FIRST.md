# READ_THIS_FIRST.md — Sitzungsübergabe

**Was dieses Dokument ist:** der flüchtige Zustand *zwischen* zwei Chat-Sitzungen — was gerade läuft,
was uncommittet im Working Tree liegt, welche Entscheidung als Nächstes ansteht. Nichts weiter.

**Was es ausdrücklich nicht ist:** ein Planungs- oder Statusdokument. `CLAUDE.md` verbietet ein
zweites davon. Alles Dauerhafte gehört dorthin, nach `PAPER_1.md` oder ins `DIARY.md` —
**nicht hierher.**

**Regeln:** wird immer **vollständig überschrieben**, nie angehängt. Was älter als ein paar Tage
ist, ist vermutlich falsch — dann gilt `CLAUDE.md`.

**Stand: 2026-09-28, nachmittags.** Push und `oc apply` macht der Nutzer.

---

## 1. Was läuft

| Lauf | Wo | Stand 28.09. | Anmerkung |
|---|---|---|---|
| C-1/C-2 | Orion, `221a3a7` | 755 / 756 | Zelle 474 (System 40, ungecappt), Level 28/30 |
| C-3 | Orion, `221a3a7` | 175 / 180 | 5 × Lorenz 55/56 `pretune_on`, Level 26–27/30, ~20–25 h/Level → Ende ~1./2.10. |
| WP-T1d | Orion, `5a87efb` | **fertig 36/36, eingesammelt** | lokal `outputs/wp_t1d_neighbourhood/orion_5a87efb/` |
| ODEFormer-Kandidat | Orion, `8e0e699` | **fertig 126/126**, nicht eingesammelt | `--collect` für `…/candidate`, Befehl in `SCRIPTS.md` |

Status lesen ohne eigenen Pod: `oc exec` in einen laufenden Kampagnen-Pod, NFS unter `/outputs`.

## 2. Offene Entscheidung (Nutzer)

**WP-T1f zurückhalten oder starten?** Vorschlag Claude: bis zum Statusgespräch nach dem Ende von
C-3 (~1./2.10.) zurückhalten, damit der Cluster dann leer ist und der Kappungsbefund (DIARY 28.09.)
vorher besprochen wird. Er berührt: dim-3-Auswertung von Phase C (erreichbar 52/61 vs. unerreichbar
54–59), ob der C-5-Orakel-Arm mit Kappung läuft, Claim D, die Deutung des „dim-3-Kollapses“.
**C-5 nicht vor diesem Gespräch starten.**

## 3. WP-T1f — bereit, nicht gestartet

Committet `9941d7e` (Specs `16cad92`, `d765608` u. a.). Ohne Kappung, warmer Start, geteilte
Kontrolle, Deadline 14 Tage. Lokal geprüft: alle Tests, Self-Test, `--control-only` (36/36 ≤ 2e-20),
Smoke. Start-Ablauf: Push → Image-Build abwarten → Bootstrap → Smoke → Kampagne
(`SCRIPTS.md`, Abschnitt WP-T1f).

## 4. CI

`build_campaign_image` für `8e0e699` scheiterte beim **Push** (`write: broken pipe` mitten im
Upload), nicht beim Build. Vermutlich eine Netzwerkstörung; der nächste Push ist der Test. Tritt es
wieder auf: Limit oder Timeout auf der Registry-Seite, Admin fragen.

## 5. Offen, nicht dringend

- `analysis/configs/paper1_phaseC_v1.json` zeigt noch auf die Probe `outputs/phase_c_dryrun_2026-09-25/`;
  nach dem Ende von C-1/C-2/C-3 auf die vollständige Registry umstellen (ohne `--allow-incomplete`).

## 6. Git

Working Tree sauber bis auf diese Datei und `DIARY.md`. Lokal committet, **nicht gepusht** seit
`8e0e699`.

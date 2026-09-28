# READ_THIS_FIRST.md — Sitzungsübergabe

**Was dieses Dokument ist:** der flüchtige Zustand *zwischen* zwei Chat-Sitzungen — was gerade läuft,
was uncommittet im Working Tree liegt, welche Entscheidung als Nächstes ansteht. Nichts weiter.

**Was es ausdrücklich nicht ist:** ein Planungs- oder Statusdokument. `CLAUDE.md` verbietet ein
zweites davon. Alles Dauerhafte gehört dorthin, nach `PAPER_1.md` oder ins `DIARY.md` —
**nicht hierher.**

**Regeln:** wird immer **vollständig überschrieben**, nie angehängt. Was älter als ein paar Tage
ist, ist vermutlich falsch — dann gilt `CLAUDE.md`.

**Stand: 2026-09-28, nachmittags.** Push und `oc apply` macht der Nutzer — **Ausnahme 28.09.
(Nutzer unterwegs):** Claude darf WP-T1f selbst starten: Push (erledigt, `1db1193`), Bootstrap,
Smoke und, nur wenn der Smoke sauber ist, die Kampagne. Die Freigabe gilt nur dafür.

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

**WP-T1f startet sofort** (Entscheidung Nutzer 28.09.). Statusgespräch nach dem Ende von C-3
(~1./2.10.), der Kappungsbefund (DIARY 28.09.) steht darin oben. Er berührt: dim-3-Auswertung von Phase C (erreichbar 52/61 vs. unerreichbar
54–59), ob der C-5-Orakel-Arm mit Kappung läuft, Claim D, die Deutung des „dim-3-Kollapses“.
**C-5 nicht vor diesem Gespräch starten.**

## 3. WP-T1f — läuft auf Orion seit 28.09. nachmittags

Image `1db1193`, Job `evoode-wp-t1f-indexed-campaign`, 36 Zellen, `parallelism: 6`, Deadline
14 Tage. Ausgabe `/outputs/wp_t1f_campaign_1db11932c4335e480d374c7de1be35593b62b447/cell_*`.
Orion-Smoke sauber (DIARY 28.09.), lokal unter `outputs/wp_t1f_warm_neighbourhood/orion_smoke_1db1193/`.
Erwartet 4–6 Tage; dim-3-Zellen kommen zuletzt (Indexreihenfolge aufsteigend).
Nach dem Ende: einsammeln (tar über `oc exec`), dann `--aggregate-only --input-dir <lokaler Ordner>`.

## 4. CI

`build_campaign_image` für `8e0e699` scheiterte beim **Push** (`write: broken pipe` mitten im
Upload), nicht beim Build. Vermutlich eine Netzwerkstörung; der nächste Push ist der Test. Tritt es
wieder auf: Limit oder Timeout auf der Registry-Seite, Admin fragen.

## 5. Offen, nicht dringend

- **CLAUDE.md eindampfen** (983 Zeilen, Anspruch „kept short“): beim Statusgespräch nach Phase C,
  zusammen mit dem Claim-Tracing-Audit. Am 28.09. nur die nachweislich falschen Aussagen korrigiert.
- Nutzer: `.pytest_tmp*`, `.pytest_cache` sowie die pytest-Reste in `.tmp/` und `.codex_tmp/`
  löschen (Claude fehlt das Recht dazu).

- `analysis/configs/paper1_phaseC_v1.json` zeigt noch auf die Probe `outputs/phase_c_dryrun_2026-09-25/`;
  nach dem Ende von C-1/C-2/C-3 auf die vollständige Registry umstellen (ohne `--allow-incomplete`).

## 6. Git

Gepusht bis `1db1193` (beide Remotes). Danach nur lokale Doku-Commits.

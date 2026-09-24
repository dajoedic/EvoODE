# READ_THIS_FIRST.md — Sitzungsübergabe

**Was dieses Dokument ist:** der flüchtige Zustand *zwischen* zwei Chat-Sitzungen — was gerade läuft,
was uncommittet im Working Tree liegt, welche Entscheidung als Nächstes ansteht. Nichts weiter.

**Was es ausdrücklich nicht ist:** ein Planungs- oder Statusdokument. `CLAUDE.md` verbietet ein
zweites davon. Alles Dauerhafte gehört dorthin, nach `PAPER_1.md` oder ins `DIARY.md` —
**nicht hierher.**

**Regeln:** wird immer **vollständig überschrieben**, nie angehängt. Was älter als ein paar Tage
ist, ist vermutlich falsch — dann gilt `CLAUDE.md`.

**Stand: 2026-09-24, 10:15.** Bewusste Pause — nichts ansteht, was nicht auf laufende Rechnungen wartet.

---

## 1. Was gerade läuft

| Lauf | Wo | Stand 24.09. 10:00 | Anmerkung |
|---|---|---|---|
| C-1/C-2 | Orion, `221a3a7` | 313 / 756, 64 aktiv, 0 Fehler | letzte 15 dim-3-Zellen laufen, dann dim 4 und dim 1 |
| C-3 | Orion, `221a3a7` | 172 / 180, 8 aktiv, 0 Fehler | letzte 8 sind dim 3 inkl. Lorenz |
| WP-T1d | Orion, `5a87efb` | 24 / 36, **8 aktiv** | `parallelism` am 24.09. 09:59 von 2 auf 8 (Nutzer), keine Deadline; Rest ~15–20 h geschätzt |
| ODEFormer-Neuberechnung (WP-N23) | Laptop, 4 Docker-Shards | Referenz 107/504, dann Kandidat | Ausgabe `analysis/data/paper1_phaseC_v1/odeformer_baseline/{reference,candidate}_wp_n23/` |

```powershell
oc get jobs -o custom-columns="NAME:.metadata.name,PAR:.spec.parallelism,SUCC:.status.succeeded,ACTIVE:.status.active,FAILED:.status.failed"
```

Records Phase C: `S:/BigDataOrion/data-science/joedicke/phase_c_campaign_221a3a7…/tasks/`; WP-T1d:
`wp_t1e_campaign_5a87efb…/cell_*/neighbour_rows.csv`. Statusseite (Version 9):
https://claude.ai/artifact/4sq6HhRsnxgrFVqVF2trBx — führt **alle** Läufe, bei Statuswechsel neu veröffentlichen.

**Wenn die ODEFormer-Neuberechnung fertig ist:** (a) R² und Ausdrücke gegen die ersten Raster
(`reference/`, `candidate/`) vergleichen — müssen bitgleich sein, das ist der Determinismus-Beleg
über 1.008 Zellen; (b) Ausgänge der Vorhersagen auszählen (`*_prediction_outcome`); (c) bei
Gleichheit die alten Ordner durch die `_wp_n23`-Ordner ersetzen, committen, DIARY.

## 2. Wer was macht

Claude liest die Freigabe, fragt `oc` ab, prüft, wertet aus, committet, schreibt DIARY und hält
die Statusseite aktuell. **Beim Nutzer:** HPC-Jobs starten oder ändern (`oc apply`, `oc patch`),
GitLab-Logs ansehen (`glab` fehlt), pushen.

## 3. Heute entschieden (alles im DIARY vom 2026-09-23)

1. **WP-T1d-Deadline entfernt**, bewusste Ausnahme von der 8-h-Regel. Die 86.400 s kamen aus einer
   zu optimistischen dim-3-Schätzung; das „Ende gegen 06:00" war derselbe Fehler.
2. **Rauschen zurückgestellt**, bis Phase C den Nutzen auf rauschfreien Daten zeigt. ODEBench liefert
   rauschfreie Daten; Rauschen ist Teil des ODEFormer-Evaluationsprotokolls.
3. **Prädiktives Kriterium für Kappen-Versagen:** eigene tiefere Analyse **nach** der
   Phase-C-Auswertung. Der Nutzer findet es spannend.
4. **`docker:29-dind` per Digest gepinnt** (`e4f8d38`, `CHANGELOG.md`). Wird erst beim nächsten Push
   gebaut — falls der Harbor-Cache den Digest-Pull ablehnt, scheitert der Bau am Service-Start.
5. **Namespace-Umzug nach Ende aller Läufe**, mit eigenen Image-Regeln. **Die Images ziehen mit** —
   der Nutzer muss das beim Umzugsauftrag ausdrücklich sagen. Priorität in `CLAUDE.md` (Open, not
   scheduled): unbedingt `221a3a7`, `91f88c4`; behalten `5a87efb`, `ec3b6bd`; kann weg `f6143eb`,
   `88eaeb6`. Keine Aufräumregel im alten Projekt.

## 4. Was als Nächstes ansteht — der Reihe nach, keine neuen Themen

1. **ODEFormer-Neuberechnung prüfen** (siehe §1).
2. **WP-T1d vollständig** → neuen Maßstab entscheiden (Orakelstart + symmetrischer Mehrfachstart;
   Vorschlag im DIARY vom 23.09., Zwischenblick). Wartet auf Zustimmung des Nutzers.
3. **Kampagne fertig** → Phase-C-Auswertung → gepaarter Vergleich EvoGrow / SINDy / ODEFormer
   (Claim D) → prädiktives Kappen-Kriterium → Namespace-Umzug samt Image-Härtung.

Zurückgestellt, bewusst: Rauschen (bis Phase C trägt). Vorgemerkt: WP-T2a (hängt an WP-T1d).

## 5. Git

Alles committet, **nichts gepusht**. Ein Push baut das Kampagnen-Image neu (Digest-Pin testet sich
dabei zum ersten Mal); laufende Jobs hängen an festen SHAs.

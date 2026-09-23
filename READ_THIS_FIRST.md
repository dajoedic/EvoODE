# READ_THIS_FIRST.md — Sitzungsübergabe

**Was dieses Dokument ist:** der flüchtige Zustand *zwischen* zwei Chat-Sitzungen — was gerade läuft,
was uncommittet im Working Tree liegt, welche Entscheidung als Nächstes ansteht. Nichts weiter.

**Was es ausdrücklich nicht ist:** ein Planungs- oder Statusdokument. `CLAUDE.md` verbietet ein
zweites davon. Alles Dauerhafte gehört dorthin, nach `PAPER_1.md` oder ins `DIARY.md` —
**nicht hierher.**

**Regeln:** wird immer **vollständig überschrieben**, nie angehängt. Was älter als ein paar Tage
ist, ist vermutlich falsch — dann gilt `CLAUDE.md`.

**Stand: 2026-09-23, 11:30.**

---

## 1. Was gerade läuft — drei Jobs auf Orion, 0 Fehler, 0 Neustarts

| Job | Stand | Image | Deadline |
|---|---|---|---|
| `evoode-phase-c-c1-c2-campaign` | **258 / 756**, 64 aktiv, 5.599 Kernstunden | `221a3a7` | keine (vor der 8-h-Regel gestartet) |
| `evoode-phase-c-c3-campaign` | **172 / 180**, 8 aktiv (alle dim 3, inkl. Lorenz), 1.205 Kernstunden | `221a3a7` | keine |
| `evoode-wp-t1e-indexed-campaign` (WP-T1d) | **22 / 36**, 2 aktiv (System 54), 14 dim-3-Zellen offen | `5a87efb` | **am 23.09. entfernt** |

Integrität C-1–C-3: 430 Records, alle `error = None`, ein Identitätstripel
(`221a3a7` sauber / `0c9672de35c75a9d` / `ffb0266c7913352c`). Capped und uncapped exakt gleich weit.
Heartbeats älter als 6 h bei 22 Zellen sind **kein Hängen** — ein Heartbeat pro Level, ein
Lorenz-Level dauerte in Phase B ~10 h. Offen in C-1/C-2: 26 dim 3 (alle laufen), Rest dim 2,
alle 24 dim 4 und alle 276 dim 1 (billig). Kein Enddatum nennen.

Prüfen:

```powershell
oc get jobs -o custom-columns="NAME:.metadata.name,COMPL:.spec.completions,SUCC:.status.succeeded,ACTIVE:.status.active,FAILED:.status.failed,DEADLINE:.spec.activeDeadlineSeconds"
```

Records: Phase C unter `S:\BigDataOrion\data-science\joedicke\phase_c_campaign_221a3a7…\tasks\`
(`cell_NNNNNN.jsonl` + `.heartbeat.jsonl`, `manifest.csv` eine Ebene höher). WP-T1d unter
`wp_t1e_campaign_5a87efb…\cell_NNN_system_XXXX_icN\neighbour_rows.{csv,jsonl}`.

**Online-Statusseite:** https://claude.ai/artifact/4sq6HhRsnxgrFVqVF2trBx („EvoODE auf Orion",
Version 5). Führt **seit heute alle Läufe** samt Image, nicht nur Phase C — bei jedem
Statuswechsel neu veröffentlichen, gleiche URL.

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

## 4. Was als Nächstes ansteht

- **Warten.** Bei Abschluss von WP-T1d: auswerten (Klasse `swap_one` bei gleicher Größe ist die
  entscheidende; `add_one` zu gewinnen ist Verschachtelung) → danach **WP-T2a** festlegen.
- Wenn dim 1 in C-1/C-2 gerechnet ist: Claim-B-Paartabelle neu ziehen (129 Paare fertig, Stand heute).
- Nach Kampagnenende: Phase-C-Auswertung → Claim D → Kappen-Kriterium → Umzug.
- **Trivy geklärt, bleibt rot bis nach der Kampagne:** 109 Befunde in Julia-Binärpaketen (v. a. `Plots`/`CairoMakie` in `Project.toml`), 72 Debian (5 behebbar), torch im Baseline-Nachbau. Ausnahme E6 im `CHANGELOG.md`; Härtung kommt mit dem Namespace-Umzug (`CLAUDE.md`). Der nächste Push ändert an den roten Jobs nichts.
- **ODEFormer-Arbeitspaket:** Abnahme muss den torch/sympy-Konflikt lösen (Phase-C-Plan, Abschnitt zum Baseline-Image).

## 5. Git

Heute committet, **nichts gepusht**: `af40dc6`, `2d5b0b5`/`b833d6b`, `689eff3`, `7b6161f`/`095609c`,
`5a9d724`/`1d35aeb`, `e4f8d38`, `383273b`, `776d4a5`, plus der Commit mit dieser Datei. Der Push löst
einen Image-Neubau aus (~35 min); die laufenden Jobs hängen an festen SHAs und sind unberührt.

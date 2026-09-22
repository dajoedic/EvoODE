# READ_THIS_FIRST.md — Sitzungsübergabe

**Was dieses Dokument ist:** der flüchtige Zustand *zwischen* zwei Chat-Sitzungen — was gerade läuft,
was uncommittet im Working Tree liegt, welche Entscheidung als Nächstes ansteht. Nichts weiter.

**Was es ausdrücklich nicht ist:** ein Planungs- oder Statusdokument. `CLAUDE.md` verbietet ein
zweites davon. Alles Dauerhafte gehört dorthin, nach `PAPER_1.md` oder ins `DIARY.md` —
**nicht hierher.**

**Regeln:** wird immer **vollständig überschrieben**, nie angehängt. Was älter als ein paar Tage
ist, ist vermutlich falsch — dann gilt `CLAUDE.md`.

**Stand: 2026-09-22, nachmittags.**

---

## 1. Das Wichtigste zuerst

**Uncommittet im Working Tree liegt WP-T1b, und es ist NICHT geprüft.** Codex meldet `done`, aber
keine Zahl daraus gilt, bevor sie nachgerechnet ist. Das ist die offene Aufgabe der nächsten
Sitzung.

Die Phase-C-Kampagne läuft unverändert auf Orion weiter. **Es steht keine Entscheidung offen, die
den Lauf betrifft.** Nichts, was heute passiert ist, hat den Kampagnenpfad berührt.

---

## 2. Was uncommittet im Baum liegt

```
 M analysis/exploratory/term_relevance/term_relevance.py
 M codex/CURRENT_TASK.md          (WP-T1b-Spec)
 M codex/STATUS.md                (Codex meldet done)
?? analysis/scripts/aggregate/run_wp_t1b_standalone_ranking.py
?? analysis/tests/test_wp_t1b_standalone_ranking.py
?? codex/reports/REPORT_WP_T1b.md
```

Dazu die Ausgaben unter `analysis/data/wp_t1b_standalone_ranking/` und
`analysis/figures/wp_t1b_standalone_ranking/` (gitignoriert, Tracking-Entscheidung wie bei WP-T1:
Aggregate ja, Rohsätze nein).

## 3. Die Prüfliste für WP-T1b, bevor irgendetwas committet wird

Beim ersten Anlauf war der Teilstand nicht deterministisch — genau dort also hinsehen:

1. `cd analysis && python -m pytest tests/test_wp_t1b_standalone_ranking.py tests/test_wp_t1_term_relevance.py -q`
   — beide müssen grün sein.
2. **Die WP-T1-Regression:** ein erneuter WP-T1-Lauf muss `gate_decision.json` und
   `aggregate_by_configuration_dimension.csv` **bitidentisch** reproduzieren. Die Spec verlangt,
   dass die Intercept-Reparatur als Option mit altem Vorgabewert gebaut ist. Prüfen, nicht glauben.
3. **Die Integrationsschranke:** die Spec verbietet den vollen Lauf über 40.000 Integrationen und
   verlangt eine Hochrechnung aus einem Smoke-Test. Erwartet waren ~21.600. Steht die tatsächliche
   Zahl in `cost.csv`, und liegt sie darunter?
4. **Kein Ground-Truth-Leck** in der Selektion — bei WP-T1 war das sauber (`rank_forward` sieht
   keinen Truth), bei den neuen Betriebspunkten neu prüfen. `oracle_size` darf den Truth sehen,
   `bic` nicht.
5. Gegen die vorab festgelegte Latte lesen: SINDy auf denselben Trajektorien, exakte Systeme,
   bestes von zehn Konfigurationen — **dim 2: 66,7 % Strukturtreffer, dim 3: 28,6 %.**
   Deutung A/B/C steht in `codex/CURRENT_TASK.md`, nicht nachträglich ändern.

Danach committen wie bei WP-T1: Implementierung getrennt von den getrackten Ausgaben, nie
`git add -A` (Codex arbeitet nebenher).

## 4. Was heute committet wurde

| Commit | Inhalt |
|---|---|
| `700a685` / `2eb54e6` | DIARY: Umhängung des Seitenzweigs — Ziel ist Strukturtreffer auf gekoppelten Systemen, nicht Compute |
| `ae7573d` | WP-T1: trajektorien-abgeleitete Term-Relevanz, isolierte Machbarkeitsstudie |
| `b4498f6` | WP-T1-Ausgaben getrackt, 11-MB-Rohsätze draußen |
| `139dd89` | Paper-Bogen umgebaut, `PAPER_TIMELINE.md` eingearbeitet und entfernt, zwei CLAUDE.md-Stellen nachgezogen |
| `32c7989` / `401e07f` | DIARY: die vier Bogen-Entscheidungen und die beibehaltene Grenzen-Rahmung |

**Das Kampagnen-Image ist SHA-gepinnt — verifiziert am 2026-09-22 auf dem Cluster.** Beide
Phase-C-Jobs laufen unter `evoode:221a3a72f0cb43164a22b09baac2d9ae82681a02` — Commit `221a3a7` vom
14.09., Vorfahr von `main` — mit `imagePullPolicy: IfNotPresent`.

**Ein GitLab-Push kann die laufende Kampagne deshalb nicht verändern.** Der Push erzeugt einen neuen
SHA-Tag und verschiebt `:main`; beide sind verschieden vom gepinnten Tag, und die CI hat gar keinen
Deploy-Schritt — `.gitlab-ci.yml` kennt nur die Stages `build` und `security`, ohne `oc`, `kubectl`,
`apply` oder `helm`.

**Wichtig für das nächste Mal:** aus den Vorlagen unter `k8s/` lässt sich das **nicht** schließen,
die tragen nur den Platzhalter `<COMMIT_SHA>`, und die erzeugten Manifeste sind gitignoriert. Der
Prüfbefehl steht in `docs/hpc_deployment_guide.md` §6b. Stünde dort `:main`, wäre ein Push während
eines Indexed Job mit `completions: 756` fatal: jeder danach erzeugte Pod rechnete mit anderem Code,
und die Kampagne trüge zwei Git-Hashes in ihren Records.

**Trotzdem kein GitLab-Push, solange nichts ihn braucht.** Nicht aus Sicherheitsgründen — die sind
oben geklärt —, sondern weil der Build drei Stunden CI kostet und bisher zwecklos wäre. Gebraucht
wird er erst, wenn eine Cluster-Rechnung neuen Code braucht. GitHub-Push wie immer durch den Nutzer.

## 5. WP-T1 — geprüft und gültig

Gate **positiv**, von mir nachgerechnet: Median `n_false_before_last_true` = **0,0**, 37/44
Gleichungen ≤ 3, Replikation auf IC2 hält. Entscheidungszelle weak × forward, σ=0, IC1, dim 2+3.

**Zwei Befunde, die im Codex-Report fehlen und in `docs/phd_thesis_arc.md` §5 stehen:**

- Alle p-Werte sitzen am **Auflösungsboden** von 18 Clustern (2^18 Vorzeichenwechsel, Minimum
  3,8e-06). Nicht mit zwölf Stellen zitieren.
- **„weak schlägt fd" ist nicht haltbar.** Auf den 39 Gleichungen ohne Konstante im Support sind
  beide bei σ=0 identisch (0,872). Die Lücke kommt aus einem Zentrierungsdefekt, der die Konstante
  im `fd`-Arm unauffindbar macht — den repariert WP-T1b.

## 6. Offene Entscheidungen, keine davon dringend

1. **Der Rauschzuschnitt von Paper 1** — der größte unbudgetierte Posten des Projekts. Robustheit
   ist heute in Paper 1 gefaltet worden, aber die Phase-C-Kampagne hat keine Rauschachse, es gibt
   keine Rausch-Infrastruktur im Julia-Suchpfad, und Phase C kostet bereits ~12.300–15.900
   Kernstunden. Entweder reduzierter Rauscharm auf benannter Teilmenge oder deklarierte
   Zukunftsarbeit. `docs/phd_thesis_arc.md` §3 und §11.
2. **Das prädiktive Kriterium für Kappen-Versagen hat keinen Besitzer mehr** unter dem
   Claim-A–D-Zuschnitt. Benannt, nicht entschieden.
3. **Was WP-T2a wird**, hängt an WP-T1bs Ausgang A/B/C. Nicht vorher festlegen.

## 7. Zwei betriebliche Dinge

- **Ein Branch wurde geprüft und verworfen** (Historie ist vollständig linear, Pfade sind disjunkt,
  ein nicht gemergter Zweig läge außerhalb des Claim-Tracing-Audits). Begründung im DIARY-Eintrag
  `700a685`. Bei **WP-T2a** neu bewerten — der greift in `src/structure/evogrow.jl` ein.
- **`PAPER_TIMELINE.md` nicht wieder anlegen.** Eingearbeitet in `docs/phd_thesis_arc.md`, das ist
  jetzt die Paper-Roadmap. Eine Sicherungskopie lag im Scratchpad dieser Sitzung und ist flüchtig.

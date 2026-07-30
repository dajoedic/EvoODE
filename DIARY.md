# EvoODE — Projekt-Tagebuch

Neueste Einträge zuerst. Aktueller Projektzustand: siehe `CLAUDE.md`.

---

## 2026-07-30

### WP-G2.1 geliefert — Zwei-Varianten-Runner, Einzelzell-Selektor, Do-or-Die-Readout

Gate-2-Vorbereitung: statt einer teuren 45-Lauf-Matrix ein sequenzieller, paarweiser v2.2-vs-v3-Vergleich mit **System 26 / Seed 42 als vorab festgelegter Do-or-Die-Zelle**. Der v2.2-Arm ist bereits eingefroren (Baseline v0, von WP-T2 bit-exakt reproduziert), also genuegt zum Entscheiden **ein** frischer v3-Lauf. Tests real gefahren (Baseline abgebrochen, keine CPU-Konkurrenz):

- **Runner auf zwei Varianten** (`evogrow_v2_2_stage_local`, `evogrow_v3`); Screening aus der Ausfuehrungsliste. `test_regression_runner_gate2.jl` 6/6.
- **Einzelzell-Selektor** ueber `EVO_REGRESSION_VARIANT/SYSTEM_ID/SEED` (leer = volle Matrix), plus `EVO_REGRESSION_HISTORY_PATH`-Override. `main()` nur noch unter `PROGRAM_FILE`-Guard, damit `include`-bar fuer Tests.
- **`BFGS_TIME_LIMIT_S` 86.400 → 1.800 s** (reine Notbremse; greift nie — WP-T1/T2). Aendert bewusst den `config_fingerprint`.
- **Fingerprint sauber:** Codex hat `FINGERPRINT_VARIANT_LABELS` (die alten drei Labels) eingefroren, sodass die Variantenreduktion den Fingerprint **nicht** bewegt. Verifiziert: aktuell `1f9c5f80…` vs. v0 `0c739d4e…`, Delta nur durch das Zeitlimit.
- **Do-or-Die-Readout** (`studies/gate2_do_or_die/readout.jl` → `outputs/studies/gate2_do_or_die/`): reines Post-Processing, stellt v3/26/42 gegen den eingefrorenen v2.2-Anker. Vorab festgelegtes Kriterium — PASS nur wenn (a) `eq_final_stages[1]==3` (du1 bleibt auf wahrer Stage, kein Overshoot), (b) du1-Support exakt `{u1,u1^2,u1*u2}`, (c) Loss ≤ 0.001391623174905009; sonst PARTIAL (nur a verletzt) bzw. FAIL. `test_gate2_do_or_die.jl` 9/9 (PASS/PARTIAL/FAIL).

Zwei kleine Unsauberkeiten der Lieferung, ohne Korrektheitsfehler: (1) Codex schrieb sechs ungefragte v2.2-Scalar-Records unter einem Zwischenstand-Fingerprint `d596e066` (den der finale Code nicht mehr erzeugt) in die echte History — per `git checkout -- history.jsonl` entfernt, da git-getrackt und einzige uncommittete Aenderung. (2) Der v3-Smoke lief nicht end-to-end ueber den Runner (nur der Selektor unit-getestet); Risiko gering, der echte 26/42-Lauf deckt es ab.

Naechster Schritt: der User startet den einen Lauf (`EVO_REGRESSION_VARIANT=evogrow_v3 EVO_REGRESSION_SYSTEM_ID=26 EVO_REGRESSION_SEED=42`), dann `readout.jl` → Gate-2-Vorentscheidung.

<!-- HASH_G2_1 -->

### WP-v3.5 geliefert — Pro-Gleichungs-Overshoot-Metriken + gekoppelter Integrations-Smoke

Codex hat die Pro-Gleichungs-Metriken umgesetzt und die Integrationsluecke geschlossen. Statisch geprueft (Julia nicht gestartet, Baseline v1 laeuft weiter):

- **Metrik-Funktionen (§8):** `eq_overshoot`/`eq_wasted_levels` in `src/structure/evogrow_v3_promote.jl` — rein abgeleitet, kein RNG, keine Integration; `eq_overshoot` klammert Untersteuerung, `eq_wasted_levels` zaehlt Level ueber `expected_stage`. Exportiert in `EvoODE.jl`.
- **Record-Aufnahme:** `run_regression.jl` zieht `eq_stage_histories` aus den Meta-Daten; `has_eq_stage_data`-Guard verlangt beide Felder (`eq_final_stages` + `eq_stage_histories`), sonst bleiben beide neuen Felder `nothing` — genau wie `eq_final_stages` bei Nicht-v3-Varianten.
- **Fingerprint unveraendert:** nur zwei Ausgabefelder plus deren Export; keine gehashte Hyperparameter-Konstante angefasst. Additiv am Record-Schema, das nicht in den Fingerprint eingeht.
- **Integrationsluecke geschlossen.** `test/smoke_evogrow_v3_coupled_divergence.jl` faehrt ein billiges synthetisches 2D-System end-to-end: `u1=exp(-0.5t)` (exakt `du1=-0.5·u1`, Stufe 1) vs. `u2=1/(1+t)` (`du2=-u2²`, Stufe 2). Gleichung 1 faellt unter `loss_tol` und promotet nie, Gleichung 2 steigt — `eq_final_stages` divergieren. Damit lief der divergente Pfad (v3.3 eq-aware Child-Generation + v3.4 Pro-Gleichungs-Promotion) **erstmals in einem echten gekoppelten Lauf**, bisher nur mit injizierten Stufen unit-getestet. Ein `FastDerivativeOptimizer` ersetzt BFGS (keine teuren ODE-Solves), umgeht aber den zu testenden Suchpfad nicht — Child-Generation und Promotion laufen durch echten EvoGrowV3-Code.
- **Tests:** `test/test_evogrow_v3_metrics.jl` (alle drei Spec-Faelle inkl. Aggregat-Konsistenz `maximum(eq_overshoot) == max(0, maximum(eq_final_stages) - expected_stage)`).

Such-Verhalten und globale Metriken (`stage_overshoot`/`wasted_levels`) unangetastet; die Pro-Gleichungs-Metriken verfeinern nur. Damit ist die v3-Kette bis zur Validierung komplett. Naechster Schritt: WP-v3.6 — externer Validierungslauf v3 vs. Baseline v1 (Overshoot-Rueckgang auf gekoppelten Systemen 26/31/63), nach Abschluss der laufenden Baseline.

<!-- 960b0e6 -->

## 2026-07-29

### WP-v3.4 geliefert — Pro-Gleichungs-Promotion scharf geschaltet

Codex hat die Pro-Gleichungs-Promotionsregel umgesetzt: `src/structure/evogrow_v3_promote.jl` (neu); `evogrow_v3.jl` ersetzt die Lockstep-Promotion durch pro-gleichungs `r_k`-Plateau plus globale Termination; der Bit-Identitaets-Smoke wurde durch einen Scalar-Promote-Smoke ersetzt (korrekt — v3.4 bricht die v2.2-Gleichheit bewusst). Statisch geprueft (Julia nicht gestartet, Baseline v1 laeuft):

- **Signal (§3):** `r_k` = Ableitungsresiduum auf der beobachteten Trajektorie; `estimate_derivatives` aus `pretune.jl` wiederverwendet, RHS pro Gleichung an beobachteten Zustaenden ausgewertet — keine Integration im Normalpfad, RNG-neutral (kein Einfluss auf den Such-Stream). Fallback auf Trajektorienresiduum mit lauf-globalem Flag.
- **Promotion (§4):** drei Bedingungen (Budget `max(min_levels_per_stage, plateau_window+1)`, `r_k`-Plateau, `r_k > loss_tol`) plus Maxstufen-Guard; mehrere Gleichungen koennen pro Level promoten. `eq_plateau_histories` traegt jetzt `r_k` statt `best.objective`.
- **Termination (§5):** vor der Promotion ausgewertet → globaler `loss_tol`-Stopp hat Vorrang; neue Erschoepfung „alle Gleichungen auf Maxstufe und plateaut"; `min_levels`-Guard erhalten.
- **Tests stark:** `test/test_evogrow_v3_promote.jl` deckt alle vier §4-Bedingungen deterministisch ab (Plateau / `r_k<tol` / Budget / Maxstufe) plus den `r_k`-Signal-Test (Konstanten-Basis, lineare Trajektorie → `r_1≈0`, `r_2=9`). `test/smoke_evogrow_v3_scalar_promote.jl` faehrt System 3+11 end-to-end ohne v2.2-Gleichheitsanspruch.
- EvoGrow/v2.2 und Child-Generation unangetastet; `promotion_log`-Formaenderung unkritisch (nur generische Serialisierung in `experiments/run_experiment.jl`).

**Bewusst kein No-Op:** das Plateau-Signal wechselt von `best.objective` auf `r_k`; das aendert das Verhalten auch auf skalaren Systemen. Bit-Identitaet war hier nicht das Kriterium, sondern deterministische Unit-Test-Logik.

Zwei kleine, nicht-blockierende Punkte fuer spaeter: `stage_level_count` ist jetzt toter Code (wird inkrementiert, nie gelesen); der Trajektorien-Fallback ist ungetestet (nur bei nicht-finiter FD aktiv). Naechster Schritt: WP-v3.5 (expected-stage-Metriken `eq_overshoot`/`eq_wasted_levels`), dann WP-v3.6 (Validierung gegen Baseline v1: Overshoot-Rueckgang auf 26/31/63, extern nach der laufenden Baseline).

<!-- a334256 -->

### WP-v3.3 geliefert — gleichungs-bewusste Child-Generation, unter Lockstep bit-identisch

Codex hat WP-v3.3 umgesetzt: `src/structure/evogrow_v3_childgen.jl` (neu), `evogrow_v3.jl` ruft im Level-Loop jetzt `_expand_equation_aware_with_usage_policy` statt `_expand_with_usage_policy`, `EvoODE.jl` bindet die neue Datei ein. Verifikation **statisch** geprueft (Julia nicht gestartet, um die parallel laufende Baseline v1 nicht um CPU zu bringen; Ausfuehrungs-Evidenz liefert Codex' eigener Testlauf):

- **Strukturelle Bit-Identitaet korrekt.** Bei uniformen `eq_stages` — dem Lockstep-Zustand — delegiert `_expand_equation_aware_with_usage_policy` an den unveraenderten `_expand_with_usage_policy` mit denselben `allowed_terms`/`current_stage_terms`: derselbe Code, dieselbe RNG-Reihenfolge. Der Pro-Gleichungs-Pfad wird nur bei divergierenden Stufen betreten und ist bis WP-v3.4 (Promotion) im echten Lauf tot.
- **Verfuegbarkeits-Praedikat korrekt.** `stage(t)` aus `term_groups`, `vars(t)` per Regex `u(\d+)` aus `basis_term_name`. Namensformat bestaetigt (`u1`, `u1^2`, `u1*u2`, `u1^3`, `sin(u1)`, `cos(u1)`) — nur echte Cross-Terme haben zwei Variablen, dort greift die Paarregel `min(eq_stages[v] for v in vars(t)) >= stage(t)`.
- **Tests stark.** `test/test_evogrow_v3_childgen.jl`: divergente Stufen `[1,3]` (Gleichung 1 nur Stage-1-Terme, `u1*u2` fuer keine Gleichung verfuegbar) und — der harte Teil — die Delegation bei `[3,3]` erzeugt byte-identische Kinder wie der Direktaufruf (gleicher Seed, Vergleich aller `active_idxs`). `test/smoke_evogrow_v3_bit_identity.jl`: EvoGrowV3 gegen EvoGrow(v2.2) end-to-end auf analytischer System-11-Trajektorie; bricht bei jeder Abweichung in loss/objective/final_stage/Struktur ab. Transitiv: WP-v3.2 hatte EvoGrowV3 ≡ v2.2 etabliert, dieser Smoke bestaetigt es nach v3.3, also v3.3 unveraendert.

Promotion (`_lockstep_stage_progression_decision`, `_apply_lockstep_stage_update!`), Metriken und `EvoGrow`/v2.2 unangetastet. `history.jsonl` bewusst nicht committet — die Baseline v1 schreibt dort gerade live. Naechster Schritt: WP-v3.4 (Pro-Gleichungs-Promotionsregel), die die Stufen erst divergieren laesst — regressionsgeprueft gegen Baseline v1.

<!-- f6261a0 -->

### WP-T2 gelaufen — Vorhersage bestaetigt, Overshoot algorithmisch, v3 validiert

Der externe System-26-Lauf ist durch (16,8 h Wall-Clock, Seed 42, 30 Level, drei Bedingungen D8/R8/R6). Ausgaben in `outputs/studies/numerics/system26_tolerance_screening/`. **Anker bit-exakt reproduziert:** R6 (1e-6) liefert `0.001391623174905009`, `final_stage = 5`, Overshoot 2, wasted 8, `pruned_match = false` — identisch zu Baseline v0 (`0c739d4e36ee6498`). Damit ist die Messung interpretierbar.

**Q2 — Toleranz aendert den Overshoot nicht (Vorhersage bestaetigt).** R6 (1e-6) und R8 (1e-8) haben bit-identisch `final_stage = 5`, `stage_overshoot = 2`, `wasted_levels = 8`. Die engere Toleranz senkt nur den Loss (1,39e-3 → 2,52e-4), nicht das Stopp-Verhalten. Beide terminieren via `plateau_absolute`, keiner naehert sich je `loss_tol = 1e-8` (haengt bei 1e-4 bzw. 1e-3). **Der Overshoot auf System 26 ist algorithmisch, nicht numerisch** — genau die geschaerfte Prognose vom 2026-07-23. Damit trennt die Messung sauber: auf System 3 numerisch (siehe 2026-07-22), auf gekoppelten Systemen algorithmisch. Die v3-Begruendung ist bestaetigt, nicht bedroht.

**Q3 — Screening auf gekoppeltem System: schnell, aber kein Discovery-Gewinn.** D8 (Screening) gegen R8 (Referenz), beide 1e-8:
- Deterministisch, tragend: D8 braucht **98.253 Integrationen gegen R8s 3.348.287** (34x weniger). Beide `pruned_match = false`, beide Overshoot 2. D8 nutzt 9 Terme (5+4), R8 nur 6 (4+2) — D8s niedrigerer Loss (1,01e-4 vs 2,52e-4) ist Ueberparametrisierung, kein Strukturgewinn.
- Ranking-Kollaps: `rank_agreement_spearman` Median **−0,014** (Mittel 0,12, Min −0,64, Max 0,998). Das FD-Ableitungs-Screening rankt Kandidaten auf dem gekoppelten System praktisch nicht wie der echte Loss. Der 34x-Vorteil kommt aus wenig-integrieren, nicht aus gutem Diskriminieren.
- Nested-F-Gate hier **inert**: `selection_diff_from_residual = 0` ueber alle Level. Der WP-P2.4-Durchbruchmechanismus aendert auf System 26 keine einzige Auswahl gegenueber purem Residual. Er half auf System 3, tut hier nichts — der Gate-Nutzen ist systemabhaengig.

Fazit: Screening ist eine Performance-Optimierung (mit `polish_start=reference` sicher), kein Discovery-Qualitaets-Hebel. Gehoert als optionale Beschleunigung dokumentiert, nicht in den Kern-Claim; der Ranking-Kollaps muss in die Discussion.

**Q4 — der v3-Beleg steckt in der Struktur.** Wahrheit: `du1 = 3·u1 − u1² − 2·u1·u2 | du2 = 2·u2 − u1·u2 − u2²`. R8 nach Pruning: `du1`-Support `{u1, u1², u1·u2}` = **exakt Gleichung 1** (`3.03·u1 − 1.07·u1² − 1.99·u1·u2`), aber `du2` = `{u1, u1²}` — **komplett falsch.** Eine Gleichung geloest, die andere im Blindflug; der globale Plateau-Mechanismus eskaliert Stages 4/5 fuer beide, obwohl Gleichung 1 laengst fertig ist. **Das ist die Signatur, die v3 (gleichungsweise Promotion) aufloest:** geloeste Gleichung einfrieren, nur die offene weiterwachsen. Robust (suspend-fest): 8 von 25 Leveln (R8) liegen jenseits der erwarteten Stage 3, das sind ~25 % der Integrationen (Stages 4+5: 832.350 von 3.348.287 Solves).

**Korrektur meiner eigenen „63 %"-Aussage.** Die 63 % Overshoot-Kosten waren die *Wall-Clock*-Sicht (Zeitanteil der Stages 4+5 bei R8). Nach deterministischer Integrationszaehlung sind es ~25 %. Die Differenz kommt daher, dass die spaeten Integrationen einzeln teurer sind (bei 1e-8 kostet ein Stage-5-Solve 35 ms) — das ist zum Teil eine echte numerische Eigenschaft, aber die Wall-Clock-Achse ist genau die vom Suspend kontaminierte. Load-bearing bleibt: 8 verschwendete Level, ~25 % der Integrationen, eine Gleichung exakt, die andere blind.

**Nebenbefund Toleranz.** 1e-8 senkt den Loss, aendert aber kein Stopp-Verhalten auf plateauenden Systemen und verteuert ausgerechnet die verschwendeten Spaeten-Stages. Fuer den Suchpfad auf gekoppelten Systemen ist 1e-6 die guenstigere, verhaltensgleiche Wahl. Der WP-T1-Rauschgrenzen-Aspekt bleibt nur fuer exakt loesbare Systeme relevant, die die Toleranz tatsaechlich erreichen (z. B. System 11) — separate, kleinere Frage.

### Messvorbehalt — Wall-Clock kontaminiert, deterministische Schluesse unberuehrt

Der PC wurde waehrend des Laufs 2x zugeklappt (Weg zur Arbeit und zurueck, je ~45 min, ~90 min gesamt), und es lief Nebenlast durch paralleles Arbeiten. **Das kontaminiert ausschliesslich die Wall-Clock-Achse:** `elapsed_s`, `s_per_level`, `ms_per_ode_solve`, Zeitanteile und der 6,35x-Speedup sind aufgeblaeht und verrauscht und duerfen nicht als praezise Messwerte zitiert werden. Warum die wissenschaftlichen Schluesse trotzdem stehen:

1. **Anker bit-exakt** → die Berechnung selbst ist unkorrumpiert; Suspend hat den Determinismus nicht gebrochen.
2. **`time_limit_s = 86400` war nie bindend** (max R8: 31.413 s ≪ 86.400 s) → keine Iteration wurde zeitlich abgeschnitten → Iterationszahlen und Ergebnisse deterministisch, unabhaengig von Suspend-Luecken.
3. **Alle tragenden Zahlen sind Zaehlungen, keine Zeiten:** Stage, Overshoot, wasted_levels, Struktur/Support, Integrationszaehlungen (98.253 vs 3.348.287), Rank-Agreement, Gate-Diagnostik. Genau dafuer hat WP-P1 die Wall-Clock aus dem Ergebnispfad entfernt und das Skript die Solve-Zaehlungen praezise protokolliert.

Konsequenz fuer das Paper: Kosten ueber Integrationszaehlungen berichten, nicht ueber Wall-Clock. Fuer eine belastbare Zeitmessung braeuchte es einen ungestoerten Lauf ohne Suspend/Nebenlast; das ist aber fuer die v3-Begruendung nicht noetig, weil diese auf den deterministischen Achsen ruht.

<!-- e8f12f4 -->

## 2026-07-23

### WP-T2 beauftragt — Toleranz und Screening auf System 26, mit geschaerfter Vorhersage

Naechster Schritt festgelegt: die entscheidende Messung auf System 26, dem Gate-1-System. Drei Bedingungen, Seed 42, 30 Level: R6 (Referenz, Toleranz 1e-6), R8 (Referenz, 1e-8), D8 (Screening Nested-Gate + entkoppelter Start, 1e-8). User hat die kombinierte Ein-Seed-Variante gewaehlt.

**Geschaerfte Vorhersage, die den Wert der Messung erhoeht.** Beim Durchdenken des Mechanismus zeigt sich, dass mein urspruengliches „Overshoot koennte numerisch sein" zu breit war. Der numerische Kanal auf System 3 war spezifisch: der Loss operiert dort nahe `loss_tol = 1e-8`, und bei 1e-6 erreicht der Optimierer die Schwelle nicht → kein Abbruch → Eskalation. Auf System 26 liegt der Loss-Boden bei ~1,4e-3, also drei Groessenordnungen **ueber** selbst der 1e-6-Toleranz. `loss_tol` kann dort nie feuern, unabhaengig von der Toleranz, und die Eskalation ist plateau-getrieben. **Vorhersage: die engere Toleranz aendert den Overshoot auf System 26 nicht — der Overshoot ist hier algorithmisch, was die v3-Begruendung bestaetigt statt bedroht.** Falsifizierbar an den gemessenen Stage-Zahlen.

Damit trennt die Messung im Bestaetigungsfall sauber: auf einfachen Systemen numerisch, auf gekoppelten algorithmisch — eine staerkere Paper-Aussage als „Overshoot ist numerisch". Im Widerlegungsfall verstehe ich den Mechanismus nicht und muss das vor v3.3 klaeren. Unabhaengig davon wird D zum ersten Mal auf einem gekoppelten System getestet, dem, wo v2.2 die Struktur komplett falsch fand.

Ankerpflicht in der Spec: R6 muss Baseline v0 reproduzieren (System 26 Seed 42, 30 Level, 1e-6: Loss `0.001391623174905009`, `final_stage = 5`, Overshoot 2, `pruned_match = false`). Ohne bestaetigten Anker ist nichts interpretierbar. Reihenfolge nach steigender Laufzeit (D8, R8, R6), nach jeder Bedingung sofort schreiben.

### WP-T2 und WP-T2b geliefert — Lauf startklar

WP-T2 (`78124f0`): `studies/numerics/system26_tolerance_screening.jl`, drei Bedingungen D8/R8/R6, Anker gegen Baseline v0, inkrementelles Flush, Antwortblatt fuer die vier Fragen. Beim Spec-Schreiben Fast-Fehler korrigiert: die urspruengliche Verification-Zeile „Skript ausfuehren und berichten" haette Codex den 5-8h-Lauf starten lassen — durch No-Execute-Riegel plus billigen System-3-Smoke-Test ersetzt. Als Gedaechtnisnotiz festgehalten ([[feedback_long_run_no_execute]]).

WP-T2b (`4dead22`): rein additive Beobachtbarkeit. Statischer Review bestaetigt: nebenwirkungsfreier `level_callback` (liest nur den Snapshot, kein RNG, `verbose` bleibt 0), robust gegen beide Snapshot-Formen (EvoGrow `vis_history` ohne `elapsed_s`/`n_params` via hasproperty-Fallback, EvoGrowScreening `level_log` mit beiden), eine Live-Zeile pro Level plus `run.log`. Ergebnisse bit-identisch by construction.

Ausgeführter Lauf steht aus — wird extern gestartet. Ablauf: erst Sekunden-Preflight `EVO_T2_SYSTEM_ID=11` (bestaetigt Anker-Reproduktion und End-to-End-Lauf), dann System 26.

<!-- 78124f0, 2ee1b5a, 4dead22 -->

### Projektjournal erstellt

Auf Wunsch ein ausfuehrliches Projektjournal als roter Faden erstellt: `docs/projektjournal.md` (Narrativ) und `docs/projektjournal.pdf` (13 Seiten, gesetzt). Zeitraum 2026-04-20 bis 2026-07-23, mit allen Entscheidungen, verworfenen Ansaetzen samt Begruendung und Beleg, und den Messzahlen. Ergaenzt CLAUDE.md (Zustand), DIARY.md (Chronologie), PAPER_1.md (Plan). Committet `fa25253`.

<!-- 713d85f -->

## 2026-07-22

### WP-P1b Korrekturen vor Benchmark-Lauf

- `EvoGrowV3` bekommt denselben `screening_optimizer`-Durchreichpfad und dieselben Kosten-Meta-Felder wie `EvoGrow`; ohne gesetzten Screening-Optimizer bleibt die Lockstep-Bruecke im Referenzpfad unveraendert.
- Fruehe Verwerfung divergierender Screening-Solves nutzt `unstable_check` statt `isoutofdomain`; die zusaetzliche Pruefung gegen `divergence_limit` ist elementweise formuliert.
- Profiling-Benchmark wird auf 12 Level begrenzt, rechnet Screening vor Referenz und schreibt Zwischenergebnisse nach jedem Fall.
- Offener Reproduzierbarkeitszustand: ausserhalb des Regression-Runners konstruieren Benchmarks, Experimente und alte Studies `BFGSOptimizer` weiterhin ohne explizites `time_limit_s`; der Struct-Default bleibt `300.0` und muss vor Phase B bewusst entschieden werden.

### WP-P2.4 gelaufen — beide Interventionen wirken; Bedingung D schlaegt den Referenzpfad um Faktor 6,2

Committet `7eb8381`. Ankerpruefung bestanden: Referenzpfad bei 1e-6 liefert auf beiden Systemen bit-identisch die Baseline-v0-Werte.

**System 3, Bewertungstoleranz 1e-8:**

| Bedingung | Zeit | Loss | Stage | Fits | Integrationen |
|---|---|---|---|---|---|
| A Referenz | 78,6 s | 6,25e-9 | 2 | 110 | 275.098 |
| B Residuum + LS-Start (heute) | 353,2 s | 3,236e-8 | 5 | 241 | 761.581 |
| C Nested-Gate + LS-Start | 49,2 s | 3,236e-8 | 5 | 241 | 232.224 |
| **D Nested-Gate + entkoppelter Start** | **12,6 s** | **2,558e-9** | **2** | 61 | 73.680 |

System 11: alle Bedingungen qualitativ gleichwertig (Loss ~2,0e-16, Stage 4, `pruned_match` true), D mit 0,6 s gegen 1,1 s am schnellsten.

**Antwort auf die drei Pflichtfragen:**

1. **Der geschachtelte Test veraendert die Auswahl** — anders als AIC. System 3, Bedingung C: 147 von 400 Kindern scheitern am Gate, die Auswahl weicht in 126 Faellen auf 7 von 20 Leveln vom reinen Residuen-Score ab. Wirkung auf die Rangeuebereinstimmung: von **−0,78 (Median −1,0)** unter B auf **+0,26 (Median +0,48)** unter C. Der Test behebt also genau das, wofuer er gebaut wurde.
2. **Die Stage-Eskalation verschwindet — aber erst durch den Startpunkt.** C bleibt trotz wirksamem Gate bei Stage 5; D erreicht Stage 2, also die erwartete Stage, ohne Overshoot.
3. **Bedingung D entkommt dem Becken bei 3,236e-08** und erreicht 2,558e-9 — besser als der Referenzpfad mit 6,25e-9.

**Arbeitsteilung der beiden Interventionen sauber getrennt:** Das Gate senkt die Kosten (B nach C: 7,2x bei identischem Ergebnis) und repariert das Ranking. Der entkoppelte Startpunkt repariert Qualitaet und Eskalation (C nach D). Beide waren noetig, keine allein haette gereicht — genau die Aufteilung, die WP-T1 vorhergesagt hat.

**Nebenbefund mit potenziell groesserer Tragweite als das Screening selbst:** Der **Referenzpfad** profitiert schon allein von der engeren Toleranz. Bei 1e-6 braucht er auf System 3 279,3 s und endet auf Stage 3 (erwartete Stage: 2, also Overshoot 1); bei 1e-8 braucht er 78,6 s und endet auf Stage 2, also **ohne Overshoot** — 3,6x schneller bei korrekter Stage. Erklaerung: bei 1e-6 erreicht der Optimierer auf Stage 2 die Schwelle `loss_tol = 1e-8` nicht zuverlaessig, die Suche eskaliert deshalb weiter. **Ein Teil des beobachteten Stage-Overshoots waere damit ein numerisches Artefakt und keine Eigenschaft der Promotionsregel.** Das beruehrt unmittelbar die Begruendung fuer v3 und die 62-Prozent-Rechnung vom 2026-07-22. Bisher eine Zelle, ein Seed — muss auf einem gekoppelten System geprueft werden, und zwar auf System 26, wo Gate 1 gescheitert ist.

**Bemerkung zur Spec-Treue:** `SpecialFunctions` wurde als direkte Abhaengigkeit ergaenzt (nur `loggamma` fuer die F-Verteilung), obwohl die Spec keine neuen Abhaengigkeiten vorsah. Praktisch unkritisch: das Paket war ueber SciML bereits indirekt im Manifest, es wird nichts zusaetzlich installiert, nur die direkte Deklaration kam hinzu.

<!-- 7eb8381, 3327c9b -->

### WP-P2.4 beauftragt — zwei getrennte Interventionen statt nur harter Penalty

Die Spec sieht nach WP-T1 anders aus als geplant. Der harte Penalty allein kann das Ergebnis nicht retten, weil das Screening-Versagen auf System 3 laut Befund 3 nicht vom Ranking kommt, sondern vom LS-Warmstart. Deshalb zwei Interventionen, jeweils einzeln abschaltbar und einzeln messbar.

**Intervention 1 — geschachtelter Modellvergleich als Gate.** Kein additiver Strafterm mehr: bei n = 200 ist jedes Informationskriterium vom Fit-Term dominiert (AIC-Strafe hoechstens 10 Einheiten ueber p = 1..6, Fit-Term aendert sich um 19 schon bei 10 % Residuenunterschied; BIC mit `p*log(n) <= 26,5` ebenfalls zu schwach). Stattdessen darf ein Kind seinen Elternteil nur ueberholen, wenn die Residuenverbesserung groesser ist, als ein zusaetzlicher Parameter zufaellig liefern wuerde. Umsetzung als Gate mit zwei Raengen, innerhalb der Gruppen weiter nach Residuum. Erfordert, dass die Kindergenerierung die Herkunft eines Kandidaten bis zur Bewertung mitfuehrt.

**Pflicht-Nachweis der Wirksamkeit.** Die AIC-Runde ist daran gescheitert, dass die Intervention die Rangfolge nicht bewegt hat und das erst hinterher auffiel. Diesmal muss der Lauf selbst protokollieren, in wie vielen Faellen sich die ausgewaehlte Kandidatenmenge von der des reinen Residuen-Scores unterscheidet. Ist der Wert null, ist die Intervention wirkungslos und das ist sofort erkennbar.

**Intervention 2 — Polish-Start entkoppeln.** Der LS-Fit erfuellt heute zwei Rollen: Screening-Score und Startpunkt fuers Nachpolieren. Die zweite ist nach WP-T1 schaedlich. Kuenftig konfigurierbar, mit dem Startpunkt des Referenzpfads als Alternative; der LS-Fit dient dann nur noch der Bewertung.

**Rangeuebereinstimmung repariert:** ausweisen, auf wie vielen Leveln ueberhaupt ein endlicher Wert zustande kam, Mittelwert nur ueber diese, dazu Median und Spannweite. Der Verdacht aus WP-P2.3 (rho auf den meisten Leveln `NaN`, Mittelwert von wenigen Leveln getragen) wird damit pruefbar.

**Vergleichslauf mit vier Bedingungen** je System (3 und 11, Seed 42, 30 Level, Bewertungstoleranz **1e-8**, damit System 11 ueberhaupt oberhalb der Rauschgrenze liegt): A Referenz, B Screening mit Residuen-Score und LS-Start (heutiges Verhalten als Kontrolle), C geschachtelter Test mit LS-Start, D geschachtelter Test mit entkoppeltem Start. C gegen B zeigt den Penalty, D gegen C den Startpunkt. Dazu eine Ankerpruefung des Referenzpfads bei 1e-6 gegen Baseline v0.

Drei Fragen sind im Bericht ausdruecklich zu beantworten: veraendert der Test die Auswahl ueberhaupt, verschwindet die Stage-Eskalation auf System 3, und entkommt Bedingung D dem Becken bei 3,236e-08.

Aus WP-T1 vermerkt, aber ausdruecklich **nicht** Teil dieses WP: der Sentinel-Loss `1e6` mit Retcode `Success` bei vollstaendig gescheitertem Fit, die pathologische Line-Search mit bis zu 39.933 Auswertungen bei zwei Parametern, und die Frage, ob die Bewertungstoleranz im Regression-Runner dauerhaft auf 1e-8 gehen soll.

<!-- 9db9741 -->

### WP-T1 gelaufen — Toleranz-Hypothese fuer System 11 bestaetigt, fuer System 3 widerlegt; vier Befunde

Committet `a6919ca`. Diagnose auf Systemen 3 und 11 bei fester bekannt-korrekter Struktur, Toleranzraster {1e-5, 1e-6, 1e-8, 1e-10, 1e-12} im Bewertungspfad, Trajektorienerzeugung unveraendert 1e-9.

**Befund 1 — System 11: berichteter Loss ist numerisches Rauschen.** Erreichter Loss aus dem LS-Warmstart je Toleranz: 8,435e-14 (1e-5), 4,606e-15 (1e-6), 1,669e-17 (1e-8), 4,860e-18 (1e-10), 4,856e-18 (1e-12). Der Wert skaliert also unmittelbar mit der Solver-Toleranz und saettigt erst bei ~5e-18. Baseline v0 meldet **4,402192340718147e-15** — genau das Niveau der 1e-6-Toleranz. Teil A verschaerft das: mit den **wahren** Parametern erreicht man bei 1e-6 nur 1,859e-14, der Fit liefert also 4,6e-15 und damit ein *besseres* Ergebnis als die Wahrheit. Das ist nur moeglich, wenn numerisches Rauschen gefittet wird. Der in Baseline v0, in Phase A und in allen heutigen Regressionspruefungen gefuehrte System-11-Loss ist nicht interpretierbar.

**Befund 2 — System 3: Hypothese widerlegt.** Aus dem LS-Warmstart landet der Fit bei **3,236e-08 bei jeder Toleranz von 1e-6 bis 1e-12**, voellig flach. Sechs Groessenordnungen engere Toleranz aendern nichts. Der Boden aus Teil A liegt bei 1e-6 bei 4,401e-12, das Ergebnis also rund 7.000-fach darueber. Hier ist nicht die Numerik die Grenze, sondern der Optimierer bzw. die Landschaft.

**Befund 3 — die eigentliche Ursache des Screening-Versagens auf System 3.** Der LS-Warmstart konvergiert auf 3,236e-08 — exakt der Wert, bei dem die Screening-Variante haengenblieb (3,2363742537347274e-8). Der Referenzlauf erreicht dagegen 2,66e-10, und er benutzt **keinen** Warmstart (`USE_PRETUNING = false`). Das Screening-Versagen ist damit kein Toleranz- und kein Ranking-Problem, sondern: **der ableitungsbasierte Least-Squares-Warmstart fuehrt auf System 3 in ein Becken, aus dem BFGS nicht herausfindet.** Die Screening-Variante fuehrt damit genau das wieder ein, was die Regression-Konfiguration bewusst abgeschaltet hat.

**Befund 4 — pathologische Line-Search.** Auf System 3 verbrauchen einzelne Fits bei zwei Parametern **39.933 / 37.933 / 39.065** Loss-Auswertungen (jede eine vollstaendige Integration) mit Retcode `Failure`, Laufzeiten 3,2 / 10,4 / 23,6 s — bei `maxiters = 200`, also rund 200 Auswertungen pro Iteration fuer ein Zweiparameterproblem. Erratisch: bei 1e-6 und 1e-8 braucht derselbe Startpunkt nur 585 bzw. 257 Auswertungen. Das erklaert die 7.281 Integrationen pro Fit aus der Regressionsmessung.

**Nebenbefund:** Der Standardstart liefert auf System 3 bei mehreren Toleranzen `final_loss = 1.000e+06` nach 5 Auswertungen mit Retcode **`Success`**. 1e6 ist der Initialwert `l_best` in `fit_parameters` — ein vollstaendig gescheiterter Fit wird also als Erfolg mit Sentinel-Loss gemeldet und ist von einem echten schlechten Fit nicht unterscheidbar.

**Kosten (Teil C, pretune-Start, hochgerechnet auf 20 Fits pro Level):** System 3 — 0,48 s bei 1e-6, 0,64 s bei 1e-8, 1,38 s bei 1e-10, 6,00 s bei 1e-12. System 11 — 0,06 / 0,12 / 0,08 / 0,22 s. **Die Verschaerfung von 1e-6 auf 1e-8 kostet also rund Faktor 1,3 und hebt den System-11-Boden von 1,86e-14 auf 1,36e-17**, womit alle berichteten Losses wieder oberhalb der Rauschgrenze liegen. Empfehlung: Bewertungstoleranz auf 1e-8. Zur Einordnung: die WP-P1b-Screening-Budgets setzen 1e-5 und druecken den System-3-Boden auf 2,06e-10, also auf Faktor 1,29 an den dort berichteten Loss heran — fuer billige Systeme zu grob, fuer System 26 (Loss ~1,4e-3) unkritisch.

<!-- a6919ca, f327de6 -->

### Screening-Spur wieder aufgenommen; WP-T1 (Toleranz-Rauschgrenze) vorgezogen

User hat die Abbruchentscheidung revidiert: Zeit ist doch da, und im Projekt geht es um wissenschaftliche Fundierung, nicht um Schnelligkeit. Gewuenscht sind beide offenen Faeden — harter Penalty **und** Toleranzanalyse.

**Reihenfolge festgelegt: Toleranz zuerst.** Begruendung: Die beiden Faeden sind nicht unabhaengig. Die Ursachenkette auf System 3 lautete „Loss bleibt bei 3,24e-8 -> ueber `loss_tol = 1e-8` -> kein Abbruch -> Eskalation auf Stage 5 -> teurere Kandidaten -> netto langsamer". Wenn der Loss dort nicht wegen schlechter Kandidatenauswahl haengenblieb, sondern weil der Optimierer im Bereich unter der Solver-Toleranz blind ist, dann ist **das gesamte beobachtete Versagen der Screening-Variante ein Toleranz-Artefakt**. Ein Test des Auswahlkriteriums unter unkontrolliertem Confounder waere wertlos.

**Die Frage ist groesser als die Screening-Spur.** System 11 meldet in Baseline v0 einen Loss von 4,402192340718147e-15, also rund 6,6e-8 mittleren Fehler pro Punkt — deutlich unterhalb der Genauigkeit, mit der der Bewertungspfad (`abstol = reltol = 1e-6`) diese Trajektorie berechnet. Die Zahl steht in Baseline v0, in der Phase-A-Auswertung und in jeder heutigen Regressionspruefung. Ist sie numerisches Rauschen, betrifft das die Belastbarkeit der berichteten Losses im gesamten Projekt und die Frage, ob `loss_tol = 1e-8` als Abbruchkriterium sinnvoll definiert ist.

**WP-T1 beauftragt:** Diagnose-Experiment unter `studies/numerics/`, Systeme 3 und 11, feste bekannt-korrekte Struktur, Toleranzraster {1e-5, 1e-6, 1e-8, 1e-10, 1e-12} im Bewertungspfad bei unveraenderter Trajektorienerzeugung (1e-9). Teil A misst ohne Optimierer den bestmoeglich erreichbaren Loss je Toleranz (Belastbarkeitsgrenze der berichteten Werte), Teil B laesst `fit_parameters` je Toleranz aus drei Startpunkten laufen — Standardstart, LS-Warmstart, und wahre Parameter mit 1 % Stoerung als schaerfsten Test —, Teil C beziffert den Preis der Genauigkeit. 1e-5 ist im Raster, weil die WP-P1b-Screening-Budgets diesen Wert setzen.

Falsifizierbare Vorhersage in der Spec: bei 1e-6 bleibt der Warmstart stehen und meldet `Success` nach wenigen Auswertungen, bei 1e-10 verbessert er sich. Tritt das nicht ein, ist die Vermutung widerlegt und wir gehen direkt zum Screening-Test.

**Danach WP-P2.4:** harter Penalty statt AIC. Richtung: kein Informationskriterium — bei n = 200 ist jedes vom Fit-Term dominiert —, sondern ein Nested-Model-Test, bei dem ein Kind seinen Elternteil nur schlaegt, wenn die Residuenverbesserung groesser ist, als ein zusaetzlicher Parameter zufaellig liefern wuerde. Das adressiert die Monotonie-Falle direkt statt sie mit einer Konstanten zu ueberstimmen. Plus Reparatur der rho-Kennzahl. WP-v3.3 bleibt bis dahin liegen.

<!-- b37e457 -->

### Entscheidung: Screening-Spur eingestellt; zurueck zu WP-v3.3

User hat die Abbruchregel wie vereinbart gezogen. Die Screening-Spur (WP-P2.1 bis WP-P2.3) wird eingestellt.

**Was bleibt:** `docs/evogrow_screening_design.md`, `src/structure/evogrow_screening.jl`, `studies/debug/compare_screening_variant.jl` und die Messdaten bleiben im Repository als dokumentierte Zwischenablage. Nicht ohne neue Evidenz wieder aufnehmen.

**Was gesichert ist:** 2,71x aus WP-P1b (Solver-Budgets, System 26), Determinismus im Regression-Ergebnispfad, vollstaendige Kosteninstrumentierung pro Level, und ein quantifiziertes Kostenprofil des Bewertungspfads.

**Ehrliche Einordnung der Falsifikation:** Sie ist weich. Die AIC-Intervention war mathematisch zu schwach, um die Rangfolge ueberhaupt zu bewegen, und die rho-Kennzahl ist fragwuerdig. Die Hypothese „ableitungsbasiertes Screening taugt als Auswahlsignal" ist damit nicht widerlegt, sondern ungeprueft. Eingestellt wurde aus Aufwandsgruenden, nicht aus wissenschaftlicher Klaerung — das gehoert so in eine spaetere Diskussion, falls die Spur wieder aufgenommen wird.

**CLAUDE.md aktualisiert:** Prioritaeten auf Stand 2026-07-22, WP-P1.x als erledigt und WP-P2.x als eingestellt vermerkt, offene Toleranz-Hypothese als ungeplanter Punkt festgehalten.

**Offener Punkt vor der naechsten Baseline:** Die Regression-Konfiguration hat sich seit Baseline v0 geaendert (expliziter `time_limit_s`, zusaetzliche Fingerprint-Felder). Baseline v0 bleibt als historischer Datensatz gueltig, aber vor einer Regressionspruefung von v3.3-Ergebnissen muss eine neue Baseline unter der aktuellen Konfiguration gerechnet werden.

**WP-v3.3 beauftragt** (Designnotiz Abschnitt 6): gleichungsweise Kindergenerierung, zulaessige Terme aus `eq_stages[k]` statt aus einer globalen Stage, Kreuzterm-Regel `min(eq_stages[i], eq_stages[j])`, `StageUsagePolicy` pro Gleichung. Zentraler Punkt der Spec: da WP-v3.4 (gleichungsweise Promotion) noch aussteht, sind alle `eq_stages` weiterhin gleichgeschaltet — der Umbau muss daher **bit-identische** Ergebnisse liefern und ist ein verhaltensneutraler Refactor, dessen Wirkung erst mit v3.4 sichtbar wird. Ausdruecklich mitspezifiziert: die RNG-Ziehreihenfolge darf sich nicht aendern, sonst ist das Kriterium nicht pruefbar. Zusaetzlich wird die Screening-Variante aus `VARIANTS` im Regression-Runner entfernt.

Nebenbefund beim Lesen der Designnotiz: Abschnitt 9 fuehrt die Kreuzterm-Frage als offen, obwohl Abschnitt 6 sie bereits beantwortet. In der Spec als entschieden festgehalten, mit der Konsequenz im Docstring: ein Kreuzterm haengt an den Stages der Gleichungen seiner **Variablen**, nicht an der Stage der verwendenden Gleichung — die einzige Stelle, an der die Gleichungen gekoppelt bleiben.

<!-- afbc065 -->

### WP-P2.3 gelaufen — Abbruchregel ausgeloest, aber der Test war zu schwach, um die Hypothese zu pruefen

Committet `9ca9127`. Codex hat `screening_score = :residual | :aic` eingebaut und — besser als von mir spezifiziert — die Rangeuebereinstimmung auf den **tatsaechlich verwendeten Score** umgestellt statt weiter das rohe Residuum zu vergleichen.

| System 3 | Referenz | Screening residual | Screening AIC |
|---|---|---|---|
| Laufzeit | 370,8 s | 460,1 s | **239,0 s** |
| Loss | 2,66e-10 | 3,2363742537347274e-8 | **3,2363742537347274e-8** |
| `final_stage` | 3 | 5 | **5** |
| Integrationen | 1.529.009 | 711.757 | 510.539 |
| Rangeuebereinstimmung | — | −0,7777777777777778 | **−0,7777777777777778** |

System 11: beide Screening-Bedingungen identisch zum vorigen Lauf, rho +1,0, korrekte Struktur, 1,37–1,47x schneller.

**Die Abbruchregel ist ausgeloest** — rho auf System 3 bleibt negativ. Der Test taugt aber nicht als Falsifikation, und zwar aus einem Grund, den ich in der Spec haette vorhersehen muessen:

**AIC ist hier faktisch eine monotone Transformation des Residuums.** `AIC = n*log(mse) + 2p` mit `n = 200` Beobachtungen: der Fit-Term aendert sich um 19 Einheiten schon bei 10 % Residuenunterschied und um 139 bei Faktor 2, waehrend die Komplexitaetsstrafe ueber den gesamten Bereich `p = 1..6` hoechstens **10** Einheiten betraegt. Spearman ist gegen monotone Transformationen invariant — die Rangfolge kann sich also praktisch nicht aendern. Belegt durch die Daten: Loss bit-identisch, `final_stage` identisch, `total_parameter_fits` identisch, rho bit-identisch. Die Intervention hat die Auswahl nicht bewegt. BIC waere mit `p*log(n) <= 26,5` ebenfalls zu schwach. Bei n = 200 Datenpunkten ist **jedes** Standard-Informationskriterium vom Fit-Term dominiert.

**Zweiter Zweifel an der Messgroesse:** rho betraegt in beiden Bedingungen exakt −7/9, obwohl sich Laufzeit (460 vs 239 s), Integrationen (711.757 vs 510.539) und Konvergenzfehler (106 vs 79) deutlich unterscheiden. Das passt schlecht zu einer stabilen Kennzahl und gut zu der Vermutung, dass rho auf den meisten Leveln `NaN` ist (alle simulierten Losses gleich -> `denom == 0`) und der berichtete Mittelwert von sehr wenigen Leveln getragen wird. Ungeprueft, aber die Kennzahl ist damit als Entscheidungsgrundlage fragwuerdig.

**Neuer Befund zum wirkungslosen finalen Refit:** Die Diagnostik zeigt `final_refit_method = BFGS`, `final_refit_retcode = Success`, `final_refit_loss_evals = 5`, keine Failure-Hits. BFGS kehrt also nach fuenf Auswertungen als *konvergiert* zurueck. Der Verdacht: die ODE-Solver-Toleranz im Bewertungspfad betraegt `abstol = reltol = 1e-6`, waehrend der Loss bei ~3e-8 liegt. Finite-Differenzen-Gradienten einer Groesse, die nur auf 1e-6 genau berechnet wird, sind in diesem Bereich Rauschen — der Optimierer sieht keinen Abstieg mehr. Das waere kein Screening-Problem, sondern eine Eigenschaft des gesamten Bewertungspfads und beruehrt auch Pretuning-Warmstarts und die Frage, ob `loss_tol = 1e-8` ueberhaupt zuverlaessig erreichbar ist. Als Hypothese notiert, nicht als Befund.

**Bilanz der Screening-Spur:** AIC-Screening ist auf beiden Systemen schneller als der Referenzpfad (1,55x auf System 3, 1,37x auf System 11), liefert aber auf System 3 einen um Faktor 121 schlechteren Loss und eskaliert auf Stage 5 statt 3. In dieser Form nicht verwendbar.

<!-- 9ca9127, 96ac621 -->

### WP-P2.2c gelaufen — erste echte Zahlen: System 11 funktioniert, System 3 falsifiziert das Kriterium

Vergleichsskript `studies/debug/compare_screening_variant.jl` committet (`2eb7202`) und ausgefuehrt. Konfiguration identisch zur Regression-Suite (30 Level, pop 10, λ=1e-3, BFGS 200, Seed 42).

| | System 3 Referenz | System 3 Screening | System 11 Referenz | System 11 Screening |
|---|---|---|---|---|
| Laufzeit | 357,6 s | **400,9 s** | 3,63 s | **2,36 s** |
| Loss | 2,66e-10 | **3,24e-8** | 4,402e-15 | 4,407e-15 |
| `final_stage` | 3 | **5** | 4 | 4 |
| `pruned_match` | true | true | true | true |
| Integrationen | 1.529.009 | 711.757 | 8.942 | 10.599 |
| Kosten/Integration | 0,172 ms | **0,490 ms** | — | — |
| Rangeuebereinstimmung | — | **−0,78** | — | **+1,00** |

Referenzpfad reproduziert in beiden Zellen exakt Baseline v0 (Loss und `final_stage` geprueft).

**System 11 funktioniert:** korrekte Struktur `-u1^3` gefunden, Faktor 1,53 schneller, Rangeuebereinstimmung +1,0, kein erschoepftes Polish-Budget, kein abgelehnter Kandidat haette gewonnen.

**System 3 falsifiziert das Kriterium in seiner jetzigen Form.** Rangeuebereinstimmung −0,78: der Screening-Score ordnet nahezu **umgekehrt** zum simulierten Loss. Belegte Ursachenkette: (1) der Loss bleibt bei 3,24e-8 und damit ueber `loss_tol = 1e-8`, die absolute Abbruchbedingung feuert nie, waehrend der Referenzlauf bei 2,66e-10 abbricht und auf Stage 3 bleibt; (2) die Suche eskaliert bis Stage 5, also trigonometrische Terme und steifere Kandidaten-ODEs — Kosten pro Integration 0,490 ms gegen 0,172 ms, Faktor 2,85, womit die eingesparten Integrationen mehr als aufgefressen werden; (3) der finale Refit auf vollem Budget dauert **0,001 s** und bewirkt nichts, obwohl beide Varianten dieselbe Struktur finden (`du1/dt = 0.790*u1 + -0.011*u1^2`, beide `pruned_match = true`) — der Loss-Unterschied stammt allein aus den Parametern.

**Vermutete Ursache der negativen Rangeuebereinstimmung:** Kinder entstehen durch Hinzufuegen von Termen, sind also geschachtelte Obermengen ihrer Eltern. Fuer geschachtelte Least-Squares-Probleme ist das Residuum monoton nicht-steigend in der Termzahl — ein groesseres Modell kann nie ein schlechteres LS-Residuum haben. Der Screening-Score enthaelt aber nur einen Tiebreak von `1e-12 * n_params`, waehrend das Suchziel mit `λ = 1e-3` bestraft. Der Score bevorzugt damit systematisch die groessten Kandidaten, was sowohl die negative Rangeuebereinstimmung als auch die Stage-Eskalation erklaert.

**Befund gegen die Praemisse des Kostenmodells:** `polish_budget_exhausted = 0` in **allen** Laeufen. Das 20-Iterationen-Budget wurde nie ausgeschoepft; BFGS terminiert vorher, in 106 von 200 Faellen mit Konvergenzfehler. Die Einsparung von 200 auf 20 Iterationen existiert also gar nicht, weil der Referenzpfad die 200 ebenfalls nie erreicht. Passend dazu sinken die Integrationen pro Fit nur von 7.281 auf 2.953 (Faktor 2,5) trotz zehnfach kleinerem Iterationsbudget — die Zahl der Integrationen wird offenbar nicht vom Iterationslimit getrieben.

**WP-P2.3 beauftragt als letzter Versuch, mit Abbruchregel:** komplexitaetsbewusster Screening-Score (skalenfreies Informationskriterium; ein Uebernehmen von `λ` waere falsch, weil dort ein Simulations-MSE und hier ein Ableitungsresiduum bestraft wird), Untersuchung des wirkungslosen finalen Refits, und Wiederholung der Messung mit drei Bedingungen je System (Referenz, alter Score als Kontrolle, neuer Score). Bleibt die Rangeuebereinstimmung auf System 3 negativ, gilt das Kriterium als falsifiziert und die Arbeit daran wird eingestellt; es bleiben die 2,71x aus WP-P1b.

<!-- 2eb7202, 61e6459 -->

### WP-P2.2b reviewt — Code korrekt, aber nie ausgefuehrt; WP-P2.2c beauftragt

Committet `7f52676`. Alle sechs Punkte korrekt behoben: `screening_budgets_active` behaelt seine urspruengliche Bedeutung und wird aus der Strategie abgeleitet, `derivative_screening_active` als eigenes Feld ergaenzt und im Record gefuehrt; der Runner reicht den `screening_optimizer` jetzt durch. Erschoepfung wird am Iterationslimit gemessen, Konvergenzfehler getrennt gezaehlt. Diagnose-Stichprobe abgelehnter Kandidaten implementiert — geprueft: sie wird nur gemessen, nie nach `polished` geschrieben, beeinflusst die Suche also nicht; `rejected_beats_best_selected` zaehlt die relevanten Faelle. `screen_k < pop_size` wird abgelehnt statt still zu schrumpfen. Struct-Defaults auf `EvoGrow` angeglichen. Finaler Refit ueber `_add_fit_stats!` in den Summen. Monotonie-Abweichung und leere `vis_history` im Docstring dokumentiert. Keine doppelten Funktionsdefinitionen; Include-Reihenfolge stimmt.

**Zwei kleinere Restpunkte:** (i) `screen_k` ist faktisch inert — die Validierung verbietet Werte unter `pop_size`, der Clamp `min(..., pop_size)` verbietet Werte darueber, also ist `screen_k` immer exakt `pop_size`. Damit faellt die in der Design-Notiz genannte Eigenschaft weg, durch Erhoehen von k zum heutigen Verhalten zu degradieren — eine nuetzliche Kontrollvariante. (ii) Die Diagnose-Stichprobe nimmt die **bestplatzierten** abgelehnten Kandidaten, also die knapp Gescheiterten. Das ist die trennschaerfste Wahl fuer Fehler an der Auswahlgrenze, erkennt aber nicht den Fall, dass ein Kandidat mit schlechtem Screening-Score gut simuliert haette. Als dokumentierte Einschraenkung vertretbar.

**Der eigentliche offene Punkt: die Variante ist nie ausgefuehrt worden.** Die in WP-P2.2 und WP-P2.2b jeweils ausdruecklich geforderten Messzahlen wurden beide Male nicht geliefert, und im Repository liegen keine Artefakte eines Verifikationslaufs (`history.jsonl` unveraendert bei 23 Zeilen, keine neuen Ausgaben). Statisch sieht der Code korrekt aus — ob er laeuft und ob das Ableitungskriterium als Auswahlsignal taugt, ist unbekannt.

**WP-P2.2c beauftragt:** wiederverwendbares Vergleichsskript unter `studies/debug/` (Systeme 3 und 11, Seed 42, Referenzpfad gegen Screening-Variante, Level-Budget 30 wie Baseline v0), ausfuehren, und vier Fragen mit Zahlen beantworten: laeuft es durch, findet es `-u1^3` auf System 11, wie hoch ist der Anteil erschoepfter Polish-Budgets, wie faellt die Rangeuebereinstimmung aus. Zusaetzlich Gegenprobe, dass der Referenzpfad weiterhin die Baseline-v0-Werte liefert. Wiederverwendbar statt einmalig, weil dieselbe Pruefung bei WP-v3.3 erneut gebraucht wird.

<!-- 7f52676, ee74602 -->

### WP-P2.2 umgesetzt und reviewt — drei Blocker, WP-P2.2b beauftragt

`src/structure/evogrow_screening.jl` committet (`07aee5e`). Kern korrekt: finaler Refit auf vollem Budget vorhanden, Stopplogik und Promotion bekommen `best.loss` (simulierter Loss), Incumbent wird immer mitgezogen, ungueltige Screening-Faelle explizit markiert und gezaehlt, `pretune_parameters` verhaltensgleich, `evogrow.jl` / `evogrow_v3.jl` / `discover.jl` / `stopping.jl` unangetastet. Kinder werden mit `objective = Inf` initialisiert — geprueft, damit kann der Revert-Schutz keine unbewerteten Kinder in die Population heben. Spearman mit Ties-Korrektur ueber Durchschnittsraenge korrekt implementiert.

**Blocker 1 — Feldkollision `screening_budgets_active`.** Die Variante gibt das Feld fest als `true` zurueck. In WP-P1b wurde es mit anderer Bedeutung eingefuehrt („reduzierte Solver-Budgets aktiv") und wandert aus dem Meta in den Record. Damit laesst sich in `history.jsonl` nicht mehr unterscheiden, ob ein Record mit Solver-Budgets oder mit Ableitungs-Screening lief. Verschaerfend: der Runner-Konstruktor nimmt `screening_optimizer` entgegen und verwirft ihn — die Variante nutzt die Solver-Budgets gar nicht, korrekt waere also `false`. Dieselbe Defektklasse wie WP-P1b B1, unter anderem Namen.

**Blocker 2 — Polish-Erschoepfung mit falschem Zaehler.** Erkennung ueber `optimizer_limit_hits > 0`; dieser Zaehler steigt bei **jedem** Nicht-Success-Retcode. Belegt am System-3-Benchmark: `optimizer_failure_hits = 95` bei 210 Fits, `optimizer_iteration_limit_hits = 0`. Die Kennzahl wuerde also nahezu durchgaengig „Budget erschoepft" melden, unabhaengig vom Budget — und genau sie entscheidet, ob die Losses mit dem Simulationspfad vergleichbar sind.

**Blocker 3 — die Rangeuebereinstimmung kann ihre Frage nicht beantworten.** Spearman wird nur ueber die **ausgewaehlten** Kandidaten berechnet, also ueber eine per Konstruktion auf gute Screening-Scores eingeschraenkte Menge. Gemessen wird damit die Uebereinstimmung unter den Ueberlebenden, nicht ob die Vorauswahl gute Kandidaten verwirft — das zentrale Methodenrisiko aus Abschnitt 6 der Design-Notiz. Der Vergleichslauf koennte durchlaufen und die Frage bliebe offen. Korrektur: kleine Stichprobe **abgelehnter** Kandidaten mitpolieren und simulieren, rein diagnostisch, ohne Einfluss auf die Suche.

**Kleinere Befunde:** (i) `pop` wird aus `polished` gebildet, das hoechstens `screen_k` Eintraege hat — bei `screen_k < pop_size` kollabiert die Population still auf `screen_k`. (ii) Struct-Default `usage = :soft` weicht von `EvoGrow`, `EvoGrowV3` und allen drei Runner-Varianten (`:hard`) ab. (iii) Der finale Refit wird nicht ueber die Fit-Statistik verbucht; `total_ode_solves` und `total_simulation_time_s` schliessen ihn aus. (iv) Wird ein Elternteil durchs Polieren schlechter, behaelt die Variante den alten Wert — `EvoGrow` kennt diesen Schutz nicht. Dadurch ist die Objective-Folge hier monoton, dort nicht, was Plateau-Erkennung und Promotion beruehrt; vertretbar, aber dokumentationspflichtig. (v) `vis_history` wird angelegt und zurueckgegeben, aber nie gefuellt.

**Nicht berichtet:** die in WP-P2.2 geforderten Verifikationszahlen (Laufzeit, Polish-Erschoepfung, Rangeuebereinstimmung, System 11 exakt gefunden?) liegen nicht vor, und im Repo sind keine Artefakte eines Verifikationslaufs. In WP-P2.2b sind die gemessenen Zahlen ausdruecklich Teil des Deliverables.

<!-- 07aee5e, f5f4e4e -->

### WP-P2.2 beauftragt — Screening-Variante mit begrenztem Nachpolieren

Architektur festgelegt. Reines Screening ohne Simulation waere am billigsten, macht aber die Stopplogik unbrauchbar: Parameter aus dem Ableitungs-LS sind nicht fuer das Simulationsziel optimiert, und `plateau_tol = 1e-4` sowie `loss_tol = 1e-8` sind auf BFGS-optimierte Losses kalibriert. Loesung ist ein **begrenztes Nachpolieren** der ausgewaehlten Kandidaten, ausgehend von den LS-Parametern.

Kostenmodell aus den Messwerten (4.707 Solves pro Fit bei 200 Iterationen -> 23,5 Solves/Iteration -> 41,5 ms/Iteration; heute 170,9 s pro Level):

| k | Polish-Iterationen | Kosten/Level | Solve-Faktor |
|---|---|---|---|
| 10 | 0 | 0,02 s | Stopplogik kaputt |
| 10 | 10 | 4,2 s | 41x |
| 10 | 20 | 8,3 s | 21x |
| 5 | 20 | 4,2 s | 41x |
| 10 | 50 | 20,8 s | 8x |

Nach Abzug des Overhead-Bodens von 153 s realistische Gesamterwartung **10–15x** auf dieser Zelle, nicht die 21x der theoretischen Untergrenze. Das ist die Zahl, an der die Umsetzung zu messen ist.

Ablauf pro Level: alle Kandidaten per Screening-Score bewerten (kein BFGS, keine Simulation), die besten k plus den Incumbent auswaehlen, nur diese mit begrenztem Budget nachpolieren und simulieren, nur simulierte Kandidaten duerfen in die Population. Plateau, Stopplogik und Promotion laufen **ausschliesslich** auf simuliertem Loss — die Trennung aus Abschnitt 4 der Design-Notiz. Der berichtete `loss` bleibt ein simulierter Loss auf voller Genauigkeit, die Endstruktur wird einmal mit vollem Budget nachgefittet.

Zwei Messgroessen als Pflicht: (i) wie viele ausgewaehlte Kandidaten ihr Polish-Budget ausschoepfen — durchgaengiges Ausschoepfen bedeutet, die Losses sind nicht mit dem Simulationspfad vergleichbar; (ii) **Rangeuebereinstimmung** zwischen Screening-Score und simuliertem Loss unter den simulierten Kandidaten — die Messgroesse fuer das zentrale Methodenrisiko (Zielkonflikt), ohne die sich nicht beurteilen laesst, ob die Vorauswahl gute Kandidaten verwirft.

Neue Variante neben dem bestehenden Pfad, kein Ersatz. `pretune.jl` wird um eine Score-Funktion mit Gueltigkeitsflag erweitert; `pretune_parameters` selbst bleibt verhaltensgleich. Verifikation nur auf System 3 und 11.

<!-- 64d9e3d -->

### WP-P2.1 Design-Notiz reviewt — tragfaehig, aber ohne Kostenmodell; Faktor 10 haengt an einem Wort

`docs/evogrow_screening_design.md` committet (`97e0dbe`). Alle neun Pflichtabschnitte vorhanden. Saemtliche Zahlen gegen `summary.json` geprueft und korrekt, inklusive der 21x als `3222,6 / 153,0`. API-Referenzen auf `pretune.jl` stimmen (Signaturen von `estimate_derivatives`, `build_design_matrix`, Per-Gleichungs-LS geprueft). Abschnitt 4 und 7 beziehen klare Position: Stage-Promotion bleibt am simulierten Loss verankert, und der Beitrag bleibt nur dann von SINDy unterscheidbar, wenn staged incremental growth Untersuchungsgegenstand bleibt und der simulierte Loss die berichtete Metrik.

**Luecke: kein Kostenmodell fuer den vorgeschlagenen Entwurf.** Die Notiz begruendet sich mit der 21x-Obergrenze, schaetzt aber nie, was ihr eigener Vorschlag kostet. Abschnitt 3 empfiehlt „alle Kandidaten screenen, die besten k pro Level simulieren" mit `k = pop_size` als Kandidatenregel — laesst aber offen, was „simulieren" fuer diese k bedeutet. Aus den gemessenen Groessen (Fall A: 370 Fits ueber 18 Level, 4.707 Solves pro Fit, 1,763 ms pro Solve, 8,30 s Solve-Zeit pro Fit, 0,41 s Overhead pro Fit):

| Variante pro Level (20,6 Kandidaten) | Kosten | Faktor |
|---|---|---|
| heute: alle per BFGS mit Simulation | 170,5 s | 1,0x |
| (b) Top k=10 per BFGS mit Simulation | 83,0 s | 2,1x |
| (b) Top k=5 per BFGS mit Simulation | 41,5 s | 4,1x |
| (a) Top k=10 je **eine** Simulation der LS-Parameter | 0,018 s | Solve-Kosten praktisch null |

Hochrechnung auf den ganzen Lauf: heute 3223 s, Variante (b) mit k=10 rund 1646 s (**2,0x**), Variante (a) rund 153 s (**21,1x**, Untergrenze Overhead + LS). **Der Unterschied zwischen 2x und 21x steckt in einem einzigen unausgesprochenen Wort.** Die Quelle des Speedups ist nicht das Screening an sich, sondern dass die geschlossene LS-Loesung die rund 200 BFGS-Iterationen mit je ~25 Solves pro Kandidat ersetzt. Die Notiz impliziert das, sagt es aber nirgends.

**Synthese, die die Notiz nicht zieht:** Variante (a) erfuellt die Forderung aus Abschnitt 4 mit. Eine Simulation pro ausgewaehltem Kandidaten kostet 1,763 ms; damit bleibt ein simulierter Loss-Anker fuer Plateau-Erkennung und Stage-Promotion pro Level erhalten, ohne die Kosten messbar zu erhoehen. Die 21x und die Anforderung „Promotion bleibt am simulierten Loss verankert" stehen also **nicht** im Konflikt. Offene Entscheidungen 1–3 sind damit auf Evidenzbasis beantwortbar.

**Kleinere Befunde:** (i) Abschnitt 6 nennt als Falsifikation „ein wiederholtes Muster" ohne Schwelle und ohne benannten Test; ist als offene Entscheidung 7 deklariert und damit spec-konform, fuer ein Abbruchkriterium aber zu weich. (ii) `USE_PRETUNING = false` im Regression-Config wird nicht erwaehnt — der gesamte Entwurf ruht auf Maschinerie, die in genau der Konfiguration abgeschaltet ist, die die Messung erzeugt hat. (iii) `pretune_parameters` liefert `zeros(n)`, sobald eine Gleichung nicht-endliche Werte oder `norm > 1e6` ergibt. Als Warmstart harmlos, als Screening-Score faellt ein entarteter Kandidat damit still auf „alle Parameter null" statt als ungueltig markiert zu werden. Die Notiz nennt fehlende Failure-Flags korrekt, aber nicht diese konkrete Falle im wiederverwendeten Code.

<!-- 97e0dbe, a9043e0 -->

### Loss konvergiert in allen Zellen bis Level 18 — Level-Cap trotzdem abgelehnt; WP-P2.1 beauftragt

Rekonstruktion aus dem v0-`run.log` (`best_loss` pro Level, alle 23 Zellen, keine neuen Laeufe noetig): **13 Zellen liefen ueber Level 18 hinaus, und in allen 13 war der Loss bei Level 18 bereits identisch zum Endergebnis.** Kein Level nach 18 hat je etwas verbessert. Kosten dieser Level: **15,8 von 40,5 h = 39 % der gesamten Rechenzeit**.

**Entscheidung: Level-Budget bleibt bei 30.** Der User hatte einer Kuerzung auf 18 zugestimmt, ich habe die Empfehlung zurueckgezogen. Grund: der Loss bliebe identisch, `final_stage`, `stage_overshoot` und `wasted_levels` aber nicht. System 26 Seed 42 bei 30 Leveln Stage 5 / Overshoot 2 / 8 wasted; bei 18 Leveln Stage 3 / Overshoot 0. Das sind die H1- und H3-Metriken. Ein Level-Cap wuerde das Overshoot-Phaenomen wegschneiden statt es zu messen — also genau das, was v3 beheben soll. Meine urspruengliche Optionsbeschreibung hatte diese Konsequenz nicht genannt.

**Der Befund gehoert stattdessen in den v3-Entwurf.** Der Loss konvergiert in jeder Zelle bis Level 18, die Suche laeuft aber bis Level 26–29 weiter, weil Plateau-Erkennung Stage-Promotion ausloest statt Terminierung. Die Suche kann nicht aufhoeren, solange Stages uebrig sind — sie eskaliert stattdessen. Das ist ein Befund ueber die Stopp- und Promotionsregel, kein Konfigurationsproblem: die Promotionsregel braucht ein Kriterium, das erkennt, wann zusaetzliche Komplexitaet nichts mehr bringt, nicht nur wann der Fortschritt stockt.

**WP-P2.1 beauftragt:** Design-Notiz `docs/evogrow_screening_design.md` fuer ein ableitungsbasiertes Screening-Kriterium, analog zum Vorgehen bei WP-v3.1 (erst Entwurf, dann Code). Neun Pflichtabschnitte; kritisch sind Abschnitt 4 (Stopplogik, Plateau-Erkennung und Stage-Promotion arbeiten heute auf dem Simulations-Loss — welches Signal traegt sie kuenftig?) und Abschnitt 7 (Verhaeltnis zum wissenschaftlichen Beitrag: ableitungsbasierte Bewertung rueckt naeher an SINDy, die Abgrenzung muss explizit begruendet werden). Kein Code, keine Laeufe.

<!-- b0c8eaa -->

### Mikro-Benchmark System 26 gelaufen — Kostentreiber quantifiziert, Obergrenze bei 21x

Externer Lauf `studies/profiling/profile_eval_cost.jl` auf System 26, Seed 42, v2.2, 18 Level. Beide Faelle mit **identisch 370 Parameter-Fits** — damit ist der Vergleich normiert.

| | A (Referenz) | B (Screening) | Faktor |
|---|---|---|---|
| Laufzeit | 3222,6 s (53,7 min) | 1189,8 s (19,8 min) | **2,71x** |
| Kosten pro Fit | 8,71 s | 3,22 s | 2,71x |
| ODE-Solves | 1.741.484 | 2.488.973 | 0,70x |
| Kosten pro Solve | 1,763 ms | 0,409 ms | **4,31x** |
| Solve-Anteil an Laufzeit | **95 %** | 86 % | |
| Overhead ohne Solve | 153 s | 166 s | |
| Loss | 1,391623e-3 | 2,653197e-4 | B 5,2x besser |
| erreichte Stage | 3 | 4 | |
| `pruned_match` | false | false | |

B rechnet **mehr** Integrationen (2,49 Mio. vs 1,74 Mio.), aber jede einzelne ist 4,3x billiger — der Deckel `maxiters_solve = 20.000` und die Divergenzschwelle 1e6 greifen genau bei den Ausreissern. Sichtbar im Log: Level 16 von A kostete 1054 s, davon 1045 s (99 %) im Solver, mit 112 Solves im Millionen-Schritt-Limit.

**Sauberster Einzelvergleich:** Stage 2, in beiden Faellen exakt 8 Level — A 2937,9 s, B 297,1 s, **Faktor 9,9x**. Stage 2 sind die selbst-quadratischen Terme; die erzeugen Blow-up-Dynamik, und genau dort zahlt der ungedeckelte Referenzpfad.

**Regressionsnachweis, mit Nebenbefund:** A liefert Loss `0.001391623174905009` — **bit-identisch zu Baseline v0**. v0 brauchte dafuer 30 Level und 3,0 h und lief bis Stage 5; A erreicht denselben Loss in 18 Leveln und 53,7 min bei Stage 3. **Die Level 19–30 in v0 haben rund 2,1 h gekostet und den Loss um exakt null verbessert.** Die Overshoot-Diagnose vom Vormittag ist damit an einer Einzelzelle direkt belegt.

**Determinismus bestaetigt:** `optimizer_safety_limit_hits = 0` in beiden Faellen, die Wall-Clock-Notbremse hat nie gegriffen. Beobachtete Retcodes: Solver `{Success, Unstable, MaxIters}`, Optimierer `{Success, Failure}`.

**Entscheidende Zahl fuer die naechste Stufe:** 95 % der Laufzeit von A liegen in der ODE-Integration, der Overhead ausserhalb betraegt 153 s. Ein Screening ohne Integration in der Suchschleife (ableitungsbasiertes Kriterium, Maschinerie in `pretune.jl` vorhanden) hat auf dieser Zelle eine Obergrenze von **~21x** gegenueber A — gegenueber den 2,71x, die Solver-Tuning gebracht hat. Solver-Tuning ist damit ausgereizt; der Groessenordnungssprung liegt allein in der Reduktion der Anzahl Integrationen.

**Vorbehalte:** n = 1 Zelle, 1 Seed. B ist kein freier Speedup, sondern eine andere Suche (`structure_changed = true`, abweichende Stage-Trajektorie: A 9/8/1 Level in Stage 1/2/3, B 4/8/4/2). Keiner der beiden Faelle findet die korrekte Struktur.

<!-- be9046e -->

### WP-P1c umgesetzt und reviewt — erste Messdaten, Kostentreiber identifiziert

Committet `434a8a7`. Umsetzung korrekt: Level-Budget 18, Kosten pro Level aus dem `level_log` statt aus der Gesamtzeit, erstes Level ausgeschlossen, Mittelwert **und** Median, Per-Level- und Per-Stage-Aufschlüsselung in JSON und Textausgabe. Verifikationslauf auf System 3 durchgeführt.

**Regressionsnachweis:** Fall A liefert auf System 3 Seed 42 Loss `2.663641831768419e-10` — **bit-identisch zu Baseline v0**, bei gleicher `final_stage` 3. Der Referenzpfad ist nach WP-P1/P1b/P1c unverändert.

**Determinismus empirisch bestätigt:** `total_optimizer_safety_limit_hits = 0` und `total_step_limit_solves = 0` in beiden Fällen. Die Wall-Clock-Notbremse hat nie gegriffen, das Solver-Schrittlimit ebenfalls nicht. Beobachtete Retcodes: Solver `{Success, Unstable}`, Optimierer `{Success, Failure}`. `Failure` trat bei 95 von 210 Fits auf — unter der alten Teilstring-Logik wären das alles fälschlich „Iterationslimit"-Treffer gewesen; M1 war ein realer Defekt.

**Befund — die Kopfzahl „Speedup 1,032x" ist strukturell irreführend.** A und B terminieren bei unterschiedlicher Levelzahl (A: 10, B: 12), weil die gröberen Screening-Fits die Plateau-Erkennung verschieben. Das Verhältnis der Gesamtlaufzeiten ist damit kein Kostenverhältnis. Level für Level bei gleicher Stage:

| Level | Stage | A | B | Faktor |
|---|---|---|---|---|
| 2–4 | 1 | 3,5–4,2 s | 1,6–2,2 s | 1,6–2,6× |
| 5–8 | 2 | 44–77 s | 11–48 s | 1,4–4,2× |
| 9–10 | 3 | 16–19 s | 32–35 s | nicht vergleichbar (Läufe divergiert) |

Auf den vergleichbaren Leveln ist B also **1,4–4,2× schneller**. Mechanismus sichtbar: in A sind die Level 1–4 mit null verworfenen Solves durchgelaufen, in B wurden dort je 780–1260 Solves über `unstable_check` früh abgebrochen (Schwelle `divergence_limit = 1e6`). Die Kopfzahl im `summary.txt` sollte künftig auf Per-Level-Basis stehen; da Per-Level- und Per-Stage-Daten in der JSON liegen, ist der Vergleich nachträglich rekonstruierbar — kein Blocker für den System-26-Lauf.

**Wichtigster Befund — der eigentliche Kostentreiber ist die Zahl der Integrationen, nicht die Stage.** Für 210 Parameter-Fits fielen **1,53 Mio. ODE-Solves** an, also **~7.300 Solves pro Fit** (B: ~5.500). Erwartbar wären bei `maxiters = 200` und Finite-Differenzen über 3–6 Parameter etwa 800–1.400; der Rest geht auf Gradientenauswertung und Line-Search. Anteil der Solve-Zeit an der Gesamtlaufzeit: A 74 %, B 66 %.

**Konsequenz:** Solver-Tuning allein kann höchstens den Faktor ~3,4 heben (mehr ist der Solve-Anteil nicht). Der Sprung um Größenordnungen ist nur über eine Reduktion der *Anzahl* Integrationen erreichbar — also über das ableitungsbasierte Screening-Kriterium (bisher als WP-P2 zurückgestellt), das die Integration in der Suchschleife ganz ersetzt. Das ist nach dem System-26-Lauf zu entscheiden.

<!-- 434a8a7, 807e828 -->

### WP-P1b reviewt — Code korrekt, Messaufbau greift zu kurz; WP-P1c beauftragt

Committet `268dc41`. Alle fünf Review-Punkte aus WP-P1b sind sauber umgesetzt: `screening_optimizer` in `EvoGrowV3` inkl. Brücke, eigener Suchschleife und vollständig gespiegelter Instrumentierung; `screening_budgets_active` kommt jetzt aus dem Meta, mit hartem Fehler bei fehlendem Feld statt stillem Default. Frühe Verwerfung über `unstable_check` (Abbruch) statt `isoutofdomain` (Schritt-Ablehnung), Prädikat `_state_exceeds_limit` allokationsfrei elementweise. Nicht-endlich-Verwerfung hinter `reject_nonfinite` gelegt, Zähler bleibt unbedingt — Default-Pfad damit wieder verhaltensgleich. Retcode-Kategorien über Enum-Vergleich mit eigener `:unknown`-Kategorie; alle 14 referenzierten `SciMLBase.ReturnCode`-Member gegen die aufgelöste Version 2.128.0 geprüft, alle vorhanden.

**Neuer Befund — 12 Level messen am Problem vorbei.** Level-aufgelöste Nachrechnung des v0-Logs für System 26 Seed 42: bis Level 12 kostet die Zelle **1,6 min**. Der Ausbruch beginnt danach — Level 13: 147 s, Level 14: 878 s, Level 16: 611 s, Level 19: 1484 s; bis Level 18 kumuliert 39,7 min (Stage 3 beginnt), bis Level 20 66,2 min. Der Benchmark hätte also ausschließlich den billigen Bereich vermessen und zwischen A und B praktisch keinen Unterschied gezeigt. Der Richtwert „12" stammt aus meiner WP-P1b-Spec und war ohne diese Auflösung gewählt. Korrektur auf **18 Level** (≈ 40 min für Fall A, erfasst Level 13–17 und erreicht Stage 3).

**Zweiter Befund — JIT-Warmup verzerrt gegen B.** `cost_per_level_s` wird aus der Gesamtlaufzeit geteilt durch Levelzahl gebildet. Seit WP-P1b läuft Fall B zuerst und trägt damit die gesamte Kompilierzeit des `discover`/BFGS/Solver-Pfads — also ausgerechnet der Fall, der schneller sein soll. Die Per-Level-Zeiten liegen im `level_log` bereits vor; die Kennzahl muss von dort kommen, erstes Level ausgeschlossen, zusätzlich Median (Verteilung stark rechtsschief).

**WP-P1c beauftragt:** Level-Budget 18, Kosten pro Level aus dem `level_log` inkl. Median, Per-Level- und Per-Stage-Aufschlüsselung in die Ausgabe (damit das Ergebnis mit der Baseline-Tabelle vergleichbar ist). Verifikation nur auf System 3; System 26 bleibt dem externen Lauf vorbehalten.

<!-- 268dc41, 864c9d3 -->

### WP-P1 umgesetzt und reviewt — drei Blocker, WP-P1b beauftragt

Codex hat WP-P1 umgesetzt (`911a567`, enthält versehentlich auch die WP-P1b-Spec): `BFGSOptimizer` um deterministische Budget-Parameter und `reject_nonfinite`/`divergence_limit` erweitert, Zähler pro Level (Fits, Solves, invalid/diverged/nonfinite, Optimizer-Limit-Treffer, Solve- vs. Overhead-Zeit) über EvoGrow-Meta bis in den Record durchgereicht, expliziter Referenz-Optimizer im Regression-Runner (`time_limit_s = 86_400`), Mikro-Benchmark `studies/profiling/profile_eval_cost.jl`. Instrumentierung sauber und vollständig verdrahtet; Fingerprint korrekt erweitert; Profiling-Skript verschmutzt `history.jsonl` nicht.

**Review — drei Blocker:**

1. **v3 ignoriert die Screening-Budgets, Records sind falsch etikettiert.** `EvoGrowV3` hat kein `screening_optimizer`-Feld (der Runner übergibt ihn an einen ungenutzten Parameter) und wertet in seiner eigenen Suchschleife immer mit dem Referenz-Optimizer aus. Bei aktivierten Budgets liefen v2.2 und v3 damit unter verschiedenen Budgets → Anker-Vergleich wertlos. `screening_budgets_active` wird zudem aus dem ENV-Flag statt aus dem Meta geschrieben, und die 11 Instrumentierungsfelder sind bei v3 alle `nothing`. Ursache war meine eigene Spec-Formulierung („evogrow_v3.jl nicht anfassen") — gemeint war das Lockstep-Verhalten, nicht ein Durchreich-Parameter.

2. **`isoutofdomain` ist das falsche Primitiv.** Belegt in `OrdinaryDiffEqCore/.../integrator_utils.jl:268-286`: `isoutofdomain == true` setzt `accept_step = false` → Schritt verwerfen, `dt` verkleinern, erneut versuchen, bis `maxiters`/`dtmin`. Kein Abbruch. Das Abbruch-Primitiv ist `unstable_check`, dessen Default (`DiffEqBase/common_defaults.jl:110-120`, `INFINITE_OR_GIANT`) bereits `any(!isfinite, u)` prüft — die Nicht-endlich-Erkennung war also ohnehin aktiv, über den richtigen Mechanismus. Neu ist allein die endliche Schranke. Netto verteuert die Änderung genau die divergierenden Kandidaten, die sie billiger machen sollte. Zusätzlich alloziert die Prüf-Closure zwei temporäre Arrays pro Schritt im Hot Path.

3. **Der „Mikro"-Benchmark ist nicht mikro.** Fall A ist System 26 / Seed 42 / 30 Level — die 3-h-Zelle aus Baseline v0, damals *mit* der 300-s-Bremse, die laut v0-Log regelmäßig griff (~400 s/Fit auf teuren Leveln). Mit `maxiters = 200` und `maxiters_solve = 10^6` gibt es keine deterministische Obergrenze für einen einzelnen Fit.

**Weitere Befunde:** (S1) `_predict_traj` und `simulate` verwerfen nicht-endliche Lösungen jetzt unbedingt, auch bei `reject_nonfinite = false` — vorher lief eine Success-Lösung mit `Inf` durch (die Prüfung greift nur bei NaN) und ergab Loss `Inf`; stilles Verhaltens-Delta im Default-Pfad. (S2) Der Determinismus-Fix ist lokal: Struct-Default `time_limit_s = 300.0` unverändert, `benchmark_evogrow.jl`, `experiments/run_experiment.jl` und die übrigen Studies konstruieren weiter ohne expliziten Wert — **der in CLAUDE.md eingefrorene Paper-1-Pfad bleibt wall-clock-abhängig und muss vor Phase B entschieden werden.** (M1) Die Notbremse wird per Teilstring `"time"` im Retcode erkannt; ein abweichender Retcode würde einen ausgelösten Bremseingriff still als Iterationslimit verbuchen. (M2) In Fall B werden die Parameter nie auf Referenz-Fidelity nachgefittet (`discover()` refittet nur bei Parameteranzahl-Mismatch) — Interpretationsvorbehalt.

**WP-P1b beauftragt:** Punkte 1–3 plus S1, M1; S2 nur dokumentieren, nicht umstellen. Benchmark erst danach starten.

<!-- 911a567, 4fb4508 -->

### Volllauf abgebrochen — Kostendiagnose: 62 % der Rechenzeit oberhalb der nötigen Stage

Der Volllauf wurde bei 23/30 Zellen abgebrochen (v2.2 komplett 15/15, v3.2 bei 8/15), nach **40,5 Compute-Stunden**. Daten gesichert (`a69637a`). Grund: Laufzeit inakzeptabel (mehrere Tage), Restlaufzeit ~26–30 h für Zellen mit nahezu null Informationswert (v3.2 ist die Lockstep-Brücke; Äquivalenz war bereits beantwortet).

**Befund 1 — Anker bestätigt, mit einer Ausnahme.** v2.2 == v3.2 bit-identisch in 7 von 8 überlappenden Zellen. Abweichung nur System 26 Seed 123 (1.3916e-3 vs. 1.3713e-3).

**Befund 2 — Ursache ist ein Reproduzierbarkeitsleck, kein v3-Bug.** `run_regression.jl` baut `BFGSOptimizer(maxiters=BFGS_MAXITERS)`; `time_limit_s` bleibt beim Default **300 s Wall-Clock** (`bfgs.jl:29`) und wird an Optim.jl durchgereicht. Damit hängt die Zahl der BFGS-Iterationen von der Maschinenlast ab → Ergebnisse sind nicht reproduzierbar. Dieselbe Zelle brauchte 13.352 s (v2.2) vs. 20.158 s (v3.2). Muss für Paper 1 ohnehin weg.

**Befund 3 — Kostenprofil (aus `run.log` rekonstruiert, alle 23 Zellen).** Kosten pro Level explodieren mit der Stage:

| Stage | Level | Zeit | Anteil | s/Level |
|---|---|---|---|---|
| 1 | 124 | 0,7 h | 1,9 % | 21 |
| 2 | 129 | 6,1 h | 16,3 % | 170 |
| 3 | 94 | 11,6 h | 30,9 % | 443 |
| 4 | 55 | 7,4 h | 19,7 % | 482 |
| 5 | 48 | 11,7 h | 31,3 % | 878 |

Ein Stage-5-Level kostet das **42-fache** eines Stage-1-Levels. Pro Zelle oberhalb der erwarteten Stage aufsummiert: **24,9 von 40,5 h = 62 % der gesamten Rechenzeit wurden in Komplexität investiert, die die Systeme nie gebraucht haben.** Auf gekoppelten Systemen liegt der Anteil bei 38–80 %. Extremfall System 63 Seed 123: 8,4 h, davon 6,7 h verschwendet; ein einzelnes Level (16, Stage 4) kostete 3,4 h.

**Konsequenz:** Laufzeitproblem und Gate-1-Failure-Mode sind **dasselbe Problem**. Die Suche läuft über die nötige Stage hinaus, und jede zusätzliche Stage ist überproportional teurer (Stage 4/5 = kubisch/trigonometrisch → steife und divergierende Kandidaten-ODEs → Solver kriecht bis ins 300-s-Limit). Bei ~619 s pro Kandidat auf den teuersten Levels laufen einzelne Fits sicher ins Wall-Clock-Limit.

**Blocker für Phase B:** 63 Systeme × 2 Bedingungen × 3 Seeds = 378 Runs, davon 240 gekoppelt. Bei ~3,5 h pro gekoppelter Zelle > 800 h ≈ 5 Wochen durchgehend — und das Set enthält mehr 3D/4D als das Testset. **Phase B ist mit dem aktuellen Kostenprofil nicht durchführbar.** Muss vor WP-v3.3 gelöst werden.

Zwei getrennte Hebel, multiplikativ:
- **A (Overshoot, 62 %):** Promotionsdisziplin — genau das, was v3 leisten soll. Forschungsarbeit, bereits geplant.
- **B (Kosten pro Auswertung):** EvoODE bewertet jeden Kandidaten per voller Trajektorien-Simulation (bis 200 BFGS-Iterationen × ODE-Solve mit `maxiters_solve=10^6`, Toleranz 1e-9). SINDy/GP scoren auf Ableitungsresiduen statt zu integrieren — daher der Kostenunterschied. `pretune.jl` enthält die Maschinerie (finite Differenzen → Design-Matrix → lineares LS) bereits, nutzt sie aber nur als Warmstart, und im Regression-Config ist sie mit `USE_PRETUNING=false` ganz abgeschaltet.

Reihenfolge geändert: **WP-P1 vor WP-v3.3.**

**WP-P1 beauftragt** (`2bd9463`): Determinismus (kein Wall-Clock im Ergebnispfad), getrennte Budgets für Screening während der Suche vs. finale Validierung (Defaults = heutige Werte, kein stilles Verhaltens-Delta), Instrumentierung pro Level (Fits, Solves, verworfene Solves, Zeitanteil Optimierung vs. Simulation), sowie ein Pflicht-Mikro-Benchmark über genau eine Zelle (System 26, Seed 42) mit A/B-Vergleich. Ausdrücklich nicht in WP-P1: ableitungsbasiertes Screening-Kriterium, `use_pretuning`, Parallelisierung, WP-v3.3, WP-H2.

<!-- a69637a, 2bd9463 -->

---

## 2026-07-20

### WP-H1d umgesetzt und reviewt — Resume grün

Codex hat Resume umgesetzt: `load_completed_cells(fingerprint)` liest `history.jsonl` (try/catch pro Zeile), sammelt erfolgreiche `(variant, system_id, seed)`-Zellen bei passendem `config_fingerprint` und `error===nothing`; Skip in der Schleife (äußerer Balken tickt, Skip-Zeile in `run.log`, kein Record). `FRESH=1`-Override, End-Report. Fingerprint/Schema/Metriken unverändert. Committet `488fa1d`. Review: korrekt und spec-konform. Da die 7 geretteten Records `config_fingerprint=0c739d4e36ee6498` tragen und die Config unverändert ist, überspringt der Neustart sie und macht bei System 26 Seed 123 weiter. Grünes Licht für den Neustart erteilt.

<!-- 488fa1d, a298329 -->

### Volllauf durch Rechner-Neustart abgebrochen (7/30 gerettet); WP-H1d Resume beauftragt

Der externe Volllauf (Commit 776d2f0) wurde durch einen unerwarteten Rechner-Neustart abgebrochen. Dank append-only `history.jsonl` **7 von 30 Records gerettet** (alle v2.2: System 3 alle Seeds, System 11 alle Seeds, System 26 Seed 42 — der ~3-h-Lauf). In Git gesichert (`6420953`). Verloren: v2.2 System 26 Seeds 123/7, System 31, System 63, sowie ganz v3.

Nebenbefund aus den geretteten Daten: System 26 v2.2 Seed 42 → `pruned_match=false`, Overshoot Stage 5, Loss 1.4e-3 — bestätigt den Gate-1-Failure-Mode am Volllauf. Baseline, die v3.4 schlagen muss.

**WP-H1d (Resume) beauftragt** (`5ea632c`): Runner überspringt beim Neustart alle erfolgreichen (variant, system, seed)-Zellen desselben `config_fingerprint` (Skip keyed auf Fingerprint+Zelle+`error==null`, NICHT git_hash — sonst würden die 776d2f0-Records nicht erkannt). Fingerprint bleibt über volle Config berechnet; manuelles Kürzen der Systemliste ginge nicht (würde Fingerprint entwerten). Resume auch als Härtung gegen künftige Abbrüche. Ein resumeter Baseline-Lauf darf mehrere git_hashes umfassen (Config identisch, akzeptiert).

<!-- 6420953, 5ea632c, 55a6670 -->

### WP-H1c umgesetzt und reviewt

Codex hat den inneren Live-Balken verdrahtet: VARIANTS-Konstruktoren nehmen `level_callback`, `run_one` erzeugt einen inneren `Progress` (offset 1, total = min(N_LEVELS, max_levels)) + Callback, der pro Level `system/seed/level/stage/best_loss` zeigt; `finish!` im `finally`. Äußerer Balken offset 0. Beide auf stderr → `redirect_stdout(devnull)` hält Per-Level-Text weiter vom Schirm (nur in `run.log`). Metriken/Records/Fingerprint unverändert. Committet `9cd66e7`.

**Review:** Korrekt und spec-konform; `next!` kann total nie überschreiten (max 30 Level = total). Ein rein kosmetischer Vorbehalt, den ich nicht ohne Julia verifizieren kann: die pro-Lauf-Zusammenfassungszeile (`println(summary_line)`) wird zwischen zwei gestapelten ProgressMeter-Balken ausgegeben — das kann visuell holprig sein. Beim ersten externen Kurzlauf begutachten; falls unsauber, ist der Fix eine Zeile (auf `ProgressMeter.println` umstellen oder die Zeile weglassen, da `run.log` die Done-Zeile ohnehin hat).

<!-- 9cd66e7, 7e07cc6 -->

### WP-H1c beauftragt: innerer Live-Balken pro Lauf

Fix für die WP-H1b-Lücke (statischer Balken während eines langen Laufs). User hat „innerer Balken" gewählt. WP-H1c verdrahtet EvoGrows/EvoGrowV3s bestehenden `level_callback` (feuert pro Level mit Snapshot `level`/`stage`/`best_loss`) mit einem inneren `ProgressMeter`-Balken pro Lauf, gestapelt unter dem äußeren Balken (via `offset`). Kein src-Eingriff nötig. VARIANTS-Konstruktoren nehmen künftig ein `level_callback`-Argument. `redirect_stdout(devnull)` bleibt (Balken auf stderr, Per-Level-Detail weiter nur in `run.log`). Metriken/Records/Fingerprint/Config unverändert. Committet `429b645`.

<!-- 429b645, caa4c76 -->

### WP-H1b umgesetzt und reviewt

Codex hat das Logging umgesetzt: `ProgressMeter`-Balken (ETA + variant/system/seed) über alle Läufe, `run.log` mit Start/Finish-Markern, `[i/N]`-Zeilen und EvoGrows Per-Level-Heartbeat (Logger via `LOGGER.log_io` in Append-Modus umgeleitet). Screen minimal gehalten durch `redirect_stdout(devnull)` um `discover`. Fingerprint/Records/Config unverändert, `ProgressMeter` in `Project.toml`. Committet `af6cc6d`.

**Review-Befund (Lücke):** Innerhalb eines einzelnen Laufs geht der Heartbeat nur in `run.log`, nicht auf den Schirm — der Balken tickt erst am Lauf-Ende (`next!`). Bei einem langen Lauf (System 63: Stunden) sieht der User in der cmd also einen statischen Balken — genau das „wirkt gehängt"-Problem, das er vermeiden wollte. Fix-Vorschlag WP-H1c: EvoGrows bestehenden `level_callback` nutzen, um einen inneren Per-Level-Balken/Heartbeat live im Terminal zu zeigen (run.log-Detail bleibt). Nebenpunkt: `open_evo_logger_append!` greift direkt in `EvoODE.EvoLogger.LOGGER.log_io`, weil `set_log_file` im `"w"`-Modus truncaten würde — funktioniert, aber fragil; sauberer wäre ein `append`-Flag an `set_log_file`.

<!-- af6cc6d, 3c0b68f -->

### WP-H1b beauftragt: Fortschritts-Logging (tqdm-Stil)

Zweischichtiges Logging für `run_regression.jl`, damit der User externe Läufe live in der cmd verfolgen kann: **Bildschirm** = `ProgressMeter`-Balken (tqdm-Äquivalent) über N = Varianten×Systeme×Seeds mit ETA + aktuellem Item + eine Zusammenfassungszeile pro Lauf; **Datei** = `outputs/studies/regression/run.log` mit Start/Finish-Markern, `[i/N]`-Per-Run-Zeilen und EvoGrows Per-Level-Heartbeat (via `set_log_file`). Balken terminal-only (kein `\r` in die Logdatei). Prinzip „so wenig wie möglich auf dem Schirm, so viel wie nötig in der Datei". Optional: BFGS-Zeitlimit-Treffer pro Lauf als additives Feld (erklärt die Slowness). Nur Observability — Metriken/Records/Fingerprint/Config unverändert. `ProgressMeter` neu in `Project.toml`. Committet `476e192`.

<!-- 476e192, a29fdb6 -->

### WP-H1 umgesetzt und verifiziert; Julia-Läufe künftig extern

Codex hat WP-H1 geliefert: `studies/regression/{diagnostic_systems.jl, run_regression.jl, history.jsonl}`. Runner rechnet das feste Set (Systeme 3/11/26/31/63) für v2.2 und v3, hängt ein JSONL-Record pro (variant, system, seed) an `history.jsonl` an (git-Provenienz + `config_fingerprint`). Verifiziert über den echten Runner auf dem schnellen Subset (Systeme 3, 11): valides JSONL, stabiler Fingerprint, **Anker-Äquivalenz v2.2==v3 bit-genau** (System 3: identischer Loss/final_stage je Seed; v3 `eq_final_stages` gesetzt). `history.jsonl` leer committet. Committet `99393bb`.

**Laufzeit-Befund (wichtig):** Selbst das 1D-System 3 brauchte 218–1217 s pro Lauf (Stage-Overshoot → teure BFGS gegen das 300-s-Zeitlimit), System 11 nur ~3–4 s. Der Volllauf (× 26/63) ist ein Stunden-Job.

**Workflow-Entscheidung:** Julia-Läufe führt künftig der User extern durch; Claude startet in seiner Umgebung kein Julia mehr (Kompilierzeit blockiert). Konsequenz: Julia-Runner brauchen reichhaltiges, geflushtes, dateibasiertes Fortschritts-Logging (per-Run [i/N] + Timestamp + elapsed, per-Level-Heartbeat, run.log), damit externe Läufe live beobachtbar sind. Als nächste Verbesserung vor dem Volllauf. Siehe Memory `feedback_full_runs`.

<!-- 99393bb, 80cc96a -->

### Regressions-Historie beschlossen, WP-H1 beauftragt

Neue Anforderung: longitudinales Logging, um zu verfolgen, wie sich Metriken über Algorithmus-Versionen/Commits entwickeln (besser/schlechter pro System). Fehlende Achse gegenüber den bestehenden Snapshot-Logs (`run_registry.csv`, Aggregate) und dem narrativen DIARY. Scope-Entscheidung: **Medium**.

Design: festes Diagnostik-Set (Systeme 3/11/26/31/63, feste Seeds/Hyperparameter, wie `phase1_diag`) → append-only `studies/regression/history.jsonl`, ein Record pro (git_hash, variant, system, seed) mit `config_fingerprint` (Hash über metrik-relevante Config; nur innerhalb gleichem Fingerprint vergleichen) + `git_dirty`-Flag. Python-Delta-Report separat.

Aufgeteilt wegen Sprach-Deklaration pro Task: **WP-H1 (Julia)** = Runner + append-only Store (jetzt in `codex/CURRENT_TASK.md`); **WP-H2 (Python)** = Delta-Report (letzter vs. vorheriger Commit, ↑/↓/=, DIARY-fertiger Markdown-Block) als Folge-Task. Erste Baseline-Einträge: v2.2 + v3.2 (müssen laut Anker gleich sein). Bewusst *vor* WP-v3.3/v3.4 gezogen, damit jeder echte v3-Schritt ab Beginn in die Historie geloggt wird. Trigger manuell, nicht als Git-Hook (Läufe dauern Minuten bis Stunden).

<!-- a5ef98a, 1e58fd5 -->

### WP-v3.2 umgesetzt und verifiziert

Codex hat `EvoGrowV3` implementiert (`src/structure/evogrow_v3.jl`, registriert/exportiert in `src/EvoODE.jl`). Pro-Gleichung-Stage-State (`eq_stages`, `eq_levels_in_stage`, `eq_plateau_histories`, `eq_stage_histories`), Promotion aber noch Lockstep-global über einen internen `EvoGrow`-Bridge, der die v2.2-Helfer (`_validate_policy`, `_init_population`, `_stage_progression_decision`) wiederverwendet. Meta ergänzt `eq_final_stages` + `eq_stage_histories` mit `final_stage = maximum(eq_stages)`. Saubere Seams (`_lockstep_stage_progression_decision`, `_apply_lockstep_stage_update!`) für WP-v3.4.

**Regressions-Äquivalenz selbst verifiziert** (Julia-Skript, System 3 1D + System 26 2D, Seeds 42/7): identische `active_idxs`, Loss-Differenz bit-genau 0.0, `eq_final_stages` lockstep-gleich, `maximum(eq)==final_stage`. v3.2 reproduziert v2.2 (`:stage_local`) exakt — der Refactor ist neutral. Nebenbefund als Baseline: v3.2 scheitert auf System 26 genau wie v2.2 (Loss ~0.038, nur lineare Terme), was WP-v3.4 heilen soll.

Anmerkung Tech-Debt: Die ~350-Zeilen-Hauptschleife ist eine Kopie des v2.2-Loops (unvermeidbar unter „evogrow.jl nicht anfassen"). Nach Gate 2 faktorisieren oder v2.2-Loop stilllegen.

<!-- 559d3b7, f9802b3 -->

### WP-v3.1 geliefert, WP-v3.2 beauftragt

Codex hat **WP-v3.1** umgesetzt: `docs/evogrow_v3_design.md` friert das v3-Design ein — pro-Gleichung-Stage-State (`eq_stages` statt globalem `current_stage`), Ableitungs-Residuum `r_k` als pro-Gleichung-Progress-Signal (auf beobachteter Trajektorie), Promotion-Regel mit Residuum-über-Ziel-Guard (bereits erklärte Gleichungen promoten nicht), gleichungs-bewusste Child-Generation, Warm-Start-Übernahme, neue pro-Gleichung-Metriken. Vier offene Fragen mit empfohlenen Auflösungen. Committet.

**WP-v3.2 als nächsten Codex-Task formuliert** (`codex/CURRENT_TASK.md`): neuer `EvoGrowV3`-Struct + gleichungsweiser Stage-State als lauffähiges Refactor. Bewusst enger Scope — Promotion bleibt vorerst Lockstep (alle Gleichungen gemeinsam), sodass `EvoGrowV3` v2.2 (`:stage_local`) exakt reproduziert. Das dient als **Regressions-Anker**: spätere Divergenz ist dann eindeutig den gleichungs-lokalen Mechanismen (WP-v3.3 Child-Generation, WP-v3.4 Residuum-Signal + pro-Gleichung-Promotion) zuzuordnen, nicht dem Refactor. Verifikation: Struktur-/Loss-Identität v3 vs. v2.2 auf System 3 und 26.

<!-- f9567b5, 10ef90f, 4f78d20 -->

### Status-Abgleich und Housekeeping

Statusprüfung der vier offenen Punkte aus den „Current Priorities". Ergebnis: CLAUDE.md war veraltet (Stand 2026-05-11), `PAPER_1.md` ist die aktuelle Wahrheit.

- **WP-0.1** (H4-Verdict → VACUOUS in `evaluate_hypotheses.py`): bereits erledigt, Commit `a199128` (2026-05-17). Die `vacuous`-Prüfung setzt das Verdict korrekt, das Freeze Memo schreibt „C3 cannot be evaluated".
- **WP-0.2** (Generalization-Pfad): bereits erledigt (2026-05-17). Config zeigt korrekt auf `debug_results/generalization_summary.csv`.
- **WP-v3.1** (Design Note `docs/evogrow_v3_design.md`): aktiver Codex-Task in `codex/CURRENT_TASK.md`, Deliverable noch nicht geschrieben. Das ist der reale aktuelle Arbeitspunkt.
- **Phase B**: nicht begonnen, erst nach Gate 2.

**CLAUDE.md synchronisiert:** „Current Priorities" und „Active WPs" auf Phase 2 / WP-v3.1 aktualisiert, erledigte WPs markiert. Fehl-Label korrigiert: der frühere „Phase 2"-Prioritätspunkt (R²/Protocol-Audit) ist laut `PAPER_1.md` eigentlich Phase 3.

**Untracked Runner committet:** `studies/phase1_diag/run_phase1_diag.jl` (WP-1.3-Diagnostik, Gate-1-Evidenz) war nie eingecheckt — jetzt nachgeholt.

<!-- 7f29a02, eae3e2c, e819afb -->

---

## 2026-05-30

### WP-1.3 Ergebnisse und Gate-1-Entscheidung

Phase-1-Diagnostik-Runs abgeschlossen: 15/15 JSON-Dateien in `outputs/studies/phase1_diag/`. Konfiguration: EvoGrow v2.2 stage_local, `use_pretuning=false`, `n_levels=30`, 3 Seeds je System.

**Kontrollsysteme:**

- System 3 (Logistic): `pruned_match=true` alle 3 Seeds, Loss ~7e-10. Stage-Overshoot 0–3 (Mindestbudget-Effekt). Fit-Qualität gut, kein Strukturproblem.
- System 11 (Cubic `du=-u³`): `pruned_match=true` alle 3 Seeds, Loss ~4e-15, Stage 4/4, Laufzeit ~1.3s. Metrik-Artefakt aus WP-1.2 vollständig geheilt — der Pruning-Fix funktioniert.

**Problemsysteme:**

- System 26 (Lotka-Volterra 2D): `pruned_match=false` alle 3 Seeds, Loss ~5e-4–1.4e-3, Stage 5/3, Laufzeit 2800–9400s. Gefundene Struktur: `du1 = (5.05)*u1 + (-3.87)*u1*u2`, `du2 = (1.13)*u1 + (-1.80)*u1^2` — Terme komplett falsch. Loss platzt in Stage 3 auf ~1e-3, danach keine Verbesserung trotz Eskalation bis Stage 5 (Trig-Terme nutzlos).
- System 31 (SIR 2D): Seed 42 erreicht Loss ~7e-11 (nahezu perfekt), aber `pruned_match=false` wegen Spurious-Term `0.0022*u1` — Pruning-Schwellenwert `1e-3 × max_coeff = 4e-4 < 0.0022`, Term überlebt. Seeds 123/7: Stage 5/3, Loss ~1e-4–7e-5, echter Fehler.
- System 63 (SEIR 4D): `pruned_match=false` alle 3 Seeds, Loss ~9e-4–1.8e-3, Stage 5/3, Laufzeit 11000–31000s. Konsistentes Scheitern.

**Strukturdiagnose:** Der systemweite Staging-Mechanismus von v2.2 zwingt alle Gleichungen gemeinsam in höhere Stages, sobald der globale Progress stagniert. Auf System 26 findet der Algorithmus in Stage 3 keine verwertbaren Cross-Terme, promotiert dann global zu Stage 4 (kubische Terme) und Stage 5 (Trig), obwohl keine Gleichung Trig-Terme benötigt. Das ist kein Metrik-Fehler — es ist eine echte algorithmische Schwäche des systemweiten Staging.

**Nebenbeobachtung System 31 Seed 42:** Pruning-Schwellenwert 1e-3 × max_coeff könnte für BFGS-konvergierte Modelle zu streng sein. Der Term 0.0022*u1 ist klein aber nicht null. Zu re-evaluieren nach v3-Validierung.

**Gate-1-Entscheidung: v2.2 ist NICHT paper-ready. Phase 2 (EvoGrow v3) wird ausgelöst.**

Begründung: Der Failure-Mode auf Systems 26 und 63 ist klar auf systemweites Staging zurückführbar, nicht auf Metrik-Fehler oder Parameter-Fitting. Das ist genau die Bedingung, unter der v3 (gleichungsweises Staging) motiviert ist.

WP-v3.1 (Design Note) als nächsten Codex-Task formuliert.

<!-- f5e7033 -->

---

## 2026-05-17

### Strategischer Pivot: Paper 1 Neufokus

Paper 1 wird kein Pretuning-Vergleichspaper. Pretuning wird für Paper 1 vollständig deaktiviert und als mögliches Follow-up-Paper zurückgestellt.

**Neue wissenschaftliche Kernfrage:**
> Ist inkrementelles, gestuftes Wachstum ein effektiver Suchmechanismus für interpretierbare ODE-Entdeckung — und wo hilft es, wo versagt es?

**Phase A Neubewertung:** H1/H3 PARTIAL war kein schlechtes Ergebnis, sondern ein diagnostisches Signal. System-weites Staging ist möglicherweise zu grob für mehrdimensionale Systeme (26, 31, 63). Das ist der algorithmische Befund, dem das Paper nachgehen muss.

**Neues Experiment-Design:** 63 ODEBench-Systeme × 1 finaler EvoGrow-Variant × 3 Seeds = 189 Runs. Keine externen Baselines in-house; publizierte ODEBench-Zahlen als Referenzkontext.

**Gate-Struktur eingeführt:**
- Gate 1: Ist v2.2 nach Metric-Repair paper-ready? (Phase 1 Diagnose)
- Gate 2 (nur falls nötig): Ist v3 (gleichungsweises Staging) paper-ready?

`PAPER_1.md` vollständig neu geschrieben. WP-0.2 als erledigt markiert.

<!-- fb549af -->

## 2026-05-11

### H1–H4 Auswertung und Freeze Memo (Step 2)

Codex hat `evaluate_hypotheses.py` implementiert und die formale Hypothesenauswertung auf `paper1_phaseA_v1` (300/300 Runs) durchgeführt. Ergebnisse ins Freeze Memo (`docs/paper1_freeze_memo_phaseA.md`) und Diagnostics JSON (`analysis/data/paper1_phaseA_v1/h1_h4_diagnostics.json`) geschrieben.

**Verdicts:**
- **H1** (Stage Overshoot Reduction): PARTIAL — korrekte Richtung nur auf System 54 (Lorenz), 1 von 6. Systeme 3, 11, 26, 31, 63 zeigen kein Signal oder falscher Trend. Ursache: Mindestbudget pro Stage erzwingt mehr Levels auf einfachen Systemen.
- **H2** (Competitive Recovery Quality): SUPPORTED — 7 von 8 Systemen kompetitiv (exact_match oder mean_loss). Nur System 11 nicht kompetitiv.
- **H3** (Wasted Levels Reduction): PARTIAL — korrekte Richtung nur auf Systemen 11 und 54, 2 von 6.
- **H4** (Usage Policy Effect): SUPPORTED (vakuös) — alle Policy-Varianten zeigen exact_match=0 auf Stage-≥3-Systemen, erwartete Ordnung `hard ≥ soft ≥ passive` daher nicht unterscheidbar.

**Design-Entscheidungen dokumentiert:**
- `exact_support_match` als striktes Binary-Metrik ohne Schwellenwert ist korrekt und bleibt unverändert
- System 11 (`du=-u³`): EvoGrow findet Struktur mit loss ~4e-15, aber growth-without-pruning akkumuliert Null-Terme → kein exact_match. Echter algorithmischer Mangel, kein Metrik-Fehler. Muss im Paper explizit genannt werden.
- Generalisierungsstudie: keine förderfähigen Zellen (n_exact_runs < 3), bleibt im Supplementary.

### Repo Readiness Review und Cleanup

Vollständiges Repo-Review vor nächster Implementierungsphase. Alle gefundenen Issues behoben:

- `codex/CURRENT_TASK.md`: abgeschlossenen Step-2-Task gelöscht, "Kein aktiver Task" gesetzt
- `CLAUDE.md`: veraltete Abschnitte (242/300 Befunde, Active Studies 2026-04-29, Current Priorities 2026-04-29, Known Gaps) auf aktuellen Stand 2026-05-11 gebracht
- `analysis/CONVENTIONS.md`: gebrochene Referenz `CURRENT_TASK_ANALYSIS.md` → `CURRENT_TASK.md` korrigiert (Datei existiert nicht)
- `docs/paper1_study_protocol.md`: als Phase-A-Archivdokument markiert, nicht mehr aktives Protokoll
- `analysis/configs/paper1_phaseA_v1.json`: Generalisierungspfad von `outputs/studies/generalization/` → `debug_results/` korrigiert (WP-0.2)

Abschließende Verifikation: `debug_results/generalization_summary.csv` und `generalization_detail.csv` existieren — WP-0.2 damit vollständig erledigt.

Offener Rest: WP-0.1 (H4-Claim-Korrektur in `evaluate_hypotheses.py`) — wird morgen als Codex-Task formuliert. Das ist der einzige noch ausstehende Punkt vor dem endgültigen Abschluss von Phase A.

<!-- b4c1cce, 5f5fc43 -->

### Strategische Neuausrichtung: Paper 1 Roadmap

ODEBench-Paper (d'Ascoli et al. 2023, 2310.05573) analysiert: EvoODE verwendet dieselben 63 Strogatz-Systeme mit identischen ICs (alle 8 exakten Systeme verifiziert). Baseline-Strategie: veröffentlichte ODEBench-Zahlen direkt zitieren (σ=0, ρ=0 Regime), R²-Metrik aus existierenden Trajektorien berechnen.

**Strategie:** EvoODE konkurriert nicht mit ODEFormer (50M Training-Beispiele, A100), sondern mit SINDy(poly) und PySR (~35–50% Accuracy bei σ=0). EvoGrow v3 (gleichungsweise gestufte Promotion) als nächste Variante geplant.

`PAPER_1.md` komplett ersetzt durch detaillierten Ausführungsplan: Phasen 0–5, WP-Aufschlüsselung, EvoGrow v3 Design-Spec, Risikoregister, eingefrorene Baselines.

`CLAUDE.md`: neuer Abschnitt "Paper 1 — Execution Roadmap" als Pointer auf `PAPER_1.md`.

---

## 2026-05-08

### paper1_phaseA_v1 vollständig abgeschlossen

`experiments/run_experiment.jl paper1_phaseA_v1` hat alle 300 Runs durchlaufen (300/300, alle `success=true`, 0 failed, 0 interrupted). Laufzeit ca. 4.5 Tage.

Aggregation: `julia experiments/aggregate.jl paper1_phaseA_v1` → `run_registry.csv` (300 Zeilen).
Python-Pipeline: `aggregate_run_registry.py` → `data/paper1_phaseA_v1/aggregate_by_variant_system.csv` (60 Zeilen, 6 Varianten × 10 Systeme, alle Zellen vollständig).

### Erste vollständige Auswertung: paper1_phaseA_v1

**Exact Match (Kernbefunde):**

- Systeme 2, 3, 24: alle EvoGrow-Varianten `exact_match=1.0`, GP auf System 24 `exact_match=0` (loss ~4.5e-3 vs. EvoGrow 5.4e-14 — dramatischer Unterschied auf simpelstem 2D-linearem System)
- System 11 (cubic, `du=-u³`): alle EvoGrow `exact_match=0` trotz loss ~4.4e-15 — Bug in `exact_support_match` vermutet; GP `exact_match=1.0`
- Systeme 26, 31, 54, 63: `exact_match=0` für alle Varianten — kein exakter Strukturfund auf Stage-3-Systemen

**Loss EvoGrow vs. GP (höherdimensionale Systeme):**

| System | Beste EvoGrow | GP | Faktor |
|--------|--------------|-----|--------|
| 31 SIR | 7.0e-05 | 0.314 | ~4.500× |
| 54 Lorenz | 7.4e-04 | 0.921 | ~1.200× |
| 26 Lotka-Volterra | 2.5e-04 | 2.98e-03 | ~12× |

GP versagt auf gekoppelten Systemen deutlich — stärkstes Argument für EvoGrow.

**Stage Overshoot (Kernhypothese):**

- **System 54 (Lorenz):** v1=+2, v2.1=+1.6, alle v2.2=0 Overshoot, 0 Wasted Levels → sauberste Bestätigung der Kernhypothese
- **System 3 (Logistic):** v1=0 (flache Basis, keine Stage-Promotions), alle v2.x=+3 Overshoot — v2.2_stage_local verschärft wasted_levels auf 12 durch Mindestbudget
- **Systeme 26, 31, 63:** alle Varianten +2 Overshoot — kein Differenzierungssignal

**Offene Fragen:**
- `exact_support_match`-Bug bei System 11 untersuchen (loss ~0 aber kein Match)
- Warum GP auf System 24 (harmonic oscillator) so schlecht?
- Für keine Stage-3-Systeme exact match → algorithmisches Problem oder Loss-Tol-Problem?
- Kein Run konvergiert auf `loss_tol=1e-8` außer System 2/24 → Stopp-Mechanismus greift nie als Loss-Stopp

### WP3: Frame Layout Redesign (search_animation.jl)

Zweispalten-Layout für `render_frame`: linke Spalte = Trajektorien-Subplots, rechte Spalte = Info-Panel (Loss, entdeckte Gleichungen, wahre Gleichungen, farbige Legende). Aktuelle Level-Kandidaten in Orange, Historie in Grau. `plot_title` über allen Subplots. `structure_to_string` Koeffizientenformat auf `%.3f` geändert.

---

## 2026-05-05

### WP11: CairoMakie-basiertes `render_frame` (Spec + Abhängigkeit)
`ac7658f`

Codex-Spec für WP11 geschrieben: vollständiger Neubau von `render_frame` auf Basis von CairoMakie statt Plots.jl. Ziel ist pixel-genaue Kontrolle über Layout und Typography für Publikationsqualität.

CairoMakie als Abhängigkeit in `Project.toml` aufgenommen. Bestehende `search_animation.jl` bleibt unverändert, bis WP11 implementiert ist.

---

## 2026-05-04

### Animationspipeline: WP4–WP8 (Live-Rendering, Layout, Typography)

**WP4 — Live-Frame-Rendering via `level_callback`** (`2e31f2e`):
`level_callback`-Hook in EvoGrow eingebaut, der am Ende jedes Levels aufgerufen wird. Frame wird direkt während des Runs gerendert und gespeichert — kein Post-Hoc-Rendering mehr nötig.

**WP5 — Horizontale Balken im Info-Panel** (`8e46613`):
Frame-Layout auf horizontale Balken pro Kandidat umgestellt (Trajektorie-Panel links, Loss-Rang-Balken rechts). Verbesserte Lesbarkeit auf Stage-Promotions-Grenzen.

**WP6 — Stage-Grammar-Anzeige in der Gleichungsleiste** (`92f892e`):
Aktuell freigeschaltete Stage-Terme werden in der Gleichungsanzeige farblich hervorgehoben. Neue Terme (neu in dieser Stage) vs. ältere Terme visuell unterscheidbar.

**WP7 — Typografie-Refaktor** (`a496f94`):
Schriftgrößen, Zeilenabstände und Gewichtungen vereinheitlicht. Koeffizientenformat auf `%.3g` geändert (keine führenden Nullen mehr). Gleichungszeilen kürzer und lesbarer.

**WP8 — Header/Meta-Verfeinerung** (`c0f12ca`):
Titel-Header zeigt: System-Name, Variante, Seed, aktueller Stage, Level-Fortschritt. Grau-Kandidaten-Alpha von 0.08 auf 0.18 erhöht (besser sichtbar ohne Ablenkung vom besten Kandidaten).

---

## 2026-05-03

### Animationspipeline für EvoGrow-Suchverlauf (WP1–WP3)
`2fa3e18`

Visualisierung des stufenweisen EvoGrow-Suchprozesses als animiertes Video:

**WP1 — Snapshot-Sammlung in `src/structure/evogrow.jl`:**
- `vis_history`-Feld in EvoGrow; sammelt Snapshots am Ende jedes Levels
- Jeder Snapshot enthält aktuelle Population (Kandidaten + Scores) und Stage-Info

**WP2 — Rendering in `src/plotting/search_animation.jl` + `studies/visualization/animate_search.jl`:**
- `search_animation.jl`: rendert pro Level ein PNG-Frame
- `animate_search.jl`: orchestriert Discovery → Frame-Rendering → optionaler ffmpeg-Export (MP4)

**WP3 — Frame-Layout:**
- Zweispaltig: links Trajektorie-Subplots (Ground Truth vs. Kandidaten), rechts Info-Panel
- Aktuelle Level-Kandidaten: orange; akkumulierte History: grau
- Info-Panel: Stage, Level, Loss, true Gleichungen, farbige Legende

---

## 2026-05-02

### `profile_init` — Ergebnisse ausgewertet
`72629a3`

- `docs/profile_init_results.md` + `docs/profile_init_convergence.png` angelegt
- Lorenz: Pretune klar besser auf allen 3 Seeds (~4× niedrigerer Loss, erreicht Stage 3 statt Stage 2)
- Lotka-Volterra: Pretune auf Mittelwert besser, auf Seed-Ebene gemischt — treibt Algorithmus in Stage 5 (Overshoot)
- Kritisch: alle 12 Runs enden mit `max_levels`, kein Run konvergiert → Level-Budget zu gering für belastbare Aussagen

---

## 2026-04-30

### `analysis/status.py` — Logdatei-Auswertung (WP4)
`90e70f5`

`status.py` um Auswertung der neuen `run.log`-Dateien (aus WP2) erweitert:

- `LOG_PATHS`-Dict: Skript → `run.log`-Pfad im jeweiligen OUT_DIR
- `read_log_markers()`: liest `=== Started/Finished at ===`-Marker aus Logdatei (letzte 500 Zeilen)
- `build_log_info()`: leitet ab ob letzter Run sauber beendet (`clean=True/False/None`)
- `print_known_scripts()`: zeigt Log-Zeile pro Skript (Start-/Endzeit, sauber/unterbrochen)
- WMI-Logik, Output-Timestamps und ETA-Berechnung vollständig erhalten

### Resume-Logik für `benchmark_evogrow.jl` (WP1) + Stdout-Logging (WP2)
`0c74f2d`

Benchmark konnte bisher nicht sicher gestoppt werden: `open(summary_file, "w")` überschrieb
die CSV bei jedem Start. Lösung:

- `seed`-Spalte in CSV eingeführt (Header + Row + Fehler-Record)
- `parse_csv_fields()`: korrekter CSV-Parser für Semikolon-Trenner mit Quote-Handling
- `load_done_set()`: liest existierende CSV und baut `Set{Tuple{String,Int,Int}}` aus `(variant_slug, id, seed)`
- `load_records_from_csv()`: lädt alle Rows für Aggregate nach Resume
- Hauptloop: Skip-Check vor jedem Run, Append-Mode wenn CSV existiert
- Einmalige Migration der bestehenden 140-Row-CSV: `seed`-Spalte per Positionszählung
  nachträglich eingetragen (Seeds-Reihenfolge ist deterministisch → sicher ableitbar)

### Repository-Strukturmigration (WP-R)
`706549f`

Alle drei laufenden Skripte gestoppt. Migration durchgeführt:

- `benchmarks/odeformer/` → `benchmarks/data/` (Datenpfade in beiden Benchmark-Skripten aktualisiert)
- `benchmarks/results/` → `outputs/benchmarks/` (OUT_DIR in `benchmark_evogrow.jl`)
- `generalization_study.jl` → `studies/generalization/`, OUT_DIR → `outputs/studies/generalization/`
- `profile_init.jl` → `studies/profiling/`, OUT_DIR → `outputs/studies/profiling/`
- `debug_single.jl` → `studies/debug/`, OUT_DIR → `outputs/studies/debug/`
- `.gitignore`: `outputs/` eingetragen
- Vorhandene Output-Daten nach `outputs/` kopiert (Resume-Kontinuität)
- `SCRIPTS.md` + `CLAUDE.md` aktualisiert

### Stdout-Logging in alle Skripte (WP2)
`0c74f2d`

Alle fünf Skripte schreiben jetzt `run.log` im jeweiligen OUT_DIR (Append-Modus):

- `=== Started at <ts> ===` / `=== Finished at <ts> ===` als Marker
- `log_println()` + `@logf`-Makro für formatierte Ausgaben
- Betrifft: `benchmark_evogrow.jl`, `studies/profiling/profile_init.jl`,
  `studies/generalization/generalization_study.jl`, `studies/debug/debug_single.jl`,
  `experiments/run_experiment.jl`
- Bestehender per-Run-Log-Mechanismus in `profile_init.jl` bleibt erhalten

---

## 2026-04-29

### `analysis/status.py` — Study Status Checker (Codex-Task)
`756b512`, `b94601f`

Ziel: Skript, das aus SCRIPTS.md alle bekannten Scripts extrahiert und prüft, welche davon gerade laufen.

**Technische Analyse (Windows/WMI):**

- `julia.exe`-Prozesse per PowerShell + WMI abfragbar
- Problem: Command Line von `julia.exe` enthält auf Windows oft keine Script-Argumente
- Wenn Parent-Prozess `julialauncher.exe` ist: Argumente im Parent sichtbar → Script identifizierbar
- Wenn Parent `cmd.exe` ist (auch wenn cmd noch offen): Argumente gehen verloren — gilt für alle über cmd gestarteten Skripte

**Lösung: Hybrid-Ansatz**

1. Prozessbaum: julialauncher.exe-Parent → Script-Name direkt lesbar
2. Output-File-Timestamp: wenn Output-Datei < 90 min alt und Orphan-Prozess läuft → `[LÄUFT?]`

**ETA-Schätzung:**

- Rate über letzte 20 Runs (nicht Gesamtlaufzeit) — robust gegen stuck runs
- Für Experiment-Runner: Rate aus `finished_at`-Timestamps der status.json-Dateien
- Für Benchmark: Rate aus `elapsed_s`-Spalte in summary.csv
- Stuck-Run-Erkennung wenn Run seit >2h im Status `running`

**Implementierung und Nachtrag:**

- `analysis/status.py` als standalone Python-Skript mit Standard Library umgesetzt
- `SCRIPTS.md` wird per Regex auf `julia <path>.jl`-Aufrufe in Codeblöcken geparst
- Output-Mapping hart codiert, aber ohne Experiment-ID-Hardcoding (`glob`-Patterns)
- Fortschritt/ETA implementiert für:
  - `experiments/run_experiment.jl`
  - `benchmarks/benchmark_evogrow.jl`
  - `profile_init.jl`
  - `generalization_study.jl`
- Stuck-Run-Warnung erkennt aktuell hängende `status.json`-Runs, z.B. alte Lorenz-Runs mit `status="running"`
- Fehler passiert: Datei war zunächst nur untracked und wurde dadurch bei Workspace-Cleanup/Refresh entfernt
- Fix: `analysis/status.py` aus der implementierten Version wiederhergestellt und mit `b94601f` committed, damit sie nicht erneut verloren geht

---

## 2026-04-28

### Experiment-Runner: zweiter Lorenz-3D-Run hängt
`57c4ff3`

Run `54_evogrow_v1_seed7` (Lorenz periodic, EvoGrow v1, Seed 7) läuft seit 2026-04-28T07:46 ohne Fortschritt.
Ursache: Run wurde mit Git-Hash `04f458a7` generiert — **vor** der BFGS-Timeout-Implementierung.
Der neue Timeout greift nicht rückwirkend auf Runs mit altem Config-Hash.

Experiment-Runner: 234 → 242/300 Runs abgeschlossen.
Benchmark `benchmark_evogrow.jl`: ~93 → ~128/300 Runs (~43%).
`profile_init.jl`: weiterhin hängend auf Level 11, Stage 2, Lorenz 3D, Seed 42 — Daten bereits vorhanden.

---

## 2026-04-27

### BFGS-Timeout implementiert (`src/optimize/bfgs.jl`)
`59d6c16`

**Motivation**: `profile_init.jl` hängt seit 48+ Stunden auf einem einzelnen BFGS-Call (Lorenz 3D, Stage 2). `maxiters` begrenzt nur Iterationen, nicht Wall-Clock-Zeit.

**Umsetzung:**
- `time_limit_s::Float64 = 300.0` zu `BFGSOptimizer` ergänzt
- `time_limit = opt.time_limit_s` an beide `Optimization.solve`-Aufrufe (BFGS + Nelder-Mead Fallback) übergeben
- Bei Timeout gibt Optim.jl das beste bisher gefundene Ergebnis zurück — kein Absturz, kein NaN
- Logging: `log_warn("BFGS hit time_limit", ...)` wenn `retcode != Success`

**Parameterwahl**: 300s ist ~100× der medianen per-Call-Zeit (ca. 2–3s), greift bei normalen Runs nie.

### Paper 1 Reproducibility Protocol dokumentiert
`844bbe4`

Vollständige Dokumentation der Paper-1-Konfiguration direkt aus dem Code abgeleitet:
- alle 6 Varianten mit Slug, Basis, Progressions- und Usage-Mode
- alle 10 Benchmark-Systeme (exakt/Surrogate) mit IDs und True-Struktur
- sämtliche Hyperparameter explizit
- Seeds, Metriken, Execution-Loop, Output-Artefakte, Aggregationsregeln, Freeze-Klausel

Dabei 5 Diskrepanzen zwischen Dokumentation und Codebasis gefunden und behoben:
1. `EvoGrow`-Struct fehlte `progression`, `usage`, `use_pretuning`
2. `test.jl` und `test_evogrow_v2_lotka.jl` im Dateibaum, existieren nicht mehr
3. `run_odebench.jl` als Root-Datei angegeben, liegt in `benchmarks/`
4. `src/optimize/pretune.jl` existiert und wird genutzt, war undokumentiert
5. `experiments/` fehlte komplett im Dateibaum

### Experiment-Status (Stichtag 27.04.)

| Skript | Status |
|--------|--------|
| `experiments/run_experiment.jl paper1_phaseA_v1` | läuft — 234/300, ~6–7h Restlaufzeit |
| `benchmarks/benchmark_evogrow.jl` | läuft — 93/300, ~27–40h Restlaufzeit |
| `generalization_study.jl` | fertig (Output-CSVs vorhanden, 24.04.) |
| `profile_init.jl` | hängt seit 2 Tagen — Level 11, Stage 2, Lorenz 3D, Seed 42 |

---

## 2026-04-26

### Repository-Housekeeping
`1f9c643`

- `benchmarks/odeformer/results/` entfernt: alte Ergebnisdateien ohne reproduzierbaren Kontext
- `.gitignore` um `benchmarks/odeformer/results/` ergänzt

### Analyse-Pipeline für Paper 1 angelegt
`6eab0cf`, `ea3cc44`, `053d717`, `c1f51ef`, `0f8e677`, `8c1152d`, `d983abf`

- `analysis/` als dedizierter Bereich für Python-Auswertung angelegt
- `analysis/CONVENTIONS.md`: Architektur- und Regelwerk für die Python-Analyse
- `analysis/utils/`: `io.py`, `metrics.py`, `style.py` (Variant-Farben und Labels)
- `analysis/scripts/aggregate/aggregate_run_registry.py`: liest `run_registry.csv`, schreibt `aggregate_by_variant_system.csv`
- `analysis/scripts/plot/plot_exact_match_rates.py`: Exact-Match-Rate-Plot
- `analysis/scripts/plot/plot_stage_overshoot.py`: Stage-Overshoot-Plot (GP ausgeschlossen)
- `analysis/scripts/plot/table_main_results.py`: LaTeX-Tabelle Main Results

### Paper-1-Protokoll eingefroren (`docs/paper1_study_protocol.md`)
`2e65d57`, `9ca633a`, `c810703`

Core Goal: Paper 1 untersucht staged growth als Mechanismus zur kontrollierten Komplexitätssteigerung — nicht "bestes ODE-Discovery-System".

Hypothesen:
- H1: Stage-local v2.2 zeigt niedrigeren `mean_stage_overshoot` als v2.1 und v1
- H2: v2.2 liefert kompetitive `exact_match_rate` bei niedrigerem Complexity-Efficiency-Cost
- H3: `mean_wasted_levels` nur zwischen EvoGrow-Varianten; GP ausgeschlossen
- H4: usage-policy comparison (`hard`, `soft`, `passive`) als sekundäre Hypothese

Evidenzregeln:
- Surrogate-Systeme nicht für `exact_support_match` oder H1–H4-Strukturaussagen
- Systeme 2 und 24 (expected_stage=1) aus H1/H3/H4 ausgeschlossen
- No post-hoc cherry-picking; keine neuen Runs nach Ergebnisinspektion

### Variant-Slug vereinheitlicht
`9d25f44`

`evogrow_v2_2_stage_local` überall standardisiert: `benchmark_evogrow.jl`, Analyse-Skripte, `style.py`, Dokumentation.

### Logging: Datum im Timestamp ergänzt
`035e354`

`src/utils/logging.jl`: Timestamp-Format von `HH:MM:SS` auf `yyyy-mm-dd HH:MM:SS` erweitert.
Grund: über Nacht laufende Skripte erzeugen sonst Logs ohne Datumszuordnung.

---

## 2026-04-23

### Bugs gefunden und gefixt
`d27b697`

**Bug 1: `PolynomialBasis` fehlte kubischer Term für System 11**
- `evogrow_v1` nutzte `PolynomialBasis` (nur bis Grad 2), System 11 (Critical slowing down) erwartet `u1^3`
- Entscheidung: `evogrow_v1` auf `default_staged_polynomial_basis` umgestellt — gleicher Suchraum wie alle anderen Varianten, alles sofort entsperrt

**Bug 2: `log_exception` speicherte `DataType` statt `String`**
- `merged[:exception_type] = typeof(err)` schlug fehl weil `Dict{Symbol,String}` keinen `DataType` akzeptiert
- Fix: `string(typeof(err))` in `src/utils/logging.jl`

### Generalisierungsstudie geplant und implementiert (`generalization_study.jl`)
`f30af7c`

Frage: Wenn EvoODE auf Parametersatz A die korrekte Struktur findet — passt diese Struktur nach reinem Parameter-Refit auch auf ungesehene Parametersätze B–E derselben ODE-Familie?

- 3 Systeme (Logistic growth, Lotka-Volterra, SIR), je 5 Parametersätze (1 Train + 4 Test)
- 2 Varianten (evogrow_v2_2_stage_local, gp_baseline), 3 Seeds
- Baseline: frischer Discovery direkt auf Testtrajektorie
- Output: `debug_results/generalization_study/generalization_summary.csv`, `generalization_detail.csv`

### Erste Experiment-Befunde (paper1_phaseA_v1, ~40/300 Runs)

Bisher abgeschlossen: System 2 (Population growth) und System 3 (Logistic growth).

- Alle Runs: `success=true`, `exact_support_match=true`
- Loss ist deterministisch: identisch über alle Seeds (Pretuning + BFGS konvergiert immer ins gleiche Minimum)
- **Stage Overshoot:**
  - `evogrow_v2_1` (global plateau): mittlerer Overshoot 1.5 auf System 3 (expected_stage=2, landet in Stage 3–4)
  - Alle v2.2-Varianten (stage_local): Overshoot 0 — bleiben korrekt in Stage 2
  - Direkte Bestätigung der Kernhypothese

---

## 2026-04-22

### Pretuning (OLS Warm-Start)
`c4fad8a`

- `src/optimize/pretune.jl`: Ableitung per finite Differenzen, Design-Matrix aus Basistermen, OLS-Lösung als BFGS-Startwert
- `use_pretuning::Bool`-Flag in `EvoGrow`
- `level_log` um `elapsed_s`-Feld erweitert

### Experiment-Infrastruktur (WP-E1 bis WP-E3)
`c4fad8a`

- `experiments/generate_manifest.jl`: erzeugt Experiment-Verzeichnis, `manifest.json`, alle per-Run `config.json` + `status.json`
- `experiments/run_experiment.jl`: sequentieller Runner mit robustem Fehlerhandling, atomaren Writes, restart-fähig
- `experiments/aggregate.jl`: leitet `run_registry.csv` aus per-Run-Ordnern ab, idempotent
- Per-Run-Dateiprotokoll: `config.json` (immutable), `status.json` (non-atomic), `result.json` + `metrics.json` (atomar via tmp→rename)

### Debug- und Profiling-Skripte
`c4fad8a`

- `debug_single.jl`: Einzelrun auf Lotka-Volterra mit verbose Logging und PNG-Output
- `profile_init.jl`: Vergleich random vs. pretune Initialisierung auf Lotka-Volterra + Lorenz, 3 Seeds

### Experiment gestartet

`paper1_phaseA_v1`: 10 Systeme × 6 Varianten × 5 Seeds = 300 Runs, exploratory

---

## 2026-04-21

### EvoGrow v2.2 (stage_local)
`224714d`

- `StageProgressionPolicy` mit Modus `:stage_local` und `min_levels_per_stage`
- `StageUsagePolicy` mit Modi `:hard`, `:soft`, `:passive` und `new_term_bias_prob`
- Stage-lokale Plateau-Detektion mit Mindestbudget pro Stage
- Benchmark-Matrix: 10 Systeme × 6 Varianten × 5 Seeds vollständig

---

## 2026-04-20

### Projekt-Fundament
`84f94e8`, `4d8bd2e`, `f5e1d9c`, `a811927`

- Core stabilisiert: EvoGrow und GP laufen sauber mit konsistentem Loss (`discover()` end-to-end)
- Benchmark-Infrastruktur angelegt: 10-System-Suite, erste Varianten
- Housekeeping: Stubs gefixt, Docstrings, Interface-Bereinigung

---

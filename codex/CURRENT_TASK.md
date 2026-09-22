# WP-T1b — Trägt die trajektorien-abgeleitete Rangliste als eigenständiges Discovery-Verfahren?
**Language: Python**

## Warum dieses Work Package existiert

WP-T1 hat gemessen, dass das Signal da ist — und zwar stärker als erwartet: im Entscheidungsfall
(`weak` × `forward`, σ = 0, IC1, dim 2+3) ist der Median von `n_false_before_last_true` **0,0** bei
einer Zufallserwartung von 6,1 (dim 2) und 11,5 (dim 3), und 37 von 44 Gleichungen liegen bei ≤ 3.
Bei über der Hälfte der gekoppelten Gleichungen steht der vollständige wahre Support ganz oben.

Daraus folgt eine Frage, die vor jeder Guidance-Arbeit beantwortet sein muss, weil eine Begutachtung
sie zuerst stellt:

> **Wenn ein billiger linearer Schritt den wahren Support meist auf Platz 1 rankt — warum dann noch
> EvoGrow?**

WP-T1b liefert die Zahl, die diese Frage beantwortbar macht: wie weit die Rangliste **allein**
trägt, wenn man sie zu einem vollständigen Verfahren macht. Ohne sie haben wir keine Antwort;
mit ihr haben wir entweder eine klare Arbeitsteilung oder ein ehrliches Negativergebnis über die
eigene Suche. Beides ist verwertbar.

**Dies ist keine Guidance-Arbeit.** WP-T2a (relevance-guided child generation) beginnt erst danach
und ist nicht Gegenstand dieses Auftrags.

## Was gemessen wird

Aus der Rangliste wird ein Verfahren: **Selektion → Koeffizienten → Integration → Metriken**. Die
Metriken sind exakt die des bereits gerechneten SINDy-Baselines auf denselben Trajektorien, damit
die Zahlen nebeneinander stehen können, ohne umgerechnet zu werden.

## Eingänge, alle nur lesend

1. Die Trajektorien: derselbe gehashte Export wie in WP-T1,
   `outputs/phase_c_trajectory_hashes/wp_c4c/trajectory_export/`. Kein Fallback, keine
   Selbstintegration. Ein Hash-Mismatch bricht ab.
2. `studies/regression/phase_c_support.json` — Ground Truth unter der kanonischen Basis.
3. `benchmarks/data/strogatz_extended.json` — Systemdefinitionen, Initialbedingungen.
4. Der bestehende Studienkern `analysis/exploratory/term_relevance/term_relevance.py` wird
   **wiederverwendet**, nicht neu geschrieben: Basisklon, Export-Loader, Fensterbau,
   Standardisierung, `rank_forward`, Diagnostik. Erweiterungen dort sind erlaubt, dürfen aber die
   WP-T1-Ergebnisse nicht verändern — siehe Regressionskontrolle.
5. Als Vergleichspartner, nur lesend:
   `analysis/data/paper1_phaseC_v1/phasec_sindy_baseline_wp_c4c_export/`.

## Die vier Arme

Zwei Signale, jeweils als eigenständiges Verfahren:

- **`weak`** — Integral-/Weak-Form wie in WP-T1, Fenster 1/2/4/8/16, überlappend, gestapelt.
- **`fd`** — finite Differenzen, zentrale Differenzen zweiter Ordnung.

Beide mit `forward` als Selektionsverfahren. `marginal` entfällt: WP-T1 hat gezeigt, dass es das
Zufallsniveau nicht schlägt (Median 7 bis 9 gegen eine Erwartung von 6,1 bis 11,5) — als
Discovery-Verfahren ist es damit erledigt und wird nicht weitergeschleppt.

### Der `fd`-Arm muss vorher repariert werden

In WP-T1 ist im `fd`-Design die Konstantenspalte konstant, wird von der Standardisierung als
degeneriert erkannt und ans Ende gerankt. Als Rangplatz war das eine vertretbare Konvention; als
**Modellterm** ist es ein Defekt: der Arm kann die Konstante strukturell nicht finden. Messbar in
WP-T1: auf den 39 Gleichungen ohne Konstante im Support sind `fd` und `weak` bei σ = 0 identisch
(Median 0, Anteil ≤ 3 jeweils 0,872); auf den 5 Gleichungen **mit** Konstante fällt `fd` auf
Median 16 und Anteil 0,0, `weak` auf Median 2 und 0,600.

Für WP-T1b ist das zu beheben: der Intercept wird **explizit behandelt** statt durch Zentrierung
entfernt, sodass der Konstantenterm ein regulärer, auffindbarer Kandidat ist. Die gewählte Lösung
ist im Report zu benennen und zu begründen. **Das ist eine Korrektur, kein Tuning** — sie wird
nicht danach ausgewählt, welche Zahlen sie erzeugt. Der `weak`-Arm bleibt unverändert.

Konsequenz für WP-T1: dessen `fd`-Zahlen behalten ihren Defekt und werden **nicht** neu gerechnet.
Der Report hält fest, dass die WP-T1-Aussage „weak schlägt fd" **nicht haltbar** ist — auf dem
fairen Teilsatz von 39 Gleichungen liegen die beiden bei σ = 0 gleichauf, und auch unter Rauschen
zeigen Anteil ≤ 3 und Mittelwert in verschiedene Richtungen (σ = 0,05: 0,744 gegen 0,713 beim
Anteil, 2,785 gegen 2,764 beim Mittelwert).

## Selektionsregel — der gefährlichste Punkt

Vorab deklariert, nie nach Sicht der Daten gewählt. Drei Dinge werden berichtet:

1. **Der vollständige Selektionspfad** k = 1 … p. Für jedes k: Support, Koeffizienten, Metriken.
   Das ist die eigentliche Ausgabe; alles Weitere sind Betriebspunkte darauf.

   **Der volle Pfad wird ausschließlich bei σ = 0 integriert und ausgewertet.** Unter Rauschen
   werden nur die beiden Betriebspunkte `bic` und `oracle_size` integriert. Grund ist gemessen,
   nicht vermutet: die Summe der Bibliotheksgrößen über alle 63 Systeme ist 718, und der volle
   Pfad über beide Quell-ICs, beide Signale, elf Rauschstufen und zwei Auswertungen je Modell
   ergäbe **126.368 Integrationen**. Eine Integration kostet gemessen 13 ms (System 26, dim 2),
   20 ms (System 3, dim 1) und 151 ms (System 55, dim 3), gewichtet rund 65 ms — also mehrere
   Stunden, und divergierende Teil-Supports entlang des Pfades sind der teure Ausreißerfall. Der
   Schnitt bringt das auf etwa 21.600 Integrationen.

   Wissenschaftlich kostet das genau eine Aussage: wie sich die **Form** der Selektionskurve unter
   Rauschen verschiebt. Die Wanderung der beiden Betriebspunkte bleibt sichtbar, und die
   Hauptbedingung ist ohnehin σ = 0, weil nur dort die Zahlen neben dem SINDy-Baseline stehen
   dürfen. Diese Einschränkung ist im Report ausdrücklich als bewusster Zuschnitt zu nennen.
2. **BIC** als die eine parameterfreie automatische Regel. Das k mit minimalem BIC über den Pfad,
   berechnet auf dem jeweiligen Designproblem. Die verwendete Formel und die Wahl von n
   (Zeilenzahl des Designs) sind im Report zu nennen, weil beim `weak`-Signal die Zeilen
   überlappender Fenster nicht unabhängig sind — das ist eine **bekannte und zu deklarierende
   Schwäche** des Kriteriums an dieser Stelle, kein Grund, es wegzulassen.
3. **Oracle-|S|** — die wahre Supportgröße wird vorgegeben. Ausdrücklich eine **obere Schranke,
   kein Verfahren**, und in jeder Tabelle so zu kennzeichnen. Sie trennt Selektionsfehler von
   Rangfehlern: ein schlechter Oracle-|S|-Wert bedeutet, dass die Rangliste falsch war; ein guter
   Oracle-Wert bei schlechtem BIC-Wert bedeutet, dass nur die Stoppregel versagt.

**Verboten:** jeder zusätzliche Schwellenwert, jede Regel, die nach Sicht der Ergebnisse
hinzukommt, und jede Auswahl eines besten k außerhalb dieser drei deklarierten Betriebspunkte.

## Koeffizienten

Kleinste-Quadrate-Lösung auf dem selektierten Support, **im jeweiligen Signalraum** — Weak-Form
beziehungsweise Ableitungsraum. **Kein Refit im Trajektorienraum.** Gemessen werden soll die
billige Pipeline; ein Refit wäre EvoODEs teurer Schritt und würde genau die Grenze verwischen, die
dieses Work Package ziehen soll. Im Report ist zu deklarieren, dass die Koeffizienten damit aus
einem anderen Fehlermaß stammen als EvoODEs Trajektorien-MSE.

## Auswertung — identisch zum bestehenden SINDy-Baseline

Pro Modell:

- Aus dem selektierten Support und den Koeffizienten wird ein ODE-System gebaut und integriert.
- **Rekonstruktion:** Integration von der Trainings-IC, verglichen gegen deren Trajektorie.
- **Generalisierung:** Integration von der **ungesehenen** IC, Parameter unverändert.
- **Beide Richtungen**, `IC1_to_IC2` und `IC2_to_IC1`. WP-N5 hat gezeigt, dass die Richtung
  materiell ist.
- Divergenz- und Nichtendlichkeitsbehandlung wie im SINDy-Skript (`INTEGRATION_LIMIT = 1e9`),
  damit eine divergierte Integration nicht als fehlendes R² verschwindet.

Metriken, immer gemeinsam (Designprinzip 9):

- **Strukturtreffer raw und pruned.** Die Pruning-Regel ist die bestehende,
  `max(SUPPORT_ABS, SUPPORT_REL · max_abs)` mit `SUPPORT_ABS = 1e-6` und `SUPPORT_REL = 1e-3`.
  Sie wird **wiederverwendet, nie neu abgestimmt** — WP-N2 hat gezeigt, dass es keine bessere
  Schwelle gibt, nur einen Nullsummen-Tausch der Fehlerarten.
- **R² und die Rate R² > 0,9**, Verteilungen als Quantile.

Strukturmetriken **nur auf den 30 exakten Systemen** (Designprinzip 8), R² auf allen 63. Exakte und
Surrogatsysteme werden nie in eine Korrektheitskennzahl gemischt.

## Kostenachse

In denselben Einheiten wie der SINDy-Baseline, damit die Zahlen vergleichbar sind:
`n_target_regressions` und `n_evaluation_integrations` je Zelle. Zusätzlich die Anzahl der
Kleinste-Quadrate-Lösungen über den vollen Selektionspfad.

Die Kernaussage, die dabei herauskommen muss: **wie viele ODE-Integrationen während der Selektion
stattfinden.** Wall-clock ist nach Designprinzip 7 keine Evidenz und wird, wenn überhaupt, nur als
Kontext mit Etikett geführt.

## Achsen

| Achse | Werte |
|---|---|
| Signal | `weak`, `fd` (repariert) |
| Betriebspunkt | voller Pfad, `bic`, `oracle_size` |
| Rauschen | `sigma_rel` ∈ {0, 0,01, 0,05}, für σ > 0 fünf Replikate mit den WP-T1-Seeds |
| Richtung | `IC1_to_IC2`, `IC2_to_IC1` |

**Hauptbedingung ist σ = 0**, weil das die Bedingung des SINDy-Baselines ist und nur dort die
Zahlen nebeneinander stehen dürfen. Die Rauschachse läuft mit und wird getrennt berichtet.

## Ausgaben

Nach `analysis/data/wp_t1b_standalone_ranking/`:

- `details.csv` — **satzweise gespiegelt auf das Schema von**
  `phasec_sindy_baseline_wp_c4c_export/details.csv`, damit die beiden Bestände ohne Umrechnung
  übereinandergelegt werden können. Mindestens diese Spalten mit identischer Bedeutung:
  `system_id`, `system_name`, `dimension`, `source_initial_condition_set`,
  `target_initial_condition_set`, `direction`, `regime`, `n_library_terms`, `true_terms`,
  `active_terms_raw`, `active_terms_pruned`, `structure_hit_raw`, `structure_hit_pruned`, `r2`,
  `r2_gt_0_9`, `diverged_or_nonfinite`, `integration_status`, `fit_status`,
  `n_target_regressions`, `n_evaluation_integrations`, `phasec_representability_threeway`,
  `phasec_basis_name`, `valid_for_analysis`. Dazu die T1b-eigenen Spalten: `signal`,
  `operating_point`, `selected_k`, `sigma_rel`, `noise_replicate`.
- `summary.csv` — aggregiert nach Dimension und Repräsentierbarkeitsklasse, in derselben
  Gliederung wie die SINDy-Summary, mit Nennern in jeder Zeile.
- `selection_path.csv` — der volle Pfad k = 1 … p je Zelle.
- `cost.csv` — die Kostenspalten.
- `run_metadata.json` — Konfigurationshash, Eingangs-Hashes, Seeds, verwendete BIC-Formel.

Nach `analysis/figures/wp_t1b_standalone_ranking/` genau zwei Abbildungen: Strukturtreffer gegen k
entlang des Pfades je Dimension mit den beiden Betriebspunkten markiert; und Strukturtreffer gegen
R²-über-0,9-Rate, T1b-Arme gegen SINDy, je Dimension.

**Kein Vergleich gegen EvoGrow-Zahlen in diesem Work Package.** Phase B läuft auf der alten Basis
ohne Konstante und ist als Vergleichspartner ungültig; die kanonische EvoGrow-Zahl kommt aus der
laufenden Phase-C-Kampagne. Wer die Zahlen trotzdem nebeneinanderstellt, vergleicht zwei Basen.

## Vorab festgelegte Deutung

Nicht nach Sicht der Ergebnisse zu ändern. Der Vergleichspartner ist der SINDy-Baseline auf
denselben Trajektorien, exakte Systeme, bestes von zehn Konfigurationen: dim 2 Strukturtreffer
66,7 % und R² > 0,9 bei 70,0 % (Rekonstruktion) beziehungsweise 66,7 % (Generalisierung), dim 3
28,6 % und 12,5 %.

- **A** — Standalone erreicht oder schlägt diese Werte auf dim 2+3. Dann muss EvoGrows
  Rechtfertigung woanders herkommen — Rauschen, Surrogate, Generalisierung — oder die Pipeline
  wird screening-first.
- **B** — Die Rangliste ist stark (WP-T1), aber die Standalone-Selektion scheitert. Dann ist die
  Arbeitsteilung real und WP-T2a ist gerechtfertigt. Der Oracle-|S|-Arm sagt dabei, ob es an der
  Stoppregel oder am Rang lag.
- **C** — Standalone scheitert ebenfalls und der Oracle-Arm auch. Dann war die Rangqualität
  notwendig, aber nicht hinreichend.

Alle drei sind verwertbare Ergebnisse. Keines ist ein Grund, Parameter zu ändern.

## Laufzeitschranke, verpflichtend

Vor dem vollen Lauf ist ein **Smoke-Test auf wenigen Systemen** zu fahren, aus dem die projizierte
Gesamtzahl der Integrationen hochgerechnet wird. Diese Zahl ist im Report zu nennen.

**Liegt die Projektion über 40.000 Integrationen, wird der volle Lauf nicht gestartet**, sondern
als `blocked` gemeldet, mit der projizierten Zahl und der Stelle, an der der Zuschnitt verletzt
ist. Die erwartete Größenordnung nach dem Schnitt ist rund 21.600; eine deutliche Überschreitung
bedeutet, dass der Schnitt falsch umgesetzt wurde, und ist kein Grund, trotzdem zu rechnen.

Die Zahl der tatsächlich ausgeführten Integrationen wird mitgezählt und in `cost.csv` geführt.

## Regressionskontrolle

`analysis/exploratory/term_relevance/` wird erweitert, und WP-T1 hängt daran. Verpflichtend:
**ein erneuter WP-T1-Lauf reproduziert `gate_decision.json` und
`aggregate_by_configuration_dimension.csv` bitidentisch** — mit Ausnahme der `fd`-Zahlen, falls die
Intercept-Reparatur den gemeinsamen Codepfad berührt. Ist das der Fall, ist die Reparatur so zu
bauen, dass der WP-T1-Pfad unverändert bleibt (etwa als Option, deren Vorgabewert das alte
Verhalten ist). Die Kontrolle läuft als Test, nicht als Behauptung im Report.

## Tests

- Synthetisches System mit bekanntem Support und bekannten Koeffizienten: Oracle-|S| muss den
  exakten Support und die Koeffizienten bis auf Integrationsfehler treffen.
- Der Intercept-Test: ein System, dessen wahrer Support die Konstante enthält, muss im reparierten
  `fd`-Arm auffindbar sein. Dieser Test scheitert gegen den WP-T1-Stand — das ist sein Zweck.
- Schema-Kontrolle: die geforderten Spalten von `details.csv` existieren und tragen dieselben
  Wertebereiche wie im SINDy-Bestand (`direction`, `regime`, boolesche Trefferspalten).
- Determinismus: zweimaliger Lauf mit identischem Seed erzeugt identische Ausgaben.
- Die WP-T1-Regressionskontrolle oben.

## Verbote

- Keine Änderung unter `src/`, `experiments/`, `studies/`, `k8s/`, `containers/`, `benchmarks/`.
- Kein Schreiben in `analysis/data/paper1_phaseA_v1`, `paper1_phaseB_v1`, `paper1_phaseC_v1`. Der
  SINDy-Bestand und der Trajektorien-Export werden ausschließlich gelesen. Die Phase-C-Kampagne
  läuft.
- Keine Julia-Ausführung.
- Keine neue Abhängigkeit über `analysis/requirements.txt` hinaus; fehlt etwas, als Blocker melden.
- Kein Neuabstimmen der Pruning-Schwelle, kein zusätzlicher Selektionsschwellenwert, keine Auswahl
  eines besten Arms.
- Kein GitLab-Push.

## Abnahmekriterium

Alle vier Arm-Kombinationen laufen über alle 63 Systeme, beide Richtungen und beide IC-Sätze
durch; die drei Betriebspunkte sind berichtet; `details.csv` lässt sich ohne Umrechnung auf den
SINDy-Bestand legen; die WP-T1-Regressionskontrolle ist grün; jede berichtete Rate nennt ihren
Nenner. Welche der drei Deutungen A, B oder C eintritt, ist für die Abnahme ohne Belang.

## Bericht

`codex/reports/REPORT_WP_T1b.md`. Zwingend aufzunehmen: die gewählte Intercept-Behandlung mit
Begründung, die BIC-Formel samt der Abhängigkeitsschwäche bei überlappenden Fenstern, die
Feststellung, dass die WP-T1-Aussage „weak schlägt fd" nicht haltbar ist, die Kennzeichnung von
Oracle-|S| als obere Schranke, die Zahl der ODE-Integrationen während der Selektion, und die
ausdrückliche Feststellung, dass kein EvoGrow-Vergleich stattgefunden hat und warum.

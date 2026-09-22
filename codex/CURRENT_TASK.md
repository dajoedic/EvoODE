# WP-T1c — Welcher Prioritätsgeber ordnet unsere Basisterme besser?
**Language: Python**

## Die eine Frage

> **Ordnet der STLSQ-Pfad die kanonischen Basisterme besser als unsere Forward-Residual-Selektion —
> gemessen an der Rangqualität, nicht an eigenständiger Entdeckung?**

Das Ergebnis wählt den Prioritätsgeber für WP-T2a (relevance-guided child generation). Mehr nicht.

## Warum diese Frage jetzt kommt

WP-T1b hat gezeigt, dass der billige Schritt die teure Suche **nicht** ersetzt (Deutung C). Dabei
fiel eine Zahl an, die woanders hinzeigt: auf dim 2 erreicht unser `forward`+`bic` als
eigenständiges Verfahren **30,0 %** Strukturtreffer, der `fd`-Arm **20,0 %** — beide auf **unserer**
kanonischen Basis —, während SINDy mit STLSQ auf **seiner** Bibliothek **66,7 %** erreicht (bestes
von zehn Konfigurationen; Median 44,4 %).

Der Abstand kommt also **nicht vom Signal** — `fd` trägt dasselbe Ableitungssignal wie SINDy. Er
kommt von der Bibliothek oder von der Selektionsregel. Dieses Work Package trennt die beiden, indem
es STLSQ auf **unsere** Basis setzt.

Und es beantwortet dabei eine Designfrage, die im Raum steht: wenn SINDys billiger Schritt besser
selektiert, wäre er möglicherweise auch der bessere **Prior-Erzeuger**. Für einen Prior zählt nur
die Ordnung über die Terme, nicht das Modell, das dabei herauskommt.

## Warum die Metrik aus WP-T1 und nicht aus WP-T1b

`n_false_before_last_true` misst **Ordnung**. Der Strukturtreffer aus WP-T1b misst **eigenständige
Entdeckung**. EvoGrow braucht vom Prior keine korrekte Modellauswahl, sondern eine Reihenfolge, die
besser ist als uniform. Deshalb wird hier mit WP-T1s Metrik gemessen, und ausschließlich damit.

## Was gebaut wird

Eine **dritte Ranking-Methode** in der bestehenden Maschinerie
`analysis/exploratory/term_relevance/term_relevance.py`: `stlsq_path`.

### Verfahren

Sequentielle schwellwertbasierte kleinste Quadrate auf dem standardisierten Design, wie in WP-T1:
kleinste Quadrate lösen, Koeffizienten unterhalb der Schwelle auf null setzen, auf den
verbleibenden Spalten neu lösen, wiederholen bis die aktive Menge stabil ist.

**Die Rangliste entsteht aus dem Pfad, nicht aus einer einzelnen Lösung.** Die Schwelle läuft über
ein **vorab deklariertes geometrisches Raster**; die Reihenfolge, in der Terme ausscheiden, ergibt
den Rang — wer zuletzt überlebt, steht oben. Das Raster ist fest, wird vollständig berichtet und
**nicht abgestimmt**. Es muss weit genug spannen, dass am oberen Ende alle Terme ausgeschieden sind
und am unteren Ende keiner; trifft das nicht zu, ist es zu erweitern und das im Report zu
vermerken — nicht enger zu wählen, bis es passt.

**Rangbindungen:** scheiden mehrere Terme bei derselben Schwelle aus, entscheidet der Betrag des
standardisierten Koeffizienten bei der letzten Schwelle, an der beide aktiv waren; danach der
aufsteigende Basisindex. Die Regel steht im Report.

### Der `fd`-Arm läuft repariert

Die Intercept-Behandlung aus WP-T1b (`explicit_intercept=True`) wird hier für **beide** Methoden
verwendet, damit der Vergleich fair ist. Ohne sie ist der Konstantenterm im `fd`-Design strukturell
unauffindbar, und der Vergleich misst den Defekt statt der Methode.

## Achsen

| Achse | Werte |
|---|---|
| Signal | `weak`, `fd` (mit explizitem Intercept) |
| Methode | `forward`, `stlsq_path` |
| Rauschen | `sigma_rel` ∈ {0, 0,01, 0,05}, für σ > 0 fünf Replikate mit den WP-T1-Seeds |
| IC-Strategie | `ic1`, `ic2` |

`marginal` entfällt — WP-T1 hat es als Zufallsniveau erledigt. `ic1_ic2` entfällt, weil ein Prior
zur Suchzeit nur eine Trajektorie sieht.

Reine lineare Algebra, **null ODE-Integrationen**. Die Laufzeit muss im Minutenbereich liegen.

## Entscheidungsregel — vorab festgelegt

**Entscheidungszelle:** Signal `weak`, `sigma_rel = 0`, IC-Strategie `ic1`, Stratum **dim 2 und
dim 3** (18 Systeme, 44 Gleichungen) — identisch zu WP-T1, damit die Zahlen direkt vergleichbar
sind.

**Gewinner ist die Methode mit dem kleineren Median `n_false_before_last_true`.** Bei gleichem
Median entscheidet der höhere Anteil mit Wert ≤ 3. Sind auch die gleich, gibt es **keinen
Gewinner**.

**Replikationsbedingung:** die Richtung muss auf `ic2` dieselbe sein. Kippt sie, gibt es **keinen
Gewinner**.

**Bei „kein Gewinner" bleibt `forward` der Prioritätsgeber** — als Amtsinhaber aus WP-T1, nicht
weil er besser wäre. Das ist die vorab festgelegte Regel gegen eine Auswahl nach Geschmack.

Der `fd`-Arm und die Rauschachse werden **vollständig berichtet, entscheiden aber nichts.** Die
Phase-C-Trajektorien sind rauschfrei; eine Wahl nach Rauschverhalten wäre eine Wahl nach einer
Bedingung, die in der Anwendung nicht vorliegt.

**Verboten:** den Prioritätsgeber später danach zu wählen, welcher bei EvoGrow besser aussieht. Das
wäre der WP-V1-Fehler in neuer Verkleidung. Die Wahl fällt hier, an der Rangqualität, und sie wird
berichtet.

## Ausgaben

Nach `analysis/data/wp_t1c_prior_generator/`:

- Satzweise Records im Format von WP-T1 (`records.csv`), erweitert um `ranking_method =
  stlsq_path` und um `stlsq_threshold_grid`, `stlsq_dropout_threshold` je Term.
- Aggregat je Konfiguration und Dimension: Quantile (0,1 / 0,25 / 0,5 / 0,75 / 0,9) und
  Schwellenraster über `n_false_before_last_true` bei 0, 1, 2, 3, 5, 10.
- Direkter Methodenvergleich je Dimension: Median, Anteil ≤ 3, und die **gepaarte** Differenz je
  Gleichung (dieselbe Gleichung, beide Methoden), als Verteilung, nicht als Mittelwert.
- `generator_decision.json`: Entscheidungszelle, beide Kandidatenwerte, die Replikationsbedingung,
  der Gewinner oder „kein Gewinner", und die Regel im Klartext.
- `run_metadata.json` mit Konfigurationshash, Eingangs-Hashes, Seeds und dem Schwellenraster.

Eine Abbildung nach `analysis/figures/wp_t1c_prior_generator/`: die gepaarte Differenz je Dimension.

Jede berichtete Rate nennt ihren Nenner.

## Regressionskontrolle

**Verpflichtend, und beim ersten WP-T1b-Anlauf war genau das gebrochen:** ein erneuter WP-T1-Lauf
muss `analysis/data/wp_t1_term_relevance/gate_decision.json` und
`aggregate_by_configuration_dimension.csv` **bitidentisch** reproduzieren, ebenso die WP-T1b-
Ausgaben `summary.csv` und `cost.csv`. Neue Funktionalität kommt als Option mit dem alten
Vorgabewert hinein. Die Kontrolle läuft als Test, nicht als Behauptung im Report.

## Tests

- Regressionskontrolle oben, für WP-T1 **und** WP-T1b.
- Synthetisches System mit bekanntem Support, gut angeregt und schwach kollinear: **beide**
  Methoden müssen `n_false_before_last_true == 0` liefern.
- Rasterabdeckung: am oberen Ende des Schwellenrasters ist die aktive Menge leer, am unteren Ende
  vollständig. Andernfalls Abbruch.
- Die Tie-Break-Regel: ein konstruierter Fall mit zwei gleichzeitig ausscheidenden Termen wird
  deterministisch aufgelöst.
- Determinismus: zweimaliger Lauf mit identischem Seed erzeugt identische Records.

## Verbote

- Keine Änderung unter `src/`, `experiments/`, `studies/`, `k8s/`, `containers/`, `benchmarks/`.
- Kein Schreiben in `analysis/data/paper1_phase*`, `wp_t1_term_relevance` oder
  `wp_t1b_standalone_ranking`. Die Phase-C-Kampagne läuft.
- Keine Julia-Ausführung, keine neue Abhängigkeit über `analysis/requirements.txt` hinaus.
- Kein Abstimmen des Schwellenrasters auf das Ergebnis, keine dritte Methode als Ausweg, wenn eine
  der beiden schlecht aussieht.
- Kein GitLab-Push.

## Abnahmekriterium

Beide Methoden laufen über alle 30 exakten Systeme, beide IC-Sätze und alle Rauschstufen durch; die
Regressionskontrolle für WP-T1 und WP-T1b ist grün; `generator_decision.json` benennt einen Gewinner
oder ausdrücklich „kein Gewinner" mit allen Einzelbedingungen. **Welche Methode gewinnt, ist für die
Abnahme ohne Belang** — „kein Gewinner" ist ein gültiges Ergebnis.

## Bericht

`codex/reports/REPORT_WP_T1c.md`. Zwingend: das Schwellenraster und der Nachweis seiner Abdeckung,
die Tie-Break-Regel, die gepaarte Differenz als Verteilung, die Feststellung, ob der `fd`-Arm die
Bibliothek-gegen-Selektionsregel-Frage beantwortet, und die ausdrückliche Notiz, dass die Wahl des
Prioritätsgebers hier fällt und nicht später an EvoGrow-Ergebnissen.

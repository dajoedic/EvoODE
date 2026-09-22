# WP-T1 — Trajektorien-abgeleitete Term-Relevanz: Machbarkeit auf gekoppelten Systemen
**Language: Python**

## Oberstes Designprinzip

**A positive dim-1 result proves nothing. The branch lives or dies on coupled systems.**

Jede Aggregation, jede Tabelle und jedes Gate trennt dim 1 von dim ≥ 2. dim 1 ist ausschließlich
Sanity-Check — „erkennt das Verfahren offensichtliche Signale überhaupt?" — und geht nie in eine
Entscheidung ein.

## Forschungsfrage

Do trajectory-derived term rankings contain enough equation-specific information to place the
complete ground-truth support ahead of substantially fewer false candidates than random ordering
on coupled, exactly representable ODE systems?

Der Mechanismus, den die Frage vorbereitet und der **nicht** Gegenstand dieses Work Packages ist:

trajectory → term relevance prior → better early additions → less add-only path damage →
higher support recovery.

**Nicht das Ziel:** Bibliotheksreduktion oder Compute-Ersparnis. Kosten sind eine sekundäre
Folgekennzahl, nie die Zielgröße. Begriffe wie „pruning", „library reduction" oder „compute
saving" gehören nicht in Code, Spaltennamen oder Report.

## Motivation, in dieser Reihenfolge

1. **Der Konstantenterm ist das Minimalbeispiel.** Er ist nötig, damit die Modellklasse 30 statt
   20 Systeme exakt darstellt (P3-Freeze, WP-N16), kann also nicht entfernt werden. Gleichzeitig
   ist er ein gemessener False-Positive-Magnet — dim 1: in 31 von 37 verfehlten Zellen; dim 2:
   Strukturtreffer pruned 55,6 % → 35,2 % (WP-N15). Threshold-Tuning löst das nicht (WP-N2:
   Nullsummen-Dial, 45 ist die Decke). Ein Prior kann sagen „Term bleibt zulässig, aber diese
   Trajektorie liefert wenig Evidenz dafür" — ohne die Bibliothek anzutasten.
2. **Add-only growth macht frühe Fehlgriffe teuer.** `_expand` fügt nur hinzu; ein falscher früher
   Term verlässt eine Linie nie wieder. Kandidaten-Reihenfolge zählt hier mehr als in einer Suche
   mit Löschen oder Ersetzen.
3. **Auf gekoppelten Systemen scheitern beide Seiten.** EvoGrow erkennt 0 von 50 exakten
   dim-3/dim-4-Supports; SINDy liefert dort ebenfalls keinen guten Support. Genau dort ist Raum
   für einen methodischen Gewinn.

## Abgrenzung

WP-T1 beantwortet **eine** Frage: enthält das Signal die Information. Nicht Gegenstand:

- keine Änderung an `src/structure/evogrow.jl` oder irgendeinem Suchcodepfad,
- keine relevance-guided child generation — das ist WP-T2a, später,
- keine Anwendung des Signals auf Stage Progression oder Stage Cap — das ist WP-T2b, später,
- keine Surrogatsysteme, dort gibt es keinen sauberen wahren Support,
- keine Aussage über Compute-Ersparnis.

## Ort im Repository

Explorative, isolierte Studie. Implementierung unter `analysis/exploratory/term_relevance/`; das
Verzeichnis `analysis/exploratory/` existiert und ist leer. `analysis/CONVENTIONS.md` gilt: keine
Cross-Imports zwischen Julia und Python, Daten nach `analysis/data/<id>/`, Tests nach
`analysis/tests/`. Der Bezeichner lautet `wp_t1_term_relevance`; er ist **kein**
Experiment-Identifier im Sinne von Paper 1 und darf nie so behandelt werden.

## Eingänge, alle nur lesend

1. `benchmarks/data/strogatz_extended.json` — Systemdefinitionen und Initialbedingungen.
2. `studies/regression/phase_c_support.json` — Ground-Truth-Support unter der kanonischen
   Phase-C-Basis `staged_polynomial_basis_with_constant`, bereits in Basis-Termnamen
   (`support_terms`) **und** 1-basierten Basisindizes (`support_idxs`). Verwendet werden nur
   Einträge mit `representability == "exact"` und `status == "ok"`: 30 Systeme, 11/10/8/1 auf
   dim 1/2/3/4.
3. **Trajektorien: die exportierten Kampagnenbytes**, nicht neu integrierte.
   `outputs/phase_c_trajectory_hashes/wp_c4c/trajectory_export/` enthält
   `trajectory_manifest.csv` mit 126 Zeilen (63 Systeme × 2 IC-Sätze) und die Rohdaten als
   float64 unter `cells/`. Achsenreihenfolge, Form, Dtype und Byte-Order stehen im Manifest und
   sind **zu lesen, nicht anzunehmen**; die SHA256-Summen sind zu prüfen und ein Mismatch bricht
   ab. Damit arbeitet WP-T1 auf denselben Bytes wie die Phase-C-Kampagne.

   **Fallback, nur falls der Export fehlt:** Selbstintegration über den vorhandenen Helfer
   `integrate_truth` aus `analysis/scripts/aggregate/run_wp_n6_sindy_baseline.py` (DOP853,
   rtol = atol = 1e-9), Gitter 512 Punkte über t ∈ [0,10]. Dieser Fall ist im Record über ein
   Feld `trajectory_source` zu kennzeichnen und im Report zu deklarieren: WP-C4b misst zwischen
   Tsit5 und DOP853 bei 1e-9 eine relative Abweichung von etwa 1e-10 bei bitgleichem Zeitgitter.
   Für eine Rangfrage ist das irrelevant, muss aber genannt werden. Beide Quellen zu mischen ist
   verboten — ein Lauf verwendet genau eine.

## Basisklon und Drift-Schutz

Die kanonische Basis wird in Python nachgebaut, in genau der Stage-Reihenfolge der Julia-Seite
(`src/basis/staged_polynomial.jl`, `staged_polynomial_basis_with_constant`):

- Stage 1: `1`, dann `u1` … `ud`
- Stage 2: `u1^2` … `ud^2`
- Stage 3: `ui*uj` für i < j, i aufsteigend außen, j innen
- Stage 4: `u1^3` … `ud^3`
- Stage 5: je Variable `sin(ui)` und `cos(ui)`, in dieser Reihenfolge

Bibliotheksgröße 1 + 5d + d(d−1)/2, also 6 / 12 / 19 / 27 für dim 1 bis 4.

**Drift-Schutz, verpflichtend als Test:** für alle 30 exakten Systeme muss `support_idxs[k]` im
Python-Basisklon exakt auf die Namen in `support_terms[k]` zeigen. Ein einziger Mismatch bricht
den Lauf ab — kein Warnen, kein Überspringen. Damit ist kein Julia-Aufruf nötig, und ein
Auseinanderlaufen der beiden Implementierungen wird sofort sichtbar.

## Zwei Signale, die verglichen werden

Nicht „Integral statt Ableitung", sondern Integral **gegen** Ableitung. Beide erzeugen eine
Designmatrix A und einen Zielvektor y **pro Gleichung i**.

### Signal `weak` — Integral-/Weak-Form

Fenster über dem Abtastgitter. Für ein Fenster w = [t_a, t_b]:

- Ziel: die Zustandsdifferenz der Zielkomponente zwischen Fensterende und Fensteranfang.
- Spalte j: das Integral der Basisfunktion φ_j, ausgewertet entlang der beobachteten Trajektorie,
  über das Fenster, numerisch per Trapezregel auf dem Abtastgitter.

Fenster-Schema: multi-scale, Längen 1, 2, 4, 8, 16 Abtastschritte, überlappend mit Schrittweite 1,
alle Längen in **eine** gemeinsame Matrix gestapelt. Das Fenster-Schema ist in WP-T1 **keine**
Studienachse — es ist fixiert und wird als Designentscheidung deklariert.

### Signal `fd` — finite Differenzen

- Ziel: punktweise Schätzung der Ableitung der Zielkomponente, zentrale Differenzen zweiter
  Ordnung, einseitig an den Rändern. Bewusst dieselbe Ordnung wie `FiniteDifference(order=2)` im
  SINDy-Baseline-Skript, damit der Vergleich zur bestehenden Baseline lesbar bleibt.
- Spalte j: die Basisfunktion φ_j, ausgewertet an den Gitterpunkten.

### Normalisierung

Beide Signale werden vor dem Ranking spaltenweise standardisiert (Mittelwert abziehen, durch
Standardabweichung teilen), y wird zentriert. Spalten mit verschwindender Streuung — der
Konstantenterm im `fd`-Signal ist der Regelfall — werden **nicht entfernt**, sondern erhalten eine
dokumentierte Sonderbehandlung: sie bleiben in der Bibliothek, bekommen den schlechtestmöglichen
Rang und werden im Record als `degenerate_column` markiert. Stilles Entfernen ist verboten; das
wäre genau der Präprozessierungsfehler, den der Konstantenterm provoziert. Die gewählte Regel wird
im Report ausdrücklich als Regel genannt.

## Zwei Ranking-Methoden

1. `marginal` — normierte marginale Korrelation zwischen Spalte und Ziel, absolut genommen.
   Primitiver Sanity-Baseline ohne Behandlung von Kollinearität.
2. `forward` — Forward Residual Reduction, OMP-artig: wiederholt jenen noch nicht gewählten
   Kandidaten wählen, der den Residualfehler am stärksten senkt, gewählte Menge refitten, Residuum
   aktualisieren. **Die Auswahlreihenfolge ist das Ranking**, nicht das entstehende Modell. Die
   Schleife läuft über die gesamte Bibliothek, bis alle Terme gerankt sind.

Ridge wird bewusst **nicht** implementiert. Falls `forward` sich als numerisch instabil erweist —
nicht reproduzierbare Auswahlreihenfolge bei identischem Input — ist das als Blocker zu melden,
nicht durch eine dritte Methode zu umgehen.

Beide Methoden sind deterministisch. Rangbindungen werden nach aufsteigendem Basisindex gelöst;
diese Regel wird im Report genannt.

## Achsen des Experiments

| Achse | Werte |
|---|---|
| Signal | `weak`, `fd` |
| Methode | `marginal`, `forward` |
| Rauschen | `sigma_rel` ∈ {0, 0,01, 0,05} |
| IC-Strategie | `ic1`, `ic2`, `ic1_ic2` (Zeilen beider Trajektorien gestapelt) |

36 Konfigurationen. Alles ist lineare Algebra auf 512 Punkten; die Gesamtlaufzeit muss im
Minutenbereich liegen. Falls nicht, ist die Implementierung falsch — dann melden, nicht Systeme
streichen.

**Rauschen:** additives gaußsches Rauschen auf den beobachteten Zuständen, Standardabweichung
`sigma_rel` mal der empirischen Standardabweichung der jeweiligen Zustandskomponente über die
Trajektorie. Der wahre Support bleibt unverändert. Für `sigma_rel > 0` fünf Replikate mit fest
deklarierten Seeds; Replikate werden als Verteilung berichtet, nie als Mittelwert allein. Rauschen
wird **nach** der Integration aufgeprägt, nie während ihr.

## Primäre Metrik

Pro Gleichung und Konfiguration:

**`n_false_before_last_true`** — die Anzahl falscher Kandidaten, die im Ranking vor dem schlechtest
gerankten Ground-Truth-Term stehen.

Beispiel: wahrer Support {u1, u2^3, u1*u2}, Ranking [u2^3, u1, sin(u1), 1, u1*u2, …] ergibt 2.

Lesart: so viele falsche Richtungen muss die Suche überleben, bevor alle nötigen Terme priorisiert
sind. Genau die Größe, die für add-only-Pfadabhängigkeit zählt.

Sekundär, immer mitberichtet:

- `rank_worst_true` — Rang des schlechtesten wahren Terms, 1-basiert,
- `mrr_true` — mittlerer reziproker Rang der wahren Terme,
- `recall_at_k` — als Diagnose, nicht als Gate.

`k_star / p` wird **nicht** als Entscheidungsgröße geführt: bei p = 6 bis 27 ist die Granularität
zu grob, um darauf eine Entscheidung zu stützen.

## Nullmodell

Jedes Ergebnis wird gegen zufällige Rangordnungen gestellt.

- Analytisch: der Erwartungswert von `n_false_before_last_true` unter gleichverteilter Permutation
  bei Bibliotheksgröße p und Supportgröße s beträgt (p − s)·s/(s + 1). Zur Orientierung: dim 2 mit
  s = 2, p = 12 ergibt 6,67; dim 3 mit s = 3, p = 19 ergibt 12,0.
- Empirisch: 10 000 zufällige Permutationen pro Gleichung, fester deklarierter Seed. Empirische
  und analytische Erwartung müssen übereinstimmen; die Abweichung ist ein Test.

**Signifikanz cluster-robust.** Die Gleichungen stammen aus wenigen Systemen — dim 2+3 sind 44
Gleichungen aus 18 Systemen, die effektive Stichprobengröße ist also 18, nicht 44. Der primäre
Test permutiert **pro System**, analog zum in WP-A6 etablierten Verfahren; ein gleichungsweise
unabhängiger Test darf zusätzlich berichtet werden, nie als der primäre. Effektstärken werden als
Quantile und Schwellenraster berichtet, nie als Mittelwert oder Median allein, und die Schwellen
werden nicht nach Sicht der Ergebnisse gewählt.

## Diagnostik, die Misserfolge erklären soll

Pro Gleichung und Konfiguration zusätzlich erheben:

- Konditionszahl der standardisierten Matrix A,
- für jeden wahren Term die maximale absolute Kosinus-Ähnlichkeit zu irgendeiner falschen Spalte —
  das ist der Fall `x` gegen `sin(x)` auf kleinem Zustandsbereich,
- Anregung jeder Spalte: Standardabweichung und mittlerer Absolutwert entlang der Trajektorie,
- effektiver Rang von A, Anteil der Singulärwerte oberhalb einer deklarierten relativen Schwelle,
- Beitragsgröße jedes wahren Terms: Betrag des wahren Koeffizienten mal Streuung seiner Spalte.
  Ein wahrer Term mit verschwindendem Beitrag ist ein Identifizierbarkeits-, kein
  Verfahrensproblem, und das muss unterscheidbar sein.

## Entscheidungszelle und Gate — vor Sicht der Ergebnisse festgelegt

**Entscheidungszelle:** Signal `weak`, Methode `forward`, `sigma_rel = 0`, IC-Strategie `ic1`,
Stratum **dim 2 und dim 3** — 18 Systeme, 44 Gleichungen.

Begründung für `ic1` statt `ic1_ic2`: EvoGrow sieht pro Zelle genau eine Trajektorie, eine Zelle
ist (System, Seed, IC-Satz). Ein Prior, der zwei IC-Sätze braucht, existiert zur Suchzeit nicht.
`ic1_ic2` läuft als **obere Referenz** mit und beantwortet die Frage nach dem Wert von
Trajektoriendiversität, ist aber nicht die Entscheidungsgrundlage.

Begründung für den Ausschluss von dim 4: System 63 ist der dokumentierte
Identifizierbarkeitsgrenzfall des Projekts — Cap überall `nothing`, Supportrate 0. Es läuft mit und
wird getrennt berichtet, verzerrt aber kein Aggregat.

**Gate, dreiwertig:**

- **positiv** — Median `n_false_before_last_true` ≤ 2 **und** mindestens 60 % der Gleichungen mit
  Wert ≤ 3 **und** das cluster-robuste Nullmodell wird mit p < 0,01 geschlagen.
- **bedingt** — das Nullmodell wird klar geschlagen, aber eine der beiden Niveaubedingungen fällt.
  Dann ist nur konfidenzgesteuerte weiche Guidance gerechtfertigt, nie hartes Pruning.
- **negativ** — das cluster-robuste Nullmodell wird auf dim 2+3 nicht geschlagen. Dann endet der
  Seitenzweig, und das negative Ergebnis wird dokumentiert.

Die Schwellen 2 und 3 sind eine **menschliche Designentscheidung**, keine aus Daten abgeleitete
Größe, und im Report ausdrücklich als solche zu kennzeichnen — so, wie das Projekt es bei der
Reopen-Schwelle 0,35 tut. Begründung: bei add-only-Wachstum mit mehreren parallelen Linien ist das
Überleben von zwei falschen frühen Additionen plausibel; jenseits von etwa drei verliert ein Prior
seine Handlungsrelevanz.

**Replikationsbedingung:** das Urteil muss auf `ic2` in derselben Richtung stehen. Ein Ergebnis,
das zwischen IC1 und IC2 kippt, ist kein Ergebnis und führt höchstens zu **bedingt**.

**Verboten:** nach Sicht der Ergebnisse eine andere Entscheidungszelle, ein anderes Stratum oder
eine andere Schwelle zu wählen. Die beste von 36 Konfigurationen zu berichten wäre genau der
WP-V1-Fehler. Das volle Raster wird berichtet, ausgewählt wird nichts.

## Ausgaben

Nach `analysis/data/wp_t1_term_relevance/`:

- Satzweise Records, eine Zeile je (System, Gleichung, IC-Strategie, Signal, Methode, `sigma_rel`,
  Rausch-Replikat), mindestens mit: `system_id`, `system_name`, `dimension`, `equation_idx`,
  `ic_strategy`, `signal`, `ranking_method`, `sigma_rel`, `noise_replicate`, `noise_seed`,
  `basis_name`, `library_size`, `true_support_terms`, `true_support_size`, `candidate_names`,
  `candidate_scores`, `candidate_ranks`, `n_false_before_last_true`, `rank_worst_true`,
  `mrr_true`, `condition_number`, `effective_rank`, `max_cosine_true_vs_false`,
  `column_excitation`, `true_term_contribution`, `degenerate_column_count`, `trajectory_source`,
  `trajectory_sha256`.
- Aggregat je Konfiguration und Dimension, als Quantile (0,1 / 0,25 / 0,5 / 0,75 / 0,9) und als
  Schwellenraster über `n_false_before_last_true` bei 0, 1, 2, 3, 5, 10.
- Nullmodell-Vergleich je Konfiguration und Dimension, analytisch und empirisch, mit
  cluster-robustem p-Wert.
- Gate-Urteil als JSON: Entscheidungszelle, die drei Bedingungen einzeln, die
  Replikationsbedingung, das dreiwertige Urteil.

Nach `analysis/figures/wp_t1_term_relevance/` genau zwei Abbildungen:

1. Verteilung von `n_false_before_last_true` je Dimension und Konfiguration, mit der
   Nullmodell-Erwartung als Referenzlinie.
2. `n_false_before_last_true` gegen `max_cosine_true_vs_false` beziehungsweise Konditionszahl —
   die Prüfung, ob Misserfolge Identifizierbarkeitsprobleme sind.

Konfigurationshash und Eingangs-Hashes werden mitgeschrieben, damit der Lauf reproduzierbar ist.
Jede berichtete Rate nennt ihren Nenner.

## Tests

Nach `analysis/tests/`:

- Basis-Konsistenz: `support_idxs` zeigt für alle 30 exakten Systeme auf `support_terms`;
  Bibliotheksgrößen 6 / 12 / 19 / 27.
- Synthetisches System mit bekanntem Support, gut angeregt und schwach kollinear: beide
  Ranking-Methoden müssen `n_false_before_last_true == 0` liefern. Fällt dieser Test, ist die
  Implementierung falsch, nicht das Signal schwach.
- Nullmodell: empirischer Erwartungswert stimmt mit (p − s)·s/(s + 1) überein.
- Determinismus: zweimaliger Lauf mit identischem Seed erzeugt identische Records.
- Degenerierte Spalten: eine konstante Spalte wird nicht entfernt, sondern markiert und
  schlechtest gerankt.
- Trajektorienquelle: ein manipuliertes Byte im Export führt zum Abbruch, nicht zu stillem
  Weiterrechnen.

## Verbote

- Keine Änderung unter `src/`, `experiments/`, `studies/`, `k8s/`, `containers/`, `benchmarks/`.
- Kein Schreiben nach `analysis/data/paper1_phaseA_v1`, `paper1_phaseB_v1` oder
  `paper1_phaseC_v1`. Die Phase-C-Kampagne läuft; nichts in diesem WP darf ihre Records lesen,
  schreiben oder anfassen. Der Trajektorien-Export unter `outputs/` wird ausschließlich gelesen.
- Keine Julia-Ausführung; in dieser Umgebung ohnehin nicht möglich.
- Keine neue Abhängigkeit über `analysis/requirements.txt` hinaus. Fehlt etwas, als Blocker
  melden.
- Keine Auswahl einer besten Konfiguration, kein nachträglich gewählter Schwellenwert.
- Ergebnisse sind ausdrücklich explorativ; keine Paper-1-Aussage hängt daran.
- Kein GitLab-Push.

## Abnahmekriterium

Alle 36 Konfigurationen laufen über die 30 exakten Systeme und beide IC-Sätze durch, die Tests sind
grün, die Ausgaben liegen vollständig vor, und das Gate-Urteil ist als dreiwertige Entscheidung mit
allen Einzelbedingungen belegt — unabhängig davon, wie es ausfällt. **Ein negatives Urteil ist ein
vollwertiges Ergebnis dieses Work Packages** und kein Grund, Parameter zu ändern.

## Bericht

`codex/reports/REPORT_WP_T1.md`. Zwingend aufzunehmen: die verwendete Trajektorienquelle mit ihrer
Deklaration, die Regel für degenerierte Spalten, die Tie-Break-Regel, die Kennzeichnung der
Gate-Schwellen als menschliche Entscheidung, die effektive Clustergröße 18, und die getrennte
Darstellung von dim 1 als Sanity-Check und dim 4 als System 63.

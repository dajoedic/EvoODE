# WP-N6 — SINDy als Baseline auf unseren Daten

**Language: Python**

## Kontext und Zweck

EvoODE ist in vier Jahren Projektarbeit **nie gegen ein anderes Verfahren gemessen worden**. Alle
Vergleiche liefen gegen frühere EvoODE-Varianten. Damit ist bis heute unbekannt, ob die Zahlen gut
oder schlecht sind — unser Anteil R2 > 0,9 liegt bei 80,7 % auf der Kampagne, und niemand kann sagen,
ob das ein Erfolg ist.

Dieses WP liefert die fehlende Vergleichszahl. `pysindy 2.1.0`, `scikit-learn 1.5.1`, `scipy 1.13.1`
und `numpy 2.2.6` sind installiert.

**Dies ist kein Wettbewerb, sondern eine Messung.** Das Ergebnis darf ausfallen, wie es will, und
wird so berichtet. Jede Konfigurationswahl, die SINDy schlechter aussehen liesse, ist ein
Auswertungsfehler.

## Die Daten: identisch zu unseren

SINDy bekommt **exakt dieselben Trajektorien**, die EvoODE bekommt. Erzeuge sie nach dem Phase-B-
Protokoll (`docs/paper1_odebench_protocol_alignment.md` §3):

- Systeme aus `benchmarks/data/strogatz_extended.json`, alle 63
- 512 Punkte ueber t in [0, 10], beide Endpunkte, Abstand 10/511
- **beide** Anfangswertsaetze je System
- selbst integriert mit Toleranz 1e-9, **nicht** die mitgelieferten Trajektorien

Die mitgelieferten Loesungen sind ausdruecklich **nicht** zu verwenden — der Audit hat gemessen, dass
sie MSE-Boeden von bis zu 2,5e-2 tragen. Wenn `scipy.integrate.solve_ivp` verwendet wird, mit
`rtol=atol=1e-9` und expliziter Auswertung an den 512 Zeitpunkten.

**Prüfe und berichte**, ob deine Trajektorien mit denen uebereinstimmen, die EvoODE verwendet. Eine
Abweichung ist ein Befund, kein Detail — ohne identische Daten ist der Vergleich wertlos.

## Was gemessen wird

### Beide Metriken, beide Regime

Design-Prinzip 9 gilt: **Strukturtreffer und Anteil R2 > 0,9**, immer beide. Zusaetzlich beide
Regime aus WP-N5:

- **Rekonstruktion** — Modell auf IC-Satz *x* fitten, ab IC-Satz *x* integrieren
- **Generalisierung** — Modell auf IC-Satz *x* fitten, ab dem **anderen** IC-Satz integrieren

Beide Richtungen getrennt (IC1→IC2 und IC2→IC1), wie in WP-N5.

### Strukturtreffer, sauber definiert

SINDy schwellt intern bereits. Ein Strukturvergleich braucht deshalb eine **explizit benannte**
Regel, und diese Regel muss dieselbe sein wie bei uns: ein Term zaehlt als aktiv, wenn sein
Koeffizient betragsmaessig ueber `max(1e-6, 1e-3 * max_abs)` derselben Gleichung liegt
(`experiments/run_experiment.jl:239`). Wende sie auf SINDys Koeffizientenmatrix an und vergleiche
gegen die wahre Termmenge.

Strukturtreffer sind **nur auf den 20 exakt darstellbaren Systemen** definiert. Nutze
`analysis/data/paper1_phaseB_v1/representational_adequacy.csv` für die Zuordnung — und beachte, dass
die Spalte `sindy_poly` dort sagt, welche Systeme in *SINDys* Bibliothek darstellbar sind (40 von
63). **Weise beide Teilmengen getrennt aus:** die 20 für uns darstellbaren und die 40 für SINDy
darstellbaren. Sie sind nicht dieselben, und das ist selbst ein Ergebnis.

### Bibliotheken: ein Gitter, keine Auswahl

Rechne **mehrere** Konfigurationen und berichte alle:

- Polynombibliothek Grad 2, 3, 4, 5
- Polynom Grad 3 zusaetzlich mit `sin` und `cos`
- je Konfiguration mindestens zwei Sparsity-Schwellen der STLSQ, etwa 0,01 und 0,1

**Keine wird als die beste bezeichnet, keine wird ausgewählt.** Dieselbe Regel wie beim
Pruning-Gitter in WP-N2: die Abhaengigkeit sichtbar machen, nicht wegoptimieren. Die
Konfigurationszahl bleibt klein genug, dass die Tabelle lesbar bleibt.

### Was ausserdem in den Report gehoert

- **Ableitungen.** SINDy braucht Ableitungen, EvoODE nicht. Halte fest, welches
  Differentiationsverfahren du verwendest und dass dies ein **protokollarischer Unterschied** ist,
  kein Implementierungsdetail. Unsere Daten sind rauschfrei, das begünstigt SINDy hier.
- **Kosten** als Zaehlwerte, nicht als Zeit (Design-Prinzip 7): Zahl der Regressionen, Groesse der
  Bibliothek. `elapsed_s` nur als gekennzeichnete Nicht-Evidenz.
- Zellen, deren Modell beim Integrieren divergiert oder nicht-finite Werte liefert, getrennt zaehlen.

## Verboten

- keine Aenderung an Julia-Code, an der Kampagne, an `outputs/wp_n*`-Verzeichnissen oder den
  A5-bis-A9-Skripten
- **keine Auswahl einer besten SINDy-Konfiguration**
- **kein Tuning gegen unsere Ergebnisse** — SINDys Konfigurationen werden nicht danach gewaehlt, wie
  EvoODE dasteht
- keine mitgelieferten Trajektorien
- **keine Figuren**
- keine Ergebnisse in `PAPER_1.md`, `CLAUDE.md` oder `DIARY.md`
- kein `git add -A`, keine Git-Operationen

## Akzeptanzkriterium

Skript unter `analysis/scripts/aggregate/`, ueber `--config` parametrisiert, Ergebnisse nach
`analysis/data/` und Tabellen nach `analysis/tables/`, `.csv` und `.tex`. Die Trajektorienprüfung
gegen EvoODEs Daten ist durchgefuehrt und ihr Ergebnis berichtet. Alle Tabellen tragen beide
Metriken und beide Regime. Fehlerpfad an einer Fixture belegt.

`pysindy` ist mit fester Version in `analysis/requirements.txt` einzutragen.

## Report

`codex/REPORT_WP_N6.md`. Enthaelt: die Kommandos, das Ergebnis der Trajektorienprüfung, das
vollstaendige Konfigurationsgitter mit beiden Metriken und beiden Regimen, die getrennte Auswertung
auf den 20 und den 40 darstellbaren Systemen, die Zahl divergenter Integrationen, das
Differentiationsverfahren — und einen Absatz dazu, **wo SINDy in dieser Messung besser und wo
schlechter abschneidet als die in `outputs/wp_n5_ic_generalization/` liegenden EvoODE-Zahlen**. Diese
Gegenueberstellung ist deskriptiv zu halten: keine Signifikanztests, keine Wertung, nur die Zahlen
nebeneinander.

# WP-N19 — Baseline-Harness: Fremdmethoden auf unseren Trajektorien
**Language: Python**

## Ziel

Ein neuer Teilbaum `baselines/`, der fremde ODE-Discovery-Methoden auf **unseren exportierten
Trajektorien** laufen laesst und Records ausgibt, die die bestehende Analysepipeline neben
Kampagnen-Records legen kann.

Der wissenschaftliche Zweck ist Claim D: der Vergleich muss **auf identischen Trajektorien, per Hash
belegt** stattfinden. Publizierte Zahlen aus dem ODEFormer-Paper sind dafuer unbrauchbar — das Repo
liefert keine Ergebnisdateien, und deren Trajektorien sind die mitgelieferten, unsere sind selbst
integriert.

**Dieses Arbeitspaket baut das Geruest und macht zwei Methoden lauffaehig. Es rechnet keine
Kampagne.**

## Harte Auflagen

1. **`containers/Dockerfile` bleibt unberuehrt.** Die Baseline-Abhaengigkeiten duerfen das
   Kampagnen-Image nie erreichen. `baselines/` bekommt ein **eigenes** Dockerfile und eine eigene
   Abhaengigkeitsdatei.
2. **Nicht nach GitLab pushen.** Ein Push baut das Kampagnen-Image neu, und C-1+C-2 rechnet noch.
   Arbeiten bleiben lokal; Claude committet nach Pruefung.
3. **`odeformer` wird gepinnt, nicht einkopiert.** Commit `c9193012ad07a97186290b98d8290d1a177f4609`
   (Stand main, 2024-08-15, MIT). Kein Fremdcode in unseren Baum kopieren.
4. **Python 3.9** in der Baseline-Umgebung. Die Pins des Fremdrepos sind von 2023
   (`torch==2.0.0`, `numpy==1.23.5`); ein Container ist der einzige vernuenftige Weg, und die
   Umgebung `odeformer39` liefert das Fremdrepo nicht mit — sie ist zu rekonstruieren.
5. **Kein langer Lauf.** Siehe Abschnitt „Was ausdruecklich nicht gerechnet wird".

## Eingabevertrag

Quelle ist der bestehende Export:
`outputs/phase_c_trajectory_hashes/wp_c4c/trajectory_export/` mit `trajectory_manifest.csv`
(126 Zeilen = 63 Systeme x 2 IC-Sets) und 252 Rohdateien unter `cells/`.

Das Manifest benennt fuer jede Zeile Datentyp, Byte-Reihenfolge, Achsenreihenfolge, Formen und je
einen `time_sha256` und `state_sha256`.

**Die Harness prueft vor jeder Nutzung beide Hashes und bricht bei Abweichung ab.** Ein
stillschweigendes Weiterrechnen auf abweichenden Daten zerstoert genau die Aussage, fuer die das
Arbeitspaket existiert. Die Pruefung ist zu protokollieren, nicht nur durchzufuehren.

Die Achsen- und Formangaben des Manifests sind zu **lesen**, nicht anzunehmen.

## Ausgabevertrag

Ein Record je Kombination aus System, IC-Set, Methode und Konfiguration. Jeder Record traegt:

- Identitaet: unser `git_hash`, der gepinnte odeformer-Commit, eine Umgebungskennung (aufgeloeste
  Paketversionen), Methodenkennung und die vollstaendige Konfiguration der Methode
- die beiden Trajektorien-Hashes aus dem Manifest, damit die Paarung spaeter nachpruefbar ist
- das entdeckte Modell in wiederherstellbarer Form, **Koeffizienten eingeschlossen** — ohne sie ist
  keine Generalisierung rechenbar, das ist der Fehler, den Phase B gemacht hat
- die Metriken aus dem naechsten Abschnitt
- Fehlerfelder: eine gescheiterte Methode erzeugt einen Record mit Begruendung, **niemals gar
  keinen**. Eine fehlende Zeile ist als Ergebnis nicht unterscheidbar von einem nie gestarteten Lauf.

Format und Ablage analog zu den bestehenden Baseline-Ausgaben unter
`analysis/data/paper1_phaseC_v1/phasec_sindy_baseline/`; das Schema dort ist die Vorlage, nicht neu
zu erfinden.

## Metrikvertrag — der Teil, der am leichtesten falsch wird

1. **Beide Aggregationen ueber Dimensionen berichten.** Wir bilden bisher das arithmetische Mittel
   ueber die Dimensionen (`run_regression.jl:675`), ODEFormer gewichtet nach Varianz
   (`metrics.py`, `r2_score(..., multioutput='variance_weighted')`). Das sind auf mehrdimensionalen
   Systemen **verschiedene Groessen**. Beide Spalten fuehren, beide benennen. Keine davon zur
   Hauptzahl erklaeren — das entscheidet Claude.
2. **Fehlschlag zaehlt als Misserfolg, nicht als fehlender Wert.** Nicht-endliche oder fehlende
   Vorhersagen ergeben R² = 0 und bleiben im Nenner. Das ist die Konvention des Fremdrepos und
   bereits unsere; sie darf nicht versehentlich durch ein `dropna` verlorengehen.
3. **Beide Richtungen.** Rekonstruktion (Fit-IC) und Generalisierung (die jeweils andere IC),
   getrennt ausgewiesen.
4. **Strukturtreffer und R²>0,9-Rate immer beide**, wo ein Strukturvergleich ueberhaupt definiert
   ist; bei Strukturtreffern **roh und gepruned getrennt**. Die Pruning-Regel wird uebernommen, nicht
   neu gewaehlt.

## Methodenumfang

**Jetzt lauffaehig zu machen:**

- **ODEFormer** — pip-installierbar, vortrainierte Gewichte werden per `gdown` von Google Drive
  geladen. Hoechster Wert, es ist die Vergleichsarbeit.
- **SINDy (`pysindy`)** — als Gegenprobe gegen unsere eigene Implementierung unter
  `analysis/scripts/aggregate/run_phasec_sindy_baseline.py`. Die Frage, die diese Gegenprobe
  beantwortet: reproduziert unsere Implementierung deren Wrapper?

**Jetzt nur vorbereitet, registriert und ausdruecklich inaktiv:** PySR, ProGED, FFX, ellyn. Je ein
Platzhalter, der die Methode kennt, ihre Abhaengigkeit benennt und beim Aufruf sauber meldet, dass
sie nicht eingerichtet ist.

**Warnung zu PySR:** es bringt eine **eigene Julia** mit. Die darf der eingefrorenen Julia 1.12.6
der Kampagne nicht begegnen. Das ist der Grund fuer das getrennte Image und in der
Abhaengigkeitsdatei zu kommentieren.

## Was ausdruecklich nicht gerechnet wird

Die vollen 126 Trajektorien x Methoden sind **nicht** zu rechnen. Erlaubt und erwartet ist ein
**Rauchtest ueber hoechstens drei Systeme der Dimension 1**, der zeigt, dass Hashpruefung, Lauf,
Metrikberechnung und Recordschreibung zusammenspielen. Laufzeit im Minutenbereich.

Den vollen Lauf startet ausschliesslich der Nutzer, nach Abnahme.

## Abnahmekriterium

1. Ein Rauchtest laeuft durch und erzeugt fuer jedes geprueste System je einen Record fuer
   ODEFormer und SINDy, mit allen Feldern des Ausgabevertrags belegt.
2. Eine absichtlich verfaelschte Hashangabe fuehrt zum Abbruch mit klarer Meldung, nicht zu einem
   Ergebnis.
3. Eine absichtlich zum Scheitern gebrachte Methode erzeugt einen Fehler-Record, keine fehlende
   Zeile.
4. `containers/Dockerfile` ist unveraendert; `git status` zeigt keine Aenderung daran.
5. Die beiden R²-Aggregationen stehen als getrennte Spalten im Record und unterscheiden sich auf
   mindestens einem mehrdimensionalen Testfall nachweisbar — sonst ist die Implementierung
   vermutlich zweimal dieselbe.

## Bericht

`codex/reports/REPORT_WP_N19.md`. Aufzunehmen: die rekonstruierte Umgebung mit aufgeloesten
Versionen, welche Methoden laufen und welche nur registriert sind, das Ergebnis des Rauchtests, und
**jede Abweichung, die beim Nachbauen der Umgebung noetig war** — die Pins sind zwei Jahre alt, und
jede stille Anpassung ist spaeter eine unerklaerliche Zahl.

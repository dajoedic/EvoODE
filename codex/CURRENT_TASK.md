# WP-N5 — Generalisierung: das gefundene Modell auf einem ungesehenen Anfangswert

**Language: Julia**

## Kontext

Im gesamten Projekt gibt es **keine einzige Auswertung auf zurueckgehaltenen Daten**. Beide
Anfangswertsaetze wurden trainiert, nie getestet; jedes R2 ist In-Sample, gerechnet auf derselben
Trajektorie, an die angepasst wurde.

ODEBench ist anders gebaut. Die Publikation liefert zwei Anfangswerte je System ausdruecklich
*to evaluate generalization*, und die Kennzahl wird in **zwei getrennten Regimen** berichtet:

- **Rekonstruktion** — aus demselben Anfangswert integrieren, aus dem angepasst wurde
- **Generalisierung** — aus dem **zweiten** Anfangswert integrieren

Berichtet wird jeweils der **Anteil der Vorhersagen mit R2 > 0,9**. Wir koennen bisher nur die erste
Haelfte rechnen.

Seit WP-N1 stehen die Koeffizienten im Record (`model_terms` mit `term`, `term_index`,
`coefficient`) und die Basis unter `basis_name`. Damit ist das gefundene Modell rekonstruierbar, und
die zweite Haelfte wird erreichbar — **ohne einen einzigen neuen Suchlauf**.

## Zweck

Die Generalisierungsmetrik als Standardauswertung verfuegbar machen und auf den vorhandenen Daten
messen.

## Deliverables

### 1. Die Auswertung

Fuer jede Zelle, deren Modell aus **IC-Satz 1** stammt:

1. Struktur und Koeffizienten aus dem Record rekonstruieren (Basis aus `basis_name`)
2. Das Modell vom **Anfangswert des IC-Satzes 2** aus integrieren, ueber dieselbe Zeitspanne und
   dasselbe Zeitgitter wie im Original
3. Gegen die wahre Loesung des Systems ab IC-Satz 2 vergleichen
4. Loss und R2 berechnen, mit derselben R2-Definition wie im Rest des Projekts

**Die Parameter werden nicht neu angepasst.** Das ist der Kern der Metrik: es geht um das Modell, das
die Suche geliefert hat, nicht um ein nachtraeglich verbessertes.

Symmetrisch dasselbe fuer Modelle aus IC-Satz 2, integriert ab IC-Satz 1. Beide Richtungen getrennt
ausweisen — sie sind nicht austauschbar, weil die beiden Saetze unterschiedlich viel Dynamik tragen.

### 2. Auf welchen Daten

Zwei Quellen, getrennt gehalten und **nie in einer Datei zusammengefuehrt**:

- **`outputs/wp_n1_dim1_probe/history.jsonl`** — 132 Zellen, beide Basen. Hier ist die Frage, ob die
  Konstante die Generalisierung anders beeinflusst als die Rekonstruktion.
- **`experiments/paper1_phaseB_v1/run_registry.csv`** — die 756 Kampagnenzellen. Achtung: dort fehlen
  die Koeffizienten, weil sie vor WP-N1 gerechnet wurden. **Pruefe das zuerst und melde es als
  Befund**, statt es zu umgehen. Wenn die Kampagne nicht auswertbar ist, ist das die Antwort — dann
  laeuft dieses WP nur auf dem Probelauf, und der Kampagnenteil wird zum eigenen offenen Punkt.

### 3. Was zu berichten ist

**Immer beide Metriken** (Design-Prinzip 9): Strukturtreffer und Anteil R2 > 0,9.

Zusaetzlich, und das ist der eigentliche Zweck:

| Groesse | Rekonstruktion | Generalisierung |
|---|---|---|
| Anteil R2 > 0,9 | vorhanden | **neu** |
| Loss-Quantile 5/10/25/50/75/90/95 | vorhanden | **neu** |

Getrennt nach Basis, Dimension und Richtung (IC1 → IC2 und IC2 → IC1). Kein Mittelwert oder Median
als alleinige Zusammenfassung.

Zaehle ausserdem die Zellen, deren Modell beim Integrieren ab dem ungesehenen Anfangswert
**divergiert oder nicht-finite Werte** liefert — das ist bei ungesehenen Anfangswerten ein
erwartbarer Ausgang und darf nicht stillschweigend als schlechtes R2 verbucht werden.

### 4. Die Frage, die der Report beantworten muss

> **Wie weit faellt der Anteil R2 > 0,9 von der Rekonstruktion zur Generalisierung?** Die
> ODEFormer-Publikation berichtet, Generalisierung liege durchweg deutlich niedriger. Faellt unsere
> Zahl aehnlich stark, ist das ein Hinweis auf ein gemeinsames Problem der Verfahrensklasse. Faellt
> sie kaum, waere das ein starkes Ergebnis — und dann ist zuerst zu pruefen, ob die Messung stimmt.

### 5. Ausfuehrung

Kosten: eine Integration je Zelle, **keine Anpassung, keine Suche**. Das ist billiger als alles
bisher Gerechnete.

**Du kannst Julia in dieser Umgebung nicht starten** (`A specified logon session does not exist`).
Schreibe den Code, pruefe ihn statisch so sorgfaeltig wie in WP-N3b, melde `blocked` und **erfinde
keine Ergebnisse**. Claude fuehrt aus. Halte zwei Kommandos im Report fest: einen `--limit`-Testlauf
ueber wenige Zellen und den vollen Lauf.

Ergebnisse in ein eigenes Verzeichnis unter `outputs/`.

## Verboten

- keine Aenderung an der Suchlogik, der Basis, am Stage-Cap oder an `pruned_match`
- **keine Neuanpassung der Parameter** — das waere eine andere Messung
- keine Aenderung an `outputs/wp_n1_dim1_probe/`, `outputs/wp_n3_oracle_refit/`,
  `outputs/wp_n4_multistart_refit/`, der Kampagne oder den A5-bis-A9-Skripten
- **keine Figuren**
- keine Ergebnisse in `PAPER_1.md`, `CLAUDE.md` oder `DIARY.md`
- kein `git add -A`, keine Git-Operationen

## Akzeptanzkriterium

Kontrolle, die stimmen muss: Integriert man ein Modell ab **seinem eigenen** Anfangswert, muss der
Loss dem im Record gespeicherten entsprechen. Baue diese Probe ein und melde jede Abweichung — sie
waere der Beleg, dass Rekonstruktion aus dem Record nicht korrekt funktioniert, und dann ist jedes
Generalisierungsergebnis wertlos.

## Report

`codex/REPORT_WP_N5.md`. Enthaelt: die Kommandos, das Ergebnis der Rekonstruktionsprobe, die
Tabellen mit beiden Metriken und beiden Regimen, die Zahl divergierender Integrationen, den Befund
zur Kampagne (Koeffizienten vorhanden oder nicht) — und die Antwort auf die Frage aus Abschnitt 4.

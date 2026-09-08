# WP-N2 — Die Pruning-Regel als Messinstrument pruefen

**Language: Python**

## Kontext

Der WP-N1-Probelauf (132 Zellen, `outputs/wp_n1_dim1_probe/history.jsonl`) hat einen Defekt in der
Auswertungsregel sichtbar gemacht. `pruned_match` beurteilt eine gefundene Struktur, indem es Terme
mit kleinem Koeffizienten entfernt und den Rest mit der Wahrheit vergleicht. Die Schwelle steht in
`experiments/run_experiment.jl:239`:

```
threshold = max(1e-6, 1e-3 * max_abs)
```

`max_abs` ist der groesste Betrag unter den Koeffizienten **derselben Gleichung**. Die Schwelle ist
also relativ zum groessten Term.

**Das zerstoert wahre Terme, sobald ein Term gross ist.** Beispiel aus dem Lauf, System 5, Seed 123,
IC-Satz 1, neue Basis: Koeffizienten `1` = +9,809, `u1` = +7,8e-05, `u1^2` = -2,1e-03. Erwartet sind
`['1','u1^2']`. Die Schwelle betraegt 9,8e-03 und entfernt **beide** kleinen Terme — auch das echte
`u1^2`. Uebrig bleibt `['1']`, die Zelle gilt als Fehlschlag. Der Loss dieser Zelle ist 1,4e-07 und
ihr R2 0,9999999996.

Ueber die 66 exakten Zellen der neuen Basis klassifiziert sich das heute so: 29 Treffer, **12 Zellen
mit ueberlebendem ueberzaehligem Term**, **4 Zellen mit vom Pruning geloeschtem wahrem Term**, 21
Zellen, in denen ein wahrer Term nie gefunden wurde.

Seit WP-N1 stehen die Koeffizienten im Record (`model_terms` mit `term`, `term_index`,
`coefficient`), die Frage ist also vollstaendig aus vorhandenen Daten beantwortbar — **ohne einen
einzigen neuen Suchlauf**.

## Zweck

Feststellen, **wie stark die Bewertung von der Pruning-Regel abhaengt** und ob es eine Regel gibt,
die weniger Artefakte erzeugt. Das ist eine Messung ueber ein Messinstrument, keine Optimierung
eines Ergebnisses.

## Deliverables

### 1. Zerlegung der Fehlschlaege nach Ursache

Fuer beide Basen getrennt, je Gleichung, aus `model_terms` und den erwarteten Termen:

| Kategorie | Bedeutung |
|---|---|
| Treffer | beschnittene Menge gleich der erwarteten |
| ueberzaehliger Term ueberlebt | erwartete Menge ist Teilmenge, ein Fremdterm bleibt ueber der Schwelle |
| wahrer Term geloescht | ein erwarteter Term liegt **unter** der Schwelle und faellt weg |
| wahrer Term nie gefunden | erwartete Menge ist keine Teilmenge der gefundenen |

Die Kategorien sind in dieser Reihenfolge zu pruefen und schliessen einander aus. Berichte
zusaetzlich, in wie vielen Zellen **beide** Fehler zugleich auftreten, falls das vorkommt.

### 2. Sensitivitaet gegenueber der Regel

Rechne die Klassifikation fuer ein **Gitter** von Pruning-Regeln durch und berichte es vollstaendig:

- rein relativ: `rel * max_abs` mit `rel` in 1e-4, 1e-3 (heutiger Wert), 1e-2, 1e-1
- rein absolut: `abs` in 1e-8, 1e-6 (heutiger Boden), 1e-4, 1e-2
- die heutige Mischform `max(abs, rel * max_abs)` fuer die Kombinationen des Gitters

Fuer jede Regel: Trefferzahl und die drei Fehlerkategorien, je Basis.

**Keine Regel wird als die beste bezeichnet, keine wird empfohlen.** Eine Schwelle nach Sichtung der
Daten auszuwaehlen ist der Fehler, den WP-V1 fuer den Reopen-Schwellwert bereits benannt hat. Der
Auftrag ist, die Abhaengigkeit **sichtbar** zu machen: wie viele Zellen wechseln ihre Bewertung, und
ab wo ist die Klassifikation stabil.

### 3. Ein regelfreies Mass als Gegenprobe

Zusaetzlich eine Bewertung, die ohne Schwelle auskommt: der gefundene Termsatz **ohne jede
Beschneidung** gegen die Wahrheit (`raw_match`), sowie die Frage, ob die wahre Menge **Teilmenge**
der gefundenen ist. Letzteres ist die Obergrenze dessen, was Beschneiden ueberhaupt erreichen kann.

### 4. Beide Metriken, immer

Jede Tabelle traegt **beide** Kennzahlen: Strukturtreffer **und** den Anteil der Zellen mit
R2 > 0,9 (Design-Prinzip 9 in `CLAUDE.md`). Das gilt auch dort, wo die zweite Zahl langweilig
aussieht — gerade dort ist sie die Aussage.

## Verboten

- keine Aenderung an Julia-Code, insbesondere **nicht** an `experiments/run_experiment.jl` oder der
  dortigen Schwelle. Dieses WP **misst**, es aendert nichts.
- keine Aenderung an den WP-N1-Ergebnissen, an der Kampagne oder an der Analyse-Pipeline der
  A5-bis-A9-Reihe
- **keine Empfehlung fuer eine Schwelle**, weder im Code noch im Report
- **keine Figuren**
- keine Ergebnisse in `PAPER_1.md`, `CLAUDE.md` oder `DIARY.md`
- kein Mittelwert oder Median als alleinige Zusammenfassung
- kein `git add -A`, keine Git-Operationen

## Akzeptanzkriterium

Ein Skript unter `analysis/scripts/aggregate/`, ueber `--config` oder `--input` parametrisiert, das
`outputs/wp_n1_dim1_probe/history.jsonl` liest und nach `analysis/data/` schreibt; Tabellen als
`.csv` und `.tex` unter `analysis/tables/`. Die Zerlegung reproduziert fuer die heutige Regel die
bekannten Zahlen: alte Basis 30 Treffer von 36, neue Basis 29 von 66 mit 12 ueberlebenden Fremdtermen
und 4 geloeschten wahren Termen. Weicht deine Rechnung davon ab, ist das ein Befund und im Report zu
benennen, nicht anzugleichen.

Fehlerpfad an einer Fixture unter `analysis/fixtures/` belegen (z. B. ein Record ohne `model_terms`).

## Report

`codex/REPORT_WP_N2.md`. Enthaelt: die Kommandos, die Ursachenzerlegung fuer beide Basen, das
vollstaendige Regelgitter, die regelfreien Gegenproben, alle Tabellen mit beiden Metriken — und
einen Absatz dazu, **wie viele Zellen ihre Bewertung ueber das Gitter hinweg wechseln** und ob es
einen Bereich gibt, in dem die Klassifikation stabil ist.

# WP-A8 — Die deskriptiven Ergebnistabellen der Phase-B-Kampagne

**Language: Python**

## Kontext

Die Kampagne ist ausgewertet, was die *Tests* angeht: WP-A6 hat den gepaarten Pretuning-Kontrast
gerechnet (Strukturdifferenz haelt der Clusterung nicht stand), WP-A7 die verteilungsbewusste
Effektstaerke und die Seed-Kollaps-Messung (Verankerung ist strukturell, clusterfest p = 1e-5). Beide
sind abgeschlossen und werden hier **nicht wiederholt**.

Was fehlt, sind die deskriptiven Ergebnistabellen, die `PAPER_1.md` als Platzhalter fuehrt:
Fit-Qualitaet ueber alle 63 Systeme, Support-Findung auf den 20 exakten, R² auf den 43 Surrogaten,
die Stufenoekonomie-Zaehler, sowie Robustheit, Fehler und Stabilitaet.

**Dieses WP fuehrt keine Signifikanztests durch.** Es beschreibt. Jede Teststatistik, jeder p-Wert
und jede Aussage der Form „A ist besser als B" ist hier verboten — das ist in WP-A6/A7 entschieden
worden und faellt nicht erneut an. Die beiden Bedingungen stehen in den Tabellen nebeneinander, ohne
Wertung.

Datengrundlage: `experiments/paper1_phaseB_v1/run_registry.csv`, 756 Zeilen, geprueft durch
`analysis/scripts/aggregate/verify_campaign_registry.py`. Config:
`analysis/configs/paper1_phaseB_v1.json`.

## Teil 1 — Die letzte Konvertererweiterung

Fuer die Fehler- und Robustheitstabelle fehlen Felder. Ergaenze
`convert_campaign_history_to_run_registry.py` um genau diese neun und **keine weiteren**:

`solver_retcodes`, `optimizer_retcodes`, `total_diverged_solves`, `total_invalid_solves`,
`total_nonfinite_solves`, `total_solver_unstable_solves`, `total_step_limit_solves`,
`total_optimizer_limit_hits`, `total_optimizer_budget_stop_fits`

Die beiden Retcode-Felder sind Abbildungen und werden wie in WP-A7 als JSON in die Zelle
geschrieben. Danach Registry neu erzeugen und `verify_campaign_registry.py` erneut laufen lassen;
die Pruefung muss unveraendert durchlaufen. **Scheitert sie, ist das ein Abbruchgrund und kein
Anlass, die Pruefung anzupassen.**

## Teil 2 — Trennung von Aggregation und Darstellung

`analysis/CONVENTIONS.md` verbietet ausdruecklich ein Skript, das beides mischt. Also:

- ein Aggregationsskript unter `analysis/scripts/aggregate/`, das nach
  `analysis/data/paper1_phaseB_v1/` schreibt
- ein Tabellenskript unter `analysis/scripts/plot/`, das daraus nach
  `analysis/tables/paper1_phaseB_v1/` schreibt, als `.csv` **und** `.tex`

Beide ueber `--config` parametrisiert, keine harten Pfade.

## Teil 3 — Die Tabellen

Durchgaengige Regeln, die fuer **jede** Tabelle gelten:

- **Exakt und Surrogat werden nie in eine Kennzahl gemischt** (Design-Prinzip 8). Jede Tabelle weist
  sie getrennt aus oder gilt ausdruecklich nur fuer eine der beiden Klassen.
- **Die beiden IC-Saetze werden nicht weggemittelt** (WP-A4b). Sie sind eine eigene Achse.
- **Kein Mittelwert und kein Median als alleinige Zusammenfassung.** Verteilungen werden als
  Quantile 5/10/25/50/75/90/95 berichtet, Anteile ueber ein vollstaendiges Schwellengitter. Diese
  Regel steht seit WP-A7 in `CLAUDE.md`; sie entstand aus einem Fehler, der die Kampagne beinahe als
  ergebnislos haette erscheinen lassen.
- **`elapsed_s` ist keine Evidenz** (Design-Prinzip 7). Es darf in keiner Kostentabelle als
  Kostenmass auftreten. Kosten werden ueber `total_loss_evals`, `total_ode_solves` und
  `total_parameter_fits` ausgedrueckt. Wenn `elapsed_s` ueberhaupt erscheint, dann in einer eigenen
  Kontextspalte, die in der Tabellenbeschriftung als Nicht-Evidenz gekennzeichnet ist.

### T1 — Fit-Qualitaet, Surrogate (43 Systeme, 516 Zellen)

R²-Verteilung, aufgeschluesselt nach Bedingung, IC-Satz und Systemdimension. Quantile wie oben plus
Schwellengitter: Anteil der Zellen mit R² > 0,5 / 0,9 / 0,99 / 0,999. Das Gitter vollstaendig, keine
Schwelle hervorgehoben.

### T2 — Fit-Qualitaet, exakte Systeme (20 Systeme, 240 Zellen)

Loss-Verteilung auf `log10`, nach Bedingung, IC-Satz und Dimension. Zusaetzlich R², da es laut
`CLAUDE.md` fuer 43 von 63 Systemen die Metrik ist, hier aber auch fuer die exakten vorliegt —
weise es getrennt aus und vermenge es nicht mit T1.

### T3 — Support-Findung, nur exakte Systeme

`exact_support_match` je System, IC-Satz und Bedingung (also je 3 Seeds), plus eine Zusammenfassung
je Dimension. Rein deskriptiv, Zaehlungen und Anteile. **Kein Test, kein Vergleichsurteil.**

Der bekannte Nullbefund auf dim 3 und dim 4 muss in der Tabelle sichtbar sein und darf nicht durch
Aggregation ueber Dimensionen verschwinden.

### T4 — Stufenoekonomie

Fuer Claim B aus der Kampagne, ergaenzend zum Regressionsgitter. Je Bedingung, IC-Satz und Dimension:
`final_stage`, `stage_caps`, `eq_final_stages`, `n_levels`, und die Zaehler `total_loss_evals`,
`total_ode_solves`, `total_parameter_fits` als Quantile.

`stage_overshoot`, `wasted_levels` und `eq_overshoot` sind **nur auf exakten Systemen definiert**.
Auf Surrogaten ist `expected_stage` nominell, weshalb `eq_overshoot` dort in allen 516 Zellen
ungleich null ist — das ist eine Definitionsgrenze und keine Messung. Diese drei Spalten erscheinen
ausschliesslich in der exakten Haelfte der Tabelle, und die Tabellenbeschriftung sagt warum.

### T5 — Robustheit und Fehlermodi

Aus den neun neuen Feldern: Haeufigkeit der Solver- und Optimizer-Retcodes, Zaehler fuer divergente,
ungueltige, nichtfinite und instabile Solves, Schrittlimit-Treffer, Optimizer-Limit-Treffer und
Budget-Stopps. Nach Bedingung und getrennt nach exakt/Surrogat. Zusaetzlich die Zahl der Zellen mit
`success == True` und mit gesetztem `failure_reason` — erwartet werden 756 erfolgreiche Zellen und
keine Fehler; **pruefe das und melde jede Abweichung, statt sie zu glaetten**.

## Teil 4 — Abbruchbedingungen

Wie in WP-A6/A7: fehlende oder leere Pflichtfelder, abweichende Zellzahlen, Sentinel-Loss `1e6`.
Zusaetzlich: ein Retcode-Feld, das sich nicht als JSON lesen laesst. Kein stiller Ausschluss von
Zellen. Fehlerpfad an einer Fixture unter `analysis/fixtures/` belegen.

## Verboten

- keine Aenderung an `src/`, `studies/`, `experiments/` oder Julia-Code
- keine Aenderung an `verify_campaign_registry.py`, an den A6/A7-Skripten oder ihren Ergebnissen
- keine weiteren Konverterspalten als die neun genannten
- **keine Figuren** — dieses WP produziert Tabellen
- **keine Signifikanztests, keine p-Werte, keine Vergleichsurteile zwischen den Bedingungen**
- **keine Ergebnisse in `PAPER_1.md`, `CLAUDE.md` oder `DIARY.md`** — der Report berichtet, gewertet
  wird von Claude; die Platzhalter in `PAPER_1.md` fuellt Claude
- `elapsed_s` nie als Kostenmass
- kein `git add -A`, keine Git-Operationen

## Akzeptanzkriterium

Die neu erzeugte Registry traegt die neun zusaetzlichen Spalten und `verify_campaign_registry.py`
laeuft unveraendert durch. Beide Skripte laufen fehlerfrei, T1 bis T5 liegen als `.csv` und `.tex`
unter `analysis/tables/paper1_phaseB_v1/`. Jede Verteilungstabelle traegt die sieben Quantile, jede
Anteilstabelle das vollstaendige Gitter. Auf der Fixture bricht das Aggregationsskript mit Exit-Code
ungleich null ab.

## Report

`codex/REPORT_WP_A8.md`. Enthaelt: die Kommandos, die unveraenderte Ausgabe der Invariantenpruefung,
alle fuenf Tabellen im Report selbst wiedergegeben (nicht nur ihre Pfade), das Ergebnis der
Erfolgs-/Fehlerpruefung aus T5 — und einen Absatz dazu, ob in den Robustheitszaehlern etwas steht,
das der Annahme „756 fehlerfreie Zellen" widerspricht.

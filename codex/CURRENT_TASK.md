# WP-A7 — Verteilungsbewusste Effektstaerke und die Seed-Kollaps-Messung

**Language: Python**

## Kontext

WP-A6 hat den gepaarten Pretuning-Kontrast gerechnet. Zwei Ergebnisse stehen, beide committet:

1. Die Strukturdifferenz auf exakten Systemen (13 nur `pretune_off`, 3 nur `pretune_on` unter 120
   Paaren) **haelt der Clusterung nicht stand**: exakter McNemar p = 0,021, clusterfeste Permutation
   p = 0,218. Die 120 Paare stammen aus 20 Systemen. Das ist abgeschlossen und wird hier nicht
   wiederholt.
2. Die berichtete Effektstaerke fuer R² und Loss ist **unbrauchbar** — nicht falsch gerechnet,
   sondern falsch gewaehlt. Das zu reparieren ist der erste Teil dieses Auftrags.

Bestehende Bausteine, auf denen aufgesetzt wird:
`analysis/scripts/aggregate/analyze_pretuning_contrast.py` (Paarung, Clusterpermutation,
System-Bootstrap), `analysis/configs/paper1_phaseB_v1.json`,
`experiments/paper1_phaseB_v1/run_registry.csv`, geprueft durch `verify_campaign_registry.py`.

Paarung wie gehabt: Schluessel aus `system_id`, `seed`, `initial_condition_set`; 378 vollstaendige
Paare, 120 exakt, 258 Surrogat; Bedingung aus `variant_slug`.

## Teil 1 — Der Konverter muss mehr Felder tragen

`convert_campaign_history_to_run_registry.py` laesst 53 der 77 Record-Felder fallen
(`codex/REPORT_WP_A5.md`). Teil 2 dieses Auftrags braucht davon `support_terms`. Ergaenze die
Spaltenliste um genau diese sieben Felder und **keine weiteren**:

`support_terms`, `condition`, `use_pretuning`, `n_levels`, `eq_overshoot`, `eq_final_stages`,
`stage_caps`

Die letzten vier und `support_terms` sind verschachtelte Werte (Beispiele: `support_terms` ist
`[['u1', 'u1^2', 'cos(u1)']]`, `stage_caps` ist `[5]`, `eq_overshoot` kann `null` sein). Sie werden
als JSON in die Zelle geschrieben, damit sie verlustfrei zurueckgelesen werden koennen — nicht als
Pythons `str()`-Darstellung, die sich nicht sicher parsen laesst.

Anschliessend die Registry neu erzeugen und `verify_campaign_registry.py` erneut laufen lassen. Die
Pruefung muss unveraendert durchlaufen; halte ihre Ausgabe im Report fest. **Wenn sie scheitert, ist
das ein Abbruchgrund und kein Anlass, die Pruefung anzupassen.**

## Teil 2 — Die Auswertung

Erweitere `analyze_pretuning_contrast.py` oder lege ein zweites Skript daneben — entscheide nach
Lesbarkeit und begruende die Wahl kurz im Report. Alles unter `analysis/scripts/aggregate/`,
Ergebnis maschinenlesbar nach `analysis/data/paper1_phaseB_v1/`.

### 2a — Effektstaerke, die die Verteilung abbildet

Fuer R² (258 Surrogat-Paare) und Loss (getrennt nach exakt und Surrogat, nie gemischt):

- **Die Verteilung selbst**, nicht ihre Mitte: die Quantile 5, 10, 25, 50, 75, 90, 95 der
  Paardifferenz. Fuer den Loss auf `log10` wie in WP-A6.
- **Anteil der Paare jenseits einer Schwelle**, ueber ein **Gitter** von Schwellen, jeweils mit
  clusterfestem Bootstrap-Intervall auf Systemebene. Fuer R²: 1e-4, 1e-3, 1e-2, 1e-1. Fuer den Loss:
  Fold-Change-Schwellen 1,1 / 2 / 10 / 100.

  Das Gitter wird **vollstaendig berichtet**. Es wird keine Schwelle ausgewaehlt, hervorgehoben oder
  als *die* Effektstaerke bezeichnet — genau diese Auswahl nach Sichtung der Daten waere
  Schwellenschieberei und ist hier verboten.
- **Vorzeichenasymmetrie**: Zahl der Paare zugunsten jeder Bedingung und die Zahl der exakten
  Nullen, geprueft mit demselben clusterfesten Permutationsverfahren wie in WP-A6.

**Verboten:** ein Median als alleinige Effektstaerke, an irgendeiner Stelle der Ausgabe. Er war der
Fehler, der dieses WP ausgeloest hat. Er darf als **eines** von sieben Quantilen erscheinen, nie
allein.

### 2b — Die Seed-Kollaps-Messung

Die Beobachtung, die dieses WP traegt: unter `pretune_on` liefern die drei Seeds sehr viel haeufiger
dasselbe Ergebnis als unter `pretune_off`. Eine Handmessung ergab 96 von 126 Gruppen gegen 34 von
126 auf R². Diese Messung gehoert sauber in die Pipeline, nicht in eine Notiz.

Gruppierungseinheit ist das Tripel aus System, IC-Satz und Bedingung — je drei Seeds, 126 Gruppen je
Bedingung. Zu berichten:

- Anteil der Gruppen, deren drei Seeds **dasselbe Ergebnis** liefern, getrennt fuer drei Zielgroessen:
  `r2`, `loss` und das **gefundene Support-Muster** aus `support_terms`. Das Support-Muster ist der
  interessanteste der drei, weil er Strukturgleichheit misst statt Zahlengleichheit; er ist der
  Grund, warum Teil 1 noetig war.
- Die Gleichheitstoleranz ist ein **CLI-Parameter**, kein fest verdrahteter Wert. Vorgabe: relative
  Toleranz 1e-12. Begruende im Report, wie du absolute und relative Toleranz behandelst, besonders
  fuer Losswerte nahe null. Der Support-Vergleich ist exakt und braucht keine Toleranz — dokumentiere
  aber, ob Reihenfolge innerhalb einer Gleichung normalisiert wird und warum.
- Die Streuung je Gruppe, nicht nur die Ja/Nein-Aussage: Spannweite bei `r2`, Spannweite von
  `log10(loss)`.
- **Der Vergleich zwischen den Bedingungen ist gepaart**: dieselbe (System, IC)-Gruppe unter beiden
  Bedingungen, also 126 Paare aus 63 Systemen. Naiver exakter McNemar auf „kollabiert ja/nein" **und**
  clusterfeste Permutation auf Systemebene, beide nebeneinander wie in WP-A6.

Exakte und Surrogat-Systeme werden auch hier getrennt ausgewiesen (Design-Prinzip 8).

### 2c — Abbruchbedingungen

Wie in WP-A6: unvollstaendige Paarung, abweichende Paarzahlen, Sentinel-Loss `1e6`, fehlendes `r2`,
leere Zielgroesse. Zusaetzlich: eine Gruppe, die nicht genau drei Seeds hat, und ein
`support_terms`-Feld, das sich nicht als JSON lesen laesst. Kein stiller Ausschluss.

Fehlerpfad an einer Fixture unter `analysis/fixtures/` belegen.

## Verboten

- keine Aenderung an `src/`, `studies/`, `experiments/` oder Julia-Code
- keine Aenderung an `verify_campaign_registry.py` und keine Abschwaechung seiner Invarianten
- keine weiteren Konverterspalten als die sieben genannten
- **keine Figuren**
- **keine Ergebnisse in `PAPER_1.md`, `CLAUDE.md` oder `DIARY.md`** — der Report berichtet, gewertet
  wird von Claude
- keine Signifikanzaussage je Dimension, je System oder je IC-Satz
- keine Auswahl einer bevorzugten Schwelle aus dem Gitter
- kein `git add -A`, keine Git-Operationen

## Akzeptanzkriterium

Die neu erzeugte Registry traegt die sieben zusaetzlichen Spalten, `verify_campaign_registry.py`
laeuft unveraendert durch. Die Auswertung liefert fuer R² und Loss die sieben Quantile und das
vollstaendige Schwellengitter mit clusterfesten Intervallen, und fuer alle drei Zielgroessen der
Kollapsmessung beide Testverfahren nebeneinander. Auf der Fixture bricht das Skript mit Exit-Code
ungleich null ab.

## Report

`codex/REPORT_WP_A7.md`. Enthaelt: die Kommandos, die unveraenderte Ausgabe der Invariantenpruefung,
die Quantiltabellen, das vollstaendige Schwellengitter, die Kollapstabelle fuer alle drei
Zielgroessen mit beiden p-Werten, die Begruendung der Toleranzbehandlung und der Support-
Normalisierung — und einen Absatz dazu, ob die Kollapsmessung auf dem Support-Muster dasselbe Bild
zeigt wie auf R².

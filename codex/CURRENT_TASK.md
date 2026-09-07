# WP-A6 — Der Pretuning-Kontrast, gepaart und clusterfest

**Language: Python**

## Kontext

Die Phase-B-Kampagne liegt vollständig in der Analyse-Pipeline (WP-A5). Die konvertierte Registry
ist `experiments/paper1_phaseB_v1/run_registry.csv`, 756 Zeilen, geprüft durch
`analysis/scripts/aggregate/verify_campaign_registry.py`.

Die Kampagne existiert für **einen** Kontrast: `evogrow_v2_2_stage_capped` mit `pretuning=true`
gegen `pretuning=false`, alles andere identisch. Dieses WP entscheidet, ob dieser Kontrast eine
Aussage trägt. Es ist der Test, von dem die Gewichtung aller späteren Tabellen abhängt.

**Die Paarung ist bereits verifiziert** und darf als gegeben angenommen, muss aber vom Skript selbst
geprüft werden: Schlüssel ist das Tripel aus `system_id`, `seed` und `initial_condition_set`. Es gibt
378 vollständige Paare, davon **120 auf exakten Systemen** und **258 auf Surrogaten**. Kein Paar ist
unvollständig. In der Registry unterscheidet `variant_slug` die beiden Bedingungen
(`..._pretune_on` / `..._pretune_off`); eine Spalte `condition` gibt es dort nicht.

Zwei weitere geprüfte Randbedingungen: es gibt **keine** Zelle mit dem Sentinel-Loss `1e6`, und `r2`
ist in allen 756 Zeilen numerisch belegt. Beides muss das Skript trotzdem prüfen und bei Verletzung
abbrechen — die Randbedingung gilt für diese Kampagne, nicht für alle künftigen.

## Das methodische Problem, das den Auftrag bestimmt

Die 120 exakten Paare stammen aus nur **20 Systemen** — sechs Paare je System (3 Seeds x 2 IC-Sätze).
Die 258 Surrogat-Paare stammen aus 43 Systemen. Paare innerhalb eines Systems sind **nicht
unabhängig**: sie teilen dieselbe Dynamik, dieselbe Repräsentierbarkeit und dieselbe Schwierigkeit.

Ein gewöhnlicher McNemar-Test behandelt alle 120 Paare als unabhängige Ziehungen und wird deshalb
einen zu kleinen p-Wert liefern. Die effektive Stichprobengröße liegt näher an 20 als an 120.

**Deshalb ist die Kernanforderung dieses WP nicht ein Test, sondern zwei — und die ehrliche
Hauptaussage ist die clusterfeste.** Beide werden berichtet, nebeneinander, mit der Differenz als
eigenem Ergebnis. Wenn die beiden Verfahren zu verschiedenen Schlüssen kommen, ist das ein Befund und
kein Grund, sich das günstigere auszusuchen.

## Deliverables

### 1. Ein Auswertungsskript

Neu unter `analysis/scripts/aggregate/`, benannt nach `<verb>_<subject>.py`, parametrisiert über
`--config` nach dem Muster der bestehenden Skripte, Sollwerte der Paarung als CLI-Parameter mit den
oben genannten Zahlen als Vorgabe. Es schreibt sein Ergebnis als maschinenlesbare Datei nach
`analysis/data/paper1_phaseB_v1/` und gibt eine lesbare Zusammenfassung auf stdout aus.

Es wertet **drei** Zielgrößen aus, exakte und Surrogat-Systeme strikt getrennt (Design-Prinzip 8 —
sie werden nie in eine Kennzahl gemischt):

**(a) Strukturfindung, exakte Systeme, 120 Paare.** Zielgröße ist `exact_support_match`, binär.

- Die vollständige 2x2-Kontingenztafel der Paare wird berichtet, nicht nur die diskordanten Zellen.
- Primärtest naiv: **exakter McNemar** über die diskordanten Paare, also der zweiseitige exakte
  Binomialtest mit p = 0.5. **Kein** Chi-Quadrat, **keine** Stetigkeitskorrektur — die Zahl der
  diskordanten Paare ist klein, die Approximation dort unbrauchbar.
- Primärtest clusterfest: ein **Permutationstest**, der die Bedingungszuweisung **innerhalb jedes
  Systems** vertauscht und so die Clusterstruktur erhält. Prüfgröße ist die Differenz der
  Trefferzahlen zwischen den Bedingungen. Die Zahl der Permutationen ist ein benannter Konstantenwert
  im Skript, der Zufallsgenerator wird mit einem ebenfalls benannten Seed initialisiert, mit
  Kommentar — das ist die einzige erlaubte Randomisierung (`analysis/CONVENTIONS.md`).

**(b) Fit-Qualität, Surrogat-Systeme, 258 Paare.** Zielgröße ist `r2`.

- Gepaarter **Wilcoxon-Vorzeichen-Rang-Test** über die Paardifferenzen.
- Derselbe clusterfeste Permutationstest wie in (a), Prüfgröße ist der Median der Paardifferenzen.
- Effektstärke: Median der Paardifferenz mit Bootstrap-Konfidenzintervall, wobei **auf Systemebene
  gebootstrappt wird**, nicht auf Paarebene — sonst wiederholt sich derselbe Unabhängigkeitsfehler.

**(c) Loss, alle 378 Paare.** Der Loss überspannt siebzehn Größenordnungen (4,6e-15 bis 5,8e+2),
deshalb wird auf `log10` gerechnet oder rangbasiert getestet; begründe die Wahl im Report. Getrennt
nach exakt und Surrogat berichten, nie zusammengefasst.

Für jede Zielgröße gehören in die Ausgabe: die Prüfgröße, der p-Wert beider Verfahren, die
Effektstärke mit Intervall, und die Zahl der eingehenden Paare. **Ein p-Wert ohne Effektstärke ist
kein Ergebnis.**

### 2. Deskriptive Aufschlüsselung nach Dimension

Die Kontingenztafel aus (a) zusätzlich je Systemdimension, als **rein beschreibende** Tabelle.

**Ausdrücklich verboten:** ein Signifikanztest je Dimension. Die Zellen sind winzig, und vier Tests
auf denselben Daten wären unkorrigiertes multiples Testen. Die Aufschlüsselung zeigt, *wo* der
Unterschied sitzt, sie behauptet nichts über ihn.

### 3. Abbruchbedingungen

Das Skript bricht mit Exit-Code ungleich null ab, wenn: die Paarung unvollständig ist, die Zahl der
Paare von den Sollwerten abweicht, eine Zelle den Sentinel-Loss `1e6` trägt, `r2` fehlt, oder eine
Zielgröße in einer der beiden Bedingungen leer ist. Kein stiller Ausschluss von Zellen — wenn Daten
fehlen, ist das ein Fehler und keine Filterbedingung.

Belege den Fehlerpfad an mindestens einer Fixture unter `analysis/fixtures/` mit unvollständiger
Paarung.

### 4. Abhängigkeiten

`analysis/requirements.txt` enthält bisher nur `sympy`. Falls du `scipy` für den Wilcoxon-Test
verwendest, trage es mit **fester** Version ein (installiert ist 1.13.1, kein `>=`,
`analysis/CONVENTIONS.md`). Den exakten Binomialtest und den Permutationstest bitte ohne
Fremdbibliothek — `math.comb` genügt und macht die Rechnung nachlesbar.

### 5. SCRIPTS.md

Das neue Skript in die Tabelle in Abschnitt 7 eintragen.

## Verboten

- keine Änderung an `src/`, `studies/`, `experiments/` oder irgendeinem Julia-Code
- keine Änderung an `run_registry.csv`, am Konverter oder am Prüfskript aus WP-A5
- **keine Figuren** — dieses WP produziert Zahlen, keine Grafiken
- **keine Eintragung von Ergebnissen in `PAPER_1.md`, `CLAUDE.md` oder `DIARY.md`.** Die
  wissenschaftliche Wertung trifft Claude, nicht das WP. Der Report berichtet, er schließt nicht.
- keine Signifikanzaussage je Dimension, je System oder je IC-Satz
- keine Vermischung exakter und Surrogat-Zellen in einer Kennzahl
- kein `git add -A`, keine Git-Operationen; Dateien im Arbeitsbaum liegen lassen

## Akzeptanzkriterium

Das Skript läuft auf der Phase-B-Registry fehlerfrei durch, meldet 378 Paare gesamt, 120 exakt und
258 Surrogat, und liefert für alle drei Zielgrößen **beide** Verfahren mit Effektstärke. Auf der
Fixture mit unvollständiger Paarung bricht es mit Exit-Code ungleich null ab. Die Ergebnisdatei liegt
unter `analysis/data/paper1_phaseB_v1/`.

## Report

`codex/REPORT_WP_A6.md`. Enthält: die exakten Kommandos, die vollständige Kontingenztafel, beide
p-Werte je Zielgröße nebeneinander, die Effektstärken mit Intervallen, die deskriptive
Dimensionstabelle, die Begründung der Loss-Transformation, die Zahl der Permutationen und den
verwendeten Seed — und einen ausdrücklichen Absatz dazu, **ob und wie weit naives und clusterfestes
Verfahren auseinanderlaufen**.

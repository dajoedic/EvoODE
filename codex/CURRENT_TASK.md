# WP-N4 — Die Referenzanpassung mit Mehrfachstart

**Language: Julia**

## Kontext

WP-N3 hat je Zelle **einen** Parameterfit gerechnet (`_fit_fixed_structure` in
`studies/regression/wp_n3_oracle_refit.jl`: `Random.seed!(seed)`, dann ein einziger
`fit_parameters`-Aufruf). Ergebnis auf 102 Zellen:

| Anpassung | Sentinel-Loss 1e6 |
|---|---|
| Originallauf | **0 / 102** |
| Oracle-Beschneidung | 11 / 102 |
| wahre Struktur | **15 / 102** |

Die Referenzanpassung war ausserdem in 72 von 102 Zellen schlechter als der Originallauf.

**Das ist kein fairer Vergleich, und der Grund ist der Versuchsaufbau.** Der Originallauf hat ueber
die Suche hinweg tausende Anpassungen gerechnet, jede aus einem eigenen Zufallsstart
(`0.1 .* randn(n_params)` in `bfgs.jl:269`, weil unter `pretuning=false` kein `p0` uebergeben wird),
und behaelt davon die beste. WP-N3 stellt dagegen **einen** Versuch. Der Vergleich lautet damit
"ein Versuch gegen das Beste aus tausenden" und misst ueberwiegend die Zahl der Versuche.

## Zweck

Die Frage sauber trennen:

> Scheitert die Anpassung an die wahre Struktur, **weil ein einzelner Versuch unzuverlaessig ist**,
> oder **weil der Optimierer diese Strukturen grundsaetzlich nicht anpassen kann**?

## Deliverables

### 1. Mehrfachstart statt Einzelversuch

Erweitere die Anpassung um wiederholte Zufallsstarts und behalte je Zelle das **beste** Ergebnis
nach Loss. Das gilt fuer **beide** Strukturen aus WP-N3 — Oracle-Beschneidung und wahre Struktur.

Die Zahl der Starts ist ein CLI-Parameter, Vorgabe 10. Die Startwerte muessen **deterministisch aus
dem Zellen-Seed abgeleitet** sein, damit der Lauf reproduzierbar ist; halte im Report fest, wie du
sie ableitest.

### 2. Die eigentliche Messung: eine Kurve, keine Zahl

Berichte die Ergebnisse **als Funktion der Startzahl** k = 1, 2, 3, 5, 10. Das ist der Kern dieses
WP: eine einzelne Zahl bei k = 10 wuerde die Frage nicht beantworten.

Aus denselben 10 Laeufen laesst sich jedes kleinere k ableiten, indem nur die ersten k Starts
betrachtet werden — rechne **nicht** fuer jedes k neu, sondern werte die Startfolge kumulativ aus,
und beschreibe im Report, dass die k-Werte dadurch verschachtelt und nicht unabhaengig sind.

Je k und je Struktur (Oracle, wahr), getrennt nach Basis:

- Zahl der Zellen mit Sentinel-Loss 1e6
- Loss-Quantile 5/10/25/50/75/90/95
- **beide Metriken** (Design-Prinzip 9): Strukturtreffer **und** Anteil R2 > 0,9
- Zahl der Zellen, in denen die Anpassung den Originallauf erreicht oder uebertrifft

### 3. Was der Report entscheiden muss

> **Faellt die Sentinel-Quote der wahren Struktur mit wachsendem k gegen null?** Dann ist ein
> einzelner Versuch unzuverlaessig, und der Mehrfachstart ist eine tragende Komponente des
> Verfahrens — kein Nebeneffekt von `pretuning=false`.
>
> **Bleibt sie auf einem Plateau?** Dann gibt es Strukturen, die der Optimierer grundsaetzlich nicht
> anpasst. Benenne diese Zellen einzeln mit System, IC-Satz und Seed — sie waeren der Ausgangspunkt
> der naechsten Untersuchung.

Berichte in beiden Faellen, **wie viele Starts noetig sind**, um die Sentinel-Quote unter die des
Originallaufs (null von 102) zu druecken, falls das ueberhaupt eintritt.

### 4. Ausfuehrung

Kosten: 102 Zellen mal zwei Strukturen mal 10 Starts, **keine Struktursuche**. Zum Vergleich hat
eine einzelne Kampagnenzelle tausende Anpassungen gerechnet.

**Du kannst Julia in dieser Umgebung nicht starten** (`A specified logon session does not exist`) —
das ist in WP-N1 und WP-N3 zweimal passiert. Schreibe den Code, pruefe ihn statisch so sorgfaeltig
wie in WP-N3b, melde `blocked` und **erfinde keine Ergebnisse**. Claude fuehrt aus.

Halte im Report **zwei** Kommandos fest: einen kurzen Testlauf ueber wenige Zellen via `--limit` und
den vollen Lauf. Der `--limit`-Pfad aus WP-N3b hat sich bewaehrt und ist beizubehalten.

Ergebnisse in ein eigenes Verzeichnis unter `outputs/`, nie mit WP-N3-Daten in einer Datei
zusammengefuehrt.

## Verboten

- keine Aenderung an der Suchlogik, der Basis, am Stage-Cap oder an `pruned_match`
- keine Aenderung an `outputs/wp_n1_dim1_probe/`, `outputs/wp_n3_oracle_refit/`, der Kampagne oder
  den A5-bis-A9-Skripten
- **kein Pretuning als Startwert** — die Frage ist, was zufaellige Starts leisten; ein OLS-Warmstart
  waere eine andere Untersuchung
- **keine Figuren**
- keine Ergebnisse in `PAPER_1.md`, `CLAUDE.md` oder `DIARY.md`
- `elapsed_s` nie als Kostenmass
- kein `git add -A`, keine Git-Operationen

## Akzeptanzkriterium

Bei k = 1 muss das Ergebnis die WP-N3-Zahlen **reproduzieren**, sofern der erste Startwert identisch
abgeleitet wird: 15 Sentinel-Zellen bei der wahren Struktur, 11 bei der Oracle-Beschneidung. Weicht
es ab, ist das ein Befund und im Report zu benennen, nicht anzugleichen — und dann ist die
Ableitung der Startwerte die wahrscheinliche Ursache und zu dokumentieren.

## Report

`codex/REPORT_WP_N4.md`. Enthaelt: die Kommandos, die Ableitung der Startwerte, die Kurventabellen
ueber k mit **beiden** Metriken, die Antwort auf die Entscheidungsfrage aus Abschnitt 3, und — falls
ein Plateau bleibt — die Liste der nicht anpassbaren Zellen.

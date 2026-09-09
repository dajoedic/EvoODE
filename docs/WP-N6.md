# WP-N6 — EvoODE gegen SINDy: die erste Baseline

**Messung:** 2026-09-09 · `git 731b7cf` · `pysindy 2.1.0`
**Daten:** `analysis/data/wp_n6_sindy_baseline/` · **Skript:** `analysis/scripts/aggregate/run_wp_n6_sindy_baseline.py`
**Rohbericht:** `codex/reports/REPORT_WP_N6.md`

---

## Warum diese Messung

EvoODE ist in der gesamten Projektlaufzeit **nie gegen ein fremdes Verfahren gemessen worden**. Alle
Vergleiche liefen gegen frühere EvoODE-Varianten — v1 gegen v2.2 gegen v3 gegen die gecappte
Fassung. Damit war unbekannt, ob die Zahlen des Projekts gut oder schlecht sind.

Diese Messung liefert die fehlende Vergleichszahl.

## Versuchsaufbau

SINDy bekommt **exakt dieselben Trajektorien** wie EvoODE, nach dem Phase-B-Protokoll
(`docs/paper1_odebench_protocol_alignment.md` §3):

- alle 63 ODEBench-Systeme, beide Anfangswertsätze
- 512 Punkte über t ∈ [0, 10], Abstand 10/511, beide Endpunkte
- selbst integriert bei Toleranz 1e-9; die **mitgelieferten** Trajektorien wurden nicht verwendet,
  weil der Audit dort MSE-Böden bis 2,5e-2 gemessen hat

Zehn Konfigurationen: Polynomgrade 2 bis 5, einmal zusätzlich mit `sin`/`cos`, je zwei
STLSQ-Schwellen (0,01 und 0,1). **Keine wurde ausgewählt** — dieselbe Regel wie beim Pruning-Gitter
in WP-N2. Berichtet wird das vollständige Gitter; wo unten eine einzelne Zahl steht, ist es das
Maximum über die zehn.

Strukturtreffer verwenden dieselbe Pruning-Regel wie EvoODE, `max(1e-6, 1e-3 · max_abs)` je Gleichung
(`experiments/run_experiment.jl:239`), angewandt auf SINDys Koeffizientenmatrix.

## Ergebnis, Dimension 1

Nur diese Klasse ist vergleichbar, weil EvoODEs Generalisierungszahlen aus dem eindimensionalen
Probelauf stammen (WP-N5).

| Anteil R² > 0,9 | SINDy | EvoODE |
|---|---|---|
| Rekonstruktion | 44/46 = **95,7 %** | 126/132 = **95,5 %** |
| Generalisierung | 28/46 = **60,9 %** | 90/132 = **68,2 %** |

**Rekonstruktion:** Modell auf einem Anfangswert anpassen, von demselben integrieren.
**Generalisierung:** dasselbe Modell, Parameter unverändert, vom *anderen* Anfangswert integrieren.

Ein Unentschieden auf der Rekonstruktion, EvoODE vorn auf der Generalisierung.

## Die Kostenzeile

| | Anpassungen je Zelle |
|---|---|
| SINDy | **1 bis 4** lineare Regressionen (eine je Gleichung) |
| EvoODE | **~410** nichtlineare Fits (Median der Kampagne), jeder mit ODE-Integrationen |

Rund zwei Größenordnungen. Für ein Verfahren, dessen Leitthese Effizienz ist, gehört diese Zahl
neben jede Trefferquote.

## Über alle 63 Systeme

| SINDy, bestes Gitterergebnis | |
|---|---|
| Rekonstruktion R² > 0,9 | 43/63 = 68,3 % |
| Generalisierung R² > 0,9 | 30/63 = 47,6 % |
| Strukturtreffer, alle Systeme | 19/63 |
| Strukturtreffer, die 20 für EvoODE darstellbaren | 11/20 |
| Strukturtreffer, die 40 für SINDy darstellbaren | 17/40 |

Der EvoODE-Kampagnenwert von 80,7 % ist **kein Gegenstück** dazu, siehe Vorbehalt 4.

## Vorbehalte

Diese vier gehören in jede Nennung der Zahlen.

**1. Die Systemmengen sind nicht deckungsgleich.** SINDys 46 Zellen sind alle 23 eindimensionalen
ODEBench-Systeme × 2 Anfangswertsätze. EvoODEs 132 sind **11 ausgewählte** Systeme × 3 Seeds × 2
Anfangswertsätze × 2 Basen. Die unterschiedliche Zellzahl kommt aus der Stochastik unserer Suche
(Seeds) und den zwei Basen, nicht aus der Abdeckung. Wir vergleichen eine kuratierte Teilmenge gegen
die volle Klasse; ob unsere 11 leichter sind als der Durchschnitt der 23, ist ungeprüft.

**2. SINDys Zahl ist ein Maximum über zehn Konfigurationen.** Das ist ein leichter Vorteil zu seinen
Gunsten, bewusst so gewählt, damit die Baseline nicht kleingerechnet wird.

**3. Protokollunterschied bei den Ableitungen.** SINDy braucht sie (`FiniteDifference(order=2)`),
EvoODE nicht. Unsere Daten sind rauschfrei — genau der Fall, in dem numerische Differentiation
harmlos ist. Der verrauschte Fall ist **ungemessen**.

**4. Über alle 63 Systeme existiert kein Gegenstück.** Die Aggregationseinheiten unterscheiden sich
(756 Kampagnenzellen mit drei Seeds und zwei Bedingungen gegen 63 Zellen je Konfiguration und
Richtung), und EvoODEs Generalisierung über alle Dimensionen ist gar nicht gerechnet, weil den
Kampagnenzellen die Koeffizienten fehlen (siehe WP-N5).

**5. Integrator.** SINDy-Seite `DOP853`, EvoODE `Tsit5`, beide bei 1e-9 auf identischem Gitter. Die
Gitterprüfung bestätigt 126 von 126 Zellen. Der Abgleich lief allerdings gegen die *mitgelieferten*
Trajektorien, nicht direkt gegen unsere — die Übereinstimmung folgt aus gleicher Toleranz und
gleichem Gitter, ist aber nicht unmittelbar gemessen.

## Einordnung

Die Ausgangsfrage war, ob EvoODEs Zahlen gut oder peinlich sind. Die Antwort lautet **weder noch**,
und sie verschiebt die Beweislast: Ein Verfahren, das gleichauf liegt und hundertmal mehr rechnet,
muss seinen Mehrwert woanders zeigen. Drei Kandidaten, alle ungemessen:

- **Rauschen.** SINDys Vorteil hängt an sauberen Ableitungen. Dort setzt die Literatur den Vorteil
  trajektorienbasierter Verfahren an, und ODEFormer berichtet, sein Vorsprung wachse mit Rauschen
  und Unterabtastung. Wir haben ausschließlich rauschfrei gemessen.
- **Gekoppelte Systeme.** Der erklärte Fokus der Arbeit — zugleich die härteste bekannte Grenze:
  null Strukturtreffer auf Dimension 3 und 4 in 60 von 60 exakten Kampagnenzellen.
- **Der Suchweg selbst.** EvoODE erzeugt eine nachvollziehbare Wachstumsgeschichte; SINDy eine
  Koeffizientenmatrix. Ob das ein Beitrag ist oder ein Nebenprodukt, ist offen.

## Verwandt

Die Kostenzeile hängt an `docs/WP-N4.md`: Ein **einzelner** Parameterfit scheitert bei EvoODE in 15 %
der Fälle, selbst bei vorgelegter richtiger Struktur; drei Zufallsstarts beseitigen alle
Totalausfälle. Ein Teil der 410 Anpassungen ist damit Wiederholung, nicht Suche — und potenziell
umverteilbar.

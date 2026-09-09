# WP-N4 — Das Neustart-Budget der Parameteranpassung

**Messung:** 2026-09-09 · `git a78346f`
**Daten:** `outputs/wp_n4_multistart_refit/` · **Skript:** `studies/regression/wp_n4_multistart_refit.jl`
**Rohbericht:** `codex/REPORT_WP_N4.md` · **Vorläufer:** WP-N3 (`codex/REPORT_WP_N3.md`)

---

## Was *k* bezeichnet

Die Gleichungsstruktur steht fest, etwa `ẋ = a·x + b·x²`. Gesucht sind nur noch die Zahlen `a` und
`b`. Dafür läuft ein BFGS-Optimierer, und der braucht Anfangswerte. Ohne Pretuning werden sie
zufällig gezogen — `0.1 .* randn(n_params)` (`src/optimize/bfgs.jl:269`, greift wenn kein `p0`
übergeben wird). Von dort läuft BFGS bergab und landet im richtigen Optimum, in einem Nebenminimum,
oder er scheitert ganz.

**k ist die Anzahl der Anläufe**, nicht der Startwert selbst: wie oft mit frischen Zufallszahlen neu
gestartet und das beste Ergebnis nach Loss behalten wird. Die Struktur ändert sich dabei nie.

## Versuchsaufbau

102 Zellen des dim-1-Probelaufs (WP-N1), denen die **wahre** Struktur vorgelegt wird — die Suche ist
also vollständig ausgeschaltet, gemessen wird allein die Parameteranpassung. Zwei Strukturen je
Zelle: die Oracle-Beschneidung (gefundene Terme geschnitten mit den wahren) und die wahre Struktur
selbst. Zehn Zufallsstarts, deterministisch aus dem Zellen-Seed abgeleitet; kleinere k werden aus
derselben Startfolge kumulativ ausgewertet.

## Ergebnis

Wahre Struktur, 102 Zellen:

| k | Fit gescheitert (Sentinel 1e6) | Anteil R² > 0,9 | erreicht Originallauf |
|---|---|---|---|
| 1 | **15** | 71,6 % | 29,4 % |
| 2 | 13 | 80,4 % | 37,3 % |
| 3 | **0** | 91,2 % | 46,1 % |
| 5 | 0 | 92,2 % | 52,9 % |
| 10 | **0** | **97,1 %** | 64,7 % |

Bei der Oracle-Beschneidung dasselbe Bild: 11 → 9 → **0** ab k = 3.

**Kein Plateau.** Der Optimierer kann diese Strukturen anpassen; ein **einzelner Versuch** ist
unzuverlässig. Bei k = 10 bleibt keine Zelle unanpassbar.

### Kontrollen

- Bei **k = 1** werden die WP-N3-Zahlen exakt reproduziert (15 bzw. 11 Sentinel-Zellen). Der
  Mehrfachstart fügt also nur Versuche hinzu.
- Die Strukturtrefferzahlen sind über alle k **konstant** — der Mehrfachstart ändert die Anpassung,
  nicht die Struktur.

## Bezug zum Pretuning

Unter `pretuning=false` zieht jeder Fit einen neuen Zufallsstart; unter `pretuning=true` wird der
Startwert deterministisch aus den Daten berechnet, pro Kandidatenstruktur also **einer**.

Ein Vergleich „mit gegen ohne Pretuning" variiert damit **zwei Dinge gleichzeitig** — die Güte des
Startwerts *und* ihre Anzahl. Ohne Angabe der Startzahl ist er nicht interpretierbar. Das betrifft
den Phase-B-Kampagnenkontrast rückwirkend.

**Größenordnung des impliziten Mehrfachstarts: unbekannt.** Die Kampagne rechnet im Median 410
Parameterfits je Zelle (dim 3: 570, max 610), aber verteilt auf *verschiedene* Kandidatenstrukturen.
Der Mehrfachstart je Struktur entspricht der Wiederholungsrate derselben Struktur, und die ist nie
gemessen worden (siehe `CLAUDE.md`, offener Punkt zur kanonischen Gleichheit von `StructureSpec`).
Eine frühere Formulierung, die Suche rechne „tausende Anpassungen, also ein impliziter Mehrfachstart
mit sehr großem k", war in beiden Hälften nicht gedeckt und ist am 2026-09-09 korrigiert worden.

## Einordnung gegen die Literatur

Recherche vom 2026-09-09 zu SINDy, PySR, ODEFormer und ProGED.

**Drei Budgetebenen, die nicht vermischt werden dürfen:**

| Ebene | EvoODE | Entsprechung |
|---|---|---|
| Struktursuche | geprüfte Strukturen, Suchschritte | PySR-Populationen und -Iterationen, ProGED-Kandidaten, ODEFormer-Beam |
| Parameteroptimierung | Neustarts *k* | PySR `optimizer_nrestarts`, ProGEDs DE-Population |
| Run-Stochastik | vollständige Läufe je Seed | unabhängige Wiederholungen |

**PySR ist der eigentliche Präzedenzfall:** `optimizer_nrestarts` ist dort ein regulärer
Methodenparameter für die Konstantenoptimierung. Ein benanntes Restart-Budget ist also etabliert,
kein Sonderweg. *Zu prüfen bleibt*, ob es jede Konstantenoptimierung betrifft oder nur finale
Kandidaten, und welcher Default im ODEBench-Lauf galt.

**ODEFormer liefert zwei getrennte Referenzen.** Die **Beam Size** bekommt eine eigene Ablation
(Appendix G) — der Präzedenzfall dafür, einen Budgetparameter zu vermessen statt ihn nur zu nennen.
Sie ist aber **nicht** unser k: Beam variiert *Strukturen*, k variiert *Parameterstarts*; die
Gleichsetzung wäre sachlich falsch. Die **Constant Optimization** dagegen ist strukturell unser
Pretuning — ein gelernter Warmstart plus ein *einzelner* lokaler Lauf. Offene Frage mit eigenem
Beitragswert: ist ihr Warmstart besser als unser OLS-Pretuning, oder haben sie dieselben 15 %
Ausfall und messen sie nicht?

**SINDy hat diese Fehlerklasse nicht** — die Koeffizienten folgen aus linearen Least-Squares-
Problemen, es gibt keinen Zufallsstart. Das ist **kein neutraler Unterschied**: Unsere
Startpunktabhängigkeit folgt daraus, dass wir MSE auf der *integrierten* Trajektorie optimieren, ein
schlecht konditioniertes Ziel; SINDy fittet im Ableitungsraum, wo das Problem linear ist. Die
ehrliche Formulierung lautet deshalb nicht „alle brauchen ein Budget, wir auch", sondern: **unser
Ansatz trägt eine Fehlerklasse, die SINDy strukturell nicht haben kann.** Das ist eine Limitation und
die Fortsetzung der Method-Positioning-Notiz vom 2026-09-03 (Integration gegen Differentiation).

**ProGED** löst dasselbe Problem über Differential Evolution, also populationsbasiert statt über
Neustarts — ein anderes Budget derselben Ebene.

## Was fehlt

**Die Kostenachse.** k multipliziert die Fits direkt, und das Projekt hängt an einer Effizienzthese.
Ein Restart-Budget ohne Kosten ist keine Messung, sondern eine Stellschraube. Die aussagekräftige
Kurve ist **Trefferquote gegen Fits**, nicht gegen k. Prüfbares Gegenargument: Die ~410 Fits werden
ohnehin gezahlt, nur unkontrolliert — k explizit zu machen wäre dann eine **Umverteilung** (weniger
Strukturen, jede zuverlässig angepasst) statt Zusatzkosten.

**k = 3 ist kein Default.** Belegt ist nur, dass drei Anläufe die Totalausfälle beseitigen; die
Fit-Qualität steigt danach weiter (91,2 % → 97,1 %). Die Kurve gilt für Dimension 1, höhere
Dimensionen sind ungemessen und haben deutlich größere Parameterräume.

**Pretuning mit k > 1 ist nie gemessen worden.** Der saubere Test ist zweifaktoriell:
Initialisierung (Zufall gegen verrauschten Warmstart θ_pre + ε) × Restart-Budget k ∈ {1,2,3,5,10}.
Erst das trennt „wie viel bringt mehr Budget" von „wie viel bringt Pretuning bei gleichem Budget".

**Die k-Werte sind nicht unabhängig** — kleinere k stammen kumulativ aus derselben Startfolge. Für
eine Publikation wären unabhängige Ziehungen sauberer.

## Status im Thesenaufbau

Als Paper-Kandidat neben Paper 2 vermerkt: `docs/phd_thesis_arc.md` §3. Leitfrage: *Wie viele
Neustarts braucht Strukturfindung, und wie verläuft die Kurve aus Trefferquote und Kosten?*

Die Botschaft darf nicht lauten „EvoODE hat Multistart erfunden", sondern: EvoODE weist eine
relevante Startpunktabhängigkeit der lokalen Parameteroptimierung auf, behandelt die Zahl der
Neustarts deshalb explizit als Optimierungsbudget und untersucht deren Einfluss systematisch.
Einordnender Kontext: *multistart local optimization*, *random restarts*, *basin of attraction*,
*search budget*.

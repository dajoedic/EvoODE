# CURRENT TASK: WP-P2.3 — Screening-Score komplexitätsbewusst machen; letzter Versuch vor Abbruch

**Language: Julia**

## Context

WP-P2.2c ist gelaufen (`2eb7202`). Zum ersten Mal liegen echte Zahlen vor. Ergebnis gemischt, mit
einem klaren Befund:

**System 11** (`-u1^3`): Screening findet die korrekte Struktur, ist mit 2,36 s gegen 3,63 s um
Faktor 1,53 schneller, Rangübereinstimmung **+1,0**, kein erschöpftes Polish-Budget, kein
abgelehnter Kandidat hätte gewonnen. Funktioniert.

**System 3** (Logistic): Rangübereinstimmung **−0,78**. Der Screening-Score ordnet Kandidaten also
nahezu **umgekehrt** zum simulierten Loss. Weitere Folgen: Loss 3,24e-8 statt 2,66e-10,
`final_stage` 5 statt 3, Laufzeit 400,9 s statt 357,6 s — die Variante ist dort **langsamer** als
der Simulationspfad, obwohl sie nur 711.757 statt 1.529.009 Integrationen rechnet.

Der Referenzpfad reproduziert in beiden Fällen exakt Baseline v0.

### Ursachenkette, soweit belegt

1. Der Loss bleibt bei 3,24e-8 und damit **über** `loss_tol = 1e-8`. Die absolute Loss-Abbruch-
   bedingung feuert deshalb nie. Der Referenzlauf erreicht 2,66e-10, bricht ab und bleibt auf
   Stage 3. Die Screening-Variante läuft weiter und eskaliert bis Stage 5.
2. Stage 5 bedeutet trigonometrische Terme, also steifere Kandidaten-ODEs. Kosten pro Integration:
   0,490 ms gegen 0,172 ms im Referenzlauf, Faktor 2,85. Die eingesparten Integrationen werden
   dadurch mehr als aufgefressen.
3. Der finale Refit auf vollem Budget dauert **0,001 s** und bewirkt damit praktisch nichts,
   obwohl die Struktur identisch zur Referenz ist (beide `du1/dt = 0.790*u1 + -0.011*u1^2`,
   beide `pruned_match = true`). Der Loss-Unterschied stammt also allein aus den Parametern.

### Vermutete Ursache der negativen Rangübereinstimmung

Kinder entstehen durch Hinzufügen von Termen, sind also **geschachtelte Obermengen** ihrer Eltern.
Für geschachtelte Least-Squares-Probleme ist das Residuum monoton nicht-steigend in der Zahl der
Terme — ein größeres Modell kann nie ein schlechteres LS-Residuum haben. Der Screening-Score
enthält aber nur einen Tiebreak von `1e-12 * n_params`, während das Suchziel mit `λ = 1e-3`
bestraft. **Der Score bevorzugt damit systematisch die größten Kandidaten.** Das erklärt sowohl die
negative Rangübereinstimmung als auch die Stage-Eskalation.

## Goal

Den Screening-Score komplexitätsbewusst machen und die Messung wiederholen. Dies ist der letzte
Versuch: bleibt die Rangübereinstimmung auf System 3 negativ, gilt das Kriterium als falsifiziert
(Abschnitt 6 der Design-Notiz) und die Arbeit daran wird eingestellt.

## Required Content

### 1. Komplexitätsbewusster Screening-Score

Der Score darf rohe LS-Residuen unterschiedlich großer Strukturen nicht mehr direkt vergleichen.

Zu tun: den Score um einen Komplexitätsterm ergänzen. Beachte dabei, dass ein einfaches Übernehmen
von `λ` aus dem Suchziel **nicht** korrekt ist — dort wird ein Simulations-MSE bestraft, hier ein
Ableitungs-Residuum; die Skalen sind verschieden. Ein skalenfreies Informationskriterium ist die
naheliegende Wahl. Wähle eines, begründe die Wahl im Docstring und mache die Variante
konfigurierbar, sodass der bisherige Score als Vergleichsoption erhalten bleibt.

Der bisherige, rein residuenbasierte Score muss weiterhin auswählbar sein — er ist die
Kontrollbedingung für die Messung in Punkt 3.

### 2. Wirkungslosen finalen Refit untersuchen

Der finale Refit läuft in 0,001 s durch und verbessert nichts, obwohl bei identischer Struktur ein
um Faktor 121 besserer Loss erreichbar ist. Kläre, warum der Optimierer sofort zurückkehrt
(Konvergenzkriterium bereits erfüllt, Line-Search-Fehler, oder Warmstart in einem Punkt, aus dem
BFGS nicht herausfindet) und berichte den Befund. Eine Behebung ist zulässig, wenn sie den
bestehenden Simulationspfad nicht berührt; andernfalls genügt der dokumentierte Befund.

Beachte den Zusammenhang: solange der Loss über `loss_tol` bleibt, terminiert die Suche nicht und
eskaliert Stages. Der wirkungslose Refit ist damit nicht kosmetisch, sondern Teil der Ursachenkette.

### 3. Messung wiederholen

`studies/debug/compare_screening_variant.jl` erneut ausführen, jetzt mit **drei** Bedingungen je
System: Referenzpfad, Screening mit altem Score, Screening mit neuem Score. Gleiche Systeme (3 und
11), gleicher Seed, gleiche Hyperparameter, Level-Budget 30.

Zu berichten, mit Zahlen: Rangübereinstimmung, `final_stage`, Loss, Laufzeit, Integrationen und
Kosten pro Integration je Bedingung. Ausgabe wie bisher nach
`outputs/studies/debug/compare_screening_variant/`.

### 4. Klare Aussage zum Ausgang

Der Abschlussbericht muss ausdrücklich feststellen, ob die Rangübereinstimmung auf System 3 mit dem
neuen Score positiv geworden ist und ob die Stage-Eskalation verschwunden ist. Kein Beschönigen:
bleibt sie negativ, ist das das Ergebnis und ist so zu benennen.

## Verification

Nur System 3 und System 11, Seed 42. **Nicht** System 26, 31 oder 63. Beide Systeme zusammen kosten
grob 12 Minuten je Bedingung.

Zusätzlich bestätigen, dass der Referenzpfad weiterhin Baseline v0 reproduziert: System 3 Loss
`2.663641831768419e-10` bei `final_stage = 3`, System 11 Loss `4.402192340718147e-15` bei
`final_stage = 4`.

## Constraints

- `evogrow.jl`, `evogrow_v3.jl`, `gp.jl`, `stopping.jl` bleiben unangetastet.
- Der bestehende Simulationspfad bleibt verhaltensgleich; die Baseline-v0-Gegenprobe ist Teil der
  Verifikation.
- Plateau, Stopplogik und Promotion laufen weiterhin ausschließlich auf simuliertem Loss.
- Der bisherige Screening-Score bleibt als Kontrollbedingung erhalten.
- Keine Änderung an `config_fingerprint`-relevanter Regression-Konfiguration in diesem WP.
- Keine neuen Abhängigkeiten.
- Nicht Teil dieses WP: WP-v3.3, WP-H2, Läufe auf gekoppelten Systemen.

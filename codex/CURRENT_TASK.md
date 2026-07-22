# CURRENT TASK: WP-P2.4 — Screening: harter Penalty und entkoppelter Polish-Start

**Language: Julia**

## Context

WP-T1 (`a6919ca`) hat die Ursache des Screening-Versagens auf System 3 aufgeklärt, und sie ist eine
andere als angenommen.

**Nicht die Toleranz:** Aus dem Least-Squares-Warmstart landet der Fit bei **3,236e-08 bei jeder
Toleranz von 1e-6 bis 1e-12** — völlig flach über sechs Größenordnungen. Der numerische Boden liegt
bei 4,40e-12, das Ergebnis also rund 7.000-fach darüber.

**Sondern der Warmstart selbst:** 3,236e-08 ist exakt der Wert, bei dem die Screening-Variante
hängenblieb. Der Referenzlauf erreicht 2,66e-10 und benutzt **keinen** Warmstart
(`USE_PRETUNING = false`). Der ableitungsbasierte LS-Warmstart führt auf System 3 also in ein
Becken, aus dem BFGS nicht herausfindet — die Screening-Variante führt damit genau das wieder ein,
was die Regression-Konfiguration bewusst abgeschaltet hat.

Daraus folgt: Ein harter Penalty auf das Ranking allein kann das Ergebnis nicht retten. Es braucht
zwei Änderungen, und sie müssen getrennt messbar sein.

Zweiter Befund aus WP-T1, der den Testaufbau betrifft: Auf System 11 ist der berichtete Loss bei
Toleranz 1e-6 numerisches Rauschen (erreichter Loss skaliert direkt mit der Toleranz; mit den
wahren Parametern sind bei 1e-6 nur 1,859e-14 erreichbar, gefittet werden 4,6e-15). Bei 1e-8 liegt
der Boden bei 1,36e-17, die Kosten steigen nur um Faktor rund 1,3. Der Vergleich in diesem WP läuft
deshalb bei **1e-8**.

## Goal

Zwei getrennte Interventionen an der Screening-Variante, jeweils einzeln abschaltbar, plus ein
Vergleichslauf, der ihre Wirkung einzeln und gemeinsam ausweist.

## Required Content

### 1. Harter Penalty: geschachtelter Modellvergleich statt Informationskriterium

AIC war wirkungslos, und zwar nachweisbar: Bei `n = 200` beträgt die Strafe über den gesamten
Bereich `p = 1..6` höchstens 10 Einheiten, während der Fit-Term sich schon bei 10 % Residuen-
unterschied um 19 Einheiten ändert. Jedes Standard-Informationskriterium ist hier vom Fit-Term
dominiert; BIC wäre mit `p*log(n) <= 26,5` ebenfalls zu schwach.

Das Problem ist struktureller Natur: Kinder entstehen durch Hinzufügen von Termen, sind also
geschachtelte Obermengen ihrer Eltern, und für geschachtelte Least-Squares-Probleme ist das
Residuum monoton nicht-steigend in der Termzahl. Ein größeres Modell kann nie schlechter
abschneiden.

Die angemessene Antwort ist kein additiver Strafterm, sondern ein **geschachtelter Modellvergleich**:
Ein Kind darf seinen Elternteil nur dann überholen, wenn die Residuenverbesserung größer ist, als
ein zusätzlicher Parameter zufällig liefern würde. Setze das als **Gate** um, nicht als
Rangkorrektur:

- Kandidaten, die den Test gegen ihren Elternteil bestehen, werden bevorzugt.
- Kandidaten, die ihn nicht bestehen, werden dahinter einsortiert.
- Innerhalb jeder Gruppe wird weiterhin nach Residuum sortiert.
- Elternteile selbst haben keinen Elternteil und werden nach Residuum eingeordnet.

Wähle einen geeigneten Test für geschachtelte Least-Squares-Modelle, begründe die Wahl im
Docstring, und mache das Signifikanzniveau konfigurierbar mit einem benannten Default. Dafür muss
die Kindergenerierung die Herkunft eines Kandidaten (Elternteil) bis zur Bewertung mitführen.

Der bisherige `screening_score = :residual` und `:aic` bleiben als Vergleichsbedingungen erhalten.

### 2. Pflicht-Nachweis, dass der Penalty überhaupt wirkt

Die AIC-Runde ist daran gescheitert, dass die Intervention die Rangfolge nicht bewegt hat und das
erst hinterher auffiel. Diesmal muss das im Lauf selbst sichtbar sein.

Protokolliere pro Level und aggregiert pro Lauf: **in wie vielen Fällen sich die ausgewählte
Kandidatenmenge von der unterscheidet, die der reine Residuen-Score ausgewählt hätte**, und wie
viele Kinder das Gate nicht bestanden haben.

Ist dieser Wert null, ist die Intervention wirkungslos — das ist dann sofort erkennbar und im
Bericht ausdrücklich festzustellen.

### 3. Polish-Start vom Screening entkoppeln

Der LS-Fit erfüllt derzeit zwei Rollen: er liefert den Screening-Score **und** den Startpunkt für
das Nachpolieren. Nach dem WP-T1-Befund ist die zweite Rolle schädlich.

Führe eine konfigurierbare Wahl des Polish-Startpunkts ein, mit mindestens zwei Möglichkeiten:

- die LS-Parameter (heutiges Verhalten),
- derselbe Startpunkt, den der Referenzpfad verwendet — der LS-Fit dient dann ausschließlich der
  Bewertung.

Die Diagnose-Fits abgelehnter Kandidaten verwenden denselben Startpunkt wie die ausgewählten, damit
der Vergleich fair bleibt.

### 4. Rangübereinstimmung reparieren

Die Kennzahl ist fragwürdig: In beiden WP-P2.3-Bedingungen betrug sie exakt −7/9, obwohl sich
Laufzeit, Integrationen und Konvergenzfehler deutlich unterschieden. Verdacht: Auf den meisten
Leveln ist rho `NaN`, weil alle simulierten Losses gleich sind und der Nenner null wird, sodass der
berichtete Mittelwert von sehr wenigen Leveln getragen wird.

Zu tun: Ausweisen, auf wie vielen Leveln überhaupt ein endlicher Wert zustande kam, und den
Mittelwert nur über diese bilden — zusammen mit dieser Anzahl, damit er einordenbar ist. Zusätzlich
Median und Spannweite. Bleibt die Zahl der auswertbaren Level klein, ist die Kennzahl als
Entscheidungsgrundlage zu kennzeichnen und nicht stillschweigend zu mitteln.

### 5. Vergleichslauf

`studies/debug/compare_screening_variant.jl` erweitern. Systeme 3 und 11, Seed 42, Level-Budget 30,
Bewertungstoleranz **1e-8** für alle Bedingungen:

- **A** Referenzpfad (Simulation)
- **B** Screening, Residuen-Score, LS-Polish-Start (heutiges Verhalten, Kontrolle)
- **C** Screening, geschachtelter Test, LS-Polish-Start
- **D** Screening, geschachtelter Test, entkoppelter Polish-Start

Damit ist die Wirkung beider Interventionen einzeln ablesbar: C gegen B zeigt den Penalty, D gegen
C den Startpunkt.

Zusätzlich **eine** Ankerprüfung: Referenzpfad bei Toleranz 1e-6 gegen Baseline v0 (System 3 Loss
`2.663641831768419e-10`, `final_stage = 3`; System 11 Loss `4.402192340718147e-15`,
`final_stage = 4`). Nur zur Bestätigung, dass der Referenzpfad unverändert ist — bei 1e-8 gelten
diese Werte naturgemäß nicht mehr.

### 6. Bericht

Mit Zahlen, je Bedingung: Loss, `final_stage`, `pruned_match`, Laufzeit, Integrationen,
Kosten pro Integration, Rangübereinstimmung samt Zahl auswertbarer Level, Zahl der vom Gate
abgelehnten Kinder, und die Abweichung der Auswahl gegenüber dem reinen Residuen-Score.

Drei Fragen sind ausdrücklich zu beantworten:

1. Verändert der geschachtelte Test die Auswahl überhaupt (Punkt 2)?
2. Verschwindet die Stage-Eskalation auf System 3 (Referenz: Stage 3, bisher Screening: Stage 5)?
3. Entkommt Bedingung D dem Becken bei 3,236e-08?

## Verification

Nur System 3 und System 11. **Nicht** System 26, 31 oder 63. Grobe Kostenschätzung: System 3 rund
sechs Minuten je Bedingung, System 11 Sekunden.

## Constraints

- `evogrow.jl`, `evogrow_v3.jl`, `gp.jl`, `stopping.jl`, `discover.jl` bleiben unangetastet.
- Der Referenzpfad bleibt verhaltensgleich; die Ankerprüfung bei 1e-6 ist Teil der Verifikation.
- Beide Interventionen sind einzeln abschaltbar; das heutige Verhalten bleibt als Bedingung B
  reproduzierbar.
- Plateau, Stopplogik und Promotion laufen weiterhin ausschließlich auf simuliertem Loss.
- `pretune_parameters` bleibt verhaltensgleich.
- Keine Änderung an der Regression-Konfiguration oder am `config_fingerprint` in diesem WP.
- Keine neuen Abhängigkeiten.

Nicht Teil dieses WP, aber aus WP-T1 vermerkt und nicht zu beheben:
- Ein vollständig gescheiterter Fit meldet `final_loss = 1.000e+06` (Initialwert `l_best`) mit
  Retcode `Success` und ist von einem echten schlechten Fit nicht unterscheidbar.
- Einzelne Fits verbrauchen bei zwei Parametern bis zu 39.933 Loss-Auswertungen mit Retcode
  `Failure` — die Line-Search verhält sich pathologisch.
- Die Umstellung der Bewertungstoleranz auf 1e-8 im Regression-Runner ist eine eigene Entscheidung
  und gehört nicht in dieses WP.

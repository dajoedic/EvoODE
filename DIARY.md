# EvoODE — Projekt-Tagebuch

Neueste Einträge zuerst. Aktueller Projektzustand: siehe `CLAUDE.md`.

---

## 2026-08-17

### WP-C3 abgelehnt, WP-C4 angenommen — der Cap lehnt jetzt ab, statt im Zweifel zu behaupten

<!-- d94bc3b -->

**WP-C3 erfüllte sein Zielbild und wurde trotzdem nicht angenommen.** Vier Lorenz-Zeilen auf Cap 3,
System 31 / IC 2 auf `nothing`, 75 Zeilen unverändert, Tests grün — und darunter die Bedingung
`current_stage < 3`, ein hartkodierter Stufenindex. Der Auftrag hatte ausdrücklich verlangt, dass
das Kriterium nur Residuen, Floors und Policy-Schwellen verwendet und relativ argumentiert.

Der Index war auch nicht nebensächlich. Nachgerechnet, was ohne ihn passiert wäre: Die
**Kontrollzeile** 31 / IC 1 hätte ihren korrekten Cap 3 verloren und wäre auf 4 gesprungen — ihr
Verhältnis nach der Unterschreitung liegt bei 0,496 gegen die Schwelle 0,5, also **0,8 % Abstand**.
Eine zweite Kontrolle lag bei 0,520, 4 % auf der anderen Seite. Der Stufenindex war genau das, was
die Abnahme trug.

Dazu die methodische Lehre: Der Unempfindlichkeitsnachweis im WP-C3-Report maß nur den Abstand der
**Zielzeilen** zur Schwelle (0,029–0,315 gegen 0,5). Das Risiko liegt aber auf den **Kontrollen**,
wo die Regel nicht feuern darf. **Ein Nachweis, der nur auf der Zielseite gemessen wird, ist
keiner.** Diese Auflage steht jetzt in jedem Folgeauftrag.

**Die Umstellung in WP-C4: drei Ausgänge statt zwei.** Der Versuch, Ziel- und Kontrollzeilen exakt
zu trennen, wurde aufgegeben — er ist datenseitig knapp und erzwingt deshalb passende Konstanten.
Stattdessen:

| Verhältnis nach der Floor-Unterschreitung | Ausgang |
|---|---|
| ≤ 0,35 | weitersuchen, höher deckeln |
| ≥ 0,62 | hier deckeln, wie bisher |
| dazwischen | **`nothing`** — kein Cap |

Das ist die Regel des Projekts, auf den eigenen Mechanismus angewandt: *positive Evidenz, nie deren
Abwesenheit.* Im Zweifelsband liegt keine vor, also wird nichts behauptet. Die Fehlerrichtung ist
beabsichtigt — ein `nothing` kostet Rechenzeit, ein falscher Cap kostet die Lösung, und Rechenzeit
ist nach dem Pilotbefund reichlich vorhanden.

**Ergebnis auf den 80 exakten Gleichungszeilen:** vier Lorenz-Zeilen auf 3, 31 / IC 2 auf `nothing`,
und die vier Wechsel zwischen endlichen Caps sind **genau** diese Ziele. Endliche Caps 49 → 45. Die
vier aufgegebenen Zeilen sind 12 / IC 1, 31 / IC 1, 31 / IC 2 und 55 / IC 2 Gl. 2.

**Zwei Anmerkungen, die der Report nicht enthält und die hier festgehalten werden.**

*Erstens: die Floor-Tiefen-Konstante ist jetzt die tragende.* Kontrolle 61 / IC 1 hat **drei von vier
Splits im Band** (0,520, 0,568, 0,541) und behält ihren Cap allein deshalb, weil ihre Floor-Ratios
bei 0,03 bis 0,07 unter der Schwelle 0,1 liegen. Die Zielzeilen liegen bei 0,30 bis 0,85. Die
Trennung hält also mit Faktor vier — aber sie ist nicht dokumentiert worden, obwohl der Auftrag
den Abstand nach beiden Seiten verlangt hatte. Hier nachgerechnet und bestätigt.

*Zweitens: eine Zeile geht aus dem falschen Grund verloren.* 12 / IC 1 hatte den korrekten, engen
Cap 2 und gibt ihn auf, obwohl ihre Floor-Ratio bei **9,9e-06** liegt — das Residuum ist fünf
Größenordnungen unter dem Rauschen, die anschließende „Verbesserung" von 0,477 ist reines Rauschen.
Sauber wäre, dass die Floor-Tiefen-Bedingung die Bandlogik **ganz** abschaltet statt nur den
Wiederaufnahmezweig. Der Verlust ist ungefährlich, die Begründung falsch. Notiert als offener Punkt.

*Verwandt dazu:* Sowohl 31 / IC 2 als auch 12 / IC 1 kippen über die **Mehrheitsabstimmung der
Splits**, nicht über eine klare Erkennung — bei 12 / IC 1 änderte ein einziger Split (Nr. 3) seine
Stimme. Die Robustheit der Aggregation ist damit eine eigene offene Frage.

**Fingerprints unverändert** (`1d0ccf8d53c6576d`, `e361a2af49366670`) — und das ist der eigentliche
Befund dieser Runde, siehe unten.

### Die Fingerprints bemerken Logikänderungen nicht

<!-- d94bc3b -->

Bei WP-C3 und WP-C4 hat sich das Cap-Verhalten auf fünf beziehungsweise acht Zeilen geändert, und
**beide Fingerprints standen still**. Ihre Nutzlast enthält ausschließlich
Konfigurations**konstanten**, keine Entscheidungs**logik**.

Damit leistet der Fingerprint nicht, wofür er da ist. `CLAUDE.md` verlangt vor der Publikation den
Nachweis, dass alle Läufe einen Fingerprint teilen — genau diese Prüfung kann eine Logikänderung
nicht sehen. Zwei Records mit identischem Fingerprint können aus unterschiedlich entscheidendem
Code stammen. Gerettet wird die Nachvollziehbarkeit derzeit allein durch den Commit-Hash im Record,
seit `d2aed32`; das ist Glück, nicht Konstruktion.

Nächstes Arbeitspaket.

---

### WP-C1 — der Horizont war die Ursache, aber nicht die einzige

<!-- d472f8e -->

Audit über alle 20 exakten Systeme, beide IC-Sets, Horizonte 2 bis 5, 320 Gleichungszeilen. Der
Vorausblick wurde dabei nicht angefasst, nur `estimate_stage_caps` mit variiertem Horizont
aufgerufen und das Ergebnis gegen die aus `phase_b_support.json` abgeleitete benötigte Stufe
gehalten.

**Die Rate bei Horizont 2: neun Gleichungszeilen auf fünf der zwanzig exakten Systeme.** Aus zwei
von sieben ist damit eine belastbare Zahl geworden.

**Der Mechanismus ist bestätigt, und präziser als erwartet.** Von Horizont 2 auf 3 ändern sich genau
sechs Zeilen — und jeder neue Cap trifft die benötigte Stufe **exakt**:

| System | Gl. | benötigt | Cap alt | Cap neu |
|---|---|---|---|---|
| 28 Pendel ohne Reibung | 2 | 5 | 1 | **5** |
| 32 Doppelmuldenoszillator | 2 | 4 | 1 | **4** |
| 38 Van der Pol | 1 | 4 | `nothing` | **4** |

System 38 ist der aussagekräftigste Fall, weil er nicht im Verdacht stand. Dort gab es vorher
**gar keinen** Cap; der längere Vorausblick erkennt den Kubikterm und deckelt punktgenau darauf. Der
Cap wird durch die Korrektur also nicht nur sicherer, an dieser Stelle wird er auch **schärfer** —
genau die Doppelaussage, die der Beitrag braucht.

**Der Parameter ist oberhalb von 3 wirkungslos.** Der Report belegt das über Zählwerte; zeilenweise
nachgerechnet gilt es stärker: Horizonte 3, 4 und 5 sind auf **allen 80 Gleichungszeilen
cap-identisch**. Damit ist die 3 eine getunte Konstante ohne Wirkung, und es wird auf **5** gegangen
— die Stufenzahl der Basis, also „kein Horizont". Ergebnis unverändert, aber im Paper steht dann
keine Zahl mehr, zu der „warum 3?" die einzige ehrliche Antwort „weil es auf unseren zwanzig
Systemen reicht" wäre. WP-C2 zieht das nach.

**Und es bleibt ein zweiter Defekt.** Fünf Zeilen überleben jeden Horizont:

| System | Gl. | IC | benötigt | Cap |
|---|---|---|---|---|
| 55 Lorenz (komplex periodisch) | 3 | 1, 2 | 3 | 2 |
| 56 Lorenz (Standardparameter) | 3 | 1, 2 | 3 | 2 |
| 31 | 1 | nur 2 | 3 | 1 |

Die Lorenz-Vorhersage aus dem Pilot-Eintrag hat sich bestätigt — die Erklärung nicht. Von Stufe 2
aus liegt Stufe 3 **schon bei Horizont 2** im Vorausblick. Der Kreuzterm `u1*u2` wird also gesehen
und trotzdem nicht als Gewinn gezählt. Das ist ein anderer Mechanismus, und die naheliegende
Vermutung ist die Ableitungsschätzung auf chaotischen Trajektorien, also derselbe Boden, auf dem v3
gescheitert ist (WP-L2). System 31 auf IC-Set 2 ist der längst als Grenzfall dokumentierte Fall
trajektorienarmer Dynamik — hier zum ersten Mal als tatsächliches Abschneiden belegt und nicht nur
als Instabilität über IC-Sets.

**Gegenprobe gehalten:** System 61 (Chen-Lee) steht auf `[3,3,3]` und ist damit korrekt gedeckelt.
Der Defekt ist selektiv.

**Fingerprints:** Regression `0825cdc88d9264a0` → `06e1c71fbd10a3a4`, Phase B `ca02ea284d621f6d` →
`41f69abc3670b6c4`. Beide bewegen sich mit WP-C2 erneut; das ist unkritisch, solange kein
Kampagnen-Record existiert, und es existiert keiner.

**Eine Limitation, die unabhängig vom Ausgang zu deklarieren ist.** Prüfbar ist der Cap nur auf den
**20 exakten Systemen**. Für die 43 Surrogatsysteme gibt es keinen wahren Support, die Sicherheit
des Controllers ist dort konstruktionsbedingt nicht auditierbar — und der Pilot zeigt mehrere
Surrogate mit einer auf Stufe 1 gedeckelten Gleichung (33, 34, 40, 44, 50). Bewertet werden sie über
R², es ist also ein Güte- und kein Support-Risiko. Gesagt werden muss es trotzdem.

**Kampagnenstatus: weiterhin blockiert**, jetzt auf den fünf verbleibenden Zeilen.

---

### Das Cap-Muster in den Pilot-Records: der Defekt ist breiter als 2 von 7, und Lorenz ist dabei

<!-- 9b0cf85 -->

Anlass war eine Terminfrage — kann die geplante `pretune_off`-Sondierung parallel zu WP-C1 laufen?
Zur Beantwortung wurde das Feld `stage_caps` gegen `eq_final_stages` gehalten, um zu sehen, auf
welchen Zellen der Cap ueberhaupt bindet. Die Antwort auf die Terminfrage ist ja, es kollidiert
(unten). Der Nebenbefund ist der wichtigere.

**Auf 20 der 39 Pilotzellen bindet der Cap.** Und die Cap-Vektoren zeigen ein Muster, das die
Stichprobe vom 2026-08-14 nicht sehen konnte, weil dort nur sieben Systeme mit vorliegendem Record
geprueft wurden:

| Muster | Systeme |
|---|---|
| `[*, 1]` — Gleichung 2 auf Stufe 1 gedeckelt | **28, 32, 34, 40, 44, 50** |
| `[1, *]` — dasselbe spiegelbildlich | 33, 39 |
| `[None, 3, 2]` — Gleichung 3 auf Stufe 2 | **55, 56** |

Der `[*, 1]`-Fall ist derselbe wie bei 28 und 32: Gleichung 2 wird auf Linearitaet festgenagelt.
Statt zwei Verdachtsfaellen stehen jetzt **acht** im Raum. Ob alle acht wirklich abschneiden, haengt
am wahren Support je Gleichung und ist erst nach WP-C1 zu sagen — hier steht ein Muster, keine Rate.

**Lorenz ist betroffen, und das ist die teure Zeile.** Systeme 55 und 56 tragen Cap 2 auf Gleichung
3. Die dritte Lorenz-Gleichung lautet `du3/dt = u1*u2 - beta*u3`; der Kreuzterm `u1*u2` liegt in der
gestaffelten Basis auf **Stufe 3**. Ein Cap von 2 schliesst ihn aus. Passend dazu `pruned_match =
false` auf beiden. System 56 verbraucht dabei **40 Stunden** auf einer Antwort, die nie im
zugelassenen Raum lag.

Das ist nicht irgendein Benchmarksystem. Wenn das so im Paper steht, ist es die erste Zeile, die
geprueft wird.

**Gegenprobe, damit der Cap nicht pauschal verurteilt wird:** System 61 (Chen-Lee) traegt `[3,3,3]`
und erreicht `[3,3,3]`. Chen-Lee besteht aus Kreuztermen, Stufe 3 ist dort korrekt — der Cap bindet
und liegt richtig. Der Defekt ist selektiv, nicht generell, und genau deshalb ist die
WP-C1-Auflage "loest 28 und 32, **ohne** die korrekten Caps zu verschieben" die richtige Huerde.

**Konsequenz fuer die Terminplanung: die Sondierung muss hinter WP-C1.** Die Caps steuern den
Suchraum und damit die Kosten. System 61 hat seine 49,4 Stunden *mit* bindendem Cap auf allen drei
Gleichungen verbraucht; hebt WP-C1 die Caps, wird diese Zelle teurer, nicht billiger. Eine heute
gemessene `pretune_off`-Sondierung wuerde ein Cap-Regime vermessen, das gerade abgeschafft wird.

**Und damit ist die gestrige Kostenzahl ein zweites Mal eine Untergrenze.** Die 3.384 Kernstunden
gelten fuer `lookahead_horizon = 2`. Sie sind untere Schranke einmal wegen des ungemessenen
`pretune_off` und einmal wegen des Cap-Regimes, das sich in Richtung **mehr** Suchraum bewegt. Das
Kostenmodell in `docs/hpc_requirements.md` wird deshalb erst nach WP-C1 und nach der Sondierung neu
geschrieben, nicht jetzt.

Reihenfolge: WP-C1 → Caps final → `pretune_off`-Sondierung auf 56, 59, 61 → Kostenmodell → Kampagne.
Die Sondierung misst dann beides in einem Lauf, `pretune_off` und das neue Cap-Regime.

**An WP-C1 wurde nichts geaendert.** Der Auftrag deckt alle 20 exakten Systeme und beide IC-Sets
bereits ab; 55, 56 und 61 sind darunter. Dieser Eintrag ist Gegenprobe fuer den Report, keine
Erweiterung der Spezifikation.

---

### Der Pilot ist durch — das Kostenmodell stimmt in der Summe und ist in der Verteilung falsch

<!-- d648993 -->

Der Pilot auf Orion ist abgeschlossen. Ausgewertet wurden **42 eindeutige Zellen** aus
`pilot_e20af80`, `pilot_sweep_tasks` und `pilot_sweep3_tasks`, dazu 888 Level-Intervalle aus den
Heartbeat-Dateien. Abdeckung: **Systeme 24–62, Seed 42, IC-Set 1, ausschliesslich `pretune_on`**.
Alle Records `error=null`.

**Zur Zulaessigkeit der Zeitmessung.** Grundsatz 7 in `CLAUDE.md` verbietet Wall-Clock als Evidenz —
und nennt die Ausnahme selbst: *"If a claim genuinely requires timing, measure it on a dedicated
machine."* Orion vergibt je Job einen dedizierten Kern ohne Suspend und ohne Mitbewerber. Fuer
**Kapazitaetsplanung** ist die Messung damit zulaessig; fuer **Methodenvergleiche** bleibt sie es
nicht. Alle Zahlen unten sind Planungsgroessen, keine Leistungsaussagen ueber Varianten.

**Die Gesamtsumme haelt, die Klassenaufteilung nicht.** Gegen `docs/hpc_requirements.md` §5:

| Dimension | geschaetzt s/Job | gemessen Median | gemessen Mittel | Urteil |
|---|---|---|---|---|
| 1 | 170 | 250 s | 250 s | brauchbar (nur System 1, n=3) |
| 2 | 20.900 | 684 s | 10.440 s | Median 30x zu hoch, Mittel 2x zu hoch |
| 3 | 41.700 | 22.400 s | 63.800 s | **zu niedrig**, Mittel 1,5x |
| 4 | 83.500 | 4.280 s | 2.300 s | 36x zu hoch (nur System 62, n=2) |

Hochrechnung auf die 756 Phase-B-Zellen mit gemessenen Systemmitteln, fuer unbeobachtete Systeme das
Mittel ihrer Dimensionsklasse: **3.384 Kernstunden** gegen geschaetzte 3.900. Das sind **15 Prozent
Abweichung nach unten** — die Schaetzung war in der Summe richtig.

**Damit ist die bisherige Diagnose zu korrigieren.** `CLAUDE.md` fuehrt unter "Active", die Schaetzung
sei *"one to two orders of magnitude too high"*. Das war aus den ersten, billigen Zellen geschlossen
(System 24: 10 s gegen 20.900 s geschaetzt) und ueberlebt den vollen Sweep nicht. Die Verteilung ist
extrem schief — dim 2 hat Median 0,19 h und Mittel 2,90 h, Faktor 15 zwischen beiden. Wer aus
Medianzellen auf die Kampagne schliesst, unterschaetzt sie um eine Groessenordnung. Die Ursache des
alten Fehlschlusses ist also nicht die Umrechnung Sekunden-pro-Integration, sondern eine
**Stichprobe aus dem Kopf der Verteilung**.

**Kalenderzeit bei `parallelism: 16`: rund 9 Tage** (3.384 / 16 = 212 h). Bei 32 Kernen 4,4 Tage,
bei allen 96 rund 1,5 Tage. Untere Schranke der Makespan ist aber die **laengste Einzelzelle: 68 h**
— unter 3 Tage kommt die Kampagne durch keine Parallelitaet.

**Der eigentliche Befund: die pathologischen Level sind keine Ausreisser, sondern ein Trend.**
`CLAUDE.md` beschreibt sie bisher als *"a single search level consuming three to five hours while its
neighbours take seconds"*. Die Level-Serie von System 59 (Roessler, chaotisch) zeigt etwas anderes:

```text
Level  1..8   49  107   60   74  107  115   91  129            Sekunden
Level  9..16  6214 3985 9532 4468 4482 6035 3473 2917
Level 17..24  3630 2858 3348 5996 4373 6278 8021 11538
Level 25..30  25462 20960 21524 30075 16658 42372              = 11,8 h im letzten Level
```

Kein Ausreisser, sondern **monotones Wachstum ueber drei Groessenordnungen mit der Strukturgroesse**.
Bestaetigt auf System 61 (48 s → 37.211 s) und, im Kleinen, auf dem billigen System 26 (14 s → 63 s).
Auch die Konzentrationsmessung passt: In den teuersten Zellen macht das langsamste Level nur 17–26 %
der Zelle aus — teuer ist die **ganze zweite Haelfte**, nicht ein Level.

**Und diese zweite Haelfte ist Verschwendung.** System 59 endet nach 30 Levels und 68 Stunden bei
`loss = 1,54`, System 61 bei `63,1`, System 56 (Lorenz) bei `44,5` — alle drei chaotisch, alle drei
ohne brauchbare Loesung. Die 60 von 68 Stunden ab Level 9 kaufen nichts. In Zaehlern, wie Grundsatz 7
es verlangt: 6.625.512 Loss-Evaluationen bei 610 Parameter-Fits auf System 59, also **rund 10.900
Solves je Fit** — das ist die Liniensuche, die seit WP-D2 als offener Kostenhebel notiert ist, hier
zum ersten Mal auf dedizierter Hardware beziffert.

Das verschiebt die Prioritaet: Nicht ein einzelnes pathologisches Level ist zu jagen, sondern es ist
zu entscheiden, ob chaotische Systeme ueberhaupt 30 Levels bekommen. Ein Levelbudget in Abhaengigkeit
der Dimension oder ein Abbruch bei ausbleibender Verbesserung waere fingerprint-relevant und muesste
damit **vor** dem ersten Kampagnen-Record fallen. Bewusst nicht jetzt entschieden: Der Cap-Defekt hat
Vorrang, und beide Aenderungen zusammen in einem Fingerprint-Sprung sind sauberer als zwei.

**Provenienz, wie erwartet.** Alle 42 Records tragen `config_fingerprint: c71c85ac2ec580ff` und
`git_hash: "unknown"` — also den Stand **vor** WP-M1 und vor dem Provenienz-Fix. Sie sind damit
genau das, was sie sein sollten: gueltige Infrastruktur- und Kostenmessungen, die **niemals** mit
Kampagnen-Records vermengt werden duerfen. Die Kampagne laeuft unter `ca02ea284d621f6d`.

**Nebenbefund:** Der Pilot hat **281 Kernstunden** verbraucht. `docs/hpc_requirements.md` §5 kuendigt
dem Standort gegenueber *"roughly 20 jobs, ~50 core-hours"* an. Faktor 5,6 darueber, verursacht von
denselben drei chaotischen Zellen. Kein Schaden, aber beim naechsten Mal anzukuendigen.

**Offen aus dem Pilot:**

1. **`pretune_off` ist ungemessen** — das ist die Haelfte der Kampagne. Ohne Warmstart ist mehr
   BFGS-Arbeit je Fit zu erwarten, die Hochrechnung oben ist insofern eine untere Schranke.
2. Systeme 1–23 ruhen auf **einem** gemessenen System (System 1, 3 Records), System 63 auf keinem.
3. Ein Seed, ein IC-Set. Die Seed-Streuung ist dort, wo gemessen, erheblich: System 62 braucht
   4.279 s bei Seed 42 und 300 s bei Seed 123 — Faktor 14 bei identischer Konfiguration.

---

## 2026-08-14

### Der Stage-Cap schneidet wahre Strukturen ab - auf 2 von 7 geprueften exakten Systemen

<!-- e5c739b -->

**Das ist ein Defekt im Beitrag des Papiers, gefunden vor der Kampagne.**

Anlass war die Umpositionierung von EvoODE als *Search-Space-Controller* (siehe
`docs/paper1_scope_discussion_2026-08-14.md`): Der Cap entscheidet, wie weit der Hypothesenraum je
Gleichung ueberhaupt geoeffnet wird, der innere Sucher ist austauschbar. Diese Position steht und
faellt mit einem Halbsatz — der Controller darf unnoetige Suche vermeiden, **ohne relevante
Strukturen abzuschneiden**. Genau das wurde geprueft.

**Befund.** Je Gleichung die benoetigte Stufe aus `phase_b_support.json` abgeleitet und gegen den im
Record protokollierten Cap gehalten:

| System | wahrer Support Gl. 2 | benoetigte Stufe | Cap | Ergebnis |
|---|---|---|---|---|
| 28 | `sin(u1)` | **5** | **1** | abgeschnitten |
| 32 | `u1`, `u2`, `u1^3` | **4** | **1** | abgeschnitten |
| 26, 27, 29, 31, 54 | — | — | — | in Ordnung |

Beide betroffenen Systeme haben `pruned_match = false`. Die Ursache ist damit **nicht** der additive
Sucher, sondern der Controller: Die Antwort war nie im zugelassenen Raum.

**Die entlastende Erklaerung haelt nicht.** Naheliegend waere, dass die Trajektorie die
Nichtlinearitaet gar nicht anregt und der Cap insofern recht hat — der Term waere symbolisch
vorhanden, aus den Daten aber nicht identifizierbar. Gegen den Datensatz geprueft:

```text
System 28 (Pendel ohne Reibung)     du2/dt = -0.9*sin(u1)      |u1|max = 1.90 rad ~ 109 Grad
                                    sin(1.90) = 0.946  gegen  u1 = 1.90        -> Faktor 2
System 32 (Doppelmuldenoszillator)  du2/dt = -u1^3 + u1 - ...  |u1|max = 2.09
                                    u1^3 = 9.08        gegen  u1 = 2.09        -> Faktor 4,4
```

In beiden Faellen **dominiert** der hochstufige Term die Dynamik. Ein Cap von 1 ist dort nicht
konservativ, sondern falsch.

Damit verletzt der Cap die Regel, die aus dem System-63-Vorfall abgeleitet wurde und in `CLAUDE.md`
unter "Settled" steht: *the cap must rest on positive evidence, never on the absence of evidence.*
Ein Cap von 1 behauptet positive Evidenz, dass Stufe 1 genuegt.

**Der Mechanismus ist gefunden: der Vorausblick ist genau eine Stufe zu kurz.**

```julia
# src/structure/stage_cap.jl
horizon_end = min(length(applicable_stages), pos + policy.lookahead_horizon)
#                                                  lookahead_horizon = 2
```

Von Stufe 1 aus prueft die Analyse nur die Stufen 2 und 3. Stufe 4 und 5 sieht sie nie. Und die
Basis staffelt nach **Grad**, nicht nach **Symmetrie**:

| Stufe | Terme | Paritaet |
|---|---|---|
| 1 | `u1`, `u2` | ungerade |
| 2 | `u1^2`, `u2^2` | gerade |
| 3 | `u1*u2` | gemischt |
| 4 | `u1^3` | ungerade |
| 5 | `sin`, `cos` | ungerade / gerade |

Fuer eine **ungerade** Nichtlinearitaet liegt die erste brauchbare Naeherung jenseits von linear
also bei Stufe 4 oder 5. Die Stufen 2 und 3 koennen sie nicht approximieren — `u1^2` ist gerade,
Kreuzterme brauchen eine zweite Variable. Der Vorausblick sieht keine Verbesserung und schliesst:
Stufe 1 genuegt.

Damit erklaeren sich **alle zehn Faelle**: Jeder korrekte Cap liegt bei Stufe 3, also innerhalb des
Horizonts. Beide Fehlschlaege brauchen Stufe 4 bzw. 5, also jenseits davon.

> **Designregel, zweite ihrer Art nach der System-63-Regel:** Ein datengetriebener Deckel muss so
> weit vorausschauen, wie die Basis strukturelle Luecken erzeugt. Bei gradgestaffelter Basis und
> ungeraden Nichtlinearitaeten betraegt diese Luecke zwei Stufen; ein kuerzerer Horizont schliesst
> die wahre Struktur systematisch aus.

**Der Cap ist damit nicht grundsaetzlich defekt** — der Parameter ist falsch. Naheliegender Fix:
`lookahead_horizon` auf 4, also bis ans Ende der Basis. Der Vorausblick rechnet nur
Ableitungsregressionen, keine Fits; die Mehrkosten sind gegenueber der Suche vernachlaessigbar.

Zwei Auflagen: Der Parameter steckt in `LOOKAHEAD_CAP_POLICY` und damit im Fingerprint, muss also
vor dem ersten Kampagnen-Record landen. Und es ist zu validieren statt zu glauben — loest es 28 und
32, **ohne** die fuenf korrekten Caps (26, 27, 29, 31, 54) zu verschieben?

**Konsequenz fuer die Interpretation der 40 % Recovery:** Mindestens zwei der sechs Fehlschlaege sind
**keine** Suchfehler. Die Diagnose "der additive Sucher kann eine falsche Festlegung nicht
zuruecknehmen" gilt fuer System 54 — fuer 28 und 32 gilt eine andere Ursache. Beide Fehlerquellen
muessen getrennt gezaehlt werden, sonst wird dem Sucher angelastet, was der Controller verursacht hat.

**Offen, vor der Kampagne zu klaeren:**

1. Alle 20 exakten Systeme pruefen, nicht nur die sieben mit vorliegendem Record. Zwei von sieben ist
   eine Stichprobe, keine Rate.
2. Den Mechanismus verstehen: Warum liefert die Voraus-Analyse bei sinus- bzw. kubikdominierter
   Dynamik "Stufe 1 genuegt"?
3. Erst danach entscheiden, ob der Cap in dieser Form in die Kampagne geht.

---

### GPU geprueft und verworfen — die Begruendung, damit die Frage nicht wiederkommt

<!-- 7d23da5 -->

Frage aufgeworfen: laesst sich im Projekt irgendwo die GPU nutzen? Antwort nach Durchsicht von
`build_rhs`, `simulate` und der Populationsschleife: **nein, nicht auf dem Paper-1-Pfad.** Vier
unabhaengige Gruende, jeder fuer sich ausreichend.

**1. Die Batch-Breite fehlt.** Eine GPU gewinnt bei ODEs dieser Groesse (dim 1–4, 512 Punkte) erst
ab ~1e4 gleichzeitigen Trajektorien — das ist der Arbeitsbereich von `DiffEqGPU.EnsembleGPUKernel`.
Vorhanden sind `pop_size = 20` plus Kinder, also 20–60 unabhaengige Kandidaten pro Level. Innerhalb
eines Kandidaten ist BFGS strikt sequenziell. Damit ist ausgerechnet das groesste offene
Kostenrisiko GPU-immun: die pathologischen Level (3–5 h, bis 39.933 Loss-Evals bei zwei Parametern)
sind eine Liniensuche, also eine Kette und kein Batch. Eine GPU verkuerzt sie um null.

**2. Die RHS ist nicht kernel-faehig.** `build_rhs` (`src/basis/interface.jl:24`) schliesst ueber
`basis.funcs::Vector{Function}` und dispatcht pro Term und Zeitschritt dynamisch. Das ist nicht auf
eine GPU kompilierbar; noetig waeren StaticArrays, allokationsfrei, typstabil. Der Umbau auf eine
Koeffizientenmatrix ueber der Stage-Basis waere die Vorbedingung fuer alles GPU-artige — und
CPU-seitig ohnehin ein Gewinn.

**3. Float64.** Das Projekt argumentiert mit `abstol = reltol = 1e-9`, Losses bei 1e-11 bis 1e-15
und bit-identischen Vergleichen. Consumer-GPUs rechnen FP64 mit 1/32 Durchsatz, waeren also
langsamer als wenige CPU-Kerne; Float32 wuerde genau die Stellen zerstoeren, ueber die das Paper
argumentiert. GPU hiesse hier zwingend A100/H100-Klasse.

**4. Die Hardware.** Orion vergibt 846 Jobs a 1 Kern, kein GPU-Node. Ueber die 756 Laeufe ist die
Parallelitaet als Job-Parallelitaet bereits vollstaendig ausgeschoepft.

**Was vorher kaeme.** Im Quellbaum steht kein einziges `Threads.@threads`, `@spawn` oder `pmap`. Die
20–60 Kandidaten pro Level werden seriell gefittet, obwohl vollstaendig unabhaengig — der
offensichtliche Faktor 4–16 auf dem bestehenden Pfad. Gleiche Konsequenz wie jede GPU-Idee: beruehrt
den Pfad jedes Phase-B-Laufs, aendert den Fingerprint. Gehoert damit hinter die Kampagne, zu WP-D4b.

**Wo GPU tatsaechlich passen wuerde, beides jenseits von Paper 1:**

- *Batched Parameterfitting statt BFGS* (Phase 5, als Forschungsfrage, nicht als Optimierung).
  Ersetzt man die sequenzielle Liniensuche durch ein populationsbasiertes/Multistart-Verfahren,
  entsteht die Batch-Breite von selbst: 20 Kandidaten x 500 Starts = 1e4 Trajektorien, identische
  RHS-Struktur, nur andere Parameter — der Idealfall fuer `EnsembleGPUKernel`. Adressiert zugleich
  dokumentierte Schmerzen (Sentinel-Loss `1e6`, verlorene Parameteroptima bei identischem Support).
  Es ist ein Algorithmenwechsel und aendert die experimentelle Bedingung.
- *Die geplanten Phase-3-Achsen* (Rauschen, Sampling-Dichte). Per Konstruktion Ensembles: gleiches
  System, gleiche Struktur, viele Realisierungen. Dort liegen 1e3–1e4 Solves natuerlich vor, ohne
  den Suchalgorithmus anzufassen.

**Entscheidung:** GPU bleibt Non-Goal wie in `CLAUDE.md` festgehalten. Reihenfolge, falls Rechenzeit
je drueckt: typstabile RHS → Threads ueber die Population → erst dann GPU. Der zweite Punkt oben
lohnt nur, wenn batched Fitting als eigener Beitrag gefuehrt wird.

### Lesender Code-Durchgang vor der Kampagne: nichts zu tun, und das ist der Befund

<!-- 212c4ef -->

Reiner Lesedurchgang auf Bloat, toten Code und Schreibqualitaet. **Keine Aenderung vorgenommen** —
jede haette den Pfad beruehrt, den 756 Zellen durchlaufen, und seit WP-M1 existiert ein bit-exakter
Anker, gegen den jede Aenderung neu zu verifizieren waere.

**Toter Code: praktisch keiner.** Bei 143 Funktionen und 6.565 Zeilen genau eine ungenutzte:
`_cap_uniform_step` in `src/structure/stage_cap.jl`, drei Zeilen. (Ein erster Durchlauf meldete 16
Kandidaten — Messfehler, Namen mit `!` wurden falsch gezaehlt.)

**Die 46 Prozent "Ballast" sind bezahlte Reproduzierbarkeit.** v3 (1.233 Zeilen), GP (457),
Screening (870) und Plotting (489) stehen zusammen fuer 46 % des Quellbaums und kommen im
Paper-1-Umfang nicht vor. Loeschen waere trotzdem falsch: Das Paper erzaehlt v2.2 → v3 → capped als
dokumentierte Fehleranalyse, und ohne lauffaehigen v3-Code sind diese Zahlen nicht reproduzierbar;
`gp_baseline` steckt im eingefrorenen Phase-A-Experiment. Das ist der Preis dafuer, die eigene
Geschichte nicht wegzuwerfen, und er wird bewusst gezahlt.

**Der eine echte Befund: die Suchschleife ist ein Monolith, dreimal geforkt.**

```text
656 Zeilen  evogrow.jl            search_structure
638 Zeilen  evogrow_v3.jl         search_structure
459 Zeilen  evogrow_screening.jl  search_structure
447 Zeilen  bfgs.jl               fit_parameters
256 Zeilen  gp.jl                 search_structure
```

2.009 Zeilen in vier Suchschleifen. Der Beleg fuer das Forken ist `_validate_policy`: dreimal
vorhanden, in `evogrow.jl` (15 Zeilen), `evogrow_screening.jl` (33) und `evogrow_v3.jl` (7) — drei
verschiedene Implementierungen unter demselben Namen in Nachbardateien. So etwas entsteht, wenn
Kopieren leichter ist als Erweitern.

Das ist das Ziel fuer WP-D4b: die gemeinsame Schleife herausziehen, Varianten als Strategien
einhaengen. Dann verschwinden die drei `_validate_policy` von selbst. Bleibt hinter der Kampagne,
aus dem in CLAUDE.md genannten Grund.

**Bewusste Entscheidung, zeitkritisch:** `evogrow_v3` und `gp_baseline` bleiben in `VARIANTS`. Die
Liste geht ueber `FINGERPRINT_VARIANT_LABELS` in den Fingerprint ein und ist nach dem ersten
Kampagnen-Record eingefroren. Entschieden am 2026-08-14, Begruendung wie oben.

Sonst: keine ungenutzten Abhaengigkeiten, saubere Interface-Struktur mit korrektem Dispatch
(`search_structure` 6x, `fit_parameters` 3x, `evaluate_loss` 2x sind Interface plus
Implementierungen, keine Duplikate).

---

## 2026-08-13

### WP-M1 - R2 und abgeleitete erwartete Stage; der letzte wissenschaftliche Blocker ist zu

<!-- HASH -->

Zwei Metriken haben gefehlt, und ohne sie haette die Kampagne 756 Records erzeugt, die ihre eigenen
Fragen nicht beantworten.

**R2, fuer alle 63 Systeme.** `PAPER_1.md` fuehrt es in der Kernmetrik-Tabelle, im Code gab es keine
Zeile dazu. Fuer die 43 Surrogatsysteme — zwei Drittel der Kampagne — blieb damit der rohe Loss als
einzige Guetegroesse, ohne Anschluss an die ODEBench-Literatur, die in R2 argumentiert. Implementiert
als `r2` (arithmetisches Mittel ueber Dimensionen) plus `r2_by_dim`.

Drei Faelle liefern ausdruecklich `null` statt einer plausiblen Zahl: nicht-endliche Vorhersagen, der
`MSELoss`-Sentinel bei `loss >= 1e6`, und verschwindende Referenzvarianz in einer Dimension. Und es
wurde **kein Schwellenwert** eingefuehrt: `docs/paper1_odebench_protocol_alignment.md` haelt fest,
dass die publizierten R2-Konventionen noch nicht verifiziert sind, also waere jede Schwelle erfunden.

**`expected_stage` abgeleitet statt gepflegt.** Bisher fuer alle 63 Phase-B-Systeme hartkodiert
`nothing`, womit `stage_overshoot` und `wasted_levels` durchgehend leer blieben — auch auf den 20
exakten Systemen. Ausgerechnet `wasted_levels` traegt die zentrale Aussage, dass Stage-Eskalation
Verschwendung ist. WP-A1 hat das quantifiziert: **33 von 33 Pilot-Records ohne beide Werte.**

Die Ableitung nutzt, was WP-E2 bereits erzeugt: `support_idxs` aus `phase_b_support.json` sind
Indizes in die Basis, und `default_staged_polynomial_basis(dim).term_groups` ordnet jeden Index einer
Stufe zu. Die erwartete Stage ist die hoechste Stufe, die noch einen Supportterm enthaelt.

Abnahme gegen **alle fuenf** handgepflegten Werte in `diagnostic_systems.jl`: Systeme 3, 11, 26, 31
und 63 — hand und abgeleitet stimmen jeweils ueberein. Auf Phase B: `exact_missing=0`,
`surrogate_nonnull=0`, `expected_stage_missing=43`, und die 43 sind exakt die Surrogatsysteme. Fuer
sie wird keine Stage erfunden; die erreichte Stage bleibt Beobachtung, nicht Abweichung von einem
Soll.

**Die entscheidende Abnahme war, dass sich nichts aendert.** Referenzzelle System 11, Seed 42:

```text
loss              4.635914151853964e-15  ->  4.635914151853964e-15
pruned_match      true                   ->  true
total_loss_evals  30550                  ->  30550
expected_stage    null                   ->  4
stage_overshoot   null                   ->  0
wasted_levels     null                   ->  0
r2                null                   ->  0.9999999999999564
```

Bis auf die letzte Stelle identisch. Das Paket fuegt Messungen hinzu, ohne die Suche anzufassen.

**Fingerprints, bewusst bewegt:**

| | vorher | nachher |
|---|---|---|
| Phase B | `c71c85ac2ec580ff` | `ca02ea284d621f6d` |
| Regression | `45cb2c4507007366` | `0825cdc88d9264a0` |

Phase B bewegt sich durch die abgeleiteten Stages **und** die Metrikdefinition; die Regression nur
durch letztere, weil ihre Systeme ihre Stages schon hatten. Dass die Metrikdefinition Teil der
Nutzlast ist, ist eine Entscheidung mit Begruendung: Die R2-Definition ist eine wissenschaftliche
Wahl — ein spaeterer Wechsel von "arithmetisches Mittel ueber Dimensionen" auf eine gepoolte Variante
wuerde Records stillschweigend unvergleichbar machen. So zeigt der Fingerprint es an.

**Folge fuer die Pilotdaten:** Sie stammen vom alten Stand und tragen den alten Fingerprint. Sie
bleiben gueltige Infrastrukturmessungen, duerfen aber nicht mit Kampagnen-Records vermengt werden.

**Grundsatz 8 in CLAUDE.md korrigiert.** Das nirgends definierte "target term-class usage" ist
gestrichen; es steht jetzt dort, worauf Surrogatsysteme tatsaechlich bewertet werden — Guete ueber
R2, erreichte Stage und Stabilitaet als Beobachtungen.

---

### WP-A1 - die Analysepipeline kann Kampagnendaten nicht lesen, und eine Stelle scheitert leise

<!-- HASH -->

Die Python-Auswertung ist Phase-A-foermig: `aggregate_run_registry.py` liest `run_registry.csv` aus
der `experiments/`-Infrastruktur. Die Kampagne schreibt per-Zelle-JSONL. **Direkt gefuettert bricht
die Aggregation hart ab** (`Expected 19 fields in line 22, saw 20`) — immerhin ehrlich.

Geloest ueber eine einzelne Konvertierung statt Aenderungen quer durch die Auswertungsskripte:
`analysis/scripts/aggregate/convert_campaign_history_to_run_registry.py`. Der Phase-A-Pfad bleibt
unangetastet, `paper1_phaseA_v1` weiter reproduzierbar.

**Der wichtigste Befund ist der stille.** Nach der Konvertierung laeuft `table_main_results.py`
fehlerfrei durch — und liefert Unsinn:

```text
agg_variants   = evogrow_v2_2_stage_capped, evogrow_v3, ...   (Kampagne)
table_variants = evogrow_v1, evogrow_v2_1, gp_baseline, ...   (eingefrorene Phase-A-Liste)
table_rows=30   table_nonempty_mean_loss=5
```

Das Skript indiziert auf eine fest verdrahtete Variantenliste um und laesst alles fallen, was es
nicht kennt. 25 von 30 Zeilen bleiben leer, ohne Fehlermeldung. `evaluate_hypotheses.py` scheitert
demgegenueber sauber mit `Missing expected variants`. Die Lehre: Vor der Auswertung muessen die
Downstream-Skripte von der Phase-A-Variantenliste geloest werden, sonst entsteht eine plausibel
aussehende, fast leere Tabelle.

**Zwei Felder bleiben bewusst leer statt geraten.** `total_invalid_evals` meint in Phase A
NaN-erzeugende Evaluationen; die Kampagne verteilt verwandte Begriffe auf `total_invalid_solves`,
`total_optimizer_invalid_result_fits`, `invalid_screening_evals` und Solver-Instabilitaetszaehler.
Ohne definierte Einheit wird nichts eingetragen. Und `exact_support_match` wird aus `pruned_match`
gespeist — nuetzlich, aber nicht semantisch identisch, und fuer Surrogatsysteme korrekt leer.

**Nachtest auf echten Pilotdaten.** Codex hatte kein `S:`-Laufwerk und musste auf lokale Altdaten
ausweichen; die Faelle `pruned_match: null` und `git_hash: "unknown"` blieben ungetestet. Nachgeholt
an 33 echten Cluster-Records: `loss`, `final_stage`, `elapsed_s` und `system_dim` durchgehend
gefuellt, `exact_support_match` in 11 von 33 (genau die exakten Systeme), Surrogatsysteme korrekt
leer. Die Bruecke haelt.

Dabei faellt der Beleg fuer WP-M1 quantitativ an: **`stage_overshoot` und `wasted_levels` sind in
33 von 33 Records leer**, weil `expected_stage` nirgends gesetzt ist.

---

### Jeder Cluster-Record trug `git_hash: "unknown"` - die Provenienzkette war offen

<!-- d2aed32 -->

Beim Zaehlen von Hash-Referenzen fuer eine ganz andere Frage aufgefallen: **alle 29 bisher auf Orion
erzeugten Records tragen `git_hash: "unknown"`.**

Die Auflage in `docs/hpc_requirements.md` §7 lautet, dass jeder Job Commit-Hash und
Konfigurations-Fingerprint aufzeichnet und eine Kampagne mit gemischten Hashes nicht publizierbar
ist. Die Zeile, die das leisten soll, ruft `git rev-parse` auf — und im Container gibt es kein
`.git`-Verzeichnis, weil `.dockerignore` es zu Recht ausschliesst. Der Code trug also ehrlich
`unknown` ein, und niemandem ist es aufgefallen, weil `Completed` und `error=null` ja stimmten.

Faktisch gerettet war die Nachvollziehbarkeit bisher allein durch den Image-Tag, der der Commit-SHA
ist. Aber **aus einem Record allein liess sich nicht sagen, welcher Code ihn erzeugt hat** — genau
das, was das Protokoll verlangt. Ein Kampagnen-Blocker, gefunden zwei Tage bevor er teuer geworden
waere.

**Der Fix backt die Revision beim Bauen ein.** `.gitlab-ci.yml` reicht `$CI_COMMIT_SHA` als
Build-Argument durch, das Dockerfile legt es als `EVOODE_GIT_SHA` ab und schreibt es zusaetzlich in
`build_provenance.json`, und `git_provenance()` faellt darauf zurueck, wenn kein Git verfuegbar ist.
Der Standardwert des Build-Arguments ist **leer**, nicht `unknown` — ein lokaler Bau ohne Argument
meldet damit weiterhin ehrlich eine unbekannte Revision statt einer falschen.

`git_dirty` ist im Container-Fall `false`: Ein CI-Bau checkt genau einen Commit in einen frischen
Klon aus, ist also per Konstruktion sauber. Wo Git verfuegbar ist — lokale Laeufe — bleibt das
bisherige Verhalten unveraendert, inklusive echter Dirty-Erkennung.

Der Fingerprint ist nicht betroffen: Seine Nutzlast enthaelt ausschliesslich
Konfigurationskonstanten, keine Provenienz. Die 29 Pilot-Records bleiben damit gueltige
Infrastrukturmessungen; sie sind ohnehin als wissenschaftlich wertlos deklariert.

---

### Repo-Inventur vor der Kampagne: SCRIPTS.md neu, Slurm-Schiene entfernt

<!-- 2b95eda -->

Anlass ist der Zeitpunkt, nicht Ordnungsliebe. CLAUDE.md verlangt, dass **alle
fingerprint-relevanten Aenderungen vor dem ersten Kampagnen-Record landen**; danach kostet jede
Aenderung die Geschlossenheit der Kampagne. Dies ist das letzte bequeme Fenster.

**Der groesste Befund war kein ueberfluessiges File, sondern ein Dokument, das mehr verspricht als es
haelt.** `SCRIPTS.md` wird in CLAUDE.md als "exact commands for every script" gefuehrt, dokumentierte
aber **9 von 33** Skripten — und ausgerechnet die der alten Welt (`aggregate.jl`,
`run_experiment.jl`, `debug_single.jl`). Vom Kampagnenpfad stand **nichts** darin: weder
`run_batch_cell.jl` noch `run_k8s_indexed_cell.jl` noch `generate_phase_b_manifest.jl` noch
`merge_batch_records.jl`. Das ist gefaehrlicher als eine Luecke, weil Vollstaendigkeit behauptet
wird. Neu geschrieben mit sieben Abschnitten, Kampagnenpfad zuerst, inklusive Flags, Umgebungs-
variablen und der drei Fallen, die uns heute begegnet sind (Bootstrap genau einmal, Exit 0 heisst
nicht gueltig, Indexbasis 0 gegen 1).

**Geloescht — veraltete Dokumente.** `docs/paper1_roadmap.md` (Stand 2026-05-17, also vor beiden
Gates, und selbsterklaert nachrangig gegenueber `PAPER_1.md`), `docs/projektjournal.md` samt PDF und
dem erzeugenden `tools/build_journal_pdf.py` (abgeleitete Lesefassung von DIARY.md, eingefroren auf
2026-08-03 und damit bereits widersprechend — dasselbe Muster wie `5b4bd5b`, wo die `docs/de`-Kopien
gingen), sowie `docs/hpc_briefing_2026-08-06.md` (Kurzfassung fuer einen stattgefundenen Termin, und
fuer die falsche Plattform).

**Geloescht — die Slurm-Schiene.** `containers/evoode_regression.apptainer` und die drei Skripte
unter `hpc/`. Sie adressieren einen Standort, den es fuer dieses Projekt nicht gibt; ihre Aufgabe war
die Vorlage fuer die Docker-Uebersetzung, und die ist erledigt. Der Grund fuers Loeschen statt
Behalten ist nicht Platz, sondern Irrefuehrung: Wer `hpc/slurm_*.sh` findet, haelt Slurm fuer den
Weg. Der Git-Verlauf bewahrt sie ohnehin.

**Bewusst behalten: die abgeschlossenen Studienskripte.** Zwanzig Dateien haben keine
Code-Referenz, was bei Einstiegspunkten nichts bedeutet. Wichtiger: `studies/lookahead/`,
`studies/linesearch/`, `studies/numerics/` und `studies/gate2_do_or_die/` haben Befunde erzeugt, auf
die sich die Argumentation stuetzt — die Tolerance-Invarianz auf System 26, die Widerlegung der
Sentinel-Hypothese, die Stage-Cap-Herleitung. Ein Skript, das ein publiziertes Ergebnis erzeugt hat,
ist kein Ballast, sondern dessen Reproduzierbarkeitsnachweis. Sie sind jetzt in SCRIPTS.md mit der
Frage gelistet, die sie beantwortet haben.

**Korrigierte Fehleinschaetzung.** `studies/regression/generate_manifest.jl` sah nach abgeloestem
Vorgaenger von `generate_phase_b_manifest.jl` aus. Er iteriert aber ueber `REGRESSION_SYSTEMS` und
erzeugt das Manifest der **Regressionskampagne** (90 Zellen), die neben Phase B geplant ist. Bleibt.

**Nicht angefasst: die Grafikabhaengigkeiten.** `Qt6`, `FFMPEG`, `Xorg`, `CairoMakie` kosteten beim
ersten Cluster-Bootstrap 1.022 von 2.760 Sekunden Praekompilierung fuer Pakete, die eine Rechenzelle
nie anfasst. Nach WP-H5 kosten sie **keine Laufzeit mehr**, nur Imagegroesse. Sie zu entfernen
aendert `Manifest.toml` und laesst Pkg gemeinsame Abhaengigkeiten neu aufloesen — verschobene Zahlen
kurz vor der Kampagne gegen etwas Plattenplatz ist ein schlechtes Verhaeltnis.

**Neu aufgefallen und noch offen:** `analysis/` erwartet `run_registry.csv` aus der
`experiments/`-Infrastruktur, die Kampagne schreibt aber `cell_*.jsonl`. Dazwischen steht
`merge_batch_records.jl`, aber ob die Analysepipeline dessen Ergebnis verarbeitet, ist nirgends
geprueft. Das ist kein Aufraeumthema, sondern ein Stolperstein **nach** der Kampagne — an den
Pilotdaten durchspielen, bevor 756 Records da sind.

`docs/hpc_requirements.md` traegt bis zur Ueberarbeitung einen Warnhinweis: falsche Plattform,
Laufzeitschaetzungen um ein bis zwei Groessenordnungen zu hoch, keine Walltime und damit kein
Checkpointing noetig. Gueltig bleiben Workload-Form, Ressourcenprofil pro Zelle und die
Reproduzierbarkeitsauflagen.

---

### WP-H5 - der eingebackene Praekompilierungscache war auf dem Cluster wertlos

<!-- be6bf99 -->

**Ergebnis vorweg, gemessen auf einem Orion-Node**: derselbe Bootstrap, derselbe Fingerprint, dieselbe
Ausgabe — **2.760 s vorher, 22 s nachher**. `manifest.csv` ist in beiden Laeufen exakt 77.201 Bytes
gross, `phase_b_fingerprint=c71c85ac2ec580ff` in beiden. `Precompiling packages...` taucht im zweiten
Lauf nicht mehr auf, und ein Ladetest meldet null `Rejecting cache file`. Das ist eine
Infrastruktur-Messung auf dedizierter Hardware, nicht der Laptop-Fall, den Grundsatz 7 ausschliesst.

**Und damit lief der erste Indexed Job durch**: drei 1D-Zellen, `completionMode: Indexed`,
`completions=3`. Die Abbildung haelt auf echter Hardware — Completion-Index 0/1/2 auf Listenzeile
1/2/3 auf Manifestzeile 1/2/3, kein Off-by-one. Drei Records und drei Heartbeats liegen unter
`/bigdata/data-science/joedicke/.../tasks/` als `cell_000001` bis `cell_000003`.

Beobachtet an Zelle 3 (System 1, IC 1, Seed 7): Abbruch bei **Level 20 von 30**, Stage 5, vier Level
ohne Verbesserung bei `loss=6.630e-05`. Zehn Level ungenutzt — dasselbe Muster, das WP-L/G auf System
3 gezeigt haben, hier zum ersten Mal auf Clusterhardware. `pruned=nothing` ist korrekt: System 1 ist
eines der 43 Surrogatsysteme. Die Kosten pro Level stiegen von 3,3 auf 12,7 s, weil spaetere Level
mehr Terme und damit mehr Parameter pro Fit tragen.

Damit ist der Weg vom Commit bis zum Record einmal vollstaendig und an jedem Uebergang verifiziert:
GitHub → GitLab → CI → Registry → OpenShift → Indexed Job → NFS.

---

**Der Befund.** Der erste Bootstrap auf Orion lief 46 Minuten, davon praktisch alles
Praekompilierung — obwohl das Image ein fertiges 3,1-GB-Depot mit 1,3 GB kompiliertem Code traegt.
Weder Konfiguration noch Code waren schuld: `JULIA_DEPOT_PATH` stimmte, `DEPOT_PATH` loeste korrekt
auf, der Cache war vorhanden und exakt so gross wie lokal. Julias Lader nannte den Grund selbst:

```text
Rejecting cache file .../compiled/v1.12/Logging/....ji
Reasons = "Unable to find compatible target in cached code image.
           Target 0 (icelake-server): Rejecting this target due to
           use of runtime-disabled features"
(cache misses: target mismatch (1))
```

Der GitLab-Runner ist eine Intel-Maschine und praekompiliert fuer `icelake-server`; die Orion-Nodes
sind AMD EPYC 7643, von Julia als `znver3` gemeldet. Praekompilierte Images enthalten nativen Code
und werden gegen die CPU-Features der laufenden Maschine geprueft — also wurde jede einzelne
Cache-Datei verworfen.

**Warum die lokale Verifikation das nicht finden konnte.** WP-H2 hat auf demselben Laptop gebaut und
ausgefuehrt; dort ist der Cache per Konstruktion gueltig. Der Fehler entsteht erst, wenn Bau- und
Laufmaschine auseinanderfallen, und das tut es erst seit der CI. Das ist eine Grenze lokaler
Verifikation, kein Versaeumnis — und sie ist notierenswert, weil sie fuer jede kuenftige
Image-Aenderung gilt.

**Der Fix**: `JULIA_CPU_TARGET="generic;znver3,clone_all"` im `ENV`-Block **vor** dem
Praekompilierungsschritt, damit der eingebackene Cache beide Ziele traegt — einen portablen
Grundstock und eine Zen-3-Variante. Bewusst nicht ausschliesslich auf die Cluster-CPU gepinnt: ein
Image, das nur auf einer Mikroarchitektur laeuft, erzeugt denselben Fehler in der Gegenrichtung.
Preis sind Imagegroesse und Bauzeit, einmal pro Commit statt Dutzende Minuten pro Pod.

**Kosten, beziffert.** Von den 46 Minuten entfielen 1.462 s auf den DifferentialEquations-Stapel,
**364 s auf Plots und 658 s auf Makie/CairoMakie** — gut 37 % auf einen Grafikstapel, den eine
Batch-Zelle nie anfasst. `src/plotting/` zieht `Qt6`, `FFMPEG`, `Xorg` und `CairoMakie` in den
Manifest. Nach diesem Fix kostet das **keine Laufzeit mehr**, nur noch Imagegroesse; die Trennung von
Rechen- und Plotting-Abhaengigkeiten bleibt damit eine Aufraeumaufgabe und ist kein
Kampagnenhindernis. Sie waere ausserdem fingerprint-relevant, weil sie `Project.toml` und
`Manifest.toml` und damit die Hashes im `build_provenance.json` aendert.

**Was der Lauf trotz allem bewiesen hat.** Der Bootstrap kam mit `EXITCODE=0` durch und schrieb
Manifest und alle fuenf Indexlisten nach `/bigdata/data-science/joedicke`. Gemeldet:
`phase_b_fingerprint=c71c85ac2ec580ff`, `regression_fingerprint=45cb2c4507007366`, `rows=756`,
`unique_identities=756`, `systems=63`, `representability_exact=20`, `representability_surrogate=43`,
Dimensionen 276/336/120/24. Damit ist belegt, dass das Image auf Orion denselben Code, dieselbe
Konfiguration und dieselbe Support-Tabelle traegt wie lokal — die Korrektheitsaussage steht
unabhaengig vom Kostenproblem.

**Nebenbefund, noch offen**: Der Bootstrap wurde bei 2 GiB per OOM abgeraeumt und braucht 8 GiB. Das
Repo-Manifest traegt noch den alten Wert. Ebenso offen: `restartPolicy: OnFailure` loescht
gescheiterte Pods samt Logs — fuer die Kampagne muss das `Never` sein, sonst verschwindet jede
fehlgeschlagene Zelle spurlos. Beides gehoert in ein gemeinsames Aufraeum-Work-Package.

---

### WP-H3/H4 - der Weg vom Commit zur Zelle auf Orion steht, und was der Cluster wirklich hergibt

<!-- 9f742fd -->

**WP-H3: das Image entsteht in der CI.** `.gitlab-ci.yml` baut `containers/Dockerfile` auf dem
CPU-Runner (ALEXANDRIA, Tag `cpu`) und legt es unter `registry.gitlab.scch.at:443/joedicke/evoode`
ab, getaggt mit `$CI_COMMIT_SHA` und dem Branch-Slug. Kein `latest`. Authentifizierung ueber die
eingebauten Job-Credentials, nicht ueber den persoenlichen PAT der Hausvorlage.

Der erste Lauf scheiterte an `http://docker:2375` — der Runner belegt `DOCKER_HOST` vor, erwartet
also einen `docker:dind`-Service, den die Hausvorlage nicht deklariert. Mit Service plus
`DOCKER_TLS_CERTDIR=""` laeuft es. Anmerkung fuer spaetere Leser: die Vorlage
`orion/dev-tutorial` traegt acht aufeinanderfolgende Commits "Update .gitlab-ci.yml" und
funktioniert so, wie sie dasteht, vermutlich nicht — sie ist Anhaltspunkt, nicht Referenz.

**Der Cluster wurde verifiziert, nicht erschlossen.** Ein Wegwerf-Pod mit dem Kampagnenimage hat vier
Unbekannte auf einmal geklaert. Die UID: Pods in `scch-das` laufen als **uid 0**, nicht unter der
gewuerfelten UID, gegen die WP-H2 gehaertet hat — die Haertung bleibt richtig, sie war nur nicht
noetig; das Image ist damit in beiden Welten belegt. Der NFS-Pfad: die Verzeichnisliste im Container
ist zeichengleich mit `S:\BigDataOrion`, womit `/bigdata/data-science/joedicke` bewiesen und nicht
mehr geraten ist. Das Pull-Secret: das vorhandene `gitlab-registry` deckt dieses Projekt **nicht** ab
(`requested access to the resource is denied`); ein eigenes `evoode-gitlab-pull` aus einem
Deploy-Token mit ausschliesslich `read_registry` loest es. Schreibrecht: vorhanden — aber weil wir
root sind. Das Zielverzeichnis ist `drwxrws--- <uid> 2000513` und gewaehrt "anderen" nichts; eine
nicht-root-UID in GID 0 koennte dort **nicht** schreiben. Eine Abhaengigkeit von der derzeitigen SCC,
kein Naturgesetz, und die erste Stelle zum Nachsehen, falls dort je etwas bricht.

**Keine Walltime.** Auskunft des Betriebs: CPU-Workloads werden selten angefasst, `kind: Job` wird in
Ruhe gelassen, ausser etwas haengt offensichtlich, und der Eigentuemer wird **vorher** informiert —
ausdruecklich unter der Bedingung, dass die Workload identifizierende Metadata traegt. Damit
entfaellt das in `docs/hpc_requirements.md` §6 erwogene Checkpointing fuer die 24-bis-48-Stunden-Zellen
vollstaendig. Die Labels `hpc.scch.at/service` und `hpc.scch.at/responsibility` sind entsprechend
keine Kosmetik, sondern die Bedingung dieser Zusage; WP-H4 hatte sie zunaechst durch erfundene
Schluessel ersetzt, WP-H4b korrigiert das.

**Kapazitaet: der Cluster ist kleiner als die Planung unterstellt.** Orion hat **zwei** Worker-Nodes
mit je einem AMD EPYC 7643, also **96 physische Kerne fuer das ganze Haus**. Beide Nodes tragen 4x
A100; die CPU-Kerne existieren primaer, um acht GPUs zu fuettern. `docs/hpc_requirements.md` denkt in
Core-Stunden-Kontingenten eines grossen Standorts und muss darauf umgeschrieben werden. Bei ~4.500
geschaetzten Core-Stunden bedeutet `parallelism=16` rund zwoelf Tage, 32 rund sechs, ein ganzer Node
rund vier — und unabhaengig davon liegt eine Untergrenze bei der laengsten Einzelzelle von geschaetzt
23 Stunden. Zusaetzlich sind die Laptop-Schaetzungen vermutlich optimistisch, weil viele Zellen auf
einem Sockel um L3 und Speicherbandbreite konkurrieren. Der Pilotlauf muss messen.

**WP-H4: Zellen als Indexed Job.** Bootstrap und Zell-Job sind getrennt — der Bootstrap schreibt
Manifest und Indexlisten einmalig ins NFS, die Zellen lesen nur. Waeren beide vereint, haetten 756
Pods einen Schreibwettlauf auf gemeinsamem Speicher und koennten sich uneinig sein, was Zeile *n*
bedeutet.

Die Abbildung `JOB_COMPLETION_INDEX` → Manifestzeile liegt in
`studies/regression/run_k8s_indexed_cell.jl`, also **im Image** und damit vom Commit-SHA abgedeckt,
statt im YAML, wo sie vom Code abdriften koennte. Der Fallstrick war die Indexbasis: Slurm-Arrays
sind dort 1-basiert, `JOB_COMPLETION_INDEX` ist 0-basiert. Eine woertliche Uebersetzung haette die
erste Zelle uebersprungen und einmal ueber das Listenende hinausgelesen — leise, mit 755 plausibel
aussehenden Records. Geprueft an beiden Raendern: Index 0 loest auf Zeile 1 und Manifestzeile 1 auf,
Index 275 auf Zeile 276 und Manifestzeile 516, was der letzten 1D-Zeile entspricht.

`generate_phase_b_manifest.jl` schreibt zusaetzlich `indices_all.txt`. Die Aenderung ist rein additiv;
Manifestinhalt und Identitaetsberechnung bleiben unberuehrt, der Phase-B-Fingerprint steht weiter auf
`c71c85ac2ec580ff`. Das Job-Manifest referenziert das Image ueber den Commit-SHA, nie ueber `main`:
ein wandernder Tag koennte Pods auf verschiedenem Code laufen lassen, waehrend jeder Record denselben
Hash zitiert — genau der Fehler, gegen den die Tag-Strategie gebaut ist.

Offen bis zum ersten echten Lauf: ob Orion `JOB_COMPLETION_INDEX` wie erwartet injiziert, ob
Bootstrap und Zellen ihre Dateien auf NFS landen, und jede Laufzeitzahl.

---

## 2026-08-12

### Das Zielsystem ist kein Slurm-Standort - und WP-H2, das Docker-Image dafuer

<!-- 16d156a -->

**Der Befund, der die halbe HPC-Vorbereitung neu adressiert.** Der Zielcluster ist SCCH "Orion", ein
**OpenShift/Kubernetes**-Cluster (`console-openshift-console.apps.orion.scch.at`), **kein
Slurm-Standort**. `docs/hpc_requirements.md`, `containers/evoode_regression.apptainer` und
`hpc/slurm_*.sh` richten sich damit an eine Plattform, die es fuer dieses Projekt nicht gibt. Sie
bleiben als Slurm-seitige Referenz liegen, sind aber nicht der Weg zur Kampagne.

Die Uebersetzungstabelle: Apptainer-`.sif` → Docker-Image, gebaut von GitLab CI und abgelegt in
`registry.gitlab.scch.at`; `sbatch --array` → Kubernetes `kind: Job` mit `completions`/`parallelism`;
`$SLURM_ARRAY_TASK_ID` → `$JOB_COMPLETION_INDEX`; Shared FS → NFS-Volume auf `nfs.orion.scch.at`.
CPU-only, 1 Kern und 2 GB pro Job — eine GPU beschleunigt 1D-bis-4D-ODE-Loesungen nicht.

**Was die Batch-Architektur betrifft: sie traegt.** Manifest als geordnete Zell-Liste, ein Entry
Point pro Zelle, Merge am Ende — das ist auch das Kubernetes-Modell. Es aendert sich nur, woher der
Index kommt. Die WP-B2- und WP-H1-Arbeit ist nicht verloren.

**Nebeneffekt zugunsten der Reproduzierbarkeit.** Die CI der Hausinstanz taggt Images mit
`$CI_COMMIT_SHA`, nicht mit `latest`. Referenziert das Job-Manifest diesen Tag, ist per Konstruktion
ausgeschlossen, dass zwei Zellen einer Kampagne auf verschiedenem Code laufen — ein staerkerer
Provenance-Nachweis als ein `.sif` auf einem Login-Node. GitHub bleibt Single Source of Truth,
GitLab ist reines Deploy-Ziel; der SHA ist auf beiden identisch.

**WP-H2: `containers/Dockerfile`.** Abschnittsweise aequivalent zur Apptainer-Definition — gleiche
Basis, gleicher Julia-Pin, Depot im Image, gleicher `build_provenance.json`, Entry Point auf
`run_batch_cell.jl`.

Die eine Anforderung ohne Apptainer-Gegenstueck: **OpenShift startet Container unter einer
willkuerlichen UID mit GID 0**, nicht als der aufrufende Nutzer. Ein Image, das eine feste Identitaet
annimmt, faellt dort mit einem Rechtefehler um, der nicht nach seiner Ursache aussieht. Geloest ueber
`chgrp -R 0` plus `chmod -R g=u` auf Quellbaum, Depot und Output-Wurzel, dazu `HOME=/tmp`, weil eine
gewuerfelte UID kein Home-Verzeichnis hat. Kein fixes `USER` — das ueberschreibt die Plattform ohnehin.

Verifikation lokal, ohne Cluster: Image baut; `build_provenance.json` meldet Julia 1.12.6 und beide
Abhaengigkeits-Hashes stimmen mit den eingecheckten Dateien ueberein; Manifestgenerierung im Container
liefert `phase_b_fingerprint=c71c85ac2ec580ff` und `rows=756`, also den WP-H1-Wert. Dieselbe 1D-Zelle
(System 11, Manifestindex 61) lief **zweimal** durch, einmal als Default-User und einmal als
`--user 12345:0`: beide `loss=4.674e-15`, `error=null`, Record und Heartbeat auf dem Host. Damit ist
der teuerste OpenShift-Fehlermodus lokal ausgeschlossen statt auf dem Cluster entdeckt.

`.dockerignore` ist eine Allowlist (`*` plus gezielte `!`-Eintraege), damit kein lokaler Zustand
still ins Image geraet. Bildgroesse 1,29 GB Inhalt, davon 3,1 GB Depot auf Platte.

Offen bis Orion: CI-Mechanik und Registry, Pull-Secrets, das Job-Manifest samt Index-Abbildung, die
NFS-Konventionen und jede Laufzeitzahl. Details in `codex/REPORT_WP_H2.md`.

---

### WP-E2 - Strukturmetrik fuer alle 63 Kampagnensysteme, und eine zu grosszuegige Klassifikation

<!-- e675083 -->

`pruned_match` war fuer **jedes** Phase-B-System `nothing`. Die Kampagne haette 756 Zellen ohne ihre
Hauptmetrik gerechnet. Zwei Ursachen, beide behoben.

**Der wahre Support existierte nur fuer fuenf Systeme.** `expected_terms_for` ist eine handgepflegte
Tabelle und warf fuer alles ausserhalb des Diagnosesets. Neu:
`studies/regression/derive_phase_b_support.jl` leitet den Support pro Gleichung aus den
RHS-Ausdruecken des Datensatzes ab und schreibt `phase_b_support.json`, eingecheckt und mit blossem
Auge pruefbar. Der Support muss zweierlei erfuellen: **exakt** (reproduziert die RHS bis 1e-9) und
**minimal** (kein Term entfernbar, ohne das zu brechen). Minimalitaet ist nicht kosmetisch — eine
blosse Schwelle auf den LS-Koeffizienten lieferte fuer die Systeme 52 und 62 Supports mit 18 bzw. 26
Termen, also eine ueber die Basis verschmierte Darstellung statt des wahren Supports.

Ausgewertet wird an beiden IC-Trajektorien plus 400 Streupunkten **innerhalb** der besuchten Box. Eine
einzelne Trajektorie laesst Basisspalten kollinear, womit die LS-Loesung nicht eindeutig ist; unter
dieser Bedingung war System 63 gar nicht ableitbar. Die Streuung bleibt in der Box, weil sie sonst den
Definitionsbereich mancher RHS verlaesst (`log`, `sqrt`).

**Abnahme: alle fuenf handkodierten Systeme werden exakt reproduziert**, System 63 in 4D
eingeschlossen. Der Generator bricht bei Abweichung ab, statt die Tabelle zu schreiben.

**Nebenbefund, der die Papieraussage betrifft: die Repraesentierbarkeit war zu grosszuegig.** Die
Systeme **30, 52 und 62** galten als `exact`, haben aber keinen wahren Support in der Basis. Der alte
Test fittete die Basis entlang **einer Trajektorie**; eine Funktion kann auf einer Kurve mit einer
Basisdarstellung uebereinstimmen, ohne im Zustandsraum diese Funktion zu sein. Die Kampagne stuetzt
ihre Strukturaussage damit auf **20 exakte Systeme, nicht 23**. `representability` kommt jetzt aus
derselben Rechnung wie der Support, damit "exakt" und "es gibt einen wahren Support" eine Aussage
sind statt zweier, die auseinanderlaufen koennen. Der alte Trajektorien-Test wurde entfernt.

**Entkopplung von `expected_stage`.** Support-Recovery haengt nicht davon ab, welche Stage erwartet
wurde; das Gate ist weg. Die stage-abhaengigen Metriken bleiben ohne erwartete Stage `nothing` — es
wurde keine erwartete Stage erfunden.

**Budget-Stopps nach Dimension**: keine Schemaaenderung noetig, Records tragen `system_id` und das
Manifest `system_dim`. Grenze, die zu nennen ist: die Parameterzahl pro Fit ist **nicht**
rekonstruierbar, weil die Zaehler pro Zelle aggregiert sind.

Fingerprints: Regression unveraendert `45cb2c4507007366`. Phase B `c0a236edf030e03a` →
`c71c85ac2ec580ff`, weil drei Systeme neu klassifiziert sind und der abgeleitete Support Teil der
Identitaet wird — er definiert, was `pruned_match` bedeutet.

Verifikation: exakte Zelle (System 11) liefert `pruned=true`, Surrogatzelle (System 1) `nothing`; die
Regressionszelle System 11 ist ueber **62 Felder unveraendert**. Details in `codex/REPORT_WP_E2.md`.

---

## 2026-08-11

### WP-F3 - Evaluationsbudget final auf 20.000 gesetzt

<!-- fb2c3a9 WP-F1/F2 -->
<!-- 8ae409e WP-F3/G1 -->

Entscheidung vor dem Campaign-Freeze: `BFGS_MAX_LOSS_EVALS` im Kampagnenpfad sinkt von 100.000 auf
**20.000** pro Parameterfit. Das aendert den Regressions- und den Phase-B-Fingerprint ein letztes
Mal vor dem ersten Paper-1-Campaign-Record; ab jetzt ist diese Konfiguration eingefroren.

Die Begruendung ist dreiteilig und gehoert in die Paper-Argumentation:

1. **Sicherheitslimit, kein Tuningparameter.** Das Budget begrenzt Arbeit, die messbar nichts mehr
   zum Ergebnis beitraegt. Es ersetzt die in WP-B3 entfernte Wall-Clock-Bremse, die auf langsamen
   Knoten binden und auf schnellen nicht binden konnte. Ein Budget in Zaehleinheiten ist
   maschinenunabhaengig und verbessert damit die Reproduzierbarkeit.
2. **Gemessener Wert.** WP-F1 und WP-F2 haben komplette Evaluierungssequenzen pro Fit aufgezeichnet
   und gemessen, wann der beste Loss erstmals erreicht wurde. Ueber alle gemessenen Fits
   (Dimension 1 bis 3, Parameterzahlen 1 bis 18) lag dieser Punkt spaetestens bei **5.760**. 20.000
   haelt einen Faktor von rund **3,5** darueber. Zweite unabhaengige Plausibilisierung: bei der
   maximalen Campaign-Parameterzahl 24 ergibt `2 * maxiters * (n_params + 1)` mit `maxiters = 200`
   genau 10.000; 20.000 ist das Doppelte davon.
3. **Harmlosigkeit demonstriert und falsifizierbar.** Fuer alle aufgezeichneten WP-F1/F2-Fits
   liefert ein Stop bei 20.000 denselben best-seen Loss wie der vollstaendige Lauf. Seit WP-D2 gibt
   ein Budget-Stop den besten tatsaechlich gesehenen Punkt zurueck, also graduell statt
   katastrophal. Seit WP-D3 zaehlt jeder Record Budget-Stopps; die Kampagne kann daher berichten, in
   wie vielen der 756 Phase-B-Laeufe das Limit gebunden hat.

Nachpruefung an der WP-D5-Referenzzelle (System 3, Seed 7, IC 1,
`evogrow_v2_2_stage_capped`): Das Budget bindet entgegen Erwartung auf 9 Parameterfits. Support,
Stage und `pruned_match` bleiben gleich, der Loss wird sogar kleiner, aber
`total_parameter_fits`, `total_loss_evals`, `total_ode_solves` und die Retcode-Liste aendern sich.
Das ist kein Grund, das Budget nachzuziehen, aber ein Befund: die Kampagne muss Budget-Stopps
sichtbar und nach Dimension/Parameterzahl auswerten.

**Die eigentliche Absicherung ist ein Regressionsvergleich ueber sieben Zellen**, gefahren in zwei
Armen: 20.000 im Working Tree gegen 100.000 aus einem Worktree auf `0af12c9`. Systeme 3 und 11 mit
je drei Seeds, dazu **System 26 als gekoppelter Fall**, IC-Satz 1.

Ergebnis: `pruned_match`, `final_stage` und `support_terms` sind in **7 von 7** Zellen identisch.
Gesamtaufwand 1.227.157 gegen 2.687.140 Loss-Evaluierungen, also **54,3 % Ersparnis** bei 43
Budget-Stopps. **Kein Loss wird schlechter**, einer wird um mehr als eine Groessenordnung besser.

Die gekoppelte Zelle ist der wichtigste Datenpunkt: System 26 liefert in beiden Armen denselben Loss
(1,396e-03), dieselbe Stage, denselben Support **und dieselbe Zahl Parameterfits (310)** bei 58,2 %
weniger Evaluierungen. Gleiche Fitzahl heisst gleicher Suchpfad — das Budget hat dort ausschliesslich
Leerlauf innerhalb einzelner Fits abgeschnitten, ohne die Suche umzulenken. Auf System 11 bindet es
gar nicht, die Zellen sind bit-identisch. Wo der Pfad divergiert (System 3, Seed 7: 130 statt 150
Fits), bleiben die Strukturmetriken dennoch gleich.

Damit ist Punkt 3 oben zu praezisieren: bit-identische Ergebnisse sind **nicht** allgemein zu
erwarten, sobald das Budget bindet — ein gestoppter Fit liefert andere Parameter, damit ein anderes
Objective und ab da einen anderen Suchpfad. Die belegbare Aussage lautet: ueber sieben Zellen
einschliesslich eines gekoppelten Systems bleiben alle Strukturmetriken unveraendert, kein Loss
verschlechtert sich, und der Aufwand halbiert sich.

WP-E2-Anforderung, bewusst noch nicht implementiert: Budget-Stopps muessen nach Dimension und
Parameterzahl aufgeschluesselt werden, nicht nur global. Ein ueberproportionales Binden auf
hochdimensionalen Systemen wuerde genau die komplexen gekoppelten Strukturen benachteiligen und die
zentrale Aussage verzerren; ein globaler Zaehler wuerde das verstecken.

---

### 1D-Kostenprofil: Pretuning bringt auf 1D nichts, und die Line-Search-Pathologie haengt nicht daran

<!-- dc2847c WP-E1 -->
<!-- 0af12c9 Kostenprofil -->

Aus WP-E1 fiel eine Zelle auf, die fuer ein triviales 1D-System (System 2, ein Term, ein Parameter)
**858.540** ODE-Integrationen verbrauchte — 28.618 Loss-Evaluierungen pro Fit, bei einem
Regressionsvergleich von 38. Erste Hypothese: das derivative Pretuning trifft per Least-Squares das
Optimum praktisch exakt, BFGS startet damit im Minimum, und die Line-Search verhungert. Zur Pruefung
ein vollstaendiges Profil ueber **alle 23 1D-Systeme in beiden Phase-B-Bedingungen**, Seed 42,
IC-Satz 1 — 46 Zellen, gemessen in Zaehlgroessen, nicht in Sekunden.

**Die Hypothese ist widerlegt.** Pathologische Zellen (>= 1.000 Evals/Fit): **12 mit Pretuning, 14
ohne**. Die Line-Search-Pathologie ist eine Eigenschaft des Optimierers, nicht des Startpunkts. Auch
der Kostenfaktor relativiert sich vollstaendig: aggregiert 40,97e6 gegen 26,84e6 Evaluierungen, also
**1,53x**, nicht die 288x des Einzelfalls. Es gibt ebenso extreme Gegenfaelle — auf System 8 kostet
`pretune_off` das Tausendfache, auf 3, 12 und 20 rund das Zehnfache.

**Pretuning bringt auf 1D keinen messbaren Nutzen.** Von 23 Systemen liegen **20** im Loss innerhalb
einer Zehnerpotenz; einmal ist Pretuning besser (System 15, 1,7 Dekaden), **zweimal schlechter**. Die
erreichte Stage ist in **23 von 23** identisch, der Support in 19 von 23. Bezahlt wird das mit 53 %
mehr Evaluierungen.

Ein Fall ist ein echter Schaden: **System 8**. Mit Pretuning bricht die Suche nach 1.830
Evaluierungen mit Loss **5,75e+2** ab; ohne Pretuning kostet sie 2,2e6 Evaluierungen und erreicht
6,48e-5 — knapp sieben Groessenordnungen. Der Warmstart fuehrt die Suche offenbar in ein Plateau,
das das Abbruchkriterium ausloest. Das ist ein Kandidat fuer eine gezielte Nachanalyse, nicht fuer
eine schnelle Korrektur.

**Wichtiger Vorbehalt:** alle 23 Systeme sind eindimensional. Der Forschungsfokus sind gekoppelte
Systeme, wo ein informierter Startpunkt bei mehreren Gleichungen und groesseren Parametervektoren
plausibel mehr beitraegt als bei einem einzigen Parameter. Das Nullergebnis auf 1D ist ein
Teilergebnis der Phase-B-Frage, kein Grund, die Bedingung zu streichen.

**Fuer die Ressourcenplanung:** im Mittel rund 1,5e6 ODE-Integrationen pro 1D-Zelle. Auf 756 Laeufe
hochgerechnet liegt das in der Groessenordnung der bisherigen 1e9-Annahme in
`docs/hpc_requirements.md`, mit Aufschlag fuer hoehere Dimensionen. Die Annahme ist damit eher knapp
als grosszuegig.

Rohdaten: `outputs/studies/regression/phase_b/profile1d/` (gitignored), Manifest
`wp_e1_manifest.csv`, Phase-B-Fingerprint `e577d9d692f3125b`.

Nebenbefund aus dem Lauf: ein Rechnerabsturz mitten im Profil kostete genau **eine** Zelle — die zum
Zeitpunkt des Absturzes laufende. Alle bereits geschriebenen Records ueberlebten, weil der Batch-Pfad
je Zelle einen Prozess faehrt und sofort schreibt. Unfreiwilliger, aber realistischer Test des
Resume-Verhaltens, das fuer den Cluster gebaut wurde.

---

## 2026-08-10

### WP-D2 bis WP-D5 - Optimizer-Budget, Contract, Telemetrie, Referenzverifikation

<!-- 0498218 WP-D2/D2b -->
<!-- e0bc706 WP-D3/D3b -->
<!-- e46e80b WP-D4a -->

Ausloeser war eine externe Code-Kritik, die vor dem HPC-Start gegengeprueft wurde. Zwei ihrer
Befunde waren echte Fehler, mehrere weitere korrekt, aber bewusst nicht Paper-1-Scope.

**WP-D2 — der Budget-Abbruch warf seine Ergebnisse weg.** `p_best`/`l_best` wurden ausschliesslich
in den `isfinite(res.minimum)`-Zweigen gesetzt. Das Evaluationsbudget bricht aber per Exception aus
der Loss-Closure ab, also liefen diese Zuweisungen nie: zurueck kam der *Startvektor* mit Loss
`1e6`. Verschaerfend ist, dass `1e6` zugleich der MSE-Sentinel fuer gescheiterte Simulationen ist —
ein budget-abgebrochener Fit war im Record von einem gescheiterten nicht unterscheidbar. Fix:
best-so-far wird in der Loss-Closure mitgefuehrt (mit demselben Clamp, mit dem auch simuliert wird,
damit Loss und Parameter zusammenpassen), der Sentinel als Startwert verschwindet, und
`max_loss_evals` ist als **Gesamtbudget pro Parameterfit** festgelegt — kein Nelder-Mead nach
Budget-Treffer, weil ein Kandidat sonst sein Budget ueberschreitet und der Kostenvergleich zwischen
Strukturen unfair wird.

**WP-D2b — der Fix hatte den Fallback abgeschaltet.** Die erste Fassung akzeptierte best-so-far auch
im Exception- und im Non-finite-Zweig und setzte damit den Wachposten des Nelder-Mead-Fallbacks auf
"Ergebnis vorhanden". Da `evaluate_loss` bei jedem Problem den *finiten* Sentinel liefert, war
best-so-far nach der ersten Auswertung praktisch immer gesetzt — der Fallback lief faktisch nie
mehr. Das aendert Zahlen auf einem Pfad, auf dem das Budget gar nicht bindet. Korrigiert zu drei
Stufen: Optimizer-Ergebnis, dann Fallback, dann best-so-far als letzte Instanz. Der Budget-Stop
bleibt Sofortakzeptanz; er braucht keinen Sonderfall, weil erschoepftes Budget den Fallback ohnehin
ausschliesst.

**WP-D3 — Phase B waere ohne Bremse gelaufen.** `experiments/run_experiment.jl` konstruierte den
Optimierer nur mit `maxiters`; alles uebrige, insbesondere das Budget, kam aus den seit WP-B3
unbegrenzten Defaults. Die Kampagne haette also unbudgetiert gerechnet, waehrend die Regression, die
sie validieren soll, bei 100.000 steht. Jetzt kommen alle deterministischen Parameter aus der
Konfiguration, und `generate_manifest.jl` traegt sie, damit ein Manifest den Optimierer vollstaendig
beschreibt. Die elf ungebudgeteten Aufrufstellen in `benchmarks/` und `studies/` sind bewusst
dokumentierter Backlog und nicht angefasst — kein Repo-Cleanup unmittelbar vor einer Kampagne.
Zusaetzlich einmalig ins Record-Schema: Budget-Stopps, Fallback-Ergebnisse, Last-Resort-Faelle und
ungueltige Ergebnisse pro Lauf. Ohne diese Zaehler waere ein budget-abgebrochener Phase-B-Lauf im
Output unsichtbar. Der aus WP-D2 moegliche Rueckgabewert `Inf` wird an der JSON-Grenze als String
geschrieben; `Infinity` ist kein gueltiges JSON. Fingerprint `db8ec4003aa99a0e` →
`7acd3ebf3f60b974`.

**WP-D3b — der Fallback-Zaehler zaehlte doppelt.** Bedingung war `method == "NelderMead"`, was nach
D2b auch auf Last-Resort-Faelle zutrifft. Jetzt zusaetzlich `result_source == "optimizer_return"`;
die ersten drei Zaehler sind disjunkt, "ungueltiges Ergebnis" darf bewusst ueberlappen.

**WP-D4a — der stille Refit in `discover()` ist weg.** Bei abweichender Parameterzahl wurden
Parameter und Loss neu gefittet, das Objective aber nicht — ein Resultat aus zwei Zustaenden, bei
EvoGrows Loss-plus-Komplexitaet arithmetisch unmoeglich. `discover()` kann das auch nicht reparieren,
weil es die Objective-Definition einer beliebigen Suche nicht kennt. Jetzt harter `error()` mit
erwarteter und erhaltener Zahl, Suchverfahren und Struktur in der Meldung. Kein Rescue in den
Runnern: die Zelle faellt als failed aus und wird vom Merge zurueckgewiesen. Eine fehlende Zelle ist
sichtbar, eine mit inkonsistenten Zahlen nicht.

**WP-D5 — Referenzverifikation, beide Faelle bestanden.**

*A, nicht-bindend.* System 3, Seed 7, IC-Satz 1: derselbe Fall auf dem Commit vor WP-D2 (Worktree
auf 29951a6) und auf dem aktuellen Stand. Loss `1.920e-09` in beiden, Stage 2/2, `pruned_match`
true. Der vollstaendige Feldvergleich ueber alle gemeinsamen Record-Felder ergibt **genau zwei
Abweichungen, beide Zeitfelder** — nach Designprinzip 7 ohnehin keine Evidenz. Bit-identisch sind
Loss, Objective, Support, Parameter, `total_parameter_fits`, `total_loss_evals`,
`total_ode_solves`, alle Limit-Zaehler sowie Stage- und Cap-Entscheidungen. Kein bestehendes Feld
ist verschwunden. Vorab geprueft, dass die WP-D3-Aenderung an `_polish_optimizer` diese Zelle nicht
erreichen kann: die Funktion existiert nur fuer `EvoGrowScreening`, die finale Variante konstruiert
ein `EvoGrow`. Eine Abweichung waere also ein Befund gewesen, keine erwartete Folge.

*B, bindendes Budget.* Logistisches 1D-System, `max_loss_evals = 40`: 78 Fits, 3.120 Evaluierungen
— exakt 78 x 40, kein Fit ueberschreitet sein Budget. Alle 78 melden Budget-Stop, **null** davon
ungueltig, null Fallback, null Last-Resort. Damit ist der D2-Fix am laufenden System belegt: vor der
Reparatur waeren das 78 Fits mit Startvektor und Sentinel-Loss gewesen. Der Loss ist mit `3.5e-3`
erwartungsgemaess schlecht gegenueber `2.5e-14` unbudgetiert, aber ein gemessenes Ergebnis und kein
Sentinel.

**Anmerkung zum Testaufbau.** `src/optimize/bfgs.jl` enthaelt nun einen Solve-Hook (`const Ref`,
Default `nothing`), ueber den Tests Optimizer-Fehlschlaege deterministisch erzwingen. In Produktion
verhaltensneutral — der Aufruf geht mit identischen Argumenten an `Optimization.solve`. Bewusst
akzeptiert: einen Fehlschlag numerisch zu provozieren waere fragil gewesen.

**Nicht angefasst, bewusst.** Struktur-Deduplizierung und ein kanonischer Hash fuer `StructureSpec`
(bei `pretuning=false` sind Duplikate zugleich implizite Multistarts, ein Cache waere also keine
reine Beschleunigung, sondern eine Aenderung der experimentellen Bedingung); ein
Evaluation-Result-Typ statt der Sentinel-Semantik; Remove/Replace-Operatoren gegen das
Growth-only-Verhalten; die Discover-API-Bereinigung (`isa BFGSOptimizer`, typisiertes
Struktursuch-Resultat, `search_loss`/`final_loss`-Benennung). Letztere ist als WP-D4b nach der
Kampagne vorgesehen — ein bekannter haesslicher Pfad ist unmittelbar vor einer Kampagne sicherer als
ein frisch abstrahierter sauberer.

---

### WP-D1 - Freeze der tatsaechlich benutzten Julia-Umgebung

<!-- 417648e -->

Die dokumentierte Umgebung war falsch: mehrere Texte und die Apptainer-Definition nannten Julia
1.11.5, waehrend `Manifest.toml` `julia_version = "1.12.6"` enthaelt, die Entwicklung auf 1.12.6
laeuft und die vorhandenen Phase-A- und Regressionsresultate unter 1.12.6 erzeugt wurden.
Entscheidung: nicht die Resultate auf die alte Dokumentationsbehauptung migrieren, sondern die
tatsaechlich benutzte Umgebung als Freeze deklarieren.

`Project.toml` deklariert nun `julia = "1.12"`, der Container baut von `julia:1.12.6-bookworm`,
und die Container-Provenance schreibt Julia-Version sowie SHA-256-Hashes von `Project.toml` und
`Manifest.toml` nach `/opt/EvoODE/build_provenance.json`. `Manifest.toml` bleibt unveraendert; die
Abhaengigkeitsstate ist der Freeze, nicht ein neu aufgeloester Zustand.

**Nachtrag 2026-08-10: Load-Smoke im leeren Depot bestanden.** Frisches Depot, `Pkg.instantiate()`,
`Pkg.precompile()`, dann `using EvoODE` mit einem Basis-Aufruf: Exit 0, erwartete Ausgabe, und
`Manifest.toml` byte-identisch vor und nach dem Lauf. Damit ist nicht nur die Installierbarkeit,
sondern die **Benutzbarkeit** des eingefrorenen Zustands belegt — die eigentliche Abnahme, die im
ersten Anlauf offen geblieben war (das dort verwendete Smoke-Kommando rief zudem
`default_polynomial_basis` mit zwei Argumenten auf, die Funktion nimmt eines).

Zwei Beobachtungen aus dem Lauf, beide nicht blockierend. Erstens brach `Pkg.instantiate()` einmalig
mit `IOError: rm(...): directory not empty` beim Entpacken von `AxisArrays` ab — ein
Windows-Dateisystemeffekt im Temp-Verzeichnis, kein Manifest- oder Aufloesungsproblem; der
anschliessende `Pkg.precompile()` hat die 554 Pakete vollstaendig installiert und der
Manifest-Hash blieb gleich. Im Linux-Container ist das gegenstandslos. Zweitens meldet `Plots`
beim Praekompilieren `GKS: cairoplugin.dll: can't load library` — headless erwartbar und fuer die
Kampagne ohne Belang, da dort nicht geplottet wird. Das vollstaendige Depot belegt 2,78 GB; im
Container faellt das einmalig im Image an, nicht pro Job.

---

## 2026-08-03

### WP-B3 — Wall-Clock raus aus dem Optimierer, Merge-Semantik geradegezogen

<!-- 0f4d006 -->

Drei Luecken vor der Kampagne geschlossen.

**Merge.** `merge_batch_records.jl` verweigert jetzt Records mit gesetztem `error` und zaehlt sie
separat als `skipped_failed`. Vorher wurde eine vom Cluster-Timeout gekillte Zelle gemerged, hat
damit ihren Eindeutigkeitsschluessel belegt und den eigenen erfolgreichen Wiederlauf als Duplikat
blockiert. Die Task-Datei bleibt erhalten — auf einem 4D-System ist ein Absturz nach 40 Stunden ein
Befund, kein Muell.

**`BFGS_TIME_LIMIT_S = 1800` ist weg.** Ersetzt durch `BFGS_MAX_LOSS_EVALS = 100_000` pro
Parameterfit, also ein Budget in Zaehlgroessen. Ein Wall-Clock-Limit im Optimierer haette auf einem
langsamen Knoten gebunden und auf einem schnellen nicht — das wissenschaftliche Ergebnis haette an
der Knotenzuteilung gehangen. Records tragen jetzt `total_loss_evals` und
`total_optimizer_eval_budget_limit_hits`. Fingerprint `256014cf6f0295e1` → `db8ec4003aa99a0e`; die
WP-B1-Verifikationszelle liefert darunter unveraendert `5.18873247985214e-9` bei Cap `[2]`, das
Budget bindet auf einer gesunden Zelle also nicht.

**1D-Klasse gemessen statt skaliert.** Sechs Zellen (Systeme 3 und 11, IC-Satz 1, drei Seeds) durch
den *Batch*-Pfad, nicht durch die Suite-Schleife — also durch genau den Pfad, den der Cluster
benutzt. 110–290 Parameterfits, 1,1e4–5,7e5 ODE-Integrationen pro Job, null Budget-Treffer.
`docs/hpc_requirements.md` §5 stuetzt die 1D-Zeile jetzt darauf und weist die Kernstunden-Tabelle
ausdruecklich als Planungsannahme aus.

**Zwei Anmerkungen zur Kalibrierung, beide nicht blockierend.** Erstens ist das Budget gegen
*Mittelwerte* kalibriert (max. 7.577 Loss-Evals pro Fit im Mittel, daher der berichtete Faktor 13);
gegen den bekannten pathologischen Einzelfit von 39.933 Evals bleiben aber nur **2,5x**. Das Budget
ist damit weiterhin ein Sicherheitsnetz und kein Kostenhebel — die Line-Search-Pathologie bleibt
offen, wie vorgesehen. Zweitens: die Defaults von `BFGSOptimizer` sind auf `time_limit_s = Inf` und
`max_loss_evals = typemax(Int)` gesetzt. Der Regressionspfad setzt sein Budget explizit, aber
`experiments/run_experiment.jl`, `benchmarks/` und mehrere Studien konstruieren den Optimierer ohne
Budget und haben damit **gar keine Bremse mehr**, wo vorher 300 s standen. Vor Phase B ueber
`run_experiment.jl` zu beheben.

---

### WP-B2 — Batch-Einstiegspunkt und Container fuer den Cluster

<!-- 5a3797a -->

Die Suite lief bisher als geschachtelte Schleife in einem Prozess, gesteuert ueber
Umgebungsvariablen. Das ueberlebt keinen Scheduler. Neues Ausfuehrungsmodell: ein Slurm-Job-Array,
jede Array-Task ist ein Prozess, rechnet **genau eine Zelle** und beendet sich. Drei Teile:
`generate_manifest.jl` (Kampagne als geordnete CSV, 120 Zeilen = 4 Varianten x 5 Systeme x 2
IC-Saetze x 3 Seeds, regenerierbar byte-identisch), `run_batch_cell.jl` (ein Index rein, eine
JSONL-Datei raus, Exitcode 0 nur bei Erfolg), `merge_batch_records.jl` (Konsolidierung ueber den
Eindeutigkeitsschluessel, wiederholt ausfuehrbar).

Der wichtigste Teil ist der **Fingerprint-Guard**: stimmt der Fingerprint im Manifest nicht mit dem
zur Laufzeit berechneten ueberein, bricht die Task ab, bevor sie rechnet. Verifiziert — ein
manipuliertes Manifest wird mit Exitcode 1 und ohne Ausgabedatei abgewiesen. Eine Kampagne mit
gemischten Fingerprints ist nicht publizierbar, und auf 846 Jobs faellt das sonst erst beim
Auswerten auf.

Verifikationszelle System 3 / IC 1 / Seed 42 / `evogrow_v2_2_stage_capped` durch den Batch-Pfad:
Loss `5.18873247985214e-9`, Cap `[2]`, `eq_overshoot = [0]`, `pruned_match = true`, Support
`[["u1","u1^2"]]`, Exitcode 0 — **exakt das WP-B1-Ergebnis**, wie gefordert, nicht nur naeherungsweise.
Merge in eine Scratch-Kopie: erster Lauf `added=1`, zweiter `added=0, skipped=1`.

**Fingerprint erneut geaendert: `fa2469a4dad1b72c` → `256014cf6f0295e1`.** Die Nutzlast beschrieb
das Zeitgitter als `range(0.0, 10.0; length=512)`, tatsaechlich laeuft der `t`-Vektor aus dem
Datensatz; numerisch `i*10/511`, was ein Julia-`range` nicht bitgenau reproduzieren muss. Das Label
beschrieb also etwas anderes als das Ausgefuehrte. Korrigiert auf
`dataset solutions[1][1].t grid; shipped y ignored`. Kostet nichts: unter `fa2469a4dad1b72c` existiert
kein einziger History-Record.

Dimensionsklassen: ein globales Manifest, dazu pro Dimension eine Indexliste
(`indices_dim1/2/4.txt`, 48/48/24 Zellen; 3D kommt in der Regressionssuite nicht vor). So bleibt die
Kampagnenidentitaet in einer Datei, waehrend Slurm pro Klasse eigene Walltimes bekommt.

Container (`containers/evoode_regression.apptainer`): damals als Julia 1.11.5 gepinnt dokumentiert;
WP-D1 korrigierte das als Dokumentationsfehler, weil die vorhandenen Ergebnisse auf 1.12.6
entstanden. `instantiate` und
`precompile` **zur Bauzeit**, Depot im Image, `JULIA_NUM_THREADS=1` und `OPENBLAS_NUM_THREADS=1`
gesetzt, Ausgaben nur ueber ein gebundenes `/outputs`. Nicht gebaut — diese Umgebung hat weder
Apptainer noch Slurm; beides ist statisch geprueft und als ungetestet ausgewiesen.

**Ein Defekt beim Review gefunden.** `run_batch_cell.jl` schreibt auch bei einem Fehler einen Record
(mit gesetztem `error`) und beendet sich dann mit Exitcode 1. `merge_batch_records.jl` filtert
`error` aber nicht — anders als `load_completed_cells` in `run_regression.jl`, das genau das tut.
Folge: eine abgestuerzte Zelle vergiftet ihren Schluessel, und ein spaeterer erfolgreicher Wiederlauf
wird beim Merge als Duplikat verworfen. Auf einem Cluster mit Timeouts und OOM-Kills ist das kein
Randfall. Muss vor der Kampagne behoben werden.

---

### Projektjournal auf Stand 2026-08-03

<!-- ee52eb3 -->

Vier neue Kapitel (3.22 Attribution, 3.23 Endvariante, 3.24 Gitter-Entscheidung, 3.25 Aufraeumen und
Cluster), Kapitel 4–8 durchgezogen. Dazu `tools/build_journal_pdf.py`: die bisherigen PDFs stammten
aus einem manuellen Browserdruck und waren nicht reproduzierbar. Jetzt Markdown → HTML →
Headless-Chromium in einem Aufruf. 24 Seiten, Dichte 46 Quellzeilen/Seite gegen vorher 47.

Vorfall: ein pauschales `git add -A` hat Codex' laufende WP-B2-Arbeit in den Journal-Commit gezogen.
Per `reset --soft` aufgeloest, fremde Pfade ausgestaged, neu committet. Zweites Mal an einem Tag —
Regel jetzt festgehalten: in diesem Repo nur explizite Pfade stagen, solange Codex parallel im
selben Arbeitsbaum schreibt.

---

### WP-B1 — Regressionssuite auf das Phase-B-Abtastprotokoll

<!-- 82c4784 -->

Fest verdrahtete `u0`/`tspan`/`T` durch datensatzabgeleitete Werte ersetzt: 512 Punkte ueber
t in [0,10], beide IC-Saetze, Trajektorien selbst mit `Tsit5` bei 1e-9 integriert. Zellen werden
jetzt ueber (Variante, System, **IC-Satz**, Seed) identifiziert. Jeder Record traegt zusaetzlich
`derivative_active_fractions` pro Gleichung — damit eine gescheiterte Zelle direkt als
"Trajektorie trug nichts" lesbar ist statt als Methodenversagen. Fingerprint `fa2469a4dad1b72c`
(inzwischen durch WP-B2 abgeloest); die 42 alten Records bleiben unter ihren alten Fingerprints.

---

### CLAUDE.md aufgeteilt — 1251 auf 282 Zeilen

<!-- 6e7b916 -->

`CLAUDE.md` trug drei Sorten Inhalt gleichzeitig: Orientierung, Komponentenreferenz und ein
eingefrorenes Experimentprotokoll. Verschoben, wortgleich, nichts geloescht:

- Komponentenreferenz (Typen, Pipeline, Suchalgorithmen, Basen, Optimierer, Stopping-Logik,
  Experiment-Infrastruktur, Benchmark-Daten) → `docs/architecture.md`, 403 Zeilen
- das 263-zeilige Reproduzierbarkeitsprotokoll, das die eingefrorene `paper1_phaseA_v1` beschreibt
  → `docs/paper1_phaseA_reproducibility.md`, 273 Zeilen

Verifiziert, dass keine Ueberschrift verlorenging: alle alten `##`/`###`-Titel finden sich in einer
der drei Dateien wieder oder sind nachweislich zusammengefasst (Vision + Core Idea + PhD Focus →
"What This Project Is", Phase 1–5 → Statustabelle).

Zwei Folgefunde: `docs/paper1_study_protocol.md` verwies auf den verschobenen Abschnitt (korrigiert),
und `docs/de/` enthielt deutsche Lesefassungen vom 2026-04-26 bzw. 2026-05-08, die den Stand vor
Gate 1, Gate 2 und der Variantenentscheidung wiedergaben. Auf Entscheidung des Users geloescht —
eine veraltete Zweitfassung ist schlechter als keine.

Der Kopfbereich haelt jetzt eine Dokumentenkarte: welche Datei was haelt. Die alte Formulierung
"single source of truth ... do not maintain a second planning document" war der Grund, warum alles
in diese eine Datei gewandert ist. Die Regel gilt weiter, aber praezisiert: **Planung und Status**
gehoeren hierher, Referenz und Chronologie nicht.

---

### Konsolidierung — CLAUDE.md und Protokoll-Audit auf Stand gebracht

<!-- 2158170 -->

`CLAUDE.md` war zu einem zweiten Tagebuch geworden: die Prioritätenliste enthielt rund 100 Zeilen
chronologischer WP-Einträge, die DIARY.md dupliziert haben. Neu gegliedert nach dem, was ein Befund
*einschränkt*, nicht nach Reihenfolge — Staged-Growth-Claim, Ursachen des v3-Scheiterns, Look-Ahead
Cap, Endvariante, Phase-B-Protokoll, Kosten/Numerik. Dazu ein eigener Phase-2-Abschnitt für
`evogrow_v2_2_stage_capped` als Endvariante, aktualisierte Studien-Tabelle, Roadmap und Known Gaps
(neu darin: die ungelöste Strukturfindung auf gekoppelten Systemen, die IC-Abhängigkeit des Caps,
der Rechenbedarf von Phase B).

`docs/paper1_odebench_protocol_alignment.md` §3 hielt noch „zwei Optionen, offen" fest. Ersetzt
durch die getroffene Entscheidung samt der Messungen, die Gitterdichte und Datengenauigkeit
trennen, und fünf Konsequenzen, die mitgezogen werden müssen — darunter die Abweichung zu unseren
Gunsten, falls publizierte Zahlen auf den gelieferten Trajektorien gerechnet wurden.

---

### WP-G1 / WP-G1b — Gitter ja, Trajektorien nein

<!-- 8c5319b, 3fc286c -->

Caps auf dem ODEBench-Datensatzgitter (512 Punkte, t in [0,10]) nachgemessen, beide IC-Saetze,
beide Datenquellen: **A** = gelieferte `y`-Matrizen, **B** = selbst integriert mit `Tsit5` bei
`abstol = reltol = 1e-9` auf identischem Gitter. Keine Suche, reine Messung.
Skript `studies/lookahead/measure_dataset_grid_caps.jl`, Report
`docs/wp_g1_dataset_grid_caps.md`.

| System | per-System-Gitter | Datensatzgitter IC1 | IC2 | Wahrheit |
|---|---|---|---|---|
| 3 | `[2]` | `[2]` | `[2]` | `[2]` |
| 11 | `[4]` | `[4]` | `[4]` | `[4]` |
| 26 | `[3,3]` | `[3,3]` | `[3,3]` | `[3,3]` |
| 31 | `[3,3]` | `[3,3]` | **`[1,nothing]`** | `[3,3]` |
| 54 | `[nothing,2,2]` | **`[nothing,3,3]`** | **`[nothing,3,3]`** | `[3,3,3]` |
| 63 | alle `nothing` | alle `nothing` | alle `nothing` | `[3,3,1,1]` |

**Vorhersage 1 bestaetigt.** Die zwei bekannten Sicherheitsverletzungen auf System 54 verschwinden.
Auf IC-Satz 1: Verletzungen 2 → 0, korrekte Caps 6 → 8 von 13 Gleichungen. Das ist exakt, was
WP-L3 aus der Aufloesungsgrenze vorhergesagt hatte.

**Vorhersage 2 falsifiziert.** System 63 bleibt auf beiden IC-Saetzen vollstaendig `nothing`. Kein
Artefakt unseres t=30-Horizonts — die Identifizierbarkeitsgrenze ist echt.

**Arm A = Arm B, in allen 26 Zellen.** Die Rauschboeden unterscheiden sich erst in der dritten bis
vierten Stelle. Erklaerung: der Integrationsfehler der gelieferten Daten ist *glatt* in t, kein
punktweises Rauschen, und ein ableitungsbasierter Rauschboden sieht glatten Fehler praktisch nicht.
**Der Gewinn auf System 54 gehoert also der Gitterdichte, nicht der Datenqualitaet.**

**Daraus folgt aber nicht, dass die gelieferten Trajektorien brauchbar sind.** Der Cap ist gegen
den Datenfehler immun, der Loss ist es nicht. Gegen eine unabhaengig konvergierte RK4-Referenz
(Selbstkonvergenz ~1e-13) erzwingen die gelieferten Daten diese MSE-Untergrenzen:

| System | MSE-Boden | unser bestes Ergebnis |
|---|---|---|
| 3 | **2,5e-02** | 1,3e-08 |
| 11 | 1,9e-11 | **4,4e-15** |
| 31 | 6,1e-10 | **6,8e-11** |
| 26 | 3,5e-11 | 1,4e-03 |
| 54 | 2,0e-07 | — |

Auf 3, 11 und 31 waeren unsere bisherigen Ergebnisse mit diesen Daten unerreichbar, auf System 3
um sechs Groessenordnungen. Die `nfev`-Felder bestaetigen die Ursache: System 3 wurde mit 77
Funktionsauswertungen ueber t in [0,10] integriert, also auf scipy-Defaulttoleranzen.

**Empfehlung fuer Phase B: Abtastprotokoll uebernehmen, Trajektorien selbst integrieren.**
512 Punkte, t in [0,10], beide IC-Saetze, `Tsit5` bei 1e-9. Der Cap ist gegenueber dieser Wahl
indifferent, sie kostet also nichts von dem, was hier gemessen wurde. Offener Punkt fuer den
Protokoll-Audit: falls publizierte Zahlen auf den gelieferten Trajektorien gerechnet wurden,
arbeiten wir auf saubereren Daten als die Vergleichsarbeiten. Das ist eine Abweichung zu unseren
Gunsten und muss deklariert werden.

**Korrektur an meiner eigenen Zwischenthese.** Aus der System-31-Diagnose hatte ich gefolgert, der
feste Horizont erzeuge systematisch tote Zellen und das ziehe sich durch Phase B. Die Messung
begrenzt das scharf: von 26 Zellen sind 5 signalarm (`derivative_active_fraction <= 0.10`), und
**nur eine davon scheitert** — die anderen vier liefern korrekte Caps. Von den 12 scheiternden
Zellen ist genau eine signalarm. System 63 hat `derivative_active_fraction = 1` auf allen acht
Zellen und scheitert vollstaendig. Signalarmut erklaert also genau einen Fall (System 31 IC2
Gleichung 1: Epidemie nach t = 0,47 durch, 5,3 % der Punkte tragen Dynamik), nicht das Muster.

Notiz zur Diagnosespalte: `state_below_1pct_spread_time` feuert bei t=0 fuer wachsende Zustaende
(System 3, System 63 Gleichungen 3 und 4). Nicht falsch, aber fuer diese Faelle bedeutungslos;
tragend ist `derivative_active_fraction`.

---

### No-Harm-Zellen Systeme 3 und 11 — sauber, mit einem echten Ausreisser

<!-- 77f0fed -->

Sechs Zellen `evogrow_v2_2_stage_capped` x {3, 11} x {42, 123, 7}, sequenziell, Fingerprint
`df5db7763bcd2449`, `git_hash 63d4c1c`, `total_optimizer_safety_limit_hits = 0` durchgehend.
In `history.jsonl` gemergt (36 → 42 Records).

Alle sechs: Cap korrekt (`[2]` bzw. `[4]`), `eq_overshoot = [0]`, `eq_wasted_levels = [0]`,
`pruned_match = true`, Support exakt die Wahrheit (`u1, u1^2` bzw. `u1, u1^2, u1^3`).
**Der Cap macht die Wahrheit auf keinem der beiden Systeme unerreichbar** — auch nicht auf System
11, wo er mit Stage 4 genau auf dem Term liegt, den die Wahrheit braucht.

| Zelle | v2.2 | v2.2 + Cap | v2.2 Overshoot / wasted |
|---|---|---|---|
| 3/42 | `2.663641831768419e-10` | `1.3476451847014113e-08` | 1 / 2 |
| 3/123 | `6.52992601045936e-10` | bitgleich | 0 / 0 |
| 3/7 | `1.1091164010682478e-08` | bitgleich | **3 / 12** |
| 11/42 | `4.402192340718147e-15` | bitgleich | 0 / 0 |
| 11/123 | `4.375215202011892e-15` | bitgleich | 0 / 0 |
| 11/7 | `4.40607367978419e-15` | bitgleich | 0 / 0 |

**3/7 ist die staerkste Einzelzelle im ganzen Datensatz:** v2.2 laeuft dort bis Stage 5 und
verbrennt **12 von 30 Levels**, der gecappte Lauf bei Stage 2 liefert denselben Loss bitgleich.
Zwoelf Levels, nachweislich null Beitrag.

**3/42 ist der Ausreisser und wird nicht weggeredet.** Der gecappte Lauf ist um **Faktor 50**
schlechter (1.348e-8 gegen 2.664e-10) — bei *identischem* Support und `pruned_match = true` in
beiden Armen. Die Struktur ist also in beiden Faellen die richtige; verloren geht nur ein besseres
Parameteroptimum, das v2.2 in dem einen zusaetzlichen Stage-3-Level gefunden hat. Dasselbe Muster
wie auf 31/123: **Optimiererpfad-Abhaengigkeit, nicht eine vom Cap unerreichbar gemachte
Wahrheit.** Ueber alle bisherigen zehn v2.2+Cap-Zellen: acht bitgleich, eine auf elf Stellen
gleich, eine um 50x schlechter — und `pruned_match` in *allen zehn* unveraendert gegenueber v2.2.
Der Cap aendert die Strukturfindung nirgends, nur gelegentlich das Parameteroptimum, in beide
Richtungen.

Nebenbefund: `total_parameter_fits` ist innerhalb eines Systems ueber alle drei Seeds identisch
(170 auf System 3, 270 auf System 11). Der Cap macht das Suchbudget seed-unabhaengig, weil er die
Levelzahl festlegt.

**Provenienz-Defekt, selbst verursacht:** fuenf der sechs Records tragen `git_dirty = true`.
Ursache ist mein eigenes Runner-Design — die per-Zelle-Dateien `history_nh_*.jsonl` liegen im Repo
und sind untracked, und `git_dirty` wird aus `git status --porcelain` abgeleitet, das untracked
Dateien mitzaehlt. Der getrackte Quellstand war ueber alle sechs Laeufe identisch (`63d4c1c`, keine
Quelldatei angefasst). Das Flag meldet hier also die Ausgabedateien, nicht eine Codeaenderung.
Fuer kuenftige Laeufe: per-Zelle-Dateien ausserhalb des Repos ablegen oder ignorieren.

---

### WP-C1 Entscheidungszellen — v2.2 + Cap ist die Endvariante

<!-- 8f362c1 -->

Vier Zellen mit `evogrow_v2_2_stage_capped` gelaufen (26/42, 31/42, 31/123, 31/7), Fingerprint
`df5db7763bcd2449`, `git_hash 838b7af`, `git_dirty false`,
`total_optimizer_safety_limit_hits = 0` in allen vieren. In `history.jsonl` gemergt (32 → 36
Records), Einzeldateien entfernt.

Vorab festgelegtes Kriterium: `eq_overshoot` faellt auf `[0,0]` **und** der Loss bleibt auf
v2.2-Niveau. Beides erfuellt — und zwar in der schaerfstmoeglichen Form.

| Zelle | v2.2 | v2.2 + Cap | identisch |
|---|---|---|---|
| 26/42 | `0.001391623174905009` | `0.001391623174905009` | bitgleich |
| 31/123 | `0.00010427173348124156` | `0.00010427173348124156` | bitgleich |
| 31/42 | `6.80769890488305e-11` | `6.80769890488305e-11` | bitgleich |
| 31/7 | `6.974887728097135e-05` | `6.974887728171775e-05` | 11 Stellen |

Alle vier: `eq_final_stages = [3,3]`, `eq_overshoot = [0,0]`, `eq_wasted_levels = [0,0]`,
`stage_caps = [3,3]`, `stage_cap_policy_active = true`.

**Der entscheidende Punkt liegt nicht in der Uebereinstimmung, sondern darin, wo sie auftritt.**
31/42 ist trivial: v2.2 blieb dort schon von selbst in Stage 3 (`wasted_levels = 0`), der Cap
konnte nichts aendern. In den anderen drei Zellen lief v2.2 bis Stage 5 und verbrannte je **8 von
30 Levels** in den Stages 4 und 5 — und der gecappte Lauf liefert trotzdem denselben Loss auf 11
bis 16 Stellen. Diese acht Levels haben also nachweislich **exakt nichts** zum Ergebnis
beigetragen. Overshoot ist auf diesen Systemen reine Verschwendung, nicht ein Suchpfad, der
zufaellig nicht zahlt.

Zur Einordnung gegen die beiden v3-Arme, dieselben Zellen:

| Zelle | v2.2 | v3 | v3 + Cap | v2.2 + Cap |
|---|---|---|---|---|
| 26/42 | 1.392e-3 | 2.520e-4 (530 Fits) | 2.520e-4 (390) | 1.392e-3 (430) |
| 31/42 | 6.808e-11 | 1.285e-4 (490) | 1.678e-2 (250) | 6.808e-11 (310) |
| 31/123 | 1.043e-4 | 2.994e-5 (430) | 5.284e-3 (230) | 1.043e-4 (290) |
| 31/7 | 6.975e-5 | 9.872e-5 (390) | 9.872e-5 (230) | 6.975e-5 (330) |

Damit ist die Attribution vom 2026-08-02 endgueltig geschlossen: der Loss-Einbruch auf System 31
gehoert **dem v3-Substrat**, nicht dem Cap. Auf demselben Cap, aber v2.2 als Unterbau, kommt
6.808e-11 zurueck — genau der Wert, den v3+Cap um acht Groessenordnungen verfehlte. Der Cap ist
unschuldig; das kontaminierte `r_k`-Promotionssignal war das Problem.

Nicht belegbar aus diesen Daten: die Kostenersparnis gegenueber v2.2. Die v2.2-Records stammen aus
Baseline v0 und fuehren weder `total_parameter_fits` noch `total_ode_solves`. Belegt ist nur die
strukturelle Groesse: 8 von 30 Levels entfallen. Laufzeiten sind erfasst, aber nach Designprinzip 7
kein Beleg.

**Fingerprint-Grenze:** der v2.2-Arm liegt auf `0c739d4e36ee6498`, die gecappten Zellen auf
`df5db7763bcd2449`. Der Vergleich kreuzt die Grenze und muss ueberall so gekennzeichnet werden.
Die bitgleichen Losses sind allerdings selbst das staerkste Indiz, dass die Grenze inert ist — was
WP-T2 unabhaengig gezeigt hatte.

**Was nicht geloest ist:** `pruned_match = false` in allen vier Zellen. Auf 26/42 findet der
gecappte Lauf `du2 = f(u1, u1^2)` — dieselbe falsche Struktur wie v2.2, obwohl die Wahrheit
(`u2, u1*u2, u2^2`) in Stage 3 vollstaendig verfuegbar ist. Der Cap loest die
Komplexitaetsallokation, nicht die Suchmaechtigkeit innerhalb einer Stage. Das ist die bekannte,
explizit ausserhalb von Paper 1 liegende offene Frage.

**Konsequenz:** Endvariante fuer Paper 1 ist `evogrow_v2_2_stage_capped`. v3 wird zur
dokumentierten Fehleranalyse (Gate 2 negativ, Ursache in `r_k` diagnostiziert), der Look-Ahead-Cap
zum Beitrag.

---

## 2026-08-02

### WP-C1b — eine Kindgenerierung, cap-bewusste Kohaerenzregel

<!-- 10b717d -->

Duplikat entfernt, `stage_cap_policy` korrekt typisiert (Include-Reihenfolge in `EvoODE.jl`
angepasst), Report an Daten gebunden. Befunde 1 und 3 erledigt.

**Bei Befund 2 hat Codex bewusst von meiner Vorgabe abgewichen — und die Abweichung ist besser.**
Ich hatte spezifiziert: Kohaerenzregel raus, in beiden gecappten Varianten. Umgesetzt wurde
stattdessen eine **cap-bewusste** Regel: eine Variable, deren *Cap* sie dauerhaft unter die
Term-Stage druckt, blockiert den Kopplungsterm nicht mehr; eine, die die Stage bloss noch nicht
*erreicht* hat, weiterhin schon. Das ist genau die Unterscheidung, aus der ich meine Entscheidung
begruendet hatte — nur pro Variable statt pauschal pro Variante.

Die Inertness-Tabelle im Codex-Report prueft nur die fuenf Regressionssysteme, die alle uniforme
Caps haben und wo die Regel ohnehin wirkungslos ist. Der interessante Fall blieb dort ungetestet;
selbst nachgeholt:

| Konfiguration | coherence=true | coherence=false |
|---|---|---|
| Caps `[nothing,2,2]`, eq_stages `[3,2,2]` (v2.2-Form) | `u1*u2, u1*u3, u2*u3` verfuegbar | identisch |
| eq_stages `[3,2,2]` ohne Caps (v3-Promotionsform) | alle Kopplungsterme blockiert | verfuegbar |

Das Flag ist in der v2.2-gecappten Variante also **wirkungslos** — die cap-bewusste Ausnahme
erledigt die Arbeit bereits, das `coupling_coherence = false` in `evogrow.jl` ist redundant. In v3
wirkt es und erhaelt die Regel dort, wo sie motiviert war. Sweep ueber vier Cap-Vektoren x fuenf
Stages: kein Unterschied in der v2.2-Form. (Die boolesche Sammelvariable im Pruefskript stand wegen
Julias Soft-Scope-Regel im falschen Scope; der Beleg ist das Ausbleiben der Differenzmeldungen,
nicht ihr Rueckgabewert.)

Konsequenz fuer den Vergleich: beide gecappten Arme haben identische Verfuegbarkeitssemantik,
soweit die Stage-Unterschiede aus Caps stammen. Sie unterscheiden sich nur noch dort, wo v3s
*Promotion* die Unterschiede erzeugt — das ist die experimentelle Variable selbst, kein Confounder.

Offener Stolperstein fuer spaeter: das asymmetrische Literal (`false` in `evogrow.jl`, `true` in
`evogrow_v3.jl`) ist heute harmlos, wuerde aber tragend, sobald v2.2 eine andere Quelle
nicht-uniformer Stages als den Cap bekaeme.

### WP-P3.1 — Klassifikation aller 63 Systeme, geprueft

<!-- fab01fe -->

**20 exakt, 43 Surrogat.** Alle zehn handgepflegten Klassifikationen werden vom symbolischen
Klassifikator reproduziert — keine Abweichung, also weder Parser- noch Handeintragsfehler.

Unabhaengig nachgeprueft an Systemen ausserhalb der zehn (6, 12, 25, 55, 61 stimmen). Der
aussagekraeftigste Fall ist System 8: `0.14*x0*(1 - 0.0077*x0)*(0.227*x0 - 1)` wird korrekt zu
`u1|u1²|u1³` ausmultipliziert und als Stage 4 eingestuft. Das geht nur symbolisch, nicht per
String-Matching — der Klassifikator tut wirklich, was er soll.

Stage-Verteilung der 20 exakten Systeme: Stage 1 → 3, Stage 2 → 3, Stage 3 → 9, Stage 4 → 4,
Stage 5 → 1. Die Spalte `expected_eq_stage` liefert nebenbei die **per-Gleichung-Wahrheit fuer alle
117 Gleichungen** — genau das, was die Safety-Bewertung des Stage-Caps als Referenz braucht und
bisher nur fuer eine Handvoll Systeme offline vorlag.

**Befund, der im Codex-Report fehlt und Konsequenzen hat:** 10 der 43 Surrogat-Systeme sind es
*ausschliesslich* wegen eines konstanten Offsets (IDs 1, 5, 9, 17, 23, 43, 52, 57, 58, 59). Ein
Konstanten-Term in der Basis — die einfachste denkbare Erweiterung — wuerde sie exakt machen und
die Auswertungsmenge von 20 auf 30 Systeme heben, also um 50 %. Gratis ist das nicht: eine
Basisaenderung wechselt den Fingerprint und entwertet alle bestehenden Ergebnisse. Aber die Zahl
begrenzt direkt, worueber Paper 1 exakte Wiederfindung berichten kann, und muss deshalb in der
Scope-Diskussion stehen.

### WP-C1 — Stage-Cap auf dem v2.2-Substrat, verifiziert

<!-- d3fce98 -->

Neue Variante `evogrow_v2_2_stage_capped`: der Look-Ahead-Cap wirkt als Term-Restriktion pro
Gleichung, die Stage-Progression bleibt die globale stage-lokale Plateau-Regel von v2.2. Das
`r_k`-Signal kommt nicht vor — es ist genau das, was hier entfernt wird.

Motivation aus den System-31-Zellen: der Cap braucht v3 nicht. `estimate_stage_caps` liest nur
Trajektorie und Basis, die Caps sind ein vor der Suche berechneter Vektor. Die Kopplung an v3
bestand nur, weil der Cap in dessen Promotionspfad verdrahtet worden war.

Verifikation (von mir gefahren, nachdem der Codex-Lauf ins Timeout lief):

| Pruefung | Ergebnis |
|---|---|
| `config_fingerprint()` | `df5db7763bcd2449`, unveraendert |
| Cap deaktiviert, Sys 11/42 | Loss bit-identisch `4.402192340718147e-15`, Stage 4, Support `{u1, u1², u1³}`, `pruned_match=true` — identisch zu `evogrow_v2_2_stage_local` |
| Cap aktiv, Sys 3/42 | Cap `[2]`, Stage 2, Overshoot 0, Loss `1.3476e-8`, Support `{u1, u1²}`, `pruned_match=true` |
| Caps | 3→`[2]`, 11→`[4]`, 26→`[3,3]`, 31→`[3,3]`, 63→alles `nothing` — deckungsgleich mit WP-L5d |

Die Bit-Identitaet bei deaktiviertem Cap ist **strukturell** garantiert, nicht nur empirisch: ohne
Caps sind die `eq_stages` immer uniform, damit wird immer der alte Pfad genommen. Die
`elapsed_s`-Werte der beiden Aequivalenzlaeufe unterscheiden sich (JIT-Warmup) und sind ohnehin
keine belastbare Groesse — siehe die Notiz zu Wall-Clock weiter unten.

**Fingerprint-Falle, die vorab entschaerft wurde:** `FINGERPRINT_VARIANT_LABELS` geht in den Hash
ein. Ein Eintrag der neuen Variante haette `df5db7763bcd2449` gewechselt und alle 32
History-Records unvergleichbar gemacht — also genau das zerstoert, wofuer die Laeufe da sind. Da
Laeufe unabhaengig sind, ist das Weglassen sachlich korrekt. Der Payload nennt jetzt nur
`evogrow_v3_stage_capped` und ist damit unvollstaendig; das bleibt bewusst so stehen.

### WP-C1b beauftragt — drei Reviewbefunde

<!-- bb61b3a -->

1. **Duplikation.** `_expand_with_stage_caps` ist eine fast wortgleiche Kopie von
   `_expand_equation_aware_with_usage_policy`, `_equation_capped_terms` eine von
   `_evogrow_v3_equation_terms`. Zwei Kopien der Kindgenerierungs-Weiche, benutzt von genau den
   beiden Varianten, die gegeneinander gestellt werden.
2. **Stille Semantikaenderung bei Kopplungstermen.** Der Originalpfad filtert ueber
   `_evogrow_v3_term_available`, das eine Zusatzregel enthaelt: ein Term mit mehreren Variablen ist
   fuer Gleichung `k` nur verfuegbar, wenn *alle* referenzierten Variablen die Stage erreicht haben.
   Die Kopie laesst die Klausel weg.

   Entscheidung: **Kohaerenzregel raus, fuer cap-abgeleitete Grenzen, in beiden Varianten.** Sie
   wurde fuer v3 geschrieben, wo `eq_stages` den *Fortschritt* abbildet und eine niedrige Stage
   voruebergehend ist. Ein Cap ist eine *permanente, aus den Daten abgeleitete Obergrenze*. Ist
   Gleichung 2 dauerhaft auf 2 gedeckelt, wird `u1*u2` fuer Gleichung 1 nie verfuegbar, auch wenn
   deren Cap 3 ist — der Cap wird fuer alle Kopplungsterme zur globalen Schranke und die Wahrheit
   unerreichbar. Derselbe Fehlermodus wie WP-L4 auf System 63, und dasselbe Prinzip: eine
   Restriktion muss auf positiver Evidenz ueber die Gleichung beruhen, die sie einschraenkt.

   **Die vier bereits gefahrenen gecappten Zellen sind faktisch nicht betroffen**, weil alle Caps
   der fuenf Regressionssysteme uniform sind und die Klausel bei uniformen Stages wirkungslos ist.
   Das ist Glueck, nicht Absicht — auf System 54 (`[nothing,2,2]`) haette es gebissen. WP-C1b muss
   die Wirkungslosigkeit zeigen statt sie zu behaupten.
3. **Report mit fest verdrahteter Ergebnisprosa.** `verify_wp_c1.jl` schreibt „No parser or
   cap-estimator disagreement surfaced" als Stringliteral, unabhaengig vom Laufergebnis. Ein
   Verifikationsbericht darf keine Aussage enthalten, die nicht falsch werden kann.

Nebenbefund: `stage_cap_policy::Any` ist untypisiert, weil `stage_cap.jl` in `EvoODE.jl` nach
`evogrow.jl` inkludiert wird. Kosmetisch, in WP-C1b als risikoarme Zugabe.

### v3 uncapped auf System 31 — Cap-Effekt und v3-Effekt sind jetzt getrennt

<!-- b6fe895 -->

Drei Laeufe (31, Seeds 42/123/7, `evogrow_v3`, Fingerprint `df5db7763bcd2449`, `git_hash c6692a5`,
`git_dirty=false`, `total_optimizer_safety_limit_hits = 0`). Damit existiert erstmals ein
v3-Referenzarm auf System 31, und die offene Zuordnungsfrage aus den Bestaetigungszellen ist
beantwortet.

| Seed | v2.2 | v3 | v3 + Cap | Fits v3 → Cap |
|---|---|---|---|---|
| 42 | 6,808e-11 | 1,285e-4 | 1,678e-2 | 490 → 250 |
| 123 | 1,043e-4 | 2,994e-5 | 5,284e-3 | 430 → 230 |
| 7 | 6,975e-5 | 9,872e-5 | **9,872e-5** | 390 → 230 |

Wall-Clock ist hier bewusst **nicht** aufgefuehrt. Die Laeufe liefen auf dem Laptop des Nutzers,
wo jederzeit Parallelarbeit, Suspend oder Throttling dazwischenkommen koennen, ohne Spur in den
Daten. Kostenaussagen stuetzen sich ausschliesslich auf Zaehlgroessen.

**Die Zuordnung:** Auf Seed 42 verliert v3 gegenueber v2.2 rund **sechs Groessenordnungen**
(6,8e-11 → 1,3e-4), der Cap legt danach zwei drauf. Der dominante Anteil des Einbruchs sitzt also im
v3-Substrat, nicht im Cap. Das bestaetigt die Vermutung, die sich aus der Nicht-Bindung des Caps auf
dieser Zelle ergab, und zeigt auf das `r_k`-Promotionssignal, dessen Ableitungskontamination WP-L2
gemessen hat.

**Zwei Befunde, die mehr wert sind als die Tabelle:**

1. **Seed 7 ist bit-identisch.** Gleicher Loss, gleicher Support in beiden Gleichungen
   (`du1 = {u2, u1², u1·u2}`, `du2 = {u1, u2, u1²}`). Der Cap aendert das Ergebnis nicht und spart
   160 Fits und rund 34 000 Sekunden. Die Nulltarif-Beobachtung von System 26 repliziert hier.
2. **Seed 123 hat in beiden Armen identischen Support** (`du1 = {u1, u2, u1·u2}`,
   `du2 = {u1, u2, u1², u2²}`) und trotzdem 176-fachen Loss-Unterschied. Gleiche Struktur, andere
   Parameter — das ist Pfadabhaengigkeit im Optimierer, **nicht** eine vom Cap unerreichbar gemachte
   Struktur. Damit ist die naheliegende Sorge, der Cap schneide die Wahrheit ab, fuer diese Zelle
   ausgeraeumt.

Bleibt Seed 42, wo dem gecappten `du2` der Kopplungsterm `u1·u2` fehlt — der auf Stage 3 durchgehend
verfuegbar war. Dasselbe Muster wie auf System 26: nicht der Cap verhindert die Struktur, die Suche
findet sie innerhalb der Stage nicht. Das ist Suchkraft *innerhalb* einer Stage und liegt
ausdruecklich ausserhalb von Paper 1.

**Overshoot-Eliminierung repliziert 3/3** (`eq_overshoot [2,2] → [0,0]`, `eq_wasted_levels`
[12,12]/[7,7]/[7,7] → [0,0]) bei 41–51 % weniger Fits.
`pruned_match = false` in **allen neun** Zellen, auch bei v2.2 mit 6,8e-11 — auf System 31 gelingt
keinem Arm die exakte Wiederfindung.

Fingerprint-Grenze bleibt bestehen und muss beschriftet werden: der v2.2-Arm liegt auf
`0c739d4e36ee6498`, v3 und gecappt auf `df5db7763bcd2449`.

**Nebenbefund beim Mergen der History** (29 → 32 Zeilen): das vermeintliche Duplikat
`(evogrow_v3, 26, 42)` ist keines. Es sind zwei gueltige Laengsschnitteintraege — `0c739d4e` vom
2026-07-22 mit Loss 1,392e-3 (die v3.2-Lockstep-Bridge, per Konstruktion bit-identisch zu v2.2, was
der Wert exakt bestaetigt) und `1f9c5f80` vom 2026-07-30 mit 2,520e-4 (der divergente v3 aus dem
Gate-2-Lauf). Der Uniqueness-Key der History ist `(variant, system_id, seed, config_fingerprint)`,
nicht das Tripel.

### Phase 3 begonnen — Protokoll-Audit deckt eine Gitter-Fehlausrichtung auf

`docs/paper1_odebench_protocol_alignment.md` angelegt. Die EvoODE-Seite ist gegen den Datensatz
verifiziert, die Spalten der publizierten Quellen sind ausdruecklich als **ungeprueft** markiert —
ohne die Papers waere jede Eintragung dort erfunden.

**Verifiziert und unproblematisch:** alle zehn `u0` aus der `BENCHMARKS`-Tabelle reproduzieren exakt
den *ersten* Anfangsbedingungssatz des Datensatzes. Der Datensatz liefert allerdings **zwei** Saetze
pro System, wir nutzen nur einen — publizierte Zahlen ueber beide decken also eine groessere
Auswertungsmenge ab.

**Verifiziert und problematisch: das Zeitgitter passt bei keinem einzigen System.** Der Datensatz
liefert durchgaengig **512 Punkte ueber t ∈ [0, 10]**; EvoODE nutzt pro System eigene `tspan`/`T`
zwischen 10 und 20 Punkten pro Zeiteinheit, also **2,6- bis 5,1-fach duenner**, und teils deutlich
laengere Horizonte (System 63 bis t = 30 gegen t = 10). System 26 trifft immerhin die Zeitspanne,
aber nicht die Abtastung.

**Querverbindung, die das interessant macht:** WP-L3 hat gemessen, dass die Stage-3-Klippe auf
System 54 bei unserer Dichte nicht aufloesbar ist und ab etwa doppelter Dichte erscheint. Das
Datensatz-Gitter ist dort **2,56-fach dichter** (51,2 gegen 20 Punkte pro Zeiteinheit). Der Wechsel
auf das Datensatz-Gitter wuerde also plausibel eine der beiden verbliebenen Cap-Verletzungen
beseitigen. Vorhersage aus gemessenem Verhalten, nicht Ergebnis — ungelaufen.

Daraus die Entscheidung, die **vor** der Phase-B-Generierung faellt, weil sie die Trajektorien und
damit alles Nachgelagerte bestimmt: Datensatz-Gitter uebernehmen (Vergleichbarkeit plausibel,
doppelte Laufzahl durch zwei IC-Saetze, kein bestehendes Ergebnis traegt ueber, Baseline neu) oder
beim eigenen Gitter bleiben (bestehende Ergebnisse gelten, publizierte Zahlen bleiben rein
kontextuell und das muss im Paper konsistent so stehen). Die Systemklassifikation (WP-P3.1) ist
gitterunabhaengig und kann davor laufen.

### WP-P3.1 beauftragt — Klassifikation aller 63 Systeme

Python, im Analyse-Pipeline-Teil, `sympy` als neue Abhaengigkeit. Grundlage ist das Feld
`substituted` im Datensatz (Gleichungen mit eingesetzten Konstanten). Der Umfang laut Vorab-Scan:
63 Systeme, 117 Gleichungen, Dimensionen 1/2/3/4 mit 23/28/10/2. Operatoren: `**` 42×, `sin` 16,
`cos` 8, `exp` 6, `log`, `cot`, `Abs` je einmal — dazu additive Konstanten, fuer die die Basis
ueberhaupt keinen Term hat. Das ist symbolische Ausdrucksanalyse, kein String-Matching.

Pflichtbestandteil der Spec ist die **Validierung gegen die zehn handgepflegten Systeme** aus
`benchmark_evogrow.jl`, mit der ausdruecklichen Auflage, jede Abweichung als Befund zu behandeln und
den Parser nicht auf Uebereinstimmung zu tunen: eine Abweichung hiesse entweder Parser falsch oder
ein handgepflegter Wert falsch, auf dem saemtliche bisherigen Ergebnisse beruhen.

Der Grund, warum die Zahl selbst zaehlt und nicht nur die CSV: die Menge der exakten Systeme
bestimmt, auf wie vielen Systemen Paper 1 ueberhaupt strukturelle Wiederfindung berichten kann.
Faellt sie klein aus, aendert das, was das Paper behaupten kann.

### Bestaetigungszellen — Overshoot repliziert, aber „zum Nulltarif" haelt nicht

Vier gecappte Zellen parallel gefahren (26/123, 31/42, 31/123, 31/7), History gemerged (25 → 29).
Technisch sauber: richtige Zellen, kein Env-Leck, `error = nothing`, `git_dirty = false`, Fingerprint
`df5db7763bcd2449`, und — entscheidend fuer die Parallelitaet — `total_optimizer_safety_limit_hits = 0`
in allen vier. **Das 1800-s-Zeitlimit hat nie gefeuert, die Parallelitaet hat die Ergebnisse nicht
kontaminiert.** Die 40–68 `optimizer_limit_hits` sind ausnahmslos BFGS-Konvergenzfehler, das bekannte
Verhalten aus WP-P2.2c.

| Zelle | Variante | Loss | Stage | Over | Wasted |
|---|---|---|---|---|---|
| 26/42 | v2.2 | 1,392e-3 | 5 | 2 | 8 |
| | gecappt | **2,520e-4** | 3 | 0 | 0 |
| 26/123 | v2.2 | 1,392e-3 | 5 | 2 | 8 |
| | gecappt | 1,392e-3 | 3 | 0 | 0 |
| 31/42 | v2.2 | **6,808e-11** | 3 | 0 | 0 |
| | gecappt | **1,678e-2** | 3 | 0 | 0 |
| 31/123 | v2.2 | 1,043e-4 | 5 | 2 | 8 |
| | gecappt | 5,284e-3 | 3 | 0 | 0 |
| 31/7 | v2.2 | 6,975e-5 | 5 | 2 | 8 |
| | gecappt | 9,872e-5 | 3 | 0 | 0 |

**Was haelt: die Overshoot-Eliminierung repliziert.** Alle vier neuen Zellen `eq_overshoot = [0,0]`,
`eq_wasted_levels = [0,0]`, waehrend v2.2 in vier von fuenf Zellen Overshoot 2 und 8 verschwendete
Level hatte.

**Was nicht haelt: „zum Nulltarif".** Meine Formulierung nach der Einzelzelle war zu stark. Auf
System 26 kostet der Cap nichts (26/42 bit-identisch zu v3, 26/123 gleichauf mit v2.2). Auf System 31
kostet er erheblich: 31/123 ist 50-fach schlechter als v2.2, 31/7 leicht schlechter — und **31/42 ist
um acht Groessenordnungen schlechter** (1,7e-2 gegen 6,8e-11). Der Befund „die spaeten Stufen tragen
nichts bei" gilt fuer System 26, nicht allgemein: auf System 31 senken die Stufen 4/5 den Loss real,
wenn auch mit strukturell falschen Termen. Der Cap tauscht also Fitqualitaet gegen
Komplexitaetsdisziplin, und ob dieser Tausch gratis ist, haengt am System.

**Der Vergleich ist zudem konfundiert, und das ist der wichtigere methodische Punkt.** Die gecappte
Variante ist `EvoGrowV3` **plus** Cap. Fuer System 31 existiert kein v3-Record (v3 liegt nur fuer 3,
11 und 26 vor), also laesst sich Cap-Effekt und v3-Effekt dort nicht trennen.

Eine Zelle erlaubt die Trennung aber schon jetzt: **auf 31/42 ist der Cap nicht bindend** — v2.2
endete dort von selbst auf Stage 3, ein Cap bei 3 kann also nichts verhindert haben. Trotzdem liegt
der Loss acht Groessenordnungen hoeher. **Der Einbruch auf dieser Zelle kann folglich nicht vom Cap
kommen, sondern muss aus dem v3-Unterbau stammen** (Pro-Gleichungs-Promotion ueber `r_k` statt
globalem Plateau) — genau das Signal, das WP-L2 als ableitungsfehler-kontaminiert nachgewiesen hat.

Konsequenz: bevor daraus ein Paper-Claim wird, braucht es **v3 ungecappt auf System 31, Seeds
42/123/7** — drei Laeufe, die Cap-Effekt und v3-Effekt sauber trennen. Ohne das ist die Aussage
„der Cap kostet Fitqualitaet" nicht belegbar; sie koennte vollstaendig ein v3-Effekt sein.

Nebenbefund: `pruned_match` ist in **allen** Zellen false, auch bei v2.2 mit Loss 6,8e-11 auf 31/42 —
das ist der aus Phase 1 bekannte Fall „nahezu perfekter Fit, aber ein Fremdterm ueberlebt die
Pruning-Schwelle".

## 2026-08-01

### Scope-Entscheidung getroffen — Zweig 1, angereichert

Nach dem Ergebnis der Entscheidungszelle: die finale Paper-1-Variante traegt den Look-Ahead-Cap, das
Paper wird die mechanistische Claim-C-Studie, und die Kette v2.2 → v3 → gecappt wird als
dokumentierte Failure-Analyse mit quantifiziertem Positivergebnis zur Komplexitaetsallokation
gefuehrt. Zweig 2 (Paper um den Look-Ahead herum neu bauen) faellt weg, weil der Mechanismus genau
das Versagen *nicht* behebt, das Phase 2 ausgeloest hat. Die Frage nach der Suchkraft innerhalb einer
Stufe bleibt ausdruecklich ausserhalb von Paper 1.

**Planungsfund, der eine frueher von mir genannte Empfehlung korrigiert.** Ich hatte „Bestaetigung
auf 31 und 63" vorgeschlagen. Auf **System 63 feuert der Cap gar nicht** — alle vier Gleichungen sind
`nothing`, die gecappte Variante ist dort identisch zu v3, die Zelle koennte den Overshoot-Effekt
also gar nicht zeigen. 63 gehoert als Identifizierbarkeitsgrenze ins Paper, nicht in die
Bestaetigung. Ebenfalls geprueft: der v2.2-Vergleichsarm liegt fuer 3, 11, 26, 31 und 63 bei je drei
Seeds (42/123/7) bereits vor, es ist also nur der gecappte Arm zu fahren. Zu labeln ist dabei, dass
der Vergleich eine Fingerprint-Grenze kreuzt (v2.2 unter Baseline v0 `0c739d4e36ee6498`, neue Laeufe
unter `df5db7763bcd2449`); WP-T2 hat gezeigt, dass die zwischenzeitliche Konfigurationsaenderung die
Ergebnisse nicht bewegt, aber das gehoert benannt.

### Entscheidungszelle gelaufen — Stage-Eskalation war ein Symptom, nicht die Ursache

Der gecappte 26/42-Lauf ist durch (`evogrow_v3_stage_capped`, Fingerprint `3f9be6d36c4043de`,
`git_hash d896d77`, 21.159 s). Readout in `outputs/studies/gate2_do_or_die/`.

| | v2.2-Anker | v3 Gate 2 | **gecappt** |
|---|---|---|---|
| Loss | 1,391623174905009e-3 | 2,5195575964774715e-4 | **2,5195575964774715e-4** |
| `eq_final_stages` | 5 | [5, 5] | **[3, 3]** |
| `eq_overshoot` | 2 | [2, 2] | **[0, 0]** |
| `eq_wasted_levels` | 8 | — | **[0, 0]** |
| du1-Support | {u1, u1², u1·u2} | — | {u1, **u2**, u1², u1·u2} |
| du2-Support | {u1, u1²} | — | **{u1, u1²}** |

**Zwei Befunde, und sie zeigen in entgegengesetzte Richtungen.**

**1. Die Komplexitaetsallokation ist geloest, und zwar zum Nulltarif.** Overshoot 2 → 0, verschwendete
Level 8 → 0 — und der Loss ist **bit-identisch** zum ungecappten v3-Lauf, bis zur letzten Stelle.
Das heisst: die Stufen 4 und 5 haben im v3-Lauf zum Ergebnis buchstaeblich nichts beigetragen. Die
Eskalation war reine Verschwendung, und der Cap entfernt sie ohne jeden Preis an Fitqualitaet.
Parameter-Fits 390 gegen 530 bei v3, also 26 % weniger. Damit ist der Look-Ahead als Mechanismus
belegt — nicht mehr als Offline-Klassifikator, sondern im Suchpfad.

**2. Die strukturelle Wiederfindung ist unveraendert — nicht einmal bewegt.** `du2` ist
`{u1, u1²}`, also **exakt dasselbe, was v2.2 gefunden hat**; der Readout weist es explizit aus
(`du2_support_changed_from_anchor: false`). Die Wahrheit `2·u2 − u1·u2 − u2²` lag die ganze Zeit
vollstaendig auf Stage 3 und damit innerhalb des Caps bereit. `du1` behaelt zusaetzlich den
Fremdterm `u2`.

**Damit ist die Frage beantwortet, die seit WP-T2 offen war: die Stage-Eskalation war ein Symptom,
nicht die Ursache.** Die Suche auf die richtige Stufe zu zwingen, verbessert die Entdeckung nicht um
einen einzigen Term. Der Engpass liegt in der Suchkraft *innerhalb* einer Stufe — Populationsgroesse,
Kindergenerierung, Parsimonie-Druck —, und das ist eine andere Baustelle als alles seit Gate 1.

Das Readout-Verdikt lautet `REPORTABLE`. Das ist eine faire Bezeichnung, darf aber nicht verdecken,
dass das strukturelle Kriterium verfehlt ist: unter den urspruenglichen Do-or-Die-Kriterien waere
(a) nur eine Konstruktionspruefung, (b) verfehlt und (c) erfuellt.

**Messvorbehalt, und der geht auf mich.** `elapsed_s` ist mit 21.159 s hoeher als die 13.047 s des
v3-Laufs, obwohl weniger Fits anfielen. Die Wall-Clock ist kontaminiert: ich habe waehrend des Laufs
dreimal eigene Julia-Verifikationsjobs gestartet, die Pakete laden und rechnen. Tragend sind wie im
ganzen Projekt die Zaehlungen — 390 Fits, 1.977.546 ODE-Solves —, nicht die Zeiten.

### WP-L5d geliefert — Cap-Spur abgeschlossen

Bericht in `docs/wp_l5d_stage_cap_closeout.md`. Acceptance gruen, Suite 2 Verletzungen (die bekannten
54 du2/du3), 8 von 16 Gleichungen gecappt, 18 Stufen gespart.

**Die Fingerprint-Falle wurde korrekt behandelt.** Neuer Fingerprint `df5db7763bcd2449` mit
`aggregation` und `lookahead_horizon`; das Readout waehlt den Record aber ueber
Variante/System/Seed statt ueber den neu berechneten Fingerprint und wurde gegen die vorhandene
History geprueft (2 v3-Records korrekt *nicht* gematcht). Genau deshalb hat es den Lauf-Record mit
dem alten Fingerprint gefunden — die Auswertung waere sonst stillschweigend leer geblieben.

Sensitivitaet belegt beide Defaults: Horizont 1 liefert 4 Verletzungen statt 2 (der
System-31-Fall), `any_positive` bei Horizont 1 sogar 5; Horizont 2 und 3 sind identisch. Der
System-31-Vorbehalt (Ursache unbelegt, Diagnose lief ins Timeout) ist im Bericht festgehalten.

<!-- 27ecb09, 3ddc7f4 -->

### WP-L5d beauftragt — Provenienz, Tests, Sensitivitaet, Bericht

Abschluss der Cap-Spur; **keine Regelaenderung im Scope** — die Regel ist verifiziert, eine stille
Aenderung wuerde das entwerten. Findet ein Test einen echten Defekt, ist zu berichten statt zu
reparieren.

Wichtigster Punkt ist der Fingerprint: `aggregation` und `lookahead_horizon` fehlen im
gefingerprinteten Cap-Tupel, drei Semantikaenderungen sind bereits ohne Bewegung von
`3f9be6d36c4043de` durchgelaufen.

**Dabei eine Falle, die mir beim Schreiben aufgefallen ist und die teuer waere.** Der laufende
26/42-Lauf hat seinen Fingerprint beim Prozessstart berechnet und schreibt seinen Record mit dem
alten Wert — richtig so. Aber `studies/gate2_do_or_die/readout.jl` laeuft danach aus aktualisiertem
Code. Sucht es den Record ueber den *neu berechneten* Fingerprint, findet es ein vorhandenes
Ergebnis nicht und meldet stillschweigend nichts. Die Spec verlangt, die Record-Auswahl des Readouts
zu pruefen und gegen die vorhandenen History-Records zu verifizieren, nicht nur den Code zu lesen.

Ausserdem zu dokumentieren: die zwei System-54-Verletzungen ausdruecklich als bekannte
Aufloesungsgrenze mit dem WP-L3-Dichte-Beleg statt als offener Bug, und der Vorbehalt zum
System-31-Fix (Ursache unbelegt, Diagnose lief ins Timeout).

### WP-L5c — Acceptance gruen; die zwei Restverletzungen sind die bekannte Aufloesungsgrenze

Codex hat System 31 du1 repariert und diesmal korrekt gestoppt — belegt mit echter Ausgabe, nachdem
der Diagnosebefehl nach 552 s ins Timeout lief. Eigene Nachrechnung, jetzt inklusive System 54:

| System | Wahrheit pro Gleichung | Cap | |
|---|---|---|---|
| 3 | [2] | [2] | ✓ |
| 11 | [4] | [4] | ✓ |
| 26 | [3, 3] | [3, 3] | ✓ Vergleichsbasis des laufenden 26/42 intakt |
| 31 | [3, 3] | [3, 3] | ✓ Fix wirkt |
| 63 | [3, 3, 1, 1] | [n, n, n, n] | ✓ sicher |
| 54 | [1, 3, 3] | [n, **2**, **2**] | 2 Verletzungen |

Suiteweit: 2 Verletzungen, 8 von 16 Gleichungen gecappt, 18 Stufen gespart. Die Sicherheit ist also
nicht durch Nichtstun erkauft — genau die Gegenprobe, die die Spec verlangt hatte.

**Die zwei Verletzungen sind kein neuer Defekt.** Es sind exakt die beiden Gleichungen, die WP-L3
bereits als Undershoot ausgewiesen hatte: die floor-gated Konfusion war 12 exact / 0 over / 4 under,
und diese vier waren 63 du1/du2 plus 54 du2/du3. Nachdem 63 jetzt sauber ungecappt ist, bleiben genau
die Lorenz-Gleichungen uebrig. Die Ursache ist gemessen, nicht vermutet: bei Benchmark-Sampling
faellt das Residuum auf System 54 schon bei Stage 2 unter den Rauschboden, die Stage-3-Klippe liegt
also unter der Aufloesungsgrenze der Ableitungsschaetzung; der Dichte-Sweep aus WP-L3 zeigt sie ab
doppelter Dichte. **Datengrenze, keine Regelgrenze.**

Damit hat die Cap-Regel eine geschlossene Charakterisierung: sicher, wo die Ableitungsschaetzung die
Struktur aufloest, unsicher genau dort, wo sie es nicht tut — und das ist vorab am Rauschboden
ablesbar. Es bleibt kein unerklaerter Defekt.

**Kritikpunkt zum Vorgehen:** der System-31-Fix kam ohne die geforderte Diagnose zustande, weil diese
ins Timeout lief. Er lockert den Gewinntest, wenn das Folge-Residuum bereits auf dem Boden liegt
(`tau_abs` entfaellt, `delta > floor` und die relative Schwelle bleiben). Das wirkt in die sichere
Richtung — lockerere Gewinnerkennung heisst hoehere Caps, also weniger Blockade — und das Ergebnis
ist verifiziert. Die *Ursache* bleibt aber unbelegt; das ist eine Reparatur per Schlussfolgerung,
nicht per Messung, und gehoert so vermerkt.

Weiterhin offen: Fingerprint um `aggregation` und `lookahead_horizon` ergaenzen (inzwischen sind drei
Semantikaenderungen ohne Fingerprint-Bewegung durchgelaufen), Tests, Aggregations- und
Horizont-Sensitivitaet, Bericht.

### WP-L5b — Regel weitgehend repariert; Stoppmeldung war ein Fehlalarm; eine Verletzung bleibt

Codex meldete einen Abbruch mit „System 26 ergibt nicht mehr [3,3] sondern [nothing, nothing]".
**Der Alarm war falsch.** Die Meldung war wortgleich mit der aus WP-L5, referenzierte „WP-L5" und
„Abschnitt 8" (den WP-L5b nicht hat) und beschrieb die Umstellung auf *positive evidence only* —
also die vorige Runde. Der Pflichtcheck nach der neuen Aenderung ist offenbar nicht gelaufen, die
Meldung wurde uebernommen. Eigene Nachrechnung:

| System | Wahrheit | WP-L4 | WP-L5 | **WP-L5b** |
|---|---|---|---|---|
| 3 | [2] | [2] ✓ | nothing | **[2] ✓** |
| 11 | [4] | [4] ✓ | nothing | **[4] ✓** |
| 26 | [3, 3] | [3, 3] ✓ | nothing, nothing | **[3, 3] ✓** |
| 31 | [3, 3] | [3, 3] ✓ | [1, 1] ✗ | **[1, 3]** — du1 verletzt |
| 63 | [3, 3, 1, 1] | [1, 1, 1, 1] ✗ | [1, 1, n, n] | **[n, n, n, n]** ✓ sicher |

**System 26 steht auf [3,3]** — die Vergleichsbasis des laufenden 26/42-Laufs ist unberuehrt.
Sicherheitsverletzungen: 2 (L4) → 4 (L5) → **1 (L5b)**. Die Bodensemantik-Korrektur und der
Horizont wirken beide, und zwar sichtbar: 3, 11 und 26 sind zurueck, 63 ist jetzt durchgaengig
ungecappt und damit sicher (zum Preis, dass die Mechanik dort nichts einbringt — akzeptabel und
ehrlich auszuweisen).

**Offen bleibt System 31 du1.** Cap 1 gegen wahre Stage 3. Aufschlussreich ist die Form der
Gleichung: `du1 = -0.4*u1*u2` ist die **einzige** im Satz, deren wahrer Support vollstaendig in
einer spaeteren Stufe liegt, ohne jeden Term aus Stage 1 oder 2. Genau dieser Fall — kein Gewinn auf
den Zwischenstufen, der ganze Gewinn erst spaeter — sollte der Horizont abfangen. Dass er es nicht
tut, ist die naechste konkrete Frage; ohne Instrumentierung der Split-Entscheidungen ist nicht
entscheidbar, ob der Gewinntest bei Stage 3 nicht anschlaegt oder die Aggregation die Mehrheit
verfehlt. Passend dazu ist du2 derselben Gleichung korrekt auf 3 — dort enthaelt die Wahrheit
zusaetzlich einen Stage-1-Term.

Nicht geliefert, weil Codex am Fehlalarm abgebrochen hat: Tests, suiteweite Invariante,
Aggregations-Sensitivitaet, Fingerprint-Reparatur, Bericht.

### WP-L5b beauftragt — korrigierte Bodensemantik plus Horizont

Behebt die beiden diagnostizierten Ursachen. **Bodensemantik:** nicht „Residuum unter dem Boden →
nicht beurteilbar", sondern die Unterscheidung, ob das Residuum auf dieser Stufe *auf* den Boden
gefallen ist (positive Evidenz, hier cappen) oder schon *vorher* dort lag, bevor eine Stufe geholfen
hat (keine Information, kein Cap). **Horizont:** mindestens zwei *anwendbare* Stufen, damit eine
nutzlose Zwischenstufe ueberbrueckt werden kann; leere Stufen verbrauchen keinen Horizont. Erhalten
bleibt aus WP-L5 die Dreiteilung positive/undecidable/invalid, die expliziten Aggregationsmodi und
die Auswertbarkeitsregel — nur bei auswertbarer Folgestufe darf gecappt werden, was 63 du1/du2
ungecappt haelt, weil deren Stage-3-Bibliothek rangdefizit ist.

**Prozessaenderung, aus dem WP-L5-Verlauf gelernt:** die Abnahmetabelle ueber alle fuenf Systeme ist
**zuerst** zu erzeugen, vor Tests, Bericht und Fingerprint. WP-L5 hat die gesamte Arbeit gemacht und
erst danach gemerkt, dass die Regel kaputt ist. So steht das Ergebnis in den ersten Minuten.

Zusaetzlich mitspezifiziert: das fehlende `aggregation`-Feld im gefingerprinteten Cap-Tupel, damit
Records vor und nach der Reparatur nicht als dieselbe Konfiguration verbucht werden.

Vorregistriert inklusive Ausweg: laesst sich System 31 nur reparieren, indem anderswo eine
Verletzung entsteht, ist das mit Zahlen zu berichten statt Schwellen zu tunen, bis die Tabelle
passt — es hiesse, Rauschboden plus fester Horizont taugen nicht als Basis fuer einen sicheren Cap.

### WP-L5 durchgefallen — beide Abnahmekriterien verfehlt; die Ursache ist ein Fehler in meiner Spec

Caps nach WP-L5, wieder selbst nachgerechnet:

| System | Wahrheit pro Gleichung | WP-L4 | **WP-L5** | |
|---|---|---|---|---|
| 3 | [2] | [2] ✓ | **nothing** | Cap verloren |
| 11 | [4] | [4] ✓ | **nothing** | Cap verloren |
| 26 | [3, 3] | [3, 3] ✓ | **nothing, nothing** | Cap verloren |
| 31 | [3, 3] | [3, 3] ✓ | **[1, 1]** | **neue Verletzung** |
| 63 | [3, 3, 1, 1] | [1, 1, 1, 1] ✗ | [1, 1, nothing, nothing] | du1/du2 weiter verletzt |

Abnahmekriterium 1 (3/11/26/31 behalten ihre Caps) auf allen vier Systemen verfehlt. Kriterium 2
(63 du1/du2 ungecappt) ebenfalls verfehlt. Die Sicherheitsinvariante ist **schlechter** geworden:
Verletzungen von 2 auf 4, weil System 31 neu dazukommt. Gleichzeitig cappt die Regel auf keinem
System mehr, auf dem sie funktioniert hat — also auf beiden Achsen verschlechtert.

**Codex hat sich dabei korrekt verhalten.** Die Stoppbedingung der Spec hat gegriffen: der
System-26-Cap wurde zuerst geprueft, die Abweichung von [3,3] auf `nothing` erkannt, die Arbeit
abgebrochen und berichtet. Dass Tests, Bericht, suiteweite Invariante und Fingerprint fehlen, ist
kein Lieferdefizit, sondern Befolgung der Abbruchregel. Die Regel hat genau das getan, wofuer sie
da war — teure Folgearbeit auf einer kaputten Basis wurde vermieden.

**Codex' Deutung ist allerdings falsch** und darf nicht so stehenbleiben: er liest das Ergebnis als
den in Abschnitt 8 vorregistrierten Trade-off zwischen Sicherheit und korrekten Caps. Das ist es
nicht. Ein echter Trade-off haette die Sicherheit verbessert und dafuer Nutzen gekostet. Hier ist
**auch die Sicherheit schlechter geworden** — System 31 ist eine neue Verletzung, die es vorher
nicht gab. Beide Achsen gleichzeitig zu verschlechtern ist kein Trade-off, sondern ein Defekt.

**Der laufende 26/42-Lauf ist nicht betroffen.** Julia laedt den Code beim Prozessstart; der Lauf
faehrt die WP-L4-Semantik mit Cap [3,3]. Der Arbeitsbaum reproduziert ihn aber nicht mehr —
siehe Provenienz-Punkt unten.

**Diagnose, und der Fehler liegt bei mir.** Die Spec schrieb vor: Residuum auf oder unter dem
Rauschboden → nicht beurteilbar → kein Cap. Das ist falsch, denn **den Boden zu erreichen ist genau
das, was ein korrektes Modell tut.** Die Regel kann damit auf keinem loesbaren System je einen Cap
setzen. Die Unterscheidung, auf die es ankommt, ist eine andere: *faellt* das Residuum auf dieser
Stufe auf den Boden (positive Evidenz, hier cappen) oder lag es *schon vorher* dort, bevor
ueberhaupt eine Stufe geholfen hat (keine Information, kein Cap)?

**Zweiter Defekt, unabhaengig davon: der Look-Ahead-Horizont ist auf 1 geschrumpft.** Der alte Code
scannte alle Stufen und nahm `max(split_cap, next_stage)`, konnte also ueber eine nutzlose
Zwischenstufe hinwegsehen. Der neue Walk bricht bei der ersten Stufe ohne Gewinn ab. Genau daran
scheitert System 31: die Wahrheit braucht den Kreuzterm `u1*u2` aus Stage 3, die selbstquadratische
Stage 2 bringt dort nichts, der Walk stoppt bei 1. **Das ist die tote Zwischenstufe aus Abschnitt 5.2
des Ausgangsdokuments, wiedereingefuehrt** — dieselbe Begruendung, aus der dort N = 2 als Horizont
vorgeschlagen war.

**Provenienz-Defekt, von der Spec nicht abgedeckt.** Der Fingerprint in `run_regression.jl` fuehrt
die Cap-Politik als hartcodiertes Tupel ohne das neue Feld `aggregation`. WP-L5 hat die Cap-Semantik
materiell geaendert, ohne dass sich `3f9be6d36c4043de` bewegt. Records vor und nach L5 waeren damit
als dieselbe Konfiguration verbucht. Muss mit repariert werden.

**Konsequenz fuer HEAD:** der Arbeitsbaum enthaelt jetzt eine Cap-Berechnung, die unsicherer ist als
die vorige. Bis WP-L5b liegt, darf aus HEAD kein Lauf mit `evogrow_v3_stage_capped` gestartet werden.

<!-- 94bf5a7 -->  

### WP-L5 beauftragt — Cap nur auf positive Evidenz

Behebt den WP-L4-Defekt. Kernprinzip in der Spec: **ein Cap darf nur auf positive Evidenz gesetzt
werden, Abwesenheit von Evidenz muss ungecappt lassen** — die Kosten sind asymmetrisch, ein falscher
Cap macht die Wahrheit unerreichbar, ein fehlender kostet nur den Status quo. Drei Faelle werden
getrennt statt in eine Zahl kollabiert: Residuum ueber dem Boden und naechste Stufe bringt nichts
(→ Cap), Residuum schon unter dem Boden (→ kein Cap), naechste Stufe nicht auswertbar (→ kein Cap).
Die Aggregation ueber Splits darf undentscheidbare Splits nicht stillschweigend verschlucken.

Harte Abnahmekriterien statt Argumentation: 3 → [2], 11 → [4], 26 → [3,3], 31 → [3,3] unveraendert;
63 du1/du2 ungecappt. Dazu eine suiteweite Sicherheitsinvariante — fuer jede Gleichung muss der Cap
entweder `nothing` oder ≥ der wahren Stage sein; aktuell 2 Verletzungen, Ziel 0. Wahrheitswissen
dient dabei ausschliesslich der Beurteilung, nie der Berechnung. Gegengewicht in derselben Tabelle
gefordert: wie viele Gleichungen ueberhaupt noch einen Cap bekommen und wie viele Stufen gespart
werden — eine Regel, die sicher ist, weil sie nie cappt, waere wertlos.

Kritische Nebenbedingung: **der 26/42-Lauf laeuft gerade.** Aendert sich der Cap auf System 26, ist
dessen Vergleichsbasis hinfaellig; die Spec verlangt, das zuerst zu pruefen und bei Abweichung
abzubrechen statt weiterzumachen.

Vorregistriert inklusive Ausweg: laesst sich die Verletzungszahl nicht auf 0 bringen, ohne die
korrekten Caps auf 3/11/26/31 zu verlieren, ist das explizit mit Zahlen zu berichten — es hiesse,
das Rauschboden-Kriterium taugt nicht als Basis fuer einen sicheren Cap, und das waere ein Ergebnis
und kein Misserfolg.

### WP-L4 geliefert — Cap korrekt auf 4 von 5 Systemen; ein Sicherheitsdefekt auf System 63

Neue Variante `evogrow_v3_stage_capped` (`EvoGrowStageCapped`), Cap-Berechnung in
`src/structure/stage_cap.jl`, Bericht in `docs/wp_l4_stage_cap_report.md`. Neuer
`config_fingerprint 3f9be6d36c4043de`. Der entscheidende 26/42-Lauf wurde korrekt **nicht**
ausgefuehrt, `history.jsonl` ist unberuehrt.

**Was haelt.** Ground-Truth-Leckage ist konstruktiv ausgeschlossen: `estimate_stage_caps(traj, basis;
policy)` hat schlicht keinen Parameter, ueber den Wahrheitswissen eintreten koennte — kein
`expected_terms`, kein `expected_stage`, kein `true_rhs!`, keine System-ID. Die v3-Aenderungen sind
additiv mit `stage_caps = nothing` als Default; bei abgeschaltetem Cap ist das Verhalten identisch
(die Umstellung von `all(==(max_stage), eq_stages)` auf die Limit-Form ist aequivalent, weil Stufen
`max_stage` nie ueberschreiten koennen). Der Cap ist reine Obergrenze und entfernt keine Terme.

**Caps selbst nachgerechnet** (eigener Kontrolllauf ueber `estimate_stage_caps`, nicht aus dem
Codex-Bericht uebernommen):

| System | Erwartungsstage pro Gleichung | berechneter Cap | |
|---|---|---|---|
| 3 | [2] | [2] | korrekt |
| 11 | [4] | [4] | korrekt |
| 26 | [3, 3] | [3, 3] | korrekt |
| 31 | [3, 3] | [3, 3] | korrekt |
| 63 | [3, 3, 1, 1] | **[1, 1, 1, 1]** | **du1/du2 falsch** |

**Der Defekt.** Auf System 63 bekommen du1 und du2 einen Cap von 1, obwohl sie den Kreuzterm
`u1*u3` aus Stage 3 brauchen. Unter der gecappten Variante waere die wahre Struktur dort
**strukturell unerreichbar** — die Suche koennte sie nicht mehr finden, egal wie lange sie laeuft.
Die Zusicherung des Berichts, nicht beurteilbare Gleichungen blieben ungecappt, greift hier nicht:
`_cap_for_equation` liefert `nothing` nur, wenn *kein einziger* Split ueberhaupt einen brauchbaren
Stage-1-Fit hat; in jedem anderen Fall liefert es eine Zahl. „Residuum liegt schon bei Stage 1 unter
dem Rauschboden" wird als „Stage 1 genuegt" gelesen statt als „nicht beurteilbar".

**Warum das kein blosser Programmierfehler ist.** Die Regel kann „wirklich nur Stage 1 noetig" nicht
von „Signal zu klein, um zu urteilen" unterscheiden — beide sehen identisch aus: Residuum bei Stage 1
bereits unter dem Boden. Das ist **exakt die Fall-A-gegen-Fall-B-Ambiguitaet aus dem urspruenglichen
Problemdokument, eine Ebene tiefer wiedergekehrt**, jetzt im Bodentest des Look-Aheads selbst. Die
Konsequenz fuer das Design ist asymmetrisch und eindeutig: ein falscher Cap macht die Wahrheit
unerreichbar, ein fehlender Cap kostet nur den Status quo. **Der Cap muss positive Evidenz verlangen,
nicht die Abwesenheit von Evidenz.**

**Fuer die Entscheidungszelle unkritisch.** Auf System 26 ist der Cap [3,3] und damit korrekt; der
vorregistrierte 26/42-Lauf ist von dem Defekt nicht betroffen und kann starten. Der Defekt betrifft
die Verallgemeinerung (Phase B ueber 63 Systeme), nicht diese Zelle.

**Teil A** ist umgesetzt: `lower_stage_indistinguishable` und `rank_deficient_at_tested_stage` sind
getrennt, Rangdefizit wird pro getesteter Stage gefuehrt. Die Schlagzeile aendert sich von
10 exact / 0 over / 2 under / 4 not-identifiable auf **12 exact / 0 over / 4 under / 0 rank_deficient**.
Die beiden neuen Undershoots sind 63 du1/du2 — also derselbe Defekt, im Offline-Bild sichtbar.
Konsistent, und ein gutes Argument dafuer, dass die korrigierte Klassifikation ehrlicher ist als die
alte.

Kleine offene Punkte: beim kombinierten Test-Include trat eine Modul-Ambiguitaet auf, die betroffenen
Tests wurden einzeln nachgefahren; das sollte bereinigt werden, damit die Suite in einem Rutsch
laeuft.

<!-- fca1862 -->

## 2026-07-31

### WP-L4 beauftragt — Stage-Cap aus dem Look-Ahead, erster Test als Mechanismus

Zwei Teile. **Teil A** trennt die beiden Bedeutungen von „nicht identifizierbar", die WP-L3
vermischt und die beide zufaellig 4 ergeben: untere Stage erreicht bereits den Rauschboden (54 du2/du3,
63 du1/du2) gegen rangdefizite hoehere Stage (System 63 gesamt). Ausserdem wird Rangdefizit
**pro getesteter Stage** gefuehrt statt als Pauschaleigenschaft — 63 du3/du4 haben Erwartungsstage 1
und sind dort bestens konditioniert, sie als undentscheidbar zu fuehren untertreibt das Verfahren.
Teil B haengt davon ab, weil der Cap fuer nicht beurteilbare Gleichungen definiert sein muss.

**Teil B** integriert das Gate als Pro-Gleichungs-Obergrenze: `max_useful_stage_k` einmal vor der
Suche berechnet, danach darf keine Gleichung darueber hinaus promoten. Kein spekulatives Unlock, kein
Checkpoint, kein Rollback — das Gate haengt nur an Trajektorie, Basis, Gleichung und Stage, nie an der
Population. Neue Variante mit eigenem Slug; v2.2 und v3 muessen bei abgeschaltetem Cap bit-identisch
bleiben. Der Cap ist reine Obergrenze: er kann eine Promotion nur verhindern, nie ausloesen; nicht
beurteilbare Gleichungen bekommen gar keinen Cap.

**Die schaerfste Auflage der Spec betrifft Ground-Truth-Leckage.** Die Probe hat Wahrheitswissen
bisher nur zur *Auswertung* benutzt (Konfusionsmatrix, analytische Rauschboden-Zeilen). Der Cap muss
allein aus beobachteter Trajektorie und Basis entstehen — nichts aus `expected_terms`,
`expected_stage` oder `true_rhs!` darf ihn erreichen. Dafuer ist ein eigener Test gefordert. Der
Richardson-Boden ist datenbasiert und erlaubt.

**Zweite Auflage: der Readout darf nicht zirkulaer sein.** Auf System 26 ist der Cap `[3,3]`, also
erzwingt er `eq_final_stages = [3,3]` per Konstruktion. Das als Erfolg zu melden waere zirkulaer; es
gilt als Konstruktionspruefung. Die echten Fragen sind: findet `du2` jetzt den richtigen Support
(unter v2.2 endete es als `{u1, u1^2}`, obwohl alle Terme auf Stage 3 verfuegbar waren), wie
verhaelt sich der Loss gegen den v2.2-Anker und das v3-Ergebnis, und wie viel Kosten fallen weg —
gezaehlt in Integrationen, nicht in Wall-Clock. Ausdruecklich als vollwertiges Ergebnis vorgesehen:
Overshoot weg, Kosten runter, `du2` weiterhin falsch. Das hiesse, der Look-Ahead loest die
Komplexitaetsallokation und nicht die strukturelle Wiederfindung — genau die Frage, die seit dem
WP-T2-Befund offen ist.

Der entscheidende Lauf ist **nicht** Teil der Lieferung: Codex implementiert, prueft Bit-Identitaet,
Leckage-Test, Unit-Tests und einen billigen Smoke auf System 3/11 — den 26/42-Lauf startet der User.

### WP-L3 geliefert — alle vier Vorhersagen bestaetigt; die Grenzen sind jetzt vermessen

`studies/lookahead/floor_gated_probe.jl`, Ausgaben in `outputs/studies/lookahead/floor_gated_probe/`.

**Konfusionsmatrix ueber alle 16 exakten Gleichungen** (Hauptkonfiguration `local_poly` +
`richardson_wls` + `ols`, `tau_rel = 1e-4`, `tau_abs = 1e-8`):

| Regel | exact | over | under | not_identifiable |
|---|---|---|---|---|
| threshold_only | 9 | 3 | 0 | 4 |
| **floor_gated** | **10** | **0** | **2** | 4 |

Vorhersage 1 exakt eingetroffen: das Boden-Gate entfernt alle drei System-54-Overshoots und erzeugt
genau zwei Undershoots, beide auf System 54 (du2 und du3, je 3 → 2); du1 wird korrekt. Vorhersage 2
ebenfalls: Systeme 3, 11 und 26 bleiben unter der bodengesteuerten Regel alle korrekt.

**Vorhersage 3 bestaetigt — System 54 ist schaetzer-/sampling-begrenzt, nicht anregungsbegrenzt.**
Schon bei doppelter Dichte (T = 600) erscheint die Stage-3-Klippe: du2 hat Residuen
0,356 | 2,93e-3 | 4,19e-7 | 4,51e-8 | 3,20e-8 bei Rauschboden 6,38e-4 — Stage 2 liegt jetzt *ueber*
dem Boden, Stage 3 darunter, die Klippe ist also aufloesbar. Bei 4x und 8x noch deutlicher.
Aufschlussreich ist die Richtung: das Stage-2-Residuum *steigt* von 6,2e-4 (T = 300) auf 2,93e-3
(T = 600). Bei grobem Sampling absorbierte der Stage-2-Fit einen Teil des Ableitungsfehlers und sah
dadurch besser aus, als er ist — dieselbe Rausch-Absorptionsmechanik wie bei der `r_k`-Kontamination,
nur anders sichtbar. **Die beiden Undershoots sind damit eine Datendichte-Grenze, kein Regelfehler.**

**Vorhersage 4 bestaetigt:** System 63 bleibt bei *jeder* Dichte rangdefizient. Das Defizit ist damit
die Erhaltungsgroesse (die SEIR-Zustaende summieren sich zu einer Konstanten) und keine gewoehnliche
Schlechtkonditionierung.

**Ablation — die billigen Interventionen tragen den Grossteil.** `central` + unweighted +
threshold_only liefert exact 2 / over 10; `central` + `richardson_wls` + floor_gated bereits
exact 9 / over 0 / under 3; erst `local_poly` bringt die zehnte Gleichung. Gewichtung und Boden-Gate
tun also die Hauptarbeit, der teurere Schaetzer setzt oben drauf.

**Ridge ist vollstaendig wirkungslos** — in allen 16 Kombinationen bitgleiche Konfusionszahlen wie
`ols`. Regularisierung rettet nicht-identifizierbare Gleichungen nicht, was zum strukturellen (statt
numerischen) Charakter des Defizits passt. Ehrliches Negativergebnis, gehoert so berichtet.

**Ein Mangel, der vor jeder Paper-Verwendung behoben werden muss: „nicht identifizierbar" bedeutet in
den beiden Artefakten zwei verschiedene Dinge, und beide ergeben zufaellig 4.** Die
`identifiability.csv` flaggt {54 du2, 54 du3, 63 du1, 63 du2}; die Konfusionskategorie
`not_identifiable` umfasst dagegen alle vier Gleichungen von System 63. Dazu kommt: 63 du3 und du4
haben Erwartungsstage 1 und sind auf ihrer eigenen Stage bestens konditioniert (Kondition 234) — sie
als `not_identifiable` zu fuehren, nur weil eine *hoehere* Stage rangdefizit ist, ist konservativ und
untertreibt das Verfahren. Die beiden Definitionen muessen getrennt benannt werden.

**Einordnung.** Die Kernfrage ist damit vollstaendig beantwortet und die Grenzen sind vermessen statt
vermutet: der Test entscheidet korrekt, wo die Ableitung die Struktur aufloest; wo er das nicht tut,
ist die Ursache benannt und quantifiziert (Datendichte auf 54, Erhaltungsgroesse auf 63). Was
weiterhin **nicht** gezeigt ist: dass das die Discovery verbessert. Alles bisher Gemessene ist offline
auf Systemen mit bekannter Wahrheit, und der Checkpoint ist die *volle* Bibliothek, nicht eine
gefundene Struktur.

<!-- 2963fcc -->

### WP-L3 beauftragt — bodengesteuerte Zuendregel, Identifizierbarkeit, Sampling-Grenze

Drei Defekte aus WP-L2, keiner davon ein Zweifel am Kernergebnis: (1) die Zuendregel konsultiert den
berechneten Rauschboden nicht — Pflichtvariante mit Boden-Gate, beide Regeln nebeneinander, und die
Gegenrichtung ausdruecklich mitberichtet (auf 54 du2/du3 faellt das Residuum schon bei Stage 2 unter
den Boden, eine bodengesteuerte Regel unterschiesst dort). (2) Rangdefizit wird ein eigenes Urteil
`not_identifiable` statt eines stillen Ausschlusses, plus regularisierte Fitvariante; zusaetzlich
suiteweit die Frage, wie viele Gleichungen entlang ihrer eigenen Trajektorie nicht identifizierbar
sind — das begrenzt, was *jedes* ableitungsbasierte Verfahren aus einer Trajektorie entscheiden kann.
(3) Dichte-Sweep (2x/4x/8x `T`, `u0`/`tspan` unveraendert) trennt auf System 54 die beiden bislang
konfundierten Erklaerungen: schaetzerbegrenzt (dann erscheint die Klippe bei hoeherer Dichte) gegen
anregungsbegrenzt (dann nie). Auf System 63 muss das Rangdefizit bei jeder Dichte bestehen bleiben,
sonst ist es keine Erhaltungsgroesse, sondern gewoehnliche Schlechtkonditionierung. Sampling-Sweep ist
ausdruecklich als Sensitivitaetsstudie markiert und fliesst nicht in die Hauptkonfusionsmatrix.

### WP-L2 geliefert — Trennung gelingt; die Idee traegt, und `r_k` ist bestaetigt kontaminiert

`studies/lookahead/derivative_estimator_probe.jl`, Ausgaben in
`outputs/studies/lookahead/derivative_estimator_probe/`. Die WP-L1-Diagnose ist bestaetigt: das
vermeintliche Negativergebnis war ein Artefakt der Ableitungsschaetzung.

**Schaetzerwahl.** Median-RMS-Ableitungsfehler: `central` 1,75e-2, `fd4` 1,24e-2, `local_poly`
1,78e-3. **Hoehere FD-Ordnung ist nicht der Hebel — Glaettung ist es** (Faktor 10 gegen Faktor 1,4).

**Die Trennung gelingt sauber.** Holdout-Residuen mit `local_poly`, Splits A/C/D (B bleibt der
degenerierte Schwanz-Fit):

| Stage | System 26 du2 (wahr: 3) | System 11 du1 (wahr: 4) |
|---|---|---|
| 1 | 2,98e-3 | 7,89e-4 |
| 2 | 3,34e-6 | 4,53e-5 |
| 3 | **5,24e-13** | 4,53e-5 (leer, identisch) |
| 4 | 2,70e-11 (schlechter) | **7,60e-12** |
| 5 | 1,81e-11 | 5,05e-9 (schlechter) |

Beide Klippen sitzen exakt auf der wahren Stage, danach verschlechtert es sich. System 26 du2 faellt
von 3,65e-3 (WP-L1) auf 5,24e-13 — zehn Groessenordnungen, allein durch die Ableitungsschaetzung.
System 3 bleibt korrekt bei Stage 2. Alle drei vorregistrierten Vorhersagen halten. **Damit ist die
Kernfrage des Diskussionsdokuments beantwortet: ein billiger Ableitungs-Look-Ahead trennt die beiden
Gegenbeispiele, sobald die Ableitung stimmt.**

**Teil 4 — `r_k`-Kontamination bestaetigt, und staerker als vermutet.** Auf System 26 liegt der Boden
mit *wahrer* Struktur und *wahren* Parametern bei [1,808, 0,520], das gefittete volle Stage-3-`r_k`
dagegen bei [0,142, 0,0394] — der Boden liegt um Faktor 13 **darueber**. `r_k` misst also nicht
strukturelle Angemessenheit, sondern wie viel Ableitungsfehler ein Modell absorbieren kann, und diese
Kapazitaet waechst mit der Termzahl. Das Signal ist damit systematisch nach „mehr Terme helfen"
verzerrt — genau die Eskalation, die v3 gezeigt hat. Der bessere Schaetzer senkt den Boden auf
[0,425, 0,106] (Faktor 4,3 / 4,9), beseitigt ihn nicht. **v3s Scheitern an Gate 2 hat damit eine
zweite, numerische Ursache zusaetzlich zur Evidenz-Diagnose.**

**Drei Einschraenkungen, die der gelieferte Bericht zu leicht nimmt.** Erstens deckt die
Konfusionsmatrix nur 12 der 16 exakten Gleichungen ab: System 63 faellt komplett heraus, Stages ≥3
sind auf allen Splits rangdefizient (Kondition > 1e10). Die Ursache ist strukturell — die
SEIR-Zustaende summieren sich zu einer Konstanten, es gibt eine exakte lineare Abhaengigkeit zwischen
den Variablen; passend dazu erreicht du1 schon bei Stage 2 ein Residuum von 1,2e-14, obwohl die wahre
Gleichung einen Kreuzterm braucht. Der Vergleich „5 Overshoots vorher, 3 jetzt" ist deshalb nicht
like-for-like, die schweren Faelle sind aus dem Nenner gefallen. Zweitens sind alle drei verbliebenen
Overshoots System 54 und reines Rauschfitten: bei du1 liegt der Rauschboden bei 8,0e-4, saemtliche
Residuen ab Stage 1 bei 5,9e-6 und darunter — die Zuendregel konsultiert den Boden nicht, obwohl er
berechnet wird. Drittens ist die naheliegende Korrektur kein Freifahrtschein: bei 54 du2/du3 faellt
das Residuum schon bei Stage 2 unter den Boden, eine bodengesteuerte Regel wuerde dort unterschiessen.
Ehrliche Lesart: auf Lorenz reicht die Ableitungsgenauigkeit bei gegebenem Sampling nicht, um die
Stage-3-Kreuzterme aufzuloesen. Kleinigkeit: Split D wurde ergaenzt, aber nirgends beschrieben.

**Einordnung.** Die Grenze des Verfahrens zeichnet sich klar ab und ist selbst ein Ergebnis: der Test
funktioniert, wo die Ableitungsschaetzung die Struktur aufloest; die Systeme 54 (schnelle Dynamik) und
63 (Erhaltungsgroesse) markieren, wo das aufhoert. Das ist eine publizierbare Aussage, kein Scheitern.

<!-- 24145f6 -->

### WP-L2 beauftragt — Ableitungsschaetzung als bindende Schranke

Konsequenz aus WP-L1. Vier Teile, alle rein diagnostisch: (1) Schaetzervergleich gegen den
*tatsaechlichen* punktweisen Fehler — das wahre RHS ist bekannt, also ist der Fehler exakt
berechenbar; dazu eine Richardson-Schaetzung (Gitter gegen halbiertes Gitter) mit Pflichtvalidierung
gegen den echten Fehler, denn ein Fehlerschaetzer, der den echten Fehler nicht nachbildet, ist
stromabwaerts wertlos. (2) Probe erneut, Baseline- und bester Schaetzer nebeneinander, plus gewichtete
Regression mit Richardson-Gewichten und punktweisem statt blockweisem Rauschboden. (3) Splits mit
explizitem Gueltigkeitskriterium; ungueltige Splits werden ausgewiesen und ausgeschlossen, nicht
mitgemittelt. (4) die `r_k`-Kontaminationsmessung.

`src/optimize/pretune.jl` bleibt ausdruecklich unangetastet — `estimate_derivatives` speist den
Pretuning-Warmstart und das v3-Promotionssignal; eine Aenderung dort bewegt Suchverhalten und
`config_fingerprint`. Alle Alternativschaetzer leben im Study-Code.

Vier Vorhersagen vorab registriert, mit Abbruchklausel: scheitern die Vorhersagen zu System 11
(grosser stabiler Stage-4-Gewinn) oder System 26 (Stage-3-Residuum faellt Richtung analytischen Boden,
kein Gewinn bei 4/5) unter *allen* Schaetzern, ist der Ableitungsraum auf transientenlastigen Systemen
zu schwach fuer einen Look-Ahead. Das waere ein echtes Negativergebnis und ist so zu berichten, statt
weitere Schaetzer nachzuschieben, bis etwas passt.

### WP-L1 geliefert — das vermeintliche Negativergebnis ist ein Messartefakt

Isolierte Stage-Potential-Probe (`studies/lookahead/stage_potential_probe.jl`), Ausgaben in
`outputs/studies/lookahead/stage_potential_probe/`. Umfang gegenueber dem Diskussionsdokument
erweitert: 10 Benchmark-Systeme statt 3, davon 8 exakte mit 16 Gleichungen, jeweils mit
pro-Gleichungs-Erwartungsstage aus `expected_terms` + `term_groups` (System 63 → [3,3,1,1],
System 54 → [1,3,3]). Kein `strogatz_extended.json`-Parsing. Keine ODE-Simulation in der Probe, kein
BFGS, kein RNG, kein `src/`-Eingriff. Leerstufen korrekt erkannt (System 11, Stage 3: `new_terms = 0`).

**Der Bericht meldet: keine Trennung.** Kein Gitterpunkt liefert „System 26 stoppt bei Stage 3" und
zugleich „System 11 geht bis Stage 4"; bestes Gitter `tau_rel = 0.05`, `tau_abs = 1e-6`, Konfusion
under 2 / exact 9 / over 5. **Diese Schlagzeile ist nicht belastbar.** Die Rauschboden-Zeilen, auf
denen die Spec bestanden hat, zeigen warum — Split A, Holdout:

| | analytisch wahres RHS | LS-Fit wahrer Support | volle Bibliothek |
|---|---|---|---|
| System 3, du1 | 8,2e-12 | 4,6e-7 | Stage 2: 4,6e-7 → Stage 5: 2,6e-6 |
| System 11, du1 | 1,9e-9 | 2,3e-4 | Stage 2: 5,1e-3 → **Stage 4: 8,8e-2** |
| System 26, du2 | 4,3e-11 | 5,7e-3 | **Stage 3: 3,7e-3** → Stage 5: 1,5e-7 |

Zwei Zeilen tragen die Diagnose. **System 26 du2 ist bei Stage 3 exakt darstellbar** — der Holdout der
vollen Stage-3-Bibliothek muesste auf dem Boden von 4,3e-11 liegen, liegt aber acht Groessenordnungen
darueber; der Fit der wahren Struktur ist mit 5,7e-3 sogar schlechter als die volle Bibliothek.
**System 11 wiederholt exakt das WP-T1-Muster:** das analytisch wahre RHS hat auf dem Fit-Block
Residuum 4,606, der LS-Fit derselben wahren Struktur kommt auf 1,159 — der Fit schlaegt die Wahrheit
um Faktor 4, was nur beim Fitten von Rauschen moeglich ist. Entsprechend sieht Stage 4 (8,8e-2)
schlechter aus als Stage 2 (5,1e-3), die kubische Klippe ist unsichtbar.

Ursache ist `estimate_derivatives` — ein einfacher zentraler Differenzenquotient. System 11 startet
bei `du = -39,3`, System 26 du2 bei `du = -31,4`, beide bei `h = 0,05`. Im Transienten ist der
FD-Fehler dort von Ordnung 1, also groesser als jedes zu detektierende Signal. System 3 hat zahme
Dynamik und liefert das korrekte Urteil. **Das Muster ist nicht „die Idee traegt nicht", sondern „die
Probe funktioniert genau dort, wo die Ableitung stimmt".** Die Idee ist damit nicht widerlegt, sondern
ungeprueft — dieselbe Lage wie bei der Screening-Spur im Juli, diesmal aber mit sofort bekannter
Ursache.

Zweiter, unabhaengiger Mangel: **Split B ist strukturell wertlos.** Er fittet auf dem kollabierten
Trajektorienschwanz (Trainingsresiduen ~1e-11, Konditionszahlen bis 3,9e11) und extrapoliert in den
Transienten (Holdout 1,8 bis 5,3e8). Der Bericht bildet den Median ueber alle drei Splits, mischt also
einen brauchbaren mit einem degenerierten — die Aussage „keine Trennung" ist teilweise
Aggregationsartefakt.

**Nebenbefund mit potenziell groesserer Tragweite als die Probe selbst.** `estimate_derivatives` ist
nicht nur hier im Einsatz: WP-v3.4 verwendet dasselbe Signal als Promotionskriterium (`r_k` ist das
Ableitungsresiduum auf der beobachteten Trajektorie). Ist der FD-Fehler auf System 26 von Ordnung 1,
war das Plateau, auf das v3 seine Stage-Entscheidungen gestuetzt hat, dort massgeblich ein numerisches
Artefakt — eine **zweite, von der Evidenz-Diagnose unabhaengige Erklaerung fuer das Scheitern an
Gate 2**. Als Hypothese notiert, nicht als Befund; Messung ist Teil 4 von WP-L2.

<!-- 57fa6ba -->

### Gate 2 entschieden — v3 gescheitert, Entkopplung bleibt aus

Der Do-or-Die-Lauf ist durch (System 26, Seed 42, 30 Level, `evogrow_v3`, Fingerprint
`1f9c5f807d609548`, `git_hash e82715b`, `git_dirty false`, 13.047 s ≈ 3,6 h). Ergebnis gegen die am
2026-07-30 vorab festgelegten drei Kriterien:

| Kriterium | Soll | Ist | Urteil |
|---|---|---|---|
| (a) `eq_final_stages[1]` | 3 | 5 | verfehlt |
| (b) du1-Support | exakt `{u1, u1^2, u1*u2}` | zusaetzlicher u2-Term | verfehlt |
| (c) Loss | ≤ 0,001391623174905009 | 2,5195575964774715e-4 | erfuellt |

`eq_final_stages = [5,5]`, `eq_overshoot = [2,2]`. **Keine erkennbare Entkopplung — v3 faellt durch
Gate 2.** Bemerkenswert ist (c): der Loss ist gegenueber dem eingefrorenen v2.2-Anker um Faktor 5,5
besser. Die Fitqualitaet war also nie das Problem; gescheitert ist die Komplexitaetsallokation, also
genau der Punkt, fuer den v3 gebaut wurde.

**Diagnose.** Die v3-Promotionsregel stellt pro Gleichung drei Fragen: genug Stage-Budget, `r_k`
plateau, `r_k > loss_tol = 1e-8`. Bedingung 3 ist auf gekoppelten Systemen unerreichbar — der
Fehlerboden liegt bei 1e-3 bis 1e-4. Fuer eine bereits korrekt modellierte Gleichung sind damit alle
drei Bedingungen dauerhaft erfuellt, und die Regel kann Untermodellierung (eine hoehere Stage enthaelt
wirklich relevante Terme) nicht von einem irreduziblen Fehlerboden (die Struktur reicht, aber Numerik,
Fit, Daten oder Kopplung verhindern kleinere Residuen) unterscheiden. Beide Faelle sehen identisch
aus: flaches Residuum oberhalb von 1e-8. Deshalb eskalieren auch unabhaengige Pro-Gleichungs-
Controller weiter bis Stage 5 — die Dezentralisierung war technisch aktiv, aber beide lokalen
Automaten trafen dieselbe qualitative Entscheidung.

**Zentraler Erkenntnisgewinn: v3 hat veraendert, wer entscheidet, aber nicht, welche Evidenz eine
Promotion rechtfertigt.** Das ist ein sauberes, publizierbares Negativergebnis und keine verlorene
Arbeit.

Ein bloss relatives Kriterium statt des absoluten Zielwerts loest das ebenfalls nicht. Gegenbeispiel-
paar: Lotka-Volterra (Best-Loss 3,84e-2 → 3,35e-3 → 1,39e-3 → flach; richtig waere *stoppen* nach
Stage 3) gegen `du = -u^3` (2,96e-1 → 3,43e-3 → flach → 4,40e-15; richtig waere *weitergehen* ueber
die flache Stage 3, die in 1D sogar leer ist). Beide Entscheidungsmomente sehen lokal gleich aus —
Loss um 1e-3, aktuelle Stage bringt nichts, Verlauf flach. Der Unterschied liegt ausschliesslich in
Information ueber zukuenftige Termgruppen. **Das Stage-Zuend-Problem ist damit ein Look-Ahead-Problem
unter Unsicherheit.** Ein vollstaendiger simulationsbasierter Look-Ahead ist wegen der ODE-Kosten
untragbar; deshalb die Pruefung eines billigen Tests im Ableitungsraum (WP-L1).

Offen und bewusst noch nicht entschieden: PAPER_1 sieht fuer ein gescheitertes Gate 2 „v2.2 mit
ehrlicher Failure-Analyse **oder** Planrevision" vor. Der Look-Ahead waere faktisch v4. Die
Entscheidung haengt am WP-L2-Ergebnis.

<!-- a022ed2 -->

## 2026-07-30

### WP-G2.1 geliefert — Zwei-Varianten-Runner, Einzelzell-Selektor, Do-or-Die-Readout

Gate-2-Vorbereitung: statt einer teuren 45-Lauf-Matrix ein sequenzieller, paarweiser v2.2-vs-v3-Vergleich mit **System 26 / Seed 42 als vorab festgelegter Do-or-Die-Zelle**. Der v2.2-Arm ist bereits eingefroren (Baseline v0, von WP-T2 bit-exakt reproduziert), also genuegt zum Entscheiden **ein** frischer v3-Lauf. Tests real gefahren (Baseline abgebrochen, keine CPU-Konkurrenz):

- **Runner auf zwei Varianten** (`evogrow_v2_2_stage_local`, `evogrow_v3`); Screening aus der Ausfuehrungsliste. `test_regression_runner_gate2.jl` 6/6.
- **Einzelzell-Selektor** ueber `EVO_REGRESSION_VARIANT/SYSTEM_ID/SEED` (leer = volle Matrix), plus `EVO_REGRESSION_HISTORY_PATH`-Override. `main()` nur noch unter `PROGRAM_FILE`-Guard, damit `include`-bar fuer Tests.
- **`BFGS_TIME_LIMIT_S` 86.400 → 1.800 s** (reine Notbremse; greift nie — WP-T1/T2). Aendert bewusst den `config_fingerprint`.
- **Fingerprint sauber:** Codex hat `FINGERPRINT_VARIANT_LABELS` (die alten drei Labels) eingefroren, sodass die Variantenreduktion den Fingerprint **nicht** bewegt. Verifiziert: aktuell `1f9c5f80…` vs. v0 `0c739d4e…`, Delta nur durch das Zeitlimit.
- **Do-or-Die-Readout** (`studies/gate2_do_or_die/readout.jl` → `outputs/studies/gate2_do_or_die/`): reines Post-Processing, stellt v3/26/42 gegen den eingefrorenen v2.2-Anker. Vorab festgelegtes Kriterium — PASS nur wenn (a) `eq_final_stages[1]==3` (du1 bleibt auf wahrer Stage, kein Overshoot), (b) du1-Support exakt `{u1,u1^2,u1*u2}`, (c) Loss ≤ 0.001391623174905009; sonst PARTIAL (nur a verletzt) bzw. FAIL. `test_gate2_do_or_die.jl` 9/9 (PASS/PARTIAL/FAIL).

Zwei kleine Unsauberkeiten der Lieferung, ohne Korrektheitsfehler: (1) Codex schrieb sechs ungefragte v2.2-Scalar-Records unter einem Zwischenstand-Fingerprint `d596e066` (den der finale Code nicht mehr erzeugt) in die echte History — per `git checkout -- history.jsonl` entfernt, da git-getrackt und einzige uncommittete Aenderung. (2) Der v3-Smoke lief nicht end-to-end ueber den Runner (nur der Selektor unit-getestet); Risiko gering, der echte 26/42-Lauf deckt es ab.

Naechster Schritt: der User startet den einen Lauf (`EVO_REGRESSION_VARIANT=evogrow_v3 EVO_REGRESSION_SYSTEM_ID=26 EVO_REGRESSION_SEED=42`), dann `readout.jl` → Gate-2-Vorentscheidung.

<!-- f13dbc7 -->

### WP-v3.5 geliefert — Pro-Gleichungs-Overshoot-Metriken + gekoppelter Integrations-Smoke

Codex hat die Pro-Gleichungs-Metriken umgesetzt und die Integrationsluecke geschlossen. Statisch geprueft (Julia nicht gestartet, Baseline v1 laeuft weiter):

- **Metrik-Funktionen (§8):** `eq_overshoot`/`eq_wasted_levels` in `src/structure/evogrow_v3_promote.jl` — rein abgeleitet, kein RNG, keine Integration; `eq_overshoot` klammert Untersteuerung, `eq_wasted_levels` zaehlt Level ueber `expected_stage`. Exportiert in `EvoODE.jl`.
- **Record-Aufnahme:** `run_regression.jl` zieht `eq_stage_histories` aus den Meta-Daten; `has_eq_stage_data`-Guard verlangt beide Felder (`eq_final_stages` + `eq_stage_histories`), sonst bleiben beide neuen Felder `nothing` — genau wie `eq_final_stages` bei Nicht-v3-Varianten.
- **Fingerprint unveraendert:** nur zwei Ausgabefelder plus deren Export; keine gehashte Hyperparameter-Konstante angefasst. Additiv am Record-Schema, das nicht in den Fingerprint eingeht.
- **Integrationsluecke geschlossen.** `test/smoke_evogrow_v3_coupled_divergence.jl` faehrt ein billiges synthetisches 2D-System end-to-end: `u1=exp(-0.5t)` (exakt `du1=-0.5·u1`, Stufe 1) vs. `u2=1/(1+t)` (`du2=-u2²`, Stufe 2). Gleichung 1 faellt unter `loss_tol` und promotet nie, Gleichung 2 steigt — `eq_final_stages` divergieren. Damit lief der divergente Pfad (v3.3 eq-aware Child-Generation + v3.4 Pro-Gleichungs-Promotion) **erstmals in einem echten gekoppelten Lauf**, bisher nur mit injizierten Stufen unit-getestet. Ein `FastDerivativeOptimizer` ersetzt BFGS (keine teuren ODE-Solves), umgeht aber den zu testenden Suchpfad nicht — Child-Generation und Promotion laufen durch echten EvoGrowV3-Code.
- **Tests:** `test/test_evogrow_v3_metrics.jl` (alle drei Spec-Faelle inkl. Aggregat-Konsistenz `maximum(eq_overshoot) == max(0, maximum(eq_final_stages) - expected_stage)`).

Such-Verhalten und globale Metriken (`stage_overshoot`/`wasted_levels`) unangetastet; die Pro-Gleichungs-Metriken verfeinern nur. Damit ist die v3-Kette bis zur Validierung komplett. Naechster Schritt: WP-v3.6 — externer Validierungslauf v3 vs. Baseline v1 (Overshoot-Rueckgang auf gekoppelten Systemen 26/31/63), nach Abschluss der laufenden Baseline.

<!-- 960b0e6 -->

## 2026-07-29

### WP-v3.4 geliefert — Pro-Gleichungs-Promotion scharf geschaltet

Codex hat die Pro-Gleichungs-Promotionsregel umgesetzt: `src/structure/evogrow_v3_promote.jl` (neu); `evogrow_v3.jl` ersetzt die Lockstep-Promotion durch pro-gleichungs `r_k`-Plateau plus globale Termination; der Bit-Identitaets-Smoke wurde durch einen Scalar-Promote-Smoke ersetzt (korrekt — v3.4 bricht die v2.2-Gleichheit bewusst). Statisch geprueft (Julia nicht gestartet, Baseline v1 laeuft):

- **Signal (§3):** `r_k` = Ableitungsresiduum auf der beobachteten Trajektorie; `estimate_derivatives` aus `pretune.jl` wiederverwendet, RHS pro Gleichung an beobachteten Zustaenden ausgewertet — keine Integration im Normalpfad, RNG-neutral (kein Einfluss auf den Such-Stream). Fallback auf Trajektorienresiduum mit lauf-globalem Flag.
- **Promotion (§4):** drei Bedingungen (Budget `max(min_levels_per_stage, plateau_window+1)`, `r_k`-Plateau, `r_k > loss_tol`) plus Maxstufen-Guard; mehrere Gleichungen koennen pro Level promoten. `eq_plateau_histories` traegt jetzt `r_k` statt `best.objective`.
- **Termination (§5):** vor der Promotion ausgewertet → globaler `loss_tol`-Stopp hat Vorrang; neue Erschoepfung „alle Gleichungen auf Maxstufe und plateaut"; `min_levels`-Guard erhalten.
- **Tests stark:** `test/test_evogrow_v3_promote.jl` deckt alle vier §4-Bedingungen deterministisch ab (Plateau / `r_k<tol` / Budget / Maxstufe) plus den `r_k`-Signal-Test (Konstanten-Basis, lineare Trajektorie → `r_1≈0`, `r_2=9`). `test/smoke_evogrow_v3_scalar_promote.jl` faehrt System 3+11 end-to-end ohne v2.2-Gleichheitsanspruch.
- EvoGrow/v2.2 und Child-Generation unangetastet; `promotion_log`-Formaenderung unkritisch (nur generische Serialisierung in `experiments/run_experiment.jl`).

**Bewusst kein No-Op:** das Plateau-Signal wechselt von `best.objective` auf `r_k`; das aendert das Verhalten auch auf skalaren Systemen. Bit-Identitaet war hier nicht das Kriterium, sondern deterministische Unit-Test-Logik.

Zwei kleine, nicht-blockierende Punkte fuer spaeter: `stage_level_count` ist jetzt toter Code (wird inkrementiert, nie gelesen); der Trajektorien-Fallback ist ungetestet (nur bei nicht-finiter FD aktiv). Naechster Schritt: WP-v3.5 (expected-stage-Metriken `eq_overshoot`/`eq_wasted_levels`), dann WP-v3.6 (Validierung gegen Baseline v1: Overshoot-Rueckgang auf 26/31/63, extern nach der laufenden Baseline).

<!-- a334256 -->

### WP-v3.3 geliefert — gleichungs-bewusste Child-Generation, unter Lockstep bit-identisch

Codex hat WP-v3.3 umgesetzt: `src/structure/evogrow_v3_childgen.jl` (neu), `evogrow_v3.jl` ruft im Level-Loop jetzt `_expand_equation_aware_with_usage_policy` statt `_expand_with_usage_policy`, `EvoODE.jl` bindet die neue Datei ein. Verifikation **statisch** geprueft (Julia nicht gestartet, um die parallel laufende Baseline v1 nicht um CPU zu bringen; Ausfuehrungs-Evidenz liefert Codex' eigener Testlauf):

- **Strukturelle Bit-Identitaet korrekt.** Bei uniformen `eq_stages` — dem Lockstep-Zustand — delegiert `_expand_equation_aware_with_usage_policy` an den unveraenderten `_expand_with_usage_policy` mit denselben `allowed_terms`/`current_stage_terms`: derselbe Code, dieselbe RNG-Reihenfolge. Der Pro-Gleichungs-Pfad wird nur bei divergierenden Stufen betreten und ist bis WP-v3.4 (Promotion) im echten Lauf tot.
- **Verfuegbarkeits-Praedikat korrekt.** `stage(t)` aus `term_groups`, `vars(t)` per Regex `u(\d+)` aus `basis_term_name`. Namensformat bestaetigt (`u1`, `u1^2`, `u1*u2`, `u1^3`, `sin(u1)`, `cos(u1)`) — nur echte Cross-Terme haben zwei Variablen, dort greift die Paarregel `min(eq_stages[v] for v in vars(t)) >= stage(t)`.
- **Tests stark.** `test/test_evogrow_v3_childgen.jl`: divergente Stufen `[1,3]` (Gleichung 1 nur Stage-1-Terme, `u1*u2` fuer keine Gleichung verfuegbar) und — der harte Teil — die Delegation bei `[3,3]` erzeugt byte-identische Kinder wie der Direktaufruf (gleicher Seed, Vergleich aller `active_idxs`). `test/smoke_evogrow_v3_bit_identity.jl`: EvoGrowV3 gegen EvoGrow(v2.2) end-to-end auf analytischer System-11-Trajektorie; bricht bei jeder Abweichung in loss/objective/final_stage/Struktur ab. Transitiv: WP-v3.2 hatte EvoGrowV3 ≡ v2.2 etabliert, dieser Smoke bestaetigt es nach v3.3, also v3.3 unveraendert.

Promotion (`_lockstep_stage_progression_decision`, `_apply_lockstep_stage_update!`), Metriken und `EvoGrow`/v2.2 unangetastet. `history.jsonl` bewusst nicht committet — die Baseline v1 schreibt dort gerade live. Naechster Schritt: WP-v3.4 (Pro-Gleichungs-Promotionsregel), die die Stufen erst divergieren laesst — regressionsgeprueft gegen Baseline v1.

<!-- f6261a0 -->

### WP-T2 gelaufen — Vorhersage bestaetigt, Overshoot algorithmisch, v3 validiert

Der externe System-26-Lauf ist durch (16,8 h Wall-Clock, Seed 42, 30 Level, drei Bedingungen D8/R8/R6). Ausgaben in `outputs/studies/numerics/system26_tolerance_screening/`. **Anker bit-exakt reproduziert:** R6 (1e-6) liefert `0.001391623174905009`, `final_stage = 5`, Overshoot 2, wasted 8, `pruned_match = false` — identisch zu Baseline v0 (`0c739d4e36ee6498`). Damit ist die Messung interpretierbar.

**Q2 — Toleranz aendert den Overshoot nicht (Vorhersage bestaetigt).** R6 (1e-6) und R8 (1e-8) haben bit-identisch `final_stage = 5`, `stage_overshoot = 2`, `wasted_levels = 8`. Die engere Toleranz senkt nur den Loss (1,39e-3 → 2,52e-4), nicht das Stopp-Verhalten. Beide terminieren via `plateau_absolute`, keiner naehert sich je `loss_tol = 1e-8` (haengt bei 1e-4 bzw. 1e-3). **Der Overshoot auf System 26 ist algorithmisch, nicht numerisch** — genau die geschaerfte Prognose vom 2026-07-23. Damit trennt die Messung sauber: auf System 3 numerisch (siehe 2026-07-22), auf gekoppelten Systemen algorithmisch. Die v3-Begruendung ist bestaetigt, nicht bedroht.

**Q3 — Screening auf gekoppeltem System: schnell, aber kein Discovery-Gewinn.** D8 (Screening) gegen R8 (Referenz), beide 1e-8:
- Deterministisch, tragend: D8 braucht **98.253 Integrationen gegen R8s 3.348.287** (34x weniger). Beide `pruned_match = false`, beide Overshoot 2. D8 nutzt 9 Terme (5+4), R8 nur 6 (4+2) — D8s niedrigerer Loss (1,01e-4 vs 2,52e-4) ist Ueberparametrisierung, kein Strukturgewinn.
- Ranking-Kollaps: `rank_agreement_spearman` Median **−0,014** (Mittel 0,12, Min −0,64, Max 0,998). Das FD-Ableitungs-Screening rankt Kandidaten auf dem gekoppelten System praktisch nicht wie der echte Loss. Der 34x-Vorteil kommt aus wenig-integrieren, nicht aus gutem Diskriminieren.
- Nested-F-Gate hier **inert**: `selection_diff_from_residual = 0` ueber alle Level. Der WP-P2.4-Durchbruchmechanismus aendert auf System 26 keine einzige Auswahl gegenueber purem Residual. Er half auf System 3, tut hier nichts — der Gate-Nutzen ist systemabhaengig.

Fazit: Screening ist eine Performance-Optimierung (mit `polish_start=reference` sicher), kein Discovery-Qualitaets-Hebel. Gehoert als optionale Beschleunigung dokumentiert, nicht in den Kern-Claim; der Ranking-Kollaps muss in die Discussion.

**Q4 — der v3-Beleg steckt in der Struktur.** Wahrheit: `du1 = 3·u1 − u1² − 2·u1·u2 | du2 = 2·u2 − u1·u2 − u2²`. R8 nach Pruning: `du1`-Support `{u1, u1², u1·u2}` = **exakt Gleichung 1** (`3.03·u1 − 1.07·u1² − 1.99·u1·u2`), aber `du2` = `{u1, u1²}` — **komplett falsch.** Eine Gleichung geloest, die andere im Blindflug; der globale Plateau-Mechanismus eskaliert Stages 4/5 fuer beide, obwohl Gleichung 1 laengst fertig ist. **Das ist die Signatur, die v3 (gleichungsweise Promotion) aufloest:** geloeste Gleichung einfrieren, nur die offene weiterwachsen. Robust (suspend-fest): 8 von 25 Leveln (R8) liegen jenseits der erwarteten Stage 3, das sind ~25 % der Integrationen (Stages 4+5: 832.350 von 3.348.287 Solves).

**Korrektur meiner eigenen „63 %"-Aussage.** Die 63 % Overshoot-Kosten waren die *Wall-Clock*-Sicht (Zeitanteil der Stages 4+5 bei R8). Nach deterministischer Integrationszaehlung sind es ~25 %. Die Differenz kommt daher, dass die spaeten Integrationen einzeln teurer sind (bei 1e-8 kostet ein Stage-5-Solve 35 ms) — das ist zum Teil eine echte numerische Eigenschaft, aber die Wall-Clock-Achse ist genau die vom Suspend kontaminierte. Load-bearing bleibt: 8 verschwendete Level, ~25 % der Integrationen, eine Gleichung exakt, die andere blind.

**Nebenbefund Toleranz.** 1e-8 senkt den Loss, aendert aber kein Stopp-Verhalten auf plateauenden Systemen und verteuert ausgerechnet die verschwendeten Spaeten-Stages. Fuer den Suchpfad auf gekoppelten Systemen ist 1e-6 die guenstigere, verhaltensgleiche Wahl. Der WP-T1-Rauschgrenzen-Aspekt bleibt nur fuer exakt loesbare Systeme relevant, die die Toleranz tatsaechlich erreichen (z. B. System 11) — separate, kleinere Frage.

### Messvorbehalt — Wall-Clock kontaminiert, deterministische Schluesse unberuehrt

Der PC wurde waehrend des Laufs 2x zugeklappt (Weg zur Arbeit und zurueck, je ~45 min, ~90 min gesamt), und es lief Nebenlast durch paralleles Arbeiten. **Das kontaminiert ausschliesslich die Wall-Clock-Achse:** `elapsed_s`, `s_per_level`, `ms_per_ode_solve`, Zeitanteile und der 6,35x-Speedup sind aufgeblaeht und verrauscht und duerfen nicht als praezise Messwerte zitiert werden. Warum die wissenschaftlichen Schluesse trotzdem stehen:

1. **Anker bit-exakt** → die Berechnung selbst ist unkorrumpiert; Suspend hat den Determinismus nicht gebrochen.
2. **`time_limit_s = 86400` war nie bindend** (max R8: 31.413 s ≪ 86.400 s) → keine Iteration wurde zeitlich abgeschnitten → Iterationszahlen und Ergebnisse deterministisch, unabhaengig von Suspend-Luecken.
3. **Alle tragenden Zahlen sind Zaehlungen, keine Zeiten:** Stage, Overshoot, wasted_levels, Struktur/Support, Integrationszaehlungen (98.253 vs 3.348.287), Rank-Agreement, Gate-Diagnostik. Genau dafuer hat WP-P1 die Wall-Clock aus dem Ergebnispfad entfernt und das Skript die Solve-Zaehlungen praezise protokolliert.

Konsequenz fuer das Paper: Kosten ueber Integrationszaehlungen berichten, nicht ueber Wall-Clock. Fuer eine belastbare Zeitmessung braeuchte es einen ungestoerten Lauf ohne Suspend/Nebenlast; das ist aber fuer die v3-Begruendung nicht noetig, weil diese auf den deterministischen Achsen ruht.

<!-- e8f12f4 -->

## 2026-07-23

### WP-T2 beauftragt — Toleranz und Screening auf System 26, mit geschaerfter Vorhersage

Naechster Schritt festgelegt: die entscheidende Messung auf System 26, dem Gate-1-System. Drei Bedingungen, Seed 42, 30 Level: R6 (Referenz, Toleranz 1e-6), R8 (Referenz, 1e-8), D8 (Screening Nested-Gate + entkoppelter Start, 1e-8). User hat die kombinierte Ein-Seed-Variante gewaehlt.

**Geschaerfte Vorhersage, die den Wert der Messung erhoeht.** Beim Durchdenken des Mechanismus zeigt sich, dass mein urspruengliches „Overshoot koennte numerisch sein" zu breit war. Der numerische Kanal auf System 3 war spezifisch: der Loss operiert dort nahe `loss_tol = 1e-8`, und bei 1e-6 erreicht der Optimierer die Schwelle nicht → kein Abbruch → Eskalation. Auf System 26 liegt der Loss-Boden bei ~1,4e-3, also drei Groessenordnungen **ueber** selbst der 1e-6-Toleranz. `loss_tol` kann dort nie feuern, unabhaengig von der Toleranz, und die Eskalation ist plateau-getrieben. **Vorhersage: die engere Toleranz aendert den Overshoot auf System 26 nicht — der Overshoot ist hier algorithmisch, was die v3-Begruendung bestaetigt statt bedroht.** Falsifizierbar an den gemessenen Stage-Zahlen.

Damit trennt die Messung im Bestaetigungsfall sauber: auf einfachen Systemen numerisch, auf gekoppelten algorithmisch — eine staerkere Paper-Aussage als „Overshoot ist numerisch". Im Widerlegungsfall verstehe ich den Mechanismus nicht und muss das vor v3.3 klaeren. Unabhaengig davon wird D zum ersten Mal auf einem gekoppelten System getestet, dem, wo v2.2 die Struktur komplett falsch fand.

Ankerpflicht in der Spec: R6 muss Baseline v0 reproduzieren (System 26 Seed 42, 30 Level, 1e-6: Loss `0.001391623174905009`, `final_stage = 5`, Overshoot 2, `pruned_match = false`). Ohne bestaetigten Anker ist nichts interpretierbar. Reihenfolge nach steigender Laufzeit (D8, R8, R6), nach jeder Bedingung sofort schreiben.

### WP-T2 und WP-T2b geliefert — Lauf startklar

WP-T2 (`78124f0`): `studies/numerics/system26_tolerance_screening.jl`, drei Bedingungen D8/R8/R6, Anker gegen Baseline v0, inkrementelles Flush, Antwortblatt fuer die vier Fragen. Beim Spec-Schreiben Fast-Fehler korrigiert: die urspruengliche Verification-Zeile „Skript ausfuehren und berichten" haette Codex den 5-8h-Lauf starten lassen — durch No-Execute-Riegel plus billigen System-3-Smoke-Test ersetzt. Als Gedaechtnisnotiz festgehalten ([[feedback_long_run_no_execute]]).

WP-T2b (`4dead22`): rein additive Beobachtbarkeit. Statischer Review bestaetigt: nebenwirkungsfreier `level_callback` (liest nur den Snapshot, kein RNG, `verbose` bleibt 0), robust gegen beide Snapshot-Formen (EvoGrow `vis_history` ohne `elapsed_s`/`n_params` via hasproperty-Fallback, EvoGrowScreening `level_log` mit beiden), eine Live-Zeile pro Level plus `run.log`. Ergebnisse bit-identisch by construction.

Ausgeführter Lauf steht aus — wird extern gestartet. Ablauf: erst Sekunden-Preflight `EVO_T2_SYSTEM_ID=11` (bestaetigt Anker-Reproduktion und End-to-End-Lauf), dann System 26.

<!-- 78124f0, 2ee1b5a, 4dead22 -->

### Projektjournal erstellt

Auf Wunsch ein ausfuehrliches Projektjournal als roter Faden erstellt: `docs/projektjournal.md` (Narrativ) und `docs/projektjournal.pdf` (13 Seiten, gesetzt). Zeitraum 2026-04-20 bis 2026-07-23, mit allen Entscheidungen, verworfenen Ansaetzen samt Begruendung und Beleg, und den Messzahlen. Ergaenzt CLAUDE.md (Zustand), DIARY.md (Chronologie), PAPER_1.md (Plan). Committet `fa25253`.

<!-- 713d85f -->

## 2026-07-22

### WP-P1b Korrekturen vor Benchmark-Lauf

- `EvoGrowV3` bekommt denselben `screening_optimizer`-Durchreichpfad und dieselben Kosten-Meta-Felder wie `EvoGrow`; ohne gesetzten Screening-Optimizer bleibt die Lockstep-Bruecke im Referenzpfad unveraendert.
- Fruehe Verwerfung divergierender Screening-Solves nutzt `unstable_check` statt `isoutofdomain`; die zusaetzliche Pruefung gegen `divergence_limit` ist elementweise formuliert.
- Profiling-Benchmark wird auf 12 Level begrenzt, rechnet Screening vor Referenz und schreibt Zwischenergebnisse nach jedem Fall.
- Offener Reproduzierbarkeitszustand: ausserhalb des Regression-Runners konstruieren Benchmarks, Experimente und alte Studies `BFGSOptimizer` weiterhin ohne explizites `time_limit_s`; der Struct-Default bleibt `300.0` und muss vor Phase B bewusst entschieden werden.

### WP-P2.4 gelaufen — beide Interventionen wirken; Bedingung D schlaegt den Referenzpfad um Faktor 6,2

Committet `7eb8381`. Ankerpruefung bestanden: Referenzpfad bei 1e-6 liefert auf beiden Systemen bit-identisch die Baseline-v0-Werte.

**System 3, Bewertungstoleranz 1e-8:**

| Bedingung | Zeit | Loss | Stage | Fits | Integrationen |
|---|---|---|---|---|---|
| A Referenz | 78,6 s | 6,25e-9 | 2 | 110 | 275.098 |
| B Residuum + LS-Start (heute) | 353,2 s | 3,236e-8 | 5 | 241 | 761.581 |
| C Nested-Gate + LS-Start | 49,2 s | 3,236e-8 | 5 | 241 | 232.224 |
| **D Nested-Gate + entkoppelter Start** | **12,6 s** | **2,558e-9** | **2** | 61 | 73.680 |

System 11: alle Bedingungen qualitativ gleichwertig (Loss ~2,0e-16, Stage 4, `pruned_match` true), D mit 0,6 s gegen 1,1 s am schnellsten.

**Antwort auf die drei Pflichtfragen:**

1. **Der geschachtelte Test veraendert die Auswahl** — anders als AIC. System 3, Bedingung C: 147 von 400 Kindern scheitern am Gate, die Auswahl weicht in 126 Faellen auf 7 von 20 Leveln vom reinen Residuen-Score ab. Wirkung auf die Rangeuebereinstimmung: von **−0,78 (Median −1,0)** unter B auf **+0,26 (Median +0,48)** unter C. Der Test behebt also genau das, wofuer er gebaut wurde.
2. **Die Stage-Eskalation verschwindet — aber erst durch den Startpunkt.** C bleibt trotz wirksamem Gate bei Stage 5; D erreicht Stage 2, also die erwartete Stage, ohne Overshoot.
3. **Bedingung D entkommt dem Becken bei 3,236e-08** und erreicht 2,558e-9 — besser als der Referenzpfad mit 6,25e-9.

**Arbeitsteilung der beiden Interventionen sauber getrennt:** Das Gate senkt die Kosten (B nach C: 7,2x bei identischem Ergebnis) und repariert das Ranking. Der entkoppelte Startpunkt repariert Qualitaet und Eskalation (C nach D). Beide waren noetig, keine allein haette gereicht — genau die Aufteilung, die WP-T1 vorhergesagt hat.

**Nebenbefund mit potenziell groesserer Tragweite als das Screening selbst:** Der **Referenzpfad** profitiert schon allein von der engeren Toleranz. Bei 1e-6 braucht er auf System 3 279,3 s und endet auf Stage 3 (erwartete Stage: 2, also Overshoot 1); bei 1e-8 braucht er 78,6 s und endet auf Stage 2, also **ohne Overshoot** — 3,6x schneller bei korrekter Stage. Erklaerung: bei 1e-6 erreicht der Optimierer auf Stage 2 die Schwelle `loss_tol = 1e-8` nicht zuverlaessig, die Suche eskaliert deshalb weiter. **Ein Teil des beobachteten Stage-Overshoots waere damit ein numerisches Artefakt und keine Eigenschaft der Promotionsregel.** Das beruehrt unmittelbar die Begruendung fuer v3 und die 62-Prozent-Rechnung vom 2026-07-22. Bisher eine Zelle, ein Seed — muss auf einem gekoppelten System geprueft werden, und zwar auf System 26, wo Gate 1 gescheitert ist.

**Bemerkung zur Spec-Treue:** `SpecialFunctions` wurde als direkte Abhaengigkeit ergaenzt (nur `loggamma` fuer die F-Verteilung), obwohl die Spec keine neuen Abhaengigkeiten vorsah. Praktisch unkritisch: das Paket war ueber SciML bereits indirekt im Manifest, es wird nichts zusaetzlich installiert, nur die direkte Deklaration kam hinzu.

<!-- 7eb8381, 3327c9b -->

### WP-P2.4 beauftragt — zwei getrennte Interventionen statt nur harter Penalty

Die Spec sieht nach WP-T1 anders aus als geplant. Der harte Penalty allein kann das Ergebnis nicht retten, weil das Screening-Versagen auf System 3 laut Befund 3 nicht vom Ranking kommt, sondern vom LS-Warmstart. Deshalb zwei Interventionen, jeweils einzeln abschaltbar und einzeln messbar.

**Intervention 1 — geschachtelter Modellvergleich als Gate.** Kein additiver Strafterm mehr: bei n = 200 ist jedes Informationskriterium vom Fit-Term dominiert (AIC-Strafe hoechstens 10 Einheiten ueber p = 1..6, Fit-Term aendert sich um 19 schon bei 10 % Residuenunterschied; BIC mit `p*log(n) <= 26,5` ebenfalls zu schwach). Stattdessen darf ein Kind seinen Elternteil nur ueberholen, wenn die Residuenverbesserung groesser ist, als ein zusaetzlicher Parameter zufaellig liefern wuerde. Umsetzung als Gate mit zwei Raengen, innerhalb der Gruppen weiter nach Residuum. Erfordert, dass die Kindergenerierung die Herkunft eines Kandidaten bis zur Bewertung mitfuehrt.

**Pflicht-Nachweis der Wirksamkeit.** Die AIC-Runde ist daran gescheitert, dass die Intervention die Rangfolge nicht bewegt hat und das erst hinterher auffiel. Diesmal muss der Lauf selbst protokollieren, in wie vielen Faellen sich die ausgewaehlte Kandidatenmenge von der des reinen Residuen-Scores unterscheidet. Ist der Wert null, ist die Intervention wirkungslos und das ist sofort erkennbar.

**Intervention 2 — Polish-Start entkoppeln.** Der LS-Fit erfuellt heute zwei Rollen: Screening-Score und Startpunkt fuers Nachpolieren. Die zweite ist nach WP-T1 schaedlich. Kuenftig konfigurierbar, mit dem Startpunkt des Referenzpfads als Alternative; der LS-Fit dient dann nur noch der Bewertung.

**Rangeuebereinstimmung repariert:** ausweisen, auf wie vielen Leveln ueberhaupt ein endlicher Wert zustande kam, Mittelwert nur ueber diese, dazu Median und Spannweite. Der Verdacht aus WP-P2.3 (rho auf den meisten Leveln `NaN`, Mittelwert von wenigen Leveln getragen) wird damit pruefbar.

**Vergleichslauf mit vier Bedingungen** je System (3 und 11, Seed 42, 30 Level, Bewertungstoleranz **1e-8**, damit System 11 ueberhaupt oberhalb der Rauschgrenze liegt): A Referenz, B Screening mit Residuen-Score und LS-Start (heutiges Verhalten als Kontrolle), C geschachtelter Test mit LS-Start, D geschachtelter Test mit entkoppeltem Start. C gegen B zeigt den Penalty, D gegen C den Startpunkt. Dazu eine Ankerpruefung des Referenzpfads bei 1e-6 gegen Baseline v0.

Drei Fragen sind im Bericht ausdruecklich zu beantworten: veraendert der Test die Auswahl ueberhaupt, verschwindet die Stage-Eskalation auf System 3, und entkommt Bedingung D dem Becken bei 3,236e-08.

Aus WP-T1 vermerkt, aber ausdruecklich **nicht** Teil dieses WP: der Sentinel-Loss `1e6` mit Retcode `Success` bei vollstaendig gescheitertem Fit, die pathologische Line-Search mit bis zu 39.933 Auswertungen bei zwei Parametern, und die Frage, ob die Bewertungstoleranz im Regression-Runner dauerhaft auf 1e-8 gehen soll.

<!-- 9db9741 -->

### WP-T1 gelaufen — Toleranz-Hypothese fuer System 11 bestaetigt, fuer System 3 widerlegt; vier Befunde

Committet `a6919ca`. Diagnose auf Systemen 3 und 11 bei fester bekannt-korrekter Struktur, Toleranzraster {1e-5, 1e-6, 1e-8, 1e-10, 1e-12} im Bewertungspfad, Trajektorienerzeugung unveraendert 1e-9.

**Befund 1 — System 11: berichteter Loss ist numerisches Rauschen.** Erreichter Loss aus dem LS-Warmstart je Toleranz: 8,435e-14 (1e-5), 4,606e-15 (1e-6), 1,669e-17 (1e-8), 4,860e-18 (1e-10), 4,856e-18 (1e-12). Der Wert skaliert also unmittelbar mit der Solver-Toleranz und saettigt erst bei ~5e-18. Baseline v0 meldet **4,402192340718147e-15** — genau das Niveau der 1e-6-Toleranz. Teil A verschaerft das: mit den **wahren** Parametern erreicht man bei 1e-6 nur 1,859e-14, der Fit liefert also 4,6e-15 und damit ein *besseres* Ergebnis als die Wahrheit. Das ist nur moeglich, wenn numerisches Rauschen gefittet wird. Der in Baseline v0, in Phase A und in allen heutigen Regressionspruefungen gefuehrte System-11-Loss ist nicht interpretierbar.

**Befund 2 — System 3: Hypothese widerlegt.** Aus dem LS-Warmstart landet der Fit bei **3,236e-08 bei jeder Toleranz von 1e-6 bis 1e-12**, voellig flach. Sechs Groessenordnungen engere Toleranz aendern nichts. Der Boden aus Teil A liegt bei 1e-6 bei 4,401e-12, das Ergebnis also rund 7.000-fach darueber. Hier ist nicht die Numerik die Grenze, sondern der Optimierer bzw. die Landschaft.

**Befund 3 — die eigentliche Ursache des Screening-Versagens auf System 3.** Der LS-Warmstart konvergiert auf 3,236e-08 — exakt der Wert, bei dem die Screening-Variante haengenblieb (3,2363742537347274e-8). Der Referenzlauf erreicht dagegen 2,66e-10, und er benutzt **keinen** Warmstart (`USE_PRETUNING = false`). Das Screening-Versagen ist damit kein Toleranz- und kein Ranking-Problem, sondern: **der ableitungsbasierte Least-Squares-Warmstart fuehrt auf System 3 in ein Becken, aus dem BFGS nicht herausfindet.** Die Screening-Variante fuehrt damit genau das wieder ein, was die Regression-Konfiguration bewusst abgeschaltet hat.

**Befund 4 — pathologische Line-Search.** Auf System 3 verbrauchen einzelne Fits bei zwei Parametern **39.933 / 37.933 / 39.065** Loss-Auswertungen (jede eine vollstaendige Integration) mit Retcode `Failure`, Laufzeiten 3,2 / 10,4 / 23,6 s — bei `maxiters = 200`, also rund 200 Auswertungen pro Iteration fuer ein Zweiparameterproblem. Erratisch: bei 1e-6 und 1e-8 braucht derselbe Startpunkt nur 585 bzw. 257 Auswertungen. Das erklaert die 7.281 Integrationen pro Fit aus der Regressionsmessung.

**Nebenbefund:** Der Standardstart liefert auf System 3 bei mehreren Toleranzen `final_loss = 1.000e+06` nach 5 Auswertungen mit Retcode **`Success`**. 1e6 ist der Initialwert `l_best` in `fit_parameters` — ein vollstaendig gescheiterter Fit wird also als Erfolg mit Sentinel-Loss gemeldet und ist von einem echten schlechten Fit nicht unterscheidbar.

**Kosten (Teil C, pretune-Start, hochgerechnet auf 20 Fits pro Level):** System 3 — 0,48 s bei 1e-6, 0,64 s bei 1e-8, 1,38 s bei 1e-10, 6,00 s bei 1e-12. System 11 — 0,06 / 0,12 / 0,08 / 0,22 s. **Die Verschaerfung von 1e-6 auf 1e-8 kostet also rund Faktor 1,3 und hebt den System-11-Boden von 1,86e-14 auf 1,36e-17**, womit alle berichteten Losses wieder oberhalb der Rauschgrenze liegen. Empfehlung: Bewertungstoleranz auf 1e-8. Zur Einordnung: die WP-P1b-Screening-Budgets setzen 1e-5 und druecken den System-3-Boden auf 2,06e-10, also auf Faktor 1,29 an den dort berichteten Loss heran — fuer billige Systeme zu grob, fuer System 26 (Loss ~1,4e-3) unkritisch.

<!-- a6919ca, f327de6 -->

### Screening-Spur wieder aufgenommen; WP-T1 (Toleranz-Rauschgrenze) vorgezogen

User hat die Abbruchentscheidung revidiert: Zeit ist doch da, und im Projekt geht es um wissenschaftliche Fundierung, nicht um Schnelligkeit. Gewuenscht sind beide offenen Faeden — harter Penalty **und** Toleranzanalyse.

**Reihenfolge festgelegt: Toleranz zuerst.** Begruendung: Die beiden Faeden sind nicht unabhaengig. Die Ursachenkette auf System 3 lautete „Loss bleibt bei 3,24e-8 -> ueber `loss_tol = 1e-8` -> kein Abbruch -> Eskalation auf Stage 5 -> teurere Kandidaten -> netto langsamer". Wenn der Loss dort nicht wegen schlechter Kandidatenauswahl haengenblieb, sondern weil der Optimierer im Bereich unter der Solver-Toleranz blind ist, dann ist **das gesamte beobachtete Versagen der Screening-Variante ein Toleranz-Artefakt**. Ein Test des Auswahlkriteriums unter unkontrolliertem Confounder waere wertlos.

**Die Frage ist groesser als die Screening-Spur.** System 11 meldet in Baseline v0 einen Loss von 4,402192340718147e-15, also rund 6,6e-8 mittleren Fehler pro Punkt — deutlich unterhalb der Genauigkeit, mit der der Bewertungspfad (`abstol = reltol = 1e-6`) diese Trajektorie berechnet. Die Zahl steht in Baseline v0, in der Phase-A-Auswertung und in jeder heutigen Regressionspruefung. Ist sie numerisches Rauschen, betrifft das die Belastbarkeit der berichteten Losses im gesamten Projekt und die Frage, ob `loss_tol = 1e-8` als Abbruchkriterium sinnvoll definiert ist.

**WP-T1 beauftragt:** Diagnose-Experiment unter `studies/numerics/`, Systeme 3 und 11, feste bekannt-korrekte Struktur, Toleranzraster {1e-5, 1e-6, 1e-8, 1e-10, 1e-12} im Bewertungspfad bei unveraenderter Trajektorienerzeugung (1e-9). Teil A misst ohne Optimierer den bestmoeglich erreichbaren Loss je Toleranz (Belastbarkeitsgrenze der berichteten Werte), Teil B laesst `fit_parameters` je Toleranz aus drei Startpunkten laufen — Standardstart, LS-Warmstart, und wahre Parameter mit 1 % Stoerung als schaerfsten Test —, Teil C beziffert den Preis der Genauigkeit. 1e-5 ist im Raster, weil die WP-P1b-Screening-Budgets diesen Wert setzen.

Falsifizierbare Vorhersage in der Spec: bei 1e-6 bleibt der Warmstart stehen und meldet `Success` nach wenigen Auswertungen, bei 1e-10 verbessert er sich. Tritt das nicht ein, ist die Vermutung widerlegt und wir gehen direkt zum Screening-Test.

**Danach WP-P2.4:** harter Penalty statt AIC. Richtung: kein Informationskriterium — bei n = 200 ist jedes vom Fit-Term dominiert —, sondern ein Nested-Model-Test, bei dem ein Kind seinen Elternteil nur schlaegt, wenn die Residuenverbesserung groesser ist, als ein zusaetzlicher Parameter zufaellig liefern wuerde. Das adressiert die Monotonie-Falle direkt statt sie mit einer Konstanten zu ueberstimmen. Plus Reparatur der rho-Kennzahl. WP-v3.3 bleibt bis dahin liegen.

<!-- b37e457 -->

### Entscheidung: Screening-Spur eingestellt; zurueck zu WP-v3.3

User hat die Abbruchregel wie vereinbart gezogen. Die Screening-Spur (WP-P2.1 bis WP-P2.3) wird eingestellt.

**Was bleibt:** `docs/evogrow_screening_design.md`, `src/structure/evogrow_screening.jl`, `studies/debug/compare_screening_variant.jl` und die Messdaten bleiben im Repository als dokumentierte Zwischenablage. Nicht ohne neue Evidenz wieder aufnehmen.

**Was gesichert ist:** 2,71x aus WP-P1b (Solver-Budgets, System 26), Determinismus im Regression-Ergebnispfad, vollstaendige Kosteninstrumentierung pro Level, und ein quantifiziertes Kostenprofil des Bewertungspfads.

**Ehrliche Einordnung der Falsifikation:** Sie ist weich. Die AIC-Intervention war mathematisch zu schwach, um die Rangfolge ueberhaupt zu bewegen, und die rho-Kennzahl ist fragwuerdig. Die Hypothese „ableitungsbasiertes Screening taugt als Auswahlsignal" ist damit nicht widerlegt, sondern ungeprueft. Eingestellt wurde aus Aufwandsgruenden, nicht aus wissenschaftlicher Klaerung — das gehoert so in eine spaetere Diskussion, falls die Spur wieder aufgenommen wird.

**CLAUDE.md aktualisiert:** Prioritaeten auf Stand 2026-07-22, WP-P1.x als erledigt und WP-P2.x als eingestellt vermerkt, offene Toleranz-Hypothese als ungeplanter Punkt festgehalten.

**Offener Punkt vor der naechsten Baseline:** Die Regression-Konfiguration hat sich seit Baseline v0 geaendert (expliziter `time_limit_s`, zusaetzliche Fingerprint-Felder). Baseline v0 bleibt als historischer Datensatz gueltig, aber vor einer Regressionspruefung von v3.3-Ergebnissen muss eine neue Baseline unter der aktuellen Konfiguration gerechnet werden.

**WP-v3.3 beauftragt** (Designnotiz Abschnitt 6): gleichungsweise Kindergenerierung, zulaessige Terme aus `eq_stages[k]` statt aus einer globalen Stage, Kreuzterm-Regel `min(eq_stages[i], eq_stages[j])`, `StageUsagePolicy` pro Gleichung. Zentraler Punkt der Spec: da WP-v3.4 (gleichungsweise Promotion) noch aussteht, sind alle `eq_stages` weiterhin gleichgeschaltet — der Umbau muss daher **bit-identische** Ergebnisse liefern und ist ein verhaltensneutraler Refactor, dessen Wirkung erst mit v3.4 sichtbar wird. Ausdruecklich mitspezifiziert: die RNG-Ziehreihenfolge darf sich nicht aendern, sonst ist das Kriterium nicht pruefbar. Zusaetzlich wird die Screening-Variante aus `VARIANTS` im Regression-Runner entfernt.

Nebenbefund beim Lesen der Designnotiz: Abschnitt 9 fuehrt die Kreuzterm-Frage als offen, obwohl Abschnitt 6 sie bereits beantwortet. In der Spec als entschieden festgehalten, mit der Konsequenz im Docstring: ein Kreuzterm haengt an den Stages der Gleichungen seiner **Variablen**, nicht an der Stage der verwendenden Gleichung — die einzige Stelle, an der die Gleichungen gekoppelt bleiben.

<!-- afbc065 -->

### WP-P2.3 gelaufen — Abbruchregel ausgeloest, aber der Test war zu schwach, um die Hypothese zu pruefen

Committet `9ca9127`. Codex hat `screening_score = :residual | :aic` eingebaut und — besser als von mir spezifiziert — die Rangeuebereinstimmung auf den **tatsaechlich verwendeten Score** umgestellt statt weiter das rohe Residuum zu vergleichen.

| System 3 | Referenz | Screening residual | Screening AIC |
|---|---|---|---|
| Laufzeit | 370,8 s | 460,1 s | **239,0 s** |
| Loss | 2,66e-10 | 3,2363742537347274e-8 | **3,2363742537347274e-8** |
| `final_stage` | 3 | 5 | **5** |
| Integrationen | 1.529.009 | 711.757 | 510.539 |
| Rangeuebereinstimmung | — | −0,7777777777777778 | **−0,7777777777777778** |

System 11: beide Screening-Bedingungen identisch zum vorigen Lauf, rho +1,0, korrekte Struktur, 1,37–1,47x schneller.

**Die Abbruchregel ist ausgeloest** — rho auf System 3 bleibt negativ. Der Test taugt aber nicht als Falsifikation, und zwar aus einem Grund, den ich in der Spec haette vorhersehen muessen:

**AIC ist hier faktisch eine monotone Transformation des Residuums.** `AIC = n*log(mse) + 2p` mit `n = 200` Beobachtungen: der Fit-Term aendert sich um 19 Einheiten schon bei 10 % Residuenunterschied und um 139 bei Faktor 2, waehrend die Komplexitaetsstrafe ueber den gesamten Bereich `p = 1..6` hoechstens **10** Einheiten betraegt. Spearman ist gegen monotone Transformationen invariant — die Rangfolge kann sich also praktisch nicht aendern. Belegt durch die Daten: Loss bit-identisch, `final_stage` identisch, `total_parameter_fits` identisch, rho bit-identisch. Die Intervention hat die Auswahl nicht bewegt. BIC waere mit `p*log(n) <= 26,5` ebenfalls zu schwach. Bei n = 200 Datenpunkten ist **jedes** Standard-Informationskriterium vom Fit-Term dominiert.

**Zweiter Zweifel an der Messgroesse:** rho betraegt in beiden Bedingungen exakt −7/9, obwohl sich Laufzeit (460 vs 239 s), Integrationen (711.757 vs 510.539) und Konvergenzfehler (106 vs 79) deutlich unterscheiden. Das passt schlecht zu einer stabilen Kennzahl und gut zu der Vermutung, dass rho auf den meisten Leveln `NaN` ist (alle simulierten Losses gleich -> `denom == 0`) und der berichtete Mittelwert von sehr wenigen Leveln getragen wird. Ungeprueft, aber die Kennzahl ist damit als Entscheidungsgrundlage fragwuerdig.

**Neuer Befund zum wirkungslosen finalen Refit:** Die Diagnostik zeigt `final_refit_method = BFGS`, `final_refit_retcode = Success`, `final_refit_loss_evals = 5`, keine Failure-Hits. BFGS kehrt also nach fuenf Auswertungen als *konvergiert* zurueck. Der Verdacht: die ODE-Solver-Toleranz im Bewertungspfad betraegt `abstol = reltol = 1e-6`, waehrend der Loss bei ~3e-8 liegt. Finite-Differenzen-Gradienten einer Groesse, die nur auf 1e-6 genau berechnet wird, sind in diesem Bereich Rauschen — der Optimierer sieht keinen Abstieg mehr. Das waere kein Screening-Problem, sondern eine Eigenschaft des gesamten Bewertungspfads und beruehrt auch Pretuning-Warmstarts und die Frage, ob `loss_tol = 1e-8` ueberhaupt zuverlaessig erreichbar ist. Als Hypothese notiert, nicht als Befund.

**Bilanz der Screening-Spur:** AIC-Screening ist auf beiden Systemen schneller als der Referenzpfad (1,55x auf System 3, 1,37x auf System 11), liefert aber auf System 3 einen um Faktor 121 schlechteren Loss und eskaliert auf Stage 5 statt 3. In dieser Form nicht verwendbar.

<!-- 9ca9127, 96ac621 -->

### WP-P2.2c gelaufen — erste echte Zahlen: System 11 funktioniert, System 3 falsifiziert das Kriterium

Vergleichsskript `studies/debug/compare_screening_variant.jl` committet (`2eb7202`) und ausgefuehrt. Konfiguration identisch zur Regression-Suite (30 Level, pop 10, λ=1e-3, BFGS 200, Seed 42).

| | System 3 Referenz | System 3 Screening | System 11 Referenz | System 11 Screening |
|---|---|---|---|---|
| Laufzeit | 357,6 s | **400,9 s** | 3,63 s | **2,36 s** |
| Loss | 2,66e-10 | **3,24e-8** | 4,402e-15 | 4,407e-15 |
| `final_stage` | 3 | **5** | 4 | 4 |
| `pruned_match` | true | true | true | true |
| Integrationen | 1.529.009 | 711.757 | 8.942 | 10.599 |
| Kosten/Integration | 0,172 ms | **0,490 ms** | — | — |
| Rangeuebereinstimmung | — | **−0,78** | — | **+1,00** |

Referenzpfad reproduziert in beiden Zellen exakt Baseline v0 (Loss und `final_stage` geprueft).

**System 11 funktioniert:** korrekte Struktur `-u1^3` gefunden, Faktor 1,53 schneller, Rangeuebereinstimmung +1,0, kein erschoepftes Polish-Budget, kein abgelehnter Kandidat haette gewonnen.

**System 3 falsifiziert das Kriterium in seiner jetzigen Form.** Rangeuebereinstimmung −0,78: der Screening-Score ordnet nahezu **umgekehrt** zum simulierten Loss. Belegte Ursachenkette: (1) der Loss bleibt bei 3,24e-8 und damit ueber `loss_tol = 1e-8`, die absolute Abbruchbedingung feuert nie, waehrend der Referenzlauf bei 2,66e-10 abbricht und auf Stage 3 bleibt; (2) die Suche eskaliert bis Stage 5, also trigonometrische Terme und steifere Kandidaten-ODEs — Kosten pro Integration 0,490 ms gegen 0,172 ms, Faktor 2,85, womit die eingesparten Integrationen mehr als aufgefressen werden; (3) der finale Refit auf vollem Budget dauert **0,001 s** und bewirkt nichts, obwohl beide Varianten dieselbe Struktur finden (`du1/dt = 0.790*u1 + -0.011*u1^2`, beide `pruned_match = true`) — der Loss-Unterschied stammt allein aus den Parametern.

**Vermutete Ursache der negativen Rangeuebereinstimmung:** Kinder entstehen durch Hinzufuegen von Termen, sind also geschachtelte Obermengen ihrer Eltern. Fuer geschachtelte Least-Squares-Probleme ist das Residuum monoton nicht-steigend in der Termzahl — ein groesseres Modell kann nie ein schlechteres LS-Residuum haben. Der Screening-Score enthaelt aber nur einen Tiebreak von `1e-12 * n_params`, waehrend das Suchziel mit `λ = 1e-3` bestraft. Der Score bevorzugt damit systematisch die groessten Kandidaten, was sowohl die negative Rangeuebereinstimmung als auch die Stage-Eskalation erklaert.

**Befund gegen die Praemisse des Kostenmodells:** `polish_budget_exhausted = 0` in **allen** Laeufen. Das 20-Iterationen-Budget wurde nie ausgeschoepft; BFGS terminiert vorher, in 106 von 200 Faellen mit Konvergenzfehler. Die Einsparung von 200 auf 20 Iterationen existiert also gar nicht, weil der Referenzpfad die 200 ebenfalls nie erreicht. Passend dazu sinken die Integrationen pro Fit nur von 7.281 auf 2.953 (Faktor 2,5) trotz zehnfach kleinerem Iterationsbudget — die Zahl der Integrationen wird offenbar nicht vom Iterationslimit getrieben.

**WP-P2.3 beauftragt als letzter Versuch, mit Abbruchregel:** komplexitaetsbewusster Screening-Score (skalenfreies Informationskriterium; ein Uebernehmen von `λ` waere falsch, weil dort ein Simulations-MSE und hier ein Ableitungsresiduum bestraft wird), Untersuchung des wirkungslosen finalen Refits, und Wiederholung der Messung mit drei Bedingungen je System (Referenz, alter Score als Kontrolle, neuer Score). Bleibt die Rangeuebereinstimmung auf System 3 negativ, gilt das Kriterium als falsifiziert und die Arbeit daran wird eingestellt; es bleiben die 2,71x aus WP-P1b.

<!-- 2eb7202, 61e6459 -->

### WP-P2.2b reviewt — Code korrekt, aber nie ausgefuehrt; WP-P2.2c beauftragt

Committet `7f52676`. Alle sechs Punkte korrekt behoben: `screening_budgets_active` behaelt seine urspruengliche Bedeutung und wird aus der Strategie abgeleitet, `derivative_screening_active` als eigenes Feld ergaenzt und im Record gefuehrt; der Runner reicht den `screening_optimizer` jetzt durch. Erschoepfung wird am Iterationslimit gemessen, Konvergenzfehler getrennt gezaehlt. Diagnose-Stichprobe abgelehnter Kandidaten implementiert — geprueft: sie wird nur gemessen, nie nach `polished` geschrieben, beeinflusst die Suche also nicht; `rejected_beats_best_selected` zaehlt die relevanten Faelle. `screen_k < pop_size` wird abgelehnt statt still zu schrumpfen. Struct-Defaults auf `EvoGrow` angeglichen. Finaler Refit ueber `_add_fit_stats!` in den Summen. Monotonie-Abweichung und leere `vis_history` im Docstring dokumentiert. Keine doppelten Funktionsdefinitionen; Include-Reihenfolge stimmt.

**Zwei kleinere Restpunkte:** (i) `screen_k` ist faktisch inert — die Validierung verbietet Werte unter `pop_size`, der Clamp `min(..., pop_size)` verbietet Werte darueber, also ist `screen_k` immer exakt `pop_size`. Damit faellt die in der Design-Notiz genannte Eigenschaft weg, durch Erhoehen von k zum heutigen Verhalten zu degradieren — eine nuetzliche Kontrollvariante. (ii) Die Diagnose-Stichprobe nimmt die **bestplatzierten** abgelehnten Kandidaten, also die knapp Gescheiterten. Das ist die trennschaerfste Wahl fuer Fehler an der Auswahlgrenze, erkennt aber nicht den Fall, dass ein Kandidat mit schlechtem Screening-Score gut simuliert haette. Als dokumentierte Einschraenkung vertretbar.

**Der eigentliche offene Punkt: die Variante ist nie ausgefuehrt worden.** Die in WP-P2.2 und WP-P2.2b jeweils ausdruecklich geforderten Messzahlen wurden beide Male nicht geliefert, und im Repository liegen keine Artefakte eines Verifikationslaufs (`history.jsonl` unveraendert bei 23 Zeilen, keine neuen Ausgaben). Statisch sieht der Code korrekt aus — ob er laeuft und ob das Ableitungskriterium als Auswahlsignal taugt, ist unbekannt.

**WP-P2.2c beauftragt:** wiederverwendbares Vergleichsskript unter `studies/debug/` (Systeme 3 und 11, Seed 42, Referenzpfad gegen Screening-Variante, Level-Budget 30 wie Baseline v0), ausfuehren, und vier Fragen mit Zahlen beantworten: laeuft es durch, findet es `-u1^3` auf System 11, wie hoch ist der Anteil erschoepfter Polish-Budgets, wie faellt die Rangeuebereinstimmung aus. Zusaetzlich Gegenprobe, dass der Referenzpfad weiterhin die Baseline-v0-Werte liefert. Wiederverwendbar statt einmalig, weil dieselbe Pruefung bei WP-v3.3 erneut gebraucht wird.

<!-- 7f52676, ee74602 -->

### WP-P2.2 umgesetzt und reviewt — drei Blocker, WP-P2.2b beauftragt

`src/structure/evogrow_screening.jl` committet (`07aee5e`). Kern korrekt: finaler Refit auf vollem Budget vorhanden, Stopplogik und Promotion bekommen `best.loss` (simulierter Loss), Incumbent wird immer mitgezogen, ungueltige Screening-Faelle explizit markiert und gezaehlt, `pretune_parameters` verhaltensgleich, `evogrow.jl` / `evogrow_v3.jl` / `discover.jl` / `stopping.jl` unangetastet. Kinder werden mit `objective = Inf` initialisiert — geprueft, damit kann der Revert-Schutz keine unbewerteten Kinder in die Population heben. Spearman mit Ties-Korrektur ueber Durchschnittsraenge korrekt implementiert.

**Blocker 1 — Feldkollision `screening_budgets_active`.** Die Variante gibt das Feld fest als `true` zurueck. In WP-P1b wurde es mit anderer Bedeutung eingefuehrt („reduzierte Solver-Budgets aktiv") und wandert aus dem Meta in den Record. Damit laesst sich in `history.jsonl` nicht mehr unterscheiden, ob ein Record mit Solver-Budgets oder mit Ableitungs-Screening lief. Verschaerfend: der Runner-Konstruktor nimmt `screening_optimizer` entgegen und verwirft ihn — die Variante nutzt die Solver-Budgets gar nicht, korrekt waere also `false`. Dieselbe Defektklasse wie WP-P1b B1, unter anderem Namen.

**Blocker 2 — Polish-Erschoepfung mit falschem Zaehler.** Erkennung ueber `optimizer_limit_hits > 0`; dieser Zaehler steigt bei **jedem** Nicht-Success-Retcode. Belegt am System-3-Benchmark: `optimizer_failure_hits = 95` bei 210 Fits, `optimizer_iteration_limit_hits = 0`. Die Kennzahl wuerde also nahezu durchgaengig „Budget erschoepft" melden, unabhaengig vom Budget — und genau sie entscheidet, ob die Losses mit dem Simulationspfad vergleichbar sind.

**Blocker 3 — die Rangeuebereinstimmung kann ihre Frage nicht beantworten.** Spearman wird nur ueber die **ausgewaehlten** Kandidaten berechnet, also ueber eine per Konstruktion auf gute Screening-Scores eingeschraenkte Menge. Gemessen wird damit die Uebereinstimmung unter den Ueberlebenden, nicht ob die Vorauswahl gute Kandidaten verwirft — das zentrale Methodenrisiko aus Abschnitt 6 der Design-Notiz. Der Vergleichslauf koennte durchlaufen und die Frage bliebe offen. Korrektur: kleine Stichprobe **abgelehnter** Kandidaten mitpolieren und simulieren, rein diagnostisch, ohne Einfluss auf die Suche.

**Kleinere Befunde:** (i) `pop` wird aus `polished` gebildet, das hoechstens `screen_k` Eintraege hat — bei `screen_k < pop_size` kollabiert die Population still auf `screen_k`. (ii) Struct-Default `usage = :soft` weicht von `EvoGrow`, `EvoGrowV3` und allen drei Runner-Varianten (`:hard`) ab. (iii) Der finale Refit wird nicht ueber die Fit-Statistik verbucht; `total_ode_solves` und `total_simulation_time_s` schliessen ihn aus. (iv) Wird ein Elternteil durchs Polieren schlechter, behaelt die Variante den alten Wert — `EvoGrow` kennt diesen Schutz nicht. Dadurch ist die Objective-Folge hier monoton, dort nicht, was Plateau-Erkennung und Promotion beruehrt; vertretbar, aber dokumentationspflichtig. (v) `vis_history` wird angelegt und zurueckgegeben, aber nie gefuellt.

**Nicht berichtet:** die in WP-P2.2 geforderten Verifikationszahlen (Laufzeit, Polish-Erschoepfung, Rangeuebereinstimmung, System 11 exakt gefunden?) liegen nicht vor, und im Repo sind keine Artefakte eines Verifikationslaufs. In WP-P2.2b sind die gemessenen Zahlen ausdruecklich Teil des Deliverables.

<!-- 07aee5e, f5f4e4e -->

### WP-P2.2 beauftragt — Screening-Variante mit begrenztem Nachpolieren

Architektur festgelegt. Reines Screening ohne Simulation waere am billigsten, macht aber die Stopplogik unbrauchbar: Parameter aus dem Ableitungs-LS sind nicht fuer das Simulationsziel optimiert, und `plateau_tol = 1e-4` sowie `loss_tol = 1e-8` sind auf BFGS-optimierte Losses kalibriert. Loesung ist ein **begrenztes Nachpolieren** der ausgewaehlten Kandidaten, ausgehend von den LS-Parametern.

Kostenmodell aus den Messwerten (4.707 Solves pro Fit bei 200 Iterationen -> 23,5 Solves/Iteration -> 41,5 ms/Iteration; heute 170,9 s pro Level):

| k | Polish-Iterationen | Kosten/Level | Solve-Faktor |
|---|---|---|---|
| 10 | 0 | 0,02 s | Stopplogik kaputt |
| 10 | 10 | 4,2 s | 41x |
| 10 | 20 | 8,3 s | 21x |
| 5 | 20 | 4,2 s | 41x |
| 10 | 50 | 20,8 s | 8x |

Nach Abzug des Overhead-Bodens von 153 s realistische Gesamterwartung **10–15x** auf dieser Zelle, nicht die 21x der theoretischen Untergrenze. Das ist die Zahl, an der die Umsetzung zu messen ist.

Ablauf pro Level: alle Kandidaten per Screening-Score bewerten (kein BFGS, keine Simulation), die besten k plus den Incumbent auswaehlen, nur diese mit begrenztem Budget nachpolieren und simulieren, nur simulierte Kandidaten duerfen in die Population. Plateau, Stopplogik und Promotion laufen **ausschliesslich** auf simuliertem Loss — die Trennung aus Abschnitt 4 der Design-Notiz. Der berichtete `loss` bleibt ein simulierter Loss auf voller Genauigkeit, die Endstruktur wird einmal mit vollem Budget nachgefittet.

Zwei Messgroessen als Pflicht: (i) wie viele ausgewaehlte Kandidaten ihr Polish-Budget ausschoepfen — durchgaengiges Ausschoepfen bedeutet, die Losses sind nicht mit dem Simulationspfad vergleichbar; (ii) **Rangeuebereinstimmung** zwischen Screening-Score und simuliertem Loss unter den simulierten Kandidaten — die Messgroesse fuer das zentrale Methodenrisiko (Zielkonflikt), ohne die sich nicht beurteilen laesst, ob die Vorauswahl gute Kandidaten verwirft.

Neue Variante neben dem bestehenden Pfad, kein Ersatz. `pretune.jl` wird um eine Score-Funktion mit Gueltigkeitsflag erweitert; `pretune_parameters` selbst bleibt verhaltensgleich. Verifikation nur auf System 3 und 11.

<!-- 64d9e3d -->

### WP-P2.1 Design-Notiz reviewt — tragfaehig, aber ohne Kostenmodell; Faktor 10 haengt an einem Wort

`docs/evogrow_screening_design.md` committet (`97e0dbe`). Alle neun Pflichtabschnitte vorhanden. Saemtliche Zahlen gegen `summary.json` geprueft und korrekt, inklusive der 21x als `3222,6 / 153,0`. API-Referenzen auf `pretune.jl` stimmen (Signaturen von `estimate_derivatives`, `build_design_matrix`, Per-Gleichungs-LS geprueft). Abschnitt 4 und 7 beziehen klare Position: Stage-Promotion bleibt am simulierten Loss verankert, und der Beitrag bleibt nur dann von SINDy unterscheidbar, wenn staged incremental growth Untersuchungsgegenstand bleibt und der simulierte Loss die berichtete Metrik.

**Luecke: kein Kostenmodell fuer den vorgeschlagenen Entwurf.** Die Notiz begruendet sich mit der 21x-Obergrenze, schaetzt aber nie, was ihr eigener Vorschlag kostet. Abschnitt 3 empfiehlt „alle Kandidaten screenen, die besten k pro Level simulieren" mit `k = pop_size` als Kandidatenregel — laesst aber offen, was „simulieren" fuer diese k bedeutet. Aus den gemessenen Groessen (Fall A: 370 Fits ueber 18 Level, 4.707 Solves pro Fit, 1,763 ms pro Solve, 8,30 s Solve-Zeit pro Fit, 0,41 s Overhead pro Fit):

| Variante pro Level (20,6 Kandidaten) | Kosten | Faktor |
|---|---|---|
| heute: alle per BFGS mit Simulation | 170,5 s | 1,0x |
| (b) Top k=10 per BFGS mit Simulation | 83,0 s | 2,1x |
| (b) Top k=5 per BFGS mit Simulation | 41,5 s | 4,1x |
| (a) Top k=10 je **eine** Simulation der LS-Parameter | 0,018 s | Solve-Kosten praktisch null |

Hochrechnung auf den ganzen Lauf: heute 3223 s, Variante (b) mit k=10 rund 1646 s (**2,0x**), Variante (a) rund 153 s (**21,1x**, Untergrenze Overhead + LS). **Der Unterschied zwischen 2x und 21x steckt in einem einzigen unausgesprochenen Wort.** Die Quelle des Speedups ist nicht das Screening an sich, sondern dass die geschlossene LS-Loesung die rund 200 BFGS-Iterationen mit je ~25 Solves pro Kandidat ersetzt. Die Notiz impliziert das, sagt es aber nirgends.

**Synthese, die die Notiz nicht zieht:** Variante (a) erfuellt die Forderung aus Abschnitt 4 mit. Eine Simulation pro ausgewaehltem Kandidaten kostet 1,763 ms; damit bleibt ein simulierter Loss-Anker fuer Plateau-Erkennung und Stage-Promotion pro Level erhalten, ohne die Kosten messbar zu erhoehen. Die 21x und die Anforderung „Promotion bleibt am simulierten Loss verankert" stehen also **nicht** im Konflikt. Offene Entscheidungen 1–3 sind damit auf Evidenzbasis beantwortbar.

**Kleinere Befunde:** (i) Abschnitt 6 nennt als Falsifikation „ein wiederholtes Muster" ohne Schwelle und ohne benannten Test; ist als offene Entscheidung 7 deklariert und damit spec-konform, fuer ein Abbruchkriterium aber zu weich. (ii) `USE_PRETUNING = false` im Regression-Config wird nicht erwaehnt — der gesamte Entwurf ruht auf Maschinerie, die in genau der Konfiguration abgeschaltet ist, die die Messung erzeugt hat. (iii) `pretune_parameters` liefert `zeros(n)`, sobald eine Gleichung nicht-endliche Werte oder `norm > 1e6` ergibt. Als Warmstart harmlos, als Screening-Score faellt ein entarteter Kandidat damit still auf „alle Parameter null" statt als ungueltig markiert zu werden. Die Notiz nennt fehlende Failure-Flags korrekt, aber nicht diese konkrete Falle im wiederverwendeten Code.

<!-- 97e0dbe, a9043e0 -->

### Loss konvergiert in allen Zellen bis Level 18 — Level-Cap trotzdem abgelehnt; WP-P2.1 beauftragt

Rekonstruktion aus dem v0-`run.log` (`best_loss` pro Level, alle 23 Zellen, keine neuen Laeufe noetig): **13 Zellen liefen ueber Level 18 hinaus, und in allen 13 war der Loss bei Level 18 bereits identisch zum Endergebnis.** Kein Level nach 18 hat je etwas verbessert. Kosten dieser Level: **15,8 von 40,5 h = 39 % der gesamten Rechenzeit**.

**Entscheidung: Level-Budget bleibt bei 30.** Der User hatte einer Kuerzung auf 18 zugestimmt, ich habe die Empfehlung zurueckgezogen. Grund: der Loss bliebe identisch, `final_stage`, `stage_overshoot` und `wasted_levels` aber nicht. System 26 Seed 42 bei 30 Leveln Stage 5 / Overshoot 2 / 8 wasted; bei 18 Leveln Stage 3 / Overshoot 0. Das sind die H1- und H3-Metriken. Ein Level-Cap wuerde das Overshoot-Phaenomen wegschneiden statt es zu messen — also genau das, was v3 beheben soll. Meine urspruengliche Optionsbeschreibung hatte diese Konsequenz nicht genannt.

**Der Befund gehoert stattdessen in den v3-Entwurf.** Der Loss konvergiert in jeder Zelle bis Level 18, die Suche laeuft aber bis Level 26–29 weiter, weil Plateau-Erkennung Stage-Promotion ausloest statt Terminierung. Die Suche kann nicht aufhoeren, solange Stages uebrig sind — sie eskaliert stattdessen. Das ist ein Befund ueber die Stopp- und Promotionsregel, kein Konfigurationsproblem: die Promotionsregel braucht ein Kriterium, das erkennt, wann zusaetzliche Komplexitaet nichts mehr bringt, nicht nur wann der Fortschritt stockt.

**WP-P2.1 beauftragt:** Design-Notiz `docs/evogrow_screening_design.md` fuer ein ableitungsbasiertes Screening-Kriterium, analog zum Vorgehen bei WP-v3.1 (erst Entwurf, dann Code). Neun Pflichtabschnitte; kritisch sind Abschnitt 4 (Stopplogik, Plateau-Erkennung und Stage-Promotion arbeiten heute auf dem Simulations-Loss — welches Signal traegt sie kuenftig?) und Abschnitt 7 (Verhaeltnis zum wissenschaftlichen Beitrag: ableitungsbasierte Bewertung rueckt naeher an SINDy, die Abgrenzung muss explizit begruendet werden). Kein Code, keine Laeufe.

<!-- b0c8eaa -->

### Mikro-Benchmark System 26 gelaufen — Kostentreiber quantifiziert, Obergrenze bei 21x

Externer Lauf `studies/profiling/profile_eval_cost.jl` auf System 26, Seed 42, v2.2, 18 Level. Beide Faelle mit **identisch 370 Parameter-Fits** — damit ist der Vergleich normiert.

| | A (Referenz) | B (Screening) | Faktor |
|---|---|---|---|
| Laufzeit | 3222,6 s (53,7 min) | 1189,8 s (19,8 min) | **2,71x** |
| Kosten pro Fit | 8,71 s | 3,22 s | 2,71x |
| ODE-Solves | 1.741.484 | 2.488.973 | 0,70x |
| Kosten pro Solve | 1,763 ms | 0,409 ms | **4,31x** |
| Solve-Anteil an Laufzeit | **95 %** | 86 % | |
| Overhead ohne Solve | 153 s | 166 s | |
| Loss | 1,391623e-3 | 2,653197e-4 | B 5,2x besser |
| erreichte Stage | 3 | 4 | |
| `pruned_match` | false | false | |

B rechnet **mehr** Integrationen (2,49 Mio. vs 1,74 Mio.), aber jede einzelne ist 4,3x billiger — der Deckel `maxiters_solve = 20.000` und die Divergenzschwelle 1e6 greifen genau bei den Ausreissern. Sichtbar im Log: Level 16 von A kostete 1054 s, davon 1045 s (99 %) im Solver, mit 112 Solves im Millionen-Schritt-Limit.

**Sauberster Einzelvergleich:** Stage 2, in beiden Faellen exakt 8 Level — A 2937,9 s, B 297,1 s, **Faktor 9,9x**. Stage 2 sind die selbst-quadratischen Terme; die erzeugen Blow-up-Dynamik, und genau dort zahlt der ungedeckelte Referenzpfad.

**Regressionsnachweis, mit Nebenbefund:** A liefert Loss `0.001391623174905009` — **bit-identisch zu Baseline v0**. v0 brauchte dafuer 30 Level und 3,0 h und lief bis Stage 5; A erreicht denselben Loss in 18 Leveln und 53,7 min bei Stage 3. **Die Level 19–30 in v0 haben rund 2,1 h gekostet und den Loss um exakt null verbessert.** Die Overshoot-Diagnose vom Vormittag ist damit an einer Einzelzelle direkt belegt.

**Determinismus bestaetigt:** `optimizer_safety_limit_hits = 0` in beiden Faellen, die Wall-Clock-Notbremse hat nie gegriffen. Beobachtete Retcodes: Solver `{Success, Unstable, MaxIters}`, Optimierer `{Success, Failure}`.

**Entscheidende Zahl fuer die naechste Stufe:** 95 % der Laufzeit von A liegen in der ODE-Integration, der Overhead ausserhalb betraegt 153 s. Ein Screening ohne Integration in der Suchschleife (ableitungsbasiertes Kriterium, Maschinerie in `pretune.jl` vorhanden) hat auf dieser Zelle eine Obergrenze von **~21x** gegenueber A — gegenueber den 2,71x, die Solver-Tuning gebracht hat. Solver-Tuning ist damit ausgereizt; der Groessenordnungssprung liegt allein in der Reduktion der Anzahl Integrationen.

**Vorbehalte:** n = 1 Zelle, 1 Seed. B ist kein freier Speedup, sondern eine andere Suche (`structure_changed = true`, abweichende Stage-Trajektorie: A 9/8/1 Level in Stage 1/2/3, B 4/8/4/2). Keiner der beiden Faelle findet die korrekte Struktur.

<!-- be9046e -->

### WP-P1c umgesetzt und reviewt — erste Messdaten, Kostentreiber identifiziert

Committet `434a8a7`. Umsetzung korrekt: Level-Budget 18, Kosten pro Level aus dem `level_log` statt aus der Gesamtzeit, erstes Level ausgeschlossen, Mittelwert **und** Median, Per-Level- und Per-Stage-Aufschlüsselung in JSON und Textausgabe. Verifikationslauf auf System 3 durchgeführt.

**Regressionsnachweis:** Fall A liefert auf System 3 Seed 42 Loss `2.663641831768419e-10` — **bit-identisch zu Baseline v0**, bei gleicher `final_stage` 3. Der Referenzpfad ist nach WP-P1/P1b/P1c unverändert.

**Determinismus empirisch bestätigt:** `total_optimizer_safety_limit_hits = 0` und `total_step_limit_solves = 0` in beiden Fällen. Die Wall-Clock-Notbremse hat nie gegriffen, das Solver-Schrittlimit ebenfalls nicht. Beobachtete Retcodes: Solver `{Success, Unstable}`, Optimierer `{Success, Failure}`. `Failure` trat bei 95 von 210 Fits auf — unter der alten Teilstring-Logik wären das alles fälschlich „Iterationslimit"-Treffer gewesen; M1 war ein realer Defekt.

**Befund — die Kopfzahl „Speedup 1,032x" ist strukturell irreführend.** A und B terminieren bei unterschiedlicher Levelzahl (A: 10, B: 12), weil die gröberen Screening-Fits die Plateau-Erkennung verschieben. Das Verhältnis der Gesamtlaufzeiten ist damit kein Kostenverhältnis. Level für Level bei gleicher Stage:

| Level | Stage | A | B | Faktor |
|---|---|---|---|---|
| 2–4 | 1 | 3,5–4,2 s | 1,6–2,2 s | 1,6–2,6× |
| 5–8 | 2 | 44–77 s | 11–48 s | 1,4–4,2× |
| 9–10 | 3 | 16–19 s | 32–35 s | nicht vergleichbar (Läufe divergiert) |

Auf den vergleichbaren Leveln ist B also **1,4–4,2× schneller**. Mechanismus sichtbar: in A sind die Level 1–4 mit null verworfenen Solves durchgelaufen, in B wurden dort je 780–1260 Solves über `unstable_check` früh abgebrochen (Schwelle `divergence_limit = 1e6`). Die Kopfzahl im `summary.txt` sollte künftig auf Per-Level-Basis stehen; da Per-Level- und Per-Stage-Daten in der JSON liegen, ist der Vergleich nachträglich rekonstruierbar — kein Blocker für den System-26-Lauf.

**Wichtigster Befund — der eigentliche Kostentreiber ist die Zahl der Integrationen, nicht die Stage.** Für 210 Parameter-Fits fielen **1,53 Mio. ODE-Solves** an, also **~7.300 Solves pro Fit** (B: ~5.500). Erwartbar wären bei `maxiters = 200` und Finite-Differenzen über 3–6 Parameter etwa 800–1.400; der Rest geht auf Gradientenauswertung und Line-Search. Anteil der Solve-Zeit an der Gesamtlaufzeit: A 74 %, B 66 %.

**Konsequenz:** Solver-Tuning allein kann höchstens den Faktor ~3,4 heben (mehr ist der Solve-Anteil nicht). Der Sprung um Größenordnungen ist nur über eine Reduktion der *Anzahl* Integrationen erreichbar — also über das ableitungsbasierte Screening-Kriterium (bisher als WP-P2 zurückgestellt), das die Integration in der Suchschleife ganz ersetzt. Das ist nach dem System-26-Lauf zu entscheiden.

<!-- 434a8a7, 807e828 -->

### WP-P1b reviewt — Code korrekt, Messaufbau greift zu kurz; WP-P1c beauftragt

Committet `268dc41`. Alle fünf Review-Punkte aus WP-P1b sind sauber umgesetzt: `screening_optimizer` in `EvoGrowV3` inkl. Brücke, eigener Suchschleife und vollständig gespiegelter Instrumentierung; `screening_budgets_active` kommt jetzt aus dem Meta, mit hartem Fehler bei fehlendem Feld statt stillem Default. Frühe Verwerfung über `unstable_check` (Abbruch) statt `isoutofdomain` (Schritt-Ablehnung), Prädikat `_state_exceeds_limit` allokationsfrei elementweise. Nicht-endlich-Verwerfung hinter `reject_nonfinite` gelegt, Zähler bleibt unbedingt — Default-Pfad damit wieder verhaltensgleich. Retcode-Kategorien über Enum-Vergleich mit eigener `:unknown`-Kategorie; alle 14 referenzierten `SciMLBase.ReturnCode`-Member gegen die aufgelöste Version 2.128.0 geprüft, alle vorhanden.

**Neuer Befund — 12 Level messen am Problem vorbei.** Level-aufgelöste Nachrechnung des v0-Logs für System 26 Seed 42: bis Level 12 kostet die Zelle **1,6 min**. Der Ausbruch beginnt danach — Level 13: 147 s, Level 14: 878 s, Level 16: 611 s, Level 19: 1484 s; bis Level 18 kumuliert 39,7 min (Stage 3 beginnt), bis Level 20 66,2 min. Der Benchmark hätte also ausschließlich den billigen Bereich vermessen und zwischen A und B praktisch keinen Unterschied gezeigt. Der Richtwert „12" stammt aus meiner WP-P1b-Spec und war ohne diese Auflösung gewählt. Korrektur auf **18 Level** (≈ 40 min für Fall A, erfasst Level 13–17 und erreicht Stage 3).

**Zweiter Befund — JIT-Warmup verzerrt gegen B.** `cost_per_level_s` wird aus der Gesamtlaufzeit geteilt durch Levelzahl gebildet. Seit WP-P1b läuft Fall B zuerst und trägt damit die gesamte Kompilierzeit des `discover`/BFGS/Solver-Pfads — also ausgerechnet der Fall, der schneller sein soll. Die Per-Level-Zeiten liegen im `level_log` bereits vor; die Kennzahl muss von dort kommen, erstes Level ausgeschlossen, zusätzlich Median (Verteilung stark rechtsschief).

**WP-P1c beauftragt:** Level-Budget 18, Kosten pro Level aus dem `level_log` inkl. Median, Per-Level- und Per-Stage-Aufschlüsselung in die Ausgabe (damit das Ergebnis mit der Baseline-Tabelle vergleichbar ist). Verifikation nur auf System 3; System 26 bleibt dem externen Lauf vorbehalten.

<!-- 268dc41, 864c9d3 -->

### WP-P1 umgesetzt und reviewt — drei Blocker, WP-P1b beauftragt

Codex hat WP-P1 umgesetzt (`911a567`, enthält versehentlich auch die WP-P1b-Spec): `BFGSOptimizer` um deterministische Budget-Parameter und `reject_nonfinite`/`divergence_limit` erweitert, Zähler pro Level (Fits, Solves, invalid/diverged/nonfinite, Optimizer-Limit-Treffer, Solve- vs. Overhead-Zeit) über EvoGrow-Meta bis in den Record durchgereicht, expliziter Referenz-Optimizer im Regression-Runner (`time_limit_s = 86_400`), Mikro-Benchmark `studies/profiling/profile_eval_cost.jl`. Instrumentierung sauber und vollständig verdrahtet; Fingerprint korrekt erweitert; Profiling-Skript verschmutzt `history.jsonl` nicht.

**Review — drei Blocker:**

1. **v3 ignoriert die Screening-Budgets, Records sind falsch etikettiert.** `EvoGrowV3` hat kein `screening_optimizer`-Feld (der Runner übergibt ihn an einen ungenutzten Parameter) und wertet in seiner eigenen Suchschleife immer mit dem Referenz-Optimizer aus. Bei aktivierten Budgets liefen v2.2 und v3 damit unter verschiedenen Budgets → Anker-Vergleich wertlos. `screening_budgets_active` wird zudem aus dem ENV-Flag statt aus dem Meta geschrieben, und die 11 Instrumentierungsfelder sind bei v3 alle `nothing`. Ursache war meine eigene Spec-Formulierung („evogrow_v3.jl nicht anfassen") — gemeint war das Lockstep-Verhalten, nicht ein Durchreich-Parameter.

2. **`isoutofdomain` ist das falsche Primitiv.** Belegt in `OrdinaryDiffEqCore/.../integrator_utils.jl:268-286`: `isoutofdomain == true` setzt `accept_step = false` → Schritt verwerfen, `dt` verkleinern, erneut versuchen, bis `maxiters`/`dtmin`. Kein Abbruch. Das Abbruch-Primitiv ist `unstable_check`, dessen Default (`DiffEqBase/common_defaults.jl:110-120`, `INFINITE_OR_GIANT`) bereits `any(!isfinite, u)` prüft — die Nicht-endlich-Erkennung war also ohnehin aktiv, über den richtigen Mechanismus. Neu ist allein die endliche Schranke. Netto verteuert die Änderung genau die divergierenden Kandidaten, die sie billiger machen sollte. Zusätzlich alloziert die Prüf-Closure zwei temporäre Arrays pro Schritt im Hot Path.

3. **Der „Mikro"-Benchmark ist nicht mikro.** Fall A ist System 26 / Seed 42 / 30 Level — die 3-h-Zelle aus Baseline v0, damals *mit* der 300-s-Bremse, die laut v0-Log regelmäßig griff (~400 s/Fit auf teuren Leveln). Mit `maxiters = 200` und `maxiters_solve = 10^6` gibt es keine deterministische Obergrenze für einen einzelnen Fit.

**Weitere Befunde:** (S1) `_predict_traj` und `simulate` verwerfen nicht-endliche Lösungen jetzt unbedingt, auch bei `reject_nonfinite = false` — vorher lief eine Success-Lösung mit `Inf` durch (die Prüfung greift nur bei NaN) und ergab Loss `Inf`; stilles Verhaltens-Delta im Default-Pfad. (S2) Der Determinismus-Fix ist lokal: Struct-Default `time_limit_s = 300.0` unverändert, `benchmark_evogrow.jl`, `experiments/run_experiment.jl` und die übrigen Studies konstruieren weiter ohne expliziten Wert — **der in CLAUDE.md eingefrorene Paper-1-Pfad bleibt wall-clock-abhängig und muss vor Phase B entschieden werden.** (M1) Die Notbremse wird per Teilstring `"time"` im Retcode erkannt; ein abweichender Retcode würde einen ausgelösten Bremseingriff still als Iterationslimit verbuchen. (M2) In Fall B werden die Parameter nie auf Referenz-Fidelity nachgefittet (`discover()` refittet nur bei Parameteranzahl-Mismatch) — Interpretationsvorbehalt.

**WP-P1b beauftragt:** Punkte 1–3 plus S1, M1; S2 nur dokumentieren, nicht umstellen. Benchmark erst danach starten.

<!-- 911a567, 4fb4508 -->

### Volllauf abgebrochen — Kostendiagnose: 62 % der Rechenzeit oberhalb der nötigen Stage

Der Volllauf wurde bei 23/30 Zellen abgebrochen (v2.2 komplett 15/15, v3.2 bei 8/15), nach **40,5 Compute-Stunden**. Daten gesichert (`a69637a`). Grund: Laufzeit inakzeptabel (mehrere Tage), Restlaufzeit ~26–30 h für Zellen mit nahezu null Informationswert (v3.2 ist die Lockstep-Brücke; Äquivalenz war bereits beantwortet).

**Befund 1 — Anker bestätigt, mit einer Ausnahme.** v2.2 == v3.2 bit-identisch in 7 von 8 überlappenden Zellen. Abweichung nur System 26 Seed 123 (1.3916e-3 vs. 1.3713e-3).

**Befund 2 — Ursache ist ein Reproduzierbarkeitsleck, kein v3-Bug.** `run_regression.jl` baut `BFGSOptimizer(maxiters=BFGS_MAXITERS)`; `time_limit_s` bleibt beim Default **300 s Wall-Clock** (`bfgs.jl:29`) und wird an Optim.jl durchgereicht. Damit hängt die Zahl der BFGS-Iterationen von der Maschinenlast ab → Ergebnisse sind nicht reproduzierbar. Dieselbe Zelle brauchte 13.352 s (v2.2) vs. 20.158 s (v3.2). Muss für Paper 1 ohnehin weg.

**Befund 3 — Kostenprofil (aus `run.log` rekonstruiert, alle 23 Zellen).** Kosten pro Level explodieren mit der Stage:

| Stage | Level | Zeit | Anteil | s/Level |
|---|---|---|---|---|
| 1 | 124 | 0,7 h | 1,9 % | 21 |
| 2 | 129 | 6,1 h | 16,3 % | 170 |
| 3 | 94 | 11,6 h | 30,9 % | 443 |
| 4 | 55 | 7,4 h | 19,7 % | 482 |
| 5 | 48 | 11,7 h | 31,3 % | 878 |

Ein Stage-5-Level kostet das **42-fache** eines Stage-1-Levels. Pro Zelle oberhalb der erwarteten Stage aufsummiert: **24,9 von 40,5 h = 62 % der gesamten Rechenzeit wurden in Komplexität investiert, die die Systeme nie gebraucht haben.** Auf gekoppelten Systemen liegt der Anteil bei 38–80 %. Extremfall System 63 Seed 123: 8,4 h, davon 6,7 h verschwendet; ein einzelnes Level (16, Stage 4) kostete 3,4 h.

**Konsequenz:** Laufzeitproblem und Gate-1-Failure-Mode sind **dasselbe Problem**. Die Suche läuft über die nötige Stage hinaus, und jede zusätzliche Stage ist überproportional teurer (Stage 4/5 = kubisch/trigonometrisch → steife und divergierende Kandidaten-ODEs → Solver kriecht bis ins 300-s-Limit). Bei ~619 s pro Kandidat auf den teuersten Levels laufen einzelne Fits sicher ins Wall-Clock-Limit.

**Blocker für Phase B:** 63 Systeme × 2 Bedingungen × 3 Seeds = 378 Runs, davon 240 gekoppelt. Bei ~3,5 h pro gekoppelter Zelle > 800 h ≈ 5 Wochen durchgehend — und das Set enthält mehr 3D/4D als das Testset. **Phase B ist mit dem aktuellen Kostenprofil nicht durchführbar.** Muss vor WP-v3.3 gelöst werden.

Zwei getrennte Hebel, multiplikativ:
- **A (Overshoot, 62 %):** Promotionsdisziplin — genau das, was v3 leisten soll. Forschungsarbeit, bereits geplant.
- **B (Kosten pro Auswertung):** EvoODE bewertet jeden Kandidaten per voller Trajektorien-Simulation (bis 200 BFGS-Iterationen × ODE-Solve mit `maxiters_solve=10^6`, Toleranz 1e-9). SINDy/GP scoren auf Ableitungsresiduen statt zu integrieren — daher der Kostenunterschied. `pretune.jl` enthält die Maschinerie (finite Differenzen → Design-Matrix → lineares LS) bereits, nutzt sie aber nur als Warmstart, und im Regression-Config ist sie mit `USE_PRETUNING=false` ganz abgeschaltet.

Reihenfolge geändert: **WP-P1 vor WP-v3.3.**

**WP-P1 beauftragt** (`2bd9463`): Determinismus (kein Wall-Clock im Ergebnispfad), getrennte Budgets für Screening während der Suche vs. finale Validierung (Defaults = heutige Werte, kein stilles Verhaltens-Delta), Instrumentierung pro Level (Fits, Solves, verworfene Solves, Zeitanteil Optimierung vs. Simulation), sowie ein Pflicht-Mikro-Benchmark über genau eine Zelle (System 26, Seed 42) mit A/B-Vergleich. Ausdrücklich nicht in WP-P1: ableitungsbasiertes Screening-Kriterium, `use_pretuning`, Parallelisierung, WP-v3.3, WP-H2.

<!-- a69637a, 2bd9463 -->

---

## 2026-07-20

### WP-H1d umgesetzt und reviewt — Resume grün

Codex hat Resume umgesetzt: `load_completed_cells(fingerprint)` liest `history.jsonl` (try/catch pro Zeile), sammelt erfolgreiche `(variant, system_id, seed)`-Zellen bei passendem `config_fingerprint` und `error===nothing`; Skip in der Schleife (äußerer Balken tickt, Skip-Zeile in `run.log`, kein Record). `FRESH=1`-Override, End-Report. Fingerprint/Schema/Metriken unverändert. Committet `488fa1d`. Review: korrekt und spec-konform. Da die 7 geretteten Records `config_fingerprint=0c739d4e36ee6498` tragen und die Config unverändert ist, überspringt der Neustart sie und macht bei System 26 Seed 123 weiter. Grünes Licht für den Neustart erteilt.

<!-- 488fa1d, a298329 -->

### Volllauf durch Rechner-Neustart abgebrochen (7/30 gerettet); WP-H1d Resume beauftragt

Der externe Volllauf (Commit 776d2f0) wurde durch einen unerwarteten Rechner-Neustart abgebrochen. Dank append-only `history.jsonl` **7 von 30 Records gerettet** (alle v2.2: System 3 alle Seeds, System 11 alle Seeds, System 26 Seed 42 — der ~3-h-Lauf). In Git gesichert (`6420953`). Verloren: v2.2 System 26 Seeds 123/7, System 31, System 63, sowie ganz v3.

Nebenbefund aus den geretteten Daten: System 26 v2.2 Seed 42 → `pruned_match=false`, Overshoot Stage 5, Loss 1.4e-3 — bestätigt den Gate-1-Failure-Mode am Volllauf. Baseline, die v3.4 schlagen muss.

**WP-H1d (Resume) beauftragt** (`5ea632c`): Runner überspringt beim Neustart alle erfolgreichen (variant, system, seed)-Zellen desselben `config_fingerprint` (Skip keyed auf Fingerprint+Zelle+`error==null`, NICHT git_hash — sonst würden die 776d2f0-Records nicht erkannt). Fingerprint bleibt über volle Config berechnet; manuelles Kürzen der Systemliste ginge nicht (würde Fingerprint entwerten). Resume auch als Härtung gegen künftige Abbrüche. Ein resumeter Baseline-Lauf darf mehrere git_hashes umfassen (Config identisch, akzeptiert).

<!-- 6420953, 5ea632c, 55a6670 -->

### WP-H1c umgesetzt und reviewt

Codex hat den inneren Live-Balken verdrahtet: VARIANTS-Konstruktoren nehmen `level_callback`, `run_one` erzeugt einen inneren `Progress` (offset 1, total = min(N_LEVELS, max_levels)) + Callback, der pro Level `system/seed/level/stage/best_loss` zeigt; `finish!` im `finally`. Äußerer Balken offset 0. Beide auf stderr → `redirect_stdout(devnull)` hält Per-Level-Text weiter vom Schirm (nur in `run.log`). Metriken/Records/Fingerprint unverändert. Committet `9cd66e7`.

**Review:** Korrekt und spec-konform; `next!` kann total nie überschreiten (max 30 Level = total). Ein rein kosmetischer Vorbehalt, den ich nicht ohne Julia verifizieren kann: die pro-Lauf-Zusammenfassungszeile (`println(summary_line)`) wird zwischen zwei gestapelten ProgressMeter-Balken ausgegeben — das kann visuell holprig sein. Beim ersten externen Kurzlauf begutachten; falls unsauber, ist der Fix eine Zeile (auf `ProgressMeter.println` umstellen oder die Zeile weglassen, da `run.log` die Done-Zeile ohnehin hat).

<!-- 9cd66e7, 7e07cc6 -->

### WP-H1c beauftragt: innerer Live-Balken pro Lauf

Fix für die WP-H1b-Lücke (statischer Balken während eines langen Laufs). User hat „innerer Balken" gewählt. WP-H1c verdrahtet EvoGrows/EvoGrowV3s bestehenden `level_callback` (feuert pro Level mit Snapshot `level`/`stage`/`best_loss`) mit einem inneren `ProgressMeter`-Balken pro Lauf, gestapelt unter dem äußeren Balken (via `offset`). Kein src-Eingriff nötig. VARIANTS-Konstruktoren nehmen künftig ein `level_callback`-Argument. `redirect_stdout(devnull)` bleibt (Balken auf stderr, Per-Level-Detail weiter nur in `run.log`). Metriken/Records/Fingerprint/Config unverändert. Committet `429b645`.

<!-- 429b645, caa4c76 -->

### WP-H1b umgesetzt und reviewt

Codex hat das Logging umgesetzt: `ProgressMeter`-Balken (ETA + variant/system/seed) über alle Läufe, `run.log` mit Start/Finish-Markern, `[i/N]`-Zeilen und EvoGrows Per-Level-Heartbeat (Logger via `LOGGER.log_io` in Append-Modus umgeleitet). Screen minimal gehalten durch `redirect_stdout(devnull)` um `discover`. Fingerprint/Records/Config unverändert, `ProgressMeter` in `Project.toml`. Committet `af6cc6d`.

**Review-Befund (Lücke):** Innerhalb eines einzelnen Laufs geht der Heartbeat nur in `run.log`, nicht auf den Schirm — der Balken tickt erst am Lauf-Ende (`next!`). Bei einem langen Lauf (System 63: Stunden) sieht der User in der cmd also einen statischen Balken — genau das „wirkt gehängt"-Problem, das er vermeiden wollte. Fix-Vorschlag WP-H1c: EvoGrows bestehenden `level_callback` nutzen, um einen inneren Per-Level-Balken/Heartbeat live im Terminal zu zeigen (run.log-Detail bleibt). Nebenpunkt: `open_evo_logger_append!` greift direkt in `EvoODE.EvoLogger.LOGGER.log_io`, weil `set_log_file` im `"w"`-Modus truncaten würde — funktioniert, aber fragil; sauberer wäre ein `append`-Flag an `set_log_file`.

<!-- af6cc6d, 3c0b68f -->

### WP-H1b beauftragt: Fortschritts-Logging (tqdm-Stil)

Zweischichtiges Logging für `run_regression.jl`, damit der User externe Läufe live in der cmd verfolgen kann: **Bildschirm** = `ProgressMeter`-Balken (tqdm-Äquivalent) über N = Varianten×Systeme×Seeds mit ETA + aktuellem Item + eine Zusammenfassungszeile pro Lauf; **Datei** = `outputs/studies/regression/run.log` mit Start/Finish-Markern, `[i/N]`-Per-Run-Zeilen und EvoGrows Per-Level-Heartbeat (via `set_log_file`). Balken terminal-only (kein `\r` in die Logdatei). Prinzip „so wenig wie möglich auf dem Schirm, so viel wie nötig in der Datei". Optional: BFGS-Zeitlimit-Treffer pro Lauf als additives Feld (erklärt die Slowness). Nur Observability — Metriken/Records/Fingerprint/Config unverändert. `ProgressMeter` neu in `Project.toml`. Committet `476e192`.

<!-- 476e192, a29fdb6 -->

### WP-H1 umgesetzt und verifiziert; Julia-Läufe künftig extern

Codex hat WP-H1 geliefert: `studies/regression/{diagnostic_systems.jl, run_regression.jl, history.jsonl}`. Runner rechnet das feste Set (Systeme 3/11/26/31/63) für v2.2 und v3, hängt ein JSONL-Record pro (variant, system, seed) an `history.jsonl` an (git-Provenienz + `config_fingerprint`). Verifiziert über den echten Runner auf dem schnellen Subset (Systeme 3, 11): valides JSONL, stabiler Fingerprint, **Anker-Äquivalenz v2.2==v3 bit-genau** (System 3: identischer Loss/final_stage je Seed; v3 `eq_final_stages` gesetzt). `history.jsonl` leer committet. Committet `99393bb`.

**Laufzeit-Befund (wichtig):** Selbst das 1D-System 3 brauchte 218–1217 s pro Lauf (Stage-Overshoot → teure BFGS gegen das 300-s-Zeitlimit), System 11 nur ~3–4 s. Der Volllauf (× 26/63) ist ein Stunden-Job.

**Workflow-Entscheidung:** Julia-Läufe führt künftig der User extern durch; Claude startet in seiner Umgebung kein Julia mehr (Kompilierzeit blockiert). Konsequenz: Julia-Runner brauchen reichhaltiges, geflushtes, dateibasiertes Fortschritts-Logging (per-Run [i/N] + Timestamp + elapsed, per-Level-Heartbeat, run.log), damit externe Läufe live beobachtbar sind. Als nächste Verbesserung vor dem Volllauf. Siehe Memory `feedback_full_runs`.

<!-- 99393bb, 80cc96a -->

### Regressions-Historie beschlossen, WP-H1 beauftragt

Neue Anforderung: longitudinales Logging, um zu verfolgen, wie sich Metriken über Algorithmus-Versionen/Commits entwickeln (besser/schlechter pro System). Fehlende Achse gegenüber den bestehenden Snapshot-Logs (`run_registry.csv`, Aggregate) und dem narrativen DIARY. Scope-Entscheidung: **Medium**.

Design: festes Diagnostik-Set (Systeme 3/11/26/31/63, feste Seeds/Hyperparameter, wie `phase1_diag`) → append-only `studies/regression/history.jsonl`, ein Record pro (git_hash, variant, system, seed) mit `config_fingerprint` (Hash über metrik-relevante Config; nur innerhalb gleichem Fingerprint vergleichen) + `git_dirty`-Flag. Python-Delta-Report separat.

Aufgeteilt wegen Sprach-Deklaration pro Task: **WP-H1 (Julia)** = Runner + append-only Store (jetzt in `codex/CURRENT_TASK.md`); **WP-H2 (Python)** = Delta-Report (letzter vs. vorheriger Commit, ↑/↓/=, DIARY-fertiger Markdown-Block) als Folge-Task. Erste Baseline-Einträge: v2.2 + v3.2 (müssen laut Anker gleich sein). Bewusst *vor* WP-v3.3/v3.4 gezogen, damit jeder echte v3-Schritt ab Beginn in die Historie geloggt wird. Trigger manuell, nicht als Git-Hook (Läufe dauern Minuten bis Stunden).

<!-- a5ef98a, 1e58fd5 -->

### WP-v3.2 umgesetzt und verifiziert

Codex hat `EvoGrowV3` implementiert (`src/structure/evogrow_v3.jl`, registriert/exportiert in `src/EvoODE.jl`). Pro-Gleichung-Stage-State (`eq_stages`, `eq_levels_in_stage`, `eq_plateau_histories`, `eq_stage_histories`), Promotion aber noch Lockstep-global über einen internen `EvoGrow`-Bridge, der die v2.2-Helfer (`_validate_policy`, `_init_population`, `_stage_progression_decision`) wiederverwendet. Meta ergänzt `eq_final_stages` + `eq_stage_histories` mit `final_stage = maximum(eq_stages)`. Saubere Seams (`_lockstep_stage_progression_decision`, `_apply_lockstep_stage_update!`) für WP-v3.4.

**Regressions-Äquivalenz selbst verifiziert** (Julia-Skript, System 3 1D + System 26 2D, Seeds 42/7): identische `active_idxs`, Loss-Differenz bit-genau 0.0, `eq_final_stages` lockstep-gleich, `maximum(eq)==final_stage`. v3.2 reproduziert v2.2 (`:stage_local`) exakt — der Refactor ist neutral. Nebenbefund als Baseline: v3.2 scheitert auf System 26 genau wie v2.2 (Loss ~0.038, nur lineare Terme), was WP-v3.4 heilen soll.

Anmerkung Tech-Debt: Die ~350-Zeilen-Hauptschleife ist eine Kopie des v2.2-Loops (unvermeidbar unter „evogrow.jl nicht anfassen"). Nach Gate 2 faktorisieren oder v2.2-Loop stilllegen.

<!-- 559d3b7, f9802b3 -->

### WP-v3.1 geliefert, WP-v3.2 beauftragt

Codex hat **WP-v3.1** umgesetzt: `docs/evogrow_v3_design.md` friert das v3-Design ein — pro-Gleichung-Stage-State (`eq_stages` statt globalem `current_stage`), Ableitungs-Residuum `r_k` als pro-Gleichung-Progress-Signal (auf beobachteter Trajektorie), Promotion-Regel mit Residuum-über-Ziel-Guard (bereits erklärte Gleichungen promoten nicht), gleichungs-bewusste Child-Generation, Warm-Start-Übernahme, neue pro-Gleichung-Metriken. Vier offene Fragen mit empfohlenen Auflösungen. Committet.

**WP-v3.2 als nächsten Codex-Task formuliert** (`codex/CURRENT_TASK.md`): neuer `EvoGrowV3`-Struct + gleichungsweiser Stage-State als lauffähiges Refactor. Bewusst enger Scope — Promotion bleibt vorerst Lockstep (alle Gleichungen gemeinsam), sodass `EvoGrowV3` v2.2 (`:stage_local`) exakt reproduziert. Das dient als **Regressions-Anker**: spätere Divergenz ist dann eindeutig den gleichungs-lokalen Mechanismen (WP-v3.3 Child-Generation, WP-v3.4 Residuum-Signal + pro-Gleichung-Promotion) zuzuordnen, nicht dem Refactor. Verifikation: Struktur-/Loss-Identität v3 vs. v2.2 auf System 3 und 26.

<!-- f9567b5, 10ef90f, 4f78d20 -->

### Status-Abgleich und Housekeeping

Statusprüfung der vier offenen Punkte aus den „Current Priorities". Ergebnis: CLAUDE.md war veraltet (Stand 2026-05-11), `PAPER_1.md` ist die aktuelle Wahrheit.

- **WP-0.1** (H4-Verdict → VACUOUS in `evaluate_hypotheses.py`): bereits erledigt, Commit `a199128` (2026-05-17). Die `vacuous`-Prüfung setzt das Verdict korrekt, das Freeze Memo schreibt „C3 cannot be evaluated".
- **WP-0.2** (Generalization-Pfad): bereits erledigt (2026-05-17). Config zeigt korrekt auf `debug_results/generalization_summary.csv`.
- **WP-v3.1** (Design Note `docs/evogrow_v3_design.md`): aktiver Codex-Task in `codex/CURRENT_TASK.md`, Deliverable noch nicht geschrieben. Das ist der reale aktuelle Arbeitspunkt.
- **Phase B**: nicht begonnen, erst nach Gate 2.

**CLAUDE.md synchronisiert:** „Current Priorities" und „Active WPs" auf Phase 2 / WP-v3.1 aktualisiert, erledigte WPs markiert. Fehl-Label korrigiert: der frühere „Phase 2"-Prioritätspunkt (R²/Protocol-Audit) ist laut `PAPER_1.md` eigentlich Phase 3.

**Untracked Runner committet:** `studies/phase1_diag/run_phase1_diag.jl` (WP-1.3-Diagnostik, Gate-1-Evidenz) war nie eingecheckt — jetzt nachgeholt.

<!-- 7f29a02, eae3e2c, e819afb -->

---

## 2026-05-30

### WP-1.3 Ergebnisse und Gate-1-Entscheidung

Phase-1-Diagnostik-Runs abgeschlossen: 15/15 JSON-Dateien in `outputs/studies/phase1_diag/`. Konfiguration: EvoGrow v2.2 stage_local, `use_pretuning=false`, `n_levels=30`, 3 Seeds je System.

**Kontrollsysteme:**

- System 3 (Logistic): `pruned_match=true` alle 3 Seeds, Loss ~7e-10. Stage-Overshoot 0–3 (Mindestbudget-Effekt). Fit-Qualität gut, kein Strukturproblem.
- System 11 (Cubic `du=-u³`): `pruned_match=true` alle 3 Seeds, Loss ~4e-15, Stage 4/4, Laufzeit ~1.3s. Metrik-Artefakt aus WP-1.2 vollständig geheilt — der Pruning-Fix funktioniert.

**Problemsysteme:**

- System 26 (Lotka-Volterra 2D): `pruned_match=false` alle 3 Seeds, Loss ~5e-4–1.4e-3, Stage 5/3, Laufzeit 2800–9400s. Gefundene Struktur: `du1 = (5.05)*u1 + (-3.87)*u1*u2`, `du2 = (1.13)*u1 + (-1.80)*u1^2` — Terme komplett falsch. Loss platzt in Stage 3 auf ~1e-3, danach keine Verbesserung trotz Eskalation bis Stage 5 (Trig-Terme nutzlos).
- System 31 (SIR 2D): Seed 42 erreicht Loss ~7e-11 (nahezu perfekt), aber `pruned_match=false` wegen Spurious-Term `0.0022*u1` — Pruning-Schwellenwert `1e-3 × max_coeff = 4e-4 < 0.0022`, Term überlebt. Seeds 123/7: Stage 5/3, Loss ~1e-4–7e-5, echter Fehler.
- System 63 (SEIR 4D): `pruned_match=false` alle 3 Seeds, Loss ~9e-4–1.8e-3, Stage 5/3, Laufzeit 11000–31000s. Konsistentes Scheitern.

**Strukturdiagnose:** Der systemweite Staging-Mechanismus von v2.2 zwingt alle Gleichungen gemeinsam in höhere Stages, sobald der globale Progress stagniert. Auf System 26 findet der Algorithmus in Stage 3 keine verwertbaren Cross-Terme, promotiert dann global zu Stage 4 (kubische Terme) und Stage 5 (Trig), obwohl keine Gleichung Trig-Terme benötigt. Das ist kein Metrik-Fehler — es ist eine echte algorithmische Schwäche des systemweiten Staging.

**Nebenbeobachtung System 31 Seed 42:** Pruning-Schwellenwert 1e-3 × max_coeff könnte für BFGS-konvergierte Modelle zu streng sein. Der Term 0.0022*u1 ist klein aber nicht null. Zu re-evaluieren nach v3-Validierung.

**Gate-1-Entscheidung: v2.2 ist NICHT paper-ready. Phase 2 (EvoGrow v3) wird ausgelöst.**

Begründung: Der Failure-Mode auf Systems 26 und 63 ist klar auf systemweites Staging zurückführbar, nicht auf Metrik-Fehler oder Parameter-Fitting. Das ist genau die Bedingung, unter der v3 (gleichungsweises Staging) motiviert ist.

WP-v3.1 (Design Note) als nächsten Codex-Task formuliert.

<!-- f5e7033 -->

---

## 2026-05-17

### Strategischer Pivot: Paper 1 Neufokus

Paper 1 wird kein Pretuning-Vergleichspaper. Pretuning wird für Paper 1 vollständig deaktiviert und als mögliches Follow-up-Paper zurückgestellt.

**Neue wissenschaftliche Kernfrage:**
> Ist inkrementelles, gestuftes Wachstum ein effektiver Suchmechanismus für interpretierbare ODE-Entdeckung — und wo hilft es, wo versagt es?

**Phase A Neubewertung:** H1/H3 PARTIAL war kein schlechtes Ergebnis, sondern ein diagnostisches Signal. System-weites Staging ist möglicherweise zu grob für mehrdimensionale Systeme (26, 31, 63). Das ist der algorithmische Befund, dem das Paper nachgehen muss.

**Neues Experiment-Design:** 63 ODEBench-Systeme × 1 finaler EvoGrow-Variant × 3 Seeds = 189 Runs. Keine externen Baselines in-house; publizierte ODEBench-Zahlen als Referenzkontext.

**Gate-Struktur eingeführt:**
- Gate 1: Ist v2.2 nach Metric-Repair paper-ready? (Phase 1 Diagnose)
- Gate 2 (nur falls nötig): Ist v3 (gleichungsweises Staging) paper-ready?

`PAPER_1.md` vollständig neu geschrieben. WP-0.2 als erledigt markiert.

<!-- fb549af -->

## 2026-05-11

### H1–H4 Auswertung und Freeze Memo (Step 2)

Codex hat `evaluate_hypotheses.py` implementiert und die formale Hypothesenauswertung auf `paper1_phaseA_v1` (300/300 Runs) durchgeführt. Ergebnisse ins Freeze Memo (`docs/paper1_freeze_memo_phaseA.md`) und Diagnostics JSON (`analysis/data/paper1_phaseA_v1/h1_h4_diagnostics.json`) geschrieben.

**Verdicts:**
- **H1** (Stage Overshoot Reduction): PARTIAL — korrekte Richtung nur auf System 54 (Lorenz), 1 von 6. Systeme 3, 11, 26, 31, 63 zeigen kein Signal oder falscher Trend. Ursache: Mindestbudget pro Stage erzwingt mehr Levels auf einfachen Systemen.
- **H2** (Competitive Recovery Quality): SUPPORTED — 7 von 8 Systemen kompetitiv (exact_match oder mean_loss). Nur System 11 nicht kompetitiv.
- **H3** (Wasted Levels Reduction): PARTIAL — korrekte Richtung nur auf Systemen 11 und 54, 2 von 6.
- **H4** (Usage Policy Effect): SUPPORTED (vakuös) — alle Policy-Varianten zeigen exact_match=0 auf Stage-≥3-Systemen, erwartete Ordnung `hard ≥ soft ≥ passive` daher nicht unterscheidbar.

**Design-Entscheidungen dokumentiert:**
- `exact_support_match` als striktes Binary-Metrik ohne Schwellenwert ist korrekt und bleibt unverändert
- System 11 (`du=-u³`): EvoGrow findet Struktur mit loss ~4e-15, aber growth-without-pruning akkumuliert Null-Terme → kein exact_match. Echter algorithmischer Mangel, kein Metrik-Fehler. Muss im Paper explizit genannt werden.
- Generalisierungsstudie: keine förderfähigen Zellen (n_exact_runs < 3), bleibt im Supplementary.

### Repo Readiness Review und Cleanup

Vollständiges Repo-Review vor nächster Implementierungsphase. Alle gefundenen Issues behoben:

- `codex/CURRENT_TASK.md`: abgeschlossenen Step-2-Task gelöscht, "Kein aktiver Task" gesetzt
- `CLAUDE.md`: veraltete Abschnitte (242/300 Befunde, Active Studies 2026-04-29, Current Priorities 2026-04-29, Known Gaps) auf aktuellen Stand 2026-05-11 gebracht
- `analysis/CONVENTIONS.md`: gebrochene Referenz `CURRENT_TASK_ANALYSIS.md` → `CURRENT_TASK.md` korrigiert (Datei existiert nicht)
- `docs/paper1_study_protocol.md`: als Phase-A-Archivdokument markiert, nicht mehr aktives Protokoll
- `analysis/configs/paper1_phaseA_v1.json`: Generalisierungspfad von `outputs/studies/generalization/` → `debug_results/` korrigiert (WP-0.2)

Abschließende Verifikation: `debug_results/generalization_summary.csv` und `generalization_detail.csv` existieren — WP-0.2 damit vollständig erledigt.

Offener Rest: WP-0.1 (H4-Claim-Korrektur in `evaluate_hypotheses.py`) — wird morgen als Codex-Task formuliert. Das ist der einzige noch ausstehende Punkt vor dem endgültigen Abschluss von Phase A.

<!-- b4c1cce, 5f5fc43 -->

### Strategische Neuausrichtung: Paper 1 Roadmap

ODEBench-Paper (d'Ascoli et al. 2023, 2310.05573) analysiert: EvoODE verwendet dieselben 63 Strogatz-Systeme mit identischen ICs (alle 8 exakten Systeme verifiziert). Baseline-Strategie: veröffentlichte ODEBench-Zahlen direkt zitieren (σ=0, ρ=0 Regime), R²-Metrik aus existierenden Trajektorien berechnen.

**Strategie:** EvoODE konkurriert nicht mit ODEFormer (50M Training-Beispiele, A100), sondern mit SINDy(poly) und PySR (~35–50% Accuracy bei σ=0). EvoGrow v3 (gleichungsweise gestufte Promotion) als nächste Variante geplant.

`PAPER_1.md` komplett ersetzt durch detaillierten Ausführungsplan: Phasen 0–5, WP-Aufschlüsselung, EvoGrow v3 Design-Spec, Risikoregister, eingefrorene Baselines.

`CLAUDE.md`: neuer Abschnitt "Paper 1 — Execution Roadmap" als Pointer auf `PAPER_1.md`.

---

## 2026-05-08

### paper1_phaseA_v1 vollständig abgeschlossen

`experiments/run_experiment.jl paper1_phaseA_v1` hat alle 300 Runs durchlaufen (300/300, alle `success=true`, 0 failed, 0 interrupted). Laufzeit ca. 4.5 Tage.

Aggregation: `julia experiments/aggregate.jl paper1_phaseA_v1` → `run_registry.csv` (300 Zeilen).
Python-Pipeline: `aggregate_run_registry.py` → `data/paper1_phaseA_v1/aggregate_by_variant_system.csv` (60 Zeilen, 6 Varianten × 10 Systeme, alle Zellen vollständig).

### Erste vollständige Auswertung: paper1_phaseA_v1

**Exact Match (Kernbefunde):**

- Systeme 2, 3, 24: alle EvoGrow-Varianten `exact_match=1.0`, GP auf System 24 `exact_match=0` (loss ~4.5e-3 vs. EvoGrow 5.4e-14 — dramatischer Unterschied auf simpelstem 2D-linearem System)
- System 11 (cubic, `du=-u³`): alle EvoGrow `exact_match=0` trotz loss ~4.4e-15 — Bug in `exact_support_match` vermutet; GP `exact_match=1.0`
- Systeme 26, 31, 54, 63: `exact_match=0` für alle Varianten — kein exakter Strukturfund auf Stage-3-Systemen

**Loss EvoGrow vs. GP (höherdimensionale Systeme):**

| System | Beste EvoGrow | GP | Faktor |
|--------|--------------|-----|--------|
| 31 SIR | 7.0e-05 | 0.314 | ~4.500× |
| 54 Lorenz | 7.4e-04 | 0.921 | ~1.200× |
| 26 Lotka-Volterra | 2.5e-04 | 2.98e-03 | ~12× |

GP versagt auf gekoppelten Systemen deutlich — stärkstes Argument für EvoGrow.

**Stage Overshoot (Kernhypothese):**

- **System 54 (Lorenz):** v1=+2, v2.1=+1.6, alle v2.2=0 Overshoot, 0 Wasted Levels → sauberste Bestätigung der Kernhypothese
- **System 3 (Logistic):** v1=0 (flache Basis, keine Stage-Promotions), alle v2.x=+3 Overshoot — v2.2_stage_local verschärft wasted_levels auf 12 durch Mindestbudget
- **Systeme 26, 31, 63:** alle Varianten +2 Overshoot — kein Differenzierungssignal

**Offene Fragen:**
- `exact_support_match`-Bug bei System 11 untersuchen (loss ~0 aber kein Match)
- Warum GP auf System 24 (harmonic oscillator) so schlecht?
- Für keine Stage-3-Systeme exact match → algorithmisches Problem oder Loss-Tol-Problem?
- Kein Run konvergiert auf `loss_tol=1e-8` außer System 2/24 → Stopp-Mechanismus greift nie als Loss-Stopp

### WP3: Frame Layout Redesign (search_animation.jl)

Zweispalten-Layout für `render_frame`: linke Spalte = Trajektorien-Subplots, rechte Spalte = Info-Panel (Loss, entdeckte Gleichungen, wahre Gleichungen, farbige Legende). Aktuelle Level-Kandidaten in Orange, Historie in Grau. `plot_title` über allen Subplots. `structure_to_string` Koeffizientenformat auf `%.3f` geändert.

---

## 2026-05-05

### WP11: CairoMakie-basiertes `render_frame` (Spec + Abhängigkeit)
`ac7658f`

Codex-Spec für WP11 geschrieben: vollständiger Neubau von `render_frame` auf Basis von CairoMakie statt Plots.jl. Ziel ist pixel-genaue Kontrolle über Layout und Typography für Publikationsqualität.

CairoMakie als Abhängigkeit in `Project.toml` aufgenommen. Bestehende `search_animation.jl` bleibt unverändert, bis WP11 implementiert ist.

---

## 2026-05-04

### Animationspipeline: WP4–WP8 (Live-Rendering, Layout, Typography)

**WP4 — Live-Frame-Rendering via `level_callback`** (`2e31f2e`):
`level_callback`-Hook in EvoGrow eingebaut, der am Ende jedes Levels aufgerufen wird. Frame wird direkt während des Runs gerendert und gespeichert — kein Post-Hoc-Rendering mehr nötig.

**WP5 — Horizontale Balken im Info-Panel** (`8e46613`):
Frame-Layout auf horizontale Balken pro Kandidat umgestellt (Trajektorie-Panel links, Loss-Rang-Balken rechts). Verbesserte Lesbarkeit auf Stage-Promotions-Grenzen.

**WP6 — Stage-Grammar-Anzeige in der Gleichungsleiste** (`92f892e`):
Aktuell freigeschaltete Stage-Terme werden in der Gleichungsanzeige farblich hervorgehoben. Neue Terme (neu in dieser Stage) vs. ältere Terme visuell unterscheidbar.

**WP7 — Typografie-Refaktor** (`a496f94`):
Schriftgrößen, Zeilenabstände und Gewichtungen vereinheitlicht. Koeffizientenformat auf `%.3g` geändert (keine führenden Nullen mehr). Gleichungszeilen kürzer und lesbarer.

**WP8 — Header/Meta-Verfeinerung** (`c0f12ca`):
Titel-Header zeigt: System-Name, Variante, Seed, aktueller Stage, Level-Fortschritt. Grau-Kandidaten-Alpha von 0.08 auf 0.18 erhöht (besser sichtbar ohne Ablenkung vom besten Kandidaten).

---

## 2026-05-03

### Animationspipeline für EvoGrow-Suchverlauf (WP1–WP3)
`2fa3e18`

Visualisierung des stufenweisen EvoGrow-Suchprozesses als animiertes Video:

**WP1 — Snapshot-Sammlung in `src/structure/evogrow.jl`:**
- `vis_history`-Feld in EvoGrow; sammelt Snapshots am Ende jedes Levels
- Jeder Snapshot enthält aktuelle Population (Kandidaten + Scores) und Stage-Info

**WP2 — Rendering in `src/plotting/search_animation.jl` + `studies/visualization/animate_search.jl`:**
- `search_animation.jl`: rendert pro Level ein PNG-Frame
- `animate_search.jl`: orchestriert Discovery → Frame-Rendering → optionaler ffmpeg-Export (MP4)

**WP3 — Frame-Layout:**
- Zweispaltig: links Trajektorie-Subplots (Ground Truth vs. Kandidaten), rechts Info-Panel
- Aktuelle Level-Kandidaten: orange; akkumulierte History: grau
- Info-Panel: Stage, Level, Loss, true Gleichungen, farbige Legende

---

## 2026-05-02

### `profile_init` — Ergebnisse ausgewertet
`72629a3`

- `docs/profile_init_results.md` + `docs/profile_init_convergence.png` angelegt
- Lorenz: Pretune klar besser auf allen 3 Seeds (~4× niedrigerer Loss, erreicht Stage 3 statt Stage 2)
- Lotka-Volterra: Pretune auf Mittelwert besser, auf Seed-Ebene gemischt — treibt Algorithmus in Stage 5 (Overshoot)
- Kritisch: alle 12 Runs enden mit `max_levels`, kein Run konvergiert → Level-Budget zu gering für belastbare Aussagen

---

## 2026-04-30

### `analysis/status.py` — Logdatei-Auswertung (WP4)
`90e70f5`

`status.py` um Auswertung der neuen `run.log`-Dateien (aus WP2) erweitert:

- `LOG_PATHS`-Dict: Skript → `run.log`-Pfad im jeweiligen OUT_DIR
- `read_log_markers()`: liest `=== Started/Finished at ===`-Marker aus Logdatei (letzte 500 Zeilen)
- `build_log_info()`: leitet ab ob letzter Run sauber beendet (`clean=True/False/None`)
- `print_known_scripts()`: zeigt Log-Zeile pro Skript (Start-/Endzeit, sauber/unterbrochen)
- WMI-Logik, Output-Timestamps und ETA-Berechnung vollständig erhalten

### Resume-Logik für `benchmark_evogrow.jl` (WP1) + Stdout-Logging (WP2)
`0c74f2d`

Benchmark konnte bisher nicht sicher gestoppt werden: `open(summary_file, "w")` überschrieb
die CSV bei jedem Start. Lösung:

- `seed`-Spalte in CSV eingeführt (Header + Row + Fehler-Record)
- `parse_csv_fields()`: korrekter CSV-Parser für Semikolon-Trenner mit Quote-Handling
- `load_done_set()`: liest existierende CSV und baut `Set{Tuple{String,Int,Int}}` aus `(variant_slug, id, seed)`
- `load_records_from_csv()`: lädt alle Rows für Aggregate nach Resume
- Hauptloop: Skip-Check vor jedem Run, Append-Mode wenn CSV existiert
- Einmalige Migration der bestehenden 140-Row-CSV: `seed`-Spalte per Positionszählung
  nachträglich eingetragen (Seeds-Reihenfolge ist deterministisch → sicher ableitbar)

### Repository-Strukturmigration (WP-R)
`706549f`

Alle drei laufenden Skripte gestoppt. Migration durchgeführt:

- `benchmarks/odeformer/` → `benchmarks/data/` (Datenpfade in beiden Benchmark-Skripten aktualisiert)
- `benchmarks/results/` → `outputs/benchmarks/` (OUT_DIR in `benchmark_evogrow.jl`)
- `generalization_study.jl` → `studies/generalization/`, OUT_DIR → `outputs/studies/generalization/`
- `profile_init.jl` → `studies/profiling/`, OUT_DIR → `outputs/studies/profiling/`
- `debug_single.jl` → `studies/debug/`, OUT_DIR → `outputs/studies/debug/`
- `.gitignore`: `outputs/` eingetragen
- Vorhandene Output-Daten nach `outputs/` kopiert (Resume-Kontinuität)
- `SCRIPTS.md` + `CLAUDE.md` aktualisiert

### Stdout-Logging in alle Skripte (WP2)
`0c74f2d`

Alle fünf Skripte schreiben jetzt `run.log` im jeweiligen OUT_DIR (Append-Modus):

- `=== Started at <ts> ===` / `=== Finished at <ts> ===` als Marker
- `log_println()` + `@logf`-Makro für formatierte Ausgaben
- Betrifft: `benchmark_evogrow.jl`, `studies/profiling/profile_init.jl`,
  `studies/generalization/generalization_study.jl`, `studies/debug/debug_single.jl`,
  `experiments/run_experiment.jl`
- Bestehender per-Run-Log-Mechanismus in `profile_init.jl` bleibt erhalten

---

## 2026-04-29

### `analysis/status.py` — Study Status Checker (Codex-Task)
`756b512`, `b94601f`

Ziel: Skript, das aus SCRIPTS.md alle bekannten Scripts extrahiert und prüft, welche davon gerade laufen.

**Technische Analyse (Windows/WMI):**

- `julia.exe`-Prozesse per PowerShell + WMI abfragbar
- Problem: Command Line von `julia.exe` enthält auf Windows oft keine Script-Argumente
- Wenn Parent-Prozess `julialauncher.exe` ist: Argumente im Parent sichtbar → Script identifizierbar
- Wenn Parent `cmd.exe` ist (auch wenn cmd noch offen): Argumente gehen verloren — gilt für alle über cmd gestarteten Skripte

**Lösung: Hybrid-Ansatz**

1. Prozessbaum: julialauncher.exe-Parent → Script-Name direkt lesbar
2. Output-File-Timestamp: wenn Output-Datei < 90 min alt und Orphan-Prozess läuft → `[LÄUFT?]`

**ETA-Schätzung:**

- Rate über letzte 20 Runs (nicht Gesamtlaufzeit) — robust gegen stuck runs
- Für Experiment-Runner: Rate aus `finished_at`-Timestamps der status.json-Dateien
- Für Benchmark: Rate aus `elapsed_s`-Spalte in summary.csv
- Stuck-Run-Erkennung wenn Run seit >2h im Status `running`

**Implementierung und Nachtrag:**

- `analysis/status.py` als standalone Python-Skript mit Standard Library umgesetzt
- `SCRIPTS.md` wird per Regex auf `julia <path>.jl`-Aufrufe in Codeblöcken geparst
- Output-Mapping hart codiert, aber ohne Experiment-ID-Hardcoding (`glob`-Patterns)
- Fortschritt/ETA implementiert für:
  - `experiments/run_experiment.jl`
  - `benchmarks/benchmark_evogrow.jl`
  - `profile_init.jl`
  - `generalization_study.jl`
- Stuck-Run-Warnung erkennt aktuell hängende `status.json`-Runs, z.B. alte Lorenz-Runs mit `status="running"`
- Fehler passiert: Datei war zunächst nur untracked und wurde dadurch bei Workspace-Cleanup/Refresh entfernt
- Fix: `analysis/status.py` aus der implementierten Version wiederhergestellt und mit `b94601f` committed, damit sie nicht erneut verloren geht

---

## 2026-04-28

### Experiment-Runner: zweiter Lorenz-3D-Run hängt
`57c4ff3`

Run `54_evogrow_v1_seed7` (Lorenz periodic, EvoGrow v1, Seed 7) läuft seit 2026-04-28T07:46 ohne Fortschritt.
Ursache: Run wurde mit Git-Hash `04f458a7` generiert — **vor** der BFGS-Timeout-Implementierung.
Der neue Timeout greift nicht rückwirkend auf Runs mit altem Config-Hash.

Experiment-Runner: 234 → 242/300 Runs abgeschlossen.
Benchmark `benchmark_evogrow.jl`: ~93 → ~128/300 Runs (~43%).
`profile_init.jl`: weiterhin hängend auf Level 11, Stage 2, Lorenz 3D, Seed 42 — Daten bereits vorhanden.

---

## 2026-04-27

### BFGS-Timeout implementiert (`src/optimize/bfgs.jl`)
`59d6c16`

**Motivation**: `profile_init.jl` hängt seit 48+ Stunden auf einem einzelnen BFGS-Call (Lorenz 3D, Stage 2). `maxiters` begrenzt nur Iterationen, nicht Wall-Clock-Zeit.

**Umsetzung:**
- `time_limit_s::Float64 = 300.0` zu `BFGSOptimizer` ergänzt
- `time_limit = opt.time_limit_s` an beide `Optimization.solve`-Aufrufe (BFGS + Nelder-Mead Fallback) übergeben
- Bei Timeout gibt Optim.jl das beste bisher gefundene Ergebnis zurück — kein Absturz, kein NaN
- Logging: `log_warn("BFGS hit time_limit", ...)` wenn `retcode != Success`

**Parameterwahl**: 300s ist ~100× der medianen per-Call-Zeit (ca. 2–3s), greift bei normalen Runs nie.

### Paper 1 Reproducibility Protocol dokumentiert
`844bbe4`

Vollständige Dokumentation der Paper-1-Konfiguration direkt aus dem Code abgeleitet:
- alle 6 Varianten mit Slug, Basis, Progressions- und Usage-Mode
- alle 10 Benchmark-Systeme (exakt/Surrogate) mit IDs und True-Struktur
- sämtliche Hyperparameter explizit
- Seeds, Metriken, Execution-Loop, Output-Artefakte, Aggregationsregeln, Freeze-Klausel

Dabei 5 Diskrepanzen zwischen Dokumentation und Codebasis gefunden und behoben:
1. `EvoGrow`-Struct fehlte `progression`, `usage`, `use_pretuning`
2. `test.jl` und `test_evogrow_v2_lotka.jl` im Dateibaum, existieren nicht mehr
3. `run_odebench.jl` als Root-Datei angegeben, liegt in `benchmarks/`
4. `src/optimize/pretune.jl` existiert und wird genutzt, war undokumentiert
5. `experiments/` fehlte komplett im Dateibaum

### Experiment-Status (Stichtag 27.04.)

| Skript | Status |
|--------|--------|
| `experiments/run_experiment.jl paper1_phaseA_v1` | läuft — 234/300, ~6–7h Restlaufzeit |
| `benchmarks/benchmark_evogrow.jl` | läuft — 93/300, ~27–40h Restlaufzeit |
| `generalization_study.jl` | fertig (Output-CSVs vorhanden, 24.04.) |
| `profile_init.jl` | hängt seit 2 Tagen — Level 11, Stage 2, Lorenz 3D, Seed 42 |

---

## 2026-04-26

### Repository-Housekeeping
`1f9c643`

- `benchmarks/odeformer/results/` entfernt: alte Ergebnisdateien ohne reproduzierbaren Kontext
- `.gitignore` um `benchmarks/odeformer/results/` ergänzt

### Analyse-Pipeline für Paper 1 angelegt
`6eab0cf`, `ea3cc44`, `053d717`, `c1f51ef`, `0f8e677`, `8c1152d`, `d983abf`

- `analysis/` als dedizierter Bereich für Python-Auswertung angelegt
- `analysis/CONVENTIONS.md`: Architektur- und Regelwerk für die Python-Analyse
- `analysis/utils/`: `io.py`, `metrics.py`, `style.py` (Variant-Farben und Labels)
- `analysis/scripts/aggregate/aggregate_run_registry.py`: liest `run_registry.csv`, schreibt `aggregate_by_variant_system.csv`
- `analysis/scripts/plot/plot_exact_match_rates.py`: Exact-Match-Rate-Plot
- `analysis/scripts/plot/plot_stage_overshoot.py`: Stage-Overshoot-Plot (GP ausgeschlossen)
- `analysis/scripts/plot/table_main_results.py`: LaTeX-Tabelle Main Results

### Paper-1-Protokoll eingefroren (`docs/paper1_study_protocol.md`)
`2e65d57`, `9ca633a`, `c810703`

Core Goal: Paper 1 untersucht staged growth als Mechanismus zur kontrollierten Komplexitätssteigerung — nicht "bestes ODE-Discovery-System".

Hypothesen:
- H1: Stage-local v2.2 zeigt niedrigeren `mean_stage_overshoot` als v2.1 und v1
- H2: v2.2 liefert kompetitive `exact_match_rate` bei niedrigerem Complexity-Efficiency-Cost
- H3: `mean_wasted_levels` nur zwischen EvoGrow-Varianten; GP ausgeschlossen
- H4: usage-policy comparison (`hard`, `soft`, `passive`) als sekundäre Hypothese

Evidenzregeln:
- Surrogate-Systeme nicht für `exact_support_match` oder H1–H4-Strukturaussagen
- Systeme 2 und 24 (expected_stage=1) aus H1/H3/H4 ausgeschlossen
- No post-hoc cherry-picking; keine neuen Runs nach Ergebnisinspektion

### Variant-Slug vereinheitlicht
`9d25f44`

`evogrow_v2_2_stage_local` überall standardisiert: `benchmark_evogrow.jl`, Analyse-Skripte, `style.py`, Dokumentation.

### Logging: Datum im Timestamp ergänzt
`035e354`

`src/utils/logging.jl`: Timestamp-Format von `HH:MM:SS` auf `yyyy-mm-dd HH:MM:SS` erweitert.
Grund: über Nacht laufende Skripte erzeugen sonst Logs ohne Datumszuordnung.

---

## 2026-04-23

### Bugs gefunden und gefixt
`d27b697`

**Bug 1: `PolynomialBasis` fehlte kubischer Term für System 11**
- `evogrow_v1` nutzte `PolynomialBasis` (nur bis Grad 2), System 11 (Critical slowing down) erwartet `u1^3`
- Entscheidung: `evogrow_v1` auf `default_staged_polynomial_basis` umgestellt — gleicher Suchraum wie alle anderen Varianten, alles sofort entsperrt

**Bug 2: `log_exception` speicherte `DataType` statt `String`**
- `merged[:exception_type] = typeof(err)` schlug fehl weil `Dict{Symbol,String}` keinen `DataType` akzeptiert
- Fix: `string(typeof(err))` in `src/utils/logging.jl`

### Generalisierungsstudie geplant und implementiert (`generalization_study.jl`)
`f30af7c`

Frage: Wenn EvoODE auf Parametersatz A die korrekte Struktur findet — passt diese Struktur nach reinem Parameter-Refit auch auf ungesehene Parametersätze B–E derselben ODE-Familie?

- 3 Systeme (Logistic growth, Lotka-Volterra, SIR), je 5 Parametersätze (1 Train + 4 Test)
- 2 Varianten (evogrow_v2_2_stage_local, gp_baseline), 3 Seeds
- Baseline: frischer Discovery direkt auf Testtrajektorie
- Output: `debug_results/generalization_study/generalization_summary.csv`, `generalization_detail.csv`

### Erste Experiment-Befunde (paper1_phaseA_v1, ~40/300 Runs)

Bisher abgeschlossen: System 2 (Population growth) und System 3 (Logistic growth).

- Alle Runs: `success=true`, `exact_support_match=true`
- Loss ist deterministisch: identisch über alle Seeds (Pretuning + BFGS konvergiert immer ins gleiche Minimum)
- **Stage Overshoot:**
  - `evogrow_v2_1` (global plateau): mittlerer Overshoot 1.5 auf System 3 (expected_stage=2, landet in Stage 3–4)
  - Alle v2.2-Varianten (stage_local): Overshoot 0 — bleiben korrekt in Stage 2
  - Direkte Bestätigung der Kernhypothese

---

## 2026-04-22

### Pretuning (OLS Warm-Start)
`c4fad8a`

- `src/optimize/pretune.jl`: Ableitung per finite Differenzen, Design-Matrix aus Basistermen, OLS-Lösung als BFGS-Startwert
- `use_pretuning::Bool`-Flag in `EvoGrow`
- `level_log` um `elapsed_s`-Feld erweitert

### Experiment-Infrastruktur (WP-E1 bis WP-E3)
`c4fad8a`

- `experiments/generate_manifest.jl`: erzeugt Experiment-Verzeichnis, `manifest.json`, alle per-Run `config.json` + `status.json`
- `experiments/run_experiment.jl`: sequentieller Runner mit robustem Fehlerhandling, atomaren Writes, restart-fähig
- `experiments/aggregate.jl`: leitet `run_registry.csv` aus per-Run-Ordnern ab, idempotent
- Per-Run-Dateiprotokoll: `config.json` (immutable), `status.json` (non-atomic), `result.json` + `metrics.json` (atomar via tmp→rename)

### Debug- und Profiling-Skripte
`c4fad8a`

- `debug_single.jl`: Einzelrun auf Lotka-Volterra mit verbose Logging und PNG-Output
- `profile_init.jl`: Vergleich random vs. pretune Initialisierung auf Lotka-Volterra + Lorenz, 3 Seeds

### Experiment gestartet

`paper1_phaseA_v1`: 10 Systeme × 6 Varianten × 5 Seeds = 300 Runs, exploratory

---

## 2026-04-21

### EvoGrow v2.2 (stage_local)
`224714d`

- `StageProgressionPolicy` mit Modus `:stage_local` und `min_levels_per_stage`
- `StageUsagePolicy` mit Modi `:hard`, `:soft`, `:passive` und `new_term_bias_prob`
- Stage-lokale Plateau-Detektion mit Mindestbudget pro Stage
- Benchmark-Matrix: 10 Systeme × 6 Varianten × 5 Seeds vollständig

---

## 2026-04-20

### Projekt-Fundament
`84f94e8`, `4d8bd2e`, `f5e1d9c`, `a811927`

- Core stabilisiert: EvoGrow und GP laufen sauber mit konsistentem Loss (`discover()` end-to-end)
- Benchmark-Infrastruktur angelegt: 10-System-Suite, erste Varianten
- Housekeeping: Stubs gefixt, Docstrings, Interface-Bereinigung

---

# Paper 1 — Zuschnitt zur Diskussion

**Stand:** 2026-08-14, auf Basis der Pilotdaten. Die Kampagne läuft noch nicht.
**Zweck:** Diskussionsgrundlage. Keine Entscheidung, keine Festlegung.

Alle Zahlen unten stammen aus je **einer** Zelle pro System (`pretune_on`, IC 1, Seed 42). Die
Kampagne rechnet zwölf pro System, was mehrere Aussagen unten verändern kann.

---

## 1. Der Befund, der die Diskussion auslöst

Auf den exakten Systemen — jenen, deren wahre rechte Seite in der Basis darstellbar ist:

| | |
|---|---|
| ausgewertet | 10 (9× 2D, 1× 3D) |
| Struktur gefunden (`pruned_match`) | **4 (40 %)** |
| davon in 3D | **0 von 1** |

Und drei exakte 3D-Systeme laufen noch mit Losses zwischen 60 und 312 — das sieht nicht nach
Erfolg aus.

### Es ist kein Metrikartefakt

Naheliegende Hoffnung: Die Struktur wird gefunden, ist nur unter Zusatztermen begraben, und
`pruned_match` ist bloß zu streng. Geprüft:

| | |
|---|---|
| `pruned_match = true` | 4 von 10 |
| wahrer Support **enthalten** (Obermenge) | 4 von 10 |

**Dieselbe Zahl.** In jedem gescheiterten Fall fehlen tatsächlich ein bis drei Terme. Die Suche
findet die Struktur nicht — sie versteckt sie nicht.

### Eine sehr scharfe Trennlinie

| | Loss-Bereich |
|---|---|
| gefunden (4×) | 7.4e-15 · 1.7e-14 · 7.0e-12 · **4.2e-08** |
| nicht gefunden (6×) | **1.3e-04** · 2.7e-04 · 6.4e-04 · 1.0e-03 · 2.0e-03 · 2.3e-01 |

Vier Größenordnungen Lücke, kein Grenzfall, über zwei Dimensionsklassen hinweg. Entweder die
Struktur wird gefunden und der Loss fällt auf Rundungsniveau — oder sie wird verfehlt und der Loss
bleibt bei ~1e-4 stehen. Ein Zwischenbereich existiert nicht.

---

## 2. Die diagnostizierte Ursache

**System 54** (3D, exakt) ist der Beleg, weil dort nachweisbar nichts gefehlt hat:

```
benötigte Stufe je Gleichung:  [1, 3, 3]
Stage-Caps:                    [None, 3, 3]
tatsächlich erreicht:          [5, 3, 3]
```

Die Gleichungen 2 und 3 haben exakt die Stufe erreicht, die ihr wahrer Support verlangt. **Alle
nötigen Terme waren verfügbar.** Ergebnis trotzdem `loss = 1.0e-03`, `pruned_match = false`.

Was gefunden wurde:

| Gl. | wahr | gefunden | fehlt | zuviel |
|---|---|---|---|---|
| 1 | `u1`, `u2` | `u1²`, `u2`, `u2²`, `u3` | **`u1`** | 3 |
| 2 | `u1`, `u2`, `u1*u3` | `u1`, `u2`, `u1*u3`, `u1²`, `u3`, `u3²` | **nichts** | 3 |
| 3 | `u3`, `u1*u2` | `u1`, `u1²`, `u2`, `u3` | **`u1*u2`** | 3 |

**Gleichung 2 ist der Schlüssel.** Sie hat den vollständigen wahren Support gefunden, inklusive des
Kreuzterms aus Stufe 3. Sie scheitert ausschließlich an drei überflüssigen Termen — und sie steht
bei genau **sechs** Termen, also am Limit `MAX_TERMS = 6`.

Damit ist sie eingesperrt: Sie kann nichts mehr hinzufügen, weil das Budget erschöpft ist. Und sie
kann nichts entfernen, weil `_expand` **nur hinzufügt**. Die drei falschen Terme bleiben dauerhaft,
zusammen mit den drei richtigen.

Die Gleichungen 1 und 3 zeigen dieselbe Mechanik früher: Ein falscher Term kam herein — `u1²` statt
`u1`, lineare Terme statt des Kreuzterms — und konnte nie wieder verschwinden.

### Der Mechanismus in einem Satz

> Die Suche scheitert nicht daran, dass sie die richtige Struktur nicht **darstellen** könnte,
> sondern daran, dass sie eine falsche Festlegung **nicht zurücknehmen** kann.

Das steht als Vermutung bereits in `CLAUDE.md` unter „Known Gaps". Neu ist, dass es an einem Fall
belegt ist, in dem alles Nötige verfügbar war.

---

## 3. Das Problem für das Paper

Die Aussage von Paper 1 ist **nicht** „wir finden Strukturen besser". Sie lautet, dass Eskalation
über das hinaus, was die Daten hergeben, **vorab vorhersagbar und beweisbar verschwendet** ist.

Und diese Aussage tragen die Pilotdaten sauber:

- Der Stage-Cap greift in **zehn von zehn** Fällen exakt — Gleichungen enden dort, wo die
  Voraus-Analyse es vorhergesagt hat
- Bei System 54 heißt das: Gleichung 2 und 3 bei Stufe 3 statt 5, ohne Qualitätsverlust
- Auf System 3 verbrennt die ungekappte Variante 12 von 30 Leveln und liefert denselben Loss

**Die zu erwartende Frage lautet trotzdem:** Wozu eine effiziente Suche, die die Antwort nicht
findet?

Darauf gibt es zwei ehrliche Antworten.

### Option A — das Mechanismus-Paper

Die Aussage ist Komplexitätskontrolle. Die Trefferquote wird als Limitation berichtet, mit
diagnostizierter Ursache und quantifiziertem Beleg.

*Dafür:* Es ist wahr, es ist belegt, und dieses Projekt kann Fehleranalyse glaubwürdig — zwei
Varianten wurden an ihren eigenen Gates verworfen und als Fehleranalyse behalten.

*Dagegen:* Bescheiden. Ein Gutachter kann sagen, der Mechanismus optimiere etwas, das nicht
funktioniert.

### Option B — erst die Suche reparieren

Beam Search bauen, Trefferquote messen, dann ein stärkeres Paper.

*Dafür:* Adressiert die Ursache statt sie zu berichten.

*Dagegen:* Monate. Und Beam Search für Gleichungsentdeckung ist Stand der Technik — die Neuheit
läge allein in der Kombination (siehe §5).

### Was die Kampagne noch beitragen kann

Die 40 % stammen aus **einer** Zelle pro System. Die Kampagne rechnet **zwölf**.

Falls die Trefferquote seedabhängig ist, ist „in 5 von 12 Läufen gefunden" eine wesentlich reichere
Aussage als ein binäres Nein — und sie stützt Option A deutlich besser. Findet sich die Struktur in
**keinem** der zwölf Läufe, ist die Skepsis bestätigt und der Zuschnitt muss neu gedacht werden.

**Diese Information kostet keinen zusätzlichen Rechenlauf.** Sie sollte vor der Zuschnittsentscheidung
vorliegen.

---

## 4. Der naheliegende Lösungsansatz

Statt pro Elternteil einige zufällige Kinder zu erzeugen: **alle möglichen Ein-Term-Erweiterungen
aufzählen, alle bewerten, die X besten weiterziehen.**

Das adressiert den beobachteten Fehler **besser als ein Entfernen-Operator**. Denn das Problem bei
System 54 war nicht, dass ein falscher Term nicht wieder wegging — es war, dass die Alternative nie
bewertet wurde. Gleichung 1 nahm `u1²`, und `u1` kam nie zum Zug. Bei vollständiger Aufzählung wären
beide bewertet worden.

Ein Entfernen-Operator repariert im Nachhinein. Aufzählen verhindert den Fehler.

**Zusatz:** Beam Search allein ist gierig — eine Linie, die zwischendurch schlechter aussieht, geht
verloren. `u1` allein passt womöglich schlechter als `u1²` allein, und erst mit `u2` dreht sich das.
Gegenmittel ist eine **stochastische Beimischung** (etwa 90 % beste, 10 % zufällige), die solche
Linien am Leben hält.

### Kosten

Die Basis hat bei Dimension *d* insgesamt `5d + d(d-1)/2` Terme:

| dim | Terme | verfügbar bei Stufe 3 |
|---|---|---|
| 2 | 11 | 5 |
| 3 | 18 | 9 |
| 4 | 26 | 14 |

Bei dim 3, Stufe 3: bis zu 9 Erweiterungen × 3 Gleichungen = **27 Kandidaten pro Elternteil**, bei
Beam-Breite 10 also **270 Fits pro Level** gegen heute 20. Faktor ~13, bei Stufe 5 eher 25.

**Das ist bezahlbar, weil das Werkzeug existiert.** `EvoGrowScreening` (870 Zeilen, derzeit als
„performance-only" geführt) bewertet Kandidaten über das Ableitungsresiduum, ohne sie teuer zu
fitten. Alle 27 billig vorsortieren, nur die besten K richtig fitten. Aus einem Nebenmechanismus
würde damit der Ermöglicher der Hauptidee.

---

## 5. Abgrenzung gegenüber Beam Search — der kritische Punkt

**Beam Search für Gleichungsentdeckung existiert.** Das muss vorne stehen, nicht in einer Fußnote.

- *Combinatorial search for selecting the structure of models of dynamical systems* (Engineering
  Applications of AI) vergleicht Beam Search und Tabu Search genau für Strukturauswahl in
  dynamischen Systemen
- *ODEFormer* nutzt Beam Sampling zur ODE-Dekodierung
- Beam Search ist in der klassischen Statistik als **Forward Stepwise Selection** seit Jahrzehnten
  etabliert

**Beam Search als solches ist kein Beitrag.** Wer das behauptet, wird zu Recht abgelehnt.

### Wo die Abgrenzung tatsächlich liegen könnte

Der entscheidende Unterschied ist, **was die beiden Mechanismen regeln**:

| | regelt |
|---|---|
| **Beam Search** | *wie viele* Kandidaten ich weiterverfolge |
| **Stufen-Grammatik** | *welche* Kandidaten überhaupt existieren, und ab wann |
| **Look-ahead-Cap** | *wie weit* jede Gleichung gehen darf, aus den Daten vorab bestimmt |

Diese drei sind **orthogonal**. Beam Search in der Literatur sucht im vollen Raum mit begrenzter
Breite. Der hier verfolgte Ansatz **beschränkt den Raum selbst** — zeitlich über die gestufte
Grammatik, und pro Gleichung über einen vorab aus der Trajektorie berechneten Deckel.

Die Kombination „gestufte Grammatik + gleichungsweiser Deckel + Beam innerhalb der Stufe" ist
plausibel nicht publiziert. Aber:

> **Das muss vor jeder Festlegung durch eine Literaturrecherche geprüft werden.** Die Kombination
> ist naheliegend genug, dass sie existieren könnte, und die Abgrenzung trägt das ganze Argument.

### Was der Cap zusätzlich leistet

Beam Search braucht eine Abbruchentscheidung: Wann höre ich auf, tiefer zu gehen? Üblich sind
Informationskriterien oder Kreuzvalidierung — beides *nachträglich*, nach dem Rechnen.

Der Look-ahead-Cap entscheidet **vorher**, aus Trajektorie und Basis, ohne einen einzigen Fit. Das
ist eine andere Art von Aussage, und sie ist unabhängig davon, welcher Suchalgorithmus darunter
läuft. Genau deshalb kombiniert er auch mit v2.2 **und** v3.

**Das ist vermutlich die tragfähigste Formulierung des Beitrags:** nicht „ein besserer Sucher",
sondern „eine datengetriebene Vorabgrenze für die Modellkomplexität, die jeden Sucher billiger
macht".

---

## 6. Zu entscheiden

| Frage | wann | Grundlage |
|---|---|---|
| Trägt die Trefferquote über 12 Läufe pro System? | nach der Kampagne | kostenlos, läuft ohnehin |
| Option A oder B | danach | die obige Zahl |
| Ist die Kombination neu? | **vor** jeder Festlegung | Literaturrecherche |
| Beam Search implementieren | frühestens nach Paper 1 | anderer Suchalgorithmus, anderer Fingerprint |

**Für Paper 1 nicht implementieren.** Der Befund ist stark genug als Limitation, er ist präzise
formulierbar, und er ist die natürliche Überleitung zum nächsten Paper.

Die Limitation lautet dann nicht „unsere Methode findet die Struktur oft nicht", sondern:

> Auf System 54 fand Gleichung 2 den vollständigen wahren Support und scheiterte allein an drei
> überzähligen Termen bei ausgeschöpftem Termbudget. Die Suche kann eine falsche Festlegung nicht
> zurücknehmen, weil sie ausschließlich additiv ist.

Das ist eine Aussage mit einem konkreten nächsten Schritt statt eines Eingeständnisses.

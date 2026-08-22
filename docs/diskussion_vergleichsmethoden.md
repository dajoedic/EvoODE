# Diskussionsgrundlage — Welche Vergleiche verwenden wir?

**Stand 22.08.2026.** Gesprächsvorlage. Zu entscheiden ist, gegen welche publizierten Arbeiten
EvoODE gestellt wird und in welcher Form. Solange das offen ist, darf Paper 1 über keine
Fremdmethode eine Aussage treffen — auch keine vorsichtige.

Zugehörig: `docs/paper1_odebench_protocol_alignment.md` (der Audit selbst, externe Spalten leer),
`docs/diskussion_repraesentationsraum.md` (Suchraum), `PAPER_1.md` §5.5.

---

## 1. Worum es geht

Paper 1 verwendet ODEBench. Damit liegt es nahe, unsere Zahlen neben publizierte Zahlen auf
demselben Benchmark zu legen. Genau das ist derzeit **nicht zulässig**, und zwar nicht aus Vorsicht,
sondern weil drei Voraussetzungen ungeprüft sind.

Der Audit hat eine Tabelle mit sieben Zeilen — Systeme, Anfangsbedingungen, Zeitspanne,
Abtastgitter, Rauschen, Metrikdefinition, Aggregation — und drei Spalten für Fremdquellen. **In
allen drei Spalten steht überall „zu prüfen".** Die Entscheidung, die ansteht, ist: welche Quellen
kommen in diese Spalten, und was tun wir mit dem Ergebnis.

---

## 2. Drei Ebenen der Vergleichbarkeit

Sie werden oft vermischt. Getrennt sind sie entscheidbar.

### Ebene 1 — Datenprotokoll

Gleiche Systeme, gleiche Anfangsbedingungen, gleiche Zeitspanne, gleiches Gitter, gleiches Rauschen?

**Hier haben wir eine bekannte Abweichung, und sie geht zu unseren Gunsten.** Wir übernehmen die
Abtastung des Datensatzes (512 Punkte über `t ∈ [0,10]`, beide IC-Sätze), **integrieren die
Trajektorien aber selbst** mit `abstol = reltol = 1e-9`. Die mitgelieferten Trajektorien würden
MSE-Böden zwischen `2,5e-2` und `6,1e-10` erzwingen — oberhalb dessen, was unser Verfahren auf
mehreren Systemen erreicht.

Wenn publizierte Zahlen auf den mitgelieferten Trajektorien beruhen, arbeiten wir auf saubereren
Daten als der Vergleich. Das muss deklariert werden, und zwar unabhängig davon, wie der Vergleich
ausgeht.

### Ebene 2 — Metrik und Erfolgskriterium

Was zählt als Treffer? Ein R²-Schwellwert, ein MSE, eine Struktur-Übereinstimmung? Über wie viele
Seeds, wie aggregiert, und was passiert mit fehlgeschlagenen Läufen?

Unsere Metriken sind getrennt nach Systemklasse: exakte Systeme über Support-Recovery,
Surrogatsysteme über R². Ein publizierter Aggregatwert über alle 63 Systeme ist damit strukturell
nicht dasselbe wie unsere Zahlen, selbst bei identischem Datenprotokoll.

### Ebene 3 — Repräsentationsfähigkeit *(die Ebene, die üblicherweise fehlt)*

**Kann die Methode die wahre Struktur überhaupt ausdrücken?** In zwei Spalten, weil eine nicht
reicht:

| Spalte | Frage |
|---|---|
| *in principle* | Könnte die Modellklasse der Methode die Struktur ausdrücken? |
| *under the evaluated protocol* | War sie unter den tatsächlich verwendeten Operatoren, Bibliotheken, Komplexitätsgrenzen und Limits erreichbar? |

Der Unterschied ist nicht spitzfindig. Ein Bibliotheksverfahren kann beliebige Terme tragen — wenn
der publizierte Lauf Polynome bis Grad 3 verwendet hat, ist ein Sättigungsterm dort unerreichbar.
Ein Verfahren mit freier Grammatik kann einen Operator erlauben und ihn durch eine
Komplexitätsstrafe faktisch ausschließen. Ein vortrainiertes Modell ist zusätzlich durch seine
Trainingsverteilung begrenzt.

**Und diese Ebene trifft uns selbst am härtesten.** Unsere Basis stellt 20 der 63 Systeme exakt dar.
Auf den anderen 43 messen wir Approximationsgüte, nicht Strukturfindung. Wer diese Spalte einführt,
muss sie zuerst auf die eigene Methode anwenden.

---

## 3. Was wir über unsere eigene Lage inzwischen wissen

Ein Befund von heute macht die Diskussion einfacher, als sie gestern gewesen wäre.

Die suchfreie Referenz (WP-R1) hat gemessen, wie gut die heutige Basis die 63 Systeme im
Ableitungsraum überhaupt treffen kann: Surrogatsysteme erreichen einen Median von **0,999993**,
exakte Systeme 0,999998. Auf dem beobachteten Wertebereich ist unsere Basis also **nicht das
Nadelöhr**, das die Abdeckungszahl vermuten lässt.

Für die Vergleichsdiskussion heißt das: Wir stehen bei der Repräsentationsfrage besser da, als
„20 von 63" klingt — aber wir stehen nicht außerhalb davon. Die Spalte gehört ausgefüllt, für uns
zuerst.

---

## 4. Die Kandidaten

Nach Rolle geordnet, nicht nach Prominenz. **Alle inhaltlichen Angaben sind zu prüfen** — das ist
gerade der Zweck des Audits.

| Rolle | Kandidat | Was er bringt | Was er kostet |
|---|---|---|---|
| **Benchmark-Quelle** | die Arbeit, die ODEBench eingeführt hat | Ohne sie kein Bezugsrahmen: Systeme, Anfangsbedingungen und Trajektorien stammen von dort. Ihre Protokollentscheidungen sind der Maßstab, gegen den unsere Abweichung deklariert wird | gering — muss ohnehin gelesen werden |
| **freie symbolische Regression** | ein Vertreter mit offener Grammatik (PySR o. ä.) | der interessante Gegenpol: ausdrucksstärkerer Raum, globale Suche. Genau die Achse, auf der EvoODE positioniert ist | Repräsentationsspalte aufwendig — Operatoren *und* Komplexitätsgrenzen müssen aus dem Lauf rekonstruiert werden |
| **Bibliotheksverfahren** | eine SINDy-Referenz | der nächste Verwandte: feste Bibliothek, keine Strukturentwicklung. Der Vergleich, der unseren Beitrag am direktesten einordnet | Bibliothek des publizierten Laufs muss bekannt sein, sonst ist die Zeile unausfüllbar |
| **vortrainiertes Modell** | ein Sequenzmodell für ODE-Entdeckung | zeigt eine ganz andere Methodenfamilie | Repräsentationsfähigkeit hängt an der Trainingsverteilung und ist praktisch kaum prüfbar |
| **weitere GP-Systeme** | Operon, ProGED, … | Breite | hoher Aufwand je Quelle, geringer Zusatznutzen für die Positionierung |

Eine Abkürzung, die es zu prüfen lohnt: Wenn eine der Arbeiten bereits **Vergleichszahlen für die
anderen Verfahren** auf demselben Benchmark berichtet, ließe sich ein Teil der Tabelle aus einer
einzigen Quelle füllen — mit dem Vorbehalt, dass fremde Reimplementierungen ihre eigenen
Protokollentscheidungen tragen.

---

## 5. Vier Fragen zur Entscheidung

1. **Wie breit?** Minimal wäre die Benchmark-Quelle allein — sie ist Pflicht, weil unsere Daten von
   dort stammen. Jede weitere Quelle kostet Lesearbeit und bringt Positionierung. Wo ist die Grenze?
2. **Zahlen übernehmen oder nur Protokolle auditieren?** Das sind verschiedene Ambitionen. „Wir
   berichten, unter welchen Bedingungen publizierte Zahlen mit unseren vergleichbar wären" ist
   deutlich billiger und deutlich sicherer als „wir stellen unsere Zahlen daneben".
3. **Was ist der Anspruch von Paper 1 gegenüber Fremdmethoden — Einordnung oder Wettbewerb?** Bisher
   steht in `PAPER_1.md` ausdrücklich *Einordnung*: keine Sieges- oder Niederlagenaussagen. Bleibt
   das so, ist Frage 2 fast schon beantwortet.
4. **Wie gehen wir mit der Repräsentationsspalte um, wenn sie uns selbst trifft?** Meine Position:
   zuerst auf uns anwenden, mit den WP-R1-Zahlen, und erst dann auf andere. Alles andere wäre
   angreifbar.

---

## 6. Meine Empfehlung

**Für Paper 1: die Benchmark-Quelle vollständig auditieren, alles andere als Kontext.** Der Beitrag
von Paper 1 ist ein Suchraum-Controller, kein Benchmark-Sieg; ein breiter Vergleich würde Arbeit
kosten, die der Aussage nichts hinzufügt, und gleichzeitig die Angriffsfläche vergrößern.

**Der breite Vergleich gehört in Paper 3.** Dort ist er der Zweck der Arbeit — und dort ist der
Suchraum von EvoODE nach der geplanten Erweiterung auch ausdrucksstark genug, dass der Vergleich
nicht in Wahrheit unsere Bibliothek misst.

**Die Repräsentationsspalte aber jetzt schon einführen**, auch wenn nur eine Quelle auditiert wird.
Sie ist billig, solange die Tabelle klein ist, und sie ist der Teil dieses Audits, der über die
Buchhaltung hinausgeht: Eine Vergleichsdimension, die in diesem Feld üblicherweise nicht berichtet
wird, ist selbst ein Ergebnis.

---

## 7. Was ich mit einer Antwort sofort tun kann

Nenn mir die Quellen, dann fülle ich die sieben Protokollzeilen plus die zwei
Repräsentationsspalten je Quelle und lege das Ergebnis als Audit-Tabelle vor. Wo eine Angabe in der
Publikation nicht steht, wird das als *nicht berichtet* eingetragen — das ist ein Befund und keine
Lücke.

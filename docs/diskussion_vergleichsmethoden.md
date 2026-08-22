# Diskussionsgrundlage — Welche Vergleiche verwenden wir?

**Stand 22.08.2026.** Abschnitte 1–7 sind die Vorlage *vor* der Diskussion, **Abschnitt 8 hält das
Ergebnis fest** — inklusive zweier Punkte, die in der Vorlage fehlten. Wo sich beide widersprechen,
gilt Abschnitt 8.

Zu entscheiden war, gegen welche publizierten Arbeiten EvoODE gestellt wird und in welcher Form.

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


---

## 8. Ergebnis der Diskussion (22.08.2026)

### Entschieden: harte Regel für Paper 1

> **Keine quantitative Cross-Method-Leistungsaussage.**

Nicht „vorsichtig", nicht „ungefähr", sondern keine. Paper 1 untersucht, ob kontrolliertes,
datenadaptives Wachstum des Suchraums etwas bringt — eine interne methodische Frage. Ein
Fremdvergleich würde eine zweite Fragestellung eröffnen und Angriffsfläche schaffen, ohne der
Aussage etwas hinzuzufügen.

Erlaubt sind Aussagen über *Protokolle*: dass ODEBench von mehreren Verfahren verwendet wurde, dass
deren Suchräume und Evaluationsprotokolle sich unterscheiden, dass publizierte Zahlen deshalb nicht
als direkt vergleichbar behandelt werden, und dass der breite Vergleich bewusst verschoben ist.
Nicht erlaubt sind „besser als", „konkurrenzfähig mit", „ähnliche Leistung wie".

### Entschieden: zwei Quellen für Paper 1

**ODEFormer / ODEBench** als Pflichtquelle — Benchmarkdefinition, Protokoll und zugleich
Kontextquelle, weil dort mehrere Methodenfamilien auf demselben Benchmark berichtet werden.

**Tonda et al. 2025**, *When Data Transformations Mislead Symbolic Regression: Deceptive Search
Spaces in System Identification* — nicht als Leistungsreferenz, sondern als **methodische Evidenz**.

### Warum die zweite Quelle heute besonders zählt

Tonda et al. zeigen, dass die Überführung eines dynamischen Problems in ein **algebraisches
Ableitungsproblem** irreführende Suchlandschaften erzeugen kann: Ein gutes Ziel im Ableitungsraum
garantiert nicht, dass die dynamisch richtige Struktur bevorzugt wird.

Das trifft zwei Stellen dieses Projekts direkt — das Pretuning und die Referenz aus WP-R1, die
ebenfalls im Ableitungsraum misst. **Und unsere eigenen Zahlen von heute reproduzieren den Effekt
unabhängig:** 13 der 126 Referenzmodelle divergieren beim Integrieren, und bei den exakten Systemen
liegt der Mittelwert der Trajektoriengüte bei −2,8 gegen einen Median von 0,9999. Nahezu perfekte
Ableitungsanpassung, unbrauchbare Dynamik.

Zwei Konsequenzen:

1. **Die Familien-Rangfolge aus WP-R1 §11 erbt diesen Vorbehalt.** Sie ist im Ableitungsraum
   gemessen und kann in genau der Weise täuschen, die Tonda et al. beschreiben. Sie bleibt
   verwertbar, aber nur mit dieser Einschränkung und, wo vorhanden, neben der Trajektoriengüte.
2. **Für das Verfahren stützt der Befund eine bestehende Designentscheidung:** Ableitungsraum als
   billiger Warmstart, Trajektorienraum als verbindliche Bewertung. Formulierung fürs Paper:
   *derivative-space optimization is useful as a computational surrogate, but trajectory-space
   verification is necessary because the transformed objective need not preserve the true ranking of
   dynamical models.*

### Neu: eine dritte Repräsentationsdimension

Aus zwei Spalten werden drei:

| Dimension | Frage | Für Fremdmethoden |
|---|---|---|
| *in principle representable* | Kann die Modellklasse die Wahrheit ausdrücken? | ja / nein / unklar |
| *representable under evaluated protocol* | War sie im tatsächlich evaluierten Raum erreichbar? | ja / nein / unklar / nicht berichtet |
| **best attainable functional fit** | Wie gut kann dieser Raum die Dynamik unabhängig von Suchfehlern überhaupt treffen? | **optional**, wo verfügbar |

Die dritte Dimension ist für EvoODE durch WP-R1 vorhanden und für die meisten Fremdmethoden nicht
rekonstruierbar. Sie darf deshalb **keine Pflichtspalte** werden — der Audit darf keine Anforderung
erzeugen, die nur die eigene Methode erfüllt. *Nicht berichtet* ist ein Befund.

### Neu: der Datensatz muss versioniert werden

„Wir verwenden ODEBench" ist als Protokollangabe zu unscharf; verschiedene Repository- oder
Release-Stände können unterschiedliche Punktzahlen, Generatoren und Solver-Defaults tragen.

**Geprüft, und es ist eine echte Lücke:** Im Repository ist die Herkunft von
`benchmarks/data/strogatz_extended.json` nirgends festgehalten — kein Commit, kein Release, keine
URL. Das `source`-Feld je System nennt die Lehrbuchstelle („strogatz p.20"), nicht den Datensatz.
Verifizierbar ist bisher nur:

```text
sha256  b11f8bda01ceee5c5c9445521ac74c8819361af4251bb90c0be398aaeb1a1136
im Repo seit  706549f (2026-04-30)
63 Systeme, alle mit mitgelieferten Lösungen
```

Zu ergänzen sind Herkunft (Repository/Release/Commit oder DOI) und die Angabe, dass wir die
mitgelieferten Trajektorien **nicht** verwenden. **Dafür brauche ich eine Angabe von dir: woher
stammt die Datei?**

### Neu: Formulierung für die eigene Trajektorienerzeugung

Nicht „wir verwenden sauberere ODEBench-Daten" — das wertet das Originalprotokoll ab und lädt zur
Gegenfrage ein. Stattdessen:

> We preserve the ODEBench systems, parameterizations, initial conditions and sampling grid, but
> regenerate trajectories at stricter numerical tolerances to avoid solver-error floors interfering
> with the accuracy regime studied here.

Und daraus abgeleitet: *published ODEBench numbers obtained on the released trajectories are not
treated as directly comparable.*

### Paper 3: die Kernmatrix steht

Kein Leaderboard, sondern ein Vergleich von **Suchphilosophien** — je eine Methode je Philosophie:

| Rolle | Methode |
|---|---|
| feste Bibliothek | SINDy |
| freie symbolische Suche | PySR |
| vortrainierte symbolische Inferenz | ODEFormer oder aktueller Nachfolger |
| kontrolliertes inkrementelles Wachstum | EvoODE |

Die dritte Zeile wird **spät** eingefroren — welcher symbolische Transformer dann der relevante
Vertreter ist, entscheidet sich kurz vor dem Experiment.

### Die Kette hat ein viertes Glied bekommen

```text
Representability -> Identifiability -> Search Recoverability -> Evaluation
```

Ein gescheiterter Recovery-Versuch darf erst dann der Suche zugeschrieben werden, wenn zusätzlich
geklärt ist, dass das **Evaluationsprotokoll** die relevante Eigenschaft überhaupt misst. Genau
darum geht es bei Tonda et al., und genau das ist der Grund, warum das vierte Glied kein
Formalismus ist.

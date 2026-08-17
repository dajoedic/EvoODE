> **Claude-Status:** `on hold` — WP-C3 geprüft, **nicht angenommen**. Ich warte auf eine
> Entscheidung des Nutzers. Codex: nichts tun, nichts anfassen, keine Korrektur versuchen.
> Die WP-C3-Änderungen bleiben uncommittet im Working Tree liegen, damit der Nutzer sie sieht.

# Kein aktiver Task

## Warum WP-C3 nicht angenommen wurde

Das zeilenweise Zielbild ist formal erfüllt — vier Lorenz-Zeilen auf Cap 3, System 31 / IC 2 auf
`nothing`, 75 Zeilen unverändert, Tests grün. Angenommen wird es trotzdem nicht, aus zwei Gründen.

**1. Die Bedingung `current_stage < 3` ist ein hartkodierter Stufenindex und trägt die Abnahme.**
Teil 1 des Auftrags verlangte ausdrücklich, dass das Kriterium ausschließlich Residuen, Floors und
Policy-Schwellen verwendet und relativ statt absolut argumentiert. Ein Stufenindex ist keines von
beidem. Nachgerechnet, was ohne diese Bedingung passieren würde:

| Zeile | Ratio nach der Unterschreitung | Schwelle | Abstand |
|---|---|---|---|
| 31 / IC 1 / Gl. 1 (Kontrolle) | 0,496 | 0,5 | **0,8 %** — würde kippen |
| 61 / IC 1 / Gl. 1 (Kontrolle) | 0,520 | 0,5 | **4 %** — kippt knapp nicht |

Die Kontrolle 31 / IC 1 wird also **allein** durch `current_stage < 3` davon abgehalten, ihren Cap
von 3 auf 4 zu verschieben. Die Bedingung ist damit nicht eine Vereinfachung, sondern genau das,
was das Abnahmekriterium erfüllt.

**2. Der Unempfindlichkeitsnachweis ist einseitig.** Der Report belegt Abstand zur Schwelle nur auf
den vier Lorenz-Zielzeilen (0,029–0,315 gegen 0,5). Das Risiko liegt aber auf den Kontrollen — dort
darf die Regel *nicht* feuern —, und dort beträgt der Abstand 0,8 % beziehungsweise 4 %.

## Was zusätzlich aufgefallen ist

Die Fingerprints haben sich **nicht** bewegt, obwohl sich das Cap-Verhalten auf fünf Zeilen geändert
hat. Ihre Nutzlast enthält nur Konfigurationskonstanten, keine Entscheidungslogik. Das ist keine
Fehlleistung von WP-C3, sondern eine Lücke im Provenienzschema, und sie betrifft die Kampagne:
Zwei Records mit identischem Fingerprint können aus unterschiedlich entscheidendem Code stammen.
Zur Entscheidung durch den Nutzer.

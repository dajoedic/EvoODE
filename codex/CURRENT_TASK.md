# WP-N1 — Die Konstante, und das Modell endlich mitschreiben

**Language: Julia**

## Kontext und Zweck

Zwei Grundlagenluecken, die vor jeder weiteren Methodenarbeit geschlossen werden muessen.

**Erstens: der Basis fehlt der konstante Term.** `src/basis/staged_polynomial.jl` kennt `u1`,
`u1^2`, `u1*u2`, `u1^3`, `sin`/`cos` — aber keine `1`. Der Audit in
`docs/paper1_odebench_protocol_alignment.md` §2.6 hat das quantifiziert: unsere Basis stellt 20 von
63 ODEBench-Systemen exakt dar, SINDys schlichte Polynombibliothek 40. **Zehn Systeme scheitern
allein an der Konstante** (1, 5, 9, 17, 23, 43, 52, 57, 58, 59), bei 15 weiteren ist sie
mitbeteiligt. System 1 ist der RC-Kondensator — das einfachste System des Benchmarks.

**Zweitens: die gefundenen Parameterwerte werden nie gespeichert.** `run_regression.jl:831` schreibt
mit `active_term_names(...)` nur die Termnamen. Die Koeffizienten aus `result.params` gehen
verloren. Damit laesst sich kein gefundenes Modell rekonstruieren, neu simulieren oder auf andere
Anfangswerte anwenden — die Generalisierungsmetrik der Literatur ist unerreichbar, und Design-Prinzip
6 („Metadaten bewahren") ist verletzt. Die 756 Zellen der Phase-B-Kampagne sind davon betroffen und
nicht nachtraeglich reparierbar.

## Absolute Randbedingung: die Kampagnenidentitaet bleibt unberuehrt

Die Phase-B-Kampagne (`git 91f88c4`, `config_fingerprint 604e79733b22d64d`,
`stage_cap_behavior_fingerprint ffb0266c7913352c`, 756 Records) ist eingefroren und wird
**ausschliesslich lesend** angefasst. Konkret:

- `default_staged_polynomial_basis` behaelt exakt sein heutiges Verhalten. Die Konstante kommt in
  eine **neue, zusaetzliche** Basisfunktion, nicht in die bestehende.
- Ein bestehender Lauf, der die alte Basis waehlt, muss weiterhin bitgleiche Ergebnisse liefern.
- Aendert sich ein Fingerprint fuer die bestehende Konfiguration, ist das ein **Abbruchgrund**.

## Teil 1 — Die Parameterwerte in den Record

Ergaenze den Record um die Koeffizienten des gefundenen Modells, direkt neben `support_terms`, so
dass Termname und Wert **eindeutig einander zugeordnet** sind. Die genaue Form ist deine
Entscheidung; sie muss nur diese Bedingung erfuellen: aus Record plus Basisangabe muss sich das
Modell **ohne Rueckgriff auf den Suchlauf** wieder aufbauen und integrieren lassen.

Schreibe zusaetzlich mit, **welche Basis** verwendet wurde, als Name oder Kennung. Ohne diese Angabe
ist die Termliste mehrdeutig, sobald es zwei Basisvarianten gibt.

Das ist eine reine Ergaenzung der Ausgabe. Sie darf den Suchverlauf nicht beeinflussen. Belege das:
ein Lauf mit alter Basis muss denselben `loss` liefern wie vorher.

## Teil 2 — Die Basisvariante mit Konstante

Eine neue Builder-Funktion neben `default_staged_polynomial_basis`, die dieselbe gestufte Struktur
hat und zusaetzlich den konstanten Term traegt.

**Der konstante Term gehoert in Stufe 1.** Begruendung: die Stufung ist nach Grad geordnet, und eine
Konstante hat Grad 0 — sie ist einfacher als der lineare Term und muss deshalb ab der ersten Stufe
verfuegbar sein. Diese Entscheidung ist bewusst getroffen und im Report festzuhalten; sie nicht
anders zu treffen ist Teil des Auftrags.

Die neue Basis muss ueber die bestehende Registrierung in `src/EvoODE.jl` erreichbar sein und in
`docs/architecture.md` auftauchen, wie es fuer Bases dort vorgesehen ist.

## Teil 3 — Der Probelauf, und nur der billige Teil davon

**Ausfuehren darfst du ausschliesslich Dimension 1.** Aus den Kampagnenlaufzeiten: die 72 exakten
dim-1-Zellen kosteten zusammen 0,6 Kernstunden, im Median 0,3 Minuten je Zelle. Das ist Minutenarbeit
und darf laufen.

**Dimension 2 und hoeher darfst du NICHT starten.** Die exakten dim-2-Zellen kosteten 114
Kernstunden, dim 3 ueber 2.600. Bereite den Lauf als startbares Skript vor und halte das Kommando im
Report fest — starten wird ihn der Nutzer.

Der dim-1-Probelauf vergleicht **alte gegen neue Basis** auf denselben Systemen, Seeds und
IC-Saetzen, alles andere unveraendert:

- die sechs bisher exakt darstellbaren dim-1-Systeme: 2, 3, 6, 8, 11, 12 — **Frage: steigt die
  Trefferquote ueber die heutigen 79 %?**
- die fuenf dim-1-Systeme, die allein an der Konstante scheitern: 1, 5, 9, 17, 23 — **Frage: werden
  sie mit Konstante gefunden?** Fuer diese fuenf ist die Strukturbewertung erst mit der neuen Basis
  ueberhaupt definiert; unter der alten Basis sind sie Surrogate. Weise das getrennt aus und behaupte
  keinen Vorher-Nachher-Vergleich, wo es kein Vorher gibt.

Seeds und IC-Saetze wie in der Kampagne: Seeds 7, 42, 123, beide IC-Saetze. Eine Bedingung genuegt;
nimm `pretuning=false` und begruende im Report, warum — nicht stillschweigend.

Ergebnisse in ein **eigenes Ausgabeverzeichnis** unter `outputs/` mit eigenem Namen. Sie werden
niemals mit Kampagnendaten in einer Datei zusammengefuehrt.

## Verboten

- keine Aenderung an `default_staged_polynomial_basis` oder an bestehenden Fingerprint-Bestandteilen
- kein Start von Laeufen jenseits Dimension 1
- keine Aenderung an `experiments/paper1_phaseB_v1/`, an der Analyse-Pipeline oder an den
  A5-bis-A9-Skripten
- keine Aenderung an der Suchlogik, am Stage-Cap oder am Optimizer — dieses WP aendert die **Basis**
  und die **Ausgabe**, sonst nichts
- keine Ergebnisse in `PAPER_1.md`, `CLAUDE.md` oder `DIARY.md`
- kein `git add -A`, keine Git-Operationen

## Akzeptanzkriterium

Ein Lauf mit der alten Basis liefert denselben `loss` wie vor der Aenderung und einen unveraenderten
`config_fingerprint`. Der Record traegt die Koeffizienten und die Basiskennung, und aus einem Record
allein laesst sich das Modell wieder aufbauen — zeige das an einem Beispiel. Der dim-1-Probelauf ist
durchgelaufen, seine Ergebnisse liegen unter `outputs/`. Das Kommando fuer den dim-2-Lauf steht im
Report, ungestartet.

## Report

`codex/REPORT_WP_N1.md`. Enthaelt: die Kommandos, den Nachweis der Bitgleichheit auf der alten Basis,
die Record-Form mit einem vollstaendigen Beispiel inklusive Rekonstruktion des Modells, die
Begruendung fuer Stufe 1 und fuer `pretuning=false`, die Ergebnistabelle des dim-1-Probelaufs mit den
beiden getrennten Fragen — und das startbereite, **nicht ausgefuehrte** Kommando fuer Dimension 2.

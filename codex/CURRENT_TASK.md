> **Claude-Status:** `waiting for codex` — WP-R1 übergeben. Melde dich über `codex/STATUS.md`,
> nicht in dieser Datei. Committe nichts.
> Der Dauerauftrag steht in `codex/CODEX_PROTOCOL.md`.

# WP-R1 — Was könnte die heutige Basis bestenfalls? Eine suchfreie Referenz
**Language: Julia**

## Warum

Nach der Kampagne soll entschieden werden, welche Termfamilien der Basis fehlen und welche davon
ihren Preis wert sind. Die geplante Auswahlregel lautet: Für jede fehlende Motivfamilie das mittlere
Surrogat-R² aus Phase B ansehen — bricht die Approximation ein, lohnt die Familie; bleibt R² hoch,
lohnt sie nicht.

**Diese Regel hat eine Verwechslungsgefahr, und ohne dieses Arbeitspaket ist sie nicht belastbar.**
Ein Surrogatsystem mit R² = 0,3 belegt nämlich *nicht*, dass ihm eine Termfamilie fehlt. Es kann
genauso gut sein, dass die Suche das beste Modell **innerhalb der heutigen Basis** nicht gefunden
hat. In den Kampagnen-Records sehen beide Fälle identisch aus.

Gebraucht wird deshalb eine Referenz: **Was wäre in der heutigen Basis überhaupt erreichbar
gewesen, ganz ohne Suche?** Erst der Abstand zwischen dieser Referenz und dem tatsächlich gefundenen
Modell trennt „die Modellklasse kann es nicht" von „die Suche hat es nicht gefunden".

Das ist zugleich die saubere Messung für eine Aussage, die im Bogen an mehreren Stellen gebraucht
wird (`docs/phd_thesis_arc.md` §3 und §5): Darstellbarkeit, Identifizierbarkeit und Auffindbarkeit
sind drei verschiedene Ebenen. Dieses Paket vermisst die erste.

## Idee

Für jedes System und jeden Anfangsbedingungs-Satz: alle Terme der Basis gleichzeitig aktivieren —
also keine Strukturauswahl, keine Stufen, kein Wachstum — und die Koeffizienten in einem Zug per
kleinster Quadrate auf dem **Ableitungsproblem** bestimmen. Das Ergebnis ist die
Kleinste-Quadrate-Projektion der wahren Dynamik auf die Basis: die beste Anpassung, die diese
Modellklasse in diesem Sinne hergibt.

Wichtig für die Einordnung im Report: Das ist eine **wohldefinierte, reproduzierbare Referenz**, kein
bewiesenes Optimum über alle möglichen Anpassungen. Formuliere es entsprechend vorsichtig — „beste
Anpassung durch unregularisierte kleinste Quadrate auf dem Ableitungsproblem über die volle Basis",
nicht „Obergrenze der Modellklasse".

## Auftrag

Ein neues Studienskript unter `studies/representation/`, eigener Ausgabeordner unter `outputs/`.

Für jede Kombination aus den **63 Systemen** und **beiden IC-Sätzen**:

1. Trajektorie erzeugen — **exakt wie in Phase B**: 512 Punkte über `t ∈ [0,10]`, `Tsit5`,
   `abstol = reltol = 1e-9`. Verwende die vorhandenen Hilfsfunktionen aus dem Phase-B-Pfad, schreibe
   nichts neu. Weichen die Trajektorien ab, ist die Referenz nicht mit den Kampagnen-Records
   vergleichbar, und das Paket ist wertlos.
2. Ableitungen schätzen — mit **derselben** Schätzung, die das Pretuning verwendet. Nicht mit einer
   eigenen, besseren.
3. Je Gleichung die Koeffizienten über die **volle** Basis per kleinster Quadrate bestimmen.
4. Zwei Güten festhalten, sie beantworten verschiedene Fragen:
   - **im Ableitungsraum**: wie gut trifft die Projektion die geschätzten Ableitungen?
   - **im Trajektorienraum**: das gefittete Modell integrieren und R² sowie MSE gegen die
     Referenztrajektorie rechnen — dieselbe R²-Definition wie im Kampagnenpfad, nicht eine eigene.
5. Die Integration des gefitteten Modells kann divergieren. Das ist ein zulässiges Ergebnis und wird
   als solches festgehalten, nicht abgefangen und beschönigt. Die Ableitungsgüte bleibt in diesem
   Fall gültig und wird trotzdem berichtet.

Ergebnis ist **eine CSV**, eine Zeile je (System, IC-Satz), mit mindestens: Systemkennung,
Dimension, IC-Satz, Darstellbarkeit (exakt oder Surrogat), Zahl der Basisterme, Güte im
Ableitungsraum je Gleichung und gemittelt, Güte im Trajektorienraum, ob die Integration stabil war.
Ergänze, was für die spätere Auswertung offensichtlich nützlich ist.

## Verboten

- **Keine Änderung an `src/`, an `phase_b_config.jl`, an der Basis oder an irgendetwas, das in einen
  Fingerprint eingeht.** Dieses Paket liest nur. Bewegt sich ein Fingerprint, hast du zu viel
  angefasst — dann `blocked` melden.
- **Nichts, was die laufende Kampagne stört.** Keine Cluster-Jobs, kein Zugriff auf `S:`, keine
  Schreibvorgänge in Kampagnenverzeichnisse.
- Keine eigene Ableitungsschätzung, keine eigene R²-Definition, keine eigene Trajektorienerzeugung.
  Alles drei existiert; doppelte Implementierungen derselben Größe laufen auseinander.
- Keine Interpretation, welche Termfamilie sich lohnt. Das Paket erzeugt die Referenz, es wertet sie
  nicht aus.
- Keine Git-Operationen.

## Abnahme

Das Ganze sollte in Minuten durchlaufen; 126 Zellen ohne Suche sind billig.

1. **Vollständigkeit:** 126 Zeilen, keine fehlt, keine doppelt.
2. **Plausibilität an den exakten Systemen:** Bei den 20 exakt darstellbaren Systemen enthält die
   Basis die Wahrheit. Dort muss die Referenz **sehr gut** sein — nenne die Werte und benenne
   ausdrücklich jedes exakte System, bei dem sie es *nicht* ist. Solche Fälle sind der interessante
   Teil des Ergebnisses, denn sie zeigen die Grenze der Ableitungsschätzung, nicht die der Basis.
3. **Kontrast:** Nenne die Verteilung der Trajektoriengüte getrennt für exakte und Surrogatsysteme.
4. **Stabilität:** Wie viele der 126 gefitteten Modelle divergieren beim Integrieren?
5. **Determinismus:** Zweimal laufen lassen, identisches Ergebnis.

## Report

`docs/WP-R1.md`. Er nennt die Zahlen aus den fünf Abnahmepunkten, die genaue Formulierung dessen,
was die Referenz ist und was sie nicht ist, und die exakten Systeme mit auffällig schlechter
Referenz. Keine Empfehlung zu Termfamilien.

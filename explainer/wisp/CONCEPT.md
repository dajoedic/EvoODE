# WISP-Explorable — Konzept

Stand 2026-11-07. Verbindlich für den Bau bis Di 10.11. Änderungen nur mit dem Nutzer.

## 1. Für wen, und was danach verstanden ist

**Leser:** jemand, der nicht blöd ist, aber vom Thema keine Ahnung hat. Kein Mathematikstudium vorausgesetzt;
Schulmathematik (Steigung, Funktion) reicht.

Nach dem Lesen kann der Leser:

1. erklären, was ein dynamisches System ist und warum eine Differentialgleichung es so kompakt beschreibt;
2. sagen, welche Aufgabe WISP löst: aus verrauschten Messungen die Gleichung selbst finden;
3. jeden WISP-Schritt in einem Satz nacherzählen und sagen, **warum** er funktioniert;
4. einschätzen, wie gut WISP gegen die etablierten Verfahren abschneidet — und wo nicht.

## 2. Das durchgehende Beispiel

**Lotka–Volterra, Hasen und Füchse** (ODEBench-System 27): `dH/dt = 1,84·H − 1,45·H·F`, `dF/dt = −3,0·F + 1,62·H·F`.
2D, anschaulich, jeder Term ist ein Satz („Hasen vermehren sich“, „Füchse fressen Hasen“).

- **Farben:** Hase und Fuchs haben je eine feste Farbe, von der Wiese bis zum letzten Diagramm.
- **Daten:** die gespeicherte Zelle `sys0027_ic1_s0.03_r0_n1` (σ = 3 %, 512 Punkte, Pfad mit 4 Schritten, 4 Kandidaten).
  Der Pfad hängt nur von den Daten ab und gilt unverändert. **Die 4 Kandidaten-Fits werden lokal in der finalen
  Konfiguration C1000 neu gerechnet** (Startwert mitgeschätzt, Grenze 1000) — die gespeicherten Fits stammen aus Q7
  (Startwert = erster Messpunkt, Grenze 10) und zeigen nicht die finale Methode. Nach W-4 wird gegen die Q9-Zelle
  getauscht.

## 3. Die Geschichte

Scrollytelling wie Version 26: Text links, eine stehende Grafik rechts, die sich mit dem Scrollen verwandelt;
gleiche Farben, gleiche Übergänge. Pro Seite **eine** Aussage, **eine** Grafik, höchstens eine Interaktion,
≤ ~100 Wörter.

### Teil A — Warum das spannend ist (4 Seiten)

| # | Aussage | Grafik / Interaktion |
|---|---|---|
| A1 | Hasen und Füchse auf einer Wiese: die Zahlen schwingen, immer wieder. Warum? | Wiese mit Tieren (Idee aus der Codex-Fassung, in unserem Stil), daneben die zwei Zählkurven, die mitwachsen |
| A2 | Ein dynamisches System: der Zustand **jetzt** bestimmt die Änderung **jetzt**. Dasselbe Prinzip steckt in Pendel, Epidemie, Klima, Chemie | Pfeilfeld im H-F-Raum, der Zustand fährt den Pfeilen nach; kleiner Streifen mit anderen Systemen |
| A3 | Die Differentialgleichung: vier Zahlen, zwei Zeilen — und daraus folgt jede Zukunft. Jeder Term ist ein Satz | Gleichung, Hover auf einen Term zeigt seinen Beitrag; Schieberegler für eine Rate verändert die Zyklen |
| A4 | Die umgekehrte Frage: wir sehen nur verrauschte Zählungen. Welche Gleichung steckt dahinter? Schwer, weil es Millionen möglicher Gleichungen gibt und Rauschen Ableitungen zerstört | Verrauschte Punkte; Zähler „12 Bausteine je Gleichung → 16,7 Mio. Kombinationen“; naive Ableitung aus den Punkten zackt |

### Teil B — WISP in Aktion (≈ 9 Seiten, alles am selben Lauf)

| # | Schritt | Warum er funktioniert | Grafik / Interaktion |
|---|---|---|---|
| B1 | Bausteine: 1, H, F, H², H·F, … | Die Wahrheit muss darin liegen — bei LV tut sie das | Bausteinleiste, die durch Teil B stehen bleibt |
| B2 | Schwache Form: statt abzuleiten, über kleine Fenster mitteln | Mitteln glättet Rauschen; die Ableitung wandert auf die glatte Testfunktion | Fenster gleitet über die Daten; Vergleich zackige Ableitung vs. ruhige Fensterwerte |
| B3 | Hinzufügen: der Baustein, der den Rest am besten erklärt, kommt dazu | Im Fensterraum ist alles linear — ein Schritt ist eine Regression, kein Suchen | Balken der 24 Gewinne, Schritt 1–4 durchklickbar; Gleichung wächst |
| B4 | Aufräumen: nach jedem Schritt prüfen, ob ein Baustein überflüssig wurde | Ein früher Fehlgriff kann wieder raus (hier bleibt alles drin — gesagt, nicht versteckt) | Prüfbalken je Term gegen die Schwelle |
| B5 | Aufhören: wenn der Rest nur noch Rauschen ist | Das Rauschen wird aus den Daten geschätzt; Stopp nur bei Beleg | Restfehler je Schritt gegen die Rauschgrenze |
| B6 | Fitten: jeder der 4 Kandidaten wird simuliert und an die Kurve angepasst, Startwert inklusive | Erst hier wird die ganze Kurve verglichen, nicht nur Fenster | 4 Kandidatenkurven gegen die Daten |
| B7 | Wählen: BIC — Genauigkeit gegen Anzahl Terme | Bestraft jeden zusätzlichen Term ehrlich | BIC-Balken, Gewinner leuchtet |
| B8 | Gegenprobe: neuer Startpunkt, nie gesehen | Wer den Mechanismus hat, sagt auch Unbekanntes voraus | Vorhersage gegen Wahrheit vom zweiten Startwert |
| B9 | Warum es so gut klappt — drei Sätze | Robust gegen Rauschen · billig, weil linear · ehrlich entschieden in der echten Kurve | Zusammenfassung des Pfads auf einer Grafik |

### Teil C — Wie oft klappt das? (2–3 Seiten)

| # | Aussage | Grafik / Interaktion |
|---|---|---|
| C1 | Über alle Systeme: WISP gegen SINDy, Weak-SINDy, E-SINDy, WSINDy — **immer beide Maße**: Struktur getroffen und R² > 0,9 | Raten nach Dimension und Rauschen |
| C2 | Explorer: jedes System, jede Bedingung | Auswahl → Kurven und gefundene Gleichung |
| C3 | Grenzen: wo es scheitert (Dim 3/4, Lorenz) und warum | ein Fehlerbeispiel, kurz |

Zahlen bis W-4: Q8 (finale Konfiguration C1000, Dim 1/2), als **vorläufig** gekennzeichnet; nach W-4 Q9.

## 4. Was nicht hineinkommt

EvoGrow und seine Geschichte · Protokollnamen (Q5–Q9), Gates, Ablationen · Formeln über Schulniveau hinaus
(Formel nur als Ausklapper) · eine zweite Beispielsystem-Kette · stochastische Tiersimulation als Datenquelle
(die Wiese ist Illustration der ODE und sagt das).

## 5. Wann es fertig ist

- Jede Seite: eine Aussage, eine Grafik, Text ≤ ~100 Wörter, Deutsch und Englisch vollständig.
- Jede Zahl im Text stammt aus einer Datendatei (`data-claim`), keine handgetippten Ergebnisse.
- Läuft auf 1280×720 und 390 px Breite ohne horizontales Scrollen, hell und dunkel.
- Claude hat jede Seite im Browser per Screenshot geprüft.
- Gesamtgröße deutlich unter Version 26 (13,7 MB).
- Probeleser-Test: der Nutzer kann die vier Ziele aus §1 an der Seite abhaken.

## 6. Bau und Zeitplan

Claude baut selbst (Browserprüfung möglich), auf der Technik von Version 26; die Codex-LV-Fassung (`src/lv/`)
liefert nur die Wiesen-Idee.

| Wann | Was |
|---|---|
| Sa 07.11. abends | Konzept abgenommen; C1000-Neufit der 4 Kandidaten (lokal, Minuten) |
| So 08.11. | Teil A inkl. Wiese |
| Mo 09.11. | Teil B; **abends Entscheidung:** steht B, geht's weiter — sonst Dienstag mit Version 26 |
| Di 10.11. vormittags | Teil C, Durchsicht, Veröffentlichung |

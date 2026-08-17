# WP-C1 — Stage-Cap-Audit über alle exakten Systeme und Korrektur des Look-ahead-Horizonts
**Language: Julia**

## Warum

Der Look-ahead-Stage-Cap ist der Beitrag von Paper 1. Am 2026-08-14 wurde festgestellt, dass er auf
2 von 7 geprüften exakten Systemen die wahre Struktur aus dem Suchraum ausschließt:

| System | wahrer Support Gl. 2 | benötigte Stufe | Cap | Ergebnis |
|---|---|---|---|---|
| 28 | `sin(u1)` | 5 | 1 | abgeschnitten |
| 32 | `u1`, `u2`, `u1^3` | 4 | 1 | abgeschnitten |
| 26, 27, 29, 31, 54 | — | — | — | in Ordnung |

Vermuteter Mechanismus: `lookahead_horizon = 2` in
`src/structure/stage_cap.jl` lässt `_cap_split_decision` von Stufe 1 aus nur die Stufen 2 und 3
prüfen. Die gestaffelte Polynombasis staffelt nach **Grad**, nicht nach **Parität** — Stufe 2
(`u^2`) ist gerade, Stufe 3 (`u1*u2`) gemischt. Eine ungerade Nichtlinearität (`u1^3` auf Stufe 4,
`sin` auf Stufe 5) ist durch die Stufen 2 und 3 nicht approximierbar, der Vorausblick sieht keinen
Gewinn und schließt „Stufe 1 genügt".

Zwei Dinge sind zu klären, **bevor** entschieden wird, ob der Cap in dieser Form in die Kampagne
geht: die tatsächliche Rate über alle exakten Systeme (2 von 7 ist eine Stichprobe), und ob ein
größerer Horizont die beiden Fälle löst, ohne die korrekten Caps zu verschieben.

## Umfang

Drei Teile. **Teil 3 nur ausführen, wenn Teil 2 das Kriterium erfüllt.**

### Teil 1 — Audit-Skript

Neues Skript unter `studies/lookahead/`, Ausgabe nach `outputs/studies/lookahead/<script_slug>/`.

Für **alle 20 exakten Phase-B-Systeme** und **beide IC-Sets**:

- Trajektorie nach Phase-B-Protokoll selbst integrieren: 512 Punkte über `t ∈ [0,10]`, `Tsit5`,
  `abstol = reltol = 1e-9`. Nicht die im Datensatz mitgelieferten Trajektorien verwenden.
- **Benötigte Stufe je Gleichung** aus `phase_b_support.json` ableiten: die `support_idxs` sind
  Indizes in die Basis, `default_staged_polynomial_basis(dim).term_groups` ordnet jeden Index einer
  Stufe zu, die benötigte Stufe ist die höchste Stufe mit einem Supportterm. Das ist exakt die
  Ableitung, die WP-M1 für `expected_stage` eingeführt hat — **wiederverwenden, nicht neu
  implementieren**, damit beide Stellen nicht auseinanderlaufen können.
- **Cap je Gleichung** über die bestehende öffentliche Funktion `estimate_stage_caps(traj, basis;
  policy)` berechnen. Die Cap-Logik selbst wird in Teil 1 **nicht** angefasst.
- Das Ganze für `lookahead_horizon ∈ {2, 3, 4, 5}`, sonst identische Policy-Felder wie
  `LOOKAHEAD_CAP_POLICY` in `studies/regression/run_regression.jl`.

Je Zeile (System, IC-Set, Horizont, Gleichung) festhalten: benötigte Stufe, Cap, und eine
Klassifikation in genau eine von drei Kategorien:

- **truncated** — Cap ist gesetzt und liegt *unter* der benötigten Stufe (der Defektfall)
- **ok** — Cap ist gesetzt und liegt auf oder über der benötigten Stufe
- **uncapped** — Cap ist `nothing` (kein Cap, per Definition kein Abschneiden)

Ausgabe: eine CSV mit allen Zeilen plus ein kurzer Markdown-Report unter `docs/` mit der
Kreuztabelle Horizont × Kategorie und einer namentlichen Liste aller `truncated`-Fälle.

**Kosten:** Der Vorausblick rechnet nur Ableitungsregressionen, keine Parameter-Fits und keine
Suche. Das Skript darf und soll vollständig ausgeführt werden; es ist Minuten-, nicht Stundenarbeit.
Falls die Laufzeit wider Erwarten über 15 Minuten geht: abbrechen und berichten statt durchlaufen
lassen.

### Teil 2 — Entscheidungskriterium

Aus der Tabelle beantworten, ausdrücklich mit Zahlen belegt:

1. Wie viele der exakten Systeme sind bei `horizon = 2` **truncated**? Das ist die gesuchte Rate.
2. Gibt es einen Horizont, der die Systeme 28 und 32 nach **ok** bewegt und dabei die Caps der
   Systeme 26, 27, 29, 31 und 54 **unverändert** lässt? „Unverändert" heißt: identischer Cap-Wert
   je Gleichung, nicht nur identische Kategorie.
3. Bewegt ein größerer Horizont irgendeinen Cap von einem endlichen Wert nach `nothing` oder
   umgekehrt? Solche Übergänge einzeln aufführen — sie ändern das Verhalten auch dort, wo die
   Kategorie gleich bleibt.
4. Falls kein Horizont beides leistet: das ausdrücklich als Ergebnis berichten und **Teil 3 nicht
   ausführen**. Ein Fehlschlag hier ist ein gültiges und wichtiges Resultat; er bedeutet, dass der
   Defekt nicht am Parameter hängt.

### Teil 3 — Nur bei erfülltem Kriterium: Default ändern

Den gefundenen Horizont als neuen Default setzen, an **allen** Stellen konsistent:

- das Default-Feld in `LookAheadStageCapPolicy` (`src/structure/stage_cap.jl`)
- `LOOKAHEAD_CAP_POLICY` in `studies/regression/run_regression.jl`
- `LOOKAHEAD_CAP_POLICY_REGRESSION` in `studies/lookahead/measure_dataset_grid_caps.jl`

Danach `config_fingerprint()` und `phase_b_fingerprint()` neu ausgeben und **beide alten und beide
neuen Werte** im Report festhalten. Der Parameter geht über `phase_b_config.jl` in den Fingerprint
ein; der Sprung ist beabsichtigt und muss dokumentiert sein.

## Verboten

- **Keine Kampagne, keine Discovery-Läufe, keine Cluster-Jobs.** Weder starten noch Manifeste dafür
  erzeugen. Das Audit rechnet ausschließlich Ableitungsregressionen.
- **Die Cap-Logik selbst nicht umbauen.** Zur Debatte steht ein Parameterwert, nicht der
  Algorithmus. `_cap_split_decision`, `_cap_rule_counts_gain` und `_cap_aggregate_split_decisions`
  bleiben unverändert.
- **Keine Ground-Truth in die Cap-Berechnung.** `estimate_stage_caps` darf laut eigenem Docstring
  nur Trajektorie, Basis und Schwellenwerte sehen. Die wahre Struktur wird ausschließlich
  *außerhalb* zur Bewertung des Ergebnisses verwendet, niemals als Eingabe.
- **Kein `git add -A`.** Nur die tatsächlich zu dieser Aufgabe gehörenden Dateien stagen.

## Abnahme

- CSV und Report liegen vor, decken 20 exakte Systeme × 2 IC-Sets × 4 Horizonte ab.
- Die Rate bei `horizon = 2` ist beziffert.
- Die Frage aus Teil 2.2 ist mit Ja oder Nein und mit Zahlen beantwortet.
- Bei Ja: Default an allen drei Stellen geändert, alte und neue Fingerprints im Report.
- Bei Nein: keine Codeänderung, und der Report benennt, woran es scheitert.

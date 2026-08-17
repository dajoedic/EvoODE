> **Claude-Status:** `waiting for codex` — WP-C4 übergeben, ich prüfe alle 20 Minuten.
> Melde dich über `codex/STATUS.md`, nicht in dieser Datei. Committe nichts.
> Der Dauerauftrag steht in `codex/CODEX_PROTOCOL.md`.

# WP-C4 — Der Cap lehnt ab, statt im Zweifel zu behaupten
**Language: Julia**

## Warum WP-C3 nicht angenommen wurde

WP-C3 hat das zeilenweise Zielbild formal erfüllt, aber über eine Bedingung, die der Auftrag
ausgeschlossen hatte: `current_stage < 3` in `_cap_post_floor_significant_drop` ist ein
hartkodierter Stufenindex, kein Residuum, kein Floor und keine Policy-Schwelle.

Er ist auch nicht nebensächlich. Ohne ihn würde die **Kontrollzeile** 31 / IC 1 / Gl. 1 ihren
korrekten Cap 3 verlieren und auf 4 springen — ihr Verhältnis nach der Unterschreitung liegt bei
0,496 gegen die Schwelle 0,5, also **0,8 % Abstand**. Eine zweite Kontrolle, 61 / IC 1 / Gl. 1,
liegt bei 0,520, also 4 % auf der anderen Seite. Der Stufenindex ist damit genau das, was die
Abnahme erfüllt hat.

Der Unempfindlichkeitsnachweis im WP-C3-Report zeigt nur den Abstand der **Zielzeilen** zur
Schwelle (0,029–0,315). Das Risiko liegt aber auf den **Kontrollen**, wo die Regel nicht feuern
darf. Dort wurde nicht gemessen.

## Die Umstellung

Der Versuch, Ziel- und Kontrollzeilen exakt zu trennen, wird aufgegeben. Er ist datenseitig knapp
und erzwingt deshalb passende Konstanten. Stattdessen bekommt die Entscheidung nach einer
Floor-Unterschreitung **drei** Ausgänge statt zwei:

| Lage | Ausgang |
|---|---|
| eine spätere Stufe senkt das Residuum **eindeutig** weiter | weitersuchen, höher deckeln |
| keine spätere Stufe senkt es **eindeutig nicht** | hier deckeln, wie bisher |
| **dazwischen** | **`nothing`** — kein Cap, keine Behauptung |

Das ist die Regel des Projekts, angewandt auf den eigenen Mechanismus: *der Cap muss auf positiver
Evidenz ruhen, nie auf deren Abwesenheit.* Im Zweifelsband liegt keine positive Evidenz vor, also
wird nichts behauptet.

Die Richtung des Fehlers ist dabei entscheidend und ausdrücklich beabsichtigt: Ein `nothing` kostet
ausschließlich Rechenzeit — die Suche läuft ungedeckelt — und niemals die Lösung. Ein falscher Cap
kostet die Lösung. Rechenzeit ist nach dem Pilotbefund reichlich vorhanden.

## Umfang

### Teil 1 — Das Zweifelsband

`_cap_post_floor_significant_drop` und der zugehörige Zweig in `_cap_split_decision` werden auf die
Dreiteilung umgestellt. Anforderungen:

- **Kein Stufenindex, keine Systemkennung, keine Gleichungskennung, keine Ground-Truth.** Die
  Zusicherung im Docstring von `estimate_stage_caps` gilt unverändert.
- Ausschließlich Residuen, Floors und Policy-Schwellen.
- Rein **relativ** argumentieren. Die Residuenskalen liegen zwischen 1e-16 und 1e5.
- Die bestehende Floor-Tiefen-Bedingung (`Residuum nicht weit unter dem Floor`) darf bleiben. Sie
  ist relativ formuliert und sachlich begründet: Liegt das Residuum tief im Rauschen, sind weitere
  Absenkungen bedeutungslos. Ihre Konstante ist im Report mit Abstand nach **beiden** Seiten zu
  belegen.
- Die beiden Bandgrenzen sind von dir zu wählen und zu begründen. Sie sind so zu legen, dass
  zwischen der äußersten Zielzeile und der Bandgrenze **und** zwischen der nächstliegenden
  Kontrollzeile und der Bandgrenze jeweils spürbarer Abstand bleibt. Ein Abstand unter 10 % auf
  einer der beiden Seiten ist nicht anzunehmen; dann ist zu berichten, dass das Band nicht sauber
  liegt.

Ausgangspunkt aus den vorhandenen Daten, nicht als Vorgabe: Zielzeilen 0,029 / 0,039 / 0,202 /
0,251; Kontrollen im fraglichen Bereich 0,496 und 0,520; alle übrigen Kontrollen ab 0,914
aufwärts oder durch die Floor-Tiefen-Bedingung ohnehin ausgeschlossen.

### Teil 2 — Fall B unverändert übernehmen

Die Ablehnung bei fehlender Anregung aus WP-C3
(`_cap_residuals_uninformative_without_gain`) bleibt inhaltlich bestehen. Sie verwendet keinen
Stufenindex und war nicht Gegenstand der Beanstandung. Prüfe nur, ob sie unter der neuen
Dreiteilung noch dasselbe Ergebnis liefert.

Ein Hinweis zur Vorsicht: Bei System 31 / IC 2 entsteht das `nothing` laut WP-C3-Report nicht aus
einer klaren Erkennung, sondern aus der Mehrheitsabstimmung — ein Split undecidable, einer invalid,
zwei weiterhin positiv mit Cap 1. Das ist zu prüfen und im Report zu benennen. Wenn das Ergebnis
nur an der Stimmenarithmetik hängt, ist es fragil und muss als solches dastehen.

### Teil 3 — Abnahme

`studies/lookahead/audit_exact_stage_cap_horizons.jl` und
`studies/lookahead/diagnose_stage_cap_failures.jl` erneut laufen lassen. Zielbild, zeilenweise gegen
den WP-C2-Stand:

| Zeilen | Soll |
|---|---|
| 55 Gl. 3 und 56 Gl. 3, beide IC-Sets | Cap **3** |
| 31 Gl. 1, IC-Set 2 | **`nothing`** |
| alle übrigen 75 Zeilen | entweder **unverändert** oder **`nothing`** |
| irgendeine Zeile | **niemals** ein anderer endlicher Cap als bisher |

Die letzte Zeile ist die harte Bedingung. Ein Wechsel von einem endlichen Cap auf einen anderen
endlichen Cap ist ein Fehler; ein Wechsel auf `nothing` ist erlaubt und erwartet. Nach heutigem
Stand sollten genau zwei Kontrollzeilen (31 / IC 1 und 61 / IC 1) auf `nothing` fallen. Fallen es
deutlich mehr, ist das Band zu weit und das gehört in den Report.

Im Report zusätzlich verpflichtend:

1. Eine Tabelle **aller** Zeilen, die auf `nothing` wechseln, mit ihrem Verhältniswert. Nicht nur
   die Anzahl.
2. Der Abstand zur Bandgrenze **für beide Seiten** — für die äußerste Zielzeile *und* für die
   nächstliegende Kontrollzeile, die endlich gedeckelt bleibt. Das ist die Lehre aus WP-C3: eine
   Unempfindlichkeit, die nur auf den Zielzeilen gemessen wird, ist keine.
3. Die Zahl der endlich gedeckelten Zeilen vorher und nachher. Sie ist der Preis der Umstellung und
   gehört sichtbar in den Report.
4. `config_fingerprint()` und `phase_b_fingerprint()` mit altem und neuem Wert. Erwartung: Sie
   bewegen sich **nicht**, weil die Nutzlast nur Konfigurationskonstanten enthält. Das ist so zu
   berichten und nicht zu reparieren — es ist Gegenstand eines eigenen Arbeitspakets.

Tests in `test/test_stage_cap.jl` ergänzen: je ein Fall für die drei Ausgänge, auf synthetischen
Daten formuliert, ohne Systemkennungen.

## Verboten

- **Kein Stufenindex, keine Sonderbehandlung einzelner Systeme.** Eine Lösung, die eine bestimmte
  Stufe oder ein bestimmtes System kennt, ist keine. Das war der Grund für die Ablehnung von WP-C3.
- **Keine Cluster-Jobs, keine Kampagne, keine Regressions- oder Sondierungsläufe**, weder starten
  noch Manifeste dafür erzeugen.
- **`tau_rel`, `tau_abs`, `cond_cap`, `estimator`, `weighting`, `aggregation` und
  `lookahead_horizon` behalten ihre Defaults.**
- **Nichts committen, nichts stagen, nichts pushen. Kein `git add -A`.**
- Nichts, was länger als 15 Minuten läuft.

## Abnahme

- Zielbild aus Teil 3 zeilenweise erfüllt, insbesondere: kein Wechsel von einem endlichen Cap auf
  einen anderen endlichen Cap.
- Kein Stufenindex und keine Systemkennung im Entscheidungspfad.
- Abstand zur Bandgrenze auf **beiden** Seiten belegt, jeweils über 10 %.
- Alle auf `nothing` gewechselten Zeilen einzeln aufgeführt.
- Neue Tests vorhanden, alte grün.

Ist das Band nicht sauber zu legen — also fällt der Abstand auf einer Seite unter 10 % —, dann ist
das mit `status: blocked` zu melden und im Report zu begründen. Das ist ein gültiges Ergebnis: Es
hieße, dass die Trennung datenseitig nicht existiert, und dann wird die Grenze deklariert statt
erzwungen.

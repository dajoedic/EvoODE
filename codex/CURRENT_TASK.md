# WP-N24 — ODEFormer: den 1-s-Wall-Clock-Timeout sichtbar und steuerbar machen, Wiederholbarkeit messen
**Language: Python**

## Ausführung

Lokal umsetzbar und testbar, **nur ein Rauchtest** (siehe Abnahme 5). Der Wiederholbarkeitslauf
selbst ist **nicht** Teil dieses Pakets — den startet Claude bzw. der Nutzer mit dem Befehl aus dem
Report.

## Der Befund

Das ODEFormer-Raster wurde nach WP-N23 komplett neu gerechnet (`reference_wp_n23/`,
`candidate_wp_n23/` unter `analysis/data/paper1_phaseC_v1/odeformer_baseline/`), gleicher
Git-Hash, gleiche Umgebung, gleiche Konfiguration, Seed 2023, ein frisch gebauter Adapter pro Zelle
(Fork-Pfad in `run_odeformer_grid.py`). Die Ergebnisse sind **nicht bitgleich** mit dem ersten Lauf
(`reference/`, `candidate/`): In 18 von 504 Referenz- und 8 von 504 Kandidatenzellen weicht ein
R²-Wert ab, in 10 davon sogar das Rohmodell (`odeformer_model_raw`), und in weiteren kippt bei
**identischem Modell** der Ausgang zwischen `finite` und `wrong_shape`.

Ursache nach Code-Lektüre im Image `evoode/odeformer-candidate:wp-n21` (noch nicht empirisch
bestätigt, das ist Teil dieses Pakets):

- `odeformer/envs/generators.py:823`: `_integrate_ode` ist mit `@timeout(1)` dekoriert, einem
  **Wall-Clock-Timeout von 1 s** per `SIGALRM` (`odeformer/utils.py:147`).
- `odeformer/envs/generators.py:919-924`: `integrate_ode` fängt `MyTimeoutError` und gibt eine
  **Liste aus NaN der Länge `len(times)`** zurück, also 1-D statt `(n, d)`. Genau das klassifiziert
  unser Harness als `wrong_shape`. Die Klasse `wrong_shape` ist also sehr wahrscheinlich
  vollständig „ODEFormer-Timeout" und kein echtes Formproblem.
- `odeformer/model/sklearn_wrapper.py:173/205`: `sort_candidates` integriert jeden Beam-Kandidaten
  für die Metrik `snmse`. Ein Timeout in der Rangfolge ändert, **welches Modell gewählt wird**.
  Das erklärt die abweichenden Rohmodelle.

Damit hängen die Ergebnisse von der Rechnerlast ab (vier parallele Docker-Shards). Das verstößt
gegen die Reproduzierbarkeit (`CLAUDE.md`, Designprinzip 2; Designprinzip 7 sinngemäß: die
Wall-Clock darf nicht ins Ergebnis eingehen).

## Was zu tun ist

1. **Timeout steuerbar machen, ohne ODEFormer zu patchen.** Neuer optionaler Konfigurationsschlüssel
   für die ODEFormer-Konfigurationen: die Integrations-Zeitgrenze in Sekunden. Fehlt er oder ist er
   `null`, bleibt ODEFormers ausgelieferte 1 s **exakt unverändert** (bestehende Records bleiben
   vergleichbar). Ist ein Wert gesetzt, ersetzt der Adapter zur Laufzeit im Modul
   `odeformer.envs.generators` die dekorierte `_integrate_ode` durch dieselbe undekorierte Funktion
   (erreichbar über das von `functools.wraps` gesetzte `__wrapped__`), neu dekoriert mit ODEFormers
   eigenem `timeout` und dem konfigurierten Wert. Prüfen und im Report belegen, dass sowohl der
   Aufruf aus `sort_candidates` als auch `integrate_prediction` über diesen Modulnamen laufen, also
   beide Pfade erfasst sind. Wenn nicht, den tatsächlichen Pfad nennen und ebenfalls abdecken.
2. **Timeouts zählen.** Pro Zelle getrennt zählen, wie oft der Timeout ausgelöst hat: (a) während
   der Kandidaten-Rangfolge in `fit`, (b) bei den Harness-Integrationen (Rekonstruktion und
   Generalisierung, jeweils vor und nach der Konstantenoptimierung), (c) innerhalb der
   Konstantenoptimierung, falls sie integriert. Dazu die wirksame Zeitgrenze als Feld im Record.
   Das Zählen darf das Ergebnis nicht verändern.
3. **Ausgang korrekt benennen.** Die Wertemenge von `*_prediction_outcome` bekommt einen Wert für
   ODEFormers Timeout-Sentinel (eindimensional, Länge der Zeitachse, vollständig NaN), getrennt von
   einem echten `wrong_shape`. R²-Werte und die 0.0-Konvention bleiben unverändert.
   `summarize_odeformer_grid.py` weist den neuen Wert aus. Alte Records behandelt es wie bisher.
4. **Wiederholbarkeitsskript** `baselines/run_odeformer_repeatability.py`:
   - Eingabe ist eine Zellenliste. Das Skript leitet sie selbst ab: jede Zelle (System, Fit-IC,
     Ziel-IC, Konfiguration, Umgebung), in der `reconstruction_r2_variance_weighted`,
     `generalization_r2_variance_weighted` oder `odeformer_model_raw` zwischen `reference/` und
     `reference_wp_n23/` bzw. `candidate/` und `candidate_wp_n23/` abweicht. Erwartet sind
     **18 + 8 = 26 Zellen**; weicht die Zahl ab, bricht das Skript ab und nennt die Differenz. Dazu
     **8 Kontrollzellen**, in beiden Läufen bitgleich, deterministisch gewählt (fester Seed, über
     Dimensionen und Konfigurationen gestreut), einmal gewählt und als Datei neben die Ausgabe
     geschrieben.
   - Modi: `faithful` (Zeitgrenze ungesetzt, also 1 s) und `lifted` (Zeitgrenze **10 s**), jeweils
     mit wählbarer Anzahl Wiederholungen und Shards. Jede Wiederholung baut den Adapter frisch, wie
     der Grid-Runner.
   - **Laufzeit per Konstruktion begrenzt:** harte Zeitgrenze pro Zelle aus dem bestehenden
     Fork-Pfad (900 s), plus eine globale Obergrenze in Stunden als Argument. Wird sie erreicht, hört
     das Skript sauber auf und markiert nicht gelaufene Zellen als nicht gelaufen, nicht als Fehler.
   - Ausgabe unter `outputs/odeformer_repeatability/<modus>_<shards>/`: ein Record pro Zelle und
     Wiederholung (Rohmodell, kanonisches Modell, alle R²-Werte, Ausgänge, Timeout-Zähler) sowie
     eine Zusammenfassung pro Zelle: Sind alle Wiederholungen bitgleich (Rohmodell und R²)? Wie
     viele Timeouts gab es, min/max über die Wiederholungen? Gab es R²>0.9-Kippungen?
   - Ein Auswertungsschritt vergleicht die Modi und beantwortet: (i) Sind unter `lifted` alle
     Wiederholungen bitgleich, und hat dort **kein** Timeout ausgelöst? (ii) Streuen die Ergebnisse
     unter `faithful`, und fällt die Streuung mit streuenden Timeout-Zählern zusammen? (iii) Hängt
     die Timeout-Zahl unter `faithful` von der Shard-Zahl ab (1 gegen 4)?
5. **Kein Urteil über den kanonischen Modus.** Welcher Modus für Claim D gilt, entscheidet Claude
   mit dem Nutzer nach dem Lauf. Keine Default-Änderung an den Rasterkonfigurationen.

## Verboten

- Keine Git-Operationen.
- ODEFormer-Quellen im Image nicht verändern. Nur Laufzeit-Ersetzung im Adapter, nur wenn der
  Schlüssel gesetzt ist.
- Nichts unter `analysis/data/` verändern (nur lesen).
- Keine Änderung an R²-Werten, Schwellen, Aggregationen oder den bestehenden Rasterkonfigurationen.
- Den Wiederholbarkeitslauf nicht vollständig ausführen. Nichts starten, was länger als 15 Minuten
  läuft.

## Abnahme

1. Ohne den neuen Schlüssel sind Records bis auf die neuen Felder unverändert. Test: gleiche Zelle,
   alter und neuer Code, gleiche R²-Werte und Modelle. Muss auf einer Zelle ohne Timeout laufen,
   sonst ist der Test selbst lastabhängig; im Report begründen, wie die Zelle gewählt wurde.
2. Test, dass mit gesetzter Zeitgrenze die Ersetzung wirkt: eine künstlich winzige Grenze erzeugt
   Timeouts, die Zähler steigen und der Ausgang heißt dann Timeout, nicht `wrong_shape`. Ebenso,
   dass die Originalfunktion nach dem Adapter-Lebenszyklus nicht dauerhaft für andere Konfigurationen
   verändert bleibt, falls mehrere Adapter in einem Prozess leben.
3. Nachweis über die 504 + 504 vorhandenen `_wp_n23`-Records (nur lesend): Wie viele `wrong_shape`
   haben exakt die Sentinel-Gestalt? Erwartet: alle. Wenn nicht, die Ausnahmen auflisten.
   Falls die Vorhersage-Arrays nicht im Record liegen, das sagen und diesen Punkt durch Abnahme 5
   ersetzen.
4. `python -m pytest baselines/tests -q` grün.
5. Rauchtest im Docker-Image auf **einer** abweichenden Zelle, 2 Wiederholungen je Modus, 1 Shard.
   Ergebnis in den Report. Wenn Docker aus deiner Umgebung nicht erreichbar ist: als `blocked`
   für genau diesen Punkt melden, der Rest bleibt `done`-fähig.
6. Report `codex/reports/REPORT_WP_N24.md` mit Belegen zu Punkt 1 (Datei:Zeile im Image), der
   Zellenliste, der Laufzeitschranke und den **exakten Befehlen** für den vollen Lauf:
   `faithful` mit 4 Shards, `faithful` mit 1 Shard, `lifted` mit 4 Shards, jeweils 3 Wiederholungen,
   Referenz- und Kandidatenumgebung. Dazu eine Obergrenze der Laufzeit aus den Schranken (nicht aus
   Mittelwerten) sowie der Auswertungsbefehl.

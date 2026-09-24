# WP-N23 — Harness: gescheiterte Integrationen sichtbar machen statt still als R² = 0 zu verbuchen
**Language: Python**

## Ausführung

Lokal umsetzbar und testbar. Ein erneuter Lauf der ODEFormer-Raster ist **nicht** Teil dieses
Pakets — den entscheidet und fährt Claude.

## Der Befund

`baselines/harness.py`, `r2_by_dimension`: Ist die Vorhersage `None`, hat sie die falsche Form oder
enthält sie nicht-endliche Werte, liefert die Funktion für jede Dimension **0.0**. Ebenso wird ein
nicht-endlicher Score still zu 0.0, und eine Dimension ohne Varianz in der Referenz ebenfalls.
Im ODEFormer-Referenzraster (1.008 Records, `analysis/data/paper1_phaseC_v1/odeformer_baseline/`)
stehen 11–12 Generalisierungszellen je Konfiguration auf exakt 0.0, bei `generalization_status =
success`. Die R² > 0.9-Rate ändert sich dadurch nicht — beide Fälle liegen unter der Schwelle —,
aber eine divergente Integration ist ein **eigener Befund**, den EvoODE getrennt zählt, und er ist
heute im Record nicht von einem echten schlechten Fit zu unterscheiden. `CLAUDE.md`,
Designprinzip 6: Diagnosen nicht still verwerfen.

## Was zu tun ist

1. **Die R²-Werte selbst ändern sich nicht.** Die 0.0-Konvention bleibt für die Rate bestehen,
   damit neue und alte Records in der Rate vergleichbar bleiben. Geändert wird nur, dass der Grund
   **mitgeschrieben** wird.
2. Für Rekonstruktion und Generalisierung je ein Feld, das den Ausgang der Vorhersage benennt, mit
   einer kleinen, festen Wertemenge — mindestens: Vorhersage vorhanden und endlich; keine
   Vorhersage (`None`, etwa weil die Integration abbrach); falsche Form; nicht-endliche Werte in der
   Vorhersage. Dazu je Dimension, ob der Score regulär berechnet oder durch die 0.0-Konvention
   ersetzt wurde, und aus welchem Grund (nicht-endlicher Score, Referenz ohne Varianz).
3. Wo die Vorhersage entsteht (ODEFormer-Adapter und SINDy-Pfad im Harness), wird eine Ausnahme
   bei der Integration nicht verschluckt, sondern als Grund im Record festgehalten — Typ und
   Meldung, gekürzt.
4. **Nur prüfen, nicht ändern:** Ob `analysis/scripts/aggregate/run_wp_n6_sindy_baseline.py`, mit
   dem C-4 gerechnet wurde, dieselbe stille 0.0-Konvention hat. Im Report mit Datei:Zeile
   beantworten. Das Skript nicht anfassen — C-4 ist gerechnet.
5. Das Zusammenfassungsskript `baselines/summarize_odeformer_grid.py` weist die Zahl der Zellen je
   Ausgang getrennt aus, sobald die Felder vorhanden sind, und kommt mit alten Records ohne die
   Felder zurecht (dann als „nicht erfasst" ausgewiesen, nicht als 0).

## Verboten

- Keine Git-Operationen.
- Keine Änderung an R²-Werten, Schwellen, Aggregationen, Konfigurationen.
- `run_wp_n6_sindy_baseline.py` und alles unter `analysis/data/` nicht verändern.
- ODEFormer nicht patchen. Nichts anfassen außerhalb von `baselines/`.
- Nichts, was länger als 15 Minuten läuft.

## Abnahme

1. Neue Felder in beiden Pfaden, feste Wertemenge, im Report dokumentiert.
2. Tests mit echten Trajektorien aus dem Export: Vorhersage `None`, nicht-endliche Vorhersage,
   falsche Form, Referenz-Dimension ohne Varianz — jeweils R² unverändert 0.0 **und** der richtige
   Grund im Record. Ein Test, der zeigt, dass ein regulärer Fall unverändert bleibt.
3. Zusammenfassung zeigt die Ausgänge; alte Records ohne Felder werden als „nicht erfasst"
   geführt.
4. `python -m pytest baselines/tests -q` lokal grün.
5. Report `codex/reports/REPORT_WP_N23.md`, inklusive der Antwort zu Punkt 4 und dem Befehl, mit
   dem Claude die beiden Raster neu rechnen kann (Records vollständig neu erzeugen, nicht
   überspringen).

# WP-DIAG-AMB-a — Diagnose AMBIGUOUS vs. WRONG (Skript, Tests, kein langer Lauf)
**Language: Python**

Grundlage und eingefrorene Regeln: `docs/DIAGNOSTIC_AMBIGUITY.md`. Lies es vollständig. **Kein Gate 2A v4.** Die
Methode von v3 wird unverändert benutzt. Bestehende Dateien unter `experiments/annihilator_gate2a_v3/` werden
**nicht verändert**. Neu entsteht nur ein Skript, das sie importiert.

## Zu bauen

`experiments/annihilator_gate2a_v3/diagnostics/ambiguity_diagnostic.py` (mit `__init__.py`), Ausgabe nach
`experiments/annihilator_gate2a_v3/results/diagnostic_ambiguity/`.

1. **Zellen:** genau F1, F2, F4, F5, F6, F8, Domäne `wide`, $\eta = 0.01$. Gruppen N1 = {F4, F5, F8},
   I = {F1, F2, F6}. Fest im Code, nicht per Argument erweiterbar.
2. **Parameter:** $\ell_{\max}$ und $\tau$ so beschaffen, wie `run_gate2a.py` sie für einen Lauf beschafft (aus den
   Stufe-K-Ergebnissen von v3). Prüfe, dass $\ell_{\max} = 4$ und $\tau$ dem Wert in
   `results/calibration/appendix_A.json` (`tau`) entspricht, sonst Abbruch. Sonst Standard-`Settings()`. Keine
   Variante, kein Überschreiben von Feldern außer denen, die `run_gate2a.py` für einen Standardlauf ebenfalls setzt.
   Schreibe alle verwendeten Settings-Felder in die Ausgabe.
3. **Eine Realisierung:** Daten mit `noisy_sample(function_key, wide, settings.n, 0.01, seed)`, dann
   `full_search(..., with_bootstrap=True)`. Zustand und Quellen durch **Aufruf** von `_state_for_clean` aus
   `acceptance/stage_k_calibration.py` (nicht kopieren), erwartete Klasse und Orakel aus
   `results/oracle_reference_v3.json` wie dort. Prüfe, dass die erwartete Klasse für F4, F5 und F8 der Referenz aus
   Anhang B entspricht ((2,1), (3,1), (1,2)).
4. **Seeds:** Realisierung $k$ hat Seed $50000 + k$. Argumente `--reps N` (Realisierungen $k = 0 \ldots N-1$) und
   `--pilot` (gleichbedeutend mit `--reps 2`).
5. **Pro Realisierung ein Record** (eine JSON-Zeile, angehängt an `records.jsonl`, sofort nach Fertigstellung
   geschrieben): Funktion, Gruppe, Seed, gewählte Klasse oder `null`, Zustand, Quellen (A1/A2/A3), `bootstrap_share`,
   ob die gewählte Klasse die Referenzklasse ist, `n_exact` der gewählten Klasse, $T$, dof, kritischer Wert, Zahl
   geprüfter Klassen, AML-Iterationen und Konvergenz der Hauptsuche, `boot_reps`, Winkel (Punkt 6), Wall-Clock in
   Sekunden (nur Logistik). Nimm die Feldnamen aus `Selection` in `operator_search.py`. Nenne im Report für jedes
   Feld die Herkunft: bestehendes `Selection`-Feld, Orakel oder neu berechnet.
6. **Winkel (diagnostisch):** Ist `n_exact` der gewählten Klasse > 0, der Hauptwinkel in Grad zwischen $\hat c$ und
   dem exakten Nullraum dieser Klasse, also $\arccos(\lVert P\hat c\rVert / \lVert\hat c\rVert)$ mit $P$ als Projektor
   auf den Nullraum. Den Nullraum mit derselben Rechnung wie `_nullspace` in `oracle.py` bestimmen (mpmath-SVD,
   gleiche Schwelle), aber **alle** `n_exact` Basisvektoren nehmen, nicht nur einen. Ergebnis pro (Funktion, Klasse)
   in `nullspace_cache.json` zwischenspeichern. **Vorher prüfen**, dass Koeffizientenreihenfolge und Skalierung von
   $\hat c$ und der Orakel-Spalten übereinstimmen: Für die Referenzklasse jeder der sechs Funktionen muss der
   Orakel-Vektor mit dem Referenzkoeffizientenvektor aus `reference_for` bis auf Vorzeichen übereinstimmen. Gelingt
   das nicht, `blocked`. Ist `n_exact = 0`, ist der Winkel `null`. Der Winkel geht nicht in den Zustand ein.
7. **Fortsetzbar:** Beim Start `records.jsonl` lesen und erledigte (Funktion, Seed) überspringen. `--workers N`
   (höchstens 6, parallel über Realisierungen), Fortschrittszeile mit Zeitstempel pro Record nach `run.log`. Am Ende
   eine Datei `DONE`.
8. **Auswertung** (`--summarize`, liest nur `records.jsonl`, rechnet nichts neu):
   - pro Funktion und pro Gruppe die Tabelle der Zustände (Anzahl, Anteil) und die AMBIGUOUS-Quellen (A1, A2, A3,
     mehrere);
   - $P(\texttt{WRONG} \mid \text{eindeutig})$ je Funktion und Gruppe;
   - B1–B4 genau nach `docs/DIAGNOSTIC_AMBIGUITY.md` §5 mit Wert, Schwelle und erfüllt ja/nein, dazu das Verdikt
     „interessant“ oder „negativ“. Das Verdikt wird nur ausgegeben, wenn alle sechs Zellen dieselbe Zahl $N$ an
     Records haben, sonst „unvollständig“;
   - Winkel: Median und Maximum je Funktion und Zustand;
   - Kosten pro Funktion: Mittelwert und Maximum von geprüften Klassen, AML-Iterationen, Wall-Clock.
   Ausgabe `summary.json` und `summary.md`. Die Markdown-Datei sagt oben in einem Satz, dass dies eine Diagnose mit
   v3 ist und kein Gate-Lauf.
9. **pytest** unter `experiments/annihilator_gate2a_v3/tests/`:
   - die Auswertung auf Records, die aus einem **echten** Record abgeleitet sind (erzeuge ihn mit einem echten
     Aufruf, siehe „Ausführen“), mit Fällen für jedes der vier Kriterien an und knapp neben der Schwelle, für „keine
     eindeutige Ausgabe in N1“ und für ungleiches $N$;
   - Winkel: für den Referenzvektor selbst etwa 0°, für einen senkrecht zum Nullraum konstruierten Vektor 90°;
   - Fortsetzen: ein vorhandener Record wird nicht erneut gerechnet.

## Ausführen

Nur Tests und **ein** echter Aufruf für den Record der Fixture: F2, Seed 50000, mit Bootstrap. Dauert er nach
Hochrechnung länger als 15 Minuten, abbrechen und im Report sagen, wie weit er kam. Den Pilot **nicht** starten. Der
Report nennt die exakten Befehle für Pilot, Hauptlauf und `--summarize`.

## Verboten

Keine bestehende Datei unter `experiments/` ändern. Keine Konstante, Schwelle, Regel oder Settings-Variante ändern
oder hinzufügen. Keine anderen Funktionen, Domänen, Rauschstufen oder Seeds außer den oben genannten. Keine
schmale Domäne. Kein Pilot- oder Hauptlauf. Nichts außerhalb von `experiments/annihilator_gate2a_v3/diagnostics/`,
`experiments/annihilator_gate2a_v3/tests/`, `experiments/annihilator_gate2a_v3/results/diagnostic_ambiguity/`,
`codex/STATUS.md` und `codex/reports/`. Kein Git außer lesend.

## Abnahme

Tests grün. Prüfung der Koeffizientenreihenfolge (Punkt 6) bestanden und im Report mit Zahlen belegt. Report
`codex/reports/REPORT_WP_DIAG_AMB_A.md` mit Feldherkunft, Ergebnis des einen echten Aufrufs (Zustand, Zählgrößen,
Dauer) und den drei Befehlen. `codex/STATUS.md` mit `WP-DIAG-AMB-a`.

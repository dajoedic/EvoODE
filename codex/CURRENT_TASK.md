# WP-G2A3-a — Gate 2A v3: AML-Schätzer mit L-BFGS, Orakel-Korrekturen, Stufe K verteilbar
**Language: Python**

Grundlage, **wörtlich verbindlich:** `docs/GATE_2A_v3.md` (eingefroren am 2026-10-05) zusammen mit
`docs/GATE_2A_v2.md`. v3 ist v2 mit den Änderungen Ä1–Ä3. Hintergrund steht im `DIARY.md` vom 05.10.

## Ort

Neues Verzeichnis `experiments/annihilator_gate2a_v3/`, ausgehend von einer Kopie von
`experiments/annihilator_gate2a_v2/` **ohne** dessen `results/`. v2 bleibt unverändert, einschließlich seiner
Ergebnisse. Der v2-Orakel-Cache (`experiments/annihilator_gate2a_v2/results/oracle_reference_v2.json`) darf für die
Nullraumrechnung übernommen werden, weil sich daran nichts ändert. Er wird nach `annihilator_gate2a_v3/results/`
kopiert, und die Herkunft wird in den Metadaten vermerkt.

## Umzusetzen

1. **Ä1, Schätzer:** FNS wird ersetzt durch die Minimierung von $J(x/\|x\|)$ mit SciPy `L-BFGS-B` ohne Schranken.
   Einzelheiten:
   - analytischer Gradient $2X(c)c$, auf den Tangentialraum projiziert und durch $\|x\|$ geteilt;
   - Start ist der SVD-Kandidat;
   - feste Werte: `gtol` 1e-12, `ftol` 1e-15, `maxiter` 2000; kein Multistart;
   - Nicht-Konvergenz wird je Lauf protokolliert (Flag, Iterationen, Meldung), das Ergebnis trotzdem verwendet;
   - Name in Code und Ausgaben: „AML (L-BFGS)“.

   Kovarianz, Test, A1, A2 und A3 bleiben unverändert und arbeiten am neuen $\hat c$. Ein pytest-Fall prüft:
   $J(\hat c) \le J(\text{SVD-Start})$, und der Gradient verschwindet am Ergebnis (projizierte Norm klein). Ein
   zweiter Fall prüft auf **K1 breit, 1 %, Seed 0**: Der Winkel zu $c^*$ liegt unter 1°. Claude hat dort 0,25°
   gemessen.
2. **Ä2, Orakel:** Die $n_{\text{exact}}$-Tabelle der breiten Domäne gilt für beide Domänen. Die schmale
   Rechnung bleibt eine Diagnose, ihre Abweichungen werden ausgewiesen, blockieren aber nicht. Für die schmale
   Domäne werden $c^*$ und die Referenzklasse aus der breiten Domäne transformiert, wie beim Transfer in v2 §8. Die
   direkt berechnete schmale Referenzklasse muss trotzdem übereinstimmen. Alles, was $n_{\text{exact}}$ liest
   (Zustand `TRUE_NOT_REF`), nimmt den breiten Wert.
3. **Ä3, Verifikation in echter Präzision:**
   - F1–F9 und alle K-Funktionen mit rationalen Parametern: `nsimplify`, danach vereinfacht $L^*[f]$ in SymPy
     exakt zu 0;
   - F10 und alles, was sich nicht rationalisieren lässt: mpmath mit mindestens 50 Stellen, Koeffizienten und
     Stützstellen als `mpf`, relativ unter 1e-45;
   - K3 und K4: Definitions-ODE symbolisch.

   Die bisherige float-Prüfung entfällt als Abnahmekriterium.
4. **Stufe K verteilbar ohne Zeitproblem:** Die Clean-Suche (K-c Punkt 4, 16 Zellen mit Bootstrap) wird **über die
   Teile verteilt**: Zelle $i$ läuft in Teil $i \bmod n$. Bisher lief sie ganz in Teil 0, das dauerte über 2 h und
   brach ab. Der Merge prüft, dass jede Clean-Zelle genau einmal vorkommt. Jeder Teil schreibt beim Start und nach
   jeder abgeschlossenen Einheit eine Fortschrittszeile auf stdout, mit Zeitstempel, damit sich ein laufender Teil
   beobachten lässt.
5. **Smoke:** pytest für v3, v2 und v1 grün; Orakel-Verifikation (nur Ä3, ohne Nullraum-Neurechnung) voll
   ausgeführt, denn sie ist billig; Stufe K mit `--limit`.

## Verboten

Wie in WP-G2A2-b. Insbesondere: keine Konstante, Schwelle oder Regel ändern, nichts auf F1–F10 rechnen außer der
Orakel-Verifikation, kein Multistart und keine Regularisierung, kein Git außer lesend, nichts außerhalb von
`experiments/annihilator_gate2a_v3/`, `codex/STATUS.md` und `codex/reports/`. **Stufe K nicht voll ausführen**, das
macht Claude.

## Abnahme

- Die Punkte 1–5 sind umgesetzt, die Tests sind grün, und der K1-Winkeltest besteht.
- Report `codex/reports/REPORT_WP_G2A3_A.md` mit den Zahlen, der Orakel-Verifikation pro Zelle, den Abweichungen
  und den **exakten Befehlen** für Stufe K in 8 Teilen und den Merge, jeweils mit `--n 2000 --reps 1000`.
- `codex/STATUS.md` mit `WP-G2A3-a`, `done` oder `blocked`.

> **Claude-Status:** `waiting for codex` — WP-P1b übergeben, ich prüfe alle 20 Minuten.
> Melde dich über `codex/STATUS.md`, nicht in dieser Datei. Committe nichts.
> Der Dauerauftrag steht in `codex/CODEX_PROTOCOL.md`.

# WP-P1b — Das Paket lädt nicht mehr
**Language: Julia**

## Der Befund

WP-P1 ist inhaltlich gut und wird übernommen — der Entwurfsvergleich, die Empfehlung und die drei
Nachweise (Reproduzierbarkeit, Änderung gegen `5d2f4f2`, Unempfindlichkeit gegen Kommentare)
stehen. **Aber das Paket lässt sich nicht mehr laden:**

```text
julia --project=. -e 'using EvoODE'

ERROR: LoadError: ArgumentError: Package EvoODE does not have SHA in its dependencies
in expression starting at src/structure/stage_cap_fingerprint.jl:3
in expression starting at src/EvoODE.jl:1
```

`src/structure/stage_cap_fingerprint.jl` verwendet `using SHA`. `SHA` ist zwar eine
Julia-Standardbibliothek, muss aber trotzdem in `[deps]` von `Project.toml` deklariert sein. Dort
steht es nicht.

**Damit ist der Zustand härter als jeder bisherige Fehler dieser Reihe:** Jeder Kampagnenlauf, jedes
Studienskript und jeder Test, der `using EvoODE` ausführt, bricht sofort ab. Der Working Tree ist
aktuell nicht lauffähig.

Der WP-P1-Report meldet `julia --project=. test/test_stage_cap.jl` als bestanden mit 38 Tests. Das
ist mit dem obigen Fehler nicht vereinbar. Kläre im Report, wie dieser Widerspruch zustande kam —
etwa weil der Test die Dateien per `include` statt über `using EvoODE` lädt. Das ist wichtig, weil
davon abhängt, ob die Testsuite solche Fehler überhaupt bemerken kann.

## Umfang

### Teil 1 — Abhängigkeit deklarieren

`SHA` in `[deps]` von `Project.toml` aufnehmen, mit korrekter UUID, und den `[compat]`-Abschnitt
konsistent halten, falls dort Standardbibliotheken geführt werden. `Manifest.toml` entsprechend
auflösen.

Prüfe, ob `SHA` im Projekt schon anderweitig verwendet wird und ob es eine bereits vorhandene
Hash-Funktion gibt, die stattdessen genutzt werden sollte — `config_fingerprint()` in
`studies/regression/run_regression.jl` berechnet bereits einen Hash. Wenn dort dieselbe Bibliothek
auf anderem Weg eingebunden wird, ist der einheitliche Weg zu wählen und im Report zu begründen.

### Teil 2 — Nachweis, dass es lädt

Im Report zu belegen, jeweils mit der tatsächlichen Ausgabe:

1. `julia --project=. -e 'using EvoODE; println("ok")'` läuft durch.
2. `julia --project=. -e 'using EvoODE; println(EvoODE.stage_cap_behavior_fingerprint())'` gibt
   einen Wert aus. Er muss `61b6548ef0014593` lauten — der Wert aus dem WP-P1-Report. Weicht er ab,
   ist das der eigentliche Befund und ausführlich zu berichten.
3. `julia --project=. test/test_stage_cap.jl` läuft durch.

### Teil 3 — Die Testsuite muss so etwas bemerken

Ein Test ist zu ergänzen, der das Paket über `using EvoODE` lädt und damit fehlschlägt, sobald eine
Abhängigkeit fehlt. Ort und Form wählst du; entscheidend ist, dass ein fehlender `[deps]`-Eintrag
künftig **rot** wird statt unbemerkt zu bleiben.

### Teil 4 — Der veraltete Gate-2-Test

`test/test_regression_runner_gate2.jl` schlägt mit 3 von 9 fehl, unabhängig von WP-P1. Er friert
Werte aus der Gate-2-Zeit ein, die seither bewusst geändert wurden:

| Zeile | erwartet | aktuell |
|---|---|---|
| 25 | `VARIANTS` ohne `evogrow_v2_2_stage_capped` | enthält die Variante |
| 26 | `BFGS_TIME_LIMIT_S == 1800.0` | `Inf` (Budgetumstellung, WP-B3/D2) |
| 34 | `lookahead_horizon == 2` | `5` (WP-C2) |

Alle drei Änderungen waren beabsichtigt und sind im Tagebuch belegt; der Test hinkt hinterher. Ziehe
die Erwartungen auf den aktuellen Stand nach und vermerke **in einem Kommentar im Test**, dass es
sich um einen historischen Gate-2-Freeze handelt und welche Arbeitspakete die Werte bewegt haben.

**Ändere dabei keine der geprüften Konstanten selbst** — der Test folgt dem Code, nicht umgekehrt.

## Verboten

- **Keine Cluster-Jobs, keine Kampagne, keine Regressions- oder Sondierungsläufe.**
- **Keine Änderung an der Cap-Logik** und keine Änderung an den Policy-Konstanten.
- **Keine Änderung am Fingerprint-Entwurf aus WP-P1.** Er ist angenommen; hier wird nur repariert,
  was ihn am Laufen hindert.
- **Nichts committen, nichts stagen, nichts pushen. Kein `git add -A`.**
- Nichts, was länger als 15 Minuten läuft.

## Abnahme

- `using EvoODE` läuft durch, mit Ausgabe im Report belegt.
- `stage_cap_behavior_fingerprint()` liefert `61b6548ef0014593`, oder die Abweichung ist erklärt.
- `test/test_stage_cap.jl` und `test/test_regression_runner_gate2.jl` laufen beide grün.
- Ein Test bemerkt künftig eine fehlende Abhängigkeit.
- Der Widerspruch zwischen der gemeldeten grünen Testausführung und dem Ladefehler ist erklärt.

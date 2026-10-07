# ODEBench-Smoke-Test, Version 2

**Eingefroren am 2026-10-06, vor dem ersten Discovery-Lauf von v2.** Beide Änderungen hat der Nutzer nach dem
gescheiterten Pilot von v1 gewählt. Grundlage ist `docs/ODEBENCH_SMOKE_TEST.md` (v1, Befund dort in §12). **Alles,
was hier nicht geändert wird, gilt aus v1 unverändert:** Systeme, Trainings- und Test-Anfangsbedingungen, Seeds,
Rauschen der Baselines, Kette $L \to \hat f$, Baselines, Metriken und die Entscheidungsregel §9 mit allen Schwellen.
`setup.json` und `reference.json` aus v1 bleiben gültig.

## Warum eine Version 2

Im Pilot von v1 lieferte der Annihilator auf rauschfreien Daten für die Systeme 7 und 3 `NONE`. Auf den 1024
Trajektorienpunkten verwirft der Test sogar den exakten Referenzoperator, mit $T \approx 5\cdot10^{14}$ bei einem
kritischen Wert von etwa 250. Auf 2000 gleichmäßigen Punkten derselben Domäne besteht er mit $T \approx 10^{-5}$.

Die Ursache: Die Trapezquadratur der schwachen Form ist auf Trajektoriengittern mit großen Lücken ungenau, der
numerische Boden $\tau$ wurde in v3 aber für 2000 gleichmäßige Punkte kalibriert. Das ist ein Fehler im
Versuchsaufbau, kein Ergebnis über die Methode.

Außerdem zählte in v1 eine Baseline mit allen 9 Library-Termen als „strukturell korrekt“.

## Änderung 1: Stichprobe des Annihilators (ersetzt v1 §4, zweiter Punkt)

- Die Trajektorien legen nur die Trainingsdomäne $[x_{\min}, x_{\max}]$ fest (v1 §3, Werte in `setup.json`).
- Der Annihilator bekommt $f$ auf **2000 gleichmäßigen Punkten** dieser Domäne, mit $z = (x - \mu)/s$ wie in v3,
  dazu $f_i = f(x_i) + \eta\,\mathrm{rms}(f)\,\xi_i$ (additiv, wie Gate 2A) und $\sigma = $ `sigma_eff` wie in v3.
- Der Kleinste-Quadrate-Fit von $\hat f$ (v1 §5) verwendet dieselben 2000 Punkte.
- **Ehrlich benannt:** Der Annihilator sieht damit die Trajektorien selbst nicht. Seine Seite des Vergleichs ist
  Gate 2A auf vier neuen Funktionen. Die Trajektorien dienen nur der Domäne und der Bewertung (Training und
  Generalisierung). Der Vorteil durch Oracle-$f$ wird damit noch größer und steht so in jedem Ergebnisdokument.

## Änderung 2: „strukturell korrekt“ (ersetzt v1 §7, Absatz `STRUCT_OK`)

`STRUCT_OK` gilt nur bei **exakter** Struktur und $\mathrm{NRMSE}_f \le 0{,}05$:

| Methode | `STRUCT_OK`, wenn |
|---|---|
| Annihilator | `CORRECT` und $\mathrm{NRMSE}_f \le 0{,}05$ |
| SINDy, W-SINDy | `TRUE_STRUCTURE` und $\mathrm{NRMSE}_f \le 0{,}05$ |

Obermengen (`TRUE_NOT_REF`, `TRUE_PLUS`) werden berichtet, zählen aber nicht. In der Entscheidungsregel (v1 §9) gilt
überall diese Definition.

## Technisches (ohne Einfluss auf Regeln)

- Ergebnisse von v2 liegen in `experiments/annihilator_odebench_smoke/results_v2/`, jeder Record trägt
  `spec_version = 2`.
- Die Records aus dem Pilot von v1 werden nicht wiederverwendet.
- `STRUCT_OK` wird in der Auswertung aus Kategorie und $\mathrm{NRMSE}_f$ neu berechnet, nicht aus einem
  gespeicherten Feld übernommen.
- Das Fortschrittsprotokoll schreibt die Sekunden je Record. In v1 standen dort im Worker-Pfad `null`.
- Läufe über 2 h starten losgelöst: eigener Prozess, Logs, `DONE`-Datei.

## Ablauf

1. Codex setzt die beiden Änderungen um (WP-OB-B), mit Tests. Die Plausibilitätsprüfung 2 aus v1 §8 wird auf der
   neuen Stichprobe wiederholt.
2. **Pilot v2:** $\eta = 0$, Systeme 7 und 3, alle Methoden. Ziel ist nur der technische Durchlauf und die Kosten.
   Die Records zählen im Hauptlauf mit.
3. **Hauptlauf v2:** alle 4 Systeme, $\eta \in \{0;\ 0{,}01\}$, Seeds wie in v1. Laufort nach den Kosten aus dem
   Pilot.
4. Auswertung nach v1 §9 mit Änderung 2, Ergebnis in §Ergebnis unten und in `docs/ODEBENCH_SMOKE_TEST_RESULT.md`.

## Ergebnis

Hauptlauf am 07.10. von 01:27 bis 03:49 auf dem Laptop, Code `f3faa77`, 72 Records, `DONE`. Ausführlich mit Tabelle,
Gleichungen und Lesart: `docs/ODEBENCH_SMOKE_TEST_RESULT.md`.

| `STRUCT_OK` | rauschfrei | 1 % |
|---|---:|---:|
| Annihilator | 2/4 (3, 21) | 0/4 |
| SINDy | 0/4 | 0/4 |
| W-SINDy | 0/4 | 0/4 |

**Verdikt: Idee #1 beenden, ausgelöst durch Bedingung A** (Annihilator rauschfrei 2/4 < 3/4). B, C und „weiter
diskutieren“ greifen nicht.

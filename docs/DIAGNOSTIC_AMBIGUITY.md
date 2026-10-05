# Diagnose: Trennt `AMBIGUOUS` identifizierbare von nicht identifizierbaren Fällen?

**Eingefroren am 2026-10-05, vor jedem Lauf.** Festgelegt vom Nutzer. Änderungen nach dem ersten Lauf brauchen eine
neue Version dieses Dokuments; dieses bleibt mit seinem Ergebnis stehen.

**Was das ist:** eine Diagnose mit der unveränderten Methode aus Gate 2A v3. **Kein Gate 2A v4**, keine Reparatur,
keine Änderung von Schätzer, Schwellen, Ambiguitätsregeln, Klassenordnung oder Rauschmodell. Sie entscheidet
ausschließlich, ob der praktische Benchmark (`PRACTICAL_ANNIHILATOR_BENCHMARK.md`) weiterverfolgt wird.

**Folge für F1–F10:** Nach diesem Lauf mit verrauschten Daten sind F1–F10 ein **Entwicklungsset**, kein unberührtes
Gate-Set mehr. Eine spätere Gate-Version braucht neue Testfunktionen.

## 1. Frage

Anhang B sagt, dass F4, F5 und F8 bei 1 % Rauschen auf der breiten Domäne nicht identifizierbar sind (N1). Reagiert
die Methode dort überwiegend mit `AMBIGUOUS`, und das deutlich häufiger als in identifizierbaren Fällen, oder wählt
sie stabil eine falsche Klasse?

## 2. Zellen

| Gruppe | Funktionen | Domäne | $\eta$ |
|---|---|---|---|
| N1 | F4 $\log x$, F5 $x\log x$, F8 $x/(2+x)$ | breit | 0,01 |
| I (Kontrolle) | F1 $x^2$, F2 $e^{1.5x}$, F6 $e^{-x^2}$ | breit | 0,01 |

Keine anderen Funktionen, Domänen oder Rauschstufen.

## 3. Methode

Gate 2A v3 unverändert: `full_search` mit Bootstrap (AML mit L-BFGS, `maxls = 40`), Standard-`Settings`
(`boot_reps = 50`, `boot_threshold = 0.8`, `a3_trace_threshold = 0.1`), keine Varianten S1–S16. $\ell_{\max} = 4$ und
$\tau = 3.4\cdot10^{-7}$ aus Stufe K v3. Rauschmodell `noisy_sample`. Zustände genau nach `_state_for_clean`
(Vorrang `NONE` > `AMBIGUOUS` > `CORRECT` > `TRUE_NOT_REF` > `WRONG`), Referenzklasse und `n_exact` aus
`results/oracle_reference_v3.json`.

**Seeds:** eigener Bereich ab 50000 (Realisierung $k$ hat Seed $50000 + k$). Kein Überlapp mit den Gate-Seeds 0–19
und 1000–1019 und mit Stufe K.

**Diagnostisch, ohne Einfluss auf den Zustand:** der Winkel zwischen $\hat c$ und dem exakten Nullraum der gewählten
Klasse (nur wenn dieser nicht leer ist).

## 4. Ablauf

1. **Pilot:** 2 Realisierungen je Zelle (Seeds 50000, 50001). Daraus Zählgrößen und Kosten pro Realisierung.
2. **Vor dem Hauptlauf** legen Nutzer und Claude $N$ (gleich für alle sechs Zellen, Ziel 100) und den Laufort fest
   und tragen beides hier in Abschnitt 6 ein. Das geschieht nur anhand der Kosten, nie anhand von Zuständen aus dem
   Pilot.
3. **Hauptlauf:** Seeds $50000 \ldots 50000 + N - 1$. Die Pilot-Realisierungen zählen mit.

## 5. Entscheidungsregel

Eindeutige Ausgabe heißt `CORRECT`, `TRUE_NOT_REF` oder `WRONG`. Alle Anteile werden über die drei Funktionen der
Gruppe aggregiert, Nenner ist die Zahl der Realisierungen der Gruppe ($3N$), außer bei der bedingten Rate.

| | Bedingung |
|---|---|
| B1 | $P(\texttt{WRONG} \mid \text{eindeutige Ausgabe}, N1) < 0{,}20$ |
| B2 | $P(\texttt{AMBIGUOUS} \mid N1) \ge 0{,}50$ |
| B3 | $P(\texttt{CORRECT} \mid I) \ge 0{,}70$ |
| B4 | $P(\texttt{AMBIGUOUS} \mid N1) - P(\texttt{AMBIGUOUS} \mid I) \ge 0{,}25$ |

Gibt es in N1 keine eindeutige Ausgabe, gilt B1 als erfüllt.

- **Interessant**, nur wenn B1–B4 alle erfüllt sind. Dann folgt die Ausarbeitung von `docs/PRACTICAL_BENCHMARK_v1.md`
  mit eingefrorenen numerischen Kriterien und Baselines.
- **Negativ** für die Abstention-Story, sobald eine Bedingung verfehlt ist. Dann wird kein Hold-out-Set gebaut und
  kein größerer Benchmark gestartet.

Keine Schwellenänderung nach dem Lauf. Das Ergebnis darf nicht genutzt werden, um A1, A2, A3 oder andere Schwellen
nachzujustieren.

## 6. Festlegung nach dem Pilot

Festgelegt am 2026-10-05 um ca. 14:45 vom Nutzer, **bevor die Pilot-Zustände angesehen wurden.**

- $N = 100$ je Zelle, Seeds 50000–50099. Die 12 Pilot-Records (Seeds 50000, 50001) zählen mit, offen sind 588.
- Laufort: Orion, 11 Pods à 1 Kern, disjunkte Teile. Erwartete Laufzeit rund 32 h. Der Nutzer erlaubt die
  Überschreitung der 24-h-Grenze.
- Grundlage, nur Kosten aus dem Pilot (12 Realisierungen, Laptop, 6 Worker): 1–7 geprüfte Klassen, 4–59
  AML-Iterationen, im Mittel 36 min, höchstens 51 min pro Realisierung; hochgerechnet 359 Kernstunden.
- Offengelegt: Im Pilot schrieb `run.log` den Zustand mit. Der Zustand **einer** Realisierung (F2, Seed 50000)
  war deshalb vor dieser Festlegung sichtbar. Die Zahl der geprüften Klassen verrät den Zustand indirekt. Beides
  ging nicht in die Festlegung ein.

## 7. Ergebnis

*(nach dem Hauptlauf)*

# CURRENT TASK: WP-P1c — Benchmark so einstellen, dass er das Kostenproblem trifft

**Language: Julia**

## Context

WP-P1b ist umgesetzt und korrekt: Screening-Budgets greifen jetzt auch für `EvoGrowV3`, die frühe
Verwerfung läuft über `unstable_check` statt `isoutofdomain`, der Default-Pfad ist wieder
verhaltensgleich, und die Retcode-Kategorien sind über Enum-Vergleich abgesichert.

Offen sind nur noch zwei Punkte am **Messaufbau** des Mikro-Benchmarks. Beide stammen aus der
Nachrechnung des Baseline-v0-Logs, level-aufgelöst für System 26, Seed 42:

```
bis Level 12:   1,6 min      <- aktuelle Benchmark-Grenze
Level 13:     147 s
Level 14:     878 s
Level 16:     611 s
bis Level 18:  39,7 min      <- Stage 3 beginnt
Level 19:    1484 s
bis Level 20:  66,2 min
```

Der Kostenausbruch beginnt bei Level 13. **Mit 12 Leveln misst der Benchmark ausschließlich den
billigen Bereich und würde zwischen A und B praktisch keinen Unterschied zeigen** — er kann die
Frage, für die er gebaut wurde, nicht beantworten. Der Richtwert „12 Level" stammt aus der
WP-P1b-Spec und war ohne diese level-aufgelöste Nachrechnung gewählt; er wird hiermit korrigiert.

## Required Content

### 1. Level-Budget so wählen, dass der teure Bereich erfasst wird

Das Benchmark-Level-Budget auf **18** setzen. Begründung im Skript-Header festhalten: Level 13–17
enthalten die teuren Auswertungen, Level 18 erreicht Stage 3; laut Baseline v0 liegt Fall A damit
bei etwa 40 Minuten, also klar begrenzt und trotzdem im relevanten Regime. Der Wert bleibt eine
benannte Konstante, getrennt von der Regression-Konfiguration.

### 2. Kosten pro Level aus dem Level-Log statt aus der Gesamtzeit

`cost_per_level_s` wird derzeit als Gesamtlaufzeit geteilt durch Levelzahl berechnet. Der zuerst
laufende Fall trägt dabei die gesamte Julia-Kompilierzeit des `discover`/BFGS/Solver-Pfads — und
das ist seit WP-P1b bewusst Fall B, also genau der Fall, der gut aussehen soll. Die Messung ist
damit systematisch gegen B verzerrt.

Zu tun:
- Die Kosten pro Level aus den bereits vorhandenen Per-Level-Zeiten im `level_log` ableiten, nicht
  aus der Gesamtlaufzeit.
- Das erste Level aus dieser Kennzahl ausschließen (Kompilierungseffekt) und das im Ausgabefeld
  bzw. Header klar benennen.
- Zusätzlich zum Mittelwert den **Median** pro Level ausgeben. Die Verteilung ist stark
  rechtsschief (einzelne Level dominieren), der Mittelwert allein ist irreführend.
- Die Gesamtlaufzeit weiterhin ausweisen; sie bleibt die ehrliche Zahl für „was kostet ein Lauf".

### 3. Per-Level- und Per-Stage-Aufschlüsselung ausgeben

Der Bericht enthält bisher nur Summen über den ganzen Lauf. Die Diagnose, die dieses WP ausgelöst
hat, war aber pro Stage aufgeschlüsselt — ohne dieselbe Auflösung ist das Ergebnis nicht mit der
Baseline vergleichbar.

Zu tun:
- Die Per-Level-Zeilen aus dem `level_log` (mindestens: Level, Stage, Zeit, Parameter-Fits,
  ODE-Solves, verworfene Solves) für beide Fälle in die JSON-Ausgabe schreiben.
- Eine Aufschlüsselung nach Stage (Levelzahl, Zeit, Zeit pro Level) für beide Fälle in die
  Textausgabe schreiben, im selben Zuschnitt wie die Baseline-Tabelle im `DIARY.md`-Eintrag vom
  2026-07-22.

## Verification

Nur ein billiges System rechnen: `PROFILE_SYSTEM_ID=3`. **Nicht** System 26 — der bleibt dem
externen Lauf vorbehalten.

1. Der Lauf erzeugt vollständige CSV-, JSON- und Textausgaben inklusive Per-Level-Zeilen und
   Per-Stage-Aufschlüsselung für beide Fälle.
2. Die neue Kennzahl für Kosten pro Level stimmt mit der Summe der Per-Level-Zeiten überein
   (abzüglich des ausgeschlossenen ersten Levels) und ist nicht aus der Gesamtzeit abgeleitet.
3. Die Zwischenausgabe nach Fall B ist weiterhin vollständig auf der Platte, bevor Fall A startet.
4. Die beobachteten Retcode-Strings stehen in der Ausgabe.

Nenne im Abschlussbericht die tatsächlich gemessenen Zahlen für System 3 (Laufzeit A, Laufzeit B,
Kosten pro Level, Retcodes) — nicht nur „läuft durch".

## Constraints

- Nur `studies/profiling/profile_eval_cost.jl` ändern. Kein Eingriff in `src/`, nicht in
  `run_regression.jl`, nicht in die Regression-Konfiguration.
- Keine Änderung an Suchverhalten, Metrikdefinitionen oder `config_fingerprint`.
- Keine neuen Abhängigkeiten.
- Weiterhin nicht Teil dieses WP: ableitungsbasiertes Screening-Kriterium, `use_pretuning`,
  finaler Refit auf Referenz-Fidelity, Parallelisierung, WP-v3.3, WP-H2.

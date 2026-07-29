# CURRENT TASK: WP-v3.3 — Gleichungs-bewusste Child-Generation (EvoGrowV3)

**Language: Julia**

## Context

WP-T2 (System 26, Seed 42, 30 Level) hat den v3-Ansatz empirisch bestaetigt: Der
Referenzpfad findet Gleichung 1 nach Pruning exakt (`du1`-Support `{u1, u1^2, u1*u2}`),
laesst Gleichung 2 aber vollstaendig falsch (`{u1, u1^2}`), und der globale Plateau-Mechanismus
eskaliert trotzdem beide Gleichungen bis Stage 5 (Overshoot 2, `pruned_match = false`). Genau
dieses Gleichungs-Ungleichgewicht adressiert EvoGrow v3: jede Gleichung soll nur wachsen, wenn
ihr eigenes Residuum stagniert.

Der aktuelle Stand (`EvoGrowV3`, WP-v3.2, `src/structure/evogrow_v3.jl`) traegt bereits
Pro-Gleichungs-**State** (`eq_stages`, `eq_levels_in_stage`, `eq_plateau_histories`,
`eq_stage_histories`), promotet aber noch **synchron**: `_apply_lockstep_stage_update!` erhoeht
alle Gleichungen gleichzeitig, getrieben von der globalen `_stage_progression_decision`. Damit
sind alle `eq_stages` in jedem Level identisch, und die Child-Generation nutzt den aggregierten
`current_stage` ueber `_expand_with_usage_policy(ind, dim, allowed_terms, current_stage_terms, ...)`.

Diese Aufgabe ist der **erste** von zwei Schritten, die die Pro-Gleichungs-Semantik einschalten:

- **WP-v3.3 (diese Aufgabe):** Child-Generation gleichungs-stufen-bewusst machen — die Designnotiz
  `docs/evogrow_v3_design.md`, Abschnitt 6. Solange alle `eq_stages` gleich sind (der jetzige
  Lockstep-Zustand), muss sich **exakt nichts** aendern; die Ergebnisse bleiben bit-identisch zum
  heutigen `EvoGrowV3` und damit zu v2.2. Die neue Logik greift ausschliesslich, sobald Gleichungen
  auf **verschiedenen** Stufen stehen.
- **WP-v3.4 (spaeter, NICHT Teil dieser Aufgabe):** die Pro-Gleichungs-Promotionsregel
  (Designnotiz Abschnitt 3–4), die die Stufen erst divergieren laesst. Erst dann wird die hier
  gebaute Child-Generation im echten Lauf wirksam.

Diese Trennung ist bewusst: WP-v3.3 fuegt einen Mechanismus hinzu, der unter uniformen Stufen
beweisbar ein No-Op ist, und ist deshalb regressionssicher gegen Baseline v0/v1 pruefbar, ohne dass
sich eine einzige Zahl aendert.

## Goal

`EvoGrowV3` erzeugt Kinder **pro Gleichung** aus einer gleichungs-eigenen Term-Menge, die durch
`eq_stages[k]` und eine Cross-Term-Paarregel bestimmt ist (Designnotiz Abschnitt 6). Bei uniformen
`eq_stages` faellt dieser Pfad strukturell auf den bestehenden `_expand_with_usage_policy`-Aufruf
zurueck, sodass die Resultate bit-identisch zum heutigen `EvoGrowV3` bleiben. Die Promotionslogik,
die Metriken und `EvoGrow`/v2.2 bleiben unveraendert.

## Files

- **Aendern:** `src/structure/evogrow_v3.jl` (Child-Generation-Aufruf im Level-Loop).
- **Ergaenzen erlaubt:** eine neue Datei im Structure-Layer (z. B. `src/structure/evogrow_v3_childgen.jl`)
  fuer die gleichungs-bewusste Expansion und die Verfuegbarkeits-Helfer, in `src/EvoODE.jl` an der
  passenden Stelle eingebunden. Alternativ die Helfer in `evogrow_v3.jl` selbst — Codex entscheidet,
  aber ohne bestehende Funktionen umzuschreiben.
- **Nicht anfassen (Verhalten):** `src/structure/evogrow.jl` (insb. `_expand_with_usage_policy`,
  `_expand`, `_expand_stage_aware`, `_expand_stage_soft`, `_allowed_terms`, `_current_stage_terms`),
  `src/structure/evogrow_screening.jl`, die Basis-Term-Reihenfolge und Stufenzuordnung in
  `StagedPolynomialBasis`, die Promotionslogik, die Regressions-Konfiguration.
- **Neuer Test:** eine fokussierte Testdatei unter `test/` (bestehendes Testschema folgen).

## Required Content

### 1. Verfuegbarkeits-Praedikat pro Gleichung

Fuer Gleichung `k` und Term-Index `t` seien definiert:

- `stage(t)`: die Stufe von `t`, also der Index der Gruppe in `basis.term_groups`, die `t` enthaelt.
- `vars(t)`: die Menge der Variablenindizes, die in `t` vorkommen (z. B. `u1*u2` -> `{1, 2}`,
  `u1^2` -> `{1}`).

Term `t` ist fuer Gleichung `k` verfuegbar (Menge `A_k`) genau dann, wenn **beide** Bedingungen gelten:

1. **Basisregel:** `stage(t) <= eq_stages[k]`.
2. **Cross-Term-Regel:** falls `t` mehrere Variablen koppelt (`length(vars(t)) >= 2`), zusaetzlich
   `minimum(eq_stages[v] for v in vars(t)) >= stage(t)`. Fuer Ein-Variablen-Terme entfaellt diese
   zweite Bedingung.

Die aktuelle-Stufe-Menge pro Gleichung (fuer die Usage-Policy) ist
`C_k = { t in A_k : stage(t) == eq_stages[k] }`.

Diese Formulierung ist die woertliche Umsetzung der Designnotiz Abschnitt 6 und der dort
empfohlenen Aufloesung der offenen Fragen 2 und 3 (Cross-Term nur verfuegbar, wenn **beide**
beteiligten Gleichungen die erforderliche Stufe erreicht haben; die Filterung passiert in der
Child-Generation, nicht in der Basis). `stage(t)` und `vars(t)` werden aus der vorhandenen
Basis-Term-Repraesentation abgeleitet; falls die Basis die Variablen-Zugehoerigkeit eines Terms
nicht bereits abfragbar macht, darf ein **lesender** Helfer ergaenzt werden, der die vorhandenen
Term-Metadaten introspektiert — ohne die Term-Reihenfolge oder Stufenzuordnung zu veraendern.

### 2. Gleichungs-bewusste Expansion in EvoGrowV3

Im Level-Loop von `search_structure(::EvoGrowV3, ...)` wird der heutige einzelne Aufruf

    _expand_with_usage_policy(ind, dim, allowed_terms, current_stage_terms, strategy.usage; ...)

durch eine gleichungs-bewusste Variante ersetzt, die fuer jede Gleichung `k` ihre eigene Menge
`A_k` (und `C_k`) verwendet statt der global aus `current_stage` abgeleiteten Mengen. Das Wachstum
einer Gleichung `k` darf nur Terme aus `A_k` hinzufuegen; die Usage-Policy (`:hard`/`:soft`/`:passive`)
wird pro Gleichung anhand von `C_k` angewandt (siehe Punkt 4).

Der `max_terms_per_eq`-Deckel und die uebrige Semantik der Expansion (wie viele Kinder pro Elter,
Add-Term-Verhalten) bleiben unveraendert. Es aendert sich ausschliesslich die **pro Gleichung
zulaessige Term-Menge**.

### 3. Uniform-Stufen-Delegation (strukturelle Bit-Identitaet)

Dies ist die zentrale Sicherheitsgarantie. Wenn alle Eintraege von `eq_stages` gleich sind (Wert `s`),
gilt per Konstruktion `A_k == _allowed_terms(basis, s)` und `C_k == _current_stage_terms(basis, s)`
fuer **jede** Gleichung. In diesem Fall MUSS die gleichungs-bewusste Expansion auf den **bestehenden**
`_expand_with_usage_policy`-Aufruf mit genau diesen globalen Mengen zurueckfallen — derselbe Code,
dieselbe RNG-Zieh-Reihenfolge. Damit ist bit-identisches Verhalten zum heutigen `EvoGrowV3` nicht nur
empirisch, sondern strukturell garantiert.

Der neue Pro-Gleichungs-Pfad wird ausschliesslich betreten, wenn `eq_stages` **nicht** ueberall
gleich sind. Da WP-v3.3 die Promotion nicht anfasst (weiterhin Lockstep, also immer uniform), wird
dieser Pfad im echten Lauf noch nie ausgefuehrt — er wird allein durch den Unit-Test aus
Verification A mit kuenstlich divergierenden Stufen geprueft.

Falls sich diese strukturelle Delegation nicht ohne Verrenkung erreichen laesst (z. B. weil die
RNG-Reihenfolge sonst kippt): NICHT still eine schwaechere Loesung waehlen, sondern anhalten und den
Konflikt im Abschlussbericht beschreiben.

### 4. Usage-Policy pro Gleichung

Die bestehende `StageUsagePolicy`-Bedeutung (`:hard`, `:soft`, `:passive`) bleibt erhalten, wird aber
pro Gleichung anhand von `C_k` ausgewertet. Eine Gleichung, deren neue-Stufen-Menge `C_k` leer ist
oder mit `A_k` uebereinstimmt, verhaelt sich wie im heutigen `:passive`/uneingeschraenkten Fall (vgl.
die Kurzschluss-Bedingung `current_stage_terms == allowed_terms` in `_expand_with_usage_policy`). Unter
uniformen Stufen ergibt sich dadurch exakt das heutige Verhalten (Punkt 3).

### 5. Keine Promotion-Aenderung, keine neuen Metriken

WP-v3.3 aendert **nicht** die Promotionsregel (`_lockstep_stage_progression_decision`,
`_apply_lockstep_stage_update!` bleiben wie sie sind) und fuegt **keine** neuen Metadaten-Felder
hinzu. Die Metrik-Erweiterung (Designnotiz Abschnitt 8: `eq_residual_log`, `eq_promotion_levels`
usw.) gehoert zu spaeteren WPs. Diese Aufgabe ist rein die Term-Mengen-Logik der Child-Generation.

## Verification

**Keinen langen Lauf und nicht die Regressions-Baseline starten.** Die Baseline (Systeme 26/31/63,
mehrere Tage) wird ausschliesslich extern gestartet. Codex fuehrt nur die folgenden billigen Checks aus.

### A. Unit-Test: divergierende Stufen (der Kern von WP-v3.3)

Neuer Test, der die gleichungs-bewusste Expansion direkt mit **kuenstlich gesetzten** `eq_stages`
aufruft (dim = 2, `StagedPolynomialBasis`), ohne einen vollen Suchlauf. Zu pruefen:

1. Bei `eq_stages = [1, 3]`: Kinder von Gleichung 1 enthalten **nur** Stage-1-Terme; kein Term mit
   `stage(t) > 1` erscheint je in Gleichung 1. Gleichung 2 darf Terme bis Stage 3 erhalten.
2. Ein Cross-Term `u1*u2` (Paarregel, erforderliche Stufe = seine `stage(t)`) ist bei `eq_stages = [1, 3]`
   fuer **keine** Gleichung verfuegbar, weil `min(eq_stages[1], eq_stages[2]) = 1 < stage(u1*u2)` —
   auch nicht fuer Gleichung 2, obwohl diese auf Stage 3 steht.
3. Bei uniformen `eq_stages = [3, 3]` stimmt `A_k` fuer beide Gleichungen exakt mit
   `_allowed_terms(basis, 3)` und `C_k` mit `_current_stage_terms(basis, 3)` ueberein.

### B. Bit-Identitaets-Smoke auf kleinem System

`EvoGrowV3` end-to-end auf einem **kleinen** System (System 3 oder 11, wenige Sekunden) vor und nach
der Aenderung rechnen und `loss`, `final_stage`, `eq_final_stages`, `stage_overshoot` sowie die
gefundene Struktur vergleichen. Diese muessen **identisch** sein — unter Lockstep sind alle Stufen
uniform, also greift die Delegation aus Punkt 3. Ein einfacher Weg: ein kurzes Skript, das
`discover(...)` mit `EvoGrowV3` auf System 3 mit festem Seed laeuft; Werte notieren, Aenderung
anwenden, erneut laufen, vergleichen. Bei jeder Abweichung ist die Delegation verletzt.

Der bestehende Regressions-Runner (`studies/regression/run_regression.jl`) darf **nicht** vollstaendig
gestartet werden. Wenn ein Smoke gewuenscht ist, nur ein einzelnes kleines System per direktem
`discover`-Aufruf, nicht die Matrix.

### C. Abschlussbericht

Im Bericht: dass Unit-Test A und Bit-Identitaets-Smoke B bestanden sind (mit den verglichenen Werten
aus B), wie das Verfuegbarkeits-Praedikat implementiert wurde, und die Bestaetigung, dass `EvoGrow`
und die Promotionslogik unveraendert sind.

## Constraints

- Reiner Child-Generation-Mechanismus. Keine Aenderung an Promotion, Metriken, `EvoGrow`/v2.2 oder
  der Basis-Term-Reihenfolge/Stufenzuordnung.
- Unter uniformen `eq_stages` strukturelle Delegation auf den bestehenden Pfad — Bit-Identitaet
  garantiert, nicht nur gemessen. Bei Zielkonflikt anhalten und berichten.
- `src/structure/evogrow.jl` bleibt im Verhalten unangetastet; neue Helfer additiv.
- Keine neuen Abhaengigkeiten.
- Keinen langen Lauf und nicht die Regressions-Baseline ausfuehren; nur Unit-Test A und der
  Sekunden-Smoke B auf einem kleinen System sind erlaubt.

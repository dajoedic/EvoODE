# WP-N39 (Wiederaufnahme) — PySR als GP-Baseline
**Language: Python** (PySR bringt eine eigene Julia-Laufzeit mit)

**Wiederaufnahme nach dem Nutzungslimit.** Die erste Sitzung brach mitten in der Arbeit ab. Ihre
Teiländerungen an `baselines/harness.py` (`pysr_default_config`, Finite-Differenzen-Ziele,
sympy-Kontext usw.) liegen uncommittet im Tree, zusammen mit WP-N38 Fortsetzung 3 (gemeinsame
Struktur-Expansion für ODEFormer/PySR). **Weiterarbeiten, nicht neu anfangen.** Die gemeinsame
Expansion aus WP-N38 Fortsetzung 3 ist für PySR **die** kanonische Expansion. Keine zweite bauen.

Zusätzlich zur Spezifikation unten: Die Festlegung `binary_operators`/`unary_operators` in
`pysr_default_config` (u. a. `exp`, `log`, `sqrt`, `pow`, `div`) muss in `docs/WP-N39.md` mit
Zeilenangabe auf ODEFormers Wrapper zurückgeführt sein. Die Operatormenge ist größer als die Basis.
Das bleibt so und wird deklariert (Teil A.2).

---


## Ziel

Plan §9.5 verlangt, dass PySR ein eigenes kleines Arbeitspaket bekommt, **bevor** es läuft. Dieses
Paket legt alles fest, baut den Harness und liefert eine Kostenschätzung. **Ein voller Lauf gehört
nicht dazu.** Erlaubt ist nur ein Smoke von höchstens zwei Zellen, und den fährt Claude.

## Teil A — Festlegungen (in `docs/WP-N39.md`, dazu die Begründung)

Jede Festlegung wird **vorab und mit Quelle** getroffen und nie nach Ergebnissen gewählt. Das ist
dieselbe Art Fairness-Entscheidung wie bei SINDys zehn Konfigurationen.

1. **Vorbild ist ODEFormers eigener PySR-Baseline-Harness**, lokal unter
   `outputs/third_party/odeformer/odeformer/baselines/pysr_wrapper.py`,
   `outputs/third_party/odeformer/scripts/run_baselines.py` und
   `outputs/third_party/odeformer/scripts/run_baselines.sh` (gepinnter Commit `c9193012…`). Lies
   dort aus und zitiere mit Zeilen: welches Ziel PySR fittet (Ableitungen? Wie geschätzt?), die
   Operatormenge, das Budget (Iterationen, Populationen, Zeitlimit, `maxsize` usw.), die Auswahl
   des Endmodells, wie das gefundene Modell integriert wird und die PySR-Version.
2. **Operatormenge:** Sie muss die kanonische Basis ausdrücken können (`1, u_i, u_i², u_i·u_j,
   u_i³, sin(u_i), cos(u_i)`, siehe `CLAUDE.md` „Scientific Position“). Wo ODEFormers Menge
   davon abweicht: Ist sie größer, bleibt sie, und das wird deklariert. Fehlt etwas, wird es
   ergänzt und als Abweichung deklariert.
3. **Budget je Trajektorie:** das von ODEFormer, unverändert. Ist dort ein Zeitlimit statt einer
   Zählgröße gesetzt, wird es übernommen. Daneben stehen die PySR-Zählgrößen (Iterationen,
   ausgewertete Ausdrücke, falls PySR sie liefert) im Record. Zeit bleibt Kontext, keine Evidenz
   (Design Principle 7).
4. **Determinismus und Seeds:** PySR deterministisch konfigurieren (`random_state`, single-thread,
   wie die PySR-Doku es verlangt; Quelle zitieren). Drei Realisierungen wie §9.4: Realisierung r ↔
   Seed r.
5. **Version und Umgebung:** PySR-Version und Julia-Backend pinnen. Die Umgebung kommt als eigenes
   Dockerfile `baselines/Dockerfile.pysr` nach dem Muster der ODEFormer-Images, mit gepinnten
   Requirements. Gebaut wird es von Claude/dem Nutzer, **nicht** in diesem Paket.
6. **Kanonische Expansion:** Das gefundene sympy-Modell wird expandiert und auf Basisterme
   abgebildet, damit die Strukturmetriken (roh/gepruned, wie bei ODEFormer/SINDy) berechnet werden
   können. Terme außerhalb der Basis (z. B. `exp`, verschachtelte `sin`) werden als
   „außerhalb der Basis“ gezählt. Sie sind ein Strukturfehler und kein Absturz.

## Teil B — Harness

`baselines/run_pysr_noise.py`. Er liest dieselben Export-Indizes wie WP-N38 und WP-N34, mit
derselben Validierung und Hash-Prüfung (wiederverwenden, nicht kopieren), dieselbe saubere
Auswertung (Rekonstruktion aus der sauberen Trainings-IC auf dem vollen 512er-Raster,
Generalisierung aus der sauberen zweiten IC, R² beider Aggregationen, Divergenz als Status) und
dasselbe Ausgabeformat (`details.csv`, `records.jsonl`, `summary.csv`, `export_checks.csv`, ein
Vergleichs-Join wie bei WP-N38). Bei unregelmäßigem Raster: PySRs bzw. ODEFormers dokumentierter
Umgang, ohne Interpolation, sofern die Ableitungsschätzung des Vorbilds das zulässt. Sonst wird
das deklariert. Eine scheiternde Zelle ergibt einen Fehler-Record und wird nicht repariert. Der
Stub `"pysr"` in `baselines/harness.py` wird durch den echten Adapter ersetzt oder darauf verwiesen.

Kontrolle (Test, ohne PySR): Mit einem Fake-Adapter, der die **wahre** Gleichung zurückgibt,
liefert der Harness eine Rekonstruktion von R² = 1 und einen Strukturtreffer auf einem exakten
System.

## Teil C — Kostenschätzung

Eine Formel in `docs/WP-N39.md`: Zellen × Budget je Trajektorie. Zellen sind 63 Systeme × 12
Bedingungen × 3 Realisierungen × 2 IC-Sets, dazu die Teilmenge dim 1/2 getrennt. Das Ergebnis in
Kernstunden und € (1,50 €/Kernstunde), mit der Unsicherheit. Ist das Budget ein Zeitlimit, ist die
Schätzung eine Obergrenze. Claude ergänzt nach dem Smoke einen gemessenen Wert je Zelle.

## Verboten

PySR-Läufe außer einem Smoke-Test von höchstens einer Zelle. Budget oder Operatoren nach
Ergebnissen wählen. Images bauen. `src/`, Julia-Code im Repo, die WP-N34/N38-Skripte im Verhalten
ändern (gemeinsame Hilfsfunktionen auslagern nur, wenn deren Tests grün bleiben). Git, `oc`,
`codex/CURRENT_TASK.md` bearbeiten.

## Abnahme

- `docs/WP-N39.md` mit allen Festlegungen samt Quellen und der Kostenformel.
- Harness und Tests grün (`baselines/tests/`).
- `baselines/Dockerfile.pysr` und gepinnte Requirements, nicht gebaut.
- Report `codex/reports/REPORT_WP_N39.md` mit den Befehlen für Claude (Image bauen, Smoke auf
  System 1, (σ 0,01; ρ 0), aus `outputs/stage1/data_export/index.csv`), jeweils mit Zweck, Dauer und
  Pass-Kriterium.
- `STATUS.md` nach Protokoll.

# Idee #1 (Annihilator-Spur) — Tagebuch

Neueste Einträge zuerst. Nur Einträge dieser Spur (2026-10-04 bis 2026-10-08); die älteren EvoGrow-Einträge stehen
im `DIARY.md` auf `main`.

---

## 2026-10-08

### Branch zur Akte aufgeräumt, Rohdaten archiviert
<!-- hash -->

Auf Wunsch des Nutzers enthält der Branch nur noch die Idee: Plan, Code, Ergebnisse und Weg.

- **Entfernt** (mit `git rm`, bleibt in der Historie): der ganze EvoGrow-Bestand aus der Abzweigung von `main`.
  - `analysis/`, `src/`, `test/`, `studies/`, `baselines/`, `k8s/`, `paper/`, `ext/`, `containers/`;
  - die übrigen `experiments/`, 48 EvoGrow-Dokumente, 119 EvoGrow-Codex-Berichte;
  - `PAPER_1.md`, `SCRIPTS.md`, `CHANGELOG.md`, Julia-Projektdateien, CI.
  - Ergebnis: 3083 → 363 Dateien.
- **Geblieben:**
  - die vier Annihilator-Ordner unter `experiments/`;
  - `benchmarks/data/strogatz_extended.json`, die einzige externe Abhängigkeit des Codes (ODEBench-Systeme);
  - die Akte in `docs/` und die Annihilator-Berichte von Codex.
- **Neu bzw. umgeschrieben:**
  - `README.md` (Englisch, nur die Idee);
  - `CLAUDE.md` (Akte);
  - `requirements.txt` mit der Umgebung aller Läufe;
  - knappe `.gitignore` und `.gitattributes`;
  - dieses DIARY, gekürzt auf die Einträge ab 04.10.;
  - `PRACTICAL_ANNIHILATOR_BENCHMARK.md` nach `docs/` verschoben;
  - Verweise auf `docs/evogrow_next.md` mit „auf `main`“ versehen.
- **Tests:** vor und nach dem Aufräumen je Ordner 8 + 16 + 54 + 34 bestanden. Ein gemeinsamer pytest-Lauf über alle
  Ordner scheitert an gleichnamigen Testdateien; das ist in der README vermerkt.
- **Rohdaten End-to-End:** auf das Orion-NFS kopiert (`annihilator_e2e_raw/`). Der erste Versuch brach durch einen
  VPN-Abriss ab, der zweite lief mit `robocopy /Z`. Beide SHA-256-Prüfsummen stimmen.
- **Tag** `idea01-annihilator-archive` auf diesen Stand; `idea01-annihilator-closed` bleibt beim Stand der
  Entscheidung.

### Idee #1 abgeschlossen: gescheitert
<!-- 5c840b3, 7111a78 -->

**Entscheidung des Nutzers** nach Sichtung der Ergebnisübersicht: Die Annihilator-Spur ist gescheitert und wird
beendet. Das Kernversprechen (Struktur vor Parametern, Familien jenseits fester Libraries, begründete Abstention) ist
in keiner der sieben Prüfungen eingelöst.

Die konkurrenzfähige Funktionsgüte im End-to-End-Lauf wird nicht weiter aufgeklärt; der Klärungslauf (SINDy auf
denselben geglätteten Paaren) entfällt.

**Dokumentiert in:**
- `docs/IDEA_01_ANNIHILATOR_DISCOVERY.md` §12 (Abschluss und Belegtabelle);
- `docs/IDEA_01_RETROSPECTIVE.md` §10 (Rückblick jetzt endgültig);
- `CLAUDE.md` mit Abschlussvermerk;
- READ_THIS_FIRST mit dem Endstand.

**Aufgeräumt:**
- Codex-Handshake geschlossen.
- Restdateien committet: der verworfene Entwurf `PRACTICAL_ANNIHILATOR_BENCHMARK.md`, der Orakel-Teil 12/18 und die
  Worker-Caches der v2-Abnahme, die stderr-Protokolle der End-to-End-Läufe.
- Rohdaten: Prüfsummen in `RAW_RECORDS_SHA256.txt`; die Archivierung auf dem Orion-NFS übernimmt der Nutzer.
- Endstand getaggt: `idea01-annihilator-closed`.
- README mit Branch-Hinweis: Idee, Scheitern, Wegweiser zur Akte (EvoGrow-Text darunter als Erbe markiert).

### End-to-End v1 und v2: Ergebnis
<!-- a08e647 -->

Die Kette lief ohne Fehler: v2 fertig um 02:18, die Fortsetzung von v1 um 03:29, je 216/216 Records. Ergebnis
deskriptiv in `docs/ODEBENCH_END2END_RESULT.md`.

- **Rekonstruktion bei 1 %:** Mit Glättung (v2) steigt der Annihilator von 4/0/5/4 auf 17/14/20/19 von 20 (Systeme
  3/7/19/21). Damit liegt er im Feld der Baselines.
- **Generalisierung P1:** Der Annihilator ist vorn, mit 8/10, 10/10 und 8/10 gegen 4–6/10 auf 3, 19 und 21.
- **Generalisierung P2:** etwa gleichauf. Gompertz generalisiert keine Methode.
- **Struktur bei 1 %:** Exakt trifft der Annihilator nur die Logistik (4/15). Sonst wählt er Surrogate, die Baselines
  dichte Modelle.
- **Offen:** Der P1-Vorsprung kann von der Glättung stammen, die nur der Annihilator bekommt.

**Neuer Befund:** W-SINDy ist nicht reproduzierbar. pysindy 2.1.0 zieht die Testfunktionen über das globale
`np.random` ohne Seed. Alle 33 von v2 neu gerechneten W-SINDy-Records weichen von v1 ab.

**Daten:** Die Rohdateien sind je etwa 910 MB groß, in Git kommen nur die Kompaktfassungen `records_compact.jsonl`
(je etwa 3 MB, ohne pysindy-Parameter und Trajektorien). Außerdem §9 im Rückblick nachgetragen.

### Git: v1-Rohdatei aus der lokalen Historie entfernt
<!-- 6678ab2 -->

Die v1-Rohdatei (490 MB) steckte im lokalen, ungepushten Commit `2dfd44b`. Die zwölf Commits ab dort wurden ohne
diese Datei neu geschrieben (`commit-tree` mit temporärem Index, Nachrichten, Autoren und Daten unverändert), im
manuellen Modus mit Freigabe des Nutzers. Das ist der einzige Unterschied zum alten Stand. Neue Hashes: `2dfd44b` →
`04a927e`, …, `41cf0bf` → `c97c6be`; die Kommentare in diesem DIARY sind angepasst. Sicherung des alten Stands:
`refs/backup/pre-bigfile-rewrite-20261008`. Kein Blob über 50 MB mehr vor dem Push. Die Rohdatei liegt weiter lokal
und ist über `.gitignore` ausgeschlossen.

---

## 2026-10-07

### End-to-End: Laptop im Standby, Lauf verzögert
<!-- 1057df0 -->

Um 22:05 gefunden: Seit 16:37 waren keine neuen Records dazugekommen. Laut Ereignisprotokoll war das System von
17:02 bis 22:03 im Modern Standby, die Prozesse waren eingefroren. Die Einstellung „Standby nie“ verhindert Modern
Standby bei Bildschirm-aus bzw. Deckel nicht. Die Worker rechnen seit 22:03 wieder (100 % CPU). Gegenmaßnahme:
`keep_awake.ps1` setzt `SetThreadExecutionState` (System und Display erforderlich), solange die Kette läuft.
Neue Erwartung: v2 gegen 02:30, v1 gegen 05:00. Der Deckel darf nicht geschlossen werden.

### End-to-End v2 gestartet, danach Fortsetzung von v1 (Kette)
<!-- 6b48ede, 106d5d5 -->

Zwischenstand v1 (113/216): Bei 1 % bricht der Annihilator ein. Diagnose: Der Fehler der geschätzten Ableitung liegt
bei 56–63 % (Logistik) und 140–190 % (Gompertz), und der interpolierende Spline vervielfacht das (bis zum
3400-Fachen des wahren Maximums). v1 wurde um 16:40 angehalten (fortsetzbar). v2 (`docs/ODEBENCH_END2END_v2.md`):
200 Abschnitte plus GCV-Glättungsspline, Fehler auf $f$ bei 1 % danach 1,7–3,5 % (Gompertz 10–15 %). WP-E2E-B
abgenommen; der v1-Pfad ist bitgleich zum alten Code (selbst geprüft). Die Kette `run_chain_e2e.ps1` startete um
16:37 losgelöst: v2 mit 7 Workern und übernommenen Baselines, danach Fortsetzung von v1. Erwartet: v2 gegen 22–23 Uhr,
v1 gegen 1–2 Uhr. Außerdem `docs/IDEA_01_RETROSPECTIVE.md` geschrieben (vorläufig).

### End-to-End: Spezifikation eingefroren, Pilot sauber, Hauptlauf gestartet
<!-- 47d5b07, 15bc333, 9800fa3, 2bbc6b7 -->

WP-E2E-A war `blocked`: Die Kette mit exaktem $\dot x$ brach für 7 und 19. Diagnose: Die lineare Interpolation auf
das Gitter erzeugte bei 7 einen Fehler von 0,86 %; AML auf exakt gleichmäßigen Daten findet den wahren Operator.
Mit kubischem Spline (Änderung vor jedem Lauf) bestehen 3, 19 und 21. Bei 7 bleiben $5\cdot10^{-4}$, weil die
Trajektorienpunkte bei großem $x$ dünn liegen; das ist als Grenze der Methode im End-to-End-Fall dokumentiert und
blockiert den Lauf nicht. Danach Einfrieren mit Freigabe des Nutzers. Der erste Pilot stürzte an einem
nicht serialisierbaren Worker-Record ab (WP-E2E-A3 behoben). Zweiter Pilot ($\eta = 0$, 7 und 3) von 13:25 bis
13:53: 18 Records, keine Fehlschläge. Annihilator 15–28 min pro Fit, Baselines unter 1 min. Der Hauptlauf startete
um 13:54 losgelöst (PID 20176, 6 Worker); Ende erwartet gegen 18:00.

### End-to-End-Vergleich: Entwurf, WP-E2E-A an Codex
<!-- ae34040 -->

Der Nutzer stellt das Smoke-Verdikt infrage: Der Testfehler-Vorsprung des Annihilators kam vom Oracle-$f$-Vorteil.
Geklärt wurde: Die schwache Form des Annihilators integriert in $x$ und beseitigt die Ableitungen von $f$, nicht die
Zeitableitung $\dot x$, die nötig ist, um $f$ aus $x(t)$ zu bekommen. Das stand im Leitdokument schon als
Engpass von Gate 2B. End-to-End braucht der Annihilator also eine Ableitungsschätzung wie SINDy, während W-SINDy sie
vermeidet. Neue Frage (Nutzer): ein fairer Vergleich rein aus denselben Trajektorien, berichtet werden R² ≥ 0,9,
Generalisierung und Strukturtreffer. Gewählt: beide Protokolle (ODEBench-Standard P1 und Extrapolation P2) und eine
gemeinsame Auswahl über den Validierungsfehler für alle drei Methoden. Beim Annihilator entfallen $\chi^2$-Test und
A1–A3, weil $\sigma$ bei geschätzten Ableitungen unbekannt und das Rauschen korreliert ist; das Risiko eines
v1-artigen Scheiterns war zu groß. Entwurf `docs/ODEBENCH_END2END.md`; §9 legt der Nutzer fest.

### ODEBench-Smoke-Test v2: Verdikt „beenden“ (Bedingung A)
<!-- 21b1c73 -->

Hauptlauf 01:27–03:49, 72 Records, `DONE`. `STRUCT_OK`: Annihilator rauschfrei 2/4 (3 und 21 `CORRECT`), bei 1 %
0/4. SINDy und W-SINDy 0/4 in beiden Fällen, weil die AICc-Auswahl dichte Modelle mit 6–9 Termen wählt (Schwäche
der Baseline-Spezifikation, offen benannt). Gompertz verfehlt der Annihilator schon rauschfrei ((1,3), `AMBIGUOUS`);
bei 1 % wählt er 3/5 stabil (2,0) (`WRONG`, Bootstrap ≈ 1). 19 landet auf Surrogaten mit konstanten Koeffizienten.
3 und 21 werden bei 1 % in 10/10 Fällen mit der richtigen Klasse gefunden, aber alle als `AMBIGUOUS` markiert
(A1/A3). Die Funktionsgüte von $\hat f$ ist gut, mit Oracle-$f$ aber kein Beleg. Verdikt nach v1 §9: **Idee #1
beenden (A)**. Übergabe: `docs/ODEBENCH_SMOKE_TEST_RESULT.md`.

### ODEBench-Smoke-Test v2: Pilot technisch sauber, Hauptlauf gestartet
<!-- f3faa77 -->

WP-OB-B abgenommen: Mit dem exakten Operator besteht der v3-Test auf allen vier Systemen bei 2000 gleichmäßigen
Punkten ($T \approx 10^{-6}$ bis $10^{-8}$, kritischer Wert ≈ 280). Pilot v2 ($\eta = 0$, Systeme 7 und 3) von 00:07
bis 01:27, 6 Records. Kosten Annihilator: System 3 mit 4 Klassen 23 min, System 7 mit 10 Klassen 81 min; SINDy etwa
2 s, W-SINDy etwa 20 s. f̂ und alle Trajektorien wurden ohne Fehlschlag gebildet. Der Hauptlauf startete wie vom
Nutzer gewünscht am 07.10. um 01:27 losgelöst (PID 13124, 6 Worker, `--detach-marker`, Log
`results_v2/main.{out,err}`). Erwartetes Ende 04:00–06:00.

## 2026-10-06

### ODEBench-Smoke-Test: v1-Pilot gescheitert (Aufbau), v2 eingefroren
<!-- 1615fc7, cf8400b, a438a2a -->

Der Pilot von v1 ($\eta = 0$, Systeme 7 und 3, etwa 3 h) ergab für den Annihilator `NONE` auf beiden Systemen, mit
allen 42 Klassen verworfen. Die Diagnose zeigt: Der exakte Referenzoperator wird auf den 1024 Trajektorienpunkten mit
$T \approx 5\cdot10^{14}$ verworfen, auf 2000 gleichmäßigen Punkten derselben Domäne besteht er mit
$T \approx 10^{-5}$. Die Trapezquadratur auf Trajektoriengittern mit Lücken passt nicht zum Boden $\tau$, der für
gleichmäßige Punkte kalibriert wurde. Das ist ein Aufbaufehler, kein Ergebnis. Zweiter Mangel: Ohne Rauschen wählt
die AICc-Auswahl alle 9 Terme, und das zählte als `STRUCT_OK`. Der Hauptlauf von v1 wurde nicht gestartet.

Der Nutzer wählte für v2 (`docs/ODEBENCH_SMOKE_TEST_v2.md`) 2000 gleichmäßige Punkte für Oracle-$f$ und
`STRUCT_OK` nur bei exakter Struktur. Codex setzt das in WP-OB-B um.

### ODEBench-Smoke-Test: Pipeline abgenommen, wartet auf Einfrieren
<!-- f177c8f -->

WP-OB-A wurde nicht abgenommen. Befunde:
- Die Baselines waren kein pysindy, liefen aber in den Records mit pysindy-Parametern; W-SINDy war identisch mit
  SINDy.
- Beide Trainingstrajektorien bekamen dasselbe Rauschen.
- $L \to \hat f$ scheiterte für 7 und 19 schon mit dem exakten Operator, weil über die Nullstelle des
  Leitkoeffizienten integriert wurde; die Plausibilitätsprüfung prüfte einen anderen Pfad.
- `TRUE_NOT_REF` war komponentenweise statt über $n_{\text{exact}}$ definiert.

WP-OB-A2 behebt alles. Selbst nachgeprüft: `Theta_` liegt in Originaleinheiten vor, und SINDy und W-SINDy finden
eine synthetische Logistik exakt. Plausibilität bestanden: Nachintegration ≤ $1{,}04\cdot10^{-5}$, die Spezifikation
wurde vor dem Einfrieren von $10^{-6}$ auf $10^{-4}$ geändert, weil die ODEBench-Speicherung selbst nur so genau
ist. Exakte Kette $L \to \hat f$ ≤ $1{,}8\cdot10^{-11}$ auf dem Produktivintervall. Referenzklassen: 3 (3,0),
7 (3,1), 19 (2,2), 21 (3,0).

Offengelegt: Codex' Feldlisten-Test erzeugt einen SINDy-Record auf System 3 bei $\eta = 0$ im Temp-Ordner, also
einen Fit auf Systemdaten vor dem Einfrieren. Die Kategorie wurde nicht angesehen; der Report nennt nur die gewählte
Schwelle 0,001.

### ODEBench-Smoke-Test: Entwurf, WP-OB-A an Codex
<!-- e8a1ba2 -->

Vor dem Abschluss will der Nutzer die Methode einmal end-to-end auf echten ODEBench-Systemen sehen. Entwurf
`docs/ODEBENCH_SMOKE_TEST.md`, noch nicht eingefroren. Gewählt (Nutzer): Systeme 7 Gompertz, 3 Logistik, 21 SIR und
19 Logistik mit Ernte, 5 Seeds bei 1 % mit Mehrheitsregel, nur Oracle-f (keine Variante B), pysindy 2.1 neu
eingefroren statt Paper-1-Einstellungen (Spurtrennung). 40/56/63 sind nicht skalar. Rauschkonvention von ODEBench
geprüft: multiplikativ $x(1+\xi)$ (ODEFormer-Paper). Die Test-Anfangsbedingungen liegen bewusst auch außerhalb des
Trainingsbereichs, weil im 1D-Fall jede innere Anfangsbedingung nur eine Zeitverschiebung eines Trainingsorbits ist.
Erwartung vorab: Gompertz entspricht F5, 19 entspricht F8.

### Reality-Check Stufe A: `STRONG_NEGATIVE`
<!-- 69923fc -->

Der Nutzer gab die Spezifikation mit zwei Änderungen frei: §8.1 ist eine Implementierungs- und
Spezifikationsprüfung mit Stopp, §9 enthält keine Zahl mehr (`084fcfc`). Pilot und Hauptlauf liefen auf dem Laptop,
400 Records, 17–276 Fits pro Realisierung.
- **BS:** 200 von 200 `TRUE_STRUCTURE` über F1–F10. Primär $P_{\text{true}} = 1{,}00$, $P_{\text{surr}} = 0{,}00$,
  Kontrollen 1,00. Beim gewählten $k$ ist immer genau eine Teilmenge akzeptiert. Fehler auf Domäne und Erweiterung
  ≈ $2\cdot10^{-4}$.
- **Annihilator gepaart** (dieselben Samples): N1 25/25 eindeutige Ausgaben falsch.
- **STLSQ** (nur berichtet) ist entartet: 14–23 Terme wegen der kollinearen Library, Extrapolation unbrauchbar.
  Keine Nachjustierung.

Lesart: Die Daten tragen die Struktur. Das Surrogatproblem kommt aus der Annihilator-Repräsentation und ihrer
Komplexitätsordnung. Vorbehalt: Die Library enthält die wahren Familien. **Folge nach §6: Idee #1 beenden.**

### Reality-Check Stufe A eingefroren, WP-RC-A an Codex
<!-- 64c295f -->

Vor dem Abschluss eine letzte Frage (Nutzer): Ist das Surrogatproblem außergewöhnlich stark, oder scheitert eine
direkte Sparse-Regression auf denselben $(x, f)$-Samples ähnlich? Spezifikation `docs/REALITY_CHECK_DIRECT_REGRESSION.md`:
Seeds 50000–50019 (gepaart mit der Diagnose), Library mit 23 festen Termen (enthält die wahren Familien, bewusst
günstig für die Baseline). Entscheidend ist Best-Subset mit der Annihilator-Suchregel (sparsestes Modell, das der
$\chi^2$-Test bei 1 % nicht verwirft). STLSQ wird nur berichtet. Obermengen zählen als `TRUE_PLUS`. Verdikt
`STRONG_NEGATIVE` bei $P_{\text{true}} \ge 0{,}70$ und $P_{\text{surr}} \le 0{,}20$ auf F4/F5/F8, sonst `OPEN`
(Stufe B nur mit eigener Spezifikation). Symbolic Regression entfällt (GP). Erwartung vorab notiert:
`STRONG_NEGATIVE`, weil $\log x$ in der Library ein Term ist, das Surrogat (3,0) aber drei Exponentialfunktionen mit
freien Raten bräuchte.

WP-RC-A abgenommen nach einer Nachbesserung (WP-RC-A2). Der Annihilator-Vergleich hatte N1 und I zusammengefasst
(118/415 statt 118/118). Der alte Test hatte das umgangen, weil er die Gruppen selbst vorfilterte. Prüfung auf
exakten Daten: F1–F10 alle `TRUE_STRUCTURE`, mit kleinstem $k$. 54 Tests grün. Gepaarte Annihilator-Zahlen
(Seeds 50000–50019): N1 25/25 eindeutige Ausgaben `WRONG`, 35 `AMBIGUOUS`; I 57 `CORRECT`, 3 `AMBIGUOUS`.
Pilot wartet auf die Freigabe der Spezifikation durch den Nutzer. <!-- eb77334 -->

### Diagnose AMBIGUOUS: Hauptlauf fertig, Verdikt negativ
<!-- 0c3feb2 -->

Orion-Job `annihilator-diag-amb` vollständig: 11/11 Pods `Completed`, keine Neustarts, 588 Records (5 × 54 +
6 × 53), mit Pilot 600, je Funktion 100. Eingesammelt nach RUNBOOK §6, `--merge --reps 100` und `--summarize`
lokal. Details und Lesart in `docs/DIAGNOSTIC_AMBIGUITY_RESULT.md`.

- **B1 = 1,000** (118 von 118 eindeutigen N1-Ausgaben `WRONG`, Schwelle < 0,20): **nicht erfüllt.**
- B2 = 0,607, B3 = 0,990, B4 = 0,597: erfüllt.
- F4: 99 `WRONG` mit (3,0), Bootstrap 1,0. F5: 100 `AMBIGUOUS`, nur über A1. F8: 81 `AMBIGUOUS` mit (3,0), 19 `WRONG`
  mit (2,0). F1, F2, F6: je 99 `CORRECT`.
- Die Fehlwahlen folgen fast exakt der Teststärke aus Anhang B: F8 (2,0) mit $eta = 0{,}80$ ergibt 20 % erwartet,
  19 % beobachtet; F4 (3,0) mit $eta = 0{,}14$ ergibt ≈ 86 % erwartet, 99 % beobachtet. Ob `AMBIGUOUS` oder
  `WRONG` herauskommt, hängt an der Nullraumdimension der gewählten falschen Klasse (A1), nicht an der
  Identifizierbarkeit. A2 erkennt stabile Fehlwahlen nicht.
- Pilot-Warnsignal 1 (stabil falsche Wahl bei F4) bestätigt. Warnsignal 2 (Referenz in I verworfen) nicht
  bestätigt: 3 von 300 = nominal 1 %, alle bei Seed 50000.

**Verdikt nach §5: negativ.** Kein `PRACTICAL_BENCHMARK_v1.md`, kein Hold-out-Set, kein größerer Benchmark, keine
Nachjustierung. Offene Entscheidung des Nutzers: Spur beenden (Empfehlung) oder grundsätzliche Neubewertung als neue
Idee. Hilfs-Pod gelöscht, Daten bleiben auf dem NFS.

## 2026-10-05

### Diagnose AMBIGUOUS: Hauptlauf auf Orion gestartet
<!-- 81f8773 Job/Runbook -->

WP-DIAG-AMB-b abgenommen: Teile, Merge, atomarer Nullraum-Cache, `run.log` ohne Zustand, echter Record als Fixture,
10 Tests grün. Orion ohne eigenes Image: `python:3.12-slim`, Wheels (numpy 2.2.6, scipy 1.13.1, sympy 1.13.1,
mpmath 1.3.0) offline vom NFS, Code per `git archive` aus `c71841f`. Probelauf im Hilfs-Pod bestanden. Der Nutzer
startete den Job am 05.10. um 15:15 (11 Pods, 588 Realisierungen, rund 32 h).

### Diagnose AMBIGUOUS: Pilot fertig, N = 100 auf Orion festgelegt, Pilot-Zustände
<!-- ba83120 Skript, a22804b §6 -->

Pilot 12:53–14:21, 12 Records, im Mittel 36 min pro Realisierung. Danach legte der Nutzer **vor** Ansicht der
Zustände fest: $N = 100$, Orion mit 11 Pods, rund 32 h. Offengelegt: Der Zustand von F2/50000 stand in `run.log`.
Pilot-Zustände (6 pro Gruppe, **nicht belastbar**):
- **N1:** 5 `AMBIGUOUS`, 1 `WRONG`. F4/50001 wählte (3,0) stabil, Bootstrap 1,0, ohne Warnung. F5 wählte zweimal
  (3,0) stabil und wurde nur durch A1 als `AMBIGUOUS` markiert.
- **I:** 3 `CORRECT`, 3 `AMBIGUOUS`. In allen drei `AMBIGUOUS`-Fällen verwarf der Test die Referenzklasse, und die
  Methode wählte eine Oberklasse mit wahrem Annihilator. Die Ambiguität war dabei jeweils angezeigt.
- Vorläufig: B1 und B3 nicht erfüllt, B2 und B4 erfüllt.

Auffällig: Die Referenzklasse wird in I in 3 von 6 Fällen verworfen, nominal sollte das in 1 % der Fälle passieren.
Das wird im Hauptlauf beobachtet, nicht jetzt untersucht.

### Diagnose AMBIGUOUS vs. WRONG eingefroren, WP-DIAG-AMB-a an Codex
<!-- ba4d7d8 -->

Der Nutzer entwarf `PRACTICAL_ANNIHILATOR_BENCHMARK.md`: die neue Frage, ob die Methode als Selective Prediction
taugt, also bei unzureichender Evidenz abstainiert statt falsch zu entscheiden. Vorher eine billige Diagnose:
Reagiert v3 in den N1-Fällen F4, F5 und F8 (breit, 1 %) mit `AMBIGUOUS` oder mit `WRONG`? Als Kontrollgruppe dienen
die I-Fälle F1, F2 und F6. Eingefrorene Regel mit B1–B4 (Nutzer) in `docs/DIAGNOSTIC_AMBIGUITY.md`. Erst Pilot mit
2 Realisierungen, dann $N$ und Laufort nach Kosten. Ab diesem Lauf sind F1–F10 Entwicklungsset. Kein Gate 2A v4.

### Gate 2A v3: Stufe K vollständig, Anhang A zusammengeführt
<!-- 9d20151 -->

Teil 6 (Clean K8 breit) endete um 11:15, alle 8 Teile mit Exit-Code 0, Zusammenführung automatisch
(`results/calibration/appendix_A.{json,md}`). Über 1.000 Realisierungen: K1 und K2 bestanden (Ablehnung 0,9 %,
$T$/dof 1,00), K6 nicht ($T$/dof 0,70, Spur-Verhältnis 3,58). Neu: Clean K7 und K8 breit sind `AMBIGUOUS` (A2)
statt `CORRECT`, beide mit richtiger Klasse. Ein weiterer K-c-4-Fehlschlag, das Verdikt bleibt gleich.
Ergebnisdokument, Nachtrag 2, aktualisiert.

### Gate 2A v3: Anhang A nicht bestanden, Anhang B (Diagnose) löst K6 aus
<!-- 4dd384b, 188b768 -->

Die Stufe K v3 (03:32 bis etwa 06:00, K8 breit lief länger) ergab:
- **bestanden:** K-a, K-b, K-c 1–3 für K1 und K2 (Test kalibriert, Bias ≤ 2e-4);
- **nicht bestanden:** K6 hat $T$/dof 0,68–0,70 und ein Spur-Verhältnis von 2,2–7,0; Clean K7 schmal ist `WRONG`.

Der Nutzer wählte Option A: Anhang B als Diagnose (WP-G2A3-c, 28 min). **Bei 1 % breit sind F4, F5, F8, F9 und F10
N1**, mit einer konkurrierenden Klasse konstanter Koeffizienten bei $\beta \approx \alpha$. **K6 würde auslösen**
(3 > 1). Bei 1 % unterscheiden die Daten polynomiale nicht von konstanten Koeffizienten. Identifizierbar bleiben nur
Operatoren erster Ordnung und der Sinus. Ergebnisdokument: `docs/GATE_2A_v3_STAGE_K_RESULT.md`.

### Gate 2A v3: zwei Implementierungsfehler behoben, Stufe K läuft
<!-- f2196ca WP-G2A3-a, 71be691 WP-G2A3-b -->

Nach der Freigabe (`140430a`) hat Codex v3 gebaut (WP-G2A3-a). Der erste Stufe-K-Lauf (01:16) wurde um 03:20 von
Claude abgebrochen: Bei K1 blieb L-BFGS in 10 von 12 Seeds bei 35° und $J \approx 290$ hängen, obwohl
$J(c^*) \approx 0.09$ ist. Ursache: Zielfunktion und Gradient normalisierten das Vorzeichen von $c$ intern. $J$ ist
gerade, der Gradient ungerade, also bekam L-BFGS einen falschen Gradienten. Das war ein reiner
Implementierungsfehler, Claudes Prototyp hatte ihn nicht. WP-G2A3-b hat ihn behoben, mit
Finite-Differenzen-Test bei negativem Maximum. K1, Seeds 2/10/18/26: 0,01–0,06°. Codex hat dabei `maxls` von
20 auf 40 gesetzt. Die Spezifikation legt diesen Wert nicht fest, keine Schwelle ist betroffen. Ausgaben des
Abbruchs unter `results/calibration/aborted_2026-10-05_sign_bug/`. Neustart von Stufe K um 03:32, losgelöst
von der Werkzeugumgebung, ohne Zeitgrenze (Nutzer).

Aus dem abgebrochenen Lauf, unabhängig vom Fehler: Gegenüber v2 unverändert sind K-a ($\ell_{\max} = 4$),
K-b ($\tau = 3.4\cdot10^{-7}$) und die ex-ante-Klassen (K3/K4 breit N1, K5/K7 breit N2). Die Clean-Suche fand K2
und K6 breit `CORRECT`. Ein Teil braucht etwa 1 h für K-a/K-b/ex-ante, eine Clean-Zelle mit Bootstrap 40–50 min.

### Gate 2A v2: Stufe K scheitert an K-c, Ursache ist die FNS-Iteration; v3 entworfen

Orakel v2 (100 Stellen, 7 min mit 8 Workern nach dem Airy-Fix WP-G2A2-c):
- Das F10-Artefakt ist verschwunden. Die einzigen Abweichungen zu v1 sind genau die drei bekannten Einträge.
- Alle 32 Referenzklassen stimmen, $n_{\text{exact}} = 1$.
- **Neue** Artefakte bei K7/K8 schmal in hohen Klassen.
- Die Verifikation der v2-Implementierung rechnet in float. Deshalb scheitern F10 und K4 formal.

Stufe K v2 (N = 2000, 1.000 Realisierungen, 8 Teile, Teile 1–7 je ~1 h). **Teil 0 mit der Clean-Suche wurde
nach 2 h vom Zeitlimit der Werkzeugumgebung beendet, ohne Ausgabe.** Es gibt keinen zusammengeführten Anhang A von
v2. Der K-c-Befund steht in den Teildateien 1–7. Die Teildateien, der Orakel-Cache und die Orakel-Abnahme sind
committet. Teil 0 wird nicht nachgerechnet, weil v2 abgelöst ist:
- **K-a:** $\ell_{\max} = 4$, max. Fehler $8\cdot10^{-10}$.
- **K-b:** $\tau = 3.4\cdot10^{-7}$ (K8).
- **Ex-ante, breit, 1 %:** K1, K2, K6, K8 I; **K3 und K4 N1** (ein Operator (4,0) ist datenkonsistent, Güte 0,27
  bzw. 0,01); K5 und K7 N2.
- **K-c (Teil 1, 125 Seeds):** K2 besteht (Ablehnung 1,6 %, $T$/dof 1,01, Spur-Verhältnis 0,95). **K1 und K6
  scheitern total:** 100 % Ablehnung, $\hat c$ bis zu 90° daneben.

Diagnose auf dem Kalibrier-Set: FNS nimmt den betragskleinsten Eigenwert von $X$ und landet auf Punkten mit
verschwindendem Gradienten, die keine Minima sind (K1: $J = 548$ gegen $J(c^*) = 0.099$). L-BFGS auf der Sphäre vom
SVD-Start trifft K1, K2 und K6 auf 0,02–4,4°. Ein Multistart über alle Singulärvektoren bringt nichts. Bei K5 und K8
gibt es Punkte fern von $c^*$ mit **kleinerem** $J$ als $c^*$: Ab Ordnung 4 sind die Koeffizienten bei 1 % nicht
identifizierbar. Das ist die w^{-k}-Grenze, jetzt direkt gemessen.

`docs/GATE_2A_v3.md` (Entwurf): L-BFGS statt FNS, $n_{\text{exact}}$ domänenunabhängig (Identitätssatz), Verifikation
in echter Präzision. Sonst bleibt alles wie in v2. Die Erwartung ist vorab notiert: Bei F4 und F5 droht K6.

## 2026-10-04

### WP-G2A2-a `blocked`, Claudes Code-Prüfung, Folgeauftrag WP-G2A2-b
<!-- 240f041, task 04c9c45 -->

Codex hat das v2-Gerüst gebaut. Zwischendurch unterbrach ein Nutzungslimit, Neustart gegen 15:30. 8/8 Tests v2,
8/8 v1. Orakel und Stufe K liefen nicht voll. Claudes Prüfung:
- **Korrekt:** stabile Leibniz-Auswertung, FNS/AML mit Gradiententest, Kovarianz erster Ordnung, Test, A1–A3.
- **Defekt:** K-c wertet keine Schwelle aus, und das Gesamtverdikt war „reps == 1000“. Das hätte ein falsches
  Bestanden in Anhang A geschrieben. Ambige Ergebnisse in der richtigen Klasse wurden als `WRONG` gezählt.
  `--part` überschreibt Anhang A. Dazu kommen aus v1 kopierte, stale Abnahmeskripte und Ergebnisse.
- **Akzeptierte Abweichung:** K-a vergleicht $Ac^*$ mit null statt mit einem mpmath-Integral. Das ist exakt
  gleichwertig, weil $\int\varphi\,L^*[f] = 0$ ist und die Randterme verschwinden.
- **Laufzeit (gemessen, Laptop, kein Beleg):** Tensoraufbau 13/27/59 s für $\ell_{\max}$ = 3/4/5, bisher pro
  Realisierung neu, obwohl der Tensor für alle Funktionen identisch ist ($z \in [-1,1]$). Eine volle Suche mit 5
  Bootstrap-Replikaten dauert 27 s. Mit 50 Replikaten wären es grob 4–5 min pro Realisierung, der Gate-Hauptlauf
  also in der Größenordnung eines Tages auf einem Kern. Damit ist er kein Laptop-Lauf unter 1 h, solange die
  Optimierung das nicht deutlich drückt. Vor dem Gate-Lauf ist eine Laufort-Entscheidung nötig.

WP-G2A2-b: Verdikt, Ergebniszustände, Merge der Teile, verhaltensneutrale Wiederverwendung des Tensors mit
Bitgleichheitsnachweis, parallelisiertes Orakel, Aufräumen. Danach Orakel und Stufe K ausführen.

### Gate 2A v2 nach externem Review ergänzt, vor jedem Lauf; Codex neu gestartet
<!-- 50bdf57 -->

Das Review (Nutzer, 04.10.) hält v2 für überzeugend und nicht für Schönrechnen. Vor dem Freeze verlangte es drei
Punkte, alle umgesetzt:
1. FNS heißt FNS/AML (heteroskedastischer Errors-in-Variables-Schätzer). Die Kovarianz ist eine asymptotische
   Näherung erster Ordnung, nicht exakt.
2. A3 ist als projektive Winkelunsicherheit $\theta_{\hat c}$ definiert: Repräsentant $\|c\|_2 = 1$ zur Basis
   $z^jD_z^k$, Tangentialraum, basisabhängig und deshalb festgeschrieben. 0,1 rad ist eine operative Heuristik.
3. Das Kalibrier-Set reicht jetzt bis Ordnung 6: K7 $= 1+\sin x+\cos 2x$ (5,0) und K8 $= \sin x+\sin 2x+\sin 3x$ (6,0),
   vorab von Claude mit 50 Stellen bestätigt (beide Domänen, Nullraumdimension 1). Beide dienen nur der numerischen
   Infrastruktur.

Dazu: „v2 ist strenger“ abgeschwächt zu „in mehreren Richtungen strengere Kill-Kriterien“, und für eine spätere
Erfolgsbehauptung ist ein neues, versiegeltes Funktions-Hold-out-Set nötig. Die laufende Codex-Sitzung (WP-G2A2-a)
wurde dafür angehalten, Stufe K war noch nicht gerechnet. Die Kindprozess-Geistersitzung wurde gezielt beendet.
Neustart mit ergänztem Auftrag, der auf dem angefangenen Code aufsetzt.

### Gate 2A v2 eingefroren, WP-G2A2-a an Codex; zweite Ursache des Matrixfehlers gefunden
<!-- 7609529 -->

Der Nutzer hat v2 abgenommen („Setz das um“, E5–E9). Vor dem Einfrieren hat Claude die Matrixgenauigkeit auf **K5**
($x + \sin x$, Ordnung 4, Kalibrier-Set, also nicht F9) nachgemessen. Relatives Residuum $\|Ac^*\|/\|A\|$ bei
$N$ = 1.000 → 8.000, Blockbreite 0,25:
- v1-Monomdarstellung, $q = 8$: $3\cdot10^{-4}$ → $7\cdot10^{-6}$; mit $q = 14$ **schlechter**, $5\cdot10^{-3}$ → $3\cdot10^{-3}$
  und flach in $N$, also Rundung;
- stabile Leibniz-Auswertung, $q = 8$: $3\cdot10^{-4}$ → $7\cdot10^{-9}$, etwa 5. Ordnung, also Quadratur;
- stabil, $q = 14$: $2\cdot10^{-10}$ → $8\cdot10^{-11}$; stabil, $q = 14$ bei Trägerbreite 1: $\sim10^{-13}$.

Zwei Defekte haben sich also überlagert: die Rundung der Monomdarstellung vom Grad ~37 und die Quadratur bei geringer
Randglattheit. Der Entwurf hatte nur die Quadratur erkannt. Vor dem Einfrieren ergänzt: die stabile Auswertung (§5)
und die K-a-Schwelle $10^{-8}$ statt $10^{-10}$ (sechs Größenordnungen unter 1 % Rauschen, Clean deckt $\tau$ ab).
Detaillierte Begründung aller Änderungen: `docs/GATE_2A_v2_RATIONALE.md`. Auftrag WP-G2A2-a: Implementierung,
Orakel mit 100 Stellen, Stufe K bis Anhang A, dann Stopp. Kein Kontakt mit F1–F10 außer dem Orakel.

### Gate 2A v2 entworfen (Nutzer: Option (a))
<!-- 5f6ac25 -->

`docs/GATE_2A_v2.md`, v1 bleibt eingefroren. Jede Änderung folgt aus einem Befund der v1-Abnahme. Keine wird an
F1–F10 eingestellt:
- $q = 14$, damit jeder Integrand global $C^7$ ist (in v1 war er bei $k = 6$ nur $C^1$). Das passt zur beobachteten
  Konvergenz zweiter Ordnung bei F9.
- ML-Schätzer (FNS): Er minimiert genau die Teststatistik, ein freier Parameter entfällt.
- Multiskalige Testfunktionen. Fit/Val werden über verschränkte Samples getrennt statt über Blöcke, und die
  ML-Gewichtung entscheidet über die Breite.
- A3: `AMBIGUOUS`, wenn die Linearisierung ungültig ist.
- Ex-ante-Identifizierbarkeit I/N1/N2 aus exakten Daten, vor dem Lauf eingefroren.
- Orakel mit 100 Stellen.

$\ell_{\max}$ und $\tau$ werden nur auf dem disjunkten Kalibrier-Set K1–K6 festgelegt, über Genauigkeitskriterien
statt über Suchergebnisse. Die statistischen Prüfungen laufen nur dort. Neue Kills: K5 (breite Operatoren ab
Ordnung 2 bei 1 % mehrheitlich nicht `CORRECT`) und K6 (das Messdesign selbst kann moderate Operatoren nicht
unterscheiden).

Einordnung der Idee nach v1: Der Kern (minimaler Annihilator, statistisch begründete Entscheidung inklusive „die
Daten reichen nicht“) ist unberührt, der Statistikteil ist durch F2 sogar bestätigt. Abgeschwächt ist die
Erwartung, dass die schwache Form das Rauschproblem *qualitativ* löst. Die Rauschverstärkung $\sim w^{-k}$ bleibt
ein Bias-Varianz-Konflikt. Der Vorteil gegenüber differenzierenden Methoden kann nur noch quantitativ sein.

### Gate 2A: Abnahme `blocked` an F4/F9. Die eingefrorene Spezifikation hat drei Schwächen, der Gate-Lauf ist nicht gestartet
<!-- 9d6a4d0 (Implementierung + Abnahme-JSONs) -->

Die Implementierung hat drei Codex-Runden gebraucht (WP-G2A, -b, -c), das Orakel mit 60 Stellen hat Claude lokal
gebaut (9 min). Abnahme: Orakel (alle 20 Referenzklassen, F1–F9 symbolisch exakt, F10 auf 1e-58), Transfer
(Winkel 0) und Determinismus (1 gegen 4 Worker bitgleich) bestanden. Bei F10 schmal ist in (4,6), (5,6) und (6,6)
die Nullraumdimension um 1 zu hoch, ein Präzisionsartefakt. $n_{\text{exact}} > 0$ ist überall gleich.
**Nicht bestanden:** Weak-gegen-stark und Kovarianz-Monte-Carlo für F4 ($\log x$, (2,1)) und F9 ($x^2+e^x$,
(4,0)). F2 ($e^{1.5x}$, (1,0)) besteht exakt: Ablehnungsrate 0,008, $T$/dof 1,00, Spur-Verhältnis 0,99. Ohne den
$\Sigma_{\hat c}$-Term läge die Ablehnungsrate bei 0,30, der Term ist also nötig.

Diagnose (Claude, Scratchpad):
- **Genauigkeit der Weak-Matrix.** Relative Annihilation $\|Ac^*\|/\|A\|$ für $N$ = 1.000/2.000/4.000/8.000:
  F2 $3.6\cdot10^{-10}$ → $1.9\cdot10^{-10}$ (flach, Rundungsboden der Monom-Polynome), F4 $1.9\cdot10^{-8}$ →
  $6.6\cdot10^{-9}$, **F9 $3.0\cdot10^{-3}$ → $6.8\cdot10^{-5}$**. Die Genauigkeit fällt mit der Ableitungsordnung
  steil ab. Folge: Der Clean-Boden $\sigma_{\text{floor}} = 10^{-8}$ liegt unter dem numerischen Fehler, F2 clean
  wird `AMBIGUOUS` statt `CORRECT`. Clean-Ergebnisse wären Numerik-Artefakte.
- **Schätzer-Bias.** Bei 1 % ist der kleinste Singulärvektor von $A_{\text{fit}}$ für F4 um das **47-Fache**
  seiner Streuung verschoben (Total Least Squares bei spaltenweise heteroskedastischem Rauschen). Der
  rauschgewichtete Eigenwertansatz (GTLS) senkt das auf das 2,3-Fache, die Streuung steigt dabei auf 0,5.
- **Identifizierbarkeit.** F9 bei 1 %: $\hat c$ praktisch zufällig (Bias ≈ Streuung ≈ 1). Schon clean ist der
  Abstand $\sigma_2/\sigma_{\min}$ nur 22. Die Erste-Ordnung-Kovarianz unterschätzt die Streuung um Faktor ~15.
  Ursache ist die Rauschverstärkung schmaler Testfunktionen (Blockbreite 0,25 in $z$) bei Ableitungsordnung 4.

Einordnung: Das sind Schwächen des Testaufbaus (Matrixgenauigkeit, Schätzer, Testfunktionsbreite). Über die
Idee sagen sie noch nichts. Die Methode scheitert so aber schon bei 1 % an Operatoren der Ordnung ≥ 2.
Hochrechnung der Laufzeit: Hauptlauf ~49 min mit 8 Workern, Raster ~4,6 h. Entscheidung beim Nutzer.

### Idee #1 (Annihilator-Discovery): eigener Branch, Gate 2A eingefroren
<!-- 4d15c29 (IDEA_01, Nutzer), f706b25 (GATE_2A eingefroren) -->

Branch `annihilator-discovery`, Worktree `..\EvoODE-next`. Der Name `evogrow-next` wurde verworfen, weil die
Methode keine Weiterentwicklung von EvoGrow ist. Leitdokument `docs/IDEA_01_ANNIHILATOR_DISCOVERY.md`, das
`docs/idea_structural_diagnostics.md` ablöst. Kill-Test `docs/GATE_2A.md`, vom Nutzer abgenommen (E1–E4).

**Exakte Vorab-Kontrolle der Referenzklassen** (Claude, Scratchpad, mpmath mit 60 Stellen, 120 Punkte, alle
42 Klassen bis (6,6), etwa 4 min). Unter $C = (r+1)(d+1)$ mit Tie-Break $r$, dann $d$:
- $x^2$ (1,1), $e^{1.5x}$ (1,0), $x^{1.5}$ (1,1), $\log x$ (2,1), $x\log x$ (3,1) mit $C = 8$, also nicht
  $(xD-1)^2$ mit $C = 9$;
- $e^{-x^2}$ (1,1), $\sin(2x+\tfrac12)$ (2,0), $x/(2+x)$ (1,2), $x^2+e^x$ (4,0) mit $C = 5$;
- $\sin x + e^{-x^2}$ (5,1) mit $C = 12$.

In jeder Referenzklasse hat der Nullraum Dimension 1. **Befund, der die Spezifikation geformt hat:** Höhere
Klassen enthalten fast immer weitere wahre, nicht-äquivalente Annihilatoren, für $x^2$ und $x/(2+x)$ sogar
bei gleichem $C$. „Eine zweite Klasse besteht auch“ kann deshalb kein Ambiguitätskriterium sein. Es wäre
schon auf exakten Daten wahr. `AMBIGUOUS` entsteht nur noch über A1 (mehrdimensionaler Nullraum in der
gewählten Klasse) und A2 (instabile Auswahl im Bootstrap). Dazu kommen die Zustände `TRUE_NOT_REF` (wahrer,
nicht minimaler Annihilator, weder `CORRECT` noch `WRONG`) und `NONE`.

---


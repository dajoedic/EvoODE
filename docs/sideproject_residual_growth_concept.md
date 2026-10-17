# Side-Projekt: Residualgesteuertes Strukturwachstum für EvoGrow

**Status:** Ideenskizze zur kritischen Diskussion – **keine** beschlossene Methodenversion und **kein** Implementierungsauftrag  
**Datum:** 17.10.2026  
**Ziel dieser Übergabe:** Claude soll das Konzept verstehen, kritisch prüfen, offene Punkte benennen und gezielte Rückfragen stellen. Erst danach wird entschieden, ob ein kleines Diagnoseexperiment sinnvoll ist.

---

## 1. Ausgangspunkt: Was wollen wir eigentlich?

Wir möchten aus beobachteten Trajektorien \(x(t)\) die **richtige, interpretierbare Struktur** eines autonomen ODE-Systems

\[
\dot x(t)=f(x(t))=\sum_{j\in S^*}c_j\,\theta_j(x(t))
\]

identifizieren. Nicht bloß eine Gleichung, die eine einzelne Trainingskurve gut reproduziert.

Die ursprüngliche Idee von **EvoGrow** bleibt ausdrücklich erhalten:

- Mit einer **kleinen Zahl an Termen** anfangen, statt sofort alle möglichen Terme gleichzeitig zu verwenden.
- Schrittweise neue Terme ergänzen; die Struktur wächst nach Bedarf.
- Am Ende eine kleine, strukturell richtige Gleichung mit guter Generalisierung erhalten.

**Das offene Problem ist der Weg:** Wie entscheidet ein solcher Algorithmus, *welche* Ergänzung ihn in Richtung des richtigen Mechanismus bringt, wenn unvollständige Gleichungen irreführende Gütewerte haben?

Unsere neue Arbeitshypothese: Der **Residualfehler** des aktuellen Modells könnte Informationen darüber enthalten, *welche Terme fehlen*. Eine Weak-SINDy-artige, ableitungsfreie Auswertung könnte diese Information als **Wachstumshinweis** nutzen – nicht zwingend als endgültigen Strukturentscheid.

**Wichtig:** Das ist zunächst eine zu prüfende Hypothese, keine bereits nachgewiesene Lösung.

## 2. Was wir über EvoGrow schon wissen

Grundlage ist das bestehende Diskussionspapier `diskussion_warum_scheitert_die_suche.md` (Stand 17.10.2026). Für Details bitte dieses Papier sowie `CLAUDE.md` und `DIARY.md` im Repository lesen. Hier die für das Side-Projekt relevanten Punkte:

- **Benchmark:** ODEBench, 63 Systeme in Dimension 1–4; 30 exakt mit der verwendeten Bibliothek darstellbar.
- **Bibliothek:** `1, u_i, u_i², u_i·u_j, u_i³, sin(u_i), cos(u_i)`.
- **EvoGrow:** Population von Kandidaten; bislang nur **Hinzufügen** von Termen, kein Entfernen. Höhere Stufen werden später freigeschaltet.
- **Fit:** BFGS über MSE zwischen simulierter und beobachteter Trajektorie, höchstens drei Startpunkte pro Kandidat (weitere nach Fehlschlag).
- **Selektion:** `Objective = MSE + λ · Anzahl Parameter`, derzeit `λ = 1e-3` absolut.
- **Datenaufteilung:** Pro System zwei Anfangsbedingungen (IC). Eine Trainingstrajektorie, die andere **ausschließlich Test/Generalisierung**.

**Eingefrorene empirische Befunde (nicht neu berechnet):**

| Befund | Beobachtung |
|---|---|
| EvoGrow, alle Dimensionen | Rekonstruktion 88,6 %, Generalisierung 41,4 %, exakte Struktur geprunt 29,4 %, roh 13,3 % |
| EvoGrow, Dimension 2 | Rekonstruktion 96,4 %, Generalisierung 29,8 % |
| Weak-SINDy deg3, alle Dimensionen | Rekonstruktion 89,2 %, Generalisierung 61,9 %, Struktur 65,0 % |
| Fit der **wahren** Struktur auf Dimension 2 | Mit 1/3/10 BFGS-Starts erreichen 25 % / 33 % / 65 % der Zellen \(R^2>0{,}9\) |
| Orakel-Prior für wahre Einzelterme, Dimension 2 | Auf 13 nachweislich fittbaren Zellen steigt die geprunte Strukturtrefferzahl nur von 3 auf 5; vorab definierter Test nicht bestanden (p = 0,25) |
| Nachbarschaft der wahren Struktur | Unter 2.479 gleich großen Ein-Term-Vertauschungen (36 Zellen, Dimension 2/3) gewinnt keine gegen eine gut gefittete Wahrheit |

**Interpretation, nicht gesichertes Resultat:** Mindestens zwei Probleme können zusammenwirken:

1. **Suchproblem (A):** Die richtige Termkombination wird gar nicht erreicht.
2. **Fitproblem (B):** Die richtige Kombination wird erreicht, aber der simulationbasierte Optimierer bewertet sie wegen eines schlechten Fits zu niedrig.

Weitere mögliche Mechanismen sind Komplexitätsstrafe, Skalenabhängigkeit und echte Nichtidentifizierbarkeit auf einer Trajektorie (Klassen C/D/E des Diskussionspapiers). Die Klassifikation ist noch nicht empirisch abgeschlossen. Ein Residual-Verfahren könnte A adressieren und durch einen linearen schwachen Fit Teile von B umgehen; beides ist **noch nicht gezeigt**.

## 3. Kernproblem: Ein richtiger Einzelterm muss nicht gut aussehen

Beispiel:

\[
\dot x=2x-0.5x^3.
\]

Ein Kandidat mit nur \(ax\) ist **teilweise strukturell richtig**, kann die Daten aber schlecht erklären. Eine *falsche* kleine Struktur kann auf der einen beobachteten Trajektorie besser aussehen. Wird die erste Erweiterung nur anhand der aktuellen Simulationsfitness gewählt, bevorzugen wir möglicherweise den falschen Weg. Weil EvoGrow nur Terme hinzufügt, bleiben solche Fehlentscheidungen lange erhalten.

Dabei gilt präzise:

- Wenn wir eine Struktur um einen Term erweitern und **global optimal ohne Komplexitätsstrafe** fitten könnten, kann der bestmögliche Trainingsfehler nicht steigen (der neue Koeffizient darf null sein).
- Die tatsächlich erreichte **BFGS-Fitness** kann sich trotzdem verschlechtern; die **komplexitätsbestrafte** Fitness erst recht.
- Die Fitness einer **unvollständigen** Struktur ist deshalb kein zuverlässiger Hinweis auf die strukturelle Richtigkeit ihrer Bestandteile.

**Forschungsfrage:** Kann eine Betrachtung des Fehlers gezielter sagen, *in welche Richtung* die aktuelle Struktur wachsen sollte, als ihr momentaner Simulations-MSE?

## 4. Idee: Den Fehler der aktuellen Gleichung auf fehlende Basisfunktionen untersuchen

### 4.1 Intuition (mit Ableitungen nur zur Erklärung)

Für eine aktuelle Struktur \(S\) mit Koeffizienten \(\hat c\):

\[
\hat f_S(x)=\sum_{j\in S}\hat c_j\theta_j(x).
\]

Formal wäre der **Dynamik-Residualfehler** entlang der gemessenen Trainingskurve:

\[
r(t)=\dot x_{\mathrm{Daten}}(t)-\hat f_S(x_{\mathrm{Daten}}(t)).
\]

Im Beispiel, wenn \(\hat f_S(x)=1.4x\) ist:

\[
r(t)=0.6x(t)-0.5x(t)^3.
\]

Dieser Fehler enthält potenziell einen Hinweis auf den fehlenden kubischen Term, **aber auch** auf einen falsch geschätzten Koeffizienten des bereits vorhandenen linearen Terms.

**Wichtige Konsequenz:** Wir dürfen „fehlender Term“ und „vorhandener Term schlecht gefittet“ nicht verwechseln.

### 4.2 Vorgeschlagener Minimalansatz: schwache Form statt numerischer Ableitung

Wir möchten gerade bei Rauschen nicht zwangsläufig \(\dot x(t)\) punktweise schätzen. Für eine Zustandskomponente und Testfunktion \(\varphi_k\), die an den Fensterrändern verschwindet, gilt:

\[
\underbrace{-\int \varphi'_k(t)x(t)\,dt}_{b_k}
=\sum_{j\in S} c_j\underbrace{\int\varphi_k(t)\theta_j(x(t))\,dt}_{A_{kj}}.
\]

Daraus entsteht für eine Gleichungskomponente ein lineares Problem:

\[
b\approx A_Sc_S,\qquad r_S=b-A_S\hat c_S.
\]

**Erste Diagnosevariante:** Bestehende Terme \(S\) zunächst *innerhalb der schwachen Form* neu fitten; dann die verbleibenden Kandidaten \(j\notin S\) danach bewerten, inwieweit sie \(r_S\) erklären. Das verhindert, dass bloße Fehler der vorhandenen Koeffizienten als Bedarf für neue Terme missverstanden werden.

Zwei naheliegende, einfache Varianten für einen späteren Vergleich:

1. **Einzelterm-Screening:** Für jeden erlaubten neuen Term \(j\) prüfen, wie stark sich der schwache Residualfehler nach Ergänzung von \(j\) und gemeinsamem linearen Refit von \(S\cup\{j\}\) reduziert.
2. **Paar-Screening nur bei Bedarf:** Für kleine Paare \(\{j,k\}\) die gemeinsame Verbesserung prüfen, wenn einzelne Erweiterungen keinen aussagekräftigen Hinweis geben.

Dabei müssen Spaltennormierung, fast kollineare Terme, Freiheitsgrade/Modellgröße und die Abhängigkeit von Testfunktionen/Fenstern berücksichtigt werden. Bloße rohe Korrelationen sind womöglich irreführend. Ein mathematisch äquivalenter Blick auf Einzelterm-Screening ist die Projektion eines Kandidatenterms auf den zu \(A_S\) orthogonalen Residualraum – unter Beachtung von Rangmangel und numerischer Stabilität.

**Entscheidend:** Der schwache Residualfehler ist **nicht** dasselbe wie der Fehler zwischen integrierter Modelltrajektorie und Beobachtung. Die beiden Größen dürfen im Experiment nicht durcheinandergeraten.

### 4.3 Was wir *nicht* vorschlagen

- Nicht bereits jetzt ein neues großes EvoGrow-System entwickeln.
- Nicht sofort eine weitere umfangreiche Phase-C-Rechnung starten.
- Nicht Weak-SINDy einfach auf der gesamten Basis ausführen und das Ergebnis als „EvoGrow-Wachstum“ verkaufen.
- Nicht die **wahre Struktur** als Eingabe für den späteren Algorithmus benutzen. Sie ist nur für die **Diagnose/Erfolgsmessung** im Benchmark erlaubt.
- Nicht automatisch aus einer guten Residualrangfolge auf Generalisierung oder identifizierten Mechanismus schließen.

## 5. Zuerst ein kleines Experiment – unabhängig von EvoGrow

**Primäres Ziel:** Prüfen, ob das Residualsignal die **wirklich fehlenden Terme** in kleinen, unvollständigen Modellen überzufällig und zuverlässig nach oben rankt.

Das ist absichtlich *noch keine* Integration in die evolutionäre Suche.

### 5.1 Versuchsaufbau (Vorschlag, mit Claude zu präzisieren)

1. **Systeme:** Kleine Auswahl exakt darstellbarer ODEBench-Systeme aus Dimension 1 und 2. Zunächst bestehende Daten verwenden. Keine Änderung der eingefrorenen Phase-C-Ergebnisse.
2. **Partielle Strukturen erzeugen:** Aus bekannten wahren Strukturen einzelne Terme entfernen (kontrollierter Positivfall). Zusätzlich ausgewählte **falsche** Teilstrukturen betrachten (realistischer Fall), idealerweise auch dokumentierte EvoGrow-Kandidaten, *soweit tatsächlich verfügbar*. Keine unbekannten Zwischenstrukturen aus bloßen Heartbeats erfinden.
3. **Residual bilden:** Schwache Bibliotheksmatrix auf **nur der Trainings-IC** erzeugen; vorhandene Terme schwach neu fitten, danach verbleibenden Residualfehler berechnen.
4. **Vorschläge ranken:** Einzelterm-Screening mit gemeinsamem linearen Refit. Kontrolliert prüfen, ob der tatsächlich fehlende wahre Term unter den besten Vorschlägen liegt.
5. **Baselines:** Zufallsauswahl sowie eine einfache residualbasierte Forward Selection / Matching-Pursuit-Variante; optional direkte Weak-SINDy-Strukturfindung als Referenz. Gerade dieser Vergleich verhindert, dass wir ein etabliertes Standardverfahren unnötig kompliziert nachbauen.
6. **Robustheit:** Wenn ein Signal sichtbar ist, über mehrere Systeme, unterschiedliche partielle Startstrukturen und vorhandene Noise-/Sampling-Bedingungen wiederholen. Konditionszahlen bzw. Rangmangel protokollieren.
7. **Paar-Erweiterungen:** **Erst** wenn einzelne Vorschläge systematisch versagen, prüfen, ob kleine Termpaare die fehlenden Beiträge besser sichtbar machen.

### 5.2 Erfolgsmessung

**Für das kleine Screening-Experiment (primär):**

- **Recall@1 / Recall@3:** Liegt mindestens ein tatsächlich fehlender wahrer Term unter den ersten 1 bzw. 3 Vorschlägen? (Bei mehreren fehlenden Termen zusätzlich vollständigen Recall und mittlere Rangposition auswerten.)
- **Verbesserung gegenüber Baselines:** Ist das Ranking besser als zufällige bzw. einfache residualgesteuerte Auswahl? Wie groß ist der Effekt – pro System, nicht nur aggregiert?
- **Stabilität:** Funktioniert das bei unterschiedlichen Teilstrukturen, bei Rauschen und bei kollinearen Basisfunktionen?
- **Fehlermodi:** Wann tauchen hauptsächlich bereits vorhandene Termrichtungen, Ersatzterme oder nicht unterscheidbare Terme auf?

**Später (nicht im ersten Screening als Erfolgsbeweis ausgeben):** Exakter struktureller Support, roh/geprunt, Trainingstrajektorie und Generalisierung auf zweite IC nach vollständiger Simulation.

Die **zweite IC bleibt unangetasteter Test** und wird nicht zur Rangsteuerung, Hyperparameterwahl oder Auswahl günstiger Fälle verwendet.

### 5.3 Was wäre ein negatives Ergebnis?

- Der Residualhinweis liegt nur auf dem Niveau einer simplen Forward Selection oder ist instabil.
- Die richtigen fehlenden Terme sind entlang einer einzelnen Trajektorie zu stark kollinear mit falschen Alternativen.
- Die Methode funktioniert nur für fast richtige Teilstrukturen, aber nicht nach frühen Fehlentscheidungen von EvoGrow.
- Ein linearer Refit erklärt den Fehler bereits; das bisherige Problem liegt wesentlich beim BFGS-Fit und nicht in der Auswahl eines neuen Terms.

Dann **kein komplexes Tuning**, nur um diese Idee zu retten. Ein negatives Ergebnis grenzt die Ursache des Problems ein.

## 6. Wichtige Denkfallen und wissenschaftliche Grenzen

1. **Conditionalität:** Ein fehlender wahrer Term kann im Residual schlecht sichtbar sein, wenn seine Wirkung von einem falschen Term entlang genau dieser Trajektorie approximiert wird.
2. **Kombinatorik:** Zwei Terme können gemeinsam notwendig sein, ohne dass jeder einzeln eine überzeugende Verbesserung liefert. Ob und wie oft das *in unseren Daten* auftritt, ist offen.
3. **Parameterfehler ≠ Strukturfehler:** Ohne kontrollierten Refit vorhandener Terme ranken wir womöglich nur Koeffizientenfehler.
4. **Schwacher Fit ≠ Simulation:** Ein sehr kleiner Fehler in der schwachen Regression garantiert weder eine stabile ODE noch gute Simulation noch Generalisierung.
5. **Selektionsbias:** Die wahren Terme dürfen nur zur Bewertung synthetischer Diagnosefälle verwendet werden, niemals zur Konstruktion der Vorschlagsregel.
6. **Bibliotheksunterschied:** Weak-SINDy und EvoGrow nutzen laut bisherigem Befund nicht vollständig identische Bibliotheken/Schwellen. Für faire Aussagen Vergleichsbedingungen sauber dokumentieren.
7. **Neuheit:** Residualbasierte Forward Selection, Matching Pursuit und sparse/weak-form Regression sind bekannte Ideen. Eine Kombination allein ist **kein** Neuheitsnachweis. Literaturabgleich ist später erforderlich, bevor ein Paper-Anspruch formuliert wird.

## 7. Ausblick: Was könnte daraus für EvoGrow werden?

**Nur wenn das erste Experiment ein robustes, relevantes Signal zeigt.**

Ein späterer, möglichst einfacher EvoGrow-Zyklus könnte so aussehen:

1. Mit kleiner Kandidatenstruktur \(S\) beginnen.
2. Auf der gemessenen **Trainingstrajektorie** den schwachen Residualfehler unter kontrolliertem Refit der bereits gewählten Terme bestimmen.
3. Daraus eine **kleine Vorschlagsliste** fehlender Terme (z. B. Top-k) ableiten, gegebenenfalls mit einer begrenzten Paaroption.
4. Kandidaten um diese Terme erweitern; einen Anteil ungelenkter Vorschläge erhalten, um nicht früh in einem falschen Ranking gefangen zu sein.
5. Erweiterungen wie bisher mit Simulation und struktureller Komplexität bewerten – gegebenenfalls später mit einer besseren Koeffizienteninitialisierung aus dem schwachen Fit.
6. Nur bei nachgewiesenem Bedarf weitere Operatoren (Ersetzen/Entfernen) untersuchen, da reines Addieren irreparable frühe Fehlentscheidungen zulassen kann.

**Wichtige Vergleichsexperimente für diese spätere Stufe:**

- Ursprüngliches EvoGrow (identische Rechenbudgets).
- EvoGrow mit Residual-Vorschlägen.
- EvoGrow nur mit verbesserter Koeffizienteninitialisierung / verbessertem Fit (damit Vorschlags- und Fit-Effekt unterscheidbar sind).
- Einfache residualbasierte Forward Selection ohne Evolution.
- Direktes Weak-SINDy.

**Ziel wäre nicht:** „EvoGrow mit mehr Tricks“.  
**Ziel wäre:** Eine überprüfbare Antwort darauf, unter welchen Bedingungen *inkrementelles Strukturwachstum aus Residualinformation* zu echter Strukturrichtigkeit führt – und wann es prinzipiell scheitert.

Möglicher wissenschaftlicher Beitrag bei positiver Evidenz: die Analyse der **lokalen Sichtbarkeit wahrer fehlender Terme** im schwachen Residualraum und eine **sparsame, residualgelenkte Wachstumsstrategie**, die über einfache Forward Selection hinaus einen messbaren Vorteil besitzt. Das ist vorerst ein *potenzieller* Paper-Baustein, kein zugesicherter PhD-Beitrag.

## 8. Fragen, die Claude zuerst kritisch prüfen soll

Bitte vor jeder Implementierung diese Punkte beurteilen und nötigenfalls Rückfragen stellen:

1. **Ist der schwache Residualansatz korrekt formuliert?** Welche Testfunktionen, Fenster, Normierungen und numerischen Stabilitätsbedingungen brauchen wir für ein aussagekräftiges Minimalexperiment?
2. **Welcher Residualbegriff ist hier sinnvoll?** Weak-form-Dynamikresidual, Simulationsresidual oder eine getrennte Betrachtung? Wie verhindern wir, dass ein Koeffizientenfehler als fehlende Struktur fehlinterpretiert wird?
3. **Ist Einzelterm-Screening mathematisch bereits identisch zu OMP / Forward Selection?** Falls ja: Was bleibt als eigentliche neue Hypothese, und welche Baseline muss zwingend mitlaufen?
4. **Wann ist das Ranking nicht identifizierbar?** Welche Diagnostik über projizierte Bibliotheksspalten, Konditionszahlen, Korrelationen oder Sensitivitäten brauchen wir? Was können wir mit einer einzigen Trajektorie überhaupt behaupten?
5. **Welche kleinste Stichprobe ist aussagekräftig?** Welche vorhandenen ODEBench-Fälle, Partialstrukturen und Trainingsdaten sind tatsächlich im Repository verfügbar?
6. **Wie operationalisieren wir den Stop/Go-Entscheid?** Eine einfache, **vorab festgelegte** Erfolgsschwelle ohne nachträgliches Schönrechnen.
7. **Paar-Screening:** Welche konkrete Beobachtung würde es rechtfertigen? Ist es mit kleinem Budget möglich, ohne in kombinatorische Suche abzurutschen?
8. **Strategische Frage:** Kann dieses Konzept EvoGrow tatsächlich einen Vorteil gegenüber direktem Weak-SINDy verschaffen, oder ist es nur ein aufwendigerer Weg zur gleichen Lösung?

## 9. Gewünschte nächste Antwort von Claude

**Bitte jetzt nicht implementieren.**

Stattdessen:

1. Die Idee kurz und präzise in eigenen Worten zusammenfassen, um das Verständnis abzugleichen.
2. Die **wichtigsten** methodischen Einwände nennen, einschließlich möglicher trivialer/etablierter Äquivalenzen.
3. Einen **minimalen, falsifizierbaren ersten Versuch** vorschlagen, der möglichst nur bestehende Daten nutzt.
4. Konkret sagen, welche Informationen aus Repository, Experimentlogs oder von mir noch nötig sind.
5. **Gezielte Rückfragen** stellen, statt die offenen Entscheidungen stillschweigend zu treffen.

Das ist ausdrücklich ein **kleines Side-Projekt**. Die bestehende EvoGrow-/Phase-C-Auswertung und die Pläne für die Dissertation bleiben davon zunächst unberührt.

---

### Interne Quellen für Claude

- `diskussion_warum_scheitert_die_suche.md` – Problemstellung, Evidenz, fünf Fehlerklassen, offene Diagnose.
- `CLAUDE.md`, `DIARY.md` – gültiger Stand und Entscheidungen im Repository.
- `analysis/data/paper1_phaseC_v1/hierarchy_n47_e935c37/` – C-1 und Vergleichstabelle.
- `analysis/data/paper1_phaseC_v1/restart_curve/` – P-04 Restart-Kurve.
- `analysis/data/wp_t1d_neighbourhood/wp_t1f_campaign_1db1193…/` – WP-T1f.
- `outputs/paper2_t2a_s1_e483f83/` – Orakel-Prior-Test S1.
- `src/structure/evogrow.jl`, `studies/regression/run_regression.jl` – Objective und Lambda-Konfiguration.

*Hinweis: Diese Pfade und Zahlen wurden aus dem vorhandenen Diskussionspapier übernommen und in dieser Skizze nicht erneut gegen Code/Logs verifiziert.*

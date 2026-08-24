# Prüfauftrag vor der ODEBench-Anfrage

**Stand 24.08.2026.** Zum Mitnehmen. Ziel: bestätigen, dass die geplante Mail
(`docs/anfrage_odebench_autoren.md`) nichts fragt, was öffentlich bereits beantwortet ist — und dass
keine ihrer Behauptungen falsch ist.

Die Mail hat genau zwei Inhalte. Beide sind unten mit ihrer Belegstelle aufgeführt, damit jede
einzeln überprüfbar ist.

---

## Was die Mail behauptet

### Behauptung A — die Frage

> Das Paper sagt, die zwei kuratierten Anfangsbedingungen je Gleichung dienten der Bewertung der
> Generalisierung. Der veröffentlichte Code liest aber nur die **erste**, und die
> Generalisierungsaufgabe zieht eine **zufällige** Anfangsbedingung. Welche wurde für die berichteten
> Zahlen verwendet?

**Belege:**

| Aussage | Fundstelle |
|---|---|
| zwei kuratierte ICs für Generalisierung | Paper, Beschreibung von ODEBench |
| Loader liest nur die erste | `evaluate.py`, `read_equations_from_json_file`: `_sample["solutions"][solution_i][0]` |
| Generalisierung zieht zufällig | `evaluate.py`, Task `y0_generalization`: `y0 = self.env.rng.randn(dimension)` |
| Struktur der Datei erlaubt beide | `solutions[0]` hat zwei Einträge, `init` = `[10.0]` und `[3.54]`, je 512 Punkte |

### Behauptung B — die Beobachtung

> Das Repository liefert zwei verschiedene Abtastungen desselben Benchmarks aus, und die gröbere hat
> sich fortgepflanzt.

**Belege:**

| Artefakt | Eigentümer | Abtastung | von einer Auswertung gelesen? |
|---|---|---|---|
| `strogatz_extended.json` in `sdascoli/odeformer` | Benchmark-Autoren | **512** | ja, `evaluate.py` |
| `solve_and_plot.py`, gleiches Verzeichnis | Benchmark-Autoren | 150 | nein, schreibt `solutions.json` |
| `github.com/GPBench/ODEBench` | **Tonda**, angelegt 2025-08-06 | 150 | ja, in seiner eigenen Studie |

---

## Was ich bereits geprüft habe

Damit das Team nicht doppelt sucht:

- Paper vollständig, arXiv 2310.05573, inklusive Appendix A (Kuration) und E
- kompletter Dateibaum von `sdascoli/odeformer`, 59 Dateien
- gelesen: `evaluate.py`, `solve_and_plot.py`, `environment.py`, `generators.py`,
  `baseline_utils.py`, `run.py`, `metrics.py`, `sklearn_wrapper.py`
- `strogatz_extended.json`: Inhalt, Struktur, Punktzahl, Upstream-Historie
  (letzte Änderung 2023-09-29), Byte-Vergleich mit unserer Kopie
- `GPBench/ODEBench`: README, Erstellungsdatum, Commit-Historie, Autorenschaft
- Tonda et al. 2025 vollständig (GECCO Companion, DOI 10.1145/3712255.3734301)

**Ergebnis:** In keiner dieser Quellen steht, welche Anfangsbedingung die berichteten
Generalisierungszahlen erzeugt hat.

---

## Was das Team prüfen sollte

Nach absteigender Trefferwahrscheinlichkeit. **Findet ihr irgendwo eine Antwort auf Behauptung A,
fällt die Mail — oder wird zu einem Dank.**

**1. OpenReview-Forum, `openreview.net/forum?id=TzoHLiGVMo`.** Die wahrscheinlichste Fundstelle.
Gutachten und Rebuttal enthalten oft genau solche Protokollklärungen. Zu durchsuchen nach: *initial
condition*, *generalization*, *ODEBench*, *150*, *512*, *trajectory points*. **Diese Stelle habe ich
nicht geprüft.**

**2. Issues, Pull Requests und Diskussionen** in `sdascoli/odeformer`. Möglicherweise hat jemand
dieselbe Frage schon gestellt. Auch geschlossene Issues.

**3. Commit-Historie von `evaluate.py`.** Falls eine frühere Fassung `[solution_i][1]` gelesen hat,
war die zweite IC einmal in Gebrauch, und die Frage beantwortet sich aus der Historie. Ebenso
prüfen: andere Branches als `main`.

**4. Camera-ready gegen arXiv.** Ich habe die arXiv-Fassung gelesen. Die ICLR-Proceedings-Fassung
(`proceedings.iclr.cc/paper_files/paper/2024/…`) kann einen abweichenden Appendix haben.

**5. Spiegelungen des Datensatzes** — HuggingFace, Zenodo, PapersWithCode. Ein Datenblatt dort würde
die kanonische Abtastung nennen.

**6. Vorträge, Folien, Poster** zur ICLR-2024-Präsentation.

**7. Spätere Arbeiten derselben Gruppe**, die ODEBench verwenden und das Protokoll beschreiben.

---

## Was die Mail widerlegen würde

Damit klar ist, worauf zu achten ist:

- **Behauptung A fällt**, wenn irgendwo steht, welche IC die Generalisierungszahlen erzeugt hat.
  Dann bleibt höchstens ein Dank für die Klarstellung — die Mail wäre überflüssig.
- **Behauptung B fällt**, wenn `evaluate.py` doch nicht der Auswertungspfad des Papers war, oder
  wenn irgendwo dokumentiert ist, dass 512 bewusst gilt und 150 ein Überbleibsel ist. Dann wäre die
  Beobachtung keine Neuigkeit, sondern eine Nachfrage zu etwas Bekanntem.
- **Beide fallen**, wenn es eine offizielle ODEBench-Dokumentation gibt, die wir übersehen haben.
  Genau danach ist zuerst zu suchen.

---

## Wenn nichts gefunden wird

Dann geht die Mail so raus, wie sie in `docs/anfrage_odebench_autoren.md` steht — mit deiner
Affiliation und deinem Absender. Zwei Hinweise zum Ton, die ich dort schon umgesetzt habe:

- Die Beobachtung ist als **Beitrag** formuliert, nicht als Fehlermeldung. Sie ist der eigentliche
  Eisbrecher: Wir liefern etwas, das sie so vermutlich nicht haben.
- EvoODE, unsere Ergebnisse und die Kampagne kommen bewusst **nicht** vor. Eine erste Mail, die
  etwas verkauft, bekommt seltener eine Antwort als eine, die etwas fragt.

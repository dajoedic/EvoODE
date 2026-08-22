# Anfrage an die ODEBench-Autoren — Entwurf

**Stand 22.08.2026.** Entwurf zum Versenden. Adressaten: Stéphane d'Ascoli, Sören Becker, Alexander
Mathis, Philippe Schwaller, Niki Kilbertus (ODEFormer, ICLR 2024).

**Was vorher geprüft wurde**, damit die Mail nichts fragt, was öffentlich beantwortet ist:

- Paper vollständig gelesen (arXiv 2310.05573), Appendix A und E eingeschlossen
- `strogatz_extended.json` heruntergeladen und mit unserer Kopie verglichen — byteidentisch
- Upstream-Historie der Datei geprüft (letzte Änderung `32dd990`, 2023-09-29)
- `odeformer/odebench/solve_and_plot.py` gelesen — 150 Punkte, schreibt nach `solutions.json`
- `evaluate.py` gelesen — liest die vorberechneten Lösungen aus `strogatz_extended.json`
- Repository-Dateibaum vollständig durchgesehen (59 Dateien)

Damit ist die Gitterfrage beantwortet und **nicht** Teil der Mail. Übrig bleibt eine Frage.

---

## Entwurf

**Betreff:** ODEBench: which initial conditions were used for the generalization results?

Dear Dr. d'Ascoli and colleagues,

I am a PhD student working on structure discovery for coupled ODE systems, and I am using ODEBench
as the evaluation suite for a study on search-space control. Before I report anything that touches
your work, I wanted to make sure I describe your protocol correctly — and while auditing it against
the released code I ran into one question I could not settle from the artefacts, plus one
observation you may want to know about.

**The question.** The paper states that two manually chosen initial conditions are included per
equation in order to evaluate generalization. In the released `evaluate.py`, however,
`read_equations_from_json_file` reads `_sample["solutions"][solution_i][0]` — the first initial
condition — and the `y0_generalization` task draws a fresh initial condition via
`self.env.rng.randn(dimension)`. Were the reported ODEBench generalization results obtained from the
second curated initial condition, or from random draws? It matters for how the number should be
read, and I would rather cite it correctly than guess.

**The observation.** The repository appears to ship two different samplings of the benchmark. The
committed `odeformer/odebench/strogatz_extended.json` carries 512-point trajectories, and this is
what `evaluate.py` reads. The generation script in the same directory, `solve_and_plot.py`, uses
`t_eval = np.linspace(0, 10, 150)` and writes to `solutions.json`, which no evaluation path in the
repository seems to read. Both are reasonable in isolation, but the difference is a factor of 3.4 in
sampling density, and at least one later study has taken the 150-point configuration as *the*
ODEBench protocol. Since sampling density has since been shown to affect how misleading the
derivative-transformed search space becomes, the two are not interchangeable. You may want to
document which is canonical.

For what it is worth from the outside: the curation is the most usable ODE benchmark I have worked
with, and the fact that the equations come with sources and descriptions is what made a careful
protocol audit possible at all.

With thanks and best regards,
David Jödicke
[Affiliation]

---

## Hinweise zum Versenden

- Der zweite Teil ist als **Beitrag** formuliert, nicht als Fehlermeldung. Das ist der Eisbrecher:
  Wir liefern ihnen eine Beobachtung, die sie so vermutlich nicht haben.
- Die Frage ist bewusst eng gehalten und belegt, dass die Artefakte gelesen wurden. Sie ist damit
  auch dann nützlich, wenn keine Antwort kommt — sie zeigt, was wir geprüft haben.
- Nicht erwähnt, bewusst: unsere eigenen Ergebnisse, die Kampagne, EvoODE als Methode. Eine erste
  Mail, die etwas verkauft, bekommt seltener eine Antwort als eine, die etwas fragt.
- Falls du EvoODE doch nennen willst, dann als einen Satz am Ende und ohne Zahlen — die
  Vergleichsfrage steht ohnehin erst in Paper 3 an.

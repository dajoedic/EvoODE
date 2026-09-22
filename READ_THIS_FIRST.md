# READ_THIS_FIRST.md — Sitzungsübergabe

**Was dieses Dokument ist:** der flüchtige Zustand *zwischen* zwei Chat-Sitzungen — was gerade läuft,
was uncommittet im Working Tree liegt, welche Entscheidung als Nächstes ansteht. Nichts weiter.

**Was es ausdrücklich nicht ist:** ein Planungs- oder Statusdokument. `CLAUDE.md` verbietet ein
zweites davon. Alles Dauerhafte gehört dorthin, nach `PAPER_1.md` oder ins `DIARY.md` —
**nicht hierher.**

**Regeln:** wird immer **vollständig überschrieben**, nie angehängt. Was älter als ein paar Tage
ist, ist vermutlich falsch — dann gilt `CLAUDE.md`.

**Stand: 2026-09-22, 19:30.** Der Nutzer hat die Freigabe auf **frühestens 20:15** terminiert.

---

## 1. Was gerade läuft

**Die Phase-C-Kampagne läuft unverändert auf Orion.** Nichts von heute hat den Kampagnenpfad
berührt. Image ist SHA-gepinnt, siehe Abschnitt 5.

**WP-T1e ist fertig und lokal verifiziert** — die Reparatur von WP-T1d plus Budget, Sharding und die
Cluster-Manifeste.

**Der Nutzer hat für heute ausnahmsweise delegiert:** Claude darf nach **GitLab** pushen und den
T1d-Job auf Orion starten. **GitHub bleibt beim Nutzer** (18 ungepushte Commits). Die Delegation
gilt für diesen einen Vorgang, nicht dauerhaft.

## 2. Der Ablauf, und wo er steht

| # | Schritt | Status |
|---|---|---|
| 1 | WP-T1e schreiben (Codex) | **fertig**, `blocked` wie vorgesehen |
| 2 | Regressionstest: `log10_loss_ratio(1e-4, 1e-2) == -2.0` | **grün**, 188 + 3 Tests |
| 3 | Lokaler Smoke, System 24 + 25, beide IC | **grün**, 168 Zeilen, 4 Zellen |
| 4 | `git push gitlab main` (77 Commits hinterher) | **frühestens 20:15** |
| 5 | CI baut, Zeitlimit 3 h | offen |
| 6 | `oc apply` Bootstrap → Smoke-Job (2 Zellen) | offen |
| 7 | Records prüfen | offen |
| 8 | `oc apply` der Lauf: `completions: 36`, `parallelism: 2` | offen |

**Der Smoke-Job ist zugleich der Build-Check.** `glab` ist nicht installiert und die Registry
verweigert Docker den Lesezugriff, also lässt sich der Pipeline-Status nicht direkt abfragen.
`ImagePullBackOff` heißt „Build noch nicht fertig", nicht „kaputt" — dann einfach später erneut.

**Abbruchbedingungen, die sich Claude gesetzt hat:** nicht pushen, wenn Schritt 2 oder 3 scheitert;
den echten Job nie vor dem Smoke; die Kampagnen-Jobs nicht anfassen; bei Unerwartetem anhalten und
aufschreiben statt improvisieren.

## 3. Warum T1d auf den Cluster geht

Entschieden 2026-09-22 und in `CLAUDE.md` als Regel festgehalten: **was nicht sicher unter 8 h
bleibt, läuft auf Orion, nie auf dem Laptop.** Risiko-Asymmetrie — eine Fehlschätzung ist auf dem
Cluster ärgerlich, auf dem Arbeitsgerät blockiert sie Tage.

Für T1d ist die Unsicherheit belegt: Projektion 3.946 Fits / 10,4 h, aber gemessen wurde auf
System 24 (dem **billigsten**) 1,80 s je Fit, während die Projektion mit 9,48 s rechnet — und
Phase B zeigt zwischen den dim-2-Systemen einen Faktor **1.800** bei den Kosten je Zelle
(0,003 h bis 5,33 h). Eine Konstante über diese Spanne ist keine Schranke. Deshalb zusätzlich:
Loss-Eval-Budget je Fit und `activeDeadlineSeconds: 86400`.

## 4. Was heute committet wurde

| Commit | Inhalt |
|---|---|
| `700a685` / `2eb54e6` | DIARY: Seitenzweig umgehängt — Ziel ist Strukturtreffer auf gekoppelten Systemen |
| `ae7573d` / `b4498f6` | WP-T1: Term-Relevanz, Machbarkeit. Gate **positiv** |
| `139dd89` | Paper-Bogen umgebaut, `PAPER_TIMELINE.md` eingearbeitet und entfernt |
| `32c7989` / `401e07f` | DIARY: die vier Bogen-Entscheidungen, Grenzen-Rahmung beibehalten |
| `10a809c` / `75baed6` | WP-T1b: Standalone-Rangliste. Deutung **C** |
| `58cb17a` / `0701cf6` | DIARY: WP-T1b und die Kreuzprüfung |
| `0dc79cc` / `5a6a447` | Seitenzweig als geschlossene Liste eingefroren, T1d-Kosten korrigiert |
| `25e4ad5` | WP-T1c: STLSQ-Pfad, **kein Gewinner**, `forward` bleibt |
| `a9a9471` / `bf5d353` | Kampagnen-Image dokumentiert, Prüfbefehl im Deployment-Guide §6b |
| `c6d714e` | Die 8-Stunden-Regel in `CLAUDE.md` |

## 5. Das Kampagnen-Image — verifiziert, nicht erschlossen

Beide Phase-C-Jobs laufen unter `evoode:221a3a72f0cb43164a22b09baac2d9ae82681a02` — Commit
`221a3a7` vom 14.09., Vorfahr von `main` — mit `imagePullPolicy: IfNotPresent`.

**Ein GitLab-Push kann die laufende Kampagne nicht verändern.** Der Push erzeugt einen neuen
SHA-Tag und verschiebt `:main`; beide sind verschieden vom gepinnten Tag, und die CI hat keinen
Deploy-Schritt — `.gitlab-ci.yml` kennt nur `build` und `security`.

**Aus den Vorlagen unter `k8s/` lässt sich das nicht schließen**, die tragen nur `<COMMIT_SHA>`,
und die erzeugten Manifeste sind gitignoriert. Prüfbefehl: `docs/hpc_deployment_guide.md` §6b.

## 6. Der Stand des Seitenzweigs

Die eingefrorene Liste steht in `docs/phd_thesis_arc.md` §5. Schritte 0–2 sind abgeschlossen:

- **WP-T1** — Signal vorhanden, Median `n_false_before_last_true` = 0,0 auf dim 2+3
- **WP-T1b** — ersetzt die Suche **nicht** (Deutung C): 30,0 % / 0,0 % gegen SINDys 66,7 % / 28,6 %
- **WP-T1c** — **kein Gewinner**, `forward` bleibt Prioritätsgeber
- **WP-T1d** — läuft als Nächstes: ist der wahre Träger ein lokales Optimum unseres Loss?

Zwei Befunde, die in den Codex-Reports fehlen und in `docs/phd_thesis_arc.md` §5 stehen: die
p-Werte sitzen am **Auflösungsboden** von 18 Clustern; und **„weak schlägt fd" ist nicht haltbar**.

## 7. Offene Entscheidungen, keine davon dringend

1. **Der Rauschzuschnitt von Paper 1** — größter unbudgetierter Posten. `docs/phd_thesis_arc.md`
   §3 und §11.
2. **Das prädiktive Kriterium für Kappen-Versagen** hat unter Claim A–D keinen Besitzer mehr.
3. **Was WP-T2a wird**, hängt an WP-T1ds Ausgang. Nicht vorher festlegen.

## 8. Betriebliches

- **Kein Branch.** Historie ist linear, Pfade disjunkt. Bei **WP-T2a** neu bewerten — der greift in
  `src/structure/evogrow.jl` ein.
- **`PAPER_TIMELINE.md` nicht wieder anlegen.** Eingearbeitet in `docs/phd_thesis_arc.md`.
- **Codex kann kein Julia ausführen.** Julia-Pakete werden geschrieben, als `blocked` gemeldet und
  von Claude ausgeführt. Heute hat das zwei Defekte erzeugt, einen davon **still**:
  `log10(neighbor / true)` teilt durch `Bool(1)`. Deshalb der konkrete Zahlenwert im
  Regressionstest.

## 9. Was die lokale Prüfung ergeben hat

Beide Defekte aus WP-T1d sind behoben: `true_loss_value` als zulässiger Name, und Zeile 364 teilt
tatsächlich durch den wahren Loss statt durch `Bool(1)`. Der Regressionstest prüft den konkreten
Wert `-2.0`, nicht nur „nicht `nothing`".

Der lokale Smoke über System 24 und 25, beide IC-Sätze, lieferte 168 Nachbarzeilen und ein Bild,
das die Theorie trifft: `add_one` schlägt die Wahrheit in 54 von 76 Fällen (Verschachtelung,
erwartet), `remove_one` in 0 von 8, `swap_one` in 19 von 84. **Das ist eine Installationsprüfung,
kein Ergebnis** — zwei Systeme, und zwar die beiden trivialsten der Stichprobe.

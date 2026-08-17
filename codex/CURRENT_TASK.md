> **Claude-Status:** `waiting for codex` — WP-W1 übergeben, ich prüfe alle 20 Minuten.
> Melde dich über `codex/STATUS.md`, nicht in dieser Datei. Committe nichts.
> Der Dauerauftrag steht in `codex/CODEX_PROTOCOL.md`.

# WP-W1 — `PAPER_1.md` ist das maßgebliche Dokument und beschreibt ein Paper, das es nicht mehr gibt
**Language: Python**

*(Sprache formal Python, weil kein Julia-Code entsteht — die Aufgabe ist redaktionell. Es ist
ausdrücklich **kein** Code zu schreiben.)*

## Der Befund

`CLAUDE.md` führt `PAPER_1.md` als autoritativen Ausführungsplan: *„takes precedence over this file
if the two drift."* Das Dokument ist auf **2026-05-17** datiert. Es plant im Detail um **v3** herum
und erwähnt den **Stage-Cap kein einziges Mal** — also genau die Variante, die inzwischen der
Beitrag des Papiers ist.

Damit steht die Präzedenzregel auf dem Kopf: Der aktuelle Stand liegt in `CLAUDE.md` und `DIARY.md`,
während das Dokument, das laut eigener Regel gewinnt, überholt ist. Je länger das offen bleibt,
desto mehr Entscheidungen hängen an einem Text, den niemand mehr liest.

## Umfang

Erstelle einen **Entwurf** einer überarbeiteten Fassung als **neue Datei** `docs/PAPER_1_draft.md`.
**`PAPER_1.md` selbst bleibt unangetastet** — die Übernahme entscheidet der Nutzer.

Der Entwurf trägt oben einen deutlichen Hinweis, dass er ein Entwurf ist, das Datum seiner
Erstellung, und den Satz, dass bis zu seiner Übernahme weiterhin `CLAUDE.md` und `DIARY.md` den
aktuellen Stand tragen.

### Quellen, in dieser Rangfolge

1. `CLAUDE.md` — aktueller Stand, Prioritäten, Ausschlüsse
2. `DIARY.md` — Chronologie und Belege; die Einträge ab 2026-07-31 sind die relevanten
3. `docs/paper1_scope_discussion_2026-08-14.md` — die Umpositionierung als Search-Space-Controller
4. `docs/wp_c1_stage_cap_horizon_audit.md`, `docs/wp_c2_stage_cap_failure_diagnosis.md`,
   `docs/wp_c4_stage_cap_doubt_band.md` — die Belege zum Cap
5. `docs/paper1_odebench_protocol_alignment.md` — Sampling-Protokoll und Vergleichbarkeits-Audit
6. `PAPER_1.md` — für Struktur, Gliederung und alles, was weiterhin gilt

### Was der Entwurf abbilden muss

- **Der Beitrag ist der Stage-Cap** als datengetriebener Search-Space-Controller auf dem
  v2.2-Substrat, nicht v3.
- **v2.2 → v3 → capped als dokumentierte Fehleranalyse.** v3 ist ein Ergebnis, kein Beitrag: Die
  Promotionsbedingung `r_k > loss_tol = 1e-8` ist auf gekoppelten Systemen unerreichbar (Fehlerboden
  ~1e-3), und `r_k` ist ableitungsfehlerkontaminiert.
- **Die Geschichte des Caps selbst gehört ins Paper**, nicht nur sein Endzustand. Drei Designregeln,
  jede aus einem Defekt gewonnen: positive Evidenz statt deren Abwesenheit (System 63); der
  Vorausblick muss so weit reichen, wie die Basis strukturelle Lücken erzeugt (WP-C1); und im
  Zweifelsband wird abgelehnt statt behauptet (WP-C4).
- **Phase-B-Umfang:** 63 Systeme, zwei Bedingungen (`pretuning` an/aus), 3 Seeds, 2 IC-Sets = 756
  Läufe; 512 Punkte über t ∈ [0,10], selbst integriert mit `Tsit5` bei `abstol = reltol = 1e-9`.
- **Provenienz:** Kampagnenidentität besteht aus drei Feldern — Git-Hash, Konfigurations- bzw.
  Phase-B-Fingerprint und `stage_cap_behavior_fingerprint`.
- **Metriken:** exakte Systeme über Supportwiederherstellung, Surrogatsysteme über R², erreichte
  Stufe und Stabilität. Beide werden **nie** zu einer Strukturkennzahl vermischt.
- **Wall-clock ist keine Evidenz.** Kostenaussagen ruhen auf Zählern.

### Was als Limitation dastehen muss, nicht kleingeredet

- `pruned_match = false` auf gekoppelten Systemen, auch bei sehr niedrigem Loss. Ursache ist der
  rein additive Sucher: `_expand` fügt nur hinzu, jede Linie startet aus einem Zufallsterm, ein
  falscher Term kann eine Linie nie verlassen.
- Der Cap ist **nur auf den 20 exakten Systemen prüfbar.** Für die 43 Surrogatsysteme existiert kein
  wahrer Support; die Sicherheit des Controllers ist dort konstruktionsbedingt nicht auditierbar.
- Der Cap gibt Schärfe für Sicherheit auf: endliche Caps 49 → 45 auf den exakten Gleichungszeilen.
- Der Verhaltens-Fingerprint deckt `_cap_split_decision` ab und sonst nichts.
- System 63 ist die Identifizierbarkeitsgrenze und keine Zelle.

### Was ausdrücklich **nicht** hineingehört

Kein GP-Baseline, kein v1, kein v2.1 im Phase-B-Umfang. Keine Behauptung über SINDy- oder
PySR-Vergleiche — die externen Spalten des Protokoll-Audits sind noch nicht gefüllt. Keine
Ergebniszahlen aus Phase B, denn es gibt noch keinen einzigen Kampagnen-Record. Wo Ergebnisse
hingehören, steht ein klar markierter Platzhalter.

### Form

Deutsch oder Englisch — nimm die Sprache, die `PAPER_1.md` heute verwendet, und bleib dabei.
Struktur, Nummerierung und Gliederungslogik des bestehenden Dokuments beibehalten, damit ein Diff
lesbar bleibt.

**Führe am Ende des Entwurfs eine Liste**, welche Abschnitte des alten Dokuments du gestrichen,
ersetzt oder unverändert übernommen hast — je mit einem Satz Begründung. Diese Liste ist für den
Nutzer das Wichtigste am ganzen Auftrag.

## Verboten

- **Keinen Code schreiben und keinen ändern**, weder Julia noch Python.
- **`PAPER_1.md` nicht anfassen.** Der Entwurf ist eine neue Datei.
- **`CLAUDE.md` und `DIARY.md` nicht anfassen.**
- **Keine Cluster-Jobs, keine Läufe, keine Manifeste.**
- **Nichts erfinden.** Jede Zahl im Entwurf muss aus einer der genannten Quellen stammen. Findest du
  einen Widerspruch zwischen den Quellen, löse ihn nicht selbst auf — führe ihn in einer eigenen
  Liste „offene Widersprüche" am Ende des Entwurfs.
- **Nichts committen, nichts stagen, nichts pushen. Kein `git add -A`.**

## Abnahme

- `docs/PAPER_1_draft.md` liegt vor, `PAPER_1.md` ist unverändert.
- Der Stage-Cap ist als Beitrag dargestellt, v3 als Fehleranalyse.
- Die drei Designregeln sind benannt und je einem Defekt zugeordnet.
- Alle oben genannten Limitationen kommen vor.
- Keine Phase-B-Ergebniszahlen, nur markierte Platzhalter.
- Die Änderungsliste am Ende ist vollständig.
- Etwaige Widersprüche zwischen den Quellen sind aufgelistet statt stillschweigend entschieden.

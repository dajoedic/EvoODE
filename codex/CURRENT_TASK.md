> **Claude-Status:** `waiting for codex` — WP-P1 übergeben, ich prüfe alle 20 Minuten.
> Melde dich über `codex/STATUS.md`, nicht in dieser Datei. Committe nichts.
> Der Dauerauftrag steht in `codex/CODEX_PROTOCOL.md`.

# WP-P1 — Der Fingerprint bemerkt Logikänderungen nicht
**Language: Julia**

## Der Befund

WP-C3 und WP-C4 haben das Cap-Verhalten auf fünf beziehungsweise acht Gleichungszeilen geändert.
**Beide Fingerprints standen still:**

| | vor WP-C3 | nach WP-C4 |
|---|---|---|
| Regression | `1d0ccf8d53c6576d` | `1d0ccf8d53c6576d` |
| Phase B | `e361a2af49366670` | `e361a2af49366670` |

Die Nutzlast von `config_fingerprint()` und `phase_b_fingerprint()` in
`studies/regression/run_regression.jl` und `studies/regression/phase_b_config.jl` enthält
ausschließlich Konfigurations**konstanten**. Ändert sich die Entscheidungs**logik** — wie in
`_cap_split_decision` geschehen —, bleibt der Hash gleich.

Damit leistet der Fingerprint nicht, wofür er existiert. `CLAUDE.md` verlangt vor der Publikation
den Nachweis, dass alle Läufe einen Fingerprint teilen. Genau diese Prüfung kann eine
Logikänderung nicht sehen: Zwei Records mit identischem Fingerprint können aus unterschiedlich
entscheidendem Code stammen. Aktuell hängt die Nachvollziehbarkeit allein am Commit-Hash im
Record — der seit `d2aed32` zuverlässig gesetzt wird, aber eine andere Frage beantwortet
(*welcher Commit?*) als der Fingerprint (*sind diese Records vergleichbar?*).

## Umfang

Dies ist zuerst eine **Entwurfsaufgabe**, dann erst eine Umsetzung. Der erste Teil ist der
wichtigere; setze nichts um, bevor der Entwurf steht.

### Teil 1 — Entwurf, im Report zu begründen

Erarbeite und bewerte die möglichen Wege, wie ein Fingerprint auch Verhaltensänderungen erfassen
kann. Mindestens diese drei sind zu behandeln, gern weitere:

1. **Quelltext-Hash über die entscheidungstragenden Dateien.** Präzise, aber übersensibel: Ein
   Kommentar oder eine Umformatierung verschiebt den Hash und erklärt Records für unvergleichbar,
   die es nicht sind.
2. **Verhaltens-Hash über eine feste Sonde.** Eine kleine, eingefrorene Menge synthetischer
   Eingaben durch die Entscheidungsfunktionen schicken und deren Ausgaben hashen. Unempfindlich
   gegen Formatierung, empfindlich genau gegen Verhalten. Frage: Wie wird die Sonde selbst
   eingefroren und versioniert, und was passiert, wenn sie erweitert wird?
3. **Getrennter zweiter Fingerprint.** Konfiguration und Verhalten bleiben zwei Größen, beide im
   Record. Frage: Was bedeutet dann „ein Fingerprint für die ganze Kampagne"?

Für jeden Weg: Was er erkennt, was er nicht erkennt, welche Fehlalarme er erzeugt, was er im
Betrieb kostet, und wie er sich zu den **bereits existierenden 42 Pilot-Records** verhält, die
keinen solchen Wert tragen.

Sprich eine **Empfehlung** aus und begründe sie.

### Teil 2 — Umsetzung des empfohlenen Wegs

Erst nach Teil 1. Anforderungen:

- Der Wert wird in jeden Record geschrieben, wie die bestehenden Fingerprints.
- Er ist **reproduzierbar** — zweimal berechnet auf demselben Stand ergibt denselben Wert. Zeige
  das im Report.
- Er **ändert sich** bei einer Verhaltensänderung. Zeige das, indem du gegen den Stand **vor**
  WP-C4 prüfst: `git stash` oder ein temporärer Checkout von `src/structure/stage_cap.jl` aus
  Commit `5d2f4f2`, Wert berechnen, zurück auf den aktuellen Stand, Wert berechnen. Die beiden
  müssen sich unterscheiden. **Danach den aktuellen Stand wiederherstellen** — der Arbeitsbaum
  muss am Ende auf dem aktuellen Code stehen.
- Er ändert sich **nicht** bei reiner Umformatierung oder Kommentaränderung. Zeige das ebenfalls.
- Die bestehenden `config_fingerprint()` und `phase_b_fingerprint()` behalten ihre Werte, sofern
  dein Weg das zulässt. Ändern sie sich, ist das im Report mit altem und neuem Wert festzuhalten.

### Teil 3 — Dokumentation

`docs/hpc_requirements.md` §7 und die Fingerprint-Passagen in `CLAUDE.md` beschreiben die
Provenienzzusage. Trage im Report zusammen, welche Stellen nach Teil 2 nachzuziehen sind. **Ändere
diese Dokumente nicht selbst** — das macht Claude.

## Verboten

- **Keine Cluster-Jobs, keine Kampagne, keine Regressions- oder Sondierungsläufe**, weder starten
  noch Manifeste dafür erzeugen.
- **Keine Änderung an der Cap-Logik.** WP-C4 ist abgenommen und bleibt, wie es ist. Diese Aufgabe
  beobachtet sie nur.
- **Keine Änderung an bestehenden Policy-Konstanten.**
- **Nichts committen, nichts stagen, nichts pushen. Kein `git add -A`.**
- Nichts, was länger als 15 Minuten läuft.
- Falls du für den Nachweis in Teil 2 den Arbeitsbaum vorübergehend veränderst: Er muss am Ende
  exakt auf dem aktuellen Stand stehen. Prüfe das ausdrücklich und berichte es.

## Abnahme

- Teil 1 liegt als begründeter Vergleich mit Empfehlung vor, nicht als Behauptung.
- Der neue Wert ist reproduzierbar, ändert sich gegen `5d2f4f2` und ändert sich nicht bei
  Umformatierung — alle drei mit konkreten Werten belegt.
- Der Arbeitsbaum steht am Ende auf dem aktuellen Code.
- Liste der nachzuziehenden Dokumentstellen im Report, ohne die Dokumente selbst anzufassen.

Führt Teil 1 zu dem Schluss, dass keiner der Wege trägt, ist das mit `status: blocked` zu melden
und zu begründen. Auch das ist ein gültiges Ergebnis.

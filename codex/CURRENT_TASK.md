> **Claude-Status:** `waiting for codex` — WP-E1 übergeben, ich prüfe alle 20 Minuten.
> Melde dich über `codex/STATUS.md`, nicht in dieser Datei. Committe nichts.
> Der Dauerauftrag steht in `codex/CODEX_PROTOCOL.md`.

# WP-E1 — Ein Beweisdokument darf sich nicht selbst überschreiben
**Language: Julia**

## Der Befund

`studies/lookahead/audit_exact_stage_cap_horizons.jl` schreibt seinen Report auf einen **fest
verdrahteten Pfad**, `docs/wp_c1_stage_cap_horizon_audit.md`. Zur Abnahme von WP-C2 und WP-C4 wurde
das Skript jeweils erneut ausgeführt — und hat dabei jedes Mal den Bericht des vorherigen
Arbeitspakets überschrieben.

Aufgefallen ist das erst beim Paper-Entwurf: Die Datei mit `wp_c1` im Namen trug intern den Titel
„WP-C2" und meldete bei Horizont 2 vier abgeschnittene Zeilen, wo WP-C1 neun gefunden hatte. Der
Beleg für die Aussage, die den Horizont überhaupt bewegt hat, existierte nur noch in der
Git-Historie.

Von Hand bereinigt: `docs/wp_c1_stage_cap_horizon_audit.md` steht wieder auf der Fassung von
`d472f8e` und trägt ein Regenerierverbot; der Wiederholungslauf liegt daneben als
`docs/wp_c4_stage_cap_horizon_audit.md`.

> **Die Regel, die daraus folgt:** Ein Beweisdokument gehört dem Arbeitspaket, das es erzeugt hat.
> Ein Skript, das auf einen festen Pfad schreibt, darf nicht zur Abnahme eines *späteren* Pakets
> erneut laufen, ohne dass das Ziel mitwandert. Sonst löscht die Abnahme den Beweis, den sie
> bestätigen soll.

## Umfang

### Teil 1 — Ziele werden übergeben, nicht verdrahtet

Alle Skripte unter `studies/`, die einen Report oder eine CSV nach `docs/` oder `outputs/`
schreiben, dürfen ihr Ziel nicht mehr fest verdrahten. Verschaffe dir zuerst einen Überblick,
welche das sind, und liste sie im Report auf — mit der Angabe, welche davon bereits einmal ein
fremdes Dokument überschrieben haben könnten.

Entwurf der Lösung liegt bei dir. Anforderungen:

- Der Zielpfad ist beim Aufruf angebbar.
- Fehlt die Angabe, darf **kein bestehendes Dokument stillschweigend überschrieben** werden.
  Ob das über einen Standardnamen mit Arbeitspaket-Kennung, über eine Abfrage vor dem Schreiben
  oder über einen Abbruch gelöst wird, entscheidest du — begründe die Wahl im Report.
- Bestehende Aufrufe in `SCRIPTS.md` müssen weiter funktionieren oder dort nachgezogen werden.

### Teil 2 — Die beiden bereinigten Dokumente nicht anfassen

`docs/wp_c1_stage_cap_horizon_audit.md` und `docs/wp_c4_stage_cap_horizon_audit.md` sind von Hand
in Ordnung gebracht und tragen erklärende Banner. Sie sind **nicht** neu zu erzeugen und nicht zu
verändern.

### Teil 3 — Nachweis

Im Report zeigen, dass ein zweiter Lauf desselben Skripts ein bestehendes Dokument **nicht**
zerstört. Führe das konkret vor, nicht als Behauptung: Prüfsumme des vorhandenen Dokuments vorher,
Skript erneut ausführen, Prüfsumme danach, plus wohin der neue Report gegangen ist.

## Verboten

- **Keine Cluster-Jobs, keine Kampagne, keine Regressions- oder Sondierungsläufe.** Auf Orion
  laufen gerade zwei Sondierungszellen; nichts anfassen, was dort hineinreicht.
- **Keine Änderung an der Cap-Logik, an Policy-Konstanten oder an irgendetwas
  Fingerprint-Relevantem.** Die Regression ist unter `1d0ccf8d53c6576d` und
  `61b6548ef0014593` abgeschlossen; diese Werte müssen stehen bleiben. Weise im Report nach, dass
  beide unverändert sind.
- **Nichts committen, nichts stagen, nichts pushen. Kein `git add -A`.**
- Nichts, was länger als 15 Minuten läuft.

## Abnahme

- Die Liste der betroffenen Skripte liegt vor.
- Ein zweiter Lauf überschreibt kein bestehendes Beweisdokument — vorgeführt mit Prüfsummen.
- `config_fingerprint()`, `phase_b_fingerprint()` und `stage_cap_behavior_fingerprint()` sind
  unverändert, im Report belegt.
- `SCRIPTS.md` ist nachgezogen, falls sich Aufrufe geändert haben.

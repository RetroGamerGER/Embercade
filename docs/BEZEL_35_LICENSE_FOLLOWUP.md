# Historical captured-bezel follow-up

> Historical evidence retained unchanged below. The current effective assignment
> is [LICENSING_1_0.md](LICENSING_1_0.md), with the corrected
> [Batocera GPL/LGPL distinction](BATOCERA_COMPONENT_LICENSES.md) and implemented
> [backend separation](ADAPTER_SEPARATION.md). Earlier prospective grants,
> blanket-scope assumptions and old captured-resource blockers are not current
> release findings. The removed captured-bezel and bundled-shader inventories
> are not the new RetroBat/host-package payload. No previous full audit was repeated.

## Preserved original report

# Gezielte Lizenzprüfung der 35 offenen Bezel-Pfade

27. Oktober 2026, Ausgangsstand `a104e47`. Geprüft wurden ausschließlich die
35 PNG-Pfade aus H/M/F/L/U der [vorherigen Entscheidungsliste](BEZEL_DECISION_FILES.csv).
Die 267 anderen Paketpfade und sämtliche Grafikdateien bleiben unverändert.

**Ergebnis:** Für `systems/spectravideo.png` lässt sich ein konkreter Bezug zu
RetroBats CC-BY-NC-SA-4.0-Projektlizenz begründet zuordnen. Diese Auswertung
über den Projektumfang ist ausdrücklich als Schlussfolgerung gekennzeichnet;
sie ist keine neue separate Freigabenachricht des Künstlers. Für die anderen
34 Pfade wurde kein abschließender anwendbarer Dateilizenzbeleg ergänzt.
Davon haben drei eine bekannte lizenzierte Originalprojekt-Quelle mit offener
Zuordnung, einer einen zusätzlichen Quellencredit und 30 keinen passenden
Zusatzbeleg. Kein Ergebnis wird als nachgewiesenes Weitergabeverbot bezeichnet.

Die [35-Zeilen-Dateiliste](BEZEL_35_LICENSE_FILES.csv) nennt für jeden Pfad die
geprüfte Quelle, das Ergebnis, Primärlinks, Grenzen und den verbleibenden Punkt.
Die ältere 302-Zeilen-Liste und historische JSON-Matrix bleiben als Baseline
unverändert. Diese Folgeprüfung ergänzt sie nur für die ausdrücklich genannten
35 Fälle.

## 1. Spectravideo: begründete Zuordnung zur RetroBat-Projektlizenz

Die Belegkette für `systems/spectravideo.png` ist konkreter als eine allgemeine
Aussage, dass RetroBat ebenfalls Bezels verwendet:

1. Der [Quellcommit R3](https://github.com/RetroBat-Official/retrobat-bezels/commit/d634f16d53a8c29a5520629241b0a9b8824206a9)
   bezeichnet den Beitrag ausdrücklich als Spectravideo von Lorenzolamas.
   Er enthält `default_unglazed/systems/spectravideo.png`.
2. Der bereits gespeicherte RetroBat-Vergleich ordnet genau diesen Inhalt
   unserem Auslieferungspfad zu. Dazu wurde kein neuer Bild-/Hashvergleich
   durchgeführt.
3. Die [offizielle Teamliste R2](https://github.com/RetroBat-Official/retrobat/blob/48ff054293bdeccb43da037b21efb030832fab90/README.md)
   nennt Lorenzolamas als Mitgründer mit Grafikaufgaben.
4. [RetroBats Projektlizenz R1](https://github.com/RetroBat-Official/retrobat/blob/48ff054293bdeccb43da037b21efb030832fab90/license.txt)
   umfasst das Projektwerk und insbesondere eigene schriftliche/grafische
   Inhalte unter CC BY-NC-SA 4.0; Upstream-Rechte bleiben bestehen.

**Schlussfolgerung:** Für den so identifizierten RetroBat-eigenen Grafikbeitrag
ist CC-BY-NC-SA-4.0 eine begründet zugeordnete Lizenzquelle. Es wird weder ein
nicht vorhandener PNG-Lizenzheader behauptet noch die Projektlizenz pauschal
auf fremde Community-Grafiken übertragen. Die dokumentierte Quelle und der
konkrete Künstlercredit sind hier entscheidend, nicht bloß die Mitlieferung.

Verbleibende Auslieferungsarbeit: Lorenzolamas, Quellverweis, Lizenzlink und
vorhandene Änderungshinweise in den späteren Notice-Umfang aufnehmen. Die
Zuordnung ist keine Freigabe für einen öffentlichen Build oder die anderen
34 Pfade. Eine separate Zustimmung wurde nicht eingeholt oder erfunden.

## 2. TheNamec: positive Originalprojekt-Lizenz, konkrete Ableitung bleibt offen

Für `systems/amiga1200.png`, `systems/amigacd32.png` und als Quellenkandidat
`systems/amiga600.png` wurde die bereits bekannte
[RC2-Dokumentation T1](https://github.com/TheNamec/megabezel-commodore-pack/blob/a0cc1c4813ad8b67edb8b367103b2ba96a34a704/README.md)
gezielt geprüft. Abschnitt 6.1.2 veröffentlicht die dortigen Assets unter
CC BY-NC-SA 4.0. Die Inhaltsbeschreibung nennt A600, A1200 und Amiga CD32.
Das Originalprojekt ist daher nicht ohne Weitergabe-/Bearbeitungslizenz.

Für A1200/CD32 bleibt der protokollierte V31-/Streitbezug bestehen. Die
vorhandenen Unterlagen ordnen die endgültigen Batocera-Grafiken aber nicht
abschließend einer bestimmten lizenzierten TheNamec-Originalfassung zu.
Bei A600 ist schon die Herkunftsverbindung lediglich ein Projekt-/Modelltreffer.
Der gemeinsame Systemname allein reicht nicht zur Übernahme der Lizenz.

Die bekannte SA-Quelle wird als positiver Beleg anerkannt. Es wird keine
Byte-Identität gefordert und keine spätere ND-Erklärung als automatische
Aufhebung früherer Rechte ausgelegt. Die drei Pfade bleiben bei der konkreten
Ableitungs-/Attributionszuordnung offen. C128 oder VIC20 werden nicht allein
wegen derselben Herstellermarke dieser RC2-Fassung zugeschlagen; ihre Zuordnung
ist durch diese Quelle nicht hergestellt.

## 3. Lightgun: zusätzlicher Original-/Bearbeitercredit

Der [offizielle gepinnte Batocera-Changelog B1](https://github.com/batocera-linux/batocera.linux/blob/9d2f7fc7d2436ba3bdccf64c8009dd73fa291f48/batocera-Changelog.md#L2617)
nennt für das Lightgun-Bezel **Orions Angel**, bearbeitet beziehungsweise
vergrößert von **Fery65**. Das ist ein zusätzlicher konkreter Paket-Quellenhinweis
für `systems/lightgun.png`, kein neu gefundener Lizenztext.

Im [Originalautoren-Thread O1, Beitrag 8](https://forums.libretro.com/t/japanese-arcade-cabinet-overlays/10470)
gestattet Orionsangel die dort besprochenen Verbesserungen mit Anerkennung
weiterer Mitwirkender. Diese Antwort belegt Kooperation und Erlaubnis für den
besprochenen Vorgang, identifiziert aber nicht unsere endgültige Lightgun-Datei.
Sie wird daher nicht als pauschale Lizenz aller Orionsangel-/Fery65-Varianten
ausgegeben. Andere lizenzierte Overlay-Portsammlungen werden ebenfalls nicht
ohne Quellenzuordnung als Lizenz dieser PNG übernommen.

Ergebnis: Quellenhinweis verbessert; die konkrete Weitergabe-Lizenzzuordnung
der ausgelieferten Lightgun-Fassung bleibt offen. Es wurde kein Bild zur
Versionsprüfung geöffnet oder verändert.

## 4. Übrige 30 Pfade: kein passender Zusatzbeleg in den geprüften Quellen

- Die sieben Mikael42-Pfade: Der
  [bekannte Originalfork M1](https://github.com/mikael42/batocera-bezel/tree/4d3c4c01fc8f04aa52c53677546145011bba6a64)
  enthält in seiner Root-Liste keine README-/Lizenzdatei. Die gezielte Textsuche
  ergab keinen Lizenztreffer. Daraus wird keine Aussage über nie veröffentlichte
  oder private Absprachen abgeleitet.
- Die acht Fery65-Pfade: Konkrete Import-Credits sind vorhanden; die geprüften
  zugehörigen öffentlichen Quellen/Kommentarstellen liefern keine passende
  zusätzliche Lizenz. Die allgemeine Genehmigung für andere Arcade-Umbauten
  ersetzt diesen Bezug nicht.
- Die 15 anderen Community-Pfade: Die vorhandenen konkreten Paketquellen und
  RetroBat-Zuordnungen wurden genutzt. Keinem davon konnte eine zusätzliche
  Originalautoren-Erklärung eindeutig zugeordnet werden.

Alle 30 Namen und die jeweiligen Quellen stehen einzeln in der Begleitliste.
Insbesondere wird ein von Fabrice Caruso bearbeiteter Import nicht allein
wegen seiner RetroBat-Rolle zu einem eigenen, neu lizenzierten Werk erklärt;
ein konkreter Originalkünstlercredit wie bei Spectravideo ist ein anderer Beleg.

## 5. Was RetroBat für genau diese 35 Fälle belegt

Aus der bereits vorhandenen RetroBat-Tabelle, ohne neue Gesamtprüfung:

- 35 Auslieferungspfade entsprechen 30 aufgelösten Quellpfaden.
- 28 der 35 haben am gespeicherten RetroBat-Pin denselben Quellpfad; 27 davon
  haben zusätzlich denselben bereits protokollierten Inhalt.
- Die sechs vertikalen MAME/DICE/FBNeo-Pfade sowie `systems/dice.png` fehlen
  dort unter genau diesem Quellpfad. Das ist kein Beweis für andere Urheber
  oder fehlende Lizenz und schließt andere Namen/Versionen nicht aus.
- `systems/snes-msu1.png` ist dort unter demselben Namen mit anderem Inhalt
  erfasst. Diese Abweichung wird nicht als neue Lizenz oder Verbot gewertet.

Das [Bezel-README R4](https://github.com/RetroBat-Official/retrobat-bezels/blob/5ce1f6ed32eb9f3df8ae14483afc4d1e3ef35d65/README.md)
bestätigt die reguläre Mitlieferung, ergänzt aber keinen gesonderten Grant für
die anderen Künstler. Die auf Lizenzfragen begrenzte Issue-/PR-Suche im
Bezel-Repository ergab keinen Treffer. Sieben bereits aus der Matrix bekannte
relevante Quellcommits haben keine öffentlichen Commit-Kommentare; neue
Erlaubnisse wurden daraus folglich nicht abgeleitet. Es wurde keine vollständige
Commit-Historie neu gesammelt.

Die [Batocera-Lizenzseite B2](https://wiki.batocera.org/license) verweist für
übernommene Komponenten auf deren jeweilige Projektlizenzen. Ihre LGPL-Aussage
für eigenen Code wird nicht in eine Grafiklizenz dieser PNGs umgedeutet.

## Umfang und Prüfgrenzen

Geprüft wurden die konkret relevanten öffentlichen Lizenz-/Credittexte,
Quellverweise und Kommentarstellen. Kein neuer Gesamtbestand, keine Bildpixel,
keine Bild-Hashes oder ganze Herkunftshistorien wurden untersucht. Sämtliche
Bezels, Shader, sonstigen bereits erledigten Fälle, Profile und AppImage-Bytes
bleiben unverändert. Keine Installation, kein Build, Kontakt, Push oder Release.

Die Quellen und Suchgrenzen sind in
`.work/bezel-35-license-2026-10-27/source-receipt.json` protokolliert.
Die Begleitliste wird auf exakt die ursprünglichen 35 Pfade, Quellen-/Alias-
Treue, Statussummen und vollständige Belegverweise geprüft. Fehlende Treffer
sind kein Nachweis, dass eine Erlaubnis außerhalb dieser Quellen nicht existiert.

Die Dokumentationsprüfung besteht: exakt 35 Zielzeilen, konsistente Quellen-
und Aliasfelder, eine ausdrücklich markierte Projektumfangs-Schlussfolgerung,
34 offene endgültige Dateizuordnungen und 102 lokale Links ohne fehlendes Ziel.
Die alte 302-Zeilen-Liste und historische JSON-Matrix sind unverändert; neue
Zugangsdatenmuster wurden nicht gefunden. Funktionstests wurden für die reine
Quellen-/Dokumentationsarbeit nicht erneut ausgeführt.

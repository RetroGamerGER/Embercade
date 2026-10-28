# Historical captured-bezel decision

> Historical evidence retained unchanged below. The current effective assignment
> is [LICENSING_1_0.md](LICENSING_1_0.md), with the corrected
> [Batocera GPL/LGPL distinction](BATOCERA_COMPONENT_LICENSES.md) and implemented
> [backend separation](ADAPTER_SEPARATION.md). Earlier prospective grants,
> blanket-scope assumptions and old captured-resource blockers are not current
> release findings. The removed captured-bezel and bundled-shader inventories
> are not the new RetroBat/host-package payload. No previous full audit was repeated.

## Preserved original report

# Bezel-Abnahme: konkrete verbleibende Fälle

Stand: 27. Oktober 2026. Auswertung der vorhandenen Unterlagen bei `14f982d`.
**Keine neue Untersuchung der Grafikdateien, Hashes oder Herkunftsgeschichte.**

**Nachtrag zur danach angefragten gezielten 35-Pfad-Lizenzsuche:**
[Folgebericht](BEZEL_35_LICENSE_FOLLOWUP.md) und
[35 konkrete Dateiergebnisse](BEZEL_35_LICENSE_FILES.csv). Spectravideo hat
jetzt einen begründet zugeordneten CC-BY-NC-SA-4.0-Projektlizenzbezug; die
Schlussfolgerung über den Projektumfang ist ausdrücklich markiert. Bei 34
Pfaden ist die konkrete Dateizuordnung weiter offen. Die folgenden 35er-Gruppen
beschreiben den unveränderten Ausgangsstand, nicht das Ergebnis der Folgeprüfung.

Die frühere Zusammenfassung „302 Dateien ohne geklärte Bezel-Rechte“ war zu
grob. Der alte Audit vergab dasselbe UNKNOWN sowohl für technische Begleitdaten
als auch für fehlende Zuordnung, vorhandene unversionierte Lizenzangaben und
noch nicht abgeschlossene Bedingungsprüfung. Daraus folgt weder, dass 302
Grafiken existieren, noch dass für jede Datei eine Erlaubnis fehlt.

## Bestand und Lesart

Grundlage ist die vorhandene [302-Pfad-Matrix](BEZEL_PROVENANCE.json):
150 PNG-Pfade, 151 INFO-Dateien und eine LAY-Datei. Die PNG-Pfade umfassen sechs
Aliase und verweisen auf 144 tatsächliche Quellpfade beziehungsweise 142 bereits
erfasste unterschiedliche Inhalte. Diese Zahlen werden nur aus der bestehenden
Matrix gelesen; die Bilder wurden nicht geöffnet oder erneut verglichen.

Der statische Ressourcenbestand ist durch denselben Bundle-Eintrag wie beim
akzeptierten privaten AppImage-Build `935eacf` beschrieben. Dieser Deskriptor
ist unverändert. Untersucht werden die mitgelieferten Konsolen-Dekorationen,
nicht zusätzliche Benutzer-Packs, Scraper-Medien oder ROM-Freigaben.

Alle unten genannten Pfade liegen unter
`share/embercade/resources/batocera/datainit/decorations/consoles/`.
Quelle ist `batocera-bezel` bei
`77a3239f3f0682fcf9e6050f07b40677395e5db7`.

Die [vollständige Dateiliste](BEZEL_DECISION_FILES.csv) enthält jeden der 302
Auslieferungspfade genau einmal: aufgelösten Inhalt, Quelle, Beitrag/Credit,
konkreten Lizenzbefund, verbleibenden Grund und bereits gespeicherte RetroBat-
Zuordnung. Die historische JSON-Matrix bleibt als Beleg unverändert.

| Gruppe | PNG-Pfade | Bereits belegt | Tatsächlich verbleibender Punkt |
| --- | ---: | --- | --- |
| N — eigener Duimon-/CC-Hinweis | 8 | Urheberhinweis/URL und CC-BY-NC-ND-Familie an der konkreten Grafik dokumentiert | Lizenzfassung/Variantenumfang und Auslieferung der Bedingungen abschließen; kein Fall „keine Lizenzangabe“ |
| D — weiterer Duimon-Beitrag | 107 | Konkreter Beitrag zugeordnet; öffentliche allgemeine Nutzungserklärung und historische SA-/ND-Lizenzen bekannt | Anwendbare Erklärung/Fassung für die protokollierte Original-/Nacht-/Standalone-Variante noch nicht abschließend zugeordnet |
| H — erhaltener historischer Streitbezug | 2 | Konkrete V31-Importfassung und Streitbezug dokumentiert | Damaliger Erlaubnisumfang und ursprüngliche Credit-Frage nicht abschließend dokumentiert; kein festgestellter Rechtsverstoß |
| M — Mikael42 | 7 | Konkreter Beitrags-/Quellencredit | Kein konkret anwendbarer Erlaubnis-/Lizenzbeleg in den ausgewerteten Unterlagen zugeordnet |
| F — Fery65 | 8 | Konkreter Quellencredit | Kein konkret anwendbarer Erlaubnis-/Lizenzbeleg zugeordnet |
| L — Lorenzolamas | 1 | Konkreter Quellencredit | Kein konkret anwendbarer Erlaubnis-/Lizenzbeleg zugeordnet |
| U — übrige historische Community-Zuordnung | 17 | Batocera-Paketquelle und Historie bekannt | Ursprünglicher Grafikurheber und anwendbare Erlaubnis nicht konkret zugeordnet |
| Summe PNG | **150** | | |
| T — technische Begleitdateien | **152 weitere Pfade** | Paketquelle, Installation und Alias-Auflösung dokumentiert | Im Paket-/Notice-Umfang behandeln; keine zusätzlichen 152 Grafiken und kein separat nachgewiesener Bildrechte-Konflikt |

Ein protokollierter Git-Beitrag benennt nicht automatisch den alleinigen
Grafikurheber. Umgekehrt ist ein anderer Hash oder eine andere Quellebene kein
Beweis für andere Rechte. Ein fehlender Eintrag über eine Erlaubnis ist keine
Feststellung, dass der Urheber die Nutzung verboten hat.

## 1. Welche konkreten Dateien haben noch welche Lücke?

### N — acht Dateien mit eigenem Lizenz- und Urheberhinweis

`systems/arduboy.png`, `systems/gamegear.png`, `systems/gb2players.png`,
`systems/gp32.png`, `systems/macintosh.png`, `systems/wasm4.png`,
`systems/ps2.png`, `systems/snes.png`.

Der vorhandene Audit protokolliert bei den ersten sechs den XMP-Textlayer
`CC BY-NC-ND - https://github.com/Duimon`; bei PS2 und SNES wurde der entsprechende
sichtbare Seitenhinweis bereits geprüft. Das ist ein positiver dateispezifischer
Lizenzbefund. Der Hinweis selbst nennt keine Versionsnummer. Deshalb lautet
der offene Punkt Fassung/Umfang und Bedingungen, nicht „Erlaubnis fehlt“.
Eine neue Einzelgenehmigung ist nicht allein deshalb nötig, weil eine
anwendbare öffentliche Lizenz ND enthält.

### D — 107 weitere Duimon-zugeordnete PNG-Pfade

`default.png`, `systems/3do.png`, `systems/3ds.png`, `systems/adam.png`, `systems/advision.png`, `systems/amiga.png`, `systems/amiga500.png`.

`systems/amstradcpc.png`, `systems/apple2.png`, `systems/apple2gs.png`, `systems/arcadia.png`, `systems/archimedes.png`, `systems/astrocade.png`, `systems/atari2600.png`.

`systems/atari5200.png`, `systems/atari7800.png`, `systems/atari800.png`, `systems/atarist.png`, `systems/atom.png`, `systems/bbcmicro.png`, `systems/c64.png`.

`systems/camplynx.png`, `systems/cdi.png`, `systems/channelf.png`, `systems/coco.png`, `systems/colecovision.png`, `systems/crvision.png`, `systems/dreamcast.png`.

`systems/electron.png`, `systems/fm7.png`, `systems/fmtowns.png`, `systems/gamate.png`, `systems/gamecom.png`, `systems/gamecube.png`, `systems/gb.png`.

`systems/gba.png`, `systems/gbc.png`, `systems/gbc2players.png`, `systems/gmaster.png`, `systems/gx4000.png`, `systems/intellivision.png`, `systems/jaguar.png`.

`systems/laser310.png`, `systems/lowresnx.png`, `systems/lynx-270.png`, `systems/lynx-90.png`, `systems/lynx.png`, `systems/markIII.png`, `systems/mastersystem.png`.

`systems/megacd.png`, `systems/megadrive.png`, `systems/megaduck.png`, `systems/msx1.png`, `systems/msx2.png`, `systems/n64.png`, `systems/neogeo.png`.

`systems/neogeocd.png`, `systems/nes.png`, `systems/ngp.png`, `systems/ngpc.png`, `systems/odyssey2.png`, `systems/pc.png`, `systems/pc88.png`.

`systems/pc98.png`, `systems/pcengine.png`, `systems/pcenginecd.png`, `systems/pcfx.png`, `systems/pdp1.png`, `systems/pico8.png`, `systems/pokemini.png`.

`systems/psx.png`, `systems/pv1000.png`, `systems/saturn.png`, `systems/scummvm.png`, `systems/scv.png`, `systems/sega32x.png`, `systems/segapico.png`.

`systems/sg1000.png`, `systems/sgb.png`, `systems/snes_msu-1.png`, `systems/socrates.png`, `systems/supergrafx.png`, `systems/supervision.png`, `systems/supracan.png`.

`systems/thomson.png`, `systems/ti99.png`, `systems/tic80.png`, `systems/triforce-standalone.png`, `systems/tutor.png`, `systems/tvgames.png`, `systems/uzebox.png`.

`systems/vc4000.png`, `systems/vectrex.png`, `systems/vemulator.png`, `systems/videopacplus.png`, `systems/virtualboy.png`, `systems/vsmile.png`, `systems/wii.png`.

`systems/wswan-90.png`, `systems/wswan.png`, `systems/wswanc-90.png`, `systems/wswanc.png`, `systems/x1.png`, `systems/x68000.png`, `systems/xbox-standalone.png`.

`systems/zx81.png`, `systems/zxspectrum.png`.

Die vorhandenen E1/E2/E6-Quellen sind echte positive Erlaubnisbelege:
Duimon erlaubt in [Beitrag 1220 vom 1. Mai 2021](https://forums.libretro.com/t/duimon-hsm-mega-bezel-graphics-and-presets-feedback-and-updates/28146?page=61)
die Nutzung seiner Grafiken und Quellen und nennt sein Batocera-Paket.
Historische SA4.0- und spätere ND4.0-Erklärungen sind bereits im
[bestehenden Audit](BEZEL_PROVENANCE.md#license-evidence-version-chronology-and-exact-file-limits)
dokumentiert. Die Restfrage betrifft die Anwendung auf die jeweilige vorhandene
Variante und gegebenenfalls andere Beiträge. Keine dieser 107 Dateien darf
allein wegen fehlender Byte-Identität als unlizenzierbar behandelt werden.
Der Audit hat diese Varianten-Zuordnung nicht abschließend entschieden;
das ist keine neue Aussage, dass Duimon keine Nutzung erlaubt hätte.

### H — zwei konkrete historische Streitfälle

| Auslieferungsdatei | Erhaltene Quelle | Konkreter Befund |
| --- | --- | --- |
| `systems/amiga1200.png` | `default_unglazed/systems/amiga1200.png` | Laut vorhandenem Audit unverändert aus V31-Import `5f95003`; diese Importgruppe steht im Bezug zur historischen TheNamec-/Credit-Debatte |
| `systems/amigacd32.png` | `default_unglazed/systems/amigacd32.png` | Derselbe belegte Importgruppen-Bezug |

Die [bereits untersuchte Diskussion](https://forums.libretro.com/t/duimon-hsm-mega-bezel-graphics-and-presets-feedback-and-updates/28146?page=101)
enthält widersprechende Angaben über damalige Erlaubnis, Herkunft und entfernte
Credits. Der Audit beweist weder eine unerlaubte Übernahme dieser beiden
konkreten Bilder noch deren rechtliche Abnahme. Sie verdienen eine eigene
Entscheidung; „nur irgendeine alte Community-Unsicherheit“ wäre zu ungenau.

**Nicht automatisch dazuzählen:** `systems/amiga.png` / `amiga500.png` und
`systems/c64.png` lösen auf spätere, von Duimon eingebrachte Standalone-Night-
Fassungen auf. Sie sind nicht die früheren V31-Dateien. `amiga600.png`,
`c128.png` oder `vic20.png` dürfen ebenfalls nicht allein wegen ihres Namens
als nachgewiesener Bestandteil dieses konkreten Streits bezeichnet werden.

### M — sieben Dateien mit Mikael42-Zuordnung, ohne zugeordneten Lizenzbeleg

`systems/amigacdtv.png`, `systems/easyrpg.png`, `systems/fds.png`,
`systems/gamepock.png`, `systems/msxturbor.png`, `systems/nds.png`,
`systems/psp.png`.

Grund: konkrete Beitrags-/Quellencredits sind vorhanden; ein passender
Weitergabe-Erlaubnisnachweis für diese Grafiken ist im bestehenden Audit nicht
zugeordnet. Eine bloße Ergänzung „Mikael42“ würde diese Beleglücke nicht lösen.

### F — acht Dateien mit Fery65-Quellencredit, ohne zugeordneten Lizenzbeleg

`systems/atomiswave.png`, `systems/naomi.png`, `systems/dice-270.png`,
`systems/dice-90.png`, `systems/fbneo-270.png`, `systems/fbneo-90.png`,
`systems/mame-270.png`, `systems/mame-90.png`.

Grund: die konkreten Import-Credits nennen Fery65. Eine zur jeweiligen Grafik
zugeordnete Weitergabelizenz dokumentiert der Audit nicht. Fünf dieser Pfade
sind Aliase; sie sind keine fünf zusätzlich gezeichneten Bilder. Zielauflösung
und Quelldatei stehen in der Dateiliste.

### L — eine Datei mit Lorenzolamas-Quellencredit

`systems/spectravideo.png` — expliziter Quellencredit in dem bereits erfassten
Commit `d634f16d`. Eine konkrete Weitergabelizenz wurde dadurch nicht belegt.

### U — 17 weitere PNGs ohne konkrete ursprüngliche Urheber-/Lizenzzuordnung

`systems/amiga600.png`, `systems/c128.png`, `systems/dice.png`,
`systems/dos.png`, `systems/fbneo.png`, `systems/lightgun.png`,
`systems/mame.png`, `systems/msx.png`, `systems/msx2+.png`,
`systems/prboom.png`, `systems/ps3.png`, `systems/satellaview.png`,
`systems/snes-msu1.png`, `systems/sufami.png`, `systems/vic20.png`,
`systems/wiiu.png`, `systems/xbox.png`.

Grund: bekannt ist der konkrete Batocera-Paketpfad mit Historie. Eine belastbare
Zuordnung des ursprünglichen Grafikurhebers und seiner Weitergabe-Erklärung
ist in diesen Unterlagen nicht erfasst. Das sind historische Dokumentationslücken,
keine nachgewiesenen Verbote. Andere Schreibweisen wie `snes_msu-1.png` oder
`xbox-standalone.png` sind getrennte Matrixeinträge und werden nicht vermischt.

### T — INFO-/LAY-Dateien

Alle 151 `.info`-Pfade und `systems/cdi.lay` sind in der Dateiliste einzeln
enthalten. Ihre bisherige Erfassung als UNKNOWN enthält ausdrücklich keine
Entscheidung über eigenständige Schutzfähigkeit. Sie werden deshalb nicht als
152 zusätzliche unlizenzierte Grafiken oder selbständige Bildrechte-Verstöße
geführt. Ihre technische Zuordnung ist erledigt; der Dokumentationsumfang des
Pakets bleibt erhalten. Daraus wird keine pauschale Gemeinfreiheit abgeleitet.

## 2. Was ist bereits erledigt?

- **Alle 302 Paketpfade:** konkrete Quelle, Rezept und Alias-Auflösung sind
  dokumentiert. Diese Bestands- und Transportfrage ist abgeschlossen.
- **258 Pfade, darunter 131 PNG-Pfade:** ein konkreter Beitrag/Quellencredit
  ist bereits zugeordnet. Das ist kein Nachweis alleiniger Urheberschaft, aber
  auch kein Grund, die Herkunftsuntersuchung erneut aufzurollen.
- **Die acht N-Grafiken:** Duimon-Zuordnung und dateispezifische Lizenzfamilie
  sind positiv dokumentiert. „Keine Lizenzangabe gefunden“ ist dafür falsch.
- **Öffentliche Erlaubnisquellen:** E1 sowie die versionierten SA-/ND-Quellen
  existieren und bleiben anerkannt. Sie müssen nicht neu gesucht werden.
- **Batocera-/RetroBat-Vertrieb:** ist dokumentiert. Das
  [RetroBat-Bezel-README](https://github.com/RetroBat-Official/retrobat-bezels/blob/5ce1f6ed32eb9f3df8ae14483afc4d1e3ef35d65/README.md)
  nennt die Batocera-Herkunft und reguläre Mitlieferung.

**Vollständige Veröffentlichungsabnahme:** Der alte Audit verzeichnet für keine
Einzeldatei `exact_file_grant_established=true`. Ich kann daraus keine bereits
erteilte vollständige Abnahme behaupten. Diese Null bedeutet aber nicht null
Lizenzbelege und rechtfertigt nicht das frühere gemeinsame Etikett für alle
Fälle. N, D, H, M/F/L/U und T benötigen unterschiedliche Entscheidungen.

## 3. Fehlen nur Credits oder tatsächlich Erlaubnisbelege?

Ein belastbar belegter reiner Fall „Nutzung vollständig geklärt, nur Name im
Embercade-Notice vergessen“ ist in den vorhandenen Unterlagen **nicht isoliert
festgestellt**. Das behauptet auch nicht, dass Credits fehlen:

- N enthält schon Credit und Lizenzangabe. Restarbeiten betreffen konkret
  Versions-/Variantenumfang und die Übernahme der Bedingungen/Notices.
- D hat bekannte allgemeine Erlaubnisquellen; offen ist deren Zuordnung und
  Bedingungsumfang, nicht eine dokumentierte Verweigerung.
- M/F/L/U und H haben in dieser Matrix noch keinen abschließend zugeordneten
  konkreten Erlaubnisnachweis. Ein Name allein ersetzt ihn nicht.

Ein vollständiger Abgleich der ausgelieferten zentralen Credit-Datei mit allen
Urheberhinweisen ist in diesen Unterlagen nicht protokolliert. Daher wäre sowohl
„es fehlen lediglich Credits“ als auch „Embercade hat die Credits entfernt“
ohne zusätzliche Belege eine unbegründete Behauptung.

## 4. Gibt es einen konkreten Lizenzwiderspruch?

**Kein konkreter Rechtsverstoß oder ausdrückliches Weitergabeverbot für eine
bestimmte aktuelle Datei ist im Audit nachgewiesen.** Dokumentiert ist der
historische Streitbezug der beiden H-Dateien. Bei den übrigen Gruppen geht es
um Zuordnung, Version und Bedingungen, nicht um ein gefundenes Verbot.

ND ist kein generelles Verbreitungsverbot: [CC BY-NC-ND 4.0, Abschnitte 2 und 3](https://creativecommons.org/licenses/by-nc-nd/4.0/legalcode.en)
erlaubt gedeckte nichtkommerzielle Weitergabe unter seinen Bedingungen;
veröffentlichte Bearbeitungen werden anders behandelt, notwendige technische
Formatänderungen gesondert zugelassen. Welche vorhandene Fassung welchem
Grant unterliegt, bleibt eine andere Frage als der Lizenzinhalt.

Der vorhandene Audit dokumentiert veränderte historische Varianten und lokale
Anzeige-/Overlay-Anpassungen. Er weist aber keinen konkreten verbotenen Export
oder entfernten Urheberhinweis durch Embercade nach. Ein möglicher Crop oder
ein anderer Hash ist kein solcher Nachweis. Die öffentliche Demo/Notice-
Darstellung kann Bedingungen berühren; eine konkrete Verletzung wurde nicht
festgestellt.

Die [RetroBat-Projektlizenz](https://github.com/RetroBat-Official/retrobat/blob/48ff054293bdeccb43da037b21efb030832fab90/license.txt)
ist eine zusätzliche Quelle für dessen Projekt-/Upstream-Regeln. Der bereits
gespeicherte Bezel-Repository-Befund enthält keinen separaten pauschalen Grant
für alle fremden Bilder. Weder wird daraus eine neue vollständige Freigabe
abgeleitet, noch wird RetroBats regulärer Vertrieb als irrelevant verworfen.
Der Audit benennt auch keine konkrete Datei, für die RetroBat nachweislich
einen vorhandenen ND-Grant durch seine Projekt-SA-Lizenz ersetzt hätte.

## Prüfung dieser Auswertung

Ausgewertet wurden nur `BEZEL_PROVENANCE.json`, die vorhandenen Audittexte und
der gespeicherte RetroBat-Beleg von 27. Oktober. Die dort schon verwendeten
öffentlichen Texte wurden für die präzise Formulierung nachgelesen. Es gab
keinen neuen Bild-, Hash-, Git-Historien- oder vollständigen Herkunftsvergleich,
keinen Build, Kontakt, Push oder eine Veröffentlichung. Keine Bezel-Datei und
kein Profil wurde verändert. Geprüft werden ausschließlich die Vollständigkeit
der 302 abgeleiteten Zeilen, die Gruppensummen, Quelldaten-Treue und Doc-Links.
Diese Prüfungen bestehen: 302 eindeutige Zeilen, alle 150 PNG-Namen im Bericht,
alle Quellen-/Aliasfelder konsistent, 90 lokale Links ohne fehlendes Ziel und
unveränderte historische JSON-Matrix. Funktionstests wurden für diese reine
Dokumentenauswertung nicht erneut ausgeführt.

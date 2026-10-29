"""Central installer catalog. English message IDs, German translations, no GUI dependency."""
from __future__ import annotations
from typing import Mapping
import os

SUPPORTED_LANGUAGES = ("de", "en")
GERMAN = {
 'Pacman unavailable': 'Pacman nicht verfügbar',
 'Pacman is not available. Install host software manually or make pacman available on your Arch-based system. No packages have been installed.': 'Pacman ist nicht verfügbar. Installiere Host-Software manuell oder stelle pacman auf deinem Arch-basierten System bereit. Es wurden keine Pakete installiert.',
 'PSP and Xbox system files are optional for Embercade setup. Leave these fields empty or skip this step if you do not need these systems yet.': 'PSP- und Xbox-Systemdateien sind für die Embercade-Einrichtung optional. Lass die Felder leer oder überspringe diesen Schritt, wenn du diese Systeme noch nicht benötigst.',
 'Choose a complete system-specific folder. The general BIOS folder is not used automatically.': 'Wähle einen vollständigen Ordner für das jeweilige System. Der allgemeine BIOS-Ordner wird nicht automatisch verwendet.',
 'PSP assets (optional for setup; required for PSP games)': 'PSP-Zusatzdateien (optional für die Einrichtung; für PSP-Spiele erforderlich)',
 'Skip for now': 'Vorerst überspringen',
 'The selected PSP or Xbox folder is incomplete. Choose the matching system files, clear the field, or select Skip for now. Your existing configuration and files are preserved.': 'Der ausgewählte PSP- oder Xbox-Ordner ist unvollständig. Wähle die passenden Systemdateien, leere das Feld oder wähle Vorerst überspringen. Deine bestehende Konfiguration und Dateien bleiben erhalten.',

 'Unsupported distribution': 'Nicht unterstützte Distribution',
 'Detected system: {distribution}. Automatic host-software installation requires an Arch-based distribution and pacman. No packages have been installed.': 'Erkanntes System: {distribution}. Die automatische Host-Software-Installation benötigt eine Arch-basierte Distribution und pacman. Es wurden keine Pakete installiert.',
 'Installer supports Arch-based Linux distributions.': 'Der Installer unterstützt Arch-basierte Linux-Distributionen.',
 "RetroArch shader collection": "RetroArch-Shader-Sammlung",
 "Library video playback": "Videowiedergabe der Spielebibliothek",
 'Opening the host installation…': 'Host-Installation wird geöffnet…',
 'Checking installed software and available packages…': 'Installierte Software und verfügbare Pakete werden geprüft…',
 'Please review and confirm the installation in the terminal.': 'Bitte prüfe und bestätige die Installation im Terminal.',
 'Installing host software: downloads, package checks and completion hooks…': 'Host-Software wird installiert: Downloads, Paketprüfungen und abschließende Systemschritte…',
 'Building additional host software. This can take several minutes; follow the terminal output.': 'Zusätzliche Host-Software wird gebaut. Das kann mehrere Minuten dauern; beachte die Terminalausgabe.',
 'Elapsed: {minutes}:{seconds}': 'Vergangen: {minutes}:{seconds}',

 "Location unavailable": "Speicherort nicht verfügbar",
 "Choose an available local folder or file. Mount network shares before selecting them. Your previous selection is unchanged.": "Wähle einen verfügbaren lokalen Ordner oder eine Datei. Binde Netzwerkfreigaben vor der Auswahl ein. Deine vorherige Auswahl bleibt unverändert.",
 "Xbox language and region are stored in Embercade's own EEPROM. Changing the original file later does not replace it. Change these settings in Xemu's dashboard.": "Xbox-Sprache und -Region sind in Embercades eigener EEPROM gespeichert. Eine spätere Änderung der Originaldatei ersetzt sie nicht. Ändere diese Einstellungen im Dashboard von Xemu.",
 "Graphical setup is unavailable. Check GTK3/PyGObject and your desktop session.": "Grafische Einrichtung nicht verfügbar. Prüfe GTK3/PyGObject und deine Desktop-Sitzung.",
 "Wayland decorations": "Wayland-Bezels",
 "Standalone decoration drawing": "Darstellung der Standalone-Bezels",
 "Display size detection": "Bildschirmgrößenerkennung",'Action unavailable': 'Aktion nicht möglich',
 'Add Embercade to Steam?': 'Embercade zu Steam hinzufügen?',
 'Add Steam later': 'Steam später hinzufügen',
 'Add to Steam (optional)': 'Optional zu Steam hinzufügen',
 'Additional system files': 'Zusätzliche Systemdateien',
 'Already configured: {path}': 'Bereits eingerichtet: {path}',
 'AppImage FUSE 2 runtime': 'AppImage-FUSE-2-Laufzeit',
 'Automatic installation is unavailable on this distribution.': 'Automatische Installation ist auf '
                                                                'dieser Distribution nicht '
                                                                'verfügbar.',
 'Available': 'Verfügbar',
 'BIOS folder': 'BIOS-Ordner',
 'BIOS: {path}': 'BIOS: {path}',
 'Back': 'Zurück',
 'Begin setup': 'Einrichtung beginnen',
 'Bubblewrap isolation': 'Bubblewrap-Isolation',
 'Cancel': 'Abbrechen',
 'Change settings': 'Einstellungen ändern',
 'Check again': 'Erneut prüfen',
 'Check and set up': 'Prüfen und einrichten',
 'Check complete': 'Prüfung abgeschlossen',
 'Check existing setup': 'Vorhandene Einrichtung prüfen',
 'Check shadPS4 file': 'shadPS4-Datei prüfen',
 'Check that the selected PSP or Xbox folder contains all the files listed on this page. Your existing files are preserved.': 'Prüfe, '
                                                                                                                              'ob '
                                                                                                                              'der '
                                                                                                                              'gewählte '
                                                                                                                              'PSP- '
                                                                                                                              'oder '
                                                                                                                              'Xbox-Ordner '
                                                                                                                              'alle '
                                                                                                                              'auf '
                                                                                                                              'dieser '
                                                                                                                              'Seite '
                                                                                                                              'genannten '
                                                                                                                              'Dateien '
                                                                                                                              'enthält. '
                                                                                                                              'Deine '
                                                                                                                              'vorhandenen '
                                                                                                                              'Dateien '
                                                                                                                              'bleiben '
                                                                                                                              'erhalten.',
 'Choose another readable folder.': 'Wähle einen anderen lesbaren Ordner.',
 'Choose file': 'Datei auswählen',
 'Choose folder': 'Ordner auswählen',
 'Choose readable games and BIOS folders. Optional source folders must exist and contain the required files listed on the previous pages.': 'Wähle '
                                                                                                                                            'lesbare '
                                                                                                                                            'Spiele- '
                                                                                                                                            'und '
                                                                                                                                            'BIOS-Ordner. '
                                                                                                                                            'Optionale '
                                                                                                                                            'Quellordner '
                                                                                                                                            'müssen '
                                                                                                                                            'vorhanden '
                                                                                                                                            'sein '
                                                                                                                                            'und '
                                                                                                                                            'die '
                                                                                                                                            'auf '
                                                                                                                                            'den '
                                                                                                                                            'vorherigen '
                                                                                                                                            'Seiten '
                                                                                                                                            'genannten '
                                                                                                                                            'Dateien '
                                                                                                                                            'enthalten.',
 'Choose your existing folders. Embercade only reads them; nothing is copied.': 'Wähle die '
                                                                                'bestehenden '
                                                                                'Ordner. Embercade '
                                                                                'liest sie nur; '
                                                                                'nichts wird '
                                                                                'kopiert.',
 'Choose your language before setup. You can change it at any time.': 'Wähle vor der Einrichtung '
                                                                      'deine Sprache. Du kannst '
                                                                      'sie jederzeit ändern.',
 'Close Steam completely and try again. Your other entries are preserved.': 'Beende Steam '
                                                                            'vollständig und '
                                                                            'versuche es erneut. '
                                                                            'Deine anderen '
                                                                            'Einträge bleiben '
                                                                            'erhalten.',
 'Complete': 'Abschluss',
 'Configured; authentication not tested': 'Eingerichtet; Anmeldung nicht geprüft',
 'Continue': 'Weiter',
 'Controller': 'Controller',
 'Controller: ↑/↓ select  ·  A confirm  ·  B back  ·  X use folder': 'Controller: ↑/↓ auswählen  '
                                                                     '·  A bestätigen  ·  B '
                                                                     'zurück  ·  X Ordner '
                                                                     'übernehmen',
 'Could not open terminal': 'Terminal konnte nicht geöffnet werden',
 'Created on first start': 'Wird beim ersten Start erzeugt',
 'Current: {shortcut}': 'Aktuell: {shortcut}',
 'Embercade opens a terminal so you can review and confirm the packages. It closes after success. On failure, the output stays visible until you press Enter.': 'Embercade '
                                                                                                                                                                'öffnet '
                                                                                                                                                                'ein '
                                                                                                                                                                'Terminal, '
                                                                                                                                                                'in '
                                                                                                                                                                'dem '
                                                                                                                                                                'du '
                                                                                                                                                                'die '
                                                                                                                                                                'Pakete '
                                                                                                                                                                'prüfst '
                                                                                                                                                                'und '
                                                                                                                                                                'bestätigst. '
                                                                                                                                                                'Bei '
                                                                                                                                                                'Erfolg '
                                                                                                                                                                'schließt '
                                                                                                                                                                'es '
                                                                                                                                                                'sich. '
                                                                                                                                                                'Bei '
                                                                                                                                                                'Fehlern '
                                                                                                                                                                'bleibt '
                                                                                                                                                                'die '
                                                                                                                                                                'Ausgabe '
                                                                                                                                                                'sichtbar, '
                                                                                                                                                                'bis '
                                                                                                                                                                'du '
                                                                                                                                                                'Enter '
                                                                                                                                                                'drückst.',
 'Existing Embercade settings need attention': 'Vorhandene Embercade-Einstellungen brauchen Hilfe',
 'Finish': 'Fertig',
 'Firmware is still missing. Install it in RPCS3 and try the check again.': 'Die Firmware fehlt '
                                                                            'weiterhin. '
                                                                            'Installiere sie in '
                                                                            'RPCS3 und prüfe '
                                                                            'erneut.',
 'Folder is unreadable': 'Ordner nicht lesbar',
 'Found; select in setup': 'Gefunden; in der Einrichtung auswählen',
 'Games folder': 'Spieleordner',
 'Games: {path}': 'Spiele: {path}',
 'Guide + Start  ·  Desktop': 'Guide + Start  ·  Desktop',
 'Host components: {available}/{total} available': 'Host-Komponenten: {available}/{total} '
                                                   'verfügbar',
 'Host installation completed.': 'Host-Installation abgeschlossen.',
 'Host installation completed. Dependencies have been checked again.': 'Host-Installation '
                                                                       'abgeschlossen. Die '
                                                                       'Abhängigkeiten wurden '
                                                                       'erneut geprüft.',
 'Host installation ended without a result. The terminal may have been closed. Dependencies will be checked again.': 'Host-Installation '
                                                                                                                     'ohne '
                                                                                                                     'Ergebnis '
                                                                                                                     'beendet. '
                                                                                                                     'Das '
                                                                                                                     'Terminal '
                                                                                                                     'wurde '
                                                                                                                     'möglicherweise '
                                                                                                                     'geschlossen. '
                                                                                                                     'Die '
                                                                                                                     'Abhängigkeiten '
                                                                                                                     'werden '
                                                                                                                     'erneut '
                                                                                                                     'geprüft.',
 'Host installation failed (exit {code}). The terminal keeps the diagnostic output. You can retry the installation.': 'Host-Installation '
                                                                                                                      'fehlgeschlagen '
                                                                                                                      '(Exit '
                                                                                                                      '{code}). '
                                                                                                                      'Das '
                                                                                                                      'Terminal '
                                                                                                                      'erhält '
                                                                                                                      'die '
                                                                                                                      'Diagnoseausgabe. '
                                                                                                                      'Du '
                                                                                                                      'kannst '
                                                                                                                      'die '
                                                                                                                      'Installation '
                                                                                                                      'erneut '
                                                                                                                      'versuchen.',
 'Host installation was cancelled.': 'Host-Installation wurde abgebrochen.',
 'Host installation was cancelled. Dependencies have been checked again; you can retry.': 'Host-Installation '
                                                                                          'wurde '
                                                                                          'abgebrochen. '
                                                                                          'Die '
                                                                                          'Abhängigkeiten '
                                                                                          'wurden '
                                                                                          'erneut '
                                                                                          'geprüft; '
                                                                                          'du '
                                                                                          'kannst '
                                                                                          'es '
                                                                                          'erneut '
                                                                                          'versuchen.',
 'Host package installation': 'Host-Paketinstallation',
 'Host package installation failed or was cancelled (exit {code}). Review the package-manager output above before retrying.': 'Host-Paketinstallation '
                                                                                                                              'fehlgeschlagen '
                                                                                                                              'oder '
                                                                                                                              'abgebrochen '
                                                                                                                              '(Exit '
                                                                                                                              '{code}). '
                                                                                                                              'Prüfe '
                                                                                                                              'vor '
                                                                                                                              'dem '
                                                                                                                              'nächsten '
                                                                                                                              'Versuch '
                                                                                                                              'die '
                                                                                                                              'Paketmanager-Ausgabe '
                                                                                                                              'oben.',
 'Host software': 'Host-Software',
 'Host status could not be checked. Please try again.': 'Der Host-Status konnte nicht geprüft '
                                                        'werden. Bitte versuche es erneut.',
 'How would you like to exit a game?': 'Wie möchtest du ein Spiel verlassen?',
 'If you already have shadPS4, select your AppImage. Embercade imports its own copy and preserves your source.': 'Wenn '
                                                                                                                 'du '
                                                                                                                 'shadPS4 '
                                                                                                                 'bereits '
                                                                                                                 'besitzt, '
                                                                                                                 'wähle '
                                                                                                                 'deine '
                                                                                                                 'AppImage. '
                                                                                                                 'Embercade '
                                                                                                                 'übernimmt '
                                                                                                                 'eine '
                                                                                                                 'eigene '
                                                                                                                 'Kopie; '
                                                                                                                 'deine '
                                                                                                                 'Quelle '
                                                                                                                 'bleibt '
                                                                                                                 'unverändert.',
 'Import another folder of RetroArch cores (optional)': 'Weiteren Ordner mit RetroArch-Cores '
                                                        'übernehmen (optional)',
 'Import another folder of emulator AppImages (optional)': 'Weiteren Ordner mit Emulator-AppImages '
                                                           'übernehmen (optional)',
 'In RPCS3, choose File → Install Firmware and select your own PS3UPDAT.PUP. Close RPCS3 when finished. Existing firmware and saves are preserved.': 'Wähle '
                                                                                                                                                     'in '
                                                                                                                                                     'RPCS3 '
                                                                                                                                                     'File '
                                                                                                                                                     '→ '
                                                                                                                                                     'Install '
                                                                                                                                                     'Firmware '
                                                                                                                                                     'und '
                                                                                                                                                     'deine '
                                                                                                                                                     'eigene '
                                                                                                                                                     'PS3UPDAT.PUP. '
                                                                                                                                                     'Schließe '
                                                                                                                                                     'RPCS3 '
                                                                                                                                                     'danach. '
                                                                                                                                                     'Vorhandene '
                                                                                                                                                     'Firmware '
                                                                                                                                                     'und '
                                                                                                                                                     'Spielstände '
                                                                                                                                                     'bleiben '
                                                                                                                                                     'erhalten.',
 'Inspection could not verify the provider': 'Der Provider konnte nicht bestätigt werden',
 'Install PS3 firmware (optional)': 'PS3-Firmware installieren (optional)',
 'Install available repository packages? [y/N] ': 'Verfügbare Repository-Pakete installieren? '
                                                  '[j/N] ',
 'Install missing host software?': 'Fehlende Host-Software installieren?',
 'Install optional host software': 'Host-Software optional installieren',
 'Install selected community packages? [y/N] ': 'Ausgewählte Community-Pakete installieren? [j/N] ',
 'Installable repository packages: {packages}': 'Installierbare Repository-Pakete: {packages}',
 'Invalid or unreadable': 'Ungültig oder nicht lesbar',
 'Language': 'Sprache',
 'Language could not be saved. Check that your settings file is writable. Your existing setup is preserved.': 'Die '
                                                                                                              'Sprache '
                                                                                                              'konnte '
                                                                                                              'nicht '
                                                                                                              'gespeichert '
                                                                                                              'werden. '
                                                                                                              'Prüfe, '
                                                                                                              'ob '
                                                                                                              'deine '
                                                                                                              'Einstellungsdatei '
                                                                                                              'beschreibbar '
                                                                                                              'ist. '
                                                                                                              'Deine '
                                                                                                              'vorhandene '
                                                                                                              'Einrichtung '
                                                                                                              'bleibt '
                                                                                                              'erhalten.',
 'Later': 'Später',
 'Libretro cores: {available}/{total} available': 'Libretro-Cores: {available}/{total} verfügbar',
 'Missing': 'Fehlt',
 'More emulator files': 'Weitere Emulator-Dateien',
 'No': 'Nein',
 'No changes made.': 'Keine Änderungen vorgenommen.',
 'No community packages installed.': 'Keine Community-Pakete installiert.',
 'No further information is available.': 'Keine weiteren Angaben verfügbar.',
 'No packages to install.': 'Keine Pakete zu installieren.',
 'No repository packages installed.': 'Keine Repository-Pakete installiert.',
 'Not configured': 'Nicht eingerichtet',
 'Nothing is downloaded. You can skip this and use the rest of Embercade.': 'Kein Download. Ohne '
                                                                            'Auswahl bleibt die '
                                                                            'übrige Einrichtung '
                                                                            'vollständig nutzbar.',
 'OK': 'OK',
 'Open a desktop terminal and run: embercade bootstrap': 'Öffne auf dem Desktop ein Terminal und '
                                                         'starte: embercade bootstrap',
 'Open the isolated RPCS3 firmware installer?': 'Isolierten RPCS3-Firmware-Installer öffnen?',
 'Optional community packages: {packages}': 'Optionale Community-Pakete: {packages}',
 'PS3 firmware: {status}': 'PS3-Firmware: {status}',
 'PS3, Xbox and PSP firmware and additional files were included in the check.': 'Systemsoftware '
                                                                                'und Zusatzdateien '
                                                                                'für PS3, Xbox und '
                                                                                'PSP wurden '
                                                                                'mitgeprüft.',
 'PSP assets (required for PSP games)': 'PSP-Zusatzdateien (für PSP-Spiele erforderlich)',
 'PSP assets: {path}': 'PSP-Zusatzdateien: {path}',
 'PSP games require the complete official PPSSPP assets folder with ppge_atlas.zim, lang/ and flash0/. PSP games cannot start reliably without it.': 'PSP-Spiele '
                                                                                                                                                     'brauchen '
                                                                                                                                                     'den '
                                                                                                                                                     'vollständigen '
                                                                                                                                                     'offiziellen '
                                                                                                                                                     'PPSSPP-assets-Ordner '
                                                                                                                                                     'mit '
                                                                                                                                                     'ppge_atlas.zim, '
                                                                                                                                                     'lang/ '
                                                                                                                                                     'und '
                                                                                                                                                     'flash0/. '
                                                                                                                                                     'Ohne '
                                                                                                                                                     'ihn '
                                                                                                                                                     'können '
                                                                                                                                                     'PSP-Spiele '
                                                                                                                                                     'nicht '
                                                                                                                                                     'zuverlässig '
                                                                                                                                                     'starten.',
 'PlayStation 4 (optional)': 'PlayStation 4 (optional)',
 'Please check your folders': 'Bitte Ordner prüfen',
 'Prefer development/git packages? [y/N] ': 'Entwicklungs-/Git-Pakete bevorzugen? [j/N] ',
 'Press Enter to close this terminal.': 'Drücke Enter, um dieses Terminal zu schließen.',
 'Previously imported files stay in Embercade. You do not need to select their original folders again.': 'Bereits '
                                                                                                         'übernommene '
                                                                                                         'Dateien '
                                                                                                         'bleiben '
                                                                                                         'in '
                                                                                                         'Embercade. '
                                                                                                         'Die '
                                                                                                         'ursprünglichen '
                                                                                                         'Quellordner '
                                                                                                         'musst '
                                                                                                         'du '
                                                                                                         'nicht '
                                                                                                         'erneut '
                                                                                                         'wählen.',
 'Python runtime': 'Python-Laufzeit',
 'RetroArch cores already imported: {count}': 'RetroArch-Cores bereits übernommen: {count}',
 'Runtime dependencies missing': 'Laufzeit-Abhängigkeiten fehlen',
 'Save and check setup': 'Einrichtung speichern und prüfen',
 'Save language and continue': 'Sprache speichern und weiter',
 'Select + Start  ·  Steam / handheld': 'Select + Start  ·  Steam / Handheld',
 'Select+Start exit bridge': 'Select+Start-Exit-Verbindung',
 'Setup': 'Einrichtung',
 'Setup  ·  {page}': 'Einrichtung  ·  {page}',
 'Setup has been checked. Embercade is ready to start.': 'Die Einrichtung ist geprüft. Embercade '
                                                         'ist startbereit.',
 'Setup needs attention': 'Einrichtung braucht Hilfe',
 'Show Embercade where your files are. Embercade will take care of the rest.': 'Zeig Embercade, wo '
                                                                               'deine Sachen '
                                                                               'liegen. Embercade '
                                                                               'erledigt den Rest.',
 'Show missing host software': 'Fehlende Host-Software anzeigen',
 'Start Embercade': 'Embercade starten',
 'Steam must be fully closed. Your other games and entries will be preserved.': 'Steam muss dafür '
                                                                                'vollständig '
                                                                                'beendet sein. '
                                                                                'Andere Spiele und '
                                                                                'Einträge bleiben '
                                                                                'erhalten.',
 'Steam shortcut saved.': 'Steam-Verknüpfung gespeichert.',
 'System files missing': 'Systemdateien fehlen',
 'Terminal required': 'Terminal erforderlich',
 'The Xenia AppImage has already been imported and configured.': 'Xenia-AppImage bereits '
                                                                 'übernommen und eingerichtet.',
 'The check also examines firmware, emulators, controllers and additional system files.': 'Beim '
                                                                                          'Prüfen '
                                                                                          'werden '
                                                                                          'auch '
                                                                                          'Firmware, '
                                                                                          'Emulatoren, '
                                                                                          'Controller '
                                                                                          'und '
                                                                                          'zusätzliche '
                                                                                          'Systemdateien '
                                                                                          'kontrolliert.',
 'The selected AppImage could not be verified as shadPS4. Choose a readable, supported shadPS4 AppImage.': 'Die '
                                                                                                           'gewählte '
                                                                                                           'AppImage '
                                                                                                           'konnte '
                                                                                                           'nicht '
                                                                                                           'als '
                                                                                                           'shadPS4 '
                                                                                                           'bestätigt '
                                                                                                           'werden. '
                                                                                                           'Wähle '
                                                                                                           'eine '
                                                                                                           'lesbare, '
                                                                                                           'unterstützte '
                                                                                                           'shadPS4-AppImage.',
 'This step could not be completed (exit {code}). Check your folders, file permissions and available disk space, then try again. Your existing setup is preserved.': 'Dieser '
                                                                                                                                                                     'Schritt '
                                                                                                                                                                     'konnte '
                                                                                                                                                                     'nicht '
                                                                                                                                                                     'abgeschlossen '
                                                                                                                                                                     'werden '
                                                                                                                                                                     '(Exit '
                                                                                                                                                                     '{code}). '
                                                                                                                                                                     'Prüfe '
                                                                                                                                                                     'Ordner, '
                                                                                                                                                                     'Dateirechte '
                                                                                                                                                                     'und '
                                                                                                                                                                     'freien '
                                                                                                                                                                     'Speicher '
                                                                                                                                                                     'und '
                                                                                                                                                                     'versuche '
                                                                                                                                                                     'es '
                                                                                                                                                                     'erneut. '
                                                                                                                                                                     'Deine '
                                                                                                                                                                     'vorhandene '
                                                                                                                                                                     'Einrichtung '
                                                                                                                                                                     'bleibt '
                                                                                                                                                                     'erhalten.',
 'Unavailable packages: {packages}': 'Nicht verfügbare Pakete: {packages}',
 'Use selected AppImage': 'Ausgewählte AppImage wählen',
 'Use this folder': 'Diesen Ordner wählen',
 'Welcome': 'Willkommen',
 'Working… Please wait.': 'Wird ausgeführt… Bitte warten.',
 'Xbox EEPROM: {status}': 'Xbox-EEPROM: {status}',
 'Xbox HDD: {status}': 'Xbox-Festplatte: {status}',
 'Xbox firmware: {status}': 'Xbox-Firmware: {status}',
 'Xbox system files (if not set up yet)': 'Xbox-Systemdateien (falls noch nicht eingerichtet)',
 'Xemu requires Complex_4627.bin, mcpx_1.0.bin and xbox_hdd.qcow2. Embercade creates working copies. Xemu generates its EEPROM on first start; an existing Embercade EEPROM is preserved.': 'Xemu '
                                                                                                                                                                                            'braucht '
                                                                                                                                                                                            'Complex_4627.bin, '
                                                                                                                                                                                            'mcpx_1.0.bin '
                                                                                                                                                                                            'und '
                                                                                                                                                                                            'xbox_hdd.qcow2. '
                                                                                                                                                                                            'Embercade '
                                                                                                                                                                                            'legt '
                                                                                                                                                                                            'eigene '
                                                                                                                                                                                            'Arbeitskopien '
                                                                                                                                                                                            'an. '
                                                                                                                                                                                            'Die '
                                                                                                                                                                                            'EEPROM '
                                                                                                                                                                                            'erzeugt '
                                                                                                                                                                                            'Xemu '
                                                                                                                                                                                            'beim '
                                                                                                                                                                                            'ersten '
                                                                                                                                                                                            'Start '
                                                                                                                                                                                            'selbst; '
                                                                                                                                                                                            'eine '
                                                                                                                                                                                            'vorhandene '
                                                                                                                                                                                            'Embercade-EEPROM '
                                                                                                                                                                                            'bleibt '
                                                                                                                                                                                            'erhalten.',
 'Xemu system files are already prepared. You do not need to select their source folder again.': 'Xemu-Systemdateien '
                                                                                                 'bereits '
                                                                                                 'vorbereitet. '
                                                                                                 'Der '
                                                                                                 'Quellordner '
                                                                                                 'muss '
                                                                                                 'nicht '
                                                                                                 'erneut '
                                                                                                 'gewählt '
                                                                                                 'werden.',
 'Xemu system files: {path}': 'Xemu-Systemdateien: {path}',
 'Xenia process scope': 'Xenia-Prozessgruppe',
 'Yes': 'Ja',
 'Your basic configuration is saved. Some components still need attention.': 'Die '
                                                                             'Grundkonfiguration '
                                                                             'ist gespeichert. '
                                                                             'Einige optionale '
                                                                             'Komponenten brauchen '
                                                                             'noch Aufmerksamkeit.',
 'Your existing setup was found. You can check it now or change its settings.': 'Deine vorhandene '
                                                                                'Einrichtung wurde '
                                                                                'erkannt. Du '
                                                                                'kannst sie direkt '
                                                                                'prüfen oder '
                                                                                'bewusst ändern.',
 'Your games and system files': 'Deine Spiele und Systemdateien',
 'Your games, BIOS files and source files will be preserved.': 'Deine Spiele, BIOS-Dateien und '
                                                               'Quelldateien werden nicht '
                                                               'verändert.',
 'Your settings file could not be read. It has not been changed. Please check it or use terminal setup.': 'Deine '
                                                                                                          'Einstellungsdatei '
                                                                                                          'konnte '
                                                                                                          'nicht '
                                                                                                          'gelesen '
                                                                                                          'werden. '
                                                                                                          'Sie '
                                                                                                          'wurde '
                                                                                                          'nicht '
                                                                                                          'geändert. '
                                                                                                          'Bitte '
                                                                                                          'prüfe '
                                                                                                          'sie '
                                                                                                          'oder '
                                                                                                          'verwende '
                                                                                                          'die '
                                                                                                          'Terminal-Einrichtung.',
 'not selected': 'nicht ausgewählt',
 'not selected yet': 'noch nicht gewählt',
 'shadPS4 AppImage (optional)': 'shadPS4-AppImage (optional)',
 'shadPS4: {path}': 'shadPS4: {path}'}


# Final installer pages share the same catalog and formatting contract.
GERMAN.update({'A local AppImage copy keeps your launcher working when the original drive is disconnected. Existing classic installations keep their verified launcher.': 'Eine '
                                                                                                                                                            'lokale '
                                                                                                                                                            'AppImage-Kopie '
                                                                                                                                                            'funktioniert '
                                                                                                                                                            'auch '
                                                                                                                                                            'ohne '
                                                                                                                                                            'das '
                                                                                                                                                            'ursprüngliche '
                                                                                                                                                            'Laufwerk. '
                                                                                                                                                            'Vorhandene '
                                                                                                                                                            'klassische '
                                                                                                                                                            'Installationen '
                                                                                                                                                            'behalten '
                                                                                                                                                            'ihren '
                                                                                                                                                            'geprüften '
                                                                                                                                                            'Starter.',
 'A valid EEPROM is required. Embercade saves a backup and preserves the HDD key and console identity.': 'Eine '
                                                                                                         'gültige '
                                                                                                         'EEPROM '
                                                                                                         'ist '
                                                                                                         'erforderlich. '
                                                                                                         'Embercade '
                                                                                                         'legt '
                                                                                                         'eine '
                                                                                                         'Sicherung '
                                                                                                         'an '
                                                                                                         'und '
                                                                                                         'erhält '
                                                                                                         'Festplattenschlüssel '
                                                                                                         'und '
                                                                                                         'Konsolenidentität.',
 'Add to Steam with Embercade artwork': 'Mit Embercade-Artwork zu Steam hinzufügen',
 'Application menu · Games (recommended)': 'Anwendungsmenü · Spiele (empfohlen)',
 'Check the Desktop folder and free space. Existing files changed outside Embercade are preserved. Adjust your choices and retry, or turn off menu and desktop integration to continue.': 'Prüfe '
                                                                                                                                                                                          'den '
                                                                                                                                                                                          'Desktop-Ordner '
                                                                                                                                                                                          'und '
                                                                                                                                                                                          'den '
                                                                                                                                                                                          'freien '
                                                                                                                                                                                          'Speicherplatz. '
                                                                                                                                                                                          'Außerhalb '
                                                                                                                                                                                          'von '
                                                                                                                                                                                          'Embercade '
                                                                                                                                                                                          'geänderte '
                                                                                                                                                                                          'Dateien '
                                                                                                                                                                                          'bleiben '
                                                                                                                                                                                          'erhalten. '
                                                                                                                                                                                          'Passe '
                                                                                                                                                                                          'die '
                                                                                                                                                                                          'Auswahl '
                                                                                                                                                                                          'an '
                                                                                                                                                                                          'und '
                                                                                                                                                                                          'versuche '
                                                                                                                                                                                          'es '
                                                                                                                                                                                          'erneut, '
                                                                                                                                                                                          'oder '
                                                                                                                                                                                          'deaktiviere '
                                                                                                                                                                                          'Menü '
                                                                                                                                                                                          'und '
                                                                                                                                                                                          'Desktop-Verknüpfung, '
                                                                                                                                                                                          'um '
                                                                                                                                                                                          'fortzufahren.',
 'Check your connection and PUP file, close RPCS3 and try again. Existing firmware is never replaced. If automatic download fails, select the official PUP downloaded in your browser.': 'Prüfe '
                                                                                                                                                                                         'Verbindung '
                                                                                                                                                                                         'und '
                                                                                                                                                                                         'PUP-Datei, '
                                                                                                                                                                                         'schließe '
                                                                                                                                                                                         'RPCS3 '
                                                                                                                                                                                         'und '
                                                                                                                                                                                         'versuche '
                                                                                                                                                                                         'es '
                                                                                                                                                                                         'erneut. '
                                                                                                                                                                                         'Vorhandene '
                                                                                                                                                                                         'Firmware '
                                                                                                                                                                                         'wird '
                                                                                                                                                                                         'nicht '
                                                                                                                                                                                         'ersetzt. '
                                                                                                                                                                                         'Falls '
                                                                                                                                                                                         'der '
                                                                                                                                                                                         'automatische '
                                                                                                                                                                                         'Download '
                                                                                                                                                                                         'scheitert, '
                                                                                                                                                                                         'wähle '
                                                                                                                                                                                         'die '
                                                                                                                                                                                         'im '
                                                                                                                                                                                         'Browser '
                                                                                                                                                                                         'heruntergeladene '
                                                                                                                                                                                         'offizielle '
                                                                                                                                                                                         'PUP-Datei.',
 'Choose a default EEPROM, import your own, or edit console settings. Existing console identity and HDD keys are preserved.': 'Erzeuge '
                                                                                                                              'eine '
                                                                                                                              'Standard-EEPROM, '
                                                                                                                              'importiere '
                                                                                                                              'deine '
                                                                                                                              'eigene '
                                                                                                                              'Datei '
                                                                                                                              'oder '
                                                                                                                              'bearbeite '
                                                                                                                              'die '
                                                                                                                              'Konsoleneinstellungen. '
                                                                                                                              'Vorhandene '
                                                                                                                              'Konsolenidentität '
                                                                                                                              'und '
                                                                                                                              'Festplattenschlüssel '
                                                                                                                              'bleiben '
                                                                                                                              'erhalten.',
 'Close Xemu and check the selected file. Editing requires an authenticated 256-byte EEPROM with valid checksums. Create a default EEPROM or import a valid file, then retry. Existing data is preserved.': 'Schließe '
                                                                                                                                                                                                            'Xemu '
                                                                                                                                                                                                            'und '
                                                                                                                                                                                                            'prüfe '
                                                                                                                                                                                                            'die '
                                                                                                                                                                                                            'ausgewählte '
                                                                                                                                                                                                            'Datei. '
                                                                                                                                                                                                            'Die '
                                                                                                                                                                                                            'Bearbeitung '
                                                                                                                                                                                                            'benötigt '
                                                                                                                                                                                                            'eine '
                                                                                                                                                                                                            'authentifizierte '
                                                                                                                                                                                                            'EEPROM '
                                                                                                                                                                                                            'mit '
                                                                                                                                                                                                            '256 '
                                                                                                                                                                                                            'Byte '
                                                                                                                                                                                                            'und '
                                                                                                                                                                                                            'gültigen '
                                                                                                                                                                                                            'Prüfsummen. '
                                                                                                                                                                                                            'Erzeuge '
                                                                                                                                                                                                            'eine '
                                                                                                                                                                                                            'Standard-EEPROM '
                                                                                                                                                                                                            'oder '
                                                                                                                                                                                                            'importiere '
                                                                                                                                                                                                            'eine '
                                                                                                                                                                                                            'gültige '
                                                                                                                                                                                                            'Datei '
                                                                                                                                                                                                            'und '
                                                                                                                                                                                                            'versuche '
                                                                                                                                                                                                            'es '
                                                                                                                                                                                                            'erneut. '
                                                                                                                                                                                                            'Vorhandene '
                                                                                                                                                                                                            'Daten '
                                                                                                                                                                                                            'bleiben '
                                                                                                                                                                                                            'erhalten.',
 'Components for your current collection appear first. Other emulators are optional.': 'Komponenten für '
                                                                                       'deine aktuelle '
                                                                                       'Sammlung stehen '
                                                                                       'zuerst. Andere '
                                                                                       'Emulatoren sind '
                                                                                       'optional.',
 'Console language': 'Konsolensprache',
 'Console settings: language {language}, region {region}, video {video}': 'Konsoleneinstellungen: Sprache '
                                                                          '{language}, Region {region}, '
                                                                          'Video {video}',
 'Create default EEPROM with Xemu': 'Standard-EEPROM mit Xemu erzeugen',
 'Desktop integration': 'Desktop-Integration',
 'Desktop integration is available from the installed application or AppImage. You can continue setup here.': 'Die '
                                                                                                              'Desktop-Integration '
                                                                                                              'steht '
                                                                                                              'in '
                                                                                                              'der '
                                                                                                              'installierten '
                                                                                                              'Anwendung '
                                                                                                              'oder '
                                                                                                              'im '
                                                                                                              'AppImage '
                                                                                                              'bereit. '
                                                                                                              'Du '
                                                                                                              'kannst '
                                                                                                              'die '
                                                                                                              'Einrichtung '
                                                                                                              'hier '
                                                                                                              'fortsetzen.',
 'Desktop integration needs attention': 'Desktop-Integration prüfen',
 'Desktop shortcut': 'Desktop-Verknüpfung',
 "Download PS3UPDAT.PUP from the official PlayStation support page and install it with RPCS3? Firmware is subject to Sony's terms. Embercade does not distribute it. Existing firmware is preserved.": 'PS3UPDAT.PUP '
                                                                                                                                                                                                       'von '
                                                                                                                                                                                                       'der '
                                                                                                                                                                                                       'offiziellen '
                                                                                                                                                                                                       'PlayStation-Supportseite '
                                                                                                                                                                                                       'herunterladen '
                                                                                                                                                                                                       'und '
                                                                                                                                                                                                       'mit '
                                                                                                                                                                                                       'RPCS3 '
                                                                                                                                                                                                       'installieren? '
                                                                                                                                                                                                       'Es '
                                                                                                                                                                                                       'gelten '
                                                                                                                                                                                                       'die '
                                                                                                                                                                                                       'Bedingungen '
                                                                                                                                                                                                       'von '
                                                                                                                                                                                                       'Sony. '
                                                                                                                                                                                                       'Embercade '
                                                                                                                                                                                                       'liefert '
                                                                                                                                                                                                       'keine '
                                                                                                                                                                                                       'Firmware '
                                                                                                                                                                                                       'mit. '
                                                                                                                                                                                                       'Vorhandene '
                                                                                                                                                                                                       'Firmware '
                                                                                                                                                                                                       'bleibt '
                                                                                                                                                                                                       'erhalten.',
 'Download and install official firmware': 'Offizielle Firmware laden und installieren',
 'Download official PS3 firmware?': 'Offizielle PS3-Firmware herunterladen?',
 'Embercade uses its own Xbox EEPROM. Your normal Xemu profile stays separate. Close Xemu before changing these settings.': 'Embercade '
                                                                                                                            'verwendet '
                                                                                                                            'eine '
                                                                                                                            'eigene '
                                                                                                                            'Xbox-EEPROM. '
                                                                                                                            'Dein '
                                                                                                                            'normales '
                                                                                                                            'Xemu-Profil '
                                                                                                                            'bleibt '
                                                                                                                            'getrennt. '
                                                                                                                            'Schließe '
                                                                                                                            'Xemu '
                                                                                                                            'vor '
                                                                                                                            'Änderungen '
                                                                                                                            'an '
                                                                                                                            'diesen '
                                                                                                                            'Einstellungen.',
 'English': 'Englisch',
 'Error': 'Fehler',
 'Europe': 'Europa',
 'Existing firmware is preserved. Close RPCS3 when its installation has finished to return here.': 'Vorhandene '
                                                                                                   'Firmware '
                                                                                                   'bleibt '
                                                                                                   'erhalten. '
                                                                                                   'Schließe '
                                                                                                   'RPCS3 '
                                                                                                   'nach der '
                                                                                                   'Installation, '
                                                                                                   'um '
                                                                                                   'hierher '
                                                                                                   'zurückzukehren.',
 'Game region': 'Spielregion',
 'Games and BIOS': 'Spiele und BIOS',
 'German': 'Deutsch',
 'Import EEPROM': 'EEPROM importieren',
 'Import EEPROM?': 'EEPROM importieren?',
 'Import existing installed firmware': 'Vorhandene installierte Firmware importieren',
 "Install official PS3 firmware in Embercade's isolated RPCS3 profile. You can also select your own PUP or skip this step.": 'Installiere '
                                                                                                                             'offizielle '
                                                                                                                             'PS3-Firmware '
                                                                                                                             'im '
                                                                                                                             'isolierten '
                                                                                                                             'RPCS3-Profil '
                                                                                                                             'von '
                                                                                                                             'Embercade. '
                                                                                                                             'Du '
                                                                                                                             'kannst '
                                                                                                                             'auch '
                                                                                                                             'eine '
                                                                                                                             'eigene '
                                                                                                                             'PUP-Datei '
                                                                                                                             'auswählen '
                                                                                                                             'oder '
                                                                                                                             'diesen '
                                                                                                                             'Schritt '
                                                                                                                             'überspringen.',
 'Install selected firmware': 'Ausgewählte Firmware installieren',
 'Install selected firmware?': 'Ausgewählte Firmware installieren?',
 'Japan': 'Japan',
 'Keep Embercade easy to find in Games, on your desktop or in Steam.': 'Finde Embercade bequem unter Spiele, '
                                                                       'auf deinem Desktop oder in Steam.',
 'Keep a stable local AppImage copy': 'Dauerhafte lokale AppImage-Kopie anlegen',
 'Keep current': 'Beibehalten',
 'NTSC-J': 'NTSC-J',
 'NTSC-M': 'NTSC-M',
 'North America': 'Nordamerika',
 'Optional': 'Optional',
 'Other': 'Andere',
 'PAL': 'PAL',
 "PS3 firmware is installed in Embercade's isolated profile.": 'PS3-Firmware ist im isolierten '
                                                               'Embercade-Profil installiert.',
 'PS3 setup needs attention': 'PS3-Einrichtung prüfen',
 'PS3UPDAT.PUP file': 'PS3UPDAT.PUP-Datei',
 'PlayStation 3': 'PlayStation 3',
 'PlayStation 3 firmware': 'PlayStation-3-Firmware',
 'RPCS3 will validate and install this PUP in a temporary Embercade profile. Only a successful installation is copied to your isolated profile. Existing firmware is preserved.': 'RPCS3 '
                                                                                                                                                                                  'prüft '
                                                                                                                                                                                  'und '
                                                                                                                                                                                  'installiert '
                                                                                                                                                                                  'diese '
                                                                                                                                                                                  'PUP '
                                                                                                                                                                                  'in '
                                                                                                                                                                                  'einem '
                                                                                                                                                                                  'temporären '
                                                                                                                                                                                  'Embercade-Profil. '
                                                                                                                                                                                  'Erst '
                                                                                                                                                                                  'eine '
                                                                                                                                                                                  'erfolgreiche '
                                                                                                                                                                                  'Installation '
                                                                                                                                                                                  'wird '
                                                                                                                                                                                  'in '
                                                                                                                                                                                  'dein '
                                                                                                                                                                                  'isoliertes '
                                                                                                                                                                                  'Profil '
                                                                                                                                                                                  'übernommen. '
                                                                                                                                                                                  'Vorhandene '
                                                                                                                                                                                  'Firmware '
                                                                                                                                                                                  'bleibt '
                                                                                                                                                                                  'erhalten.',
 'Ready': 'Bereit',
 'Refresh checks': 'Prüfung aktualisieren',
 'Save console settings': 'Konsoleneinstellungen speichern',
 'Save console settings?': 'Konsoleneinstellungen speichern?',
 'Select a valid 256-byte EEPROM file first.': 'Wähle zuerst eine gültige EEPROM-Datei mit 256 Byte.',
 'Select your PS3UPDAT.PUP file first.': 'Wähle zuerst deine PS3UPDAT.PUP-Datei.',
 'Setup required': 'Einrichtung erforderlich',
 'Show details': 'Details anzeigen',
 'System checks': 'Systemprüfung',
 'Use this file': 'Diese Datei verwenden',
 'Video standard': 'Videostandard',
 'Xbox': 'Xbox',
 'Xbox EEPROM validated and saved. Any replaced EEPROM has a backup beside it.': 'Xbox-EEPROM geprüft und '
                                                                                 'gespeichert. Jede ersetzte '
                                                                                 'EEPROM wurde im selben '
                                                                                 'Ordner gesichert.',
 'Xbox console settings': 'Xbox-Konsoleneinstellungen',
 'Xbox setup needs attention': 'Xbox-Einrichtung prüfen',
 'Your EEPROM file (optional)': 'Deine EEPROM-Datei (optional)',
 'Your existing Embercade EEPROM will be backed up before replacement. The selected source file stays unchanged.': 'Deine '
                                                                                                                   'vorhandene '
                                                                                                                   'Embercade-EEPROM '
                                                                                                                   'wird '
                                                                                                                   'vor '
                                                                                                                   'dem '
                                                                                                                   'Ersetzen '
                                                                                                                   'gesichert. '
                                                                                                                   'Die '
                                                                                                                   'ausgewählte '
                                                                                                                   'Quelldatei '
                                                                                                                   'bleibt '
                                                                                                                   'unverändert.',
 'Your setup checks passed. Start Embercade to check each game and its BIOS requirements.': 'Die '
                                                                                            'Einrichtungsprüfungen '
                                                                                            'sind bestanden. '
                                                                                            'Starte '
                                                                                            'Embercade, um '
                                                                                            'jedes Spiel und '
                                                                                            'seine '
                                                                                            'BIOS-Anforderungen '
                                                                                            'zu prüfen.',
 '{component}: {status}': '{component}: {status}'})
GERMAN.update({
    "Application runtime": "Anwendungs-Laufzeit",
    "ELF inspection": "Laufzeit- und ABI-Prüfung",
    "BIOS verification": "BIOS-Prüfung",
    "PSP assets": "PSP-Systemdateien",
    "Xbox language and region are stored in Embercade's own EEPROM. You can import or edit it on the Xbox page.": "Xbox-Sprache und Region liegen in Embercades eigener EEPROM. Du kannst sie im Xbox-Schritt importieren oder bearbeiten.",
})

GERMAN.update({
'Choose a default EEPROM, import your own, or edit console settings. Settings edits preserve console identity and HDD keys.': 'Erzeuge eine Standard-EEPROM, importiere deine eigene Datei oder bearbeite die Konsoleneinstellungen. Bei Einstellungsänderungen bleiben Konsolenidentität und Festplattenschlüssel erhalten.',
'Import replaces the whole EEPROM, including its console identity and HDD key. Your existing EEPROM is backed up; the HDD image and selected source file stay unchanged.': 'Ein Import ersetzt die gesamte EEPROM einschließlich Konsolenidentität und Festplattenschlüssel. Deine vorhandene EEPROM wird gesichert; das Festplattenabbild und die ausgewählte Quelldatei bleiben unverändert.',
})

GERMAN.update({
    'Adjust the controller driver?':
        'Controller-Treiber anpassen?',
    'Adjusting the driver and reconnecting controllers…':
        'Treiber wird angepasst und Controller werden neu verbunden…',
    'Administrator authentication is unavailable or failed. Use Back/Select + Start or retry in your desktop session.':
        'Die Administrator-Bestätigung ist nicht verfügbar oder fehlgeschlagen. Nutze Back/Select + Start oder versuche es in deiner Desktop-Sitzung erneut.',
    'Administrator authentication was cancelled. No driver change was requested.':
        'Die Administrator-Bestätigung wurde abgebrochen. Es wurde keine Treiberänderung angefordert.',
    'An existing or modified system setting cannot be safely replaced or undone by Embercade. It has been preserved. Use Back/Select + Start or review the driver configuration.':
        'Eine vorhandene oder nachträglich geänderte Systemeinstellung kann von Embercade nicht sicher ersetzt oder zurückgenommen werden. Sie bleibt erhalten. Nutze Back/Select + Start oder prüfe die Treiberkonfiguration.',
    'Another driver adjustment is running. Wait for it to finish, then refresh the check.':
        'Eine andere Treiberanpassung läuft bereits. Warte auf deren Abschluss und aktualisiere danach die Prüfung.',
    'Back/Select + Start':
        'Back/Select + Start',
    'Back/Select + Start does not require changing xpadneo.':
        'Für Back/Select + Start muss xpadneo nicht geändert werden.',
    'Choose your exit combination, check compatibility and try it here.':
        'Wähle deine Exit-Kombination, prüfe die Kompatibilität und teste sie hier.',
    'Combination detected. Release all buttons to finish.':
        'Kombination erkannt. Lass zum Abschluss alle Tasten los.',
    'Continue without a live test?':
        'Ohne Live-Test fortfahren?',
    'Controller & Hotkeys':
        'Controller & Hotkeys',
    'Controller settings need attention':
        'Controller-Einstellungen prüfen',
    'Controller: {name}':
        'Controller: {name}',
    'Enable Guide + Start compatibility…':
        'Kompatibilität für Guide + Start herstellen…',
    'Exit combination detected and released.':
        'Exit-Kombination erkannt und alle Tasten losgelassen.',
    'Exit combination not detected':
        'Exit-Kombination nicht erkannt',
    'Guide + Start':
        'Guide + Start',
    'Hold {shortcut} together for a moment.':
        'Halte {shortcut} einen Moment gleichzeitig gedrückt.',
    'Keep holding both buttons…':
        'Halte beide Tasten noch kurz gedrückt…',
    'No active xpadneo driver was found. Other controllers keep their existing setup.':
        'Kein aktiver xpadneo-Treiber gefunden. Bei anderen Controllern bleibt die bisherige Einrichtung erhalten.',
    'No controller connected. Switch it on to continue.':
        'Kein Controller verbunden. Schalte ihn ein, um fortzufahren.',
    'No sustained combination was detected within 30 seconds. Check the driver status, reconnect the controller and retry, or choose Back/Select + Start.':
        'Innerhalb von 30 Sekunden wurde keine gehaltene Tastenkombination erkannt. Prüfe den Treiberstatus, verbinde den Controller neu und versuche es erneut oder wähle Back/Select + Start.',
    'Possible hotkey conflict: xpadneo can intercept the Guide button.':
        'Möglicher Hotkey-Konflikt: xpadneo kann die Guide-Taste abfangen.',
    'Refresh controller check':
        'Controller-Prüfung aktualisieren',
    'Release all controller buttons to begin.':
        'Lass zum Start alle Controller-Tasten los.',
    "Restore the xpadneo setting saved before Embercade's adjustment? All affected connected controllers will briefly disconnect first, then reconnect. Guide-based special functions may return and Guide + Start may stop working. Administrator authentication is required. Close running games first.":
        'Die vor Embercades Anpassung gespeicherte xpadneo-Einstellung wiederherstellen? Alle betroffenen verbundenen Controller werden zuerst kurz getrennt und danach neu verbunden. Guide-Sonderfunktionen können wieder aktiv werden und Guide + Start kann dadurch ausfallen. Eine Administrator-Bestätigung ist nötig. Schließe vorher laufende Spiele.',
    'Test exit combination':
        'Exit-Kombination testen',
    'The affected controllers could not all be safely identified or disconnected. The driver was not changed. Reconnect them and retry, or use Back/Select + Start.':
        'Nicht alle betroffenen Controller konnten sicher erkannt oder getrennt werden. Der Treiber wurde nicht geändert. Verbinde sie neu und versuche es erneut oder nutze Back/Select + Start.',
    'The driver adjustment did not finish reliably. Refresh the check, switch affected controllers off and on, and retry. Back/Select + Start remains available.':
        'Die Treiberanpassung konnte nicht zuverlässig abgeschlossen werden. Aktualisiere die Prüfung, schalte betroffene Controller aus und wieder ein und versuche es erneut. Back/Select + Start steht weiterhin zur Verfügung.',
    'The driver adjustment is active. Controllers were safely reconnected. Test the exit combination now.':
        'Die Treiberanpassung ist aktiv. Die Controller wurden sicher neu verbunden. Teste jetzt die Exit-Kombination.',
    'The driver setting changed, but a controller has not reconnected. Switch affected controllers off and on, refresh the check and run the live test. Do not assume the exit shortcut works yet.':
        'Die Treibereinstellung wurde geändert, aber ein Controller ist noch nicht wieder verbunden. Schalte betroffene Controller aus und wieder ein, aktualisiere die Prüfung und starte den Live-Test. Die Exit-Kombination ist noch nicht bestätigt.',
    'The exit combination could not be saved. Your existing setup is preserved. Check file permissions and try again.':
        'Die Exit-Kombination konnte nicht gespeichert werden. Deine vorhandene Einrichtung bleibt erhalten. Prüfe die Dateirechte und versuche es erneut.',
    'The exit combination has not been tested in this session.':
        'Die Exit-Kombination wurde in dieser Sitzung noch nicht getestet.',
    'The previous driver setting was restored. Test your selected exit combination again.':
        'Die vorherige Treibereinstellung wurde wiederhergestellt. Teste deine gewählte Exit-Kombination erneut.',
    'The required driver or Bluetooth service is unavailable. Refresh the check after connecting your controller, or use Back/Select + Start.':
        'Der benötigte Treiber oder Bluetooth-Dienst ist nicht verfügbar. Verbinde deinen Controller und aktualisiere die Prüfung oder nutze Back/Select + Start.',
    'The selected exit combination has not been verified. You can test it now or return to Controller & Hotkeys later. Continue anyway?':
        'Die gewählte Exit-Kombination wurde noch nicht geprüft. Du kannst sie jetzt testen oder später zu Controller & Hotkeys zurückkehren. Trotzdem fortfahren?',
    'The test checks the controller shown in the dialog. Then test exiting a real game from Player 1.':
        'Der Test prüft den im Dialog angezeigten Controller. Teste danach als Spieler 1 das Beenden eines echten Spiels.',
    'The xpadneo Guide special mode is disabled.':
        'Der xpadneo-Sondermodus für Guide ist deaktiviert.',
    "This changes a system-wide xpadneo setting for all controllers using that driver. Guide-based mouse and profile switching will be disabled. All affected connected controllers will briefly disconnect before the change, clearing virtual mouse buttons, and then reconnect. Close running games first. Administrator authentication is required. You can undo Embercade's change here. Continue?":
        'Dies ändert eine systemweite xpadneo-Einstellung für alle Controller mit diesem Treiber. Maus- und Profilumschaltung über Guide werden deaktiviert. Alle betroffenen verbundenen Controller werden vor der Änderung kurz getrennt, damit virtuelle Maustasten freigegeben werden, und danach neu verbunden. Schließe vorher laufende Spiele. Die Änderung benötigt eine Administrator-Bestätigung und kann hier rückgängig gemacht werden. Fortfahren?',
    "Undo Embercade's driver adjustment…":
        'Embercades Treiberanpassung rückgängig machen…',
    'Use Back/Select + Start, or approve the driver adjustment below.':
        'Nutze Back/Select + Start oder bestätige unten die Treiberanpassung.',
    '{name} · Bluetooth · xpadneo':
        '{name} · Bluetooth · xpadneo',
})

GERMAN.update({
    "Existing system settings are preserved. Only changes recorded by this installer can be undone here.":
        "Vorhandene Systemeinstellungen bleiben erhalten. Hier können nur Änderungen dieses Installers rückgängig gemacht werden.",
    "Automatic driver adjustment is unavailable. You can use Back/Select + Start.":
        "Die automatische Treiberanpassung ist nicht verfügbar. Du kannst Back/Select + Start verwenden.",
})

GERMAN.update({
    "A previous driver adjustment is incomplete. Undo it before trying again.":
        "Eine vorherige Treiberanpassung ist unvollständig. Mache sie rückgängig, bevor du es erneut versuchst.",
    "A controller has not reconnected. Switch affected controllers off and on, refresh the driver check and run the live test. Do not assume the driver adjustment or exit shortcut is ready yet.":
        "Ein Controller ist noch nicht wieder verbunden. Schalte betroffene Controller aus und wieder ein, aktualisiere die Treiberprüfung und starte den Live-Test. Treiberanpassung und Exit-Kombination sind noch nicht als bereit bestätigt.",
})

def system_language(environment: Mapping[str, str] | None = None) -> str:
    env = os.environ if environment is None else environment
    locale = next((env[key] for key in ("LC_ALL", "LC_MESSAGES", "LANG") if env.get(key)), "en")
    return "de" if locale.split("_", 1)[0].split("-", 1)[0].lower() == "de" else "en"


class Translator:
    def __init__(self, language: str):
        if language not in SUPPORTED_LANGUAGES:
            raise ValueError("Unsupported installer language")
        self.language = language

    def __call__(self, message: str, **fields) -> str:
        text = GERMAN.get(message, message) if self.language == "de" else message
        return text.format(**fields) if fields else text

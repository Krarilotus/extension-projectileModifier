# Custom Projectiles 1.5.0

Geschosse, Salvenstärken und automatische Schussintervalle für alle 77 Einheitentypen einstellen. Katapulte können Mangonelsteine verschießen; Belagerungstürme und Nahkämpfer können einen automatischen Fernkampfangriff erhalten.

vanilla-projectiles.yml aus dem Modul-ZIP nach ucp/resources/custom-projectiles/ kopieren, dort bearbeiten und hier auswählen. Ausgelassene Einstellungen bleiben unverändert; ein leerer Pfad bewirkt keine Änderungen. Die UCP-Regeln für erforderliche und vorgeschlagene Werte gelten für die gesamte Dateiauswahl. Nach Änderungen das Spiel neu starten.

Benötigt UCP 3.0.7+, map-extensions 1.x und Crusader/Extreme 1.41. Alle 33 Einstellungen und 77 Einheitennamen sind in vanilla-projectiles.yml und README.md dokumentiert. Lokale Testversion; die Abnahme im Spiel steht noch aus.

Genauigkeit: inaccuracy nutzt ganze native Koordinateneinheiten: 1 = 1/8 Kachel, 8 = 1 Kachel. 0 entfernt zufällige Zielfehler; Weglassen erhält die ursprüngliche Genauigkeit. spread wirkt separat.

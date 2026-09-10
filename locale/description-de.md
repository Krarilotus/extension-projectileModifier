# Projectile Modifier

Geschosse, Salvenstärken und automatische Schussintervalle für alle 77 Einheitentypen einstellen. Katapulte können Mangonelsteine verschießen; Belagerungstürme und Nahkämpfer können einen automatischen Fernkampfangriff erhalten.

**Balance Changes → Geschosse**

Eine Gruppe und dann eine Einheit aufklappen. Das Schwert-Kontrollkästchen aktiviert eine Zahlenänderung; die aufgeklappte Einstellung zeigt ihre Hilfe. Deaktivierte Einstellungen behalten Dateiwert oder ursprüngliches Verhalten bei. Das Spiel neu starten, um Änderungen anzuwenden.

Aktiviert automatisches Feuer, auch für Nahkämpfer und Belagerungstürme. Ersetzt ursprüngliche Schüsse, sofern die Unterdrückung nicht ausdrücklich ausgeschaltet wird. Nutzt das ursprüngliche Geschoss oder sonst Pfeile. Ein Tick ist ein Simulationsschritt, keine Millisekunde.

Ziele für den Intervallangriff. Einheiten und Gebäude schließen Verbündete aus. Mauern schließen eigene Mauern ein. Eigene Prioritätslisten sind in der YAML-Datei möglich.

Eine YAML-Vorlage für erweiterte Einstellungen zu Bewegung, verzögerten Salven, Genauigkeit, Höhe und Animation laden. Aktivierte Regler unten überschreiben ihre Werte. Ohne Datei sind die üblichen Einstellungen verfügbar. Beispiele und vollständige Tabelle stehen in README.md; das Editorschema heißt projectile-config.schema.json.

Benötigt UCP 3.0.7+, map-extensions 1.x und Crusader/Extreme 1.41. Timer und ausstehende Salven werden gespeichert; zum Laden sind übereinstimmende Einstellungen erforderlich. Diese unsignierte Testversion 1.3.2 basiert auf Monsterfishs 1.2.0. Abnahmetests im Spiel, im Mehrspielerbetrieb und mit dem Recorder stehen noch aus; siehe VALIDATION.md. Die Entwicklerreferenz ist auf Englisch.

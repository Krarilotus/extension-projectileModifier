# Custom Projectiles 1.8.6

Alle 77 Einheitentypen per YAML einstellen. Normale Munition und Kühe sind unabhängig. Intervalle beachten unterstützte Schussanimationen; inaccuracy nutzt native Einheiten: 1 = 1/8 Feld, 8 = 1 Feld, 0 = genaues Zielen.

Die Mindestgröße von Zielgruppen gilt nur für die KI; menschliche Angriffsbefehle bleiben möglich.

Die vollständige vanilla-projectiles.yml aus der ZIP kopieren, bearbeiten und auswählen. native erhält die Spielregeln; ein leerer Pfad ändert nichts. auto_targeting: false erlaubt nur manuelle Angriffsbefehle. strict_range: false stellt gerundete Reichweitenprüfungen wieder her; turn_before_shot: false deaktiviert die Drehkorrektur. Erforderlich/empfohlen gilt für die gesamte Dateiauswahl. Nach Änderungen neu starten.

Eigene Grafik: unter projectiles einen Namen mit inherits und sprites anlegen (vollständige passende GM1-Datei). Dekorationen unter decorations und Einheitenregeln unter near_decorations definieren; über die Feuerkorb-Schaltfläche bauen. Formate: README.md und examples/custom-sprites-and-decorations.yml. Auf geeigneten Mauern oder Türmen bauen; Herrenhäuser unterstützen keine Feuerkörbe.

Benötigt UCP 3.0.7+, Crusader/Extreme 1.41 und die Modulabhängigkeiten. Testversion; siehe VALIDATION.md.

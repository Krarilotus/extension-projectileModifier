# Custom Projectiles 1.8.16

range begrenzt die Zielentfernung in Feldern, auch bei nativer Nachladezeit. spread und inaccuracy können Einschläge außerhalb dieses Radius verursachen. strict_range: false deaktiviert die manuelle Reichweitenkorrektur.

Ersatzgeschosse auf große Distanz: projectile_physics: {firethrower_pot: {mode: fixed_angle, angle: 30}} lässt das Spiel die Startgeschwindigkeit berechnen. Benötigt aktiven Rebalancer 1.1.3+ mit Balance-Konfiguration. Global je Typ, auch für Sprite-Varianten; native erhält bestehende Werte. Zielreichweite und Kollisionen gelten weiter.

Spielwerte können vor dem Laden geändert werden; alte Modul-Schusswarteschlangen und Zeitgeber werden zurückgesetzt. Definitionen eigener Grafiken müssen gleich bleiben. allow_config_changes_on_load: false verlangt die ursprünglichen Einstellungen. strict_range: false deaktiviert auch die neue Reichweitenprüfung manueller Schüsse.

Automatische Munition: Ziellisten unter unit_groups anlegen, beim Schützen ammo_by_target.groups: {siege: regular} oder ammo_by_target.units: {Monk: cow} setzen. Einzelne Typen haben Vorrang; andere Ziele bleiben unverändert. Intervall nötig; native entfernt Regeln. Reconquista-Beispiel enthalten.

Alle 77 Einheitentypen per YAML einstellen. Normale Munition und Kühe sind unabhängig. Intervalle beachten unterstützte Schussanimationen; inaccuracy nutzt native Einheiten: 1 = 1/8 Feld, 8 = 1 Feld, 0 = genaues Zielen.

Die Mindestgröße von Zielgruppen gilt nur für die KI; menschliche Angriffsbefehle bleiben möglich. Bei automatischen Einheitenzielen bewertet target_bias_tiles: {Monk: 3} Mönche im nativen Wert um bis zu drei Felder näher; Reichweite und übrige Spielregeln gelten weiter.

Die vollständige vanilla-projectiles.yml aus der ZIP kopieren, bearbeiten und auswählen. native erhält die Spielregeln; ein leerer Pfad ändert nichts. auto_targeting: false erlaubt nur manuelle Angriffsbefehle. strict_range: false stellt gerundete Reichweitenprüfungen wieder her; turn_before_shot: false deaktiviert die Drehkorrektur. Erforderlich/empfohlen gilt für die gesamte Dateiauswahl. Nach Änderungen neu starten.

Eigene Grafik: unter projectiles einen Namen mit inherits und sprites anlegen (vollständige passende GM1-Datei). Dekorationen unter decorations und Einheitenregeln unter near_decorations definieren; über die Feuerkorb-Schaltfläche bauen. Formate: README.md und examples/custom-sprites-and-decorations.yml. Auf geeigneten Mauern oder Türmen bauen; Herrenhäuser unterstützen keine Feuerkörbe.

Benötigt UCP 3.0.7+, Crusader/Extreme 1.41 und die Modulabhängigkeiten. Testversion; siehe VALIDATION.md.

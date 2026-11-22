# Custom Projectiles

Ändert, was Einheiten abfeuern, wie oft und wie weit sie schießen und welche Ziele sie bevorzugen.

## Verwendung

1. **Geschosskonfigurationsdatei (YAML)** für das normale Spiel leer lassen.
2. `vanilla-projectiles.yml` aus dem Erweiterungsordner oder der ZIP-Datei nach `ucp/resources/custom-projectiles/` im Spielordner kopieren. Den Ordner bei Bedarf anlegen, die Kopie bearbeiten und unter **Anpassungen > Balance Changes** auswählen.
3. Das Spiel neu starten.

## Was möglich ist

In der Kopie bei der passenden Einheit die Werte `native` durch die gezeigten Werte ersetzen.

### Nachladen von Bogenschützen verlangsamen

Europäischen Bogenschützen mehr Zeit zwischen den Schüssen geben.

```yaml
units:
  European archer:
    interval: 600
```

### Katapulten mehr Reichweite geben

Katapulte auf Ziele in bis zu 40 Feldern Entfernung zielen lassen.

```yaml
units:
  Catapult:
    interval: 700
    range: 40
```

### Mehr Steine auf einmal abfeuern

Jede Salve einer Mange zehn Steine abfeuern lassen.

```yaml
units:
  Mangonel:
    count: 10
    spread: 48
```

![Eine Salve einer Mange im Flug](https://raw.githubusercontent.com/Krarilotus/extension-projectileModifier/534bfdd4d0c01dfdefece636841d2fc336bc0ddb/docs/screenshots/mangonel-volley.jpg)

### Munition nach Ziel wählen

Katapulte automatisch Kühe auf feindliche Katapulte schleudern lassen.

```yaml
units:
  Catapult:
    interval: 700
    ammo_by_target: {units: {Catapult: cow}}
```

## Spielstände

Spielstände lassen sich nach einer Änderung der Datei weiter laden: Geänderte Einstellungen starten die Schuss-Timer neu; nach Grafikänderungen verlieren fliegende Geschosse ihr eigenes Aussehen, und platzierte Dekorationen, deren Art entfernt wurde, werden zu normalen Feuerschalen. Spielstände laden auch bei ausgeschaltetem Modul. Mit `allow_config_changes_on_load: false` am Anfang der Datei werden Spielstände mit anderen Einstellungen abgelehnt.

*Hinweis: Dies ist eine maschinelle Übersetzung, die noch auf eine menschliche Prüfung wartet.*

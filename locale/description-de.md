# Custom Projectiles

Ändert, was Einheiten abfeuern, wie oft und wie weit sie schießen und welche Ziele sie bevorzugen.

## Verwendung

1. **Geschosskonfigurationsdatei (YAML)** für das normale Spiel leer lassen.
2. `vanilla-projectiles.yml` aus dem Erweiterungsordner oder der ZIP-Datei nach `ucp/resources/custom-projectiles/` im Spielordner kopieren. Den Ordner bei Bedarf anlegen, die Kopie bearbeiten und unter **Anpassungen > Balance Changes** auswählen.
3. Das Spiel neu starten.

## Was möglich ist

Diese Einstellungen in der Kopie bei der passenden Einheit hinzufügen.

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

### Munition nach Ziel wählen

Katapulte automatisch Kühe auf feindliche Katapulte schleudern lassen.

```yaml
units:
  Catapult:
    interval: 700
    ammo_by_target: {units: {Catapult: cow}}
```

*Hinweis: Dies ist eine maschinelle Übersetzung, die noch auf eine menschliche Prüfung wartet.*

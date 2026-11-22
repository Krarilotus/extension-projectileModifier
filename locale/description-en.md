# Custom Projectiles

Change what units fire, how often and how far they shoot, and which targets they favor.

## How to use it

1. Leave **Projectile configuration file (YAML)** blank for the normal game.
2. Copy `vanilla-projectiles.yml` from the extension folder or ZIP to your game’s `ucp/resources/custom-projectiles/` folder. Create that folder if needed, then edit the copy and select it in **Customizations > Balance Changes**.
3. Restart the game.

## What you can do

Add these settings to the matching unit in your copy.

### Slow down archer reloads

Give European archers more time between shots.

```yaml
units:
  European archer:
    interval: 600
```

### Give catapults more range

Let catapults aim at targets up to 40 tiles away.

```yaml
units:
  Catapult:
    interval: 700
    range: 40
```

### Fire more stones at once

Make each mangonel volley launch ten stones.

```yaml
units:
  Mangonel:
    count: 10
    spread: 48
```

### Choose ammunition by target

Have catapults automatically launch cows at enemy catapults.

```yaml
units:
  Catapult:
    interval: 700
    ammo_by_target: {units: {Catapult: cow}}
```

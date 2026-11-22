# Custom Projectiles

Modifiez ce que tirent les unités, leur cadence, leur portée et les cibles qu'elles privilégient.

## Comment l'utiliser

1. Laissez **Fichier de configuration des projectiles (YAML)** vide pour le jeu normal.
2. Copiez `vanilla-projectiles.yml` depuis le dossier de l'extension ou l'archive ZIP, modifiez la copie et sélectionnez-la dans **Personnalisations > Balance Changes**.
3. Redémarrez le jeu.

## Ce que vous pouvez faire

Ajoutez ces paramètres à l'unité correspondante dans votre copie.

### Ralentir le rechargement des archers

Donnez plus de temps entre deux tirs aux archers européens.

```yaml
units:
  European archer:
    interval: 600
```

![Comparaison du rechargement des archers européens](https://raw.githubusercontent.com/Krarilotus/extension-projectileModifier/feature/target-ammunition/docs/screenshots/archer-reload.jpg)

### Augmenter la portée des catapultes

Permettez aux catapultes de viser des cibles jusqu'à 40 cases de distance.

```yaml
units:
  Catapult:
    interval: 700
    range: 40
```

![Catapulte tirant sur une cible éloignée](https://raw.githubusercontent.com/Krarilotus/extension-projectileModifier/feature/target-ammunition/docs/screenshots/catapult-range.jpg)

### Tirer plus de pierres à la fois

Faites lancer dix pierres à chaque salve de mangonneau.

```yaml
units:
  Mangonel:
    count: 10
    spread: 48
```

![Salve de mangonneau en vol](https://raw.githubusercontent.com/Krarilotus/extension-projectileModifier/feature/target-ammunition/docs/screenshots/mangonel-volley.jpg)

### Choisir les munitions selon la cible

Faites lancer automatiquement des vaches par les catapultes sur les catapultes ennemies.

```yaml
units:
  Catapult:
    interval: 700
    ammo_by_target: {units: {Catapult: cow}}
```

![Une vache lancée vers une catapulte ennemie](https://raw.githubusercontent.com/Krarilotus/extension-projectileModifier/feature/target-ammunition/docs/screenshots/catapult-ammunition.jpg)

*Remarque : cette traduction automatique attend encore une relecture humaine.*

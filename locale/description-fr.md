# Custom Projectiles

Modifiez ce que tirent les unités, leur cadence, leur portée et les cibles qu'elles privilégient.

## Comment l'utiliser

1. Laissez **Fichier de configuration des projectiles (YAML)** vide pour le jeu normal.
2. Copiez `vanilla-projectiles.yml` depuis le dossier de l’extension ou l’archive ZIP vers `ucp/resources/custom-projectiles/` dans le dossier du jeu. Créez ce dossier si nécessaire, puis modifiez la copie et sélectionnez-la dans **Personnalisations > Balance Changes**.
3. Redémarrez le jeu.

## Ce que vous pouvez faire

Dans votre copie, trouvez l'unité correspondante et remplacez ses valeurs `native` par celles indiquées.

### Ralentir le rechargement des archers

Donnez plus de temps entre deux tirs aux archers européens.

```yaml
units:
  European archer:
    interval: 600
```

### Augmenter la portée des catapultes

Permettez aux catapultes de viser des cibles jusqu'à 40 cases de distance.

```yaml
units:
  Catapult:
    interval: 700
    range: 40
```

### Tirer plus de pierres à la fois

Faites lancer dix pierres à chaque salve de mangonneau.

```yaml
units:
  Mangonel:
    count: 10
    spread: 48
```

![Une salve de mangonneau en vol](https://raw.githubusercontent.com/Krarilotus/extension-projectileModifier/534bfdd4d0c01dfdefece636841d2fc336bc0ddb/docs/screenshots/mangonel-volley.jpg)

### Choisir les munitions selon la cible

Faites lancer automatiquement des vaches par les catapultes sur les catapultes ennemies.

```yaml
units:
  Catapult:
    interval: 700
    ammo_by_target: {units: {Catapult: cow}}
```

## Sauvegardes

Les sauvegardes se chargent toujours après une modification de votre fichier : des paramètres modifiés redémarrent les minuteries de tir ; après une modification des graphismes, les projectiles en vol perdent leur apparence personnalisée et les décorations placées dont vous avez supprimé le type deviennent des braseros ordinaires. Les sauvegardes se chargent aussi avec le module désactivé. Placez `allow_config_changes_on_load: false` en haut de votre fichier pour refuser les sauvegardes créées avec d'autres paramètres.

## Autres extensions

Si vous utilisez Smarter Walls, Improved Siegeengines ou Improved Tunnelers, placez-les avant Custom Projectiles dans l'ordre de chargement.

*Remarque : cette traduction automatique attend encore une relecture humaine.*

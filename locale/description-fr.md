# Custom Projectiles 1.8.14

Les réglages de jeu peuvent changer avant le chargement ; les anciennes files de tirs et minuteries du module sont réinitialisées. Les définitions graphiques personnalisées doivent rester identiques. allow_config_changes_on_load: false exige les réglages d’origine. strict_range: false désactive aussi le nouveau contrôle de portée des tirs manuels.

Munitions automatiques : définir les cibles dans unit_groups, puis ammo_by_target.groups: {siege: regular} par tireur, ou ammo_by_target.units: {Monk: cow}. Les types précis ont priorité ; les autres cibles gardent leur comportement. Intervalle requis ; native efface les règles. Exemple Reconquista inclus.

Configurez les 77 types d’unités en YAML. Munitions normales et vaches sont indépendantes. Les intervalles respectent les animations de tir prises en charge ; inaccuracy utilise les unités natives : 1 = 1/8 de case, 8 = 1 case, 0 = visée exacte.

Le seuil de regroupement ne concerne que l’IA ; les joueurs peuvent toujours donner leurs ordres d’attaque. Pour les cibles automatiques, target_bias_tiles: {Monk: 3} rapproche virtuellement les moines de trois cases au plus dans le score natif ; portée et autres règles restent actives.

Copiez le fichier complet vanilla-projectiles.yml depuis le ZIP, modifiez-le et sélectionnez la copie. native conserve les règles du jeu ; un chemin vide ne change rien. auto_targeting: false impose des ordres d’attaque manuels. strict_range: false rétablit les contrôles de portée arrondis ; turn_before_shot: false désactive la correction de rotation. Obligatoire/suggéré concerne la sélection du fichier entier. Redémarrez après modification.

Images personnalisées : ajoutez un nom sous projectiles avec inherits et sprites (fichier GM1 complet compatible). Définissez decorations et les règles near_decorations des unités ; placez-les via le bouton brasero. Formats : README.md et examples/custom-sprites-and-decorations.yml. Placez-les sur des murs ou tours valides ; les manoirs n’acceptent pas de braseros.

Nécessite UCP 3.0.7+, Crusader/Extreme 1.41 et les dépendances du module. Version de test ; voir VALIDATION.md.

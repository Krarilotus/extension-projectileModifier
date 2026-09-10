# Projectile Modifier

Choisissez les projectiles, la taille des salves et les intervalles de tir automatique pour les 77 types d’unités. Les catapultes peuvent lancer des pierres de mangonneau ; les tours de siège et les unités de mêlée peuvent recevoir une attaque à distance automatique.

**Balance Changes → Projectiles**

Ouvrez une famille, puis une unité. Cochez l’épée pour modifier une valeur numérique ; dépliez le réglage pour afficher son aide. Les réglages désactivés conservent les valeurs du fichier ou le comportement d’origine. Relancez le jeu pour appliquer les changements.

Active le tir automatique, même pour les unités de mêlée et les tours de siège. Remplace les tirs d’origine par défaut. Utilise le projectile d’origine ou des flèches si l’unité n’en possède pas. Un tick est un pas de simulation, pas une milliseconde.

Cibles du tir automatique. Les unités et bâtiments alliés sont exclus. Les murs incluent les vôtres. Le fichier YAML permet de définir une liste de priorités personnalisée.

Chargez un préréglage YAML pour les options avancées : mouvement, salves échelonnées, précision, hauteur et animation. Les réglages activés ci-dessous remplacent ses valeurs. Sans fichier, utilisez les réglages courants. Exemples et tableau complet dans README.md ; schéma d’édition dans projectile-config.schema.json.

Nécessite UCP 3.0.7+, map-extensions 1.x et Crusader/Extreme 1.41. Les délais et salves en attente sont sauvegardés ; le chargement exige les mêmes réglages. Cette version d’essai 1.3.2 non signée est basée sur la version 1.2.0 de Monsterfish. Les essais en jeu, en multijoueur et avec l’enregistreur restent à effectuer ; voir VALIDATION.md. La référence technique est en anglais.

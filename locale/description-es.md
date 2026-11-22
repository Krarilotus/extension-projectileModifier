# Custom Projectiles

Cambia lo que disparan las unidades, con qué frecuencia y a qué distancia atacan, y qué objetivos prefieren.

## Cómo usarlo

1. Deja **Archivo de configuración de proyectiles (YAML)** en blanco para el juego normal.
2. Copia `vanilla-projectiles.yml` desde la carpeta de la extensión o el archivo ZIP, edita la copia y selecciónala en **Personalizaciones > Balance Changes**.
3. Reinicia el juego.

## Qué puedes hacer

Añade estos ajustes a la unidad correspondiente en tu copia.

### Ralentizar la recarga de los arqueros

Da más tiempo entre disparos a los arqueros europeos.

```yaml
units:
  European archer:
    interval: 600
```

![Comparación de recarga de los arqueros europeos](https://raw.githubusercontent.com/Krarilotus/extension-projectileModifier/feature/target-ammunition/docs/screenshots/archer-reload.jpg)

### Dar más alcance a las catapultas

Permite que las catapultas apunten a objetivos a una distancia de hasta 40 casillas.

```yaml
units:
  Catapult:
    interval: 700
    range: 40
```

![Catapulta disparando a un objetivo lejano](https://raw.githubusercontent.com/Krarilotus/extension-projectileModifier/feature/target-ammunition/docs/screenshots/catapult-range.jpg)

### Disparar más piedras a la vez

Haz que cada descarga del mangonel lance diez piedras.

```yaml
units:
  Mangonel:
    count: 10
    spread: 48
```

![Descarga de mangonel en vuelo](https://raw.githubusercontent.com/Krarilotus/extension-projectileModifier/feature/target-ammunition/docs/screenshots/mangonel-volley.jpg)

### Elegir la munición según el objetivo

Haz que las catapultas lancen vacas automáticamente contra las catapultas enemigas.

```yaml
units:
  Catapult:
    interval: 700
    ammo_by_target: {units: {Catapult: cow}}
```

![Una vaca lanzada hacia una catapulta enemiga](https://raw.githubusercontent.com/Krarilotus/extension-projectileModifier/feature/target-ammunition/docs/screenshots/catapult-ammunition.jpg)

*Nota: esta es una traducción automática pendiente de revisión humana.*

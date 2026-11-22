# Custom Projectiles

Cambia lo que disparan las unidades, con qué frecuencia y a qué distancia atacan, y qué objetivos prefieren.

## Cómo usarlo

1. Deja **Archivo de configuración de proyectiles (YAML)** en blanco para el juego normal.
2. Copia `vanilla-projectiles.yml` desde la carpeta de la extensión o el archivo ZIP a `ucp/resources/custom-projectiles/` dentro de la carpeta del juego. Crea esa carpeta si hace falta, edita la copia y selecciónala en **Personalizaciones > Balance Changes**.
3. Reinicia el juego.

## Qué puedes hacer

En tu copia, busca la unidad correspondiente y sustituye sus valores `native` por los que se muestran.

### Ralentizar la recarga de los arqueros

Da más tiempo entre disparos a los arqueros europeos.

```yaml
units:
  European archer:
    interval: 600
```

### Dar más alcance a las catapultas

Permite que las catapultas apunten a objetivos a una distancia de hasta 40 casillas.

```yaml
units:
  Catapult:
    interval: 700
    range: 40
```

### Disparar más piedras a la vez

Haz que cada descarga del mangonel lance diez piedras.

```yaml
units:
  Mangonel:
    count: 10
    spread: 48
```

![Una andanada de mangonel en vuelo](https://raw.githubusercontent.com/Krarilotus/extension-projectileModifier/534bfdd4d0c01dfdefece636841d2fc336bc0ddb/docs/screenshots/mangonel-volley.jpg)

### Elegir la munición según el objetivo

Haz que las catapultas lancen vacas automáticamente contra las catapultas enemigas.

```yaml
units:
  Catapult:
    interval: 700
    ammo_by_target: {units: {Catapult: cow}}
```

## Otras extensiones

Si usas Smarter Walls, Improved Siegeengines o Improved Tunnelers, colócalas antes de Custom Projectiles en el orden de carga.

*Nota: esta es una traducción automática pendiente de revisión humana.*

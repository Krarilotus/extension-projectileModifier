# Custom Projectiles 1.8.15

Proyectiles sustitutos de largo alcance: projectile_physics: {firethrower_pot: {mode: fixed_angle, angle: 30}} deja que el juego calcule la velocidad inicial. Requiere Rebalancer 1.1.3+ activo con configuración de equilibrio. Es global por tipo, incluidas variantes gráficas; native conserva los valores. Alcance y colisiones siguen aplicándose.

Los ajustes de juego pueden cambiar antes de cargar; se reinician las antiguas colas de disparo y temporizadores del módulo. Las definiciones gráficas personalizadas deben coincidir. allow_config_changes_on_load: false exige los ajustes originales. strict_range: false también desactiva la nueva comprobación de alcance de disparos manuales.

Munición automática: defina listas de objetivos en unit_groups y use ammo_by_target.groups: {siege: regular} por tirador, o ammo_by_target.units: {Monk: cow}. Los tipos concretos tienen prioridad; los demás objetivos conservan su comportamiento. Requiere intervalo; native borra las reglas. Incluye ejemplo Reconquista.

Configura los 77 tipos de unidades mediante YAML. La munición normal y las vacas se ajustan por separado. Los intervalos respetan las animaciones de disparo compatibles; inaccuracy usa unidades nativas: 1 = 1/8 de casilla, 8 = 1 casilla, 0 = puntería exacta.

El mínimo de enemigos agrupados solo se aplica a la IA; el jugador puede seguir dando órdenes de ataque. Para objetivos automáticos, target_bias_tiles: {Monk: 3} considera a los monjes hasta tres casillas más cercanos en la puntuación nativa; se mantienen el alcance y las demás reglas.

Copia el archivo completo vanilla-projectiles.yml del ZIP, edítalo y selecciona la copia. native conserva las reglas del juego; una ruta vacía no cambia nada. auto_targeting: false exige órdenes de ataque manuales. strict_range: false restaura las comprobaciones de alcance redondeadas; turn_before_shot: false desactiva la corrección de giro. Obligatorio/sugerido se aplica a la selección del archivo completo. Reinicia después de editar.

Gráficos propios: añade un nombre en projectiles con inherits y sprites (archivo GM1 completo y compatible). Define decorations y las reglas near_decorations de las unidades; colócalas mediante el botón del brasero. Formatos: README.md y examples/custom-sprites-and-decorations.yml. Colócalas en murallas o torres válidas; las casas señoriales no admiten braseros.

Requiere UCP 3.0.7+, Crusader/Extreme 1.41 y las dependencias del módulo. Versión de prueba; consulta VALIDATION.md.

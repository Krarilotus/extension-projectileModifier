# Custom Projectiles 1.8.12

Configura los 77 tipos de unidades mediante YAML. La munición normal y las vacas se ajustan por separado. Los intervalos respetan las animaciones de disparo compatibles; inaccuracy usa unidades nativas: 1 = 1/8 de casilla, 8 = 1 casilla, 0 = puntería exacta.

El mínimo de enemigos agrupados solo se aplica a la IA; el jugador puede seguir dando órdenes de ataque. Para objetivos automáticos, target_bias_tiles: {Monk: 3} considera a los monjes hasta tres casillas más cercanos en la puntuación nativa; se mantienen el alcance y las demás reglas.

Copia el archivo completo vanilla-projectiles.yml del ZIP, edítalo y selecciona la copia. native conserva las reglas del juego; una ruta vacía no cambia nada. auto_targeting: false exige órdenes de ataque manuales. strict_range: false restaura las comprobaciones de alcance redondeadas; turn_before_shot: false desactiva la corrección de giro. Obligatorio/sugerido se aplica a la selección del archivo completo. Reinicia después de editar.

Gráficos propios: añade un nombre en projectiles con inherits y sprites (archivo GM1 completo y compatible). Define decorations y las reglas near_decorations de las unidades; colócalas mediante el botón del brasero. Formatos: README.md y examples/custom-sprites-and-decorations.yml. Colócalas en murallas o torres válidas; las casas señoriales no admiten braseros.

Requiere UCP 3.0.7+, Crusader/Extreme 1.41 y las dependencias del módulo. Versión de prueba; consulta VALIDATION.md.

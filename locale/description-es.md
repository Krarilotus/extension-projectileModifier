# Custom Projectiles 1.6.0

Elige proyectiles, tamaños de salva e intervalos de disparo automático para los 77 tipos de unidades. Las catapultas pueden lanzar piedras de mangonel; las torres de asedio y las unidades cuerpo a cuerpo pueden obtener un ataque a distancia automático.

Copia vanilla-projectiles.yml del ZIP del módulo a ucp/resources/custom-projectiles/, edita la copia y selecciónala aquí. Los ajustes omitidos no cambian; una ruta vacía no aplica cambios. Las reglas UCP de valores obligatorios o sugeridos se aplican al archivo seleccionado en su conjunto. Reinicia el juego tras los cambios.

Requiere UCP 3.0.7+, map-extensions 1.x y Crusader/Extreme 1.41. Los 33 ajustes y 77 nombres de unidades se documentan en vanilla-projectiles.yml y README.md. Versión de prueba local; la validación en el juego sigue pendiente.

Precisión: inaccuracy usa unidades enteras del juego: 1 = 1/8 de casilla, 8 = 1 casilla. 0 elimina el error aleatorio; omitirlo conserva la precisión original. spread es independiente.

Catapultas, trabuquetes, mangoneles y balistas: interval sigue la animación de disparo y no la acorta. sync_to_animation: false restaura el temporizador independiente. Inicia una partida nueva tras actualizar.

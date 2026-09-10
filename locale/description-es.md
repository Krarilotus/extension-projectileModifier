# Projectile Modifier

Elige proyectiles, tamaños de salva e intervalos de disparo automático para los 77 tipos de unidades. Las catapultas pueden lanzar piedras de mangonel; las torres de asedio y las unidades cuerpo a cuerpo pueden obtener un ataque a distancia automático.

**Balance Changes → Proyectiles**

Abre un grupo y después una unidad. Marca la espada para modificar un valor numérico; despliega el ajuste para ver su ayuda. Los ajustes desactivados conservan los valores del archivo o el comportamiento original. Reinicia el juego para aplicar los cambios.

Activa el disparo automático, también para unidades cuerpo a cuerpo y torres de asedio. Sustituye los disparos originales de forma predeterminada. Usa el proyectil original o flechas si la unidad no tenía ninguno. Un tick es un paso de simulación, no un milisegundo.

Objetivos del disparo automático. Se excluyen las unidades y los edificios aliados. Los muros incluyen los tuyos. El archivo YAML admite listas de prioridades personalizadas.

Carga un preajuste YAML para las opciones avanzadas: movimiento, salvas escalonadas, precisión, altura y animación. Los ajustes activados abajo sustituyen sus valores. Sin archivo, utiliza los ajustes habituales. README.md contiene ejemplos y la tabla completa; projectile-config.schema.json proporciona el esquema de edición.

Requiere UCP 3.0.7+, map-extensions 1.x y Crusader/Extreme 1.41. Se guardan los temporizadores y las salvas pendientes; la carga requiere los mismos ajustes. Esta versión de prueba 1.3.2 sin firmar se basa en la 1.2.0 de Monsterfish. Quedan pendientes las pruebas en el juego, en multijugador y con el grabador; consulta VALIDATION.md. La referencia técnica está en inglés.

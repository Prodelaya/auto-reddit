# Documento de Producto Definitivo

> Aviso historico: este documento conserva el discovery inicial. Varias decisiones aqui ya estan superadas. La fuente de verdad vigente es `docs/product/product.md` y, para la integracion de Reddit, `docs/integrations/reddit/api-strategy.md`.

> En particular, ya NO aplican aqui como decisiones vigentes las referencias a `old but alive`, backlog explicito, estado `approved`, mezcla de fuentes fuera de `r/Odoo` o limites distintos del modelo operativo vigente 8/8.

## Halltic Reddit Opportunity Assistant

Versión: 1.0
Estado: Definitivo para análisis de viabilidad técnica y diseño de arquitectura
Autor del documento: ChatGPT a partir de sesiones de discovery con Product Owner
Fecha: 20/03/2026

---

# 1. Resumen ejecutivo

Halltic Reddit Opportunity Assistant es un sistema interno de apoyo al equipo de marketing y negocio de Halltic para detectar oportunidades de participación en Reddit relacionadas con Odoo y ERP, generar respuestas sugeridas de alta calidad con ayuda de un LLM y entregarlas al equipo humano para su publicación manual.

El producto no publica automáticamente. Tampoco mantiene conversaciones posteriores ni realiza seguimiento autónomo. Su función termina al proponer una respuesta lista para copiar y pegar en el hilo correspondiente.

La intención del producto es combinar cuatro objetivos:

1. Ganar visibilidad de marca.
2. Construir reputación técnica en torno a Odoo y ERP.
3. Ayudar a la comunidad con respuestas útiles y breves.
4. Generar oportunidades de contacto por mensaje privado o contratación.

La prioridad absoluta del producto es la calidad técnica de las respuestas. El mayor riesgo a evitar es publicar respuestas imprecisas que erosionen la imagen de Halltic como especialista en Odoo, ERP y desarrollo de software.

---

# 2. Contexto y origen de la necesidad

Halltic quiere participar con regularidad en comunidades públicas donde usuarios plantean dudas reales sobre Odoo, ERP, implantación, configuración, comparativas y desarrollo. La revisión manual diaria de Reddit es costosa, inconsistente y difícil de sostener con disciplina.

Se exploraron alternativas de automatización completa, incluyendo publicación automática en Reddit. El diseño final descarta la publicación automática y adopta un enfoque con humano en el loop por tres motivos:

1. Reducir la complejidad técnica total del sistema.
2. Eliminar la capa más frágil de mantenimiento asociada a publicación automatizada.
3. Añadir una validación humana final para proteger marca, tono y precisión técnica.

El sistema final es, por tanto, un pipeline de:

- detección,
- filtrado,
- priorización,
- generación,
- y entrega de sugerencias.

---

# 3. Definición del producto

## 3.1 Qué es

Un sistema interno de inteligencia operativa que analiza publicaciones de Reddit y entrega al equipo de Halltic propuestas de respuesta ya redactadas, contextualizadas y listas para copiar y pegar.

## 3.2 Qué no es

No es un bot conversacional autónomo.
No publica directamente en Reddit.
No responde a réplicas.
No mantiene debate.
No sustituye al criterio humano.
No es una herramienta de escucha social genérica.
No es un CRM.
No es una plataforma multicanal en su primera fase.

## 3.3 Alcance de la primera versión

- Fuente única: Reddit.
- Temática: Odoo y ERP relacionado.
- Idioma prioritario: español, incluyendo posts con mezcla de español e inglés técnico. Aceptamos posts en ingés.
- Canal de salida interno: preferentemente Telegram; email como alternativa si el equipo lo necesita.
- Frecuencia: una ejecución al día.
- Volumen máximo: hasta 10 sugerencias al día.

---

# 4. Visión de producto

Crear un sistema que permita a Halltic sostener una presencia útil, constante y técnicamente solvente en Reddit sin depender de una revisión manual completa de todos los hilos, reservando el tiempo humano para la validación final y el seguimiento de conversaciones interesantes.

Principio rector del producto:

**La IA detecta, prioriza y propone. El humano decide y publica.**

---

# 5. Objetivos del producto

## 5.1 Objetivos de negocio

1. Incrementar la visibilidad de Halltic en comunidades relacionadas con Odoo y ERP.
2. Construir reputación técnica percibida como experta, útil y cercana.
3. Generar señales de interés comercial y posibles leads por DM o contacto posterior.
4. Aumentar la consistencia de participación sin elevar en exceso el coste operativo humano.

## 5.2 Objetivos operativos

1. Detectar diariamente posts elegibles.
2. Reducir el tiempo dedicado a scouting manual.
3. Entregar respuestas sugeridas de calidad listas para publicación manual.
4. Mantener backlog y evitar duplicados.
5. Permitir una operativa diaria ligera por parte del equipo de marketing.

## 5.3 Objetivo prioritario absoluto

La calidad técnica de las respuestas está por encima del volumen, la velocidad y la cobertura.

## 5.4 Criterios de éxito a 6 meses

Se considerará que el producto ha sido exitoso si:

- Halltic gana buena reputación en los foros relevantes.
- Se reciben mensajes privados o contactos de usuarios interesados en implementar, mejorar o solucionar problemas en Odoo.
- El equipo percibe que las respuestas sugeridas son suficientemente buenas como para ahorrar tiempo real.
- La presencia de Halltic se mantiene natural y útil.

---

# 6. Principios de diseño cerrados

1. Reddit solo en la primera fase.
2. Una única ejecución al día.
3. Máximo de 10 sugerencias por sesión.
4. Publicación manual por parte del equipo humano.
5. Seguimiento de respuestas y DMs manual por parte del equipo.
6. Prompt y evolución del criterio controlados manualmente por el Product Owner.
7. Prioridad máxima a precisión técnica sobre cobertura.
8. En funcionalidad/configuración se puede resolver con mayor directividad.
9. En desarrollo se orienta con conocimiento, pero sin hacer trabajo gratis.
10. Halltic debe ser visible, pero sin sonar comercial de forma agresiva.
11. El tono debe ser forero, técnico, breve, pragmático y natural.
12. El sistema no debe entrar en discusiones donde Odoo sea objetivamente indefendible.

---

# 7. Usuarios y actores

## 7.1 Product Owner

Responsable de definir prompt, criterios, listas blancas y negras, tono y iteración del sistema.

## 7.2 Equipo de marketing / negocio

Usuarios operativos del producto. Reciben sugerencias, abren el hilo, revisan la propuesta y deciden si publicar, editar, descartar, responder un DM o continuar una conversación.

## 7.3 LLM

Actor de apoyo que analiza contexto y genera respuestas sugeridas dentro de reglas estrictas.

## 7.4 Usuario externo final

La persona de Reddit que ha publicado una duda sobre Odoo, ERP, implantación, uso o desarrollo.

---

# 8. Resultado deseado de percepción de marca

Tras varios meses de uso, Halltic debería percibirse, en este orden, como:

1. una opción profesional a la que escribir si necesitas ayuda,
2. una cuenta que sabe mucho de Odoo,
3. una cuenta que responde bien y ayuda,
4. una cuenta seria de desarrolladores.

---

# 9. Propuesta de valor

## 9.1 Para Halltic

- Reduce el tiempo de revisión manual.
- Multiplica oportunidades de participación útil.
- Facilita una presencia constante y de calidad.
- Convierte Reddit en un canal asistido de reputación y detección de leads.

## 9.2 Para la comunidad

- Recibe respuestas breves, útiles y con conocimiento real.
- Obtiene orientación sobre problemas funcionales, técnicos y de decisión relacionados con Odoo.

---

# 10. Alcance funcional

## 10.1 Flujo funcional general

1. El sistema consulta Reddit a través de APIs no oficiales para leer posts y comentarios.
2. Reúne candidatos nuevos y candidatos antiguos pero todavía activos.
3. Aplica filtros de idioma, temática y viabilidad.
4. Construye un conjunto elegible de hasta 10 posts por día.
5. Para cada post elegible, recopila el post principal y entre 3 y 5 comentarios recientes para contextualizar.
6. Envía el lote al LLM con instrucciones de selección y redacción.
7. Recibe una respuesta estructurada por cada post.
8. Envía cada oportunidad al equipo de marketing por Telegram o email en un formato listo para copiar y pegar.
9. Registra el estado del post y evita reenviarlo como nuevo al día siguiente.

## 10.2 Definición de elegibilidad diaria

El sistema trabaja con un máximo de 10 posts elegibles al día.

No existe obligación de que sean exactamente 5 nuevos y 5 antiguos. Ese reparto solo expresa la intención de combinar ambos tipos cuando haya volumen suficiente.

Regla práctica:

- si hay 10 elegibles, se envían 10;
- si hay 12 elegibles, se envían 10 y el resto queda pendiente;
- si al día siguiente aparecen menos posts nuevos, se complementa con backlog.

## 10.3 Definición de “post antiguo pero vivo”

Un post antiguo sigue siendo elegible si:

- ha recibido comentarios recientes,
- el hilo sigue activo,
- el contexto reciente permite aportar algo no redundante,
- no parece cerrado o definitivamente resuelto.

---

# 11. Fuentes y canal de salida

## 11.1 Fuente de entrada

Reddit, consumido a través de APIs no oficiales con límites gratuitos generosos, siempre que permitan recuperar como mínimo:

- id del post,
- título,
- cuerpo,
- subreddit,
- permalink o URL,
- timestamps,
- comentarios,
- metadatos suficientes para distinguir novedad y actividad.

## 11.2 Canal de salida interno

Canal preferido: Telegram.
Canal alternativo: email.

Telegram se considera preferible por:

- inmediatez,
- facilidad de uso móvil,
- rapidez de copy/paste,
- buena adecuación al flujo diario del equipo.

---

# 12. Requisitos funcionales

## RF-01. Ingesta diaria

El sistema debe ejecutarse una vez al día y leer publicaciones recientes y publicaciones antiguas activas de los subreddits configurados.

## RF-02. Normalización

El sistema debe transformar cada candidato en una estructura homogénea con campos mínimos:

- id,
- título,
- cuerpo,
- idioma,
- tema,
- subreddit,
- URL,
- fecha,
- actividad reciente,
- estado interno.

## RF-03. Filtro de idioma

El sistema debe priorizar posts en español y aceptar posts con mezcla de español e inglés técnico. Aceptamos posts en inglés.

## RF-04. Filtro temático

El sistema debe quedarse solo con posts relacionados con categorías aprobadas.

## RF-05. Selección diaria

El sistema debe elegir hasta 10 posts elegibles diarios, combinando nuevos y antiguos vivos.

## RF-06. Contextualización

Para cada post elegible, el sistema debe incluir en la entrada al LLM:

- el post principal,
- y entre 3 y 5 comentarios recientes del hilo.

## RF-07. Generación de respuesta

El sistema debe generar una respuesta sugerida breve, útil, contextualizada y alineada con el tono definido.

## RF-08. Entrega al equipo

El sistema debe enviar un mensaje estructurado por cada oportunidad al equipo de marketing.

## RF-09. Evitar duplicados

El sistema debe registrar qué posts ya han sido vistos o enviados para no tratarlos erróneamente como nuevos en ejecuciones futuras.

## RF-10. Backlog

El sistema debe soportar posts elegibles pendientes de días anteriores.

## RF-11. Estados internos mínimos

El sistema debe permitir al menos los estados:

- visto,
- elegible,
- enviado,
- pendiente,
- descartado,
- publicado manualmente (opcional si se implementa confirmación humana),
- error.

---

# 13. Requisitos no funcionales

## RNF-01. Precisión

El sistema debe priorizar la precisión técnica por encima del volumen.

## RNF-02. Brevedad

Las respuestas sugeridas deben ser breves y directamente utilizables.

## RNF-03. Naturalidad

Las respuestas deben sonar humanas, foreras y naturales.

## RNF-04. Trazabilidad mínima

Debe existir persistencia mínima suficiente para evitar duplicados y gestionar backlog.

## RNF-05. Mantenibilidad

El producto debe evitar capas frágiles innecesarias como navegación automatizada, sesiones web persistidas o scraping de publicación.

## RNF-06. Bajo coste operativo

La ejecución diaria debe ser ligera, económica y compatible con infraestructura simple.

---

# 14. Temáticas permitidas y priorización

## 14.1 Orden de prioridad temático

1. funcionalidad y configuración de Odoo,
2. desarrollo,
3. dudas sobre si merece la pena Odoo,
4. comparativas con otras opciones.

## 14.2 Tipos de preguntas que sí entran

- dudas técnicas de configuración,
- uso funcional de Odoo como ERP,
- desarrollo de módulos,
- orientación sobre desarrollo relacionado con Odoo,
- comparativas donde Halltic pueda explicar el enfoque en Odoo,
- preguntas sobre si Odoo es buena opción o no.

## 14.3 Tipos de preguntas que no entran

Todo lo que quede fuera de esas categorías o vulnere las listas negras definidas.

---

# 15. Lista negra explícita

El sistema debe excluir contenidos relacionados con:

- racismo,
- machismo,
- homofobia,
- xenofobia,
- islamofobia,
- política,
- fútbol,
- debates no técnicos sobre Odoo,
- temas fuera del posicionamiento profesional definido.

---

# 16. Tono y estilo deseados

La respuesta sugerida debe transmitir una mezcla de:

- experto open source colaborativo,
- consultor práctico,
- desarrollador senior de trinchera.

## Rasgos de estilo obligatorios

- forero,
- técnico,
- breve,
- pragmático,
- profesional,
- coloquial,
- colaborativo.

## Rasgos que deben evitarse

- sonar a bot,
- sonar vendedor,
- ser demasiado largo,
- ser demasiado categórico sin base,
- dar una imagen de pedantería,
- resolver gratis desarrollos complejos.

## Longitud objetivo

- 2 párrafos breves como patrón preferente;
- hasta 3 párrafos breves como máximo natural.

---

# 17. Política de respuesta por tipo de caso

## 17.1 Funcionalidad / configuración

Si se conoce con suficiente seguridad la solución, la respuesta puede ser directa y orientada a resolver.

## 17.2 Desarrollo

La respuesta debe orientar con conocimiento, pero sin hacer trabajo gratis. Debe explicar enfoque, diagnóstico, línea de investigación o puntos clave, pero evitar entregar desarrollos completos.

## 17.3 Casos complejos

La respuesta debe ofrecer:

- una primera hipótesis útil,
- cautela,
- y petición de contexto si hace falta.

## 17.4 Casos con incertidumbre

Se permiten fórmulas como:

- depende de la versión,
- revisaría primero X,
- sin ver el traceback es difícil afinar,
- si compartes más contexto se puede concretar mejor.

---

# 18. Política comercial

## 18.1 Principio general

No sonar comercial.

## 18.2 Cuándo abrir puerta comercial

Solo si el propio usuario da pie de forma clara, por ejemplo si pregunta por:

- consultora,
- partner,
- profesionales,
- ayuda externa,
- apoyo profesional.

## 18.3 Cómo hacerlo

Primero se orienta técnicamente. Solo después se puede dejar caer, con suavidad, que Halltic puede ayudar profesionalmente si el problema se complica o si el usuario decide contratar ayuda.

## 18.4 Cuándo no hacerlo

No introducir mención comercial en respuestas normales si no existe una señal clara por parte del usuario.

---

# 19. Happy path del producto

## 19.1 Happy path diario ideal

1. El sistema encuentra al menos 10 posts elegibles.
2. Todos pasan filtros de idioma, temática y viabilidad.
3. El LLM recibe el post principal, el contexto reciente y las reglas del sistema.
4. El LLM devuelve respuestas adecuadas y contextualizadas.
5. El sistema entrega cada oportunidad al canal interno correcto.
6. El equipo de marketing abre el enlace, revisa el texto, copia y pega la respuesta y la publica.
7. Las respuestas publicadas son útiles, naturales, precisas y no redundantes.

## 19.2 Happy path de contenido

Cada respuesta sugerida:

- sigue el tema del hilo,
- tiene tono adecuado,
- evita repetir lo ya dicho por otros,
- no contiene errores técnicos,
- deja a Halltic en posición de experto útil.

---

# 20. Política de no respuesta

Esta es la parte más importante del producto.

El sistema debe abstenerse cuando:

1. hay riesgo alto de imprecisión;
2. el tema es sensible;
3. el hilo parece resuelto o cerrado;
4. la crítica a Odoo es una realidad objetiva y no defendible;
5. el tema exigiría hacer trabajo gratuito excesivo;
6. no puede aportar nada nuevo y diferencial.

## Casos concretos de abstención

### Críticas fundamentadas a Odoo

Si el defecto o limitación es real y no defendible objetivamente, el sistema no debe entrar.

### Hilo ya resuelto

Si el hilo ya tiene una respuesta suficiente y no hay valor diferencial claro, el sistema no debe insistir.

### Desarrollo demasiado profundo

Si la única forma de ayudar correctamente es resolver una lógica compleja en código, despliegue, Docker, Python, XML, OWL u otros elementos equivalentes, la respuesta debe limitarse a orientación y no entrar a ejecutar el trabajo.

---

# 21. Política de prudencia y antialucinación

## Regla maestra

Cuando no haya certeza suficiente:

- no inventar,
- no afirmar categóricamente,
- orientar con cautela,
- pedir contexto si conviene.

## Comportamientos prohibidos

El sistema no debe inventar:

- reglas de Odoo,
- documentación,
- convenciones,
- capacidades de producto,
- comportamiento de versiones,
- normas o referencias no confirmadas.

## Comportamiento correcto

Cuando exista incertidumbre, la salida debe tender a:

- orientación prudente,
- matiz por versión,
- comprobaciones sugeridas,
- petición de más contexto.

## Diferencias entre versiones

Se pueden mencionar diferencias entre versiones recientes de Odoo solo cuando surja naturalmente y aporte valor.

---

# 22. Edge cases relevantes

## 22.1 Post en español con inglés técnico mezclado

Es elegible. Aceptamos posts en inglés también.

## 22.2 Comparativas o posts derivados hacia otro ERP

Se puede responder desde cómo sería la solución o el enfoque en Odoo.

## 22.3 Post orientado a buscar proveedor

Es elegible. Se puede orientar técnicamente y abrir puerta comercial con suavidad.

## 22.4 Pregunta muy básica

Es elegible. No se excluye a principiantes.

## 22.5 Pregunta donde la versión importa

Se puede responder, pero con cautela y matiz de versión.

## 22.6 Seguridad

Se puede responder solo orientando y sin afirmaciones categóricas.

## 22.7 Legal / fiscal

Solo responder si se trata de algo funcional muy básico de Odoo. No entrar en interpretaciones complejas.

## 22.8 Críticas a Odoo

Solo responder si existe una defensa objetiva y útil. Si no, abstenerse.

## 22.9 Post mal planteado técnicamente

Corregir con humildad y naturalidad.

---

# 23. Operación humana

## 23.1 Qué hace el sistema

- detecta,
- filtra,
- prioriza,
- redacta,
- y entrega sugerencias.

## 23.2 Qué hace el equipo de marketing

- revisa mensajes recibidos,
- abre hilos,
- publica si procede,
- ajusta puntualmente si lo estima necesario,
- revisa DMs y respuestas posteriores,
- decide si continuar la conversación o abrir puerta comercial.

## 23.3 Frecuencia de operación humana

Dos revisiones al día de entre 10 y 15 minutos cada una.

## 23.4 Gestión de errores de calidad

Si una respuesta sugerida o publicada se considera mala, el equipo humano la valora. Si ya fue publicada y es técnica o estratégicamente incorrecta, puede borrarse. El Product Owner usará esos ejemplos para refinar el prompt manualmente.

---

# 24. Modelo de datos conceptual

Campos sugeridos por post:

- external_post_id
- title
- body
- subreddit
- url
- language
- topic_category
- is_new
- is_old_but_alive
- created_at
- last_activity_at
- comments_snapshot
- eligibility_status
- delivery_status
- suggested_response
- delivered_at
- published_manually (opcional)
- discarded_reason (opcional)
- error_reason (opcional)

---

# 25. Estados del flujo

Estados conceptuales sugeridos:

1. descubierto
2. filtrado
3. elegible
4. pendiente de envío
5. enviado al equipo
6. publicado manualmente (si existe confirmación)
7. descartado
8. error

---

# 26. Criterios de priorización

El Product Owner indicó la siguiente jerarquía de priorización:

1. español, inglés,
2. reciente,
3. posibilidad de responder con precisión,
4. implantación / configuración,
5. desarrollo,
6. reputación,
7. comercial,
8. ayudar de verdad,
9. pocas respuestas.

Observación importante: aunque la jerarquía declarada sitúa “ayudar de verdad” relativamente abajo, el espíritu general del discovery confirma que el producto debe mantener utilidad real como condición necesaria. El equipo técnico deberá traducir esta jerarquía en reglas de scoring coherentes con el resto del documento.

---

# 27. Formato de salida al equipo

Formato deseado por oportunidad:

- identificador o índice
- título del post
- enlace directo
- breve contexto o diferenciador de por qué se eligió
- respuesta sugerida literal para copiar y pegar
- nota opcional del sistema si aplica, por ejemplo: “mención comercial omitida” o “pedir versión si responde”.

### Ejemplo de formato esperado

**NUEVA OPORTUNIDAD DE RESPUESTA**
**Post:** [título]
**URL:** [enlace]
**Contexto:** [resumen corto]
**Respuesta sugerida:**
[texto literal]
**Nota:** [si aplica]

---

# 28. Supuestos técnicos de alto nivel

Este documento no define arquitectura técnica final, pero asume como punto de partida:

- lectura por APIs no oficiales de Reddit,
- procesamiento ligero diario,
- persistencia simple,
- integración con LLM por API,
- salida por Telegram o email,
- infraestructura ligera y económica.

El equipo técnico deberá validar:

- estabilidad y cobertura real de las APIs elegidas,
- modelo de persistencia adecuado,
- estrategia de deduplicación,
- mecanismo de configuración de subreddits,
- formato de entrega óptimo,
- si conviene incorporar confirmación humana de publicación.

---

# 29. Métricas recomendadas

Aunque el Product Owner no desea reporting complejo, para evaluar el producto se recomienda medir internamente al menos:

## Métricas operativas

- posts leídos por día,
- posts filtrados,
- posts elegibles,
- sugerencias enviadas,
- ratio nuevos vs antiguos vivos,
- pendientes acumulados.

## Métricas de calidad

- porcentaje de sugerencias publicadas,
- porcentaje de sugerencias editadas antes de publicar,
- porcentaje de sugerencias descartadas por baja calidad,
- incidencias técnicas detectadas por el equipo.

## Métricas de impacto

- respuestas recibidas en hilos publicados,
- DMs recibidos,
- conversaciones con potencial comercial,
- percepción cualitativa del equipo sobre la calidad del sistema.

---

# 30. Riesgos de producto

## 30.1 Riesgos principales

1. Respuestas técnicamente imprecisas.
2. Respuestas demasiado genéricas o repetitivas.
3. Mala asociación entre post y respuesta.
4. Backlog desordenado o posts duplicados.
5. Demasiada permisividad en filtros que baje la calidad media.
6. Falta de disciplina operativa del equipo al revisar y publicar.

## 30.2 Riesgo prioritario

El riesgo principal es la pérdida de reputación técnica por respuestas imprecisas.

---

# 31. Decisiones explícitamente descartadas

1. No se implementará publicación automática en Reddit en la primera versión.
2. No se automatizarán respuestas posteriores ni seguimiento del hilo.
3. No se diseñará, por ahora, dashboard complejo ni backoffice sofisticado.
4. No se incorporará aprendizaje automático autónomo a partir de correcciones humanas.
5. No se ampliará inicialmente a otras plataformas o foros.

---

# 32. Decisiones aún abiertas para el equipo técnico

Estas decisiones no alteran el producto, pero sí afectan a la solución técnica:

1. Qué API no oficial concreta usar como primaria y cuál como fallback.
2. Persistencia exacta: SQLite, Postgres u otra opción.
3. Confirmación manual opcional de “publicado / descartado”.
4. Canal definitivo de salida: Telegram, email o ambos.
5. Nivel de granularidad de logs y auditoría.
6. Método concreto de clasificación de idioma y categorización temática.
7. Diseño de scoring y umbrales finales de elegibilidad.

---

# 33. Preguntas de diseño técnico que este documento entrega al equipo

1. ¿Qué combinación de APIs de lectura ofrece mejor cobertura y resiliencia?
2. ¿Cómo construir una capa de normalización común independiente del proveedor?
3. ¿Qué modelo de estados minimiza duplicados y simplifica backlog?
4. ¿Cómo garantizar la asociación correcta entre post y respuesta?
5. ¿Cómo entregar al equipo mensajes suficientemente cómodos sin desarrollar un panel completo?
6. ¿Qué estrategia de observabilidad mínima permite depurar errores sin añadir complejidad excesiva?
7. ¿Qué validaciones automáticas merece la pena introducir antes de enviar respuestas sugeridas?

---

# 34. Criterios de aceptación del MVP

El MVP será aceptable si:

1. Es capaz de leer posts y comentarios de los subreddits configurados.
2. Es capaz de detectar y guardar candidatos elegibles.
3. Es capaz de generar hasta 10 respuestas sugeridas al día con formato consistente.
4. Entrega esas sugerencias al equipo por un canal usable.
5. Evita reenviar el mismo post erróneamente como nuevo.
6. Permite una operación humana sencilla y útil.
7. La calidad media de las respuestas sugeridas es suficientemente alta como para ahorrar tiempo real al equipo.

---

# 35. Recomendación de enfoque de implementación

Aunque la arquitectura final queda a decisión del equipo técnico, el producto sugiere implícitamente una solución simple, modular y mantenible con al menos estos bloques conceptuales:

1. **Ingesta**
   Conectores a APIs de lectura.

2. **Normalización**
   Estructura común de posts y comentarios.

3. **Filtrado y scoring**
   Reglas de idioma, tema, actividad y viabilidad.

4. **Generación**
   Construcción de prompt y llamada al LLM.

5. **Entrega**
   Telegram o email con formato listo para acción.

6. **Persistencia**
   Estados, backlog, historial y deduplicación.

---

# 36. Anexo A — Resumen ultra corto para stakeholders

Halltic Reddit Opportunity Assistant es un sistema interno que revisa Reddit una vez al día, detecta hasta 10 oportunidades útiles relacionadas con Odoo, genera respuestas sugeridas con ayuda de IA y se las envía al equipo de marketing para que las publique manualmente.

No publica solo. No conversa solo. No hace seguimiento. Su foco es ahorrar tiempo de scouting, mantener presencia útil y proteger la calidad técnica de la marca.

---

# 37. Anexo B — Frases guía permitidas

Estas fórmulas son coherentes con el tono y la política del producto:

- “Depende bastante de la versión de Odoo.”
- “Yo revisaría primero X e Y.”
- “Sin ver el traceback es difícil afinar más.”
- “Si compartes algo más de contexto, se puede concretar mejor.”
- “En Odoo 19 eso ahora va más por este otro lado.”
- “Si la parte de implantación se os complica, en Halltic solemos trabajar con este tipo de casos.”

---

# 38. Anexo C — Líneas rojas del sistema

El sistema no debe:

- inventar comportamiento de Odoo,
- sonar comercial sin contexto,
- parecer un bot evidente,
- responder por cubrir cupo si no hay valor real,
- desarrollar gratis soluciones complejas,
- entrar en temas sensibles o irrelevantes,
- defender lo indefendible de forma poco objetiva.

---

# 39. Cierre

Este documento define el diseño de producto final acordado con el Product Owner. Su propósito es servir como base única para que el equipo responsable:

1. analice la viabilidad técnica real,
2. proponga arquitectura,
3. diseñe el flujo operativo,
4. y descomponga el sistema en entregables de implementación.

Cualquier decisión técnica futura deberá respetar los principios de producto aquí fijados, especialmente:

- precisión técnica sobre volumen,
- publicación manual,
- tono forero profesional,
- y utilidad real para la comunidad.

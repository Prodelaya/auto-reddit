# auto-reddit

## 1. Fuente de verdad

Este documento es la fuente de verdad del producto para el primer slice de `auto-reddit`.

Para la estrategia operativa de APIs de Reddit, la referencia vigente es `docs/integrations/reddit/api-strategy.md`.

Las reglas de comportamiento, tono y criterios de intervención de la IA se mantienen en un documento separado: `docs/product/ai-style.md`. Ese documento complementa este artefacto, pero no sustituye las decisiones de producto definidas aquí.

## 2. Visión

Crear un sistema que ayude al equipo de marketing y contenido a detectar, cada día, oportunidades reales de participación en Reddit alrededor de Odoo, entregadas con contexto suficiente para que un humano decida si intervenir manualmente.

## 3. Usuario y canal

- Usuario principal: equipo de marketing y contenido.
- Canal de entrega: Telegram.
- Frecuencia: diaria.
- La publicación final en Reddit queda fuera de este slice y sigue siendo manual.

## 4. Fuente inicial

- Fuente inicial: `r/Odoo`.
- El sistema solo analiza oportunidades dentro de esa comunidad en esta primera versión.

## 5. Objetivo operativo del primer slice

Cada día, el sistema recoge TODOS los posts SOLO de `r/Odoo` cuya creación esté dentro de los últimos 7 días, los normaliza para el pipeline interno y delega aguas abajo la exclusión por memoria operativa y el recorte diario a 8 candidatos para revisión.

La entrega diaria debe priorizar utilidad operativa y criterio de intervención, no volumen.

> **Nota:** los límites de revisión diaria (8 posts) y envío diario (8 oportunidades) siguen siendo parámetros operativos revisables, pero la referencia vigente para design pasa a 8/día por capacidad de cuota. Con ejecución de lunes a viernes (~22 días/mes), el happy path queda en ~198 req/mes y deja margen frente a las ~220 req/mes útiles actuales.

## 6. Flujo del producto

1. Obtener todos los posts de `r/Odoo`.
2. Filtrar para considerar solo posts cuya creación esté dentro de los últimos 7 días.
3. Normalizar cada post al contrato interno mínimo y conservar los incompletos con marca explícita.
4. Excluir por memoria operativa los posts ya decididos como `sent` o `rejected`.
5. Tomar para revisión diaria los 8 posts elegibles más recientes ordenados por fecha de creación.
6. Evaluar cada uno con IA para decidir si representa una oportunidad válida.
7. Recuperar comentarios SOLO para los posts seleccionados aguas arriba cuando haga falta contexto de hilo para la evaluación.
8. Excluir posts resueltos, cerrados, redundantes o no aptos para intervención.
9. Generar la información de oportunidad para los posts válidos.
10. Enviar por Telegram un resumen inicial del lote diario y después un mensaje por cada oportunidad seleccionada.
11. Registrar memoria operativa mínima para no reenviar posts ya enviados ni reabrir descartes finales.

## 7. Reglas de selección

### 7.1 Días de ejecución

El sistema solo ejecuta de lunes a viernes. Si la ejecución se lanza un sábado o domingo, termina sin hacer ninguna llamada a APIs ni enviar nada a Telegram. Esta lógica vive en `main.py`, no en el cron externo.

### 7.3 Ventana temporal

Solo se consideran posts cuya creación esté dentro de la ventana configurada por `review_window_days` (valor operativo por defecto: 7 días). El parámetro `review_window_days` en `config/settings.py` es la fuente de verdad que gobierna el recorte temporal tanto en colección como en toda la documentación.

### 7.4 Tamaño de la revisión diaria

La recolección inicial conserva todos los posts dentro de la ventana configurada por `review_window_days`.

El recorte diario ocurre después de aplicar memoria operativa mínima: cada día se revisan con IA los 8 posts elegibles más recientes ordenados por fecha de creación, no por última actividad.

No existe un backlog editorial explícito ni un estado `approved`. Si un post no se selecciona hoy pero sigue dentro de la ventana configurada por `review_window_days` y no está marcado como `sent` ni como `rejected`, mañana vuelve a competir normalmente desde la ventana.

### 7.5 Límite de envío diario

- Se envían como máximo `max_daily_opportunities` oportunidades al día. El parámetro `max_daily_opportunities` en `config/settings.py` es la única fuente de verdad para este límite (valor operativo por defecto: 8).
- Si de los revisados solo hay 3 válidos, se envían solo 3.

### 7.6 Regla de unicidad

Cada post solo se envía una vez.

Esto requiere un histórico operativo mínimo para recordar qué posts ya fueron enviados. Ese mínimo operativo sí forma parte del slice, pero no se considera almacenamiento histórico largo como feature de producto.

Los estados operativos mínimos relevantes son:

- `sent`: el post ya fue enviado a Telegram y no vuelve a competir.
- `rejected`: rechazo final de negocio por la IA; el sistema concluye que no aplica respuesta, que el post está cerrado o que no merece intervención y no debe volver a procesarse.

`not selected today` no es un estado persistente ni equivale a `rejected`.

Si Telegram falla después de que la IA haya aceptado una sugerencia, el comportamiento correcto es reintentar el envío sin reevaluar la IA.

### 7.7 Regla de corte cuando haya más de 8 válidos

Si hubiese más de 8 posts válidos en la revisión diaria, el corte se resuelve así:

1. Priorizar primero los no resueltos.
2. Dentro de ese grupo, priorizar por recencia.

## 8. Definición de hilo resuelto o cerrado

Un hilo se considera resuelto o cerrado cuando se cumple una de estas reglas:

- El autor dice explícitamente que ya lo solucionó.
- Si no existe esa confirmación explícita del autor, deben darse al menos dos de estas señales de cierre:
  - Otro usuario ya dio una respuesta clara y útil.
  - La conversación muestra cierre evidente.
  - Ya existe una recomendación sólida y añadir otra respuesta sería redundante.

## 9. Regla de intervención

La IA solo debe sugerir respuesta si puede aportar algo relevante, contextual y no redundante.

Los criterios detallados de cómo comportarse, cuándo intervenir y qué evitar se documentan en `ai-style.md`.

## 10. Formato de salida en Telegram

La entrega diaria en Telegram debe tener esta estructura:

- 1 mensaje inicial de resumen (se emite siempre en cada ejecución de día laborable, incluso si no hay oportunidades seleccionadas).
- 1 mensaje por oportunidad (solo cuando hay oportunidades).

El mensaje inicial de resumen debe incluir:

- fecha
- número de oportunidades
- número de posts revisados

Cada oportunidad debe incluir estos campos:

- título del post
- link
- idioma del post
- tipo de oportunidad
- resumen breve del post
- resumen breve de comentarios
- respuesta sugerida

La taxonomía actual de tipos de oportunidad se mantiene como lista cerrada. Los valores válidos son:

- funcionalidad y configuración de Odoo
- desarrollo
- dudas sobre si merece la pena Odoo
- comparativas con otras opciones

La salida debe priorizar operatividad interna sin bloquear la adaptación al contexto real del hilo.

- El sistema identifica y muestra el idioma original del post.
- Los resúmenes operativos del post y de los comentarios se entregan en español para el equipo interno.
- La respuesta sugerida se genera en dos versiones equivalentes: español e inglés.
- La publicación final y la adaptación de la respuesta al hilo siguen siendo decisión humana.

## 11. Alcance del primer slice

### Dentro de alcance

- Revisión diaria de `r/Odoo`.
- Filtrado por fecha de creación en los últimos 7 días.
- Recolección inicial de todos los posts de `r/Odoo` dentro de la ventana de 7 días.
- Normalización interna de candidatos con tolerancia a campos faltantes.
- Evaluación diaria de los 8 posts elegibles más recientes ordenados por fecha de creación.
- Recuperación de comentarios solo para los posts ya seleccionados para el flujo posterior.
- Selección y envío de hasta 8 oportunidades válidas al día.
- Entrega por Telegram con formato resumido y accionable.
- Generación de respuesta sugerida cuando aporte valor real.
- Memoria operativa mínima para no reenviar posts ya enviados ni reprocesar descartes finales.

### Fuera de alcance

- Almacenamiento histórico largo.
- Scoring o priorización avanzada.
- Seguimiento automático de posts.
- Caso `post antiguo pero vivo`.
- Autopublicación.

## 12. Criterios de aceptación

El primer slice se considera correcto cuando:

- Usa `r/Odoo` como fuente inicial.
- Conserva inicialmente todos los posts de `r/Odoo` dentro de la ventana de 7 días.
- Normaliza los candidatos al contrato interno mínimo y conserva los incompletos con marca explícita.
- Entrega diariamente oportunidades por Telegram al equipo de marketing y contenido.
- Excluye antes de la revisión los posts ya decididos como `sent` o `rejected`.
- Revisa cada día los 8 posts elegibles más recientes ordenados por fecha de creación.
- Solo considera posts cuya creación esté dentro de los últimos 7 días.
- No envía más de 8 oportunidades al día.
- Si hay menos oportunidades válidas, envía solo las válidas detectadas.
- No reenvía un mismo post más de una vez.
- Si un post no se selecciona en una ejecución pero sigue dentro de los 7 días y no fue marcado como `sent` ni `rejected`, vuelve a competir normalmente al día siguiente.
- Si hay más de 8 válidas, prioriza no resueltos y después recencia.
- Excluye hilos resueltos o cerrados según la definición de este documento.
- Si Telegram falla tras una aceptacion de IA, reintenta el envio sin reevaluar la IA.
- El mensaje inicial de Telegram incluye fecha, número de oportunidades y número de posts revisados.
- El campo `tipo de oportunidad` usa la lista cerrada definida en este documento.
- Solo genera respuesta sugerida cuando puede aportar algo relevante, contextual y no redundante.
- Cada oportunidad incluye título, link, idioma del post, tipo, resumen del post, resumen de comentarios y respuesta sugerida.
- Los resúmenes operativos se entregan en español para el equipo interno.
- La respuesta sugerida se entrega en versión española e inglesa.
- La publicación final y la adaptación al hilo siguen siendo decisión humana.
- Las reglas de estilo y comportamiento de IA quedan referenciadas y separadas en `ai-style.md`.

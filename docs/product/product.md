# auto-reddit

## 1. Fuente de verdad

Este documento es la fuente de verdad del producto para el primer slice de `auto-reddit`.

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

Cada día, el sistema revisa los 20 posts no enviados más recientes de `r/Odoo`, ordenados por fecha de creación, y selecciona oportunidades válidas para enviar al equipo por Telegram.

La entrega diaria debe priorizar utilidad operativa y criterio de intervención, no volumen.

## 6. Flujo del producto

1. Obtener los posts de `r/Odoo`.
2. Filtrar para considerar solo posts cuya creación o comentarios estén dentro de los últimos 7 días.
3. Tomar para revisión diaria los 20 posts no enviados más recientes ordenados por fecha de creación.
4. Evaluar cada uno con IA para decidir si representa una oportunidad válida.
5. Excluir posts resueltos, cerrados, redundantes o no aptos para intervención.
6. Generar la información de oportunidad para los posts válidos.
7. Enviar por Telegram un resumen inicial del lote diario y después un mensaje por cada oportunidad seleccionada.
8. Registrar memoria operativa mínima para no reenviar posts ya enviados.

## 7. Reglas de selección

### 7.1 Ventana temporal

Solo se consideran posts cuya creación o comentarios estén dentro de los últimos 7 días.

### 7.2 Tamaño de la revisión diaria

Cada día se revisan con IA los 20 posts no enviados más recientes ordenados por fecha de creación, no por última actividad.

### 7.3 Límite de envío diario

- Se envían como máximo 15 oportunidades al día.
- Si de los 20 revisados solo hay 3 válidos, se envían solo 3.

### 7.4 Regla de unicidad

Cada post solo se envía una vez.

Esto requiere un histórico operativo mínimo para recordar qué posts ya fueron enviados. Ese mínimo operativo sí forma parte del slice, pero no se considera almacenamiento histórico largo como feature de producto.

### 7.5 Regla de corte cuando haya más de 15 válidos

Si hubiese más de 15 posts válidos en la revisión diaria, el corte se resuelve así:

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

- 1 mensaje inicial de resumen.
- 1 mensaje por oportunidad.

El mensaje inicial de resumen debe incluir:

- fecha
- número de oportunidades
- número de posts revisados

Cada oportunidad debe incluir estos campos:

- título del post
- link
- tipo de oportunidad
- resumen breve del post
- resumen breve de comentarios
- respuesta sugerida

La taxonomía actual de tipos de oportunidad se mantiene como lista cerrada. Los valores válidos son:

- funcionalidad y configuración de Odoo
- desarrollo
- dudas sobre si merece la pena Odoo
- comparativas con otras opciones

La respuesta sugerida debe ir en el idioma original del post.

## 11. Alcance del primer slice

### Dentro de alcance

- Revisión diaria de `r/Odoo`.
- Filtrado por actividad en los últimos 7 días.
- Evaluación diaria de los 20 posts no enviados más recientes ordenados por fecha de creación.
- Selección y envío de hasta 15 oportunidades válidas al día.
- Entrega por Telegram con formato resumido y accionable.
- Generación de respuesta sugerida cuando aporte valor real.
- Memoria operativa mínima para no reenviar posts ya enviados.

### Fuera de alcance

- Almacenamiento histórico largo.
- Scoring o priorización avanzada.
- Seguimiento automático de posts.
- Autopublicación.

## 12. Criterios de aceptación

El primer slice se considera correcto cuando:

- Usa `r/Odoo` como fuente inicial.
- Entrega diariamente oportunidades por Telegram al equipo de marketing y contenido.
- Revisa cada día los 20 posts no enviados más recientes ordenados por fecha de creación.
- Solo considera posts cuya creación o comentarios estén dentro de los últimos 7 días.
- No envía más de 15 oportunidades al día.
- Si hay menos oportunidades válidas, envía solo las válidas detectadas.
- No reenvía un mismo post más de una vez.
- Si hay más de 15 válidas, prioriza no resueltos y después recencia.
- Excluye hilos resueltos o cerrados según la definición de este documento.
- El mensaje inicial de Telegram incluye fecha, número de oportunidades y número de posts revisados.
- El campo `tipo de oportunidad` usa la lista cerrada definida en este documento.
- Solo genera respuesta sugerida cuando puede aportar algo relevante, contextual y no redundante.
- Cada oportunidad incluye título, link, tipo, resumen del post, resumen de comentarios y respuesta sugerida.
- La respuesta sugerida está en el idioma original del post.
- Las reglas de estilo y comportamiento de IA quedan referenciadas y separadas en `ai-style.md`.

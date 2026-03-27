# Proposal: Reddit Candidate Collection

## Intent

Establecer el slice base del pipeline diario: recoger todos los posts recientes de `r/Odoo` y entregarlos como candidatos normalizados para que los cambios posteriores apliquen memoria, recorte y evaluacion.

## Scope

### In Scope
- Recoger solo posts de `r/Odoo` creados en los ultimos 7 dias.
- Priorizar la salida por recencia y normalizar cada post al contrato minimo compartido.
- Conservar posts incompletos con una marca explicita y entregar la lista en memoria/proceso.

### Out of Scope
- Comentarios, caso `old but alive`, memoria operativa y exclusiones por `sent` o `rejected`.
- Recorte a 8 candidatos, evaluacion IA y entrega por Telegram.

## Approach

Separar la recoleccion inicial como una etapa propia del pipeline. Esta etapa consulta Reddit, filtra por `created_at` dentro de 7 dias, adapta variaciones de shape al contrato minimo (`post_id`, `title`, `body/selftext`, `url/permalink`, `author`, `subreddit`, `created_at`) y propaga tambien los registros incompletos con estado explicito para no perder cobertura aguas abajo.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src/auto_reddit/reddit/` | Modified | Recoleccion y filtrado temporal de posts de `r/Odoo`. |
| `src/auto_reddit/shared/` | Modified | Contrato interno de candidato normalizado e indicador de incompleto. |
| `src/auto_reddit/main.py` | Modified | Encadenado del paso de recoleccion con el resto del flujo. |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Mezclar este slice con el recorte a 8 | Med | Mantener el done criteria centrado en cobertura completa del rango de 7 dias. |
| Perder posts utiles por respuestas heterogeneas de Reddit | Med | Exigir normalizacion tolerante y marca explicita de incompleto en vez de descarte. |

## Rollback Plan

Revertir la etapa a la fuente previa de candidatos y eliminar este cambio sin tocar las reglas aguas abajo de memoria, IA o delivery.

## Dependencies

- Acceso operativo a Reddit segun `docs/integrations/reddit/api-strategy.md`.
- Continuidad del pipeline con el change `candidate-memory-and-uniqueness` como consumidor inmediato.

## Success Criteria

- [ ] El cambio entrega todos los posts de `r/Odoo` dentro de la ventana de 7 dias, ordenados por recencia.
- [ ] Cada candidato sale con el contrato minimo o con marca explicita de incompleto.
- [ ] La salida no incluye comentarios ni aplica el recorte a 8 en esta fase.

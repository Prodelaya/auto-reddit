# Proposal: Thread Context Extraction

## Intent

Separar la obtencion de contexto del hilo de la evaluacion IA, recuperando solo para posts ya seleccionados aguas arriba un contexto bruto normalizado que permita a change 4 decidir con mas senal y sin acoplar lectura de APIs al modulo de evaluacion.

## Scope

### In Scope
- Extraer post + comentarios/contexto solo para los posts supervivientes al recorte diario aguas arriba.
- Normalizar el material recuperado a un contrato comun de contexto bruto, sin resumirlo.
- Exponer un indicador simple de degradacion y descartar del batch cualquier post cuyo contexto falle en todas las APIs previstas.

### Out of Scope
- Recoleccion inicial, filtrado de memoria operativa y recorte diario.
- Decidir oportunidad, estado resuelto/cerrado o comportamiento de entrega/publicacion.
- Fijar como requisito una profundidad exacta de comentarios/replies no confirmada por la documentacion real de providers.

## Approach

Insertar un paso intermedio despues de la seleccion diaria que aplique la estrategia vigente de APIs/fallbacks para enriquecer cada post seleccionado, transforme respuestas heterogeneas a un contrato comun y marque si el contexto llega completo o degradado. La revision de profundidad/shape real por provider queda como recomendacion obligatoria para spec/design, no como requisito inventado en proposal.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `openspec/specs/reddit-candidate-collection/spec.md` | Dependency | Mantiene la frontera: change 1 no trae comentarios. |
| `openspec/specs/candidate-memory/spec.md` | Dependency | Define que solo los 8 posts elegibles pasan aguas abajo. |
| `change 3 pipeline handoff` | Modified | Añade enriquecimiento de contexto antes de la evaluacion IA. |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Mezclar extraccion con juicio editorial | Medium | Mantener fuera decisiones de oportunidad/cierre/delivery. |
| Tratar contexto parcial como completo | Medium | Hacer obligatorio el indicador simple de degradacion. |
| Convertir dudas de provider en requisitos falsos | High | Llevar la revision de depth/shape como recomendacion para spec/design. |

## Rollback Plan

Retirar este paso del pipeline y volver al handoff actual de posts seleccionados sin contexto adicional, manteniendo intactas la coleccion inicial, la memoria operativa y la evaluacion/delivery downstream.

## Dependencies

- `openspec/discovery/thread-context-extraction.md`
- `openspec/specs/reddit-candidate-collection/spec.md`
- `openspec/specs/candidate-memory/spec.md`

## Success Criteria

- [ ] Solo se intenta extraer contexto para posts ya seleccionados aguas arriba.
- [ ] La salida es contexto bruto normalizado con indicador simple de degradacion.
- [ ] Si todas las APIs de contexto fallan para un post, ese post se excluye del batch.
- [ ] El proposal deja explicitamente fuera oportunidad, cierre/resolucion y delivery.
- [ ] Spec/design deberan revisar y recomendar la profundidad/shape real por provider.

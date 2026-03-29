# settings-govern-runtime

Asegurar que cada setting del proyecto realmente gobierne el comportamiento en runtime (ninguno decorativo, duplicado ni sin efecto).

## Investigar:

- Qué settings existen actualmente y dónde se definen (`.env`, `config.py`, modelos Pydantic)
- Cuáles no tienen ningún consumidor real en el código de ejecución
- Cuáles están duplicados o con nombre inconsistente entre capas
- Cuáles carecen de documentación o valor por defecto explícito
- Si la configuración se valida al arranque o puede fallar silenciosamente en runtime

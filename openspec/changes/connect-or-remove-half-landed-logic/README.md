# connect-or-remove-half-landed-logic

Identificar y resolver toda lógica parcialmente implementada: conectarla correctamente al flujo real o eliminarla si es código muerto.

## Investigar:

- Rutas de código, ramas o flags que existen pero nunca se invocan desde ningún punto de entrada
- Módulos importados pero sin consumidores activos
- Funciones con implementación incompleta (TODOs, `pass`, raises sin manejo)
- Integraciones que se inicializan pero cuyo resultado se descarta o ignora
- Inconsistencias de cableado: lógica presente en un lado del contrato pero ausente en el otro

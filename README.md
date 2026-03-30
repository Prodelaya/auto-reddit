<p align="center">
  <img src="assets/auto-reddit-logo.png" alt="auto-reddit" width="200">
</p>

# auto-reddit

## Descripción general del proyecto

auto-reddit es un sistema de detección diaria de oportunidades de participación en Reddit para equipos de marketing y contenido que trabajan con Odoo.

El producto resuelve un problema operativo concreto: seguir manualmente Reddit para detectar posts donde una empresa con experiencia en Odoo puede aportar valor es costoso en tiempo y difícil de sistematizar. auto-reddit automatiza esa vigilancia y entrega cada día un conjunto de oportunidades filtradas y evaluadas, directamente en Telegram, con el contexto suficiente para que un humano decida si intervenir.

El principio rector del producto es claro: **la IA propone, el humano decide y publica**. El sistema nunca publica en Reddit de forma autónoma. Su única función es reducir el trabajo de detección y preparación, dejando el criterio y la acción final siempre en manos del equipo.

El usuario principal es el equipo de marketing y contenido. La fuente de datos del primer slice es `r/Odoo`.

La referencia operativa vigente para la integración con Reddit es `docs/integrations/reddit/api-strategy.md`.

Mapa completo de documentación para maintainers: [`docs/README.md`](docs/README.md).

---

## Stack tecnológico

| Componente | Tecnología |
|---|---|
| Lenguaje | Python 3.14 |
| Gestor de dependencias | uv |
| Despliegue | Docker en VPS (contenedor efímero + cron externo) |
| Persistencia | SQLite (fichero en volumen Docker) |
| Contratos internos | Pydantic |
| Configuración y secretos | pydantic-settings + `.env` |
| Evaluación IA | DeepSeek vía SDK de OpenAI |
| Notificaciones | Telegram Bot API |
| Fuente de datos | RapidAPI (reddit3, reddit34, reddapi, reddit-com) |

El modelo operativo es un contenedor efímero: arranca, ejecuta el proceso diario completo y muere. No hay proceso persistente corriendo en segundo plano. El cron externo en el VPS se encarga de la planificación.

---

## Instalación y ejecución

El repositorio ya contiene el scaffolding inicial del proyecto y la documentación operativa principal.

Los comandos base de trabajo son:

```bash
uv sync
cp .env.example .env
uv run pytest tests/ -x --tb=short
```

---

## Estructura del proyecto

```
auto-reddit/
├── assets/
│   └── auto-reddit-logo.png
├── src/
│   └── auto_reddit/
│       ├── __init__.py
│       ├── main.py               # orquestador del proceso diario
│       ├── reddit/               # extracción de candidatos y contexto
│       │   └── client.py
│       ├── evaluation/           # evaluación IA con DeepSeek
│       │   └── evaluator.py
│       ├── delivery/             # entrega por Telegram
│       │   └── telegram.py
│       ├── persistence/          # memoria operativa SQLite
│       │   └── store.py
│       ├── shared/               # contratos Pydantic compartidos
│       │   └── contracts.py
│       └── config/               # settings con pydantic-settings
│           └── settings.py
├── tests/
│   ├── test_reddit/
│   ├── test_evaluation/
│   ├── test_delivery/
│   └── test_persistence/
├── docs/
│   ├── architecture.md           # decisiones arquitectónicas
│   ├── integrations/
│   │   └── reddit/
│   │       ├── comparison.md     # comparativa de APIs evaluadas
│   │       └── api-strategy.md   # estrategia vigente de selección y fallback
│   ├── product/
│   │   ├── product.md            # fuente de verdad del producto
│   │   └── ai-style.md           # comportamiento y estilo de la IA
│   └── discovery/                # documentación histórica de ideación
├── openspec/                     # planning SDD por changes
├── TFM/                          # documentación académica del proyecto
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Funcionalidades principales

- **Detección diaria de oportunidades en `r/Odoo`**: cada día el sistema recoge todos los posts de `r/Odoo` dentro de los últimos 7 días, los normaliza para el pipeline interno y, aguas abajo, revisa como máximo 8 candidatos elegibles priorizados por recencia.
- **Filtrado por categorías de oportunidad**: los posts se clasifican en una taxonomía cerrada: funcionalidad y configuración de Odoo, desarrollo, dudas sobre si merece la pena Odoo, y comparativas con otras opciones.
- **Evaluación por IA**: DeepSeek evalúa cada candidato para decidir si representa una oportunidad válida, resume el contexto en español para el equipo interno e incluye una respuesta sugerida en español y otra en inglés para revisión humana.
- **Entrega diaria por Telegram**: el equipo recibe un mensaje de resumen con la fecha, el número de posts revisados y el número de oportunidades detectadas, seguido de un mensaje por cada oportunidad con título, enlace, idioma del post, tipo, resumen y respuesta sugerida.
- **Contexto del hilo bajo demanda**: los comentarios se recuperan solo para los posts seleccionados aguas arriba para el flujo posterior; no forman parte de la recolección inicial de candidatos.
- **Control de duplicados e idempotencia mínima**: cada post se registra y se envía una sola vez. No existe backlog explícito ni estado `approved`; `rejected` es descarte final de negocio, `not selected today` no es un estado persistente, y si Telegram falla tras una aceptación de IA se reintenta el envío sin reevaluar.

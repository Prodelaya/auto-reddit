# auto-reddit

## Descripción general del proyecto

auto-reddit es un sistema de detección diaria de oportunidades de participación en Reddit para equipos de marketing y contenido que trabajan con Odoo.

El producto resuelve un problema operativo concreto: seguir manualmente Reddit para detectar posts donde una empresa con experiencia en Odoo puede aportar valor es costoso en tiempo y difícil de sistematizar. auto-reddit automatiza esa vigilancia y entrega cada día un conjunto de oportunidades filtradas y evaluadas, directamente en Telegram, con el contexto suficiente para que un humano decida si intervenir.

El principio rector del producto es claro: **la IA propone, el humano decide y publica**. El sistema nunca publica en Reddit de forma autónoma. Su única función es reducir el trabajo de detección y preparación, dejando el criterio y la acción final siempre en manos del equipo.

El usuario principal es el equipo de marketing y contenido. La fuente de datos del primer slice es `r/Odoo`.

---

## Stack tecnológico

| Componente | Tecnología |
|---|---|
| Lenguaje | Python 3.12 |
| Gestor de dependencias | uv |
| Despliegue | Docker en VPS (contenedor efímero + cron externo) |
| Persistencia | SQLite (fichero en volumen Docker) |
| Contratos internos | Pydantic |
| Configuración y secretos | pydantic-settings + `.env` |
| Evaluación IA | DeepSeek vía SDK de OpenAI |
| Notificaciones | Telegram Bot API |
| Fuente de datos | Reddit APIs REST |

El modelo operativo es un contenedor efímero: arranca, ejecuta el proceso diario completo y muere. No hay proceso persistente corriendo en segundo plano. El cron externo en el VPS se encarga de la planificación.

---

## Instalación y ejecución

El proyecto está actualmente en fase de definición y diseño. El código fuente y el Dockerfile aún no existen.

Esta sección se actualizará con las instrucciones completas de instalación y ejecución cuando el scaffolding esté listo. Los comandos de referencia que tendrán sentido una vez implementado el proyecto serán:

```bash
uv sync
cp .env.example .env
docker compose up
```

---

## Estructura del proyecto

```
auto-reddit/
├── docs/
│   ├── architecture.md       # decisiones arquitectónicas
│   ├── product/
│   │   ├── product.md        # fuente de verdad del producto
│   │   └── ai-style.md       # comportamiento y estilo de la IA
│   └── discovery/            # documentación histórica de ideación
├── openspec/                 # planning SDD por changes
│   ├── changes/              # un directorio por change
│   └── specs/                # specs globales del sistema
├── TFM/                      # documentación académica del proyecto
└── README.md
```

---

## Funcionalidades principales

- **Detección diaria de oportunidades en `r/Odoo`**: cada día el sistema revisa los 20 posts no enviados más recientes con actividad en los últimos 7 días.
- **Filtrado por categorías de oportunidad**: los posts se clasifican en una taxonomía cerrada: funcionalidad y configuración de Odoo, desarrollo, dudas sobre si merece la pena Odoo, y comparativas con otras opciones.
- **Evaluación por IA**: DeepSeek evalúa cada candidato para decidir si representa una oportunidad válida, genera un resumen del post y sus comentarios, y propone una respuesta sugerida en el idioma original del post.
- **Entrega diaria por Telegram**: el equipo recibe un mensaje de resumen con la fecha, el número de posts revisados y el número de oportunidades detectadas, seguido de un mensaje por cada oportunidad con título, enlace, tipo, resumen y respuesta sugerida.
- **Control de duplicados**: cada post se registra y se envía una sola vez. Los posts ya enviados, aprobados o rechazados no se vuelven a evaluar.
- **Gestión de cola diaria**: si en una jornada se detectan más oportunidades válidas de las que se pueden enviar (máximo 15 al día), los posts aprobados pendientes se retoman al día siguiente sin necesidad de reevaluar con IA.

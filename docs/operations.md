# Operations Runbook — auto-reddit

Guía de referencia para ejecutar, programar y diagnosticar el sistema en un VPS dockerizado.

---

## Execution Model

auto-reddit sigue el patrón de **contenedor efímero**:

- El contenedor arranca, ejecuta el pipeline completo (fetch → evaluate → notify) y muere.
- No hay proceso persistente corriendo 24/7.
- El estado (posts ya enviados) se persiste en un volumen Docker montado en `/data/`.
- El cron del VPS lanza el contenedor una vez al día.

```
VPS cron
  └─→ docker compose run --rm auto-reddit
        ├─ lee .env (secretos del operador)
        ├─ environment: DB_PATH=/data/auto_reddit.db  ← impuesto por compose
        ├─ monta sqlite_data:/data
        └─ escribe /data/auto_reddit.db  ← persiste entre ejecuciones
```

> **DB_PATH garantizado**: `docker-compose.yml` define `environment: DB_PATH=/data/auto_reddit.db`,
> que toma precedencia sobre `env_file: .env`. Aunque `.env` no defina `DB_PATH`, la ruta
> correcta queda asegurada a nivel de infraestructura.

---

## Prerequisites

1. **Docker + Docker Compose** instalados en el VPS.
2. Repositorio clonado:
   ```bash
   git clone <repo-url> /opt/auto-reddit
   cd /opt/auto-reddit
   ```
3. Variables de entorno configuradas:
   ```bash
   cp .env.example .env
   # Editar .env y rellenar la sección REQUIRED:
   #   DEEPSEEK_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, REDDIT_API_KEY
   ```
4. Imagen construida:
   ```bash
   docker compose build
   ```

---

## Cron Setup

Añadir a la crontab del usuario del VPS (`crontab -e`):

```cron
# auto-reddit — ejecutar el pipeline cada día a las 08:00 UTC
0 8 * * * cd /opt/auto-reddit && docker compose run --rm auto-reddit >> /var/log/auto-reddit.log 2>&1
```

Ajustar la hora y la ruta al directorio del proyecto según el entorno.

Para verificar que la tarea se registró correctamente:
```bash
crontab -l
```

---

## Volume Verification

Comprobar que el volumen SQLite existe y contiene la base de datos:

```bash
# Listar volúmenes Docker
docker volume ls | grep sqlite_data

# Inspeccionar la ruta real del volumen en el host
docker volume inspect auto-reddit_sqlite_data

# Verificar que el fichero de base de datos existe dentro del volumen
docker run --rm -v auto-reddit_sqlite_data:/data alpine ls -lh /data/
```

La salida esperada incluye `auto_reddit.db` con un tamaño mayor de 0 bytes tras la primera ejecución.

---

## Troubleshooting

### El contenedor arranca pero no guarda estado entre ejecuciones

**Síntoma**: Posts ya notificados vuelven a aparecer al día siguiente.

**Causas y soluciones**:

| Causa | Diagnóstico | Solución |
|-------|-------------|----------|
| `sqlite_data` no montado | `docker compose config` → verificar `volumes:` | Asegurarse de que `docker-compose.yml` tiene `sqlite_data:/data` |
| `DB_PATH` apunta a ruta efímera | `docker compose config` → buscar `DB_PATH` en `environment:` | Debe mostrar `DB_PATH=/data/auto_reddit.db` |
| Volumen inexistente | `docker volume ls \| grep sqlite_data` devuelve vacío | Ejecutar `docker compose run --rm auto-reddit` al menos una vez para crearlo |

### `DB_PATH` vacío o incorrecto en runtime

**Síntoma**: Log de inicio muestra una ruta distinta a `/data/auto_reddit.db`.

**Diagnóstico**:
```bash
docker compose run --rm auto-reddit env | grep DB_PATH
```

**Solución**: La sección `environment:` en `docker-compose.yml` debe existir con:
```yaml
environment:
  - DB_PATH=/data/auto_reddit.db
```

### Falta un secreto requerido

**Síntoma**: El contenedor muere con `ValidationError` o `pydantic.ValidationError` al arrancar.

**Diagnóstico**:
```bash
# Ver el error completo
docker compose run --rm auto-reddit 2>&1 | head -30
```

**Solución**: Rellenar todas las variables de la sección `REQUIRED` en `.env`:
- `DEEPSEEK_API_KEY`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `REDDIT_API_KEY`

### El cron no ejecuta el contenedor

**Síntoma**: No hay logs en `/var/log/auto-reddit.log` a la hora programada.

**Checklist**:
- [ ] `crontab -l` muestra la línea correcta
- [ ] La ruta en `cd /opt/auto-reddit` existe y contiene `docker-compose.yml`
- [ ] El usuario del cron tiene permisos para ejecutar `docker compose`
- [ ] `docker compose run --rm auto-reddit` funciona manualmente desde esa ruta

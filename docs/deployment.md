# Despliegue en servidor Ubuntu propio

Este documento describe el proceso de despliegue real de auto-reddit en un servidor Ubuntu 24.04 propio, ejecutado el 3 de abril de 2026.

## Entorno objetivo

- **Servidor:** Ubuntu 24.04 LTS (propio, acceso SSH)
- **Ruta de instalación:** `/opt/auto-reddit`
- **Modelo operativo:** contenedor efímero + cron externo

## Pasos realizados

### 1. Clonar el repositorio

El servidor tenía bloqueado el puerto 22 (SSH), por lo que se usó HTTPS en lugar de SSH:

```bash
cd /opt
sudo git clone https://github.com/Prodelaya/auto-reddit.git
cd auto-reddit
```

> **Nota:** Si el repo fuera privado, habría que usar un token de GitHub en lugar de contraseña.

### 2. Instalar Docker

Docker no estaba instalado en el servidor. Se instaló con apt:

```bash
sudo apt install -y docker.io docker-compose-v2
```

Versiones instaladas:
- Docker: 28.2.2
- Docker Compose: 2.37.1

### 3. Configurar variables de entorno

```bash
sudo cp .env.example .env
sudo nano .env
```

Variables obligatorias a rellenar:

| Variable | Descripción |
|---|---|
| `DEEPSEEK_API_KEY` | API key de DeepSeek |
| `TELEGRAM_BOT_TOKEN` | Token del bot de Telegram |
| `TELEGRAM_CHAT_ID` | ID del chat de Telegram |
| `REDDIT_API_KEY` | API key de RapidAPI |

### 4. Construir y verificar

```bash
sudo docker compose up --build
```

La primera ejecución construye la imagen y lanza el pipeline completo. Si termina con `exited with code 0` y los mensajes llegan a Telegram, el despliegue es correcto.

**Salida esperada al final:**

```
auto-reddit-1  | INFO __main__: Pipeline completado
auto-reddit-1 exited with code 0
```

### 5. Configurar el cron

El pipeline es un proceso efímero: arranca, ejecuta y muere. La ejecución diaria la gestiona un cron en el servidor.

```bash
sudo crontab -e
```

Añadir al final:

```
30 10 * * * cd /opt/auto-reddit && docker compose up >> /var/log/auto-reddit.log 2>&1
```

Esto ejecuta el pipeline todos los días a las **10:30 (hora del servidor)**.

Verificar que quedó guardado:

```bash
sudo crontab -l
```

## Funcionamiento diario

Cada día a las 10:30 el cron:

1. Entra en `/opt/auto-reddit`
2. Levanta el contenedor Docker
3. El pipeline ejecuta el proceso completo (recolección → evaluación IA → entrega Telegram)
4. El contenedor termina solo al acabar
5. Los logs se acumulan en `/var/log/auto-reddit.log`

> **Nota sobre fines de semana:** El guard de fin de semana está en `main.py` (`weekday >= 5`), no en el cron. El cron corre los 7 días; es el propio script quien decide si ejecutar o no.

## Persistencia

La base de datos SQLite vive en un volumen Docker que persiste entre ejecuciones:

```bash
docker volume ls  # debe aparecer auto-reddit_sqlite_data
```

Los posts ya entregados no se vuelven a enviar gracias a este volumen.

## Consultar logs

```bash
# Ver logs acumulados
cat /var/log/auto-reddit.log

# Seguir en tiempo real (durante una ejecución)
tail -f /var/log/auto-reddit.log

# Logs del último contenedor
sudo docker compose logs auto-reddit
```

> El fichero de log se crea la primera vez que el cron se ejecuta. Si el pipeline se lanzó manualmente con `docker compose up`, los logs de esa ejecución no van a ese fichero.

## Actualizar el código

Cuando haya cambios en el repositorio:

```bash
cd /opt/auto-reddit
sudo git pull
sudo docker compose up --build  # reconstruye la imagen con los cambios
```

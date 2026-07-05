# Desplegar el backend (Render + Supabase)

El backend es un servicio FastAPI (`backend/app/main.py`) que corre el scheduler
de polling de IMAP y digests dentro del mismo proceso (no hay worker separado
para el MVP), por lo que necesita un proceso **siempre activo** — no un tier
serverless o "sleep on idle". Se recomienda:

- **Render Starter (~$7/mes)** para el web service: el tier free de Render
  duerme el proceso tras ~15 min sin tráfico HTTP, lo que cortaría el
  scheduler entre polls, así que no sirve para este diseño. Railway es una
  alternativa igual de válida.
- **Supabase Postgres (free, 500MB)** para la base de datos, en vez del
  Postgres gestionado de Render.

## 1. Base de datos (Supabase)

1. Crear un proyecto en [supabase.com](https://supabase.com) (tier free
   alcanza para el MVP).
2. En **Project Settings → Database → Connection string → URI**, copiar la
   cadena de **conexión directa** (puerto `5432`), **no** la del pooler
   PgBouncer en modo transacción (puerto `6543`). Este backend es un único
   proceso siempre activo con su propio pool de conexiones (SQLAlchemy), así
   que no necesita PgBouncer, y el modo transacción de PgBouncer rompe
   funcionalidades que algunos drivers asumen (prepared statements del lado
   del servidor).
3. Armar el `DATABASE_URL` reemplazando el esquema `postgresql://` por
   `postgresql+psycopg://` y agregando `?sslmode=require` al final (Supabase
   exige SSL en conexiones externas). Ver el formato exacto en
   `backend/.env.example`.

## 2. Servicio web (Render)

1. Crear un **Web Service** en Render apuntando a la carpeta `backend/`, plan
   **Starter** (no Free) para que el proceso no duerma.
2. Build command: `pip install -r requirements.txt`
3. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   (equivalente al `Procfile` incluido).
4. Variables de entorno a configurar (ver `backend/.env.example`):

   | Variable | Descripción |
   |---|---|
   | `DATABASE_URL` | Connection string directa de Supabase (`postgresql+psycopg://...?sslmode=require`) |
   | `ANTHROPIC_API_KEY` | API key de Anthropic |
   | `CLAUDE_MODEL` | Modelo Claude a usar (ej. `claude-sonnet-5`) |
   | `ENCRYPTION_KEY` | Generar con `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
   | `JWT_SECRET` | Generar con `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
   | `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASSWORD` / `SMTP_FROM_ADDRESS` | Credenciales SMTP (funciona con Resend, SendGrid, SES o cualquier SMTP real) |
   | `FRONTEND_ORIGIN` | URL exacta del frontend en Netlify (sin wildcard, ej. `https://tu-sitio.netlify.app`) |
   | `POLL_INTERVAL_MINUTES` | Intervalo de polling IMAP (default 3) |
   | `MAGIC_LINK_TTL_MINUTES` / `SESSION_TTL_DAYS` | Vigencia del enlace mágico y de la sesión |
   | `COOKIE_SECURE` | `true` en producción (obligatorio para que `SameSite=None` funcione) |

5. Migraciones: correr `alembic upgrade head` contra el `DATABASE_URL` de
   Supabase la primera vez (vía el Shell de Render o localmente apuntando a
   Supabase), y de nuevo en cada deploy que incluya una migración nueva.
6. Health check: configurar el path `/healthz` en Render.

## 3. Cookie cross-site (Netlify ↔ Render)

Como el frontend y el backend viven en dominios distintos, la cookie de sesión
se emite con `SameSite=None; Secure` (activado automáticamente cuando
`COOKIE_SECURE=true`). Esto requiere que ambos extremos sirvan HTTPS — Render
y Netlify lo hacen por defecto. Verificar en las devtools del navegador que la
cookie `session` efectivamente se guarda después de `/api/auth/verify`.

## Notas sobre límites del free tier de Supabase

- 500MB de almacenamiento y el proyecto se pausa automáticamente tras 7 días
  sin actividad en el tier free (un ping periódico del backend, que ya ocurre
  naturalmente por el polling cada pocos minutos, evita la pausa mientras el
  monitoreo esté activo).
- Si el volumen de `email_analyses` crece mucho, aplicar la política de
  retención de `docs/DATA_RETENTION_POLICY.md` para no acercarse al límite de
  espacio.

# Client's Mood

Sistema multiusuario que monitorea la casilla de correo de cada usuario,
analiza el estado de ánimo de los emails entrantes con Claude, y envía un
informe (inmediato o resumen diario/semanal) a la dirección que el usuario
elija.

## Estructura

- [`backend/`](backend/) — API FastAPI + workers (polling IMAP, análisis LLM,
  envío de informes). Ver [`backend/.env.example`](backend/.env.example) para
  las variables necesarias.
- [`frontend/`](frontend/) — SPA React + Vite (login por magic link,
  configuración de monitoreo, historial de análisis).
- [`docs/`](docs/) — guías de despliegue y política de retención de datos.

## Desarrollo local

**Backend** (requiere Postgres — en producción usamos Supabase, ver
[`docs/DEPLOY_BACKEND.md`](docs/DEPLOY_BACKEND.md); para pruebas rápidas
locales también funciona con SQLite creando el schema directo desde los
modelos en vez de correr Alembic):

```
cd backend
python -m venv .venv
.venv/Scripts/pip install -r requirements-dev.txt
cp .env.example .env  # completar valores, DATABASE_URL de Supabase o local
alembic upgrade head  # contra Postgres (Supabase o local)
uvicorn app.main:app --reload
```

Los tests (`pytest`) usan SQLite en memoria y no requieren Postgres ni
credenciales reales.

**Frontend**:

```
cd frontend
npm install
cp .env.example .env  # VITE_API_BASE_URL apuntando al backend local
npm run dev
```

## Despliegue

Ver [`docs/DEPLOY_BACKEND.md`](docs/DEPLOY_BACKEND.md) (Render) y
[`docs/DEPLOY_FRONTEND.md`](docs/DEPLOY_FRONTEND.md) (Netlify).

## Seguridad

- Las contraseñas de aplicación IMAP se cifran en reposo (Fernet) y nunca se
  devuelven por la API.
- Autenticación por magic link (sin contraseñas de usuario que gestionar).
- Cada consulta está aislada por `user_id`; ver
  [`docs/DATA_RETENTION_POLICY.md`](docs/DATA_RETENTION_POLICY.md) para la
  política de retención del contenido de los correos analizados.

# Desplegar el frontend (Netlify)

El frontend es una SPA de React + Vite (`frontend/`).

## Pasos

1. Crear un nuevo sitio en Netlify apuntando al repositorio, con **base
   directory** `frontend/`.
2. Build command: `npm run build`
3. Publish directory: `dist`
4. Variable de entorno en Netlify (Site settings → Environment variables):

   | Variable | Valor |
   |---|---|
   | `VITE_API_BASE_URL` | URL pública del backend en Render (ej. `https://tu-backend.onrender.com`) |

5. El archivo `netlify.toml` ya incluye la regla de redirección SPA
   (`/* -> /index.html 200`) necesaria para que las rutas del cliente
   (`/login`, `/verify`, `/config`, `/dashboard`) funcionen al refrescar.

## Cookies cross-site

Como el frontend (Netlify) y el backend (Render) están en dominios distintos,
todas las llamadas del cliente usan `credentials: 'include'`
(`frontend/src/api/client.ts`) y el backend responde con
`Access-Control-Allow-Origin` igual a `FRONTEND_ORIGIN` (nunca `*`) y
`Access-Control-Allow-Credentials: true`. Si después del login la cookie
`session` no aparece en las devtools del navegador, lo primero a revisar es
que `FRONTEND_ORIGIN` en el backend coincida *exactamente* con la URL de
Netlify (incluyendo `https://`) y que `COOKIE_SECURE=true` esté seteado en el
backend — sin eso, `SameSite=None` es rechazado por el navegador.

# PROMPT — Sistema de Análisis de Estado de Ánimo en Emails (F + B)

## Rol

Actuá como desarrollador full-stack senior. Vas a construir un sistema multiusuario compuesto por un **Frontend (F)** y un **Backend (B)** que analiza el estado de ánimo/sentimiento de los emails recibidos en la casilla de cada usuario, y envía un informe por correo con los resultados.

---

## 1. Objetivo del sistema

Cada usuario registra en **F**:
1. La dirección de correo cuya bandeja de entrada se va a monitorear y analizar.
2. La dirección de correo donde quiere recibir el informe de análisis.

**B** monitorea esa casilla, y por cada email nuevo que llega:
1. Extrae el contenido (asunto + cuerpo, y remitente).
2. Lo envía a un LLM con un prompt de clasificación de estado de ánimo/sentimiento.
3. Genera un informe (por email individual y/o consolidado periódico — ver sección 5).
4. Envía ese informe por correo a la dirección indicada por el usuario.

El sistema es **multiusuario**: cada usuario tiene su propia casilla monitoreada, su propio destino de informes, y sus resultados están aislados de los del resto.

---

## 2. Arquitectura general

```
[Usuario] → [F: Web en Netlify] → API REST → [B: Python] → LLM (análisis)
                                                    ↓
                                          [Casilla monitoreada]
                                                    ↓
                                          Email de informe → [destino elegido]
```

- **F**: SPA estática (React o HTML/JS vanilla), deployada en Netlify. No procesa nada sensible del lado del cliente; sólo es una interfaz para dar de alta/gestionar la configuración del usuario, y consumir la API de B.
- **B**: API + workers en Python. Corre en un servidor propio o cloud (no en Netlify, que es sólo estático). Hace todo el trabajo pesado: guarda configuración, lee casillas, llama al LLM, envía informes.

---

## 3. Especificación de F (Frontend)

**Stack sugerido**: React + Vite (o HTML/JS plano si se prefiere simplicidad), deploy en Netlify. Todas las llamadas a datos van contra la API de B (nunca contra el proveedor de email directamente).

### 3.1 Pantallas

**a) Alta / registro de usuario**
- Email del usuario (identifica su cuenta en el sistema)
- Contraseña o método de login (ver 3.3 sobre auth)

**b) Configuración de monitoreo** (una vez logueado)
- Campo: *"Email a analizar"* (la casilla que B va a monitorear)
- Campo: *"Contraseña de aplicación"* de esa casilla (nunca la contraseña real de la cuenta — ver nota de seguridad en sección 6)
- Campo: *"Servidor IMAP"* (autocompletar si detecta gmail.com/outlook.com/etc., manual para dominios propios)
- Campo: *"Email de destino del informe"*
- Selector: *"Frecuencia del informe"* → Inmediato (por cada email) / Resumen diario / Resumen semanal
- Botón "Guardar configuración" → `POST /api/config`
- Botón "Activar/Pausar monitoreo" → `PATCH /api/config/status`

**c) Historial / Dashboard** (opcional pero recomendado)
- Lista de últimos análisis: fecha, remitente, estado de ánimo detectado, link al informe enviado
- Gráfico simple de evolución del estado de ánimo en el tiempo (ej. con Recharts)

### 3.2 Validaciones en F
- Formato de email válido en ambos campos.
- Alertar si "email a analizar" y "email de destino" son iguales (no es un error, pero conviene avisar).
- Nunca loguear ni mostrar la contraseña de aplicación en claro tras guardarla (mostrar como `********`).

### 3.3 Autenticación de usuarios
Como el sistema es multiusuario, F necesita distinguir usuarios. Opciones (elegir una, la más simple para arrancar es la primera):
- **Magic link por email**: el usuario pone su email, B le manda un link de acceso de un solo uso. Sin contraseñas que gestionar.
- **Email + contraseña** tradicional con JWT.
- **OAuth con Google** (si más adelante se integra Gmail API en vez de IMAP).

---

## 4. Especificación de B (Backend)

**Stack sugerido**: Python + FastAPI (API REST) + APScheduler o Celery+Redis (para los workers periódicos) + PostgreSQL o SQLite (para arrancar).

> Nota: cuando subas el archivo .json que mencionaste, esta sección se ajusta para partir de esa base en vez de construir desde cero.

### 4.1 Modelo de datos (tablas mínimas)

```
users
  id, email, password_hash / auth_token, created_at

monitor_configs
  id, user_id (FK), email_to_monitor, imap_server, imap_password_encrypted,
  report_destination_email, frequency ('immediate'|'daily'|'weekly'),
  status ('active'|'paused'), last_checked_at

email_analysis
  id, config_id (FK), message_id, sender, subject, received_at,
  mood_label, mood_score, mood_summary, analyzed_at, report_sent (bool)
```

### 4.2 Módulo de ingesta de emails

- Conexión vía **IMAP** (librería `imaplib` o `imapclient`) a la casilla configurada por cada usuario.
- Polling periódico (ej. cada 2-5 min) por cada `monitor_config` activo, buscando emails no vistos desde `last_checked_at`.
- Alternativa más eficiente a futuro: IMAP IDLE (push) o Gmail API con Pub/Sub push notifications, si el usuario usa Gmail y se migra de contraseña de aplicación a OAuth.
- Extraer: remitente, asunto, cuerpo (texto plano, o texto extraído de HTML si es necesario), fecha.

### 4.3 Módulo de análisis con LLM

Prompt sugerido para el LLM (ejemplo con Claude API):

```
Sos un analista de sentimiento. Vas a recibir el contenido de un email
(remitente, asunto y cuerpo). Tu tarea es evaluar el estado de ánimo
del remitente y devolver ÚNICAMENTE un JSON con este formato:

{
  "mood_label": "positivo" | "neutral" | "negativo" | "urgente/enojado",
  "mood_score": <número de -1.0 (muy negativo) a 1.0 (muy positivo)>,
  "summary": "<resumen de 1-2 líneas del motivo del email y el tono detectado>",
  "requires_attention": <true|false>
}

Email a analizar:
Remitente: {sender}
Asunto: {subject}
Cuerpo: {body}
```

- Llamar a la API del LLM (Claude por defecto) con este prompt por cada email nuevo.
- Parsear la respuesta JSON y guardarla en `email_analysis`.
- Manejar rate limits y reintentos si la API del LLM falla.

### 4.4 Módulo de generación y envío de informes

Según la `frequency` configurada:
- **Inmediato**: apenas se analiza un email, se arma y envía el informe de ese único email.
- **Diario/Semanal**: un worker corre a horario fijo (ej. 8am), junta todos los `email_analysis` no reportados del período, arma un resumen (cantidad por categoría, casos que requieren atención destacados) y lo envía.

Envío por SMTP o servicio transaccional (ej. Resend, SendGrid, Amazon SES) hacia `report_destination_email`. Formato del informe: HTML simple con tabla de resultados.

### 4.5 Scheduler / Workers

- Worker de polling de casillas (cada N minutos, por config activa).
- Worker de armado de informes periódicos (diario/semanal, según cron).
- Usar APScheduler para simplicidad inicial, o Celery + Redis si se espera escalar a muchos usuarios.

### 4.6 Endpoints de la API (para que F consuma)

```
POST   /api/auth/register
POST   /api/auth/login
POST   /api/config              # crear config de monitoreo
PATCH  /api/config/{id}         # editar / pausar / activar
GET    /api/config/{id}
GET    /api/analysis?config_id= # historial de análisis
```

---

## 5. Flujo end-to-end (resumen)

1. Usuario entra a F, se registra/loguea.
2. Usuario carga: email a analizar + credencial de app + email de destino + frecuencia.
3. F llama a `POST /api/config` en B.
4. B guarda la config (credencial encriptada) y arranca a monitorear esa casilla.
5. Llega un email nuevo → B lo detecta → lo manda al LLM → guarda el resultado.
6. Según la frecuencia configurada, B arma el informe y lo envía por email al destino indicado.
7. (Opcional) F muestra el historial de análisis en el dashboard.

---

## 6. Seguridad y privacidad — puntos que no se pueden saltear

- **Nunca** guardar contraseñas de casillas en texto plano. Usar cifrado simétrico (ej. Fernet de `cryptography`) con una clave maestra fuera del repo (variable de entorno / secret manager).
- Recomendar a los usuarios usar **contraseñas de aplicación**, no su contraseña real de la cuenta.
- El contenido de emails de terceros se envía a un LLM externo (Claude/OpenAI/Abacus): dejarlo explícito en los términos de uso que le muestres a cada usuario, ya que puede incluir datos personales de quien les escribió.
- Aislar datos por usuario en todas las queries (nunca traer `email_analysis` de otro `user_id`).
- Definir política de retención: ¿por cuánto tiempo se guarda el contenido de los emails analizados una vez generado el informe?
- Rate limiting en la API para evitar abuso.

---

## 7. Decisiones abiertas (a confirmar antes de programar)

| Punto | Asunción tomada acá | Alternativa |
|---|---|---|
| LLM a usar | Claude API (Anthropic) | Abacus ChatLLM (tu stack actual) / OpenAI |
| Acceso a la casilla | IMAP genérico + contraseña de app | Gmail API con OAuth por usuario |
| Frecuencia de informe | Configurable por usuario (inmediato/diario/semanal) | Fija en un solo modo |
| Hosting de B | A definir (VPS propio, Railway, Render, Fly.io) | — |
| Base de datos | PostgreSQL o SQLite para MVP | — |

---

## 8. Entregables esperados

1. Repositorio de **F**: proyecto React/Vite listo para `netlify deploy`, con las pantallas de la sección 3.
2. Repositorio de **B**: proyecto FastAPI con estructura modular (`/api`, `/workers`, `/models`, `/services/llm.py`, `/services/email_reader.py`, `/services/email_sender.py`), migraciones de base de datos, y `.env.example` con las variables necesarias (API key del LLM, clave de cifrado, credenciales SMTP).
3. Documentación mínima de deploy para ambos.

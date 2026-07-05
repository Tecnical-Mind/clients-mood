# Política de retención de datos

El contenido de correos de terceros (remitente, asunto y un extracto del
cuerpo) pasa por la API de Claude para el análisis de ánimo y se guarda en la
tabla `email_analyses` junto con el resultado del análisis.

- **Qué se guarda**: remitente, asunto, un resumen de 1-2 líneas generado por
  el LLM, la etiqueta y puntaje de ánimo, y metadatos (fecha, UID de IMAP).
  El cuerpo completo del correo **no** se persiste — solo se usa en memoria
  para la llamada al LLM y se descarta después del análisis.
- **Retención recomendada**: conservar `email_analyses` por un máximo de 90
  días desde `analyzed_at`, tiempo suficiente para el dashboard y los digests
  semanales. Implementar como un job periódico (`DELETE FROM email_analyses
  WHERE analyzed_at < now() - interval '90 days'`) o ajustar según los
  requisitos legales del usuario.
- **Credenciales de la casilla**: la contraseña de aplicación IMAP se guarda
  cifrada (Fernet) y nunca se expone en la API ni en logs. Si un usuario
  pausa o elimina su configuración, la contraseña cifrada debe eliminarse
  junto con el resto de `monitor_configs`.
- **Terceros involucrados**: el contenido de los correos (que puede incluir
  datos personales de quien los escribió, no solo del usuario dueño de la
  cuenta) se envía a la API de Anthropic (Claude) para su análisis. Esto debe
  quedar explícito en los términos de uso mostrados a cada usuario antes de
  activar el monitoreo.

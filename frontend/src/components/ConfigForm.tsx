import React, { useEffect, useState } from "react";

import type { ConfigInput, Frequency, MonitorConfig } from "../api/types";
import { FrequencySelector } from "./FrequencySelector";
import { ImapServerField, suggestImapServer } from "./ImapServerField";

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

interface Props {
  existing: MonitorConfig | null;
  onSave: (input: ConfigInput) => Promise<void>;
}

export function ConfigForm({ existing, onSave }: Props) {
  const [emailToMonitor, setEmailToMonitor] = useState(existing?.email_to_monitor ?? "");
  const [imapServer, setImapServer] = useState(existing?.imap_server ?? "");
  const [imapPort, setImapPort] = useState(existing?.imap_port ?? 993);
  const [imapPassword, setImapPassword] = useState("");
  const [destinationEmail, setDestinationEmail] = useState(
    existing?.report_destination_email ?? ""
  );
  const [frequency, setFrequency] = useState<Frequency>(existing?.frequency ?? "immediate");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Auto-suggest the IMAP server/port from the monitored email's domain,
  // but never overwrite a value the user already typed in manually.
  useEffect(() => {
    if (imapServer) return;
    const suggestion = suggestImapServer(emailToMonitor);
    if (suggestion) {
      setImapServer(suggestion.server);
      setImapPort(suggestion.port);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [emailToMonitor]);

  const emailToMonitorValid = EMAIL_RE.test(emailToMonitor);
  const destinationEmailValid = EMAIL_RE.test(destinationEmail);
  const sameEmailWarning =
    emailToMonitorValid &&
    destinationEmailValid &&
    emailToMonitor.toLowerCase() === destinationEmail.toLowerCase();

  const canSubmit =
    emailToMonitorValid &&
    destinationEmailValid &&
    imapServer.trim().length > 0 &&
    (existing || imapPassword.length > 0) &&
    !saving;

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSaving(true);
    setSaved(false);
    try {
      await onSave({
        email_to_monitor: emailToMonitor,
        imap_server: imapServer,
        imap_port: imapPort,
        imap_password: imapPassword,
        report_destination_email: destinationEmail,
        frequency,
      });
      // Never keep the password in the form state after a successful save -
      // the backend never returns it, so there's nothing to redisplay.
      setImapPassword("");
      setSaved(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo guardar la configuración.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <form onSubmit={onSubmit}>
      <label htmlFor="email_to_monitor">Email a analizar</label>
      <input
        id="email_to_monitor"
        type="email"
        value={emailToMonitor}
        onChange={(e) => setEmailToMonitor(e.target.value)}
        className={emailToMonitor.length > 0 && !emailToMonitorValid ? "invalid" : ""}
        placeholder="soporte@tuempresa.com"
        required
      />
      {emailToMonitor.length > 0 && !emailToMonitorValid && (
        <div className="field-error">Ingresá un email válido.</div>
      )}

      <ImapServerField
        server={imapServer}
        port={imapPort}
        onChange={(server, port) => {
          setImapServer(server);
          setImapPort(port);
        }}
      />

      <label htmlFor="imap_password">
        Contraseña de aplicación {existing && "(dejar en blanco para no cambiarla)"}
      </label>
      <input
        id="imap_password"
        type="password"
        value={imapPassword}
        onChange={(e) => setImapPassword(e.target.value)}
        placeholder={existing ? "********" : "Contraseña de aplicación"}
        required={!existing}
      />

      <label htmlFor="destination_email">Email de destino del informe</label>
      <input
        id="destination_email"
        type="email"
        value={destinationEmail}
        onChange={(e) => setDestinationEmail(e.target.value)}
        className={destinationEmail.length > 0 && !destinationEmailValid ? "invalid" : ""}
        placeholder="vos@ejemplo.com"
        required
      />
      {destinationEmail.length > 0 && !destinationEmailValid && (
        <div className="field-error">Ingresá un email válido.</div>
      )}

      {sameEmailWarning && (
        <div className="warning-banner">
          Estás enviando los informes a la misma casilla que estás monitoreando: los propios
          informes van a aparecer como correos nuevos y se van a analizar también.
        </div>
      )}

      <FrequencySelector value={frequency} onChange={setFrequency} />

      {error && <div className="field-error">{error}</div>}
      {saved && <div className="warning-banner">Configuración guardada.</div>}

      <button type="submit" disabled={!canSubmit}>
        {saving ? "Guardando..." : "Guardar configuración"}
      </button>
    </form>
  );
}

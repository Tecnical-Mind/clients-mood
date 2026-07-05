import React, { useState } from "react";

import { api } from "../api/client";

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const isValid = EMAIL_RE.test(email);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isValid) return;
    setSubmitting(true);
    setError(null);
    try {
      await api.post("/api/auth/request-link", { email });
      setSent(true);
    } catch {
      // Never reveal whether the account existed; always show the same
      // generic confirmation state even on unexpected errors.
      setSent(true);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="page">
      <div className="card">
        <h1>Client's Mood</h1>
        {sent ? (
          <p>
            Si <strong>{email}</strong> tiene una cuenta, te enviamos un enlace de acceso.
            Revisá tu correo.
          </p>
        ) : (
          <form onSubmit={onSubmit}>
            <label htmlFor="email">Tu email</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className={email.length > 0 && !isValid ? "invalid" : ""}
              placeholder="vos@ejemplo.com"
              required
            />
            {email.length > 0 && !isValid && (
              <div className="field-error">Ingresá un email válido.</div>
            )}
            {error && <div className="field-error">{error}</div>}
            <button type="submit" disabled={!isValid || submitting}>
              {submitting ? "Enviando..." : "Enviarme un enlace de acceso"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}

import { Link } from "react-router-dom";

import { ConfigForm } from "../components/ConfigForm";
import { StatusToggle } from "../components/StatusToggle";
import { useAuth } from "../auth/AuthContext";
import { useConfig } from "../hooks/useConfig";

export default function ConfigPage() {
  const { user, logout } = useAuth();
  const { config, loading, save, setStatus } = useConfig();

  return (
    <div className="page">
      <div className="top-nav">
        <div>
          <Link to="/config">Configuración</Link>
          <Link to="/dashboard">Historial</Link>
        </div>
        <div>
          <span style={{ fontSize: 13, color: "var(--color-muted)", marginRight: 12 }}>
            {user?.email}
          </span>
          <button type="button" className="secondary" onClick={() => logout()}>
            Salir
          </button>
        </div>
      </div>

      <div className="card">
        <h1>Monitoreo de correo</h1>
        {loading ? (
          <p>Cargando...</p>
        ) : (
          <>
            <ConfigForm
              existing={config}
              onSave={async (input) => {
                await save(input);
              }}
            />
            {config && (
              <div style={{ marginTop: 20 }}>
                <StatusToggle status={config.status} onToggle={() => setStatus(
                  config.status === "active" ? "paused" : "active"
                )} />
                {config.last_error && (
                  <div className="field-error">Último error: {config.last_error}</div>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

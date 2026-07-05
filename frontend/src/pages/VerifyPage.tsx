import { useEffect } from "react";
import { useSearchParams } from "react-router-dom";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export default function VerifyPage() {
  const [params] = useSearchParams();
  const token = params.get("token");

  useEffect(() => {
    if (!token) return;
    // Full browser navigation (not fetch) so the backend's redirect + the
    // httpOnly session cookie it sets are handled natively by the browser.
    window.location.replace(`${API_BASE_URL}/api/auth/verify?token=${encodeURIComponent(token)}`);
  }, [token]);

  return (
    <div className="page">
      <div className="card">
        {token ? <p>Verificando tu acceso...</p> : <p>Enlace inválido.</p>}
      </div>
    </div>
  );
}

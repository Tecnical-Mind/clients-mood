import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { api } from "../api/client";
import type { Analysis } from "../api/types";
import { AnalysisTable } from "../components/AnalysisTable";
import { MoodChart } from "../components/MoodChart";

export default function DashboardPage() {
  const [analyses, setAnalyses] = useState<Analysis[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get<Analysis[]>("/api/analysis")
      .then(setAnalyses)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="page">
      <div className="top-nav">
        <div>
          <Link to="/config">Configuración</Link>
          <Link to="/dashboard">Historial</Link>
        </div>
      </div>
      <div className="card">
        <h1>Historial de análisis</h1>
        {loading ? (
          <p>Cargando...</p>
        ) : (
          <>
            <MoodChart analyses={analyses} />
            <AnalysisTable analyses={analyses} />
          </>
        )}
      </div>
    </div>
  );
}

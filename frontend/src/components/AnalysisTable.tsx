
import type { Analysis } from "../api/types";

export function AnalysisTable({ analyses }: { analyses: Analysis[] }) {
  if (analyses.length === 0) {
    return <p>Todavía no se analizó ningún correo.</p>;
  }

  return (
    <table>
      <thead>
        <tr>
          <th>Fecha</th>
          <th>Remitente</th>
          <th>Asunto</th>
          <th>Ánimo</th>
          <th>Resumen</th>
        </tr>
      </thead>
      <tbody>
        {analyses.map((a) => (
          <tr key={a.id}>
            <td>{new Date(a.analyzed_at).toLocaleString()}</td>
            <td>{a.sender}</td>
            <td>{a.subject}</td>
            <td>
              <span className={`badge ${a.mood_label}`}>{a.mood_label}</span>
              {a.requires_attention && (
                <span className="badge negativo" style={{ marginLeft: 4 }}>
                  atención
                </span>
              )}
            </td>
            <td>{a.mood_summary}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

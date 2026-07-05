import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { Analysis } from "../api/types";

export function MoodChart({ analyses }: { analyses: Analysis[] }) {
  const data = [...analyses]
    .sort((a, b) => new Date(a.analyzed_at).getTime() - new Date(b.analyzed_at).getTime())
    .map((a) => ({
      date: new Date(a.analyzed_at).toLocaleDateString(),
      mood_score: a.mood_score,
    }));

  if (data.length === 0) return null;

  return (
    <div style={{ width: "100%", height: 220, marginTop: 20 }}>
      <ResponsiveContainer>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" fontSize={11} />
          <YAxis domain={[-1, 1]} fontSize={11} />
          <Tooltip />
          <Line type="monotone" dataKey="mood_score" stroke="#4f46e5" dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

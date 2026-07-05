
import type { Frequency } from "../api/types";

interface Props {
  value: Frequency;
  onChange: (value: Frequency) => void;
}

export function FrequencySelector({ value, onChange }: Props) {
  return (
    <>
      <label htmlFor="frequency">Frecuencia del informe</label>
      <select
        id="frequency"
        value={value}
        onChange={(e) => onChange(e.target.value as Frequency)}
      >
        <option value="immediate">Inmediato (por cada correo)</option>
        <option value="daily">Resumen diario</option>
        <option value="weekly">Resumen semanal</option>
      </select>
    </>
  );
}

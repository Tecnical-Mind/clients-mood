import React from "react";

import type { ConfigStatus } from "../api/types";

interface Props {
  status: ConfigStatus;
  onToggle: () => Promise<void>;
}

export function StatusToggle({ status, onToggle }: Props) {
  const [busy, setBusy] = React.useState(false);

  const handleClick = async () => {
    setBusy(true);
    try {
      await onToggle();
    } finally {
      setBusy(false);
    }
  };

  return (
    <button type="button" className="secondary" onClick={handleClick} disabled={busy}>
      {status === "active" ? "Pausar monitoreo" : "Activar monitoreo"}
    </button>
  );
}

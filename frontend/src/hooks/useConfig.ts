import { useCallback, useEffect, useState } from "react";

import { ApiError, api } from "../api/client";
import type { ConfigInput, MonitorConfig } from "../api/types";

export function useConfig() {
  const [config, setConfig] = useState<MonitorConfig | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.get<MonitorConfig>("/api/config/me");
      setConfig(data);
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) {
        setConfig(null);
      } else {
        throw err;
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const save = useCallback(
    async (input: ConfigInput) => {
      const updated = config
        ? await api.patch<MonitorConfig>(`/api/config/${config.id}`, input)
        : await api.post<MonitorConfig>("/api/config", input);
      setConfig(updated);
      return updated;
    },
    [config]
  );

  const setStatus = useCallback(
    async (status: "active" | "paused") => {
      if (!config) return;
      const updated = await api.patch<MonitorConfig>(`/api/config/${config.id}`, { status });
      setConfig(updated);
    },
    [config]
  );

  return { config, loading, save, setStatus, reload: load };
}

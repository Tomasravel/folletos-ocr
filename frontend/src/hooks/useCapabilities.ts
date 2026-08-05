import { useEffect, useState } from "react";
import { getCapabilities } from "../api/client";
import type { Capabilities } from "../types";

export function useCapabilities() {
  const [caps, setCaps] = useState<Capabilities | null>(null);
  useEffect(() => { getCapabilities().then(setCaps).catch(() => setCaps(null)); }, []);
  return caps;
}

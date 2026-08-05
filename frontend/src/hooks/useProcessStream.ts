import { useState } from "react";
import { processImages } from "../api/client";
import type { Fields, StageEvent } from "../types";

export type RowStatus = "queued" | "preview" | "done" | "error";

export interface Row {
  image_id: string;
  name: string;
  file: File;
  level: string;
  fields: Fields;
  status: RowStatus;
  events: StageEvent[];
  error?: string;
}

const EMPTY: Fields = {
  adreca: null, cp: null, zt: null, fecha: null, x_lon: null, y_lat: null,
};

export function useProcessStream() {
  const [rows, setRows] = useState<Row[]>([]);
  const [running, setRunning] = useState(false);

  async function run(files: File[], level: string, debug: boolean, workers: number) {
    setRunning(true);
    setRows(files.map((f, i) => ({
      image_id: `img_${i}`, name: f.name, file: f, level,
      fields: { ...EMPTY }, status: "queued" as RowStatus, events: [],
    })));
    const expectFinal = level !== "rapida";
    const idxOf = (id: string) => Number(id.replace("img_", ""));

    await processImages(
      files, level, debug, workers,
      (ev) => setRows((prev) => {
        const i = idxOf(ev.image_id);
        if (!prev[i]) return prev;
        const status: RowStatus = ev.stage === "final" || !expectFinal ? "done" : "preview";
        const next = [...prev];
        next[i] = { ...next[i], fields: ev.fields, status, events: [...next[i].events, ev] };
        return next;
      }),
      (err) => setRows((prev) => {
        const i = idxOf(err.image_id ?? "");
        if (!prev[i]) return prev;
        const next = [...prev];
        next[i] = { ...next[i], status: "error", error: err.error };
        return next;
      }),
    );

    setRows((prev) => prev.map((r) =>
      r.status === "queued" || r.status === "preview" ? { ...r, status: "done" } : r));
    setRunning(false);
  }

  return { rows, running, run };
}

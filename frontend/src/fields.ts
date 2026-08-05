import type { Row } from "./hooks/useProcessStream";

export const COLS = ["adreca", "cp", "zt", "fecha", "x_lon", "y_lat"] as const;
export type Edits = Record<string, Record<string, string>>;

/** Valor mostrado de un campo: la edición del usuario si existe, si no lo extraído. */
export function fieldValue(row: Row, edits: Edits, c: string): string {
  const edited = edits[row.image_id]?.[c];
  const raw = (row.fields as unknown as Record<string, unknown>)[c];
  return edited !== undefined ? edited : raw == null ? "" : String(raw);
}

/** Los 6 campos tabulados, para pegar en Excel/Sheets. */
export function rowTsv(row: Row, edits: Edits): string {
  return COLS.map((c) => fieldValue(row, edits, c)).join("\t");
}

export interface EditRecord {
  image: string;
  level: string;
  run_id?: string;
  changes: Record<string, { from: string; to: string }>;
}

/** Diff de cada imagen: campos cuyo valor editado difiere de lo extraído. */
export function buildEditRecords(rows: Row[], edits: Edits): EditRecord[] {
  const recs: EditRecord[] = [];
  for (const r of rows) {
    const e = edits[r.image_id];
    if (!e) continue;
    const changes: EditRecord["changes"] = {};
    for (const c of COLS) {
      if (e[c] === undefined) continue;
      const raw = (r.fields as unknown as Record<string, unknown>)[c];
      const orig = raw == null ? "" : String(raw);
      if (e[c] !== orig) changes[c] = { from: orig, to: e[c] };
    }
    if (Object.keys(changes).length) {
      recs.push({
        image: r.name,
        level: r.level,
        run_id: r.events[r.events.length - 1]?.run_id,
        changes,
      });
    }
  }
  return recs;
}

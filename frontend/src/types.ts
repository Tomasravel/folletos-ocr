export interface Fields {
  adreca: string | null; cp: string | null; zt: string | null;
  fecha: string | null; x_lon: number | null; y_lat: number | null;
}
export interface StageEvent {
  image_id: string; run_id: string; stage: "fast" | "final"; level: string;
  engine: string | null; parser: string | null; fields: Fields;
  timings_ms: Record<string, number>; warnings: string[];
  boxes: { box: number[]; text: string; conf: number }[];
}
export interface Capabilities {
  engines: string[]; parsers: string[]; levels: string[];
  llm_model: string | null; geocoding: boolean; auth_required: boolean;
}

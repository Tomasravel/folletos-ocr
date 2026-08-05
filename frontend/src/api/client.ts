import type { Capabilities, StageEvent } from "../types";

const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const token = import.meta.env.VITE_API_TOKEN ?? "";
const authHeaders: Record<string, string> = token ? { Authorization: `Bearer ${token}` } : {};

export async function getCapabilities(): Promise<Capabilities> {
  const r = await fetch(`${API}/capabilities`, { headers: authHeaders });
  return r.json();
}

export async function saveEdits(records: unknown[]): Promise<void> {
  if (!records.length) return;
  try {
    await fetch(`${API}/edits`, {
      method: "POST",
      headers: { ...authHeaders, "Content-Type": "application/json" },
      body: JSON.stringify({ records }),
    });
  } catch {
    /* best-effort: no bloquea el export */
  }
}

export async function processImages(
  files: File[], level: string, debug: boolean, workers: number,
  onEvent: (ev: StageEvent) => void,
  onError: (err: { image_id?: string; error: string }) => void,
): Promise<void> {
  const form = new FormData();
  files.forEach((f) => form.append("images", f));
  const r = await fetch(`${API}/process?level=${level}&stream=true&debug=${debug}&workers=${workers}`,
    { method: "POST", body: form, headers: authHeaders });
  const reader = r.body!.getReader();
  const decoder = new TextDecoder();
  let buf = "";
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    const chunks = buf.split("\n\n");
    buf = chunks.pop() ?? "";
    for (const chunk of chunks) {
      if (chunk.startsWith("event: error")) {
        const data = chunk.split("data: ")[1];
        onError(data ? JSON.parse(data) : { error: "error" });
      } else if (chunk.startsWith("data: ")) {
        const data = chunk.slice(6).trim();
        if (data && data !== "{}") onEvent(JSON.parse(data));
      }
    }
  }
}

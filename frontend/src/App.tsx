import { useEffect, useMemo, useState } from "react";
import {
  Badge, Button, Container, Group, NumberInput, Paper, Progress, SegmentedControl,
  Stack, Switch, Text, ThemeIcon, Title, Tooltip,
} from "@mantine/core";
import { IconDownload, IconEye, IconFileDownload, IconMapPin, IconPlayerPlay } from "@tabler/icons-react";
import { useCapabilities } from "./hooks/useCapabilities";
import { useProcessStream } from "./hooks/useProcessStream";
import { Dropzone } from "./components/Dropzone";
import { ResultsTable } from "./components/ResultsTable";
import { ReviewModal } from "./components/ReviewModal";
import { ColorSchemeToggle } from "./components/ColorSchemeToggle";
import { COLS, buildEditRecords, fieldValue } from "./fields";
import { saveEdits } from "./api/client";

const ALL_LEVELS = ["rapida", "media", "avanzada"];

export default function App() {
  const caps = useCapabilities();
  const { rows, running, run } = useProcessStream();
  const [files, setFiles] = useState<File[]>([]);
  const [level, setLevel] = useState("rapida");
  const [debug, setDebug] = useState(false);
  const [workers, setWorkers] = useState(1);
  const [edits, setEdits] = useState<Record<string, Record<string, string>>>({});
  const [reviewOpen, setReviewOpen] = useState(false);
  const [reviewIndex, setReviewIndex] = useState(0);

  const levels = caps?.levels ?? ["rapida"];
  useEffect(() => {
    if (caps && !levels.includes(level)) setLevel(levels[0]);
  }, [caps]); // eslint-disable-line react-hooks/exhaustive-deps

  const done = rows.filter((r) => r.status === "done" || r.status === "error").length;
  const progress = rows.length ? (done / rows.length) * 100 : 0;

  const editRecords = useMemo(() => buildEditRecords(rows, edits), [rows, edits]);
  const perField = useMemo(() => {
    const m: Record<string, number> = {};
    for (const rec of editRecords) for (const c of Object.keys(rec.changes)) m[c] = (m[c] ?? 0) + 1;
    return Object.entries(m).sort((a, b) => b[1] - a[1]);
  }, [editRecords]);

  function onEdit(id: string, key: string, val: string) {
    setEdits((p) => ({ ...p, [id]: { ...(p[id] ?? {}), [key]: val } }));
  }
  function openReview(index: number) {
    setReviewIndex(index);
    setReviewOpen(true);
  }

  function exportCsv() {
    const esc = (v: unknown) => {
      const s = v == null ? "" : String(v);
      return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
    };
    const header = COLS.join(",");
    const body = rows
      .map((r) => COLS.map((c) => esc(fieldValue(r, edits, c))).join(","))
      .join("\n");
    const url = URL.createObjectURL(new Blob([header + "\n" + body], { type: "text/csv" }));
    const a = document.createElement("a");
    a.href = url;
    a.download = "folletos.csv";
    a.click();
    URL.revokeObjectURL(url);
    void saveEdits(editRecords); // persistir diffs para análisis posterior
  }

  function downloadReport() {
    const report = {
      generated_at: new Date().toISOString(),
      total_images: rows.length,
      images_edited: editRecords.length,
      per_field: Object.fromEntries(perField),
      records: editRecords,
    };
    const url = URL.createObjectURL(new Blob([JSON.stringify(report, null, 2)], { type: "application/json" }));
    const a = document.createElement("a");
    a.href = url;
    a.download = "analisis_ediciones.json";
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <Container size="xl" py="lg">
      <Stack gap="lg">
        <Group justify="space-between" align="flex-start" wrap="nowrap">
          <Group gap="sm" align="center" wrap="nowrap">
            <ThemeIcon variant="light" size={44} radius="md">
              <IconMapPin size={26} />
            </ThemeIcon>
            <div>
              <Title order={2}>OCR de reparto de folletos</Title>
              <Text c="dimmed" size="sm">
                Subí fotos con overlay GPS y extraé dirección, fecha, CP y coordenadas.
              </Text>
            </div>
          </Group>
          <ColorSchemeToggle />
        </Group>

        <Paper withBorder p="md" radius="md"
          style={{ position: "sticky", top: 0, zIndex: 50, background: "var(--mantine-color-body)" }}>
          <Group justify="space-between" align="flex-end">
            <Group align="flex-end" gap="lg">
              <Stack gap={4}>
                <Text size="xs" fw={600} c="dimmed">NIVEL</Text>
                <SegmentedControl
                  value={level}
                  onChange={setLevel}
                  data={ALL_LEVELS.map((l) => ({ value: l, label: l, disabled: !levels.includes(l) }))}
                />
              </Stack>
              <Switch label="Debug" checked={debug}
                onChange={(e) => setDebug(e.currentTarget.checked)} />
              <Stack gap={4}>
                <Text size="xs" fw={600} c="dimmed">WORKERS</Text>
                <Tooltip multiline w={280} withArrow
                  label="Procesa varias imágenes en paralelo, en procesos separados (más rápido en lotes). Cada worker carga su propia copia del modelo OCR, así que más workers = más RAM. El backend lo limita según la RAM y los núcleos disponibles.">
                  <NumberInput value={workers} onChange={(v) => setWorkers(Number(v) || 1)}
                    min={1} max={16} step={1} w={90} clampBehavior="strict" />
                </Tooltip>
              </Stack>
            </Group>
            <Group>
              <Button leftSection={<IconPlayerPlay size={16} />} loading={running}
                disabled={!files.length} onClick={() => run(files, level, debug, workers)}>
                Procesar{files.length ? ` ${files.length}` : ""}
              </Button>
              <Button variant="default" leftSection={<IconEye size={16} />}
                disabled={!rows.length} onClick={() => openReview(0)}>Revisar</Button>
              <Button variant="light" leftSection={<IconDownload size={16} />}
                disabled={!rows.length} onClick={exportCsv}>CSV</Button>
            </Group>
          </Group>
        </Paper>

        <Dropzone onFiles={setFiles} count={files.length} />

        {rows.length > 0 && (
          <Stack gap="xs">
            <Group justify="space-between">
              <Text size="sm" c="dimmed">{done}/{rows.length} procesadas · nivel {rows[0]?.level ?? level}</Text>
              {running && <Badge variant="light" color="indigo">procesando…</Badge>}
            </Group>
            <Progress value={progress} animated={running} />

            <Group gap="xs" wrap="wrap">
              <Badge variant="light" color="grape">{editRecords.length}/{rows.length} editadas</Badge>
              <Button size="compact-xs" variant="subtle"
                leftSection={<IconFileDownload size={14} />} onClick={downloadReport}>
                Descargar análisis de ediciones
              </Button>
            </Group>

            <ResultsTable rows={rows} edits={edits} onEdit={onEdit}
              onReview={openReview} debug={debug} />
          </Stack>
        )}
      </Stack>

      <ReviewModal
        opened={reviewOpen}
        onClose={() => setReviewOpen(false)}
        rows={rows}
        index={reviewIndex}
        setIndex={setReviewIndex}
        edits={edits}
        onEdit={onEdit}
      />
    </Container>
  );
}

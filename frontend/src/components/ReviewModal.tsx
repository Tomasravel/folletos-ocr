import { useEffect, useMemo } from "react";
import {
  ActionIcon, Badge, Box, Button, CopyButton, Group, Image, Modal,
  ScrollArea, Stack, Text, TextInput, Tooltip,
} from "@mantine/core";
import { IconCheck, IconChevronLeft, IconChevronRight, IconCopy } from "@tabler/icons-react";
import type { Row } from "../hooks/useProcessStream";
import { COLS, fieldValue, rowTsv, type Edits } from "../fields";
import { StageTimeline } from "./StageTimeline";

export function ReviewModal({
  opened, onClose, rows, index, setIndex, edits, onEdit,
}: {
  opened: boolean;
  onClose: () => void;
  rows: Row[];
  index: number;
  setIndex: (i: number) => void;
  edits: Edits;
  onEdit: (id: string, key: string, val: string) => void;
}) {
  const row = rows[index];
  const url = useMemo(() => (row?.file ? URL.createObjectURL(row.file) : ""), [row?.file]);
  useEffect(() => () => { if (url) URL.revokeObjectURL(url); }, [url]);

  useEffect(() => {
    if (!opened) return;
    const h = (e: KeyboardEvent) => {
      if (e.key === "ArrowLeft") setIndex(Math.max(0, index - 1));
      if (e.key === "ArrowRight") setIndex(Math.min(rows.length - 1, index + 1));
    };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [opened, index, rows.length, setIndex]);

  if (!row) return null;

  return (
    <Modal
      opened={opened}
      onClose={onClose}
      fullScreen
      radius={0}
      title={
        <Group gap="sm">
          <Text fw={600}>Revisar</Text>
          <Badge variant="light">{index + 1} / {rows.length}</Badge>
        </Group>
      }
    >
      <Group align="stretch" gap="lg" wrap="nowrap" style={{ height: "calc(100vh - 130px)" }}>
        <Box
          style={{
            flex: 1, minWidth: 0, display: "flex", alignItems: "center",
            justifyContent: "center", borderRadius: 8,
            background: "var(--mantine-color-body)",
            border: "1px solid var(--mantine-color-default-border)",
          }}
        >
          {url ? <Image src={url} fit="contain" mah="82vh" /> : <Text c="dimmed">sin imagen</Text>}
        </Box>

        <ScrollArea style={{ width: 380 }} type="auto">
          <Stack gap="sm" pr="sm">
            <Group justify="space-between" wrap="nowrap">
              <Text fw={600} truncate title={row.name} style={{ maxWidth: 230 }}>{row.name}</Text>
              <CopyButton value={rowTsv(row, edits)}>
                {({ copied, copy }) => (
                  <Button size="xs" variant="light" color={copied ? "teal" : undefined}
                    leftSection={copied ? <IconCheck size={14} /> : <IconCopy size={14} />} onClick={copy}>
                    {copied ? "Copiado" : "Copiar fila"}
                  </Button>
                )}
              </CopyButton>
            </Group>

            <StageTimeline events={row.events}
              processing={row.status === "queued" || row.status === "preview"} />

            {COLS.map((c) => {
              const val = fieldValue(row, edits, c);
              return (
                <TextInput
                  key={c}
                  label={c}
                  value={val}
                  onChange={(e) => onEdit(row.image_id, c, e.currentTarget.value)}
                  rightSection={
                    <CopyButton value={val}>
                      {({ copied, copy }) => (
                        <Tooltip label={copied ? "Copiado" : "Copiar"} withArrow>
                          <ActionIcon variant="subtle" color={copied ? "teal" : "gray"} onClick={copy}>
                            {copied ? <IconCheck size={16} /> : <IconCopy size={16} />}
                          </ActionIcon>
                        </Tooltip>
                      )}
                    </CopyButton>
                  }
                />
              );
            })}
          </Stack>
        </ScrollArea>
      </Group>

      <Group justify="space-between" mt="md">
        <Button variant="default" leftSection={<IconChevronLeft size={16} />}
          onClick={() => setIndex(Math.max(0, index - 1))} disabled={index === 0}>
          Anterior
        </Button>
        <Text size="sm" c="dimmed">{index + 1} de {rows.length}</Text>
        <Button variant="default" rightSection={<IconChevronRight size={16} />}
          onClick={() => setIndex(Math.min(rows.length - 1, index + 1))}
          disabled={index === rows.length - 1}>
          Siguiente
        </Button>
      </Group>
    </Modal>
  );
}

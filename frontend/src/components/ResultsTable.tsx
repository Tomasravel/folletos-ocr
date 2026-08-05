import { Fragment } from "react";
import { ActionIcon, Badge, CopyButton, Group, Loader, Table, Text, TextInput, Tooltip } from "@mantine/core";
import { IconCheck, IconCopy, IconEye } from "@tabler/icons-react";
import type { Row } from "../hooks/useProcessStream";
import { COLS, fieldValue, rowTsv, type Edits } from "../fields";
import { StageTimeline } from "./StageTimeline";
import { DebugGallery } from "./DebugGallery";

function Status({ r }: { r: Row }) {
  if (r.status === "queued")
    return <Group gap={6} wrap="nowrap"><Loader size="xs" /><Text size="xs" c="dimmed">en cola</Text></Group>;
  if (r.status === "preview")
    return <Group gap={6} wrap="nowrap"><Loader size="xs" color="yellow" /><Badge size="sm" color="yellow" variant="light">refinando…</Badge></Group>;
  if (r.status === "error")
    return <Badge size="sm" color="red" variant="light">error</Badge>;
  return <Badge size="sm" color="teal" variant="light">listo</Badge>;
}

export function ResultsTable({ rows, edits, onEdit, onReview, debug }: {
  rows: Row[];
  edits: Edits;
  onEdit: (id: string, key: string, val: string) => void;
  onReview: (index: number) => void;
  debug: boolean;
}) {
  return (
    <Table.ScrollContainer minWidth={1040}>
      <Table striped highlightOnHover withTableBorder verticalSpacing="xs" horizontalSpacing="sm">
        <Table.Thead>
          <Table.Tr>
            <Table.Th w={70} />
            <Table.Th>imagen</Table.Th>
            <Table.Th>estado</Table.Th>
            {COLS.map((c) => <Table.Th key={c}>{c}</Table.Th>)}
            <Table.Th>pasos</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {rows.map((r, i) => {
            const runId = r.events[r.events.length - 1]?.run_id;
            return (
              <Fragment key={r.image_id}>
                <Table.Tr>
                  <Table.Td>
                    <Group gap={4} wrap="nowrap">
                      <Tooltip label="Revisar" withArrow>
                        <ActionIcon variant="subtle" onClick={() => onReview(i)}><IconEye size={16} /></ActionIcon>
                      </Tooltip>
                      <CopyButton value={rowTsv(r, edits)}>
                        {({ copied, copy }) => (
                          <Tooltip label={copied ? "Copiado" : "Copiar fila (TSV)"} withArrow>
                            <ActionIcon variant="subtle" color={copied ? "teal" : "gray"} onClick={copy}>
                              {copied ? <IconCheck size={16} /> : <IconCopy size={16} />}
                            </ActionIcon>
                          </Tooltip>
                        )}
                      </CopyButton>
                    </Group>
                  </Table.Td>
                  <Table.Td maw={190}>
                    <Text size="sm" truncate title={r.name}>{r.name}</Text>
                  </Table.Td>
                  <Table.Td><Status r={r} /></Table.Td>
                  {COLS.map((c) => (
                    <Table.Td key={c} miw={110}>
                      <TextInput size="xs" variant="unstyled" placeholder="—"
                        value={fieldValue(r, edits, c)}
                        onChange={(e) => onEdit(r.image_id, c, e.currentTarget.value)} />
                    </Table.Td>
                  ))}
                  <Table.Td>
                    <StageTimeline events={r.events}
                      processing={r.status === "queued" || r.status === "preview"} />
                  </Table.Td>
                </Table.Tr>
                {debug && runId && (
                  <Table.Tr>
                    <Table.Td colSpan={COLS.length + 4}>
                      <DebugGallery runId={runId} image={r.name} />
                    </Table.Td>
                  </Table.Tr>
                )}
              </Fragment>
            );
          })}
        </Table.Tbody>
      </Table>
    </Table.ScrollContainer>
  );
}

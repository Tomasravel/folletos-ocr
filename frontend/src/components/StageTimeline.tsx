import type { StageEvent } from "../types";
import { Badge, Group, Loader, Tooltip } from "@mantine/core";

export function StageTimeline({ events, processing }: { events: StageEvent[]; processing?: boolean }) {
  return (
    <Group gap={6} wrap="nowrap">
      {events.map((e, i) => {
        const ms = Object.values(e.timings_ms).reduce((a, b) => a + b, 0);
        const label = `${e.engine}/${e.parser} · ${ms} ms${e.warnings.length ? " · " + e.warnings.join("; ") : ""}`;
        return (
          <Tooltip key={i} label={label} withArrow>
            <Badge size="sm" radius="sm" variant="light"
                   color={e.stage === "final" ? "teal" : "yellow"}>
              {e.engine}/{e.parser}{e.warnings.length ? " ⚠️" : ""}
            </Badge>
          </Tooltip>
        );
      })}
      {processing && <Loader size="xs" />}
    </Group>
  );
}

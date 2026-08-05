import { Anchor, Group, Image, Stack, Text } from "@mantine/core";
import { IconDownload } from "@tabler/icons-react";

export function DebugGallery({ runId, image }: { runId: string; image: string }) {
  const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
  const seg = encodeURIComponent(image);
  const items: [string, string][] = [
    ["annot_easyocr", "EasyOCR"],
    ["annot_paddleocr", "PaddleOCR"],
    ["annot_fields", "Campos"],
  ];
  return (
    <Stack gap="xs" py="xs">
      <Group gap="md" align="flex-start">
        {items.map(([n, label]) => (
          <Stack key={n} gap={4} align="center">
            <Image w={200} radius="sm" fit="contain"
                   src={`${API}/debug/${runId}/${seg}/${n}.jpg`}
                   onError={(e) => ((e.currentTarget as HTMLImageElement).style.display = "none")} />
            <Text size="xs" c="dimmed">{label}</Text>
          </Stack>
        ))}
      </Group>
      <Group gap={4}>
        <IconDownload size={14} />
        <Anchor href={`${API}/debug/${runId}/bundle.zip`} size="sm">Descargar bundle</Anchor>
      </Group>
    </Stack>
  );
}

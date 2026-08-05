import { useRef } from "react";
import { Dropzone as MantineDropzone, IMAGE_MIME_TYPE } from "@mantine/dropzone";
import { Button, Group, Stack, Text } from "@mantine/core";
import { IconFolder, IconPhoto, IconUpload, IconX } from "@tabler/icons-react";

const IMG_RE = /\.(jpe?g|png|webp|gif|bmp|tiff?)$/i;

export function Dropzone({ onFiles, count }: { onFiles: (f: File[]) => void; count: number }) {
  const folderRef = useRef<HTMLInputElement>(null);

  return (
    <Stack gap="xs">
      <MantineDropzone onDrop={onFiles} accept={IMAGE_MIME_TYPE} multiple radius="md" p="lg">
        <Group justify="center" gap="lg" mih={110} style={{ pointerEvents: "none" }}>
          <MantineDropzone.Accept>
            <IconUpload size={46} stroke={1.4} color="var(--mantine-color-indigo-6)" />
          </MantineDropzone.Accept>
          <MantineDropzone.Reject>
            <IconX size={46} stroke={1.4} color="var(--mantine-color-red-6)" />
          </MantineDropzone.Reject>
          <MantineDropzone.Idle>
            <IconPhoto size={46} stroke={1.4} color="var(--mantine-color-dimmed)" />
          </MantineDropzone.Idle>
          <div>
            <Text size="lg" fw={500} inline>Arrastrá imágenes o una carpeta acá</Text>
            <Text size="sm" c="dimmed" inline mt={7}>
              {count > 0 ? `${count} imagen(es) lista(s)` : "JPG · PNG · WEBP · o hacé click para elegir"}
            </Text>
          </div>
        </Group>
      </MantineDropzone>

      <Group justify="center" gap="xs">
        <Text size="xs" c="dimmed">o</Text>
        <Button size="xs" variant="light" leftSection={<IconFolder size={14} />}
          onClick={() => folderRef.current?.click()}>
          Elegir carpeta
        </Button>
      </Group>

      <input
        ref={folderRef}
        type="file"
        hidden
        multiple
        {...({ webkitdirectory: "", directory: "" } as Record<string, string>)}
        onChange={(e) => {
          const picked = Array.from(e.target.files ?? []).filter((f) => IMG_RE.test(f.name));
          if (picked.length) onFiles(picked);
          e.target.value = "";
        }}
      />
    </Stack>
  );
}

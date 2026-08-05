import { ActionIcon, useComputedColorScheme, useMantineColorScheme } from "@mantine/core";
import { IconMoon, IconSun } from "@tabler/icons-react";

export function ColorSchemeToggle() {
  const { setColorScheme } = useMantineColorScheme();
  const computed = useComputedColorScheme("light");
  const dark = computed === "dark";
  return (
    <ActionIcon variant="default" size="lg" radius="md" aria-label="Cambiar tema"
      onClick={() => setColorScheme(dark ? "light" : "dark")}>
      {dark ? <IconSun size={18} /> : <IconMoon size={18} />}
    </ActionIcon>
  );
}

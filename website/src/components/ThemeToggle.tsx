import styles from "./ThemeToggle.module.scss";

export type ThemeMode = "auto" | "light" | "dark";

type ThemeToggleProps = {
  labels?: Record<ThemeMode, string> & { ariaLabel: string };
  mode: ThemeMode;
  onChange: (mode: ThemeMode) => void;
};

const modes: ThemeMode[] = ["auto", "light", "dark"];

const defaultLabels: Record<ThemeMode, string> & { ariaLabel: string } = {
  ariaLabel: "Theme selector",
  auto: "auto",
  light: "light",
  dark: "dark"
};

export function ThemeToggle({ labels = defaultLabels, mode, onChange }: ThemeToggleProps) {
  return (
    <div className={styles.toggle} aria-label={labels.ariaLabel} role="group">
      {modes.map((themeMode) => (
        <button
          aria-pressed={mode === themeMode}
          className={mode === themeMode ? styles.active : undefined}
          key={themeMode}
          onClick={() => onChange(themeMode)}
          type="button"
        >
          {labels[themeMode]}
        </button>
      ))}
    </div>
  );
}

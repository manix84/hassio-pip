import styles from "./ThemeToggle.module.scss";

export type ThemeMode = "auto" | "light" | "dark";

type ThemeToggleProps = {
  mode: ThemeMode;
  onChange: (mode: ThemeMode) => void;
};

const modes: ThemeMode[] = ["auto", "light", "dark"];

export function ThemeToggle({ mode, onChange }: ThemeToggleProps) {
  return (
    <div className={styles.toggle} aria-label="Theme selector">
      {modes.map((themeMode) => (
        <button
          aria-pressed={mode === themeMode}
          className={mode === themeMode ? styles.active : undefined}
          key={themeMode}
          onClick={() => onChange(themeMode)}
          type="button"
        >
          {themeMode}
        </button>
      ))}
    </div>
  );
}

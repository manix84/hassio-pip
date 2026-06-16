import styles from "./StatusBadge.module.scss";

export type StatusKind = "complete" | "planned" | "future";

const labels: Record<StatusKind, string> = {
  complete: "Complete",
  planned: "Planned",
  future: "Future"
};

export function StatusBadge({
  label,
  status
}: {
  label?: string;
  status: StatusKind;
}) {
  return (
    <span className={`${styles.badge} ${styles[status]}`}>
      {label ?? labels[status]}
    </span>
  );
}

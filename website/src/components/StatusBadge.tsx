import styles from "./StatusBadge.module.scss";

export type StatusKind = "phase1" | "planned" | "future";

const labels: Record<StatusKind, string> = {
  phase1: "Phase 1",
  planned: "Planned",
  future: "Future"
};

export function StatusBadge({ status }: { status: StatusKind }) {
  return <span className={`${styles.badge} ${styles[status]}`}>{labels[status]}</span>;
}

import styles from "./FeatureCard.module.scss";
import { StatusBadge, type StatusKind } from "./StatusBadge";

type FeatureCardProps = {
  title: string;
  description: string;
  status: StatusKind;
  statusLabel?: string;
};

export function FeatureCard({
  title,
  description,
  status,
  statusLabel
}: FeatureCardProps) {
  return (
    <article className={styles.card}>
      <StatusBadge label={statusLabel} status={status} />
      <h3>{title}</h3>
      <p>{description}</p>
    </article>
  );
}

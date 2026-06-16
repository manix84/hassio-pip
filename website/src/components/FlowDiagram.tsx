import styles from "./FlowDiagram.module.scss";

type FlowDiagramProps = {
  className?: string;
  steps: string[];
};

export function FlowDiagram({ className, steps }: FlowDiagramProps) {
  return (
    <ol className={`${styles.flow} ${className ?? ""}`}>
      {steps.map((step, index) => (
        <li className={styles.stepGroup} key={step}>
          <span className={styles.stepCard}>{step}</span>
          {index < steps.length - 1 ? (
            <span aria-hidden="true" className={styles.arrow}>
              →
            </span>
          ) : null}
        </li>
      ))}
    </ol>
  );
}

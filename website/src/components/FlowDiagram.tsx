import styles from "./FlowDiagram.module.scss";

type FlowDiagramProps = {
  steps: string[];
};

export function FlowDiagram({ steps }: FlowDiagramProps) {
  return (
    <ol className={styles.flow}>
      {steps.map((step) => (
        <li key={step}>
          <span>{step}</span>
        </li>
      ))}
    </ol>
  );
}

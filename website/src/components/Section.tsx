import type { ReactNode } from "react";
import styles from "./Section.module.scss";

type SectionProps = {
  id?: string;
  eyebrow?: string;
  title: string;
  children: ReactNode;
};

export function Section({ id, eyebrow, title, children }: SectionProps) {
  return (
    <section className={styles.section} id={id}>
      <div className={styles.heading}>
        {eyebrow ? <span className={styles.eyebrow}>{eyebrow}</span> : null}
        <h2>{title}</h2>
      </div>
      {children}
    </section>
  );
}

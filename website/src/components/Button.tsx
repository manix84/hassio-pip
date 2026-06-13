import type { ReactNode } from "react";
import styles from "./Button.module.scss";

type ButtonVariant = "primary" | "secondary";

type ButtonProps = {
  href: string;
  children: ReactNode;
  variant?: ButtonVariant;
};

export function Button({ href, children, variant = "primary" }: ButtonProps) {
  return (
    <a className={`${styles.button} ${styles[variant]}`} href={href}>
      {children}
    </a>
  );
}

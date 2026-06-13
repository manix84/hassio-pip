import styles from "./CodeBlock.module.scss";

type CodeBlockProps = {
  code: string;
  language?: string;
};

export function CodeBlock({ code, language = "yaml" }: CodeBlockProps) {
  return (
    <pre className={styles.codeBlock}>
      <code data-language={language}>{code.trim()}</code>
    </pre>
  );
}

import { useEffect, useMemo, useState, type ReactNode } from "react";
import styles from "./CodeBlock.module.scss";

type CodeBlockProps = {
  code: string;
  language?: string;
  labels?: {
    copyAriaLabel: string;
    copyFailed: string;
    copied: string;
    copyTitle: string;
    toolbar: string;
  };
};

type CopyState = "idle" | "success" | "error";

function CopyIcon() {
  return (
    <svg aria-hidden="true" focusable="false" viewBox="0 0 24 24">
      <rect height="13" rx="2" width="13" x="8" y="8" />
      <path d="M5 16H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v1" />
    </svg>
  );
}

function highlightYamlValue(value: string, key: string): ReactNode {
  const trimmedValue = value.trim();

  if (!trimmedValue) {
    return value;
  }

  const leadingWhitespace = value.slice(0, value.indexOf(trimmedValue));
  const leading = key ? `${leadingWhitespace}` : "";

  if (/^#/.test(trimmedValue)) {
    return (
      <>
        {leading}
        <span className={styles.comment}>{trimmedValue}</span>
      </>
    );
  }

  const commentIndex = trimmedValue.indexOf(" #");
  const valuePart = commentIndex >= 0 ? trimmedValue.slice(0, commentIndex) : trimmedValue;
  const commentPart = commentIndex >= 0 ? trimmedValue.slice(commentIndex + 1) : "";
  const valueClass =
    /^["'].*["']$/.test(valuePart)
      ? styles.string
      : /^(true|false|null)$/i.test(valuePart)
        ? styles.boolean
        : /^-?\d+(\.\d+)?$/.test(valuePart)
          ? styles.number
          : "";

  return (
    <>
      {leading}
      {valueClass ? <span className={valueClass}>{valuePart}</span> : valuePart}
      {commentPart ? <> <span className={styles.comment}>{commentPart}</span></> : null}
    </>
  );
}

function highlightYamlLine(line: string, index: number): ReactNode {
  const keyValueMatch = line.match(/^(\s*(?:-\s*)?)([^#:\n]+?)(:)(.*)$/);

  if (!keyValueMatch) {
    return (
      <span className={styles.line} key={`${index}-${line}`}>
        {highlightYamlValue(line, "")}
      </span>
    );
  }

  const [, prefix, key, separator, value] = keyValueMatch;

  return (
    <span className={styles.line} key={`${index}-${key}`}>
      {prefix}
      <span className={styles.key}>{key}</span>
      <span className={styles.separator}>{separator}</span>
      {highlightYamlValue(value, key)}
    </span>
  );
}

function highlightCode(code: string, language: string) {
  if (language !== "yaml" && language !== "home-assistant-yaml") {
    return code;
  }

  return code.split("\n").map((line, index) => highlightYamlLine(line, index));
}

const defaultLabels = {
  copyAriaLabel: "Copy Home Assistant YAML to clipboard",
  copyFailed: "Copy failed",
  copied: "Copied",
  copyTitle: "Copy YAML",
  toolbar: "Home Assistant YAML"
};

export function CodeBlock({ code, labels = defaultLabels, language = "yaml" }: CodeBlockProps) {
  const [copyState, setCopyState] = useState<CopyState>("idle");
  const trimmedCode = useMemo(() => code.trim(), [code]);
  const highlightedCode = useMemo(
    () => highlightCode(trimmedCode, language),
    [language, trimmedCode]
  );

  useEffect(() => {
    if (copyState === "idle") {
      return;
    }

    const timeoutId = window.setTimeout(() => setCopyState("idle"), 2200);
    return () => window.clearTimeout(timeoutId);
  }, [copyState]);

  async function copyToClipboard() {
    if (!navigator.clipboard) {
      setCopyState("error");
      return;
    }

    try {
      await navigator.clipboard.writeText(trimmedCode);
      setCopyState("success");
    } catch {
      setCopyState("error");
    }
  }

  const feedbackText =
    copyState === "success"
      ? labels.copied
      : copyState === "error"
        ? labels.copyFailed
        : "";

  return (
    <div className={styles.codeFrame}>
      <div className={styles.toolbar}>
        <span>{labels.toolbar}</span>
        <button
          aria-label={labels.copyAriaLabel}
          className={styles.copyButton}
          data-state={copyState}
          onClick={copyToClipboard}
          title={labels.copyTitle}
          type="button"
        >
          <CopyIcon />
        </button>
      </div>
      <pre className={styles.codeBlock}>
        <code data-language={language}>{highlightedCode}</code>
      </pre>
      <span aria-live="polite" className={styles.feedback} data-state={copyState}>
        {feedbackText}
      </span>
    </div>
  );
}

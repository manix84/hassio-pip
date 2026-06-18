import type { StatusKind } from "../components/StatusBadge";
import type { ThemeMode } from "../components/ThemeToggle";

export type WebsiteContent = {
  codeBlock: {
    copyAriaLabel: string;
    copyFailed: string;
    copied: string;
    copyTitle: string;
    toolbar: string;
  };
  currentStatus: {
    body: string[];
    eyebrow: string;
    title: string;
  };
  deviceSupport: {
    eyebrow: string;
    items: Array<{
      description: string;
      label: string;
      status: StatusKind;
      title: string;
    }>;
    title: string;
  };
  example: {
    eyebrow: string;
    mjpegTitle: string;
    standardTitle: string;
    tabAriaLabel: string;
    title: string;
  };
  faqItems: Array<{ answer: string; question: string }>;
  faqSection: {
    eyebrow: string;
    title: string;
  };
  features: Array<{
    description: string;
    status: StatusKind;
    title: string;
  }>;
  featuresSection: {
    eyebrow: string;
    title: string;
  };
  flow: {
    eyebrow: string;
    steps: string[];
    title: string;
  };
  footerAriaLabel: string;
  footerLinks: {
    architecture: string;
    development: string;
    github: string;
    license: string;
    releases: string;
    roadmap: string;
    translations: string;
  };
  hero: {
    alt: string;
    ctaPrimary: string;
    ctaSecondary: string;
    overlayKicker: string;
    overlayState: string;
    overlayTitle: string;
    signal: string;
    subtitle: string;
    title: string;
    versionLabel: string;
  };
  languageAriaLabel: string;
  problem: {
    body: string;
    eyebrow: string;
    title: string;
  };
  roadmap: {
    eyebrow: string;
    items: string[];
    title: string;
  };
  solution: {
    eyebrow: string;
    imageAlt: string;
    steps: string[];
    title: string;
  };
  statusLabels: Record<StatusKind, string>;
  theme: Record<ThemeMode, string> & { ariaLabel: string };
  translations: {
    eyebrow: string;
    tiers: Array<{ label: string; languages: string; status: StatusKind }>;
    title: string;
  };
  visualCards: Array<{ text: string; title: string }>;
  visualAlt: {
    network: string;
    phase: string;
  };
};

export const supportedLocales = [
  { code: "en", label: "English", path: "/" },
  { code: "de", label: "Deutsch", path: "/de/" },
  { code: "nl", label: "Nederlands", path: "/nl/" },
  { code: "fr", label: "Français", path: "/fr/" },
  { code: "es", label: "Español", path: "/es/" },
  { code: "it", label: "Italiano", path: "/it/" },
  { code: "pt-br", label: "Português (Brasil)", path: "/pt-br/" },
  { code: "pl", label: "Polski", path: "/pl/" },
] as const;

export type WebsiteLocale = (typeof supportedLocales)[number]["code"];

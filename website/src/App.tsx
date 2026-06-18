import { useEffect, useId, useState } from "react";
import styles from "./App.module.scss";
import controlMockup from "./assets/home-assistant-control.png";
import networkMockup from "./assets/local-network-pip.png";
import heroCleanMockup from "./assets/tv-pip-hero-clean.png";
import phaseOnePromoMockup from "./assets/tv-pip-promo.png";
import { Button } from "./components/Button";
import { CodeBlock } from "./components/CodeBlock";
import { FeatureCard } from "./components/FeatureCard";
import { FlowDiagram } from "./components/FlowDiagram";
import { Section } from "./components/Section";
import { StatusBadge } from "./components/StatusBadge";
import { ThemeToggle, type ThemeMode } from "./components/ThemeToggle";
import { supportedLocales, websiteContent, type WebsiteLocale } from "./locales";

export {
  faqItems,
  supportedLocales,
  translationTiers,
  websiteContent,
  type WebsiteLocale,
} from "./locales";

const githubUrl = "https://github.com/manix84/ha-tv-pip";
const roadmapUrl =
  "https://github.com/manix84/ha-tv-pip/blob/main/docs/roadmap.md";
const architectureUrl =
  "https://github.com/manix84/ha-tv-pip/blob/main/docs/architecture.md";
const developmentUrl =
  "https://github.com/manix84/ha-tv-pip/blob/main/docs/development.md";
const translationsUrl =
  "https://github.com/manix84/ha-tv-pip/blob/main/docs/translations.md";
const releasesUrl = "https://github.com/manix84/ha-tv-pip/releases";
const licenseUrl = "https://github.com/manix84/ha-tv-pip/blob/main/LICENSE";

export const localePreferenceKey = "ha-tv-pip-locale";
type ExampleTab = "standard" | "mjpeg";
type FaqItem = {
  answer: string;
  question: string;
};

const routedLocaleCodes = new Set<WebsiteLocale>(
  supportedLocales
    .filter((locale) => locale.code !== "en")
    .map((locale) => locale.code)
);

export function FaqDisclosure({ item }: { item: FaqItem }) {
  const [isOpen, setIsOpen] = useState(false);
  const panelId = useId();

  return (
    <article className={styles.faqItem}>
      <button
        aria-controls={panelId}
        aria-expanded={isOpen}
        className={styles.faqQuestion}
        onClick={() => setIsOpen((current) => !current)}
        type="button"
      >
        <span>{item.question}</span>
      </button>
      <div
        aria-hidden={!isOpen}
        className={styles.faqAnswer}
        data-open={isOpen ? "true" : "false"}
        id={panelId}
      >
        <div>
          <p>{item.answer}</p>
        </div>
      </div>
    </article>
  );
}

const supportedLocaleCodes = new Set<WebsiteLocale>(
  supportedLocales.map((locale) => locale.code)
);

export function getRouteLocaleFromPath(pathname: string): WebsiteLocale | null {
  const matchedRoutedLocale = pathname
    .split("/")
    .filter(Boolean)
    .map((segment) => segment.toLowerCase())
    .find((segment) => routedLocaleCodes.has(segment as WebsiteLocale));

  return matchedRoutedLocale ? (matchedRoutedLocale as WebsiteLocale) : null;
}

export function getLocaleFromPath(pathname: string): WebsiteLocale {
  return getRouteLocaleFromPath(pathname) ?? "en";
}

export function getPreferredLocale(
  browserLanguages: readonly string[],
  savedPreference?: string | null
): WebsiteLocale {
  const savedLocale = getSavedLocale(savedPreference);
  if (savedLocale) {
    return savedLocale;
  }

  for (const language of browserLanguages) {
    const normalized = language.toLowerCase().replace("_", "-");
    if (supportedLocaleCodes.has(normalized as WebsiteLocale)) {
      return normalized as WebsiteLocale;
    }

    const baseLanguage = normalized.split("-")[0];
    if (baseLanguage === "pt") {
      return "pt-br";
    }
    if (supportedLocaleCodes.has(baseLanguage as WebsiteLocale)) {
      return baseLanguage as WebsiteLocale;
    }
  }

  return "en";
}

export function getSavedLocale(savedPreference?: string | null): WebsiteLocale | null {
  const savedLocale = savedPreference?.toLowerCase();
  return supportedLocaleCodes.has(savedLocale as WebsiteLocale)
    ? (savedLocale as WebsiteLocale)
    : null;
}

export function getInitialLocale(
  pathname: string,
  browserLanguages: readonly string[],
  savedPreference?: string | null
): WebsiteLocale {
  return (
    getSavedLocale(savedPreference) ??
    getRouteLocaleFromPath(pathname) ??
    getPreferredLocale(browserLanguages)
  );
}

export function getLocaleHref(pathname: string, locale: WebsiteLocale): string {
  const segments = pathname.split("/").filter(Boolean);
  const localeIndex = segments.findIndex((segment) =>
    routedLocaleCodes.has(segment.toLowerCase() as WebsiteLocale)
  );

  if (localeIndex === -1) {
    return locale === "en" ? "./" : `.${localePath(locale)}`;
  }

  const prefix = `/${segments.slice(0, localeIndex).join("/")}`;
  const basePath = prefix === "/" ? "" : prefix;
  return `${basePath}${localePath(locale)}`;
}

function localePath(locale: WebsiteLocale): string {
  return supportedLocales.find((item) => item.code === locale)?.path ?? "/";
}

const automationExample = `
alias: Show front door alert on TV
trigger:
  - platform: state
    entity_id: binary_sensor.front_door_bell_visitor
    to: "on"
action:
  - service: ha_tv_pip.show_camera
    target:
      device_id: living_room_tv
    data:
      camera_entity: camera.front_door
      duration_seconds: 30
      enter_pip: true
      stream_camera_entity: camera.front_door_sub
      snapshot_fallback: true
      snapshot_camera_entity: camera.front_door_sub
      title: Front door
      message: Someone is at the door
      position: top_right
      background_color: "#B30F0E0E"
      width: 720
      height: 405
`;

const mjpegAutomationExample = `
alias: Show front door alert with MJPEG fallback
trigger:
  - platform: state
    entity_id: binary_sensor.front_door_bell_visitor
    to: "on"
action:
  - service: ha_tv_pip.show_camera
    target:
      device_id: living_room_tv
    data:
      camera_entity: camera.front_door
      stream_type: mjpeg_first
      stream_camera_entity: camera.front_door_sub
      snapshot_fallback: true
      snapshot_camera_entity: camera.front_door
      duration_seconds: 30
      enter_pip: true
      title: Front door
      message: Motion detected
`;

function App() {
  const [locale, setLocale] = useState<WebsiteLocale>(() =>
    getInitialLocale(
      window.location.pathname,
      window.navigator.languages,
      window.localStorage.getItem(localePreferenceKey)
    )
  );

  const [themeMode, setThemeMode] = useState<ThemeMode>(() => {
    const saved = window.localStorage.getItem("ha-tv-pip-theme");
    return saved === "light" || saved === "dark" || saved === "auto"
      ? saved
      : "auto";
  });
  const [exampleTab, setExampleTab] = useState<ExampleTab>("standard");

  useEffect(() => {
    window.localStorage.setItem("ha-tv-pip-theme", themeMode);
    if (themeMode === "auto") {
      document.documentElement.removeAttribute("data-theme");
      return;
    }
    document.documentElement.dataset.theme = themeMode;
  }, [themeMode]);

  useEffect(() => {
    const routeLocale = getRouteLocaleFromPath(window.location.pathname);
    const savedLocale = getSavedLocale(window.localStorage.getItem(localePreferenceKey));

    if (!savedLocale && routeLocale) {
      window.localStorage.setItem(localePreferenceKey, routeLocale);
      setLocale(routeLocale);
      return;
    }

    window.localStorage.setItem(localePreferenceKey, locale);
    if (routeLocale !== locale && (locale !== "en" || routeLocale)) {
      window.location.replace(getLocaleHref(window.location.pathname, locale));
    }
  }, [locale]);

  const content = websiteContent[locale];
  const activeExample = exampleTab === "standard" ? automationExample : mjpegAutomationExample;
  const visualCards = content.visualCards.map((card, index) => ({
    ...card,
    image: index === 0 ? controlMockup : networkMockup,
  }));

  function handleLocaleSelection(localeCode: WebsiteLocale, href: string) {
    window.localStorage.setItem(localePreferenceKey, localeCode);
    setLocale(localeCode);
    window.location.assign(href);
  }

  return (
    <main>
      <ThemeToggle labels={content.theme} mode={themeMode} onChange={setThemeMode} />
      <section className={styles.hero}>
        <div className={styles.heroContent}>
          <div className={styles.heroText}>
            <StatusBadge label={content.statusLabels.complete} status="complete" />
            <p className={styles.version}>
              {content.hero.versionLabel} {__PROJECT_VERSION__}
            </p>
            <h1>{content.hero.title}</h1>
            <p className={styles.subheading}>{content.hero.subtitle}</p>
            <div className={styles.actions}>
              <Button href={githubUrl}>{content.hero.ctaPrimary}</Button>
              <Button href={roadmapUrl} variant="secondary">
                {content.hero.ctaSecondary}
              </Button>
            </div>
          </div>
          <figure className={styles.heroProductVisual}>
            <img
              alt={content.hero.alt}
              src={heroCleanMockup}
            />
            <figcaption className={styles.heroOverlay}>
              <span className={styles.overlayKicker}>{content.hero.overlayKicker}</span>
              <strong>{content.hero.overlayTitle}</strong>
              <span>{content.hero.overlayState}</span>
            </figcaption>
            <div className={styles.signalPanel} aria-hidden="true">
              <div>
                <span />
                <span />
                <span />
              </div>
              <p>{content.hero.signal}</p>
            </div>
          </figure>
        </div>
      </section>

      <Section
        eyebrow={content.problem.eyebrow}
        id="problem"
        title={content.problem.title}
      >
        <p className={styles.copy}>{content.problem.body}</p>
      </Section>

      <Section
        eyebrow={content.solution.eyebrow}
        id="solution"
        title={content.solution.title}
      >
        <div className={styles.solutionShowcase}>
          <div className={styles.solutionSteps}>
            {content.solution.steps.map((step) => (
              <p key={step}>{step}</p>
            ))}
          </div>
          <figure className={styles.imageCard}>
            <img
              alt={content.solution.imageAlt}
              src={controlMockup}
            />
          </figure>
        </div>
      </Section>

      <Section
        eyebrow={content.flow.eyebrow}
        id="how-it-works"
        title={content.flow.title}
      >
        <div className={styles.flowShowcase}>
          <FlowDiagram
            className={styles.compactFlow}
            steps={content.flow.steps}
          />
          <figure className={styles.imageCard}>
            <img
              alt={content.visualAlt.network}
              src={networkMockup}
            />
          </figure>
        </div>
      </Section>

      <Section
        eyebrow={content.featuresSection.eyebrow}
        id="features"
        title={content.featuresSection.title}
      >
        <div className={styles.visualGrid}>
          {visualCards.map((card) => (
            <article className={styles.visualCard} key={card.title}>
              <img alt="" src={card.image} />
              <div>
                <h3>{card.title}</h3>
                <p>{card.text}</p>
              </div>
            </article>
          ))}
        </div>
        <div className={styles.featureGrid}>
          {content.features.map((feature) => (
            <FeatureCard
              key={feature.title}
              title={feature.title}
              description={feature.description}
              status={feature.status}
              statusLabel={content.statusLabels[feature.status]}
            />
          ))}
        </div>
      </Section>

      <Section
        eyebrow={content.currentStatus.eyebrow}
        id="status"
        title={content.currentStatus.title}
      >
        <div className={styles.statusPanel}>
          <div>
            {content.currentStatus.body.map((paragraph) => (
              <p key={paragraph}>{paragraph}</p>
            ))}
          </div>
          <img
            alt={content.visualAlt.phase}
            className={styles.phaseOneImage}
            src={phaseOnePromoMockup}
          />
        </div>
      </Section>

      <Section
        eyebrow={content.roadmap.eyebrow}
        id="roadmap"
        title={content.roadmap.title}
      >
        <ul className={styles.roadmap}>
          {content.roadmap.items.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </Section>

      <Section
        eyebrow={content.example.eyebrow}
        id="examples"
        title={content.example.title}
      >
        <div className={styles.exampleTabs}>
          <div
            aria-label={content.example.tabAriaLabel}
            className={styles.exampleTabList}
            role="tablist"
          >
            <button
              aria-controls="example-panel"
              aria-selected={exampleTab === "standard"}
              id="example-tab-standard"
              onClick={() => setExampleTab("standard")}
              role="tab"
              type="button"
            >
              {content.example.standardTitle}
            </button>
            <button
              aria-controls="example-panel"
              aria-selected={exampleTab === "mjpeg"}
              id="example-tab-mjpeg"
              onClick={() => setExampleTab("mjpeg")}
              role="tab"
              type="button"
            >
              {content.example.mjpegTitle}
            </button>
          </div>
          <div
            aria-labelledby={
              exampleTab === "standard" ? "example-tab-standard" : "example-tab-mjpeg"
            }
            id="example-panel"
            role="tabpanel"
          >
            <CodeBlock
              code={activeExample}
              labels={content.codeBlock}
              language="home-assistant-yaml"
            />
          </div>
        </div>
      </Section>

      <Section
        eyebrow={content.faqSection.eyebrow}
        id="faq"
        title={content.faqSection.title}
      >
        <div className={styles.faqList}>
          {content.faqItems.map((item) => (
            <FaqDisclosure item={item} key={item.question} />
          ))}
        </div>
      </Section>

      <Section
        eyebrow={content.translations.eyebrow}
        title={content.translations.title}
      >
        <div className={styles.translationGrid}>
          {content.translations.tiers.map((tier) => (
            <article className={styles.translationItem} key={tier.label}>
              <div className={styles.translationHeader}>
                <strong>{tier.label}</strong>
                <StatusBadge
                  label={content.statusLabels[tier.status]}
                  status={tier.status}
                />
              </div>
              <p>{tier.languages}</p>
            </article>
          ))}
        </div>
      </Section>

      <footer className={styles.footer}>
        <div>
          <strong>HA TV PiP</strong>
          <span>v{__PROJECT_VERSION__}</span>
        </div>
        <div className={styles.footerNavigation}>
          <nav aria-label={content.footerAriaLabel}>
            <a href={githubUrl}>{content.footerLinks.github}</a>
            <a href={roadmapUrl}>{content.footerLinks.roadmap}</a>
            <a href={architectureUrl}>{content.footerLinks.architecture}</a>
            <a href={developmentUrl}>{content.footerLinks.development}</a>
            <a href={translationsUrl}>{content.footerLinks.translations}</a>
            <a href={releasesUrl}>{content.footerLinks.releases}</a>
            <a href={licenseUrl}>{content.footerLinks.license}</a>
          </nav>
          <nav className={styles.localeNav} aria-label={content.languageAriaLabel}>
            {supportedLocales.map((item) => {
              const href = getLocaleHref(window.location.pathname, item.code);
              return (
                <a
                  aria-current={item.code === locale ? "page" : undefined}
                  href={href}
                  key={item.code}
                  onClick={(event) => {
                    event.preventDefault();
                    handleLocaleSelection(item.code, href);
                  }}
                >
                  {item.label}
                </a>
              );
            })}
          </nav>
        </div>
      </footer>
    </main>
  );
}

export default App;

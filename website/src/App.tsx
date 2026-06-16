import { useEffect, useMemo, useState } from "react";
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

const automationExample = `
alias: Show front door on TV
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
      snapshot_fallback: true
      snapshot_camera_entity: camera.front_door_sub
`;

const features = [
  {
    title: "Android TV receiver app",
    description:
      "A Kotlin receiver app that owns playback, PiP behavior, and TV-friendly interaction.",
    status: "complete" as const,
  },
  {
    title: "Home Assistant custom integration",
    description:
      "A controller integration for discovery, pairing, services, and camera resolution.",
    status: "complete" as const,
  },
  {
    title: "Local-first control",
    description:
      "LAN receiver control with no cloud relay by default.",
    status: "complete" as const,
  },
  {
    title: "Automatic discovery",
    description:
      "mDNS discovery so Home Assistant can find receiver apps automatically.",
    status: "complete" as const,
  },
  {
    title: "Secure pairing",
    description:
      "TV-visible pairing flow so random LAN devices cannot trigger camera popups.",
    status: "complete" as const,
  },
  {
    title: "Camera stream support",
    description:
      "Home Assistant HLS camera streams with receiver-side compatibility feedback.",
    status: "complete" as const,
  },
  {
    title: "Snapshot support",
    description:
      "Still-image popups for fast alerts and fallback previews while video loads.",
    status: "complete" as const,
  },
  {
    title: "Remote receiver mode",
    description:
      "Outbound receiver transport for travel TVs without router port forwarding.",
    status: "planned" as const,
  },
];

const roadmapItems = [
  "Local control endpoint",
  "mDNS discovery",
  "Device pairing",
  "Home Assistant service",
  "Snapshot support",
  "WebRTC support",
  "Remote mode",
  "Play Store and HACS distribution",
];

export const faqItems = [
  {
    question: "Is HA TV PiP a cloud service?",
    answer:
      "No. Local control remains the default, and remote receiver mode connects your TV outbound to your own Home Assistant external URL. HA TV PiP does not run a hosted relay.",
  },
  {
    question: "Do I need to open ports on my router?",
    answer:
      "No port forwarding to the TV is planned. For remote receiver mode, the TV opens an outbound WebSocket connection to Home Assistant.",
  },
  {
    question: "Will this work with Nabu Casa?",
    answer:
      "Yes, the Home Assistant Cloud URL can be used as your Home Assistant external URL. That still does not make HA TV PiP itself a cloud service.",
  },
  {
    question: "Why do some camera streams show snapshots or errors?",
    answer:
      "Android TV devices can reject unsupported codecs or very high-resolution streams. HA TV PiP supports snapshot fallbacks now and will keep improving stream selection and compatibility.",
  },
  {
    question: "Can I hide the receiver app from my TV home screen?",
    answer:
      "Yes. The Home Assistant integration exposes Hide Launcher and Open Launcher controls so the app can behave more like an appliance after setup.",
  },
  {
    question: "Will HA TV PiP be translated?",
    answer:
      "Yes. English is the source language. Tier 1 translations are planned for the Phase 10 polish pass before broad release.",
  },
];

export const translationTiers = [
  {
    label: "Tier 1",
    languages:
      "English, German, Dutch, French, Spanish, Italian, Brazilian Portuguese, Polish",
  },
  {
    label: "Tier 2",
    languages:
      "Swedish, Norwegian, Danish, Finnish, Czech, Hungarian, Turkish, Japanese, Korean",
  },
  {
    label: "Tier 3",
    languages:
      "Simplified Chinese, Traditional Chinese, Indonesian, Hindi, Arabic, Ukrainian, Romanian, Greek",
  },
];

function App() {
  const [themeMode, setThemeMode] = useState<ThemeMode>(() => {
    const saved = window.localStorage.getItem("ha-tv-pip-theme");
    return saved === "light" || saved === "dark" || saved === "auto"
      ? saved
      : "auto";
  });

  useEffect(() => {
    window.localStorage.setItem("ha-tv-pip-theme", themeMode);
    if (themeMode === "auto") {
      document.documentElement.removeAttribute("data-theme");
      return;
    }
    document.documentElement.dataset.theme = themeMode;
  }, [themeMode]);

  const visualCards = useMemo(
    () => [
      {
        image: controlMockup,
        title: "Automation control surface",
        text: "A Home Assistant-friendly control plane for future receiver discovery, pairing, and service calls.",
      },
      {
        image: networkMockup,
        title: "Local-first receiver path",
        text: "The TV app owns playback and PiP while Home Assistant decides what should appear.",
      },
    ],
    []
  );

  return (
    <main>
      <ThemeToggle mode={themeMode} onChange={setThemeMode} />
      <section className={styles.hero}>
        <div className={styles.heroContent}>
          <div className={styles.heroText}>
            <StatusBadge status="complete" />
            <p className={styles.version}>Version {__PROJECT_VERSION__}</p>
            <h1>Show Home Assistant camera feeds on your Android TV.</h1>
            <p className={styles.subheading}>
              HA TV PiP lets Home Assistant automations open security camera
              feeds, snapshots, and alerts in Picture-in-Picture on Android TV
              and Google TV devices.
            </p>
            <div className={styles.actions}>
              <Button href={githubUrl}>View on GitHub</Button>
              <Button href={roadmapUrl} variant="secondary">
                Read the Roadmap
              </Button>
            </div>
          </div>
          <figure className={styles.heroProductVisual}>
            <img
              alt="Living room Android TV showing a security camera feed in Picture-in-Picture"
              src={heroCleanMockup}
            />
            <figcaption className={styles.heroOverlay}>
              <span className={styles.overlayKicker}>Android TV receiver</span>
              <strong>Playing test HLS stream</strong>
              <span>PiP mode ready</span>
            </figcaption>
            <div className={styles.signalPanel} aria-hidden="true">
              <div>
                <span />
                <span />
                <span />
              </div>
              <p>Local automation path</p>
            </div>
          </figure>
        </div>
      </section>

      <Section
        eyebrow="The problem"
        title="Smart-home alerts deserve a better TV moment."
      >
        <p className={styles.copy}>
          Home Assistant can detect doorbells, motion, people, and camera
          events, but showing those events naturally on a TV is still awkward.
        </p>
      </Section>

      <Section
        eyebrow="The solution"
        title="A receiver app for the TV, a controller in Home Assistant."
      >
        <div className={styles.solutionShowcase}>
          <div className={styles.solutionSteps}>
            <p>Install the Android TV receiver app.</p>
            <p>Install the Home Assistant integration.</p>
            <p>Pair them locally.</p>
            <p>Trigger camera popups from automations.</p>
          </div>
          <figure className={styles.imageCard}>
            <img
              alt="Mockup showing Home Assistant controls connected to an Android TV PiP receiver"
              src={controlMockup}
            />
          </figure>
        </div>
      </Section>

      <Section
        eyebrow="How it works"
        title="A local-first path from event to PiP popup."
      >
        <div className={styles.flowShowcase}>
          <FlowDiagram
            className={styles.compactFlow}
            steps={[
              "Home Assistant event",
              "HA TV PiP integration",
              "Android TV receiver app",
              "PiP camera popup",
            ]}
          />
          <figure className={styles.imageCard}>
            <img
              alt="Mockup showing a local smart-home network sending a camera feed to Android TV PiP"
              src={networkMockup}
            />
          </figure>
        </div>
      </Section>

      <Section
        eyebrow="Features"
        title="Built in phases, designed as one experience."
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
          {features.map((feature) => (
            <FeatureCard
              key={feature.title}
              title={feature.title}
              description={feature.description}
              status={feature.status}
            />
          ))}
        </div>
      </Section>

      <Section eyebrow="Current status" title="Phase 9: Remote receiver mode complete">
        <div className={styles.statusPanel}>
          <div>
            <p>
              HA TV PiP now supports discovery, TV-visible pairing,
              authenticated receiver control, camera stream popups, snapshots,
              snapshot previews, receiver management, and remote receiver
              transport.
            </p>
            <p>
              Remote mode connects a TV outbound to the user's own Home
              Assistant external URL. It is designed for external TVs without
              turning HA TV PiP into a hosted cloud service.
            </p>
          </div>
          <img
            alt="Promotional overview of HA TV PiP features beside an Android TV Picture-in-Picture mockup"
            className={styles.phaseOneImage}
            src={phaseOnePromoMockup}
          />
        </div>
      </Section>

      <Section
        eyebrow="Roadmap preview"
        title="The path from MVP to daily-driver smart-home tool."
      >
        <ul className={styles.roadmap}>
          {roadmapItems.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </Section>

      <Section eyebrow="Example automation" title="Where this is headed.">
        <CodeBlock code={automationExample} language="home-assistant-yaml" />
      </Section>

      <Section
        eyebrow="FAQ"
        title="Answers for setup worries and early troubleshooting."
      >
        <div className={styles.faqGrid}>
          {faqItems.map((item) => (
            <article className={styles.faqItem} key={item.question}>
              <h3>{item.question}</h3>
              <p>{item.answer}</p>
            </article>
          ))}
        </div>
      </Section>

      <Section
        eyebrow="Translations"
        title="Internationalization is part of the product plan."
      >
        <div className={styles.translationGrid}>
          {translationTiers.map((tier) => (
            <article className={styles.translationItem} key={tier.label}>
              <strong>{tier.label}</strong>
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
        <nav aria-label="Footer links">
          <a href={githubUrl}>GitHub</a>
          <a href={roadmapUrl}>Roadmap</a>
          <a href={architectureUrl}>Architecture</a>
          <a href={developmentUrl}>Development docs</a>
          <a href={translationsUrl}>Translations</a>
          <a href={releasesUrl}>Releases</a>
          <a href={licenseUrl}>License</a>
        </nav>
      </footer>
    </main>
  );
}

export default App;

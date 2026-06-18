import type { WebsiteContent } from "./types";

export const en = {
    codeBlock: {
      copyAriaLabel: "Copy Home Assistant YAML to clipboard",
      copyFailed: "Copy failed",
      copied: "Copied",
      copyTitle: "Copy YAML",
      toolbar: "Home Assistant YAML",
    },
    currentStatus: {
      body: [
        "HA TV PiP now supports discovery, TV-visible pairing, authenticated receiver control, camera stream popups, snapshots, styled notifications, receiver management, remote receiver transport, and per-camera receiver defaults.",
        "Post-1.0 compatibility work is underway. The Home Assistant integration can calibrate a camera against a receiver, preview and save recommended defaults, flag when a TV-safe restreamed source is likely needed, expose suggested next steps on the receiver device, and report whether the installed receiver is current, degraded, legacy, or incompatible. Future restreaming providers are now documented as planned extension points, not active requirements.",
      ],
      eyebrow: "Current status",
      title: "Post-v1.0 compatibility polish",
    },
    example: {
      eyebrow: "Example automation",
      mjpegTitle: "MJPEG fallback",
      standardTitle: "Default HLS path",
      tabAriaLabel: "Example automation type",
      title: "Where this is headed.",
    },
    deviceSupport: {
      eyebrow: "Device support",
      items: [
        {
          description: "The current receiver app target and the platform used for active development.",
          label: "Supported",
          status: "complete",
          title: "Android TV and Google TV",
        },
        {
          description: "Closest to the Android receiver model, so this is the most likely next platform family.",
          label: "Next likely",
          status: "planned",
          title: "Fire TV and Vega OS",
        },
        {
          description: "Useful platforms to investigate, but each may need a separate receiver design.",
          label: "Research",
          status: "future",
          title: "Samsung Tizen, LG webOS, Roku, and Apple TV",
        },
        {
          description: "Track these until a clear app distribution path and receiver capability model emerges.",
          label: "Watchlist",
          status: "future",
          title: "VIDAA, TiVo OS, and operator TV platforms",
        },
      ],
      title: "Platform support will expand carefully.",
    },
    faqItems: [
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
          "Android TV devices can reject unsupported codecs or very high-resolution streams. HA TV PiP supports snapshot fallbacks, separate stream camera entities, automatic MJPEG fallback, MJPEG-first mode, receiver capability checks, and camera compatibility testing. If HLS/MJPEG are unavailable or only snapshots work, calibration results flag that a TV-safe restreamed source is likely needed. Start with a lower-resolution or MJPEG camera entity; go2rtc, WebRTC, and transcoding are planned future provider paths.",
      },
      {
        question: "Can I hide the receiver app from my TV home screen?",
        answer:
          "Yes. The Home Assistant integration exposes Hide Launcher and Open Launcher controls so the app can behave more like an appliance after setup.",
      },
      {
        question: "Will HA TV PiP be translated?",
        answer:
          "Yes. English is the source language. Tier 1 translations are in place for the website, Android app, and Home Assistant integration, with native review still required before broad release.",
      },
    ],
    faqSection: {
      eyebrow: "FAQ",
      title: "Answers for setup worries and early troubleshooting.",
    },
    features: [
      {
        title: "Android TV receiver app",
        description:
          "A Kotlin receiver app that owns playback, PiP behavior, and TV-friendly interaction.",
        status: "complete",
      },
      {
        title: "Home Assistant custom integration",
        description:
          "A controller integration for discovery, pairing, services, and camera resolution.",
        status: "complete",
      },
      {
        title: "Local-first control",
        description: "LAN receiver control with no cloud relay by default.",
        status: "complete",
      },
      {
        title: "Automatic discovery",
        description:
          "mDNS discovery so Home Assistant can find receiver apps automatically.",
        status: "complete",
      },
      {
        title: "Secure pairing",
        description:
          "TV-visible pairing flow so random LAN devices cannot trigger camera popups.",
        status: "complete",
      },
      {
        title: "Camera stream support",
        description:
          "HLS, MJPEG, and snapshot paths with calibration, restreaming guidance, visible compatibility results, saved recommendations, per-camera defaults, and documented future provider hooks.",
        status: "complete",
      },
      {
        title: "Snapshot support",
        description:
          "Still-image popups for fast alerts and fallback previews while video loads.",
        status: "complete",
      },
      {
        title: "Remote receiver mode",
        description:
          "Outbound receiver transport for travel TVs without router port forwarding.",
        status: "complete",
      },
    ],
    featuresSection: {
      eyebrow: "Features",
      title: "Built in phases, designed as one experience.",
    },
    flow: {
      eyebrow: "How it works",
      steps: [
        "Home Assistant event",
        "HA TV PiP integration",
        "Android TV receiver app",
        "PiP camera popup",
      ],
      title: "A local-first path from event to PiP popup.",
    },
    footerAriaLabel: "Footer links",
    footerLinks: {
      architecture: "Architecture",
      development: "Development docs",
      github: "GitHub",
      license: "License",
      releases: "Releases",
      roadmap: "Roadmap",
      translations: "Translations",
    },
    hero: {
      alt: "Living room Android TV showing a security camera feed in Picture-in-Picture",
      ctaPrimary: "View on GitHub",
      ctaSecondary: "Read the Roadmap",
      overlayKicker: "Android TV receiver",
      overlayState: "PiP mode ready",
      overlayTitle: "Playing test HLS stream",
      signal: "Local automation path",
      subtitle:
        "HA TV PiP lets Home Assistant automations open security camera feeds, snapshots, and alerts in Picture-in-Picture on Android TV and Google TV devices.",
      title: "Show Home Assistant camera feeds on your Android TV.",
      versionLabel: "Version",
    },
    languageAriaLabel: "Language",
    problem: {
      body: "Home Assistant can detect doorbells, motion, people, and camera events, but showing those events naturally on a TV is still awkward.",
      eyebrow: "The problem",
      title: "Smart-home alerts deserve a better TV moment.",
    },
    roadmap: {
      eyebrow: "Roadmap preview",
      items: [
        "Local control endpoint",
        "mDNS discovery",
        "Device pairing",
        "Home Assistant service",
        "Snapshot support",
        "WebRTC support",
        "Remote mode",
        "Play Store and HACS distribution",
      ],
      title: "The path from MVP to daily-driver smart-home tool.",
    },
    solution: {
      eyebrow: "The solution",
      imageAlt:
        "Mockup showing Home Assistant controls connected to an Android TV PiP receiver",
      steps: [
        "Install the Android TV receiver app.",
        "Install the Home Assistant integration.",
        "Pair them locally.",
        "Trigger camera popups from automations.",
      ],
      title: "A receiver app for the TV, a controller in Home Assistant.",
    },
    statusLabels: {
      complete: "Complete",
      future: "Future",
      planned: "Planned",
    },
    theme: {
      ariaLabel: "Theme selector",
      auto: "auto",
      dark: "dark",
      light: "light",
    },
    translations: {
      eyebrow: "Translations",
      tiers: [
        {
          label: "Tier 1",
          status: "complete",
          languages:
            "English, German, Dutch, French, Spanish, Italian, Brazilian Portuguese, Polish",
        },
        {
          label: "Tier 2",
          status: "planned",
          languages:
            "Swedish, Norwegian, Danish, Finnish, Czech, Hungarian, Turkish, Japanese, Korean",
        },
        {
          label: "Tier 3",
          status: "planned",
          languages:
            "Simplified Chinese, Traditional Chinese, Indonesian, Hindi, Arabic, Ukrainian, Romanian, Greek",
        },
      ],
      title: "Internationalization is part of the product plan.",
    },
    visualAlt: {
      network:
        "Mockup showing a local smart-home network sending a camera feed to Android TV PiP",
      phase:
        "Promotional overview of HA TV PiP features beside an Android TV Picture-in-Picture mockup",
    },
    visualCards: [
      {
        title: "Automation control surface",
        text: "A Home Assistant-friendly control plane for future receiver discovery, pairing, and service calls.",
      },
      {
        title: "Local-first receiver path",
        text: "The TV app owns playback and PiP while Home Assistant decides what should appear.",
      },
    ],
  } satisfies WebsiteContent;

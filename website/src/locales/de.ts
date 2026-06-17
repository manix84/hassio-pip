import type { WebsiteContent } from "./types";

export const de = {
    codeBlock: {
      copyAriaLabel: "Home-Assistant-YAML in die Zwischenablage kopieren",
      copyFailed: "Kopieren fehlgeschlagen",
      copied: "Kopiert",
      copyTitle: "YAML kopieren",
      toolbar: "Home-Assistant-YAML",
    },
    currentStatus: {
      body: [
        "HA TV PiP unterstützt jetzt Erkennung, sichtbares Pairing auf dem Fernseher, authentifizierte Receiver-Steuerung, Kamerastream-Popups, Schnappschüsse, gestaltete Benachrichtigungen, Receiver-Verwaltung und Remote-Receiver-Transport.",
        "Der aktuelle Stage-12-Durchlauf härtet das Projekt für eine erste öffentliche Beta: vollständige Checks, Release-Pakete, HACS-Zip-Validierung, Website-Updates, Installationsdokumentation und Release-Candidate-Vorbereitung.",
      ],
      eyebrow: "Aktueller Stand",
      title: "Stage 12: Beta-Release-Härtung",
    },
    example: { eyebrow: "Beispiel-Automation", title: "Wohin es geht." },
    faqItems: [
      {
        question: "Ist HA TV PiP ein Cloud-Dienst?",
        answer:
          "Nein. Lokale Steuerung bleibt der Standard, und der Remote-Receiver-Modus verbindet den Fernseher ausgehend mit deiner eigenen externen Home-Assistant-URL. HA TV PiP betreibt keinen gehosteten Relay-Dienst.",
      },
      {
        question: "Muss ich Ports an meinem Router öffnen?",
        answer:
          "Nein, Portweiterleitung zum Fernseher ist nicht geplant. Im Remote-Receiver-Modus öffnet der Fernseher eine ausgehende WebSocket-Verbindung zu Home Assistant.",
      },
      {
        question: "Funktioniert das mit Nabu Casa?",
        answer:
          "Ja, die Home-Assistant-Cloud-URL kann als externe Home-Assistant-URL verwendet werden. Dadurch wird HA TV PiP selbst trotzdem kein Cloud-Dienst.",
      },
      {
        question: "Warum zeigen manche Kamerastreams Schnappschüsse oder Fehler?",
        answer:
          "Android-TV-Geräte können nicht unterstützte Codecs oder sehr hochauflösende Streams ablehnen. HA TV PiP unterstützt bereits Snapshot-Fallbacks und verbessert Stream-Auswahl und Kompatibilität weiter.",
      },
      {
        question: "Kann ich die Receiver-App vom TV-Startbildschirm ausblenden?",
        answer:
          "Ja. Die Home-Assistant-Integration bietet Hide Launcher- und Open Launcher-Steuerungen, damit sich die App nach der Einrichtung eher wie ein Gerät verhält.",
      },
      {
        question: "Wird HA TV PiP übersetzt?",
        answer:
          "Ja. Englisch ist die Ausgangssprache. Tier-1-Übersetzungen sind für Website, Android-App und Home-Assistant-Integration vorhanden; vor einer breiten Veröffentlichung ist noch native Prüfung nötig.",
      },
    ],
    faqSection: {
      eyebrow: "FAQ",
      title: "Antworten zu Einrichtungssorgen und früher Fehlersuche.",
    },
    features: [
      {
        title: "Android-TV-Receiver-App",
        description:
          "Eine Kotlin-Receiver-App, die Wiedergabe, PiP-Verhalten und TV-freundliche Bedienung übernimmt.",
        status: "complete",
      },
      {
        title: "Home-Assistant-Custom-Integration",
        description:
          "Eine Controller-Integration für Erkennung, Pairing, Dienste und Kameraauflösung.",
        status: "complete",
      },
      {
        title: "Lokale Steuerung zuerst",
        description: "LAN-Receiver-Steuerung ohne Cloud-Relay als Standard.",
        status: "complete",
      },
      {
        title: "Automatische Erkennung",
        description:
          "mDNS-Erkennung, damit Home Assistant Receiver-Apps automatisch finden kann.",
        status: "complete",
      },
      {
        title: "Sicheres Pairing",
        description:
          "Ein sichtbarer Pairing-Ablauf auf dem Fernseher verhindert, dass beliebige LAN-Geräte Kamera-Popups auslösen.",
        status: "complete",
      },
      {
        title: "Kamerastream-Unterstützung",
        description:
          "Home-Assistant-HLS-Kamerastreams mit Kompatibilitätsfeedback auf dem Receiver.",
        status: "complete",
      },
      {
        title: "Snapshot-Unterstützung",
        description:
          "Standbild-Popups für schnelle Warnungen und Fallback-Vorschauen, während Video lädt.",
        status: "complete",
      },
      {
        title: "Remote-Receiver-Modus",
        description:
          "Ausgehender Receiver-Transport für Reise-TVs ohne Router-Portweiterleitung.",
        status: "complete",
      },
    ],
    featuresSection: {
      eyebrow: "Funktionen",
      title: "In Phasen gebaut, als eine Erfahrung gedacht.",
    },
    flow: {
      eyebrow: "So funktioniert es",
      steps: [
        "Home-Assistant-Ereignis",
        "HA-TV-PiP-Integration",
        "Android-TV-Receiver-App",
        "PiP-Kamera-Popup",
      ],
      title: "Ein lokaler Weg vom Ereignis zum PiP-Popup.",
    },
    footerAriaLabel: "Footer-Links",
    footerLinks: {
      architecture: "Architektur",
      development: "Entwicklungsdokumente",
      github: "GitHub",
      license: "Lizenz",
      releases: "Releases",
      roadmap: "Roadmap",
      translations: "Übersetzungen",
    },
    hero: {
      alt: "Android TV im Wohnzimmer zeigt einen Sicherheitskamera-Feed in Picture-in-Picture",
      ctaPrimary: "Auf GitHub ansehen",
      ctaSecondary: "Roadmap lesen",
      overlayKicker: "Android-TV-Receiver",
      overlayState: "PiP-Modus bereit",
      overlayTitle: "Test-HLS-Stream läuft",
      signal: "Lokaler Automationspfad",
      subtitle:
        "HA TV PiP lässt Home-Assistant-Automationen Sicherheitskamera-Feeds, Schnappschüsse und Warnungen in Picture-in-Picture auf Android-TV- und Google-TV-Geräten öffnen.",
      title: "Zeige Home-Assistant-Kamera-Feeds auf deinem Android TV.",
      versionLabel: "Version",
    },
    languageAriaLabel: "Sprache",
    problem: {
      body: "Home Assistant kann Türklingeln, Bewegung, Personen und Kameraereignisse erkennen, aber diese Ereignisse natürlich auf einem Fernseher zu zeigen, ist noch umständlich.",
      eyebrow: "Das Problem",
      title: "Smart-Home-Warnungen verdienen einen besseren TV-Moment.",
    },
    roadmap: {
      eyebrow: "Roadmap-Vorschau",
      items: [
        "Lokaler Steuerungsendpunkt",
        "mDNS-Erkennung",
        "Geräte-Pairing",
        "Home-Assistant-Dienst",
        "Snapshot-Unterstützung",
        "WebRTC-Unterstützung",
        "Remote-Modus",
        "Play-Store- und HACS-Verteilung",
      ],
      title: "Der Weg vom MVP zum Smart-Home-Werkzeug für den Alltag.",
    },
    solution: {
      eyebrow: "Die Lösung",
      imageAlt:
        "Mockup von Home-Assistant-Steuerungen, die mit einem Android-TV-PiP-Receiver verbunden sind",
      steps: [
        "Installiere die Android-TV-Receiver-App.",
        "Installiere die Home-Assistant-Integration.",
        "Paare sie lokal.",
        "Löse Kamera-Popups aus Automationen aus.",
      ],
      title: "Eine Receiver-App für den Fernseher, ein Controller in Home Assistant.",
    },
    statusLabels: { complete: "Fertig", future: "Zukunft", planned: "Geplant" },
    theme: { ariaLabel: "Design-Auswahl", auto: "auto", dark: "dunkel", light: "hell" },
    translations: {
      eyebrow: "Übersetzungen",
      tiers: [
        { label: "Tier 1", status: "complete", languages: "Englisch, Deutsch, Niederländisch, Französisch, Spanisch, Italienisch, Brasilianisches Portugiesisch, Polnisch" },
        { label: "Tier 2", status: "planned", languages: "Schwedisch, Norwegisch, Dänisch, Finnisch, Tschechisch, Ungarisch, Türkisch, Japanisch, Koreanisch" },
        { label: "Tier 3", status: "planned", languages: "Vereinfachtes Chinesisch, Traditionelles Chinesisch, Indonesisch, Hindi, Arabisch, Ukrainisch, Rumänisch, Griechisch" },
      ],
      title: "Internationalisierung ist Teil des Produktplans.",
    },
    visualAlt: {
      network:
        "Mockup eines lokalen Smart-Home-Netzwerks, das einen Kamera-Feed an Android-TV-PiP sendet",
      phase:
        "Promotionsübersicht der HA-TV-PiP-Funktionen neben einem Android-TV-Picture-in-Picture-Mockup",
    },
    visualCards: [
      {
        title: "Automations-Steuerfläche",
        text: "Eine Home-Assistant-freundliche Steuerungsebene für künftige Receiver-Erkennung, Pairing und Dienstaufrufe.",
      },
      {
        title: "Lokaler Receiver-Pfad",
        text: "Die TV-App übernimmt Wiedergabe und PiP, während Home Assistant entscheidet, was erscheinen soll.",
      },
    ],
  } satisfies WebsiteContent;

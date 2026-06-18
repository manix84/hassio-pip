import { describe, expect, it } from "vitest";

import {
  faqItems,
  getInitialLocale,
  getLocaleHref,
  getLocaleFromPath,
  getPreferredLocale,
  supportedLocales,
  translationTiers,
  websiteContent,
} from "./App";

describe("App content", () => {
  it("explains that remote mode is not a hosted cloud service", () => {
    const cloudAnswer = faqItems.find((item) =>
      item.question.includes("cloud service")
    );

    expect(cloudAnswer?.answer).toContain("does not run a hosted relay");
  });

  it("answers the router port forwarding concern", () => {
    const portForwardingAnswer = faqItems.find((item) =>
      item.question.includes("ports")
    );

    expect(portForwardingAnswer?.answer).toContain("No port forwarding");
  });

  it("keeps the first translation tier focused on priority languages", () => {
    const tierOne = translationTiers.find((tier) => tier.label === "Tier 1");

    expect(tierOne?.languages).toContain("German");
    expect(tierOne?.languages).toContain("Dutch");
    expect(tierOne?.languages).toContain("Brazilian Portuguese");
    expect(tierOne?.languages).toContain("Polish");
  });

  it("describes the current status as post-v1.0 work", () => {
    expect(websiteContent.en.currentStatus.title).toContain("Post-v1.0");
    expect(websiteContent.en.currentStatus.body.join(" ")).toContain(
      "Post-1.0 compatibility work"
    );

    for (const locale of supportedLocales) {
      expect(websiteContent[locale.code].currentStatus.title).not.toContain(
        "Stage 12"
      );
    }
  });

  it("defines static routes for every tier one website locale", () => {
    expect(supportedLocales.map((locale) => locale.code)).toEqual([
      "en",
      "de",
      "nl",
      "fr",
      "es",
      "it",
      "pt-br",
      "pl",
    ]);
  });

  it("ships localized website content for every tier one locale", () => {
    const englishTitle = websiteContent.en.hero.title;

    for (const locale of supportedLocales) {
      const content = websiteContent[locale.code];

      expect(content.hero.title).toBeTruthy();
      expect(content.hero.ctaPrimary).toBeTruthy();
      expect(content.features).toHaveLength(8);
      expect(content.faqItems).toHaveLength(6);
      expect(content.roadmap.items).toHaveLength(8);
      expect(content.deviceSupport.items).toHaveLength(4);
      expect(content.translations.tiers).toHaveLength(3);
      expect(content.statusLabels.complete).toBeTruthy();

      if (locale.code !== "en") {
        expect(content.hero.title).not.toBe(englishTitle);
      }
    }
  });

  it("detects locale route prefixes and falls back to English", () => {
    expect(getLocaleFromPath("/de/")).toBe("de");
    expect(getLocaleFromPath("/ha-tv-pip/de/")).toBe("de");
    expect(getLocaleFromPath("/pt-br/releases")).toBe("pt-br");
    expect(getLocaleFromPath("/unknown/")).toBe("en");
  });

  it("builds locale links for root and GitHub Pages paths", () => {
    expect(getLocaleHref("/ha-tv-pip/", "de")).toBe("./de/");
    expect(getLocaleHref("/ha-tv-pip/de/", "fr")).toBe("/ha-tv-pip/fr/");
    expect(getLocaleHref("/ha-tv-pip/de/", "en")).toBe("/ha-tv-pip/");
    expect(getLocaleHref("/de/", "en")).toBe("/");
  });

  it("uses saved language before browser detection", () => {
    expect(getPreferredLocale(["fr-FR", "en-GB"], "pl")).toBe("pl");
  });

  it("detects supported browser languages", () => {
    expect(getPreferredLocale(["de-DE", "en-GB"])).toBe("de");
    expect(getPreferredLocale(["pt-PT", "en-GB"])).toBe("pt-br");
    expect(getPreferredLocale(["cy-GB"])).toBe("en");
  });

  it("uses URL locale before saved or browser preferences", () => {
    expect(getInitialLocale("/ha-tv-pip/fr/", ["de-DE"], null)).toBe("fr");
  });

  it("uses saved language override before URL locale", () => {
    expect(getInitialLocale("/ha-tv-pip/fr/", ["de-DE"], "pl")).toBe("pl");
    expect(getInitialLocale("/ha-tv-pip/de/", ["de-DE"], "en")).toBe("en");
  });
});

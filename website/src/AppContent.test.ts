import { describe, expect, it } from "vitest";

import { faqItems, translationTiers } from "./App";

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
});

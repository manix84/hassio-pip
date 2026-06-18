import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { FaqDisclosure, websiteContent } from "./App";
import { CodeBlock } from "./components/CodeBlock";
import { ThemeToggle } from "./components/ThemeToggle";

describe("website accessibility", () => {
  it("renders FAQ items as labelled disclosure controls", () => {
    const item = {
      answer: "No port forwarding is required.",
      question: "Do I need to open ports on my router?",
    };
    const markup = renderToStaticMarkup(<FaqDisclosure item={item} />);
    const controls = markup.match(/aria-controls="([^"]+)"/)?.[1];
    const panel = markup.match(/id="([^"]+)"/)?.[1];

    expect(markup).toContain("<button");
    expect(markup).toContain('type="button"');
    expect(markup).toContain('aria-expanded="false"');
    expect(markup).toContain('aria-hidden="true"');
    expect(controls).toBeTruthy();
    expect(panel).toBe(controls);
  });

  it("renders the theme selector as a labelled button group", () => {
    const markup = renderToStaticMarkup(
      <ThemeToggle labels={websiteContent.en.theme} mode="auto" onChange={() => {}} />
    );

    expect(markup).toContain('role="group"');
    expect(markup).toContain(`aria-label="${websiteContent.en.theme.ariaLabel}"`);
    expect(markup.match(/aria-pressed=/g)).toHaveLength(3);
    expect(markup).toContain('aria-pressed="true"');
  });

  it("renders copy feedback as an aria-live region", () => {
    const markup = renderToStaticMarkup(
      <CodeBlock
        code="action: ha_tv_pip.show_camera"
        labels={websiteContent.en.codeBlock}
        language="home-assistant-yaml"
      />
    );

    expect(markup).toContain(
      `aria-label="${websiteContent.en.codeBlock.copyAriaLabel}"`
    );
    expect(markup).toContain('aria-live="polite"');
  });

  it("keeps primary image alt text available in every locale", () => {
    for (const [locale, content] of Object.entries(websiteContent)) {
      expect(content.hero.alt, locale).toBeTruthy();
      expect(content.solution.imageAlt, locale).toBeTruthy();
      expect(content.visualAlt.network, locale).toBeTruthy();
      expect(content.visualAlt.phase, locale).toBeTruthy();
    }
  });
});

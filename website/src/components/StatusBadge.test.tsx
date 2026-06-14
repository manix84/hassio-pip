import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { StatusBadge } from "./StatusBadge";

describe("StatusBadge", () => {
  it("renders the Phase 1 label", () => {
    const markup = renderToStaticMarkup(<StatusBadge status="phase1" />);

    expect(markup).toContain("Phase 1");
  });

  it("renders future status copy", () => {
    const markup = renderToStaticMarkup(<StatusBadge status="future" />);

    expect(markup).toContain("Future");
  });
});

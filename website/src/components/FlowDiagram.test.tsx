import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { FlowDiagram } from "./FlowDiagram";

describe("FlowDiagram", () => {
  it("renders each flow step in order", () => {
    const markup = renderToStaticMarkup(
      <FlowDiagram steps={["Home Assistant event", "Receiver app", "PiP popup"]} />
    );

    expect(markup.indexOf("Home Assistant event")).toBeLessThan(markup.indexOf("Receiver app"));
    expect(markup.indexOf("Receiver app")).toBeLessThan(markup.indexOf("PiP popup"));
  });
});

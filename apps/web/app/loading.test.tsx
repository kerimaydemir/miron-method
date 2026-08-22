import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import Loading from "./loading";

describe("Loading", () => {
  it("exposes a named status to assistive technology", () => {
    render(<Loading />);

    expect(
      screen.getByRole("status", { name: "Yükleniyor" }),
    ).toBeInTheDocument();
  });
});

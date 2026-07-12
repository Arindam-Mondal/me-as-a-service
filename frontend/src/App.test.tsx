import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import App from "./App";
import { profile } from "./content/profile";

describe("App", () => {
  it("mounts the profile + chat shell with starter questions", () => {
    render(<App />);
    expect(screen.getByRole("heading", { name: profile.name, level: 1 })).toBeInTheDocument();
    expect(screen.getByLabelText(/ask a question/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: profile.starters[0] })).toBeInTheDocument();
  });

  it("opens the connect dialog from the CTA", async () => {
    render(<App />);
    await userEvent.click(screen.getByRole("button", { name: /connect with me/i }));
    expect(screen.getByRole("heading", { name: /let's connect/i })).toBeInTheDocument();
  });
});

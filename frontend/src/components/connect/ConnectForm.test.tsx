import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ConnectForm } from "./ConnectForm";
import { postLead } from "../../lib/postLead";

vi.mock("../../lib/postLead", () => ({ postLead: vi.fn() }));
const postLeadMock = vi.mocked(postLead);

// NOTE: no beforeEach mock reset/clear — each test sets its own resolve/reject
// implementation. `mockReset()` here interacts with `mockRejectedValue` to trip a
// vitest unhandled-rejection false positive (the component's catch is verified to work).

async function fillAndSubmit() {
  await userEvent.type(screen.getByLabelText("Name"), "Jane");
  await userEvent.type(screen.getByLabelText("Email"), "jane@example.com");
  await userEvent.click(screen.getByRole("button", { name: /send it/i }));
  // Let the async submit settle before assertions run.
  await new Promise((r) => setTimeout(r, 50));
}

describe("ConnectForm submit", () => {
  it("posts the lead and shows the success state", async () => {
    postLeadMock.mockResolvedValue({ ok: true, id: 1 });
    render(<ConnectForm open onClose={() => {}} />);

    await fillAndSubmit();

    expect(postLeadMock).toHaveBeenCalledWith({ name: "Jane", email: "jane@example.com" });
    expect(await screen.findByRole("heading", { name: /thanks/i })).toBeInTheDocument();
  });

  it("shows an inline error and keeps the form open when the post fails", async () => {
    postLeadMock.mockRejectedValue(new Error("boom"));
    render(<ConnectForm open onClose={() => {}} />);

    await fillAndSubmit();

    expect(await screen.findByRole("alert")).toHaveTextContent(/try again/i);
    // form still present (not the success state)
    expect(screen.getByRole("button", { name: /send it/i })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: /thanks/i })).not.toBeInTheDocument();
  });
});

import { useEffect, useRef, useState } from "react";
import { Sparkle } from "../doodles";
import { postLead } from "../../lib/postLead";

type Props = {
  open: boolean;
  onClose: () => void;
};

const emailOk = (v: string) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v);

/** Native <dialog> connect form. Validates client-side, then POSTs to /api/leads. */
export function ConnectForm({ open, onClose }: Props) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [note, setNote] = useState("");
  const [errors, setErrors] = useState<{ name?: string; email?: string }>({});
  const [submitting, setSubmitting] = useState(false);
  const [sendError, setSendError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  useEffect(() => {
    const dlg = dialogRef.current;
    if (!dlg) return;
    if (open && !dlg.open) dlg.showModal();
    if (!open && dlg.open) dlg.close();
  }, [open]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    const next: typeof errors = {};
    if (!name.trim()) next.name = "Please add your name.";
    if (!emailOk(email)) next.email = "Please enter a valid email.";
    setErrors(next);
    if (Object.keys(next).length) return;

    setSendError(null);
    setSubmitting(true);
    try {
      await postLead({ name: name.trim(), email: email.trim(), message: note.trim() || undefined });
      setDone(true);
    } catch {
      setSendError("Couldn't send that — please try again in a moment.");
    } finally {
      setSubmitting(false);
    }
  };

  const close = () => {
    setDone(false);
    setErrors({});
    setSendError(null);
    setSubmitting(false);
    onClose();
  };

  return (
    <dialog
      ref={dialogRef}
      className="dialog"
      onClose={close}
      onClick={(e) => {
        if (e.target === dialogRef.current) close(); // click on backdrop closes
      }}
      aria-labelledby="connect-title"
    >
      <div className="dialog__body">
        {done ? (
          <>
            <h2 className="dialog__title" id="connect-title">
              <Sparkle
                width={24}
                height={24}
                style={{ color: "var(--accent)", display: "inline-block", verticalAlign: "-3px" }}
              />{" "}
              Thanks!
            </h2>
            <p>Your details are on their way — Arindam will follow up personally.</p>
            <div className="dialog__actions" style={{ justifyContent: "flex-end" }}>
              <button type="button" className="btn" onClick={close}>
                Done
              </button>
            </div>
          </>
        ) : (
          <form onSubmit={submit} noValidate>
            <h2 className="dialog__title" id="connect-title">
              Let's connect
            </h2>
            <p style={{ color: "var(--ink-soft)", marginTop: "var(--s-2)" }}>
              Leave your details and Arindam will get back to you.
            </p>

            <div className="field" style={{ marginTop: "var(--s-4)" }}>
              <label htmlFor="cf-name">Name</label>
              <input
                id="cf-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                autoComplete="name"
                aria-invalid={Boolean(errors.name)}
              />
              {errors.name && <span className="field__err">{errors.name}</span>}
            </div>

            <div className="field" style={{ marginTop: "var(--s-3)" }}>
              <label htmlFor="cf-email">Email</label>
              <input
                id="cf-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
                aria-invalid={Boolean(errors.email)}
              />
              {errors.email && <span className="field__err">{errors.email}</span>}
            </div>

            <div className="field" style={{ marginTop: "var(--s-3)" }}>
              <label htmlFor="cf-note">Note (optional)</label>
              <input
                id="cf-note"
                value={note}
                onChange={(e) => setNote(e.target.value)}
                placeholder="What's this about?"
              />
            </div>

            {sendError && (
              <p className="field__err" role="alert" style={{ marginTop: "var(--s-3)" }}>
                {sendError}
              </p>
            )}

            <div className="dialog__actions">
              <button
                type="button"
                className="btn btn--ghost"
                onClick={close}
                disabled={submitting}
              >
                Cancel
              </button>
              <button type="submit" className="btn" disabled={submitting}>
                {submitting ? "Sending…" : "Send it"}
              </button>
            </div>
          </form>
        )}
      </div>
    </dialog>
  );
}

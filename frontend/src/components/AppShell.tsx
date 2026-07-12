import type { ReactNode } from "react";

/** Paper background + centered page-frame that makes the app feel like a physical booklet. */
export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="shell">
      <div className="page">
        <div className="spread">{children}</div>
      </div>
    </div>
  );
}

import { useState } from "react";
import { AppShell } from "./components/AppShell";
import { ProfilePanel } from "./components/profile/ProfilePanel";
import { ChatPanel } from "./components/chat/ChatPanel";
import { ConnectForm } from "./components/connect/ConnectForm";

export default function App() {
  const [connectOpen, setConnectOpen] = useState(false);

  return (
    <>
      <AppShell>
        <ProfilePanel onConnect={() => setConnectOpen(true)} />
        <ChatPanel />
      </AppShell>
      <ConnectForm open={connectOpen} onClose={() => setConnectOpen(false)} />
    </>
  );
}

import { MessageList } from "./MessageList";
import { Composer } from "./Composer";
import { LimitNotice } from "../system/LimitNotice";
import { RefreshDoodle } from "../doodles";
import { useChatStream } from "../../lib/useChatStream";

/** Owns chat state; wires the stream hook to the transcript + composer. */
export function ChatPanel() {
  const { messages, status, send, reset } = useChatStream();

  return (
    <section className="chat" aria-label="Chat with Arindam's AI twin">
      <div className="chat__header">
        <h2 className="chat__title">Ask me anything</h2>
        {messages.length > 0 && (
          <button
            type="button"
            className="btn chat__reset"
            onClick={reset}
            aria-label="Start over"
            title="Start over"
          >
            <RefreshDoodle width={20} height={20} style={{ color: "var(--on-accent)" }} />
          </button>
        )}
      </div>

      <MessageList messages={messages} status={status} onPick={send} />

      {status === "limited" && <LimitNotice />}
      <Composer status={status} onSend={send} />
    </section>
  );
}

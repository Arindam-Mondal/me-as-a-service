import { useEffect, useRef } from "react";
import { Message } from "./Message";
import { StarterQuestions } from "./StarterQuestions";
import type { ChatStatus, Message as Msg } from "../../lib/useChatStream";

type Props = {
  messages: Msg[];
  status: ChatStatus;
  onPick: (q: string) => void;
};

/** Scrollable transcript with auto-scroll, empty state, and the "thinking" indicator. */
export function MessageList({ messages, status, onPick }: Props) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ block: "end" });
  }, [messages, status]);

  return (
    <div className="messages" aria-live="polite" aria-busy={status === "streaming"}>
      {messages.length === 0 && status === "idle" ? (
        <StarterQuestions onPick={onPick} />
      ) : (
        messages.map((m) => <Message key={m.id} msg={m} />)
      )}

      {status === "thinking" && (
        <div className="thinking">
          <span>thinking</span>
          <span className="thinking__dots" aria-hidden>
            <span>.</span>
            <span>.</span>
            <span>.</span>
          </span>
        </div>
      )}
      <div ref={endRef} />
    </div>
  );
}

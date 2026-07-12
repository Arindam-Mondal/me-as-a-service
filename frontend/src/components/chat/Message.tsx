import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { BubbleMark } from "../doodles";
import type { Message as Msg } from "../../lib/useChatStream";

/** One chat bubble. Assistant messages render sanitized markdown; user messages are plain. */
export function Message({ msg }: { msg: Msg }) {
  const isUser = msg.role === "user";
  const cls = ["msg", isUser ? "msg--user" : "msg--assistant", msg.error ? "msg--error" : ""]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={cls}>
      {!isUser && (
        <span className="msg__mark" aria-hidden>
          <BubbleMark width={28} height={28} />
        </span>
      )}
      <div className="msg__bubble">
        {isUser ? (
          <div className="md">{msg.content}</div>
        ) : (
          <div className="md">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
            {msg.streaming && <span className="caret" aria-hidden />}
          </div>
        )}
      </div>
    </div>
  );
}

import { useCallback, useRef, useState } from "react";
import { streamChat, type HistoryMsg } from "./streamChat";

export type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  streaming?: boolean;
  error?: boolean;
};

export type ChatStatus = "idle" | "thinking" | "streaming" | "error" | "limited";

const uid = () =>
  typeof crypto !== "undefined" && "randomUUID" in crypto
    ? crypto.randomUUID()
    : Math.random().toString(36).slice(2);

export function useChatStream() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [status, setStatus] = useState<ChatStatus>("idle");
  const abortRef = useRef<AbortController | null>(null);

  const patch = useCallback((id: string, fn: (m: Message) => Message) => {
    setMessages((prev) => prev.map((m) => (m.id === id ? fn(m) : m)));
  }, []);

  const send = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || status === "thinking" || status === "streaming") return;

      const history: HistoryMsg[] = messages
        .filter((m) => !m.error)
        .map((m) => ({ role: m.role, content: m.content }));

      const userMsg: Message = { id: uid(), role: "user", content: trimmed };
      const botId = uid();
      setMessages((prev) => [
        ...prev,
        userMsg,
        { id: botId, role: "assistant", content: "", streaming: true },
      ]);
      setStatus("thinking");

      const ctrl = new AbortController();
      abortRef.current = ctrl;

      try {
        let gotToken = false;
        for await (const ev of streamChat(trimmed, history, ctrl.signal)) {
          if (ev.event === "token") {
            gotToken = true;
            setStatus("streaming");
            const delta = (ev.data as { text: string }).text ?? "";
            patch(botId, (m) => ({ ...m, content: m.content + delta }));
          } else if (ev.event === "error") {
            const msg = (ev.data as { message: string }).message ?? "Something went wrong.";
            patch(botId, (m) => ({ ...m, content: msg, streaming: false, error: true }));
            setStatus("error");
            return;
          } else if (ev.event === "limit") {
            setMessages((prev) => prev.filter((m) => m.id !== botId));
            setStatus("limited");
            return;
          } else if (ev.event === "done") {
            break;
          }
        }
        patch(botId, (m) => ({
          ...m,
          streaming: false,
          error: !gotToken && m.content === "" ? true : m.error,
          content: !gotToken && m.content === "" ? "No response received." : m.content,
        }));
        setStatus("idle");
      } catch (err) {
        if ((err as Error).name === "AbortError") {
          patch(botId, (m) => ({ ...m, streaming: false }));
          setStatus("idle");
          return;
        }
        patch(botId, (m) => ({
          ...m,
          content: "I couldn't reach the server. Please try again.",
          streaming: false,
          error: true,
        }));
        setStatus("error");
      } finally {
        abortRef.current = null;
      }
    },
    [messages, status, patch],
  );

  const stop = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  const reset = useCallback(() => {
    abortRef.current?.abort();
    setMessages([]);
    setStatus("idle");
  }, []);

  return { messages, status, send, stop, reset };
}

import { useState } from "react";

import { queryAssistant } from "../../lib/api/chatApi";
import type { ChatContextTurn } from "../../lib/api/types";
import { useDashboardStore } from "../../lib/state/dashboardStore";
import { Button, Surface, TextAreaField } from "../../ui";

interface Message {
  role: "user" | "assistant";
  content: string;
  preview?: Array<Record<string, unknown>> | null;
}

const quickPrompts = [
  "今天市场是风险偏好抬升还是收缩？",
  "看看涨跌幅最强的股票。",
  "北向资金最近 5 天怎么走？",
];

export const ChatConsole = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "直接问我市场概况、北向资金、排行榜或个股线索，我会把答案整理成可追问的 desk note。",
    },
  ]);
  const [draft, setDraft] = useState("");
  const [loading, setLoading] = useState(false);
  const setActiveStock = useDashboardStore((state) => state.setActiveStock);

  const handleSend = async (nextDraft?: string) => {
    const message = (nextDraft ?? draft).trim();
    if (!message || loading) {
      return;
    }

    const nextMessages = [...messages, { role: "user" as const, content: message }];
    setMessages(nextMessages);
    setDraft("");
    setLoading(true);

    try {
      const response = await queryAssistant(
        message,
        nextMessages.map<ChatContextTurn>((item) => ({
          role: item.role,
          content: item.content,
        })),
      );

      setMessages([
        ...nextMessages,
        {
          role: "assistant",
          content: response.reply,
          preview: response.data ?? null,
        },
      ]);
    } catch (error) {
      setMessages([
        ...nextMessages,
        {
          role: "assistant",
          content: error instanceof Error ? error.message : "助手暂时不可用，请稍后再试。",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Surface className="chat-console" data-testid="assistant-console">
      <span className="section-kicker">Desk Intercom</span>
      <h2 className="chat-console__title">Analyst Copilot</h2>
      <p className="chat-console__summary">用自然语言追问盘面，助手会把回答压缩成能继续钻取的线索。</p>
      <div className="chat-console__prompts">
        {quickPrompts.map((prompt) => (
          <button key={prompt} type="button" className="chat-console__prompt" onClick={() => void handleSend(prompt)}>
            {prompt}
          </button>
        ))}
      </div>
      <div className="chat-console__messages">
        {messages.map((message, index) => (
          <div key={`${message.role}-${index}`} className={`chat-message chat-message--${message.role}`}>
            <strong className="chat-message__author">{message.role === "assistant" ? "AI" : "你"}</strong>
            <p className="chat-message__content">{message.content}</p>
            {message.preview?.length ? (
              <div className="chat-message__preview">
                {message.preview.slice(0, 4).map((row, rowIndex) => (
                  <div key={rowIndex} className="chat-preview-row">
                    <span>{String(row.name ?? row.ts_code ?? `结果 ${rowIndex + 1}`)}</span>
                    {typeof row.ts_code === "string" ? (
                      <Button size="sm" onClick={() => setActiveStock(row.ts_code as string)}>
                        查看
                      </Button>
                    ) : null}
                  </div>
                ))}
              </div>
            ) : null}
          </div>
        ))}
      </div>
      <TextAreaField
        value={draft}
        rows={4}
        placeholder="问我今天市场发生了什么，或者要哪类股票。"
        onChange={setDraft}
        onKeyDown={(event) => {
          if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            void handleSend();
          }
        }}
      />
      <div className="chat-console__actions">
        <Button loading={loading} onClick={() => void handleSend()}>
          发送
        </Button>
      </div>
    </Surface>
  );
};

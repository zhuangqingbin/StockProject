import { request } from "./httpClient";
import type { ChatContextTurn, ChatResponse } from "./types";

export const queryAssistant = (message: string, context: ChatContextTurn[] = []) => {
  return request<ChatResponse>("/api/chat/query", {
    method: "POST",
    body: {
      message,
      context: context.map((item) => ({
        role: item.role,
        content: item.content,
      })),
    },
  });
};

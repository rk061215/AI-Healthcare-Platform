import { apiClient } from "./api-client";
import type { ChatMessage, ChatResponse } from "@/types";

export const chatService = {
  async sendMessage(message: string): Promise<ChatResponse> {
    const response = await apiClient.post("/chat/message", { message });
    return response.data;
  },

  async getHistory(): Promise<ChatMessage[]> {
    const response = await apiClient.get("/chat/history");
    return response.data;
  },

  async clearHistory(): Promise<void> {
    await apiClient.delete("/chat/history");
  },
};

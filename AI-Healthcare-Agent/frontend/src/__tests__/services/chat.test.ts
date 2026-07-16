import { describe, it, expect, vi, beforeEach } from "vitest";
import type { Mock } from "vitest";

vi.mock("@/services/api-client", () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}));

import { apiClient } from "@/services/api-client";
import { chatService } from "@/services/chat";
import type { ChatMessage, ChatResponse } from "@/types";

const mockChatResponse: ChatResponse = {
  reply: "Test reply",
  sources: null,
  suggested_questions: ["What is this?"],
  metadata: null,
};

const mockChatHistory: ChatMessage[] = [
  {
    id: "1",
    role: "user",
    message: "Hello",
    metadata: null,
    created_at: "2024-01-01T00:00:00Z",
  },
  {
    id: "2",
    role: "assistant",
    message: "Hi there",
    metadata: null,
    created_at: "2024-01-01T00:01:00Z",
  },
];

describe("chatService", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("sendMessage should POST to /chat/message", async () => {
    (apiClient.post as Mock).mockResolvedValueOnce({ data: mockChatResponse });
    const result = await chatService.sendMessage("Hello");
    expect(apiClient.post).toHaveBeenCalledWith("/chat/message", {
      message: "Hello",
    });
    expect(result).toEqual(mockChatResponse);
  });

  it("getHistory should GET /chat/history", async () => {
    (apiClient.get as Mock).mockResolvedValueOnce({ data: mockChatHistory });
    const result = await chatService.getHistory();
    expect(apiClient.get).toHaveBeenCalledWith("/chat/history");
    expect(result).toEqual(mockChatHistory);
  });

  it("clearHistory should DELETE /chat/history", async () => {
    (apiClient.delete as Mock).mockResolvedValueOnce({});
    await chatService.clearHistory();
    expect(apiClient.delete).toHaveBeenCalledWith("/chat/history");
  });
});

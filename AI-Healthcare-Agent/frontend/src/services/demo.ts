import { apiClient } from "./api-client";

export const demoService = {
  upload: async (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return apiClient.post("/demo/upload", form);
  },
  ask: async (data: {
    question: string;
    report_id?: string;
    report_text?: string;
    conversation_history?: string;
  }) => {
    const params = new URLSearchParams();
    params.append("question", data.question);
    if (data.report_id) params.append("report_id", data.report_id);
    if (data.report_text) params.append("report_text", data.report_text);
    if (data.conversation_history)
      params.append("conversation_history", data.conversation_history);
    return apiClient.post("/demo/ask", params, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
  },
  getScenarios: async () => {
    return apiClient.get("/demo/scenarios");
  },
  reset: async () => {
    return apiClient.post("/demo/reset");
  },
};

export type AgentEventType =
  | "agent_start"
  | "tool_call"
  | "tool_result"
  | "agent_complete"
  | "report_chunk"
  | "error"
  | "done";

export interface AgentEvent {
  type: AgentEventType;
  data: Record<string, unknown>;
  id: string;
  receivedAt: number;
}

interface StreamCallbacks {
  onAgentEvent: (event: AgentEvent) => void;
  onReportChunk: (chunk: string) => void;
  onComplete: () => void;
  onError: (err: Error) => void;
}

export function openResearchStream(
  topic: string,
  callbacks: StreamCallbacks
): () => void {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";
  let closed = false;
  let eventId = 0;

  const controller = new AbortController();

  fetch(`${apiUrl}/api/research`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ topic }),
    signal: controller.signal,
  })
    .then(async (res) => {
      if (!res.ok || !res.body) {
        throw new Error(`HTTP ${res.status}`);
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (!closed) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split("\n\n");
        buffer = parts.pop() ?? "";

        for (const part of parts) {
          if (!part.trim()) continue;

          let eventType: AgentEventType = "agent_start";
          let dataStr = "";

          for (const line of part.split("\n")) {
            if (line.startsWith("event:")) {
              eventType = line.slice(6).trim() as AgentEventType;
            } else if (line.startsWith("data:")) {
              dataStr = line.slice(5).trim();
            }
          }

          if (!dataStr) continue;

          try {
            const data = JSON.parse(dataStr);
            const receivedAt = Date.now();

            if (eventType === "report_chunk") {
              callbacks.onReportChunk(data.chunk ?? "");
            } else if (eventType === "done") {
              callbacks.onComplete();
            } else if (eventType === "error") {
              callbacks.onError(new Error(data.message ?? "Unknown error"));
            } else {
              callbacks.onAgentEvent({
                type: eventType,
                data,
                id: String(eventId++),
                receivedAt,
              });
            }
          } catch {
            // skip malformed events
          }
        }
      }
    })
    .catch((err) => {
      if (!closed) callbacks.onError(err);
    });

  return () => {
    closed = true;
    controller.abort();
  };
}

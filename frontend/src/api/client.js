const BASE = "/api";

async function request(path, options) {
  const res = await fetch(`${BASE}${path}`, options);
  if (!res.ok) throw new Error(`${options?.method ?? "GET"} ${path} failed with ${res.status}`);
  return res.status === 204 ? null : res.json();
}

function post(path, body) {
  return request(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export function createConversation(title) {
  return post("/conversations", { title });
}

export function listConversations() {
  return request("/conversations");
}

export function getConversation(id) {
  return request(`/conversations/${id}`);
}

export function sendMessage(conversationId, content) {
  return post(`/conversations/${conversationId}/messages`, { content });
}

export async function* streamMessage(conversationId, content) {
  const res = await fetch(`${BASE}/conversations/${conversationId}/messages/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
  });
  if (!res.ok) throw new Error(`POST /conversations/${conversationId}/messages/stream failed with ${res.status}`);
  if (!res.body) throw new Error("Streaming response has no body");

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      buffer += decoder.decode(value ?? new Uint8Array(), { stream: !done });
      const lines = buffer.split("\n");
      buffer = lines.pop() ?? "";
      for (const line of lines) {
        if (line.trim()) yield JSON.parse(line);
      }
      if (done) break;
    }
    if (buffer.trim()) yield JSON.parse(buffer);
  } finally {
    reader.releaseLock();
  }
}

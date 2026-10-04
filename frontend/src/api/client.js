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

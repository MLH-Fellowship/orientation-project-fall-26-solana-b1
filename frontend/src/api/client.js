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

function patch(path, body) {
  return request(path, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export function createConversation(title) {
  return post("/conversations", title ? { title } : {});
}

export function listConversations({ limit = 100, offset = 0 } = {}) {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  return request(`/conversations?${params}`);
}

export function getConversation(id) {
  return request(`/conversations/${id}`);
}

export function renameConversation(id, title) {
  return patch(`/conversations/${id}`, { title });
}

export function deleteConversation(id) {
  return request(`/conversations/${id}`, { method: "DELETE" });
}

export function sendMessage(conversationId, content) {
  return post(`/conversations/${conversationId}/messages`, { content });
}

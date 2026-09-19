// Thin wrapper around fetch for talking to the FastAPI backend.
// Extend this as new endpoints are added (pagination, rename, delete...).

const BASE = "/api";

export async function createConversation(title) {
  const res = await fetch(`${BASE}/conversations`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
  });
  return res.json();
}

export async function listConversations() {
  const res = await fetch(`${BASE}/conversations`);
  return res.json();
}

export async function getConversation(id) {
  const res = await fetch(`${BASE}/conversations/${id}`);
  return res.json();
}

export async function sendMessage(conversationId, content) {
  const res = await fetch(`${BASE}/conversations/${conversationId}/messages`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
  });
  return res.json();
}

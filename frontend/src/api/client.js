const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function req(method, path, body) {
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export const api = {
  summariseText: (text, title) =>
    req("POST", "/summarise", { text, title, source_type: "text" }),

  summariseUrl: (url) =>
    req("POST", "/summarise/url", { url }),

  summariseFile: async (file) => {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${BASE}/summarise/file`, { method: "POST", body: form });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return res.json();
  },

  listDocuments: () => req("GET", "/documents"),
  getDocument: (id) => req("GET", `/documents/${id}`),
  deleteDocument: (id) => req("DELETE", `/documents/${id}`),
  getStats: () => req("GET", "/stats"),
};

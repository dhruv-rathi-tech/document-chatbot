const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";


export async function uploadDocuments(files, sessionId) {
  const formData = new FormData();
  for (const file of files) {
    formData.append("files", file);
  }
  if (sessionId) {
    formData.append("session_id", sessionId);
  }

  const response = await fetch(`${API_URL}/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const errorBody = await safeJson(response);
    throw new Error(errorBody?.detail || `Upload failed (${response.status})`);
  }

  return response.json();
}


export async function sendChatMessage(sessionId, query) {
  const response = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, query }),
  });

  if (!response.ok) {
    const errorBody = await safeJson(response);
    throw new Error(errorBody?.detail || `Chat request failed (${response.status})`);
  }

  return response.json();
}


export async function clearSession(sessionId) {
  if (!sessionId) return;
  try {
    await fetch(`${API_URL}/session/${sessionId}`, { method: "DELETE" });
  } catch {
    // Ignore failures (e.g. user closing tab)
  }
}

async function safeJson(response) {
  try {
    return await response.json();
  } catch {
    return null;
  }
}



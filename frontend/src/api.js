const rawUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
const API_URL = rawUrl.replace(/\/+$/, "");

async function fetchWithNetworkCheck(url, options = {}) {
  try {
    return await fetch(url, options);
  } catch (error) {
    if (error instanceof TypeError || error.name === "TypeError" || error.message?.includes("fetch")) {
      throw new Error(
        `Cannot connect to backend server (${API_URL}). If using Render free tier, the server may be waking up from sleep. Please wait a few seconds and try again.`
      );
    }
    throw error;
  }
}

export async function uploadDocuments(files, sessionId) {
  const formData = new FormData();
  for (const file of files) {
    formData.append("files", file);
  }
  if (sessionId) {
    formData.append("session_id", sessionId);
  }

  const response = await fetchWithNetworkCheck(`${API_URL}/upload`, {
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
  const response = await fetchWithNetworkCheck(`${API_URL}/chat`, {
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


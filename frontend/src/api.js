const API_BASE_URL = import.meta.env.VITE_API_BASE_URL
  || "http://localhost:8000";

const TOKEN_STORAGE_KEY = "incident-copilot-access-token";

export function getAccessToken() {
  return sessionStorage.getItem(TOKEN_STORAGE_KEY);
}

export function saveAccessToken(token) {
  sessionStorage.setItem(TOKEN_STORAGE_KEY, token);
}

export function clearAccessToken() {
  sessionStorage.removeItem(TOKEN_STORAGE_KEY);
}

async function request(path, options = {}) {
  const headers = new Headers(options.headers);
  const token = getAccessToken();

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(
    `${API_BASE_URL}${path}`,
    {
      ...options,
      headers,
    },
  );

  if (!response.ok) {
    let message = "Something went wrong.";

    try {
      const body = await response.json();
      message = body.detail || message;
    } catch {
      // Keep the default message when the API has no JSON body.
    }

    throw new Error(message);
  }

  return response.json();
}

export function registerUser(data) {
  return request("/auth/register", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });
}

export async function loginUser(data) {
  const loginResult = await request("/auth/login", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });

  saveAccessToken(loginResult.access_token);

  return loginResult;
}

export function getCurrentUser() {
  return request("/auth/me");
}

export function createIncident(data) {
  return request("/incidents", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });
}

export function getIncidents() {
  return request("/incidents?limit=100");
}

export function getSimilarIncidents(incidentId) {
  return request(`/incidents/${incidentId}/similar`);
}

export function getCorrelationTimeline(incidentId) {
  return request(
    `/incidents/${incidentId}/correlation-timeline`,
  );
}

export function getRecommendations(incidentId) {
  return request(`/incidents/${incidentId}/recommendations`);
}

export function resolveIncident(incidentId, data) {
  return request(`/incidents/${incidentId}/resolve`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });
}
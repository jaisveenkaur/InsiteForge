import { CONFIG } from "./config.js";

export async function fetchHealth(baseUrl) {
  const response = await fetch(`${baseUrl}/health`);
  if (!response.ok) {
    throw new Error("Health check failed");
  }
  return response.json();
}

export async function fetchAuthStatus(baseUrl) {
  const response = await fetch(`${baseUrl}/auth-status`);
  if (!response.ok) {
    throw new Error("Auth status check failed");
  }
  return response.json();
}

export async function runAnalysis(payload, apiKey, baseUrlOverride) {
  const baseUrl = baseUrlOverride || CONFIG.API_BASE_URL;
  const headers = { "Content-Type": "application/json" };
  if (apiKey) {
    headers["x-api-key"] = apiKey;
  }

  const response = await fetch(`${baseUrl}/analyze`, {
    method: "POST",
    headers,
    body: JSON.stringify(payload),
  });

  let data = {};
  try {
    data = await response.json();
  } catch {
    data = {};
  }

  if (!response.ok) {
    throw new Error(data.detail || "Analysis failed");
  }

  return data;
}

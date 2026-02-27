import { CONFIG } from "./config.js";

export function setHealthStatus(isOk) {
  const badge = document.getElementById("healthBadge");
  badge.textContent = isOk ? "API: online" : "API: offline";
  badge.className = `badge ${isOk ? "badge-good" : "badge-bad"}`;
}

export function setAuthStatus(isRequired) {
  const badge = document.getElementById("authBadge");
  badge.textContent = isRequired ? "Auth: required" : "Auth: open";
  badge.className = `badge ${isRequired ? "badge-warn" : "badge-good"}`;
}

export function setLoading(isLoading) {
  const button = document.getElementById("runBtn");
  button.disabled = isLoading;
  if (isLoading) {
    button.classList.add("loading");
  } else {
    button.classList.remove("loading");
  }
}

export function showAlert(message) {
  const alert = document.getElementById("alert");
  alert.textContent = message;
  alert.classList.remove("hidden");
}

export function clearAlert() {
  const alert = document.getElementById("alert");
  alert.textContent = "";
  alert.classList.add("hidden");
}

export function showToast(message) {
  const toast = document.getElementById("toast");
  toast.textContent = message;
  toast.classList.remove("hidden");
  setTimeout(() => toast.classList.add("hidden"), 2400);
}

export function updateStatusText(text) {
  document.getElementById("runStatus").textContent = text;
}

export function updateMappingStatus(mapping) {
  const mappingLabels = {
    catalog: "mapCatalog",
    reviews: "mapReviews",
    pricing: "mapPricing",
    competitors: "mapCompetitors",
    performance_signals: "mapPerformance",
  };

  Object.entries(mappingLabels).forEach(([key, elementId]) => {
    const element = document.getElementById(elementId);
    if (mapping[key]) {
      element.textContent = "Mapped";
      element.style.color = "#58d1a3";
    } else {
      element.textContent = "Not mapped";
      element.style.color = "#aab6d8";
    }
  });
}

export function renderReport(reportMarkdown) {
  const reportEl = document.getElementById("report");
  reportEl.innerHTML = window.marked.parse(reportMarkdown || "");
}

export function extractMeta(report) {
  const confidenceMatch = report.match(/Confidence Score:\s*(\d+)%/i);
  const completenessMatch = report.match(/Data Completeness(?: Assessment)?:\s*([A-Za-z]+)(?:\s*\((\d+)%\))?/i);

  const confidence = confidenceMatch ? Number(confidenceMatch[1]) : null;
  const completenessLabel = completenessMatch ? completenessMatch[1] : null;
  const completenessScore = completenessMatch && completenessMatch[2] ? Number(completenessMatch[2]) : null;

  return { confidence, completenessLabel, completenessScore };
}

export function updateBadges(meta) {
  const confidenceScore = document.getElementById("confidenceScore");
  const confidenceBadge = document.getElementById("confidenceBadge");
  const completenessScore = document.getElementById("completenessScore");
  const completenessMeter = document.getElementById("completenessMeter");

  // Update confidence metric card
  if (meta.confidence !== null) {
    const { label, className, colorClass } = scoreToBadge(meta.confidence);
    confidenceScore.textContent = `${meta.confidence}%`;
    confidenceScore.className = `metric-value ${colorClass}`;
    confidenceBadge.textContent = label;
    confidenceBadge.className = `badge ${className}`;
  } else {
    confidenceScore.textContent = "--";
    confidenceScore.className = "metric-value";
    confidenceBadge.textContent = "--";
    confidenceBadge.className = "badge badge-muted";
  }

  // Update completeness metric card with animated meter
  if (meta.completenessScore !== null) {
    completenessScore.textContent = `${meta.completenessScore}%`;
    const meterProgress = completenessMeter.querySelector(".meter-progress");
    if (meterProgress) {
      // Trigger reflow to ensure animation plays
      void meterProgress.offsetWidth;
      meterProgress.style.width = `${meta.completenessScore}%`;
      meterProgress.style.background = getLinearGradient(meta.completenessScore);
    }
  } else {
    completenessScore.textContent = "--";
  }
}

export function updateRiskList(report) {
  const riskList = document.getElementById("riskList");
  const risks = extractSection(report, "Risk Flags");
  renderList(riskList, risks.length ? risks : ["No explicit risk flags found."]);
}

export function updateRecommendations(report) {
  const recList = document.getElementById("recommendations");
  const recs = extractSection(report, "Strategic Recommendations");
  renderList(recList, recs.length ? recs : ["No recommendations extracted."]);
}

export function updateChart(confidence) {
  // Chart removed in favor of metric cards
  // Kept for backwards compatibility
}

export function getFormValues() {
  return {
    mode: document.getElementById("mode").value,
    goal: document.getElementById("goal").value,
    scopeType: document.getElementById("scopeType").value,
    scopeValue: document.getElementById("scopeValue").value.trim(),
    marketplace: document.getElementById("marketplace").value.trim(),
    region: document.getElementById("region").value.trim(),
    timeframe: document.getElementById("timeframe").value.trim(),
    constraints: Array.from(document.querySelectorAll(".constraint:checked")).map((input) => input.value),
  };
}

export function setDefaultValues() {
  document.getElementById("apiBaseUrl").value = CONFIG.API_BASE_URL;
  document.getElementById("mode").value = CONFIG.DEFAULT_BRIEF.mode;
  document.getElementById("goal").value = CONFIG.DEFAULT_BRIEF.businessGoal;
  document.getElementById("scopeType").value = CONFIG.DEFAULT_BRIEF.scopeType;
  document.getElementById("scopeValue").value = CONFIG.DEFAULT_BRIEF.scopeValue;
  document.getElementById("marketplace").value = CONFIG.DEFAULT_BRIEF.marketplace;
  document.getElementById("region").value = CONFIG.DEFAULT_BRIEF.region;
  document.getElementById("timeframe").value = CONFIG.DEFAULT_BRIEF.timeframe;
}

export function scoreToBadge(score) {
  if (score >= 75) {
    return { label: "High", className: "badge-confidence-high", colorClass: "value-high" };
  }
  if (score >= 50) {
    return { label: "Medium", className: "badge-confidence-mid", colorClass: "value-mid" };
  }
  return { label: "Low", className: "badge-confidence-low", colorClass: "value-low" };
}

function getCompletenessColor(score) {
  if (score >= 75) return "rgba(78, 209, 139, 0.5)";
  if (score >= 50) return "rgba(242, 201, 76, 0.5)";
  return "rgba(255, 107, 107, 0.5)";
}

function getLinearGradient(score) {
  if (score >= 75) return "linear-gradient(90deg, #4ed18b, #41b883)";
  if (score >= 50) return "linear-gradient(90deg, #f2c94c, #e6b800)";
  return "linear-gradient(90deg, #ff6b6b, #ff5252)";
}

function extractSection(report, sectionTitle) {
  const pattern = new RegExp(`${sectionTitle}\\n([\\s\\S]*?)(?:\\n##|$)`, "i");
  const match = report.match(pattern);
  if (!match) {
    return [];
  }

  return match[1]
    .split("\n")
    .map((line) => line.replace(/^[-*]\s+/, "").trim())
    .filter((line) => line && !line.startsWith("#"));
}

function renderList(element, items) {
  element.innerHTML = "";
  items.forEach((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    element.appendChild(li);
  });
}

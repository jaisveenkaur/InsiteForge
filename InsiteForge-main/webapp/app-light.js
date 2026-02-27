import { CONFIG } from "./config.js";
import { fetchHealth, fetchAuthStatus, runAnalysis } from "./api.js";

// ============================================================
// STATE MANAGEMENT
// ============================================================
const state = {
  currentStep: 1,
  formData: {
    product: "",
    marketplace: "",
    mode: "quick",
    goal: "growth",
    dataMode: "sample",
    files: [],
  },
  apiReady: false,
  authRequired: false,
};

// ============================================================
// UI ELEMENTS CACHE
// ============================================================
const ui = {
  // Step buttons
  step1Btn: document.getElementById("step1Btn"),
  step2Btn: document.getElementById("step2Btn"),
  step2Back: document.getElementById("step2Back"),
  step3Btn: document.getElementById("step3Btn"),
  step3Back: document.getElementById("step3Back"),
  step4Btn: document.getElementById("step4Btn"),
  step4Back: document.getElementById("step4Back"),
  newAnalysisBtn: document.getElementById("newAnalysisBtn"),

  // Form inputs
  productInput: document.getElementById("productInput"),
  marketplaceInput: document.getElementById("marketplaceInput"),
  modeRadios: document.querySelectorAll('input[name="mode"]'),
  goalRadios: document.querySelectorAll('input[name="goal"]'),
  dataModeRadios: document.querySelectorAll('input[name="dataMode"]'),
  fileInput: document.getElementById("fileInput"),

  // Panels
  steps: document.querySelectorAll(".step"),
  uploadSection: document.getElementById("uploadSection"),
  fileList: document.getElementById("fileList"),
  stepAlert: document.getElementById("stepAlert"),
  stepStatus: document.getElementById("stepStatus"),

  // Results
  resultsSection: document.getElementById("resultsSection"),
  resultsTitle: document.getElementById("resultsTitle"),
  resultsSubtitle: document.getElementById("resultsSubtitle"),
  confidenceScore: document.getElementById("confidenceScore"),
  confidenceBadge: document.getElementById("confidenceBadge"),
  completenessScore: document.getElementById("completenessScore"),
  completenessMeter: document.getElementById("completenessMeter"),
  riskList: document.getElementById("riskList"),
  recommendations: document.getElementById("recommendations"),
  report: document.getElementById("report"),

  // Status
  healthBadge: document.getElementById("healthBadge"),
  authBadge: document.getElementById("authBadge"),
  toast: document.getElementById("toast"),
};

// ============================================================
// INITIALIZATION
// ============================================================
async function init() {
  setupEventListeners();
  await checkApiHealth();
}

async function checkApiHealth() {
  try {
    const health = await fetchHealth(CONFIG.API_BASE_URL);
    state.apiReady = health.status === "ok";
    updateHealthBadge();

    const authStatus = await fetchAuthStatus(CONFIG.API_BASE_URL);
    state.authRequired = authStatus.api_key_required;
    updateAuthBadge();
  } catch (err) {
    console.error("Health check failed:", err);
    state.apiReady = false;
    updateHealthBadge();
    showToast("⚠️ API connection failed. Try refreshing.");
  }
}

// ============================================================
// EVENT LISTENERS
// ============================================================
function setupEventListeners() {
  // Step 1
  ui.step1Btn.addEventListener("click", handleStep1Next);

  // Step 2
  ui.step2Btn.addEventListener("click", handleStep2Next);
  ui.step2Back.addEventListener("click", () => goToStep(1));

  // Step 3
  ui.step3Btn.addEventListener("click", handleStep3Next);
  ui.step3Back.addEventListener("click", () => goToStep(2));

  // Step 4
  ui.step4Btn.addEventListener("click", handleStep4Run);
  ui.step4Back.addEventListener("click", () => goToStep(3));

  // Form inputs
  ui.modeRadios.forEach((r) => r.addEventListener("change", (e) => (state.formData.mode = e.target.value)));
  ui.goalRadios.forEach((r) => r.addEventListener("change", (e) => (state.formData.goal = e.target.value)));
  
  ui.dataModeRadios.forEach((r) => {
    r.addEventListener("change", (e) => {
      state.formData.dataMode = e.target.value;
      toggleUploadSection();
    });
  });

  ui.fileInput.addEventListener("change", handleFileSelect);

  // Drag and drop
  const fileInputWrapper = document.querySelector(".file-input-wrapper");
  if (fileInputWrapper) {
    fileInputWrapper.addEventListener("dragover", (e) => {
      e.preventDefault();
      fileInputWrapper.style.borderColor = "var(--primary)";
    });
    fileInputWrapper.addEventListener("dragleave", () => {
      fileInputWrapper.style.borderColor = "var(--border)";
    });
    fileInputWrapper.addEventListener("drop", (e) => {
      e.preventDefault();
      fileInputWrapper.style.borderColor = "var(--border)";
      handleFileSelect({ target: { files: e.dataTransfer.files } });
    });
  }

  // Results
  ui.newAnalysisBtn.addEventListener("click", () => {
    state.currentStep = 1;
    state.formData = {
      product: "",
      marketplace: "",
      mode: "quick",
      goal: "growth",
      dataMode: "sample",
      files: [],
    };
    goToStep(1);
    ui.productInput.focus();
  });
}

// ============================================================
// STEP NAVIGATION
// ============================================================
function goToStep(stepNum) {
  state.currentStep = stepNum;
  ui.steps.forEach((s) => s.classList.remove("active"));
  
  if (stepNum === 1) ui.steps[0].classList.add("active");
  else if (stepNum === 2) ui.steps[1].classList.add("active");
  else if (stepNum === 3) ui.steps[2].classList.add("active");
  else if (stepNum === 4) ui.steps[3].classList.add("active");
  else if (stepNum === 5) {
    ui.steps[4].classList.add("active");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  clearAlert();
}

function handleStep1Next() {
  const product = ui.productInput.value.trim();
  if (!product) {
    showAlert("Please enter a product name or SKU");
    return;
  }
  state.formData.product = product;
  state.formData.marketplace = ui.marketplaceInput.value.trim() || "Unknown";
  goToStep(2);
}

function handleStep2Next() {
  goToStep(3);
}

function handleStep3Next() {
  goToStep(4);
}

async function handleStep4Run() {
  if (!state.apiReady) {
    showAlert("❌ API is not available. Please try again.");
    return;
  }

  if (state.formData.dataMode === "upload" && state.formData.files.length === 0) {
    showAlert("Please upload at least one CSV file");
    return;
  }

  await runAnalysis();
}

// ============================================================
// FILE HANDLING
// ============================================================
function toggleUploadSection() {
  if (state.formData.dataMode === "upload") {
    ui.uploadSection.classList.remove("hidden");
  } else {
    ui.uploadSection.classList.add("hidden");
    state.formData.files = [];
    ui.fileList.innerHTML = "";
  }
}

async function handleFileSelect(e) {
  const files = Array.from(e.target.files);
  state.formData.files = files;

  ui.fileList.innerHTML = "";
  files.forEach((file) => {
    const item = document.createElement("div");
    item.className = "file-item";
    item.innerHTML = `
      <span>📄 ${file.name}</span>
      <button onclick="console.log('remove')" style="background:none;border:none;color:var(--text-light);cursor:pointer;">✕</button>
    `;
    ui.fileList.appendChild(item);
  });
}

// ============================================================
// API ANALYSIS
// ============================================================
async function runAnalysis() {
  const { product, marketplace, mode, goal, dataMode, files } = state.formData;

  showStatus("⏳ Preparing analysis...");
  ui.step4Btn.disabled = true;

  try {
    // Parse files if uploaded
    let dataSources = {
      catalog: { path: CONFIG.DEFAULT_SOURCES.catalog },
      reviews: { path: CONFIG.DEFAULT_SOURCES.reviews },
      pricing: { path: CONFIG.DEFAULT_SOURCES.pricing },
      competitors: { path: CONFIG.DEFAULT_SOURCES.competitors },
      performance_signals: { path: CONFIG.DEFAULT_SOURCES.performance_signals },
    };

    if (dataMode === "upload" && files.length > 0) {
      let fileData = {};
      for (const file of files) {
        const content = await file.text();
        const rows = content.split("\n").map((line) => {
          const values = line.split(",");
          return values;
        });
        const headers = rows[0];
        const data = rows.slice(1).map((row) => {
          const obj = {};
          headers.forEach((h, i) => {
            obj[h.trim()] = row[i];
          });
          return obj;
        });
        fileData[file.name.replace(".csv", "")] = data;
      }
      dataSources = {
        catalog: fileData.catalog || dataSources.catalog,
        reviews: fileData.reviews || dataSources.reviews,
        pricing: fileData.pricing || dataSources.pricing,
        competitors: fileData.competitors || dataSources.competitors,
        performance_signals: fileData.performance || dataSources.performance_signals,
      };
    }

    const brief = {
      mode,
      business_goal: goal,
      scope: {
        type: "Product",
        value: product,
      },
      marketplaces: [marketplace],
      region: "Unknown",
      timeframe: "Latest",
      data_sources: dataSources,
    };

    showStatus("🔄 Running analysis...");

    const result = await runAnalysis(brief, null);

    showResults(result, product, mode);
  } catch (err) {
    console.error("Analysis error:", err);
    showAlert(`❌ ${err.message}`);
  } finally {
    ui.step4Btn.disabled = false;
    clearStatus();
  }
}

// ============================================================
// RESULTS DISPLAY
// ============================================================
function showResults(result, product, mode) {
  ui.resultsTitle.textContent = `✨ Analysis Complete`;
  ui.resultsSubtitle.textContent = `${product} • ${mode === "quick" ? "Quick" : "Deep"} Analysis`;

  // Update metrics
  const confidenceMatch = result.report.match(/Confidence Score:\s*(\d+)%/i);
  const completenessMatch = result.report.match(/Data Completeness.*?:\s*(\d+)%/i);

  if (confidenceMatch) {
    const confidence = parseInt(confidenceMatch[1]);
    ui.confidenceScore.textContent = `${confidence}%`;
    ui.confidenceBadge.textContent = confidence >= 75 ? "High" : confidence >= 50 ? "Medium" : "Low";
  }

  if (completenessMatch) {
    const completeness = parseInt(completenessMatch[1]);
    ui.completenessScore.textContent = `${completeness}%`;
    ui.completenessMeter.style.width = `${completeness}%`;
  }

  // Extract risks and recommendations
  const riskMatch = result.report.match(/Risk Flags?\s*[:\-]?\s*([\s\S]*?)(?:Strategic|Recommendations|$)/i);
  const recMatch = result.report.match(/(?:Strategic )?Recommendations?\s*[:\-]?\s*([\s\S]*?)(?:Full Report|$)/i);

  if (riskMatch) {
    const risks = riskMatch[1].split("\n").filter((r) => r.trim());
    ui.riskList.innerHTML = risks.map((r) => `<li>${r.trim()}</li>`).join("");
  }

  if (recMatch) {
    const recs = recMatch[1].split("\n").filter((r) => r.trim());
    ui.recommendations.innerHTML = recs.map((r) => `<li>${r.trim()}</li>`).join("");
  }

  // Full report
  ui.report.innerHTML = window.marked.parse(result.report || "");

  goToStep(5);
  showToast("✅ Analysis complete!");
}

// ============================================================
// API FUNCTION (imported version)
// ============================================================
async function runAnalysis(brief, apiKey) {
  const headers = { "Content-Type": "application/json" };
  if (apiKey) {
    headers["x-api-key"] = apiKey;
  }

  const response = await fetch(`${CONFIG.API_BASE_URL}/analyze`, {
    method: "POST",
    headers,
    body: JSON.stringify({ brief }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Analysis failed");
  }

  return response.json();
}

// ============================================================
// UI HELPERS
// ============================================================
function showAlert(msg) {
  ui.stepAlert.textContent = msg;
  ui.stepAlert.classList.remove("hidden");
}

function clearAlert() {
  ui.stepAlert.classList.add("hidden");
  ui.stepAlert.textContent = "";
}

function showStatus(msg) {
  ui.stepStatus.textContent = msg;
  ui.stepStatus.classList.add("loading");
}

function clearStatus() {
  ui.stepStatus.textContent = "";
  ui.stepStatus.classList.remove("loading");
}

function showToast(msg) {
  ui.toast.textContent = msg;
  ui.toast.classList.add("show");
  setTimeout(() => ui.toast.classList.remove("show"), 3000);
}

function updateHealthBadge() {
  ui.healthBadge.textContent = state.apiReady ? "API: online" : "API: offline";
  ui.healthBadge.className = `badge ${state.apiReady ? "badge-good" : "badge-bad"}`;
}

function updateAuthBadge() {
  ui.authBadge.textContent = state.authRequired ? "Auth: required" : "Auth: open";
  ui.authBadge.className = `badge ${state.authRequired ? "badge-warn" : "badge-good"}`;
}

// ============================================================
// START
// ============================================================
init();

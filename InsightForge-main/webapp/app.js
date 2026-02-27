import { CONFIG } from "./config.js";

// ====================================
// STATE MANAGEMENT
// ====================================

let appState = {
  isDashboardVisible: false,
  analysisRunning: false,
  uploadedFiles: [],
  parsedData: {},
};

// ====================================
// DOM ELEMENTS - SAFE ACCESSORS
// ====================================

const getElement = (id) => {
  const elem = document.getElementById(id);
  // if (!elem) console.warn(`⚠️  Element #${id} not found`);
  return elem;
};

const heroSection = getElement("heroSection");
const dashboard = getElement("dashboard");
const startBtn = getElement("startBtn");
const runBtn = getElement("runBtn");
const demoBtn = getElement("demoBtn");
const newAnalysisBtn = getElement("newAnalysisBtn");
const downloadPdfBtn = getElement("downloadPdfBtn");

const mobileMenuBtn = getElement("mobileMenuBtn");
const mainNav = getElement("mainNav");

const productInput = getElement("productInput");
const marketplace = getElement("marketplace");
const region = getElement("region");
const fileInput = getElement("fileInput");
const fileDropZone = getElement("fileDropZone");
const fileList = getElement("fileList");
const uploadSection = getElement("uploadSection");

const riskList = getElement("riskList");
const recommendations = getElement("recommendations");
const report = getElement("report");
const confidenceScore = getElement("confidenceScore");
const completenessScore = getElement("completenessScore");
const completenessMeter = getElement("completenessMeter");
const confidenceBadge = getElement("confidenceBadge");

const configAlert = getElement("configAlert");
const configStatus = getElement("configStatus");
const toast = getElement("toast");

// ====================================
// INITIALIZATION
// ====================================

function initApp() {
  console.log("%c🔥 InsightForge Initializing...", "color:#41b883; font-weight:bold; font-size:14px");

  // Check if essential elements exist
  // startBtn is only on index.html, dashboard is on dashboard.html
  if (!startBtn) {
    console.warn("ℹ️ startBtn not found (Expected if not on index.html)");
  }

  // --- Intersection Observer for Storytelling Fade-ins ---
  const observerOptions = {
    root: null,
    rootMargin: '0px',
    threshold: 0.15
  };

  const sectionObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        observer.unobserve(entry.target);
      }
    });
  }, observerOptions);

  document.querySelectorAll('.fade-up-section').forEach(section => {
    sectionObserver.observe(section);
  });

  // --- Advanced Interactions: Cursor Glow & Parallax ---
  const cursorGlow = document.getElementById('cursorGlow');
  if (cursorGlow) {
    document.addEventListener('mousemove', (e) => {
      cursorGlow.style.transform = `translate(${e.clientX - 300}px, ${e.clientY - 300}px)`;
    });
  }

  const parallaxBg = document.getElementById('parallaxBg');
  if (parallaxBg) {
    // Removed scroll listener that forced background movement
  }

  setupEventListeners();
  checkAPIHealth();
  console.log("%c✅ InsightForge Ready", "color:#41b883; font-weight:bold; font-size:14px");
}

function setupEventListeners() {
  console.log("📍 Setting up event listeners...");

  // Start button - PRIMARY (Only on index.html)
  if (startBtn) {
    startBtn.addEventListener("click", function (e) {
      console.log("✓ Start button clicked!");
      window.location.href = "dashboard.html";
    });
  }

  // Mobile Menu Toggle
  if (mobileMenuBtn && mainNav) {
    mobileMenuBtn.addEventListener("click", () => {
      mobileMenuBtn.classList.toggle("active");
      mainNav.classList.toggle("active");
    });
  }

  // Run analysis button
  if (runBtn) {
    runBtn.addEventListener("click", function (e) {
      console.log("✓ Run analysis clicked!");
      e.preventDefault();
      handleRunAnalysis();
    });
  }

  // Enter key support for input
  if (productInput) {
    productInput.addEventListener("keydown", function (e) {
      if (e.key === "Enter") {
        e.preventDefault();
        if (!appState.analysisRunning) {
          handleRunAnalysis();
        }
      }
    });
  }

  // PDF Download support
  if (downloadPdfBtn) {
    downloadPdfBtn.addEventListener("click", function (e) {
      e.preventDefault();
      if (!report) return;
      const opt = {
        margin: [0.75, 0.5, 0.75, 0.5],
        filename: `${productInput.value.trim() || 'InsightForge'}_Intel_Report.pdf`,
        image: { type: 'jpeg', quality: 1.0 },
        html2canvas: { scale: 2, useCORS: true },
        jsPDF: { unit: 'in', format: 'letter', orientation: 'portrait' },
        pagebreak: { mode: ['avoid-all', 'css', 'legacy'] }
      };

      showToast("Generating PDF...", "info");
      report.classList.add("pdf-export");
      html2pdf().set(opt).from(report).save().then(() => {
        report.classList.remove("pdf-export");
        showToast("PDF Downloaded!", "success");
      }).catch((err) => {
        report.classList.remove("pdf-export");
        console.error("PDF generation failed:", err);
      });
    });
  }

  // Advanced Settings Toggle
  const advancedToggleBtn = getElement("advancedToggleBtn");
  const advancedSettings = getElement("advancedSettings");
  if (advancedToggleBtn && advancedSettings) {
    advancedToggleBtn.addEventListener("click", (e) => {
      e.preventDefault();
      advancedSettings.classList.toggle("hidden");
    });
  }

  // New analysis button
  if (newAnalysisBtn) {
    newAnalysisBtn.addEventListener("click", function (e) {
      console.log("✓ New analysis clicked!");
      e.preventDefault();
      resetToDashboard();
    });
  }

  // Mode radio buttons
  const modeInputs = document.querySelectorAll('input[name="mode"]');
  modeInputs.forEach(input => {
    input.addEventListener("change", (e) => {
      const modeTime = getElement("modeTime");
      if (modeTime) {
        modeTime.textContent = e.target.value === "quick" ? "⚡ Quick = Fast" : "🔍 Deep = Detailed";
      }
    });
  });

  // Data mode toggle
  const dataModeInputs = document.querySelectorAll('input[name="dataMode"]');
  dataModeInputs.forEach(input => {
    input.addEventListener("change", (e) => {
      if (uploadSection) {
        uploadSection.classList.toggle("hidden", e.target.value === "sample");
      }
    });
  });

  // File upload
  if (fileDropZone && fileInput) {
    fileDropZone.addEventListener("click", () => fileInput.click());
    fileDropZone.addEventListener("dragover", (e) => {
      e.preventDefault();
      fileDropZone.style.borderColor = "var(--primary)";
      fileDropZone.style.background = "rgba(65, 184, 131, 0.15)";
    });
    fileDropZone.addEventListener("dragleave", () => {
      fileDropZone.style.borderColor = "";
      fileDropZone.style.background = "";
    });
    fileDropZone.addEventListener("drop", (e) => {
      e.preventDefault();
      fileDropZone.style.borderColor = "";
      fileDropZone.style.background = "";
      handleFiles(e.dataTransfer.files);
    });
    fileInput.addEventListener("change", (e) => handleFiles(e.target.files));
  }

  console.log("✅ Event listeners ready");
}

// ====================================
// UI CONTROLS
// ====================================

function showDashboard() {
  console.log("📊 Showing dashboard...");
  if (heroSection) heroSection.style.display = "none";
  if (dashboard) {
    dashboard.style.display = "block";
    setTimeout(() => {
      dashboard.scrollIntoView({ behavior: "smooth" });
    }, 100);
  }
  appState.isDashboardVisible = true;
}

function resetToDashboard() {
  console.log("🔄 Resetting dashboard");

  if (productInput) productInput.value = "";
  if (marketplace) marketplace.value = "";
  if (region) region.value = "";

  const searchHero = getElement("searchHero");
  const resultsContainer = getElement("resultsContainer");

  if (searchHero) searchHero.classList.remove("active-search");
  if (resultsContainer) resultsContainer.classList.add("hidden");

  if (newAnalysisBtn) newAnalysisBtn.style.display = "none";
  if (downloadPdfBtn) downloadPdfBtn.style.display = "none";
  if (riskList) riskList.innerHTML = '<li class="placeholder">Awaiting analysis...</li>';
  if (recommendations) recommendations.innerHTML = '<li class="placeholder">Awaiting analysis...</li>';
  if (report) report.innerHTML = '<p class="placeholder">Analysis report will appear here...</p>';
  if (confidenceScore) confidenceScore.textContent = "--";
  if (completenessScore) completenessScore.textContent = "--";
  if (completenessMeter) completenessMeter.style.width = "0%";
  if (confidenceBadge) confidenceBadge.textContent = "--";

  scrollToTop();
}

function scrollToTop() {
  if (dashboard) {
    dashboard.scrollIntoView({ behavior: "smooth" });
  }
}

// ====================================
// API HEALTH CHECK
// ====================================

async function checkAPIHealth() {
  console.log("🏥 Checking API health...");
  try {
    const response = await fetch(`${CONFIG.API_BASE_URL}/health`, {
      method: "GET",
      headers: { "Content-Type": "application/json", "Bypass-Tunnel-Reminder": "true" }
    });
    const data = await response.json();
    console.log("✅ API OK:", data);

    const healthBadge = getElement("healthBadge");
    if (healthBadge) {
      healthBadge.textContent = "🟢 API Online";
      healthBadge.className = "badge active";
    }
  } catch (error) {
    console.warn("⚠️  API offline:", error.message);
    const healthBadge = getElement("healthBadge");
    if (healthBadge) {
      healthBadge.className = "badge warning";
      healthBadge.textContent = "🟡 API Offline";
    }
  }
}

// ====================================
// FILE HANDLING
// ====================================

function handleFiles(files) {
  console.log(`📁 ${files.length} file(s) selected`);
  const newFiles = Array.from(files);
  appState.uploadedFiles = newFiles;

  if (typeof Papa !== 'undefined') {
    appState.parsedData = {}; // clear old
    newFiles.forEach((file) => {
      Papa.parse(file, {
        header: true,
        dynamicTyping: true,
        skipEmptyLines: true,
        complete: function (results) {
          console.log(`Parsed ${file.name}: ${results.data.length} rows`);

          if (file.name.toLowerCase().includes('review')) {
            appState.parsedData.reviews = results.data;
          } else if (file.name.toLowerCase().includes('price') || file.name.toLowerCase().includes('pricing')) {
            appState.parsedData.pricing = results.data;
          } else {
            // Default to catalog if ambiguous
            appState.parsedData.catalog = results.data;
          }
        }
      });
    });
  }

  displayFileList();
}

function displayFileList() {
  if (!fileList) return;
  fileList.innerHTML = "";
  appState.uploadedFiles.forEach((file) => {
    const item = document.createElement("div");
    item.className = "file-item";
    item.innerHTML = `<span>📄 ${file.name} (${(file.size / 1024).toFixed(1)}KB)</span>`;
    fileList.appendChild(item);
  });
}

// ====================================
// ANALYSIS
// ====================================



async function handleRunAnalysis() {
  console.log("🔍 Running analysis...");

  if (!productInput?.value?.trim()) {
    showToast("Please enter a product name", "error");
    return;
  }

  // Trigger UI transition for minimal layout
  const searchHero = getElement("searchHero");
  const resultsContainer = getElement("resultsContainer");
  if (searchHero) searchHero.classList.add("active-search");
  if (resultsContainer) resultsContainer.classList.remove("hidden");

  setStatus("Running analysis...");
  setLoading(true);
  appState.analysisRunning = true;

  try {
    const brief = {
      product_name: productInput.value.trim(),
      scope_type: "SKU",
      business_goal: document.querySelector('input[name="goal"]:checked')?.value || "growth",
      scope_value: productInput.value.trim().toUpperCase(),
      mode: document.querySelector('input[name="mode"]:checked')?.value || "quick",
      marketplace: marketplace?.value || "Amazon",
      region: region?.value || "Global",
      data_sources: {
        catalog: { path: "catalog.json" },
        reviews: { path: "reviews.json" },
        pricing: { path: "pricing.json" },
        competitors: { path: "competitors.json" },
        performance_signals: { path: "performance_signals.json" }
      }
    };

    // If Custom CSV mode is active and we have parsed data, inject it inline
    const isCustomMode = document.querySelector('input[name="dataMode"]:checked')?.value === "custom";
    if (isCustomMode && Object.keys(appState.parsedData).length > 0) {
      console.log("Injecting custom user CSV data inline into the analysis payload.");
      if (appState.parsedData.catalog) brief.data_sources.catalog = appState.parsedData.catalog;
      if (appState.parsedData.reviews) brief.data_sources.reviews = appState.parsedData.reviews;
      if (appState.parsedData.pricing) brief.data_sources.pricing = appState.parsedData.pricing;
    }

    console.log("📤 Analysis request:", brief);
    const apiPayload = {
      brief: brief,
      update_memory: false,
      memory_path: "data/domain_memory.json",
      source_base_dir: "datasets/processed",
      output_path: "out/api_report.md"
    };

    const result = await callAPI(apiPayload);
    displayResults(result);
    setLoading(false);
    appState.analysisRunning = false;
    setStatus("✅ Analysis complete!");
    showToast("✅ Analysis complete!", "success");
    if (newAnalysisBtn) newAnalysisBtn.style.display = "block";
    scrollToTop();
  } catch (error) {
    console.warn("Analysis API unreachable or failed:", error);
    setStatus(`❌ ${error.message}`);
    showToast(error.message, "error");
  } finally {
    setLoading(false);
    appState.analysisRunning = false;
  }
}

// ====================================
// API CALL
// ====================================

async function callAPI(brief) {
  console.log("🔄 Calling API...");
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), CONFIG.API_TIMEOUT || 30000);

  try {
    const response = await fetch(`${CONFIG.API_BASE_URL}/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Bypass-Tunnel-Reminder": "true" },
      body: JSON.stringify(brief),
      signal: controller.signal
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `API Error: ${response.status}`);
    }

    return response.json();
  } catch (err) {
    clearTimeout(timeoutId);
    if (err.name === 'AbortError') {
      throw new Error("API request timed out (30s). The server might be busy or offline.");
    }
    throw err;
  }
}

// ====================================
// RESULTS DISPLAY
// ====================================

function displayResults(result) {
  console.log("📊 Displaying results...");

  if (confidenceScore) confidenceScore.textContent = Math.round((result.confidence_score || 0.75) * 100) + "%";
  if (completenessScore) completenessScore.textContent = Math.round((result.data_completeness || 0.8) * 100) + "%";
  if (completenessMeter) completenessMeter.style.width = ((result.data_completeness || 0.8) * 100) + "%";

  if (confidenceBadge) {
    const conf = result.confidence_score || 0.75;
    confidenceBadge.textContent = conf >= 0.8 ? "High" : conf >= 0.5 ? "Medium" : "Low";
  }

  if (riskList && result.risks?.length) {
    riskList.innerHTML = result.risks.slice(0, 5).map(r => `<li>${r}</li>`).join("");
  }

  if (recommendations && result.recommendations?.length) {
    recommendations.innerHTML = result.recommendations.slice(0, 5).map(r => `<li>${r}</li>`).join("");
  }

  if (report && result.report) {
    try {
      const reportContent = Array.isArray(result.report) ? result.report.join("\n") : result.report;
      report.innerHTML = marked.parse(reportContent);
    } catch (e) {
      const reportContent = Array.isArray(result.report) ? result.report.join("\n") : result.report;
      report.textContent = reportContent;
    }

    if (downloadPdfBtn) downloadPdfBtn.style.display = "block";
  }
}

// ====================================
// UTILITIES
// ====================================

function setStatus(message) {
  if (configStatus) {
    configStatus.textContent = message;
    configStatus.style.color = message.includes("❌") ? "#ff6b6b" : message.includes("✅") ? "#41b883" : "#a4b5aa";
  }
}

function setLoading(isLoading) {
  if (!runBtn) return;
  runBtn.disabled = isLoading;

  const spinner = runBtn.querySelector('.spinner');
  const btnText = runBtn.querySelector('.btn-text');

  if (isLoading) {
    if (btnText) btnText.textContent = "Analyzing...";
    if (spinner) spinner.classList.remove('hidden');
  } else {
    if (btnText) btnText.textContent = "Generate Insights";
    if (spinner) spinner.classList.add('hidden');
  }
}

function showToast(message, type = "info") {
  if (!toast) {
    // Create toast if it doesn't exist
    const t = document.createElement("div");
    t.id = "toast";
    t.className = `toast show ${type}`;
    t.textContent = message;
    t.style.cssText = `
      position: fixed;
      bottom: 20px;
      right: 20px;
      padding: 16px 24px;
      background: #41b883;
      color: white;
      border-radius: 8px;
      box-shadow: 0 8px 16px rgba(0,0,0,0.3);
      z-index: 9999;
    `;
    document.body.appendChild(t);
    setTimeout(() => t.remove(), 3000);
    return;
  }
  toast.textContent = message;
  toast.className = `toast show ${type}`;
  setTimeout(() => toast.classList.remove("show"), 3000);
}

// ====================================
// LAUNCH APP
// ====================================

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initApp);
} else {
  initApp();
}

const SAMPLE = {
  candidate_name: "Ada Lovelace",
  job_title: "Junior AI Backend Developer",
  company_name: "Example GmbH",
  cv_text:
    "I built AI backend projects with Python, FastAPI, PostgreSQL, Docker, REST APIs, Git, testing, and OpenAI API integrations.",
  job_description:
    "Requirements: Python, FastAPI, PostgreSQL, Docker, REST APIs, Git, LLM experience, and testing. Nice to have: RAG, AWS, and CI/CD. German B2 and English fluent are required. Hybrid role in Berlin. Bachelor's degree in computer science or related field.",
};

const DEFAULT_API_BASE_URL = "http://127.0.0.1:8001";
const MAX_CV_FILE_BYTES = 5 * 1024 * 1024;
const STATUS_LABELS = {
  deterministic: "local draft",
  fallback: "safety fallback",
  generated: "AI generated",
  not_requested: "not requested",
  unavailable: "unavailable",
};

const form = document.querySelector("#analysisForm");
const sampleButton = document.querySelector("#sampleButton");
const healthButton = document.querySelector("#healthButton");
const submitButton = document.querySelector("#submitButton");
const apiBaseUrlInput = document.querySelector("#apiBaseUrl");
const cvFileInput = document.querySelector("#cvFile");
const cvFileStatus = document.querySelector("#cvFileStatus");
const statusDot = document.querySelector("#statusDot");
const statusText = document.querySelector("#statusText");
const emptyState = document.querySelector("#emptyState");
const resultContent = document.querySelector("#resultContent");

apiBaseUrlInput.value = localStorage.getItem("apiBaseUrl") || DEFAULT_API_BASE_URL;
fillSample();

sampleButton.addEventListener("click", fillSample);
healthButton.addEventListener("click", () => checkHealth());
cvFileInput.addEventListener("change", () => handleCvFileChange());
apiBaseUrlInput.addEventListener("change", () => {
  localStorage.setItem("apiBaseUrl", cleanApiBaseUrl());
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  setBusy(true);
  setStatus("checking", "Analyzing...");

  try {
    localStorage.setItem("apiBaseUrl", cleanApiBaseUrl());
    const response = await fetch(`${cleanApiBaseUrl()}/applications/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(readPayload()),
    });

    const payload = await response.json();
    if (!response.ok) {
      throw new Error(readApiError(payload));
    }

    renderResult(payload);
    setStatus("online", "API online");
  } catch (error) {
    setStatus("offline", error.message || "API request failed");
  } finally {
    setBusy(false);
  }
});

async function checkHealth() {
  setStatus("checking", "Checking...");
  try {
    localStorage.setItem("apiBaseUrl", cleanApiBaseUrl());
    const response = await fetch(`${cleanApiBaseUrl()}/health`);
    if (!response.ok) {
      throw new Error("API health check failed");
    }
    setStatus("online", "API online");
  } catch (error) {
    setStatus("offline", error.message || "API offline");
  }
}

async function handleCvFileChange() {
  const file = cvFileInput.files[0];
  if (!file) {
    cvFileStatus.textContent = "No file selected";
    return;
  }

  if (file.size > MAX_CV_FILE_BYTES) {
    cvFileStatus.textContent = "File is over 5 MB";
    setStatus("offline", "CV file is too large");
    return;
  }

  setStatus("checking", "Extracting CV...");
  cvFileStatus.textContent = "Reading file...";

  try {
    localStorage.setItem("apiBaseUrl", cleanApiBaseUrl());
    const contentBase64 = await readFileAsBase64(file);
    const response = await fetch(`${cleanApiBaseUrl()}/documents/extract-text`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        filename: file.name,
        content_base64: contentBase64,
        content_type: file.type,
      }),
    });

    const payload = await response.json();
    if (!response.ok) {
      throw new Error(readApiError(payload));
    }

    form.elements.cv_text.value = payload.text;
    cvFileStatus.textContent = `${file.name} - ${payload.character_count} characters`;
    setStatus("online", "CV file loaded");
  } catch (error) {
    cvFileStatus.textContent = error.message || "CV file could not be read";
    setStatus("offline", error.message || "CV file could not be read");
  }
}

function fillSample() {
  for (const [name, value] of Object.entries(SAMPLE)) {
    form.elements[name].value = value;
  }
}

function readPayload() {
  return {
    candidate_name: form.elements.candidate_name.value.trim(),
    job_title: form.elements.job_title.value.trim(),
    company_name: form.elements.company_name.value.trim(),
    cv_text: form.elements.cv_text.value.trim(),
    job_description: form.elements.job_description.value.trim(),
    use_ai_recommendations: form.elements.use_ai_recommendations.checked,
  };
}

function cleanApiBaseUrl() {
  return apiBaseUrlInput.value.trim().replace(/\/+$/, "") || DEFAULT_API_BASE_URL;
}

function renderResult(result) {
  emptyState.classList.add("hidden");
  resultContent.classList.remove("hidden");

  setText("#resultId", `Analysis #${result.application_id}`);
  setText("#scoreValue", result.match_score);
  document.querySelector("#scoreBar").style.width = `${Math.max(0, result.match_score)}%`;
  setText("#seniorityValue", result.seniority_signal);
  setText("#aiStatus", `AI recommendations: ${formatStatus(result.ai_recommendation_status)}`);
  setText("#coverLetterStatus", `Cover letter: ${formatStatus(result.cover_letter_status)}`);
  setText("#explanation", result.explanation);
  setText("#coverLetter", result.cover_letter_draft);

  renderChips("#matchedSkills", result.matched_skills, "matched");
  renderChips("#missingSkills", result.missing_skills, "missing");
  renderChips("#extraSkills", result.extra_candidate_skills, "extra");
  renderRequirementAnalysis(result.requirement_analysis);
  renderScoreBreakdown(result.score_breakdown);
  renderPlainList("#recommendations", result.recommendations);
  renderCvRecommendations(result.cv_recommendations);
  renderWorkflowActions(result.workflow_actions);
}

function renderRequirementAnalysis(requirements) {
  renderCoverageChips(
    "#mustHaveSkills",
    requirements.must_have_skills,
    requirements.matched_must_have_skills,
    "missing",
  );
  renderCoverageChips(
    "#niceToHaveSkills",
    requirements.nice_to_have_skills,
    requirements.matched_nice_to_have_skills,
    "extra",
  );
  renderChips("#languageRequirements", requirements.language_requirements, "matched");
  renderChips("#locationRequirements", requirements.location_requirements, "extra");
  renderChips("#degreeRequirements", requirements.degree_requirements, "matched");
}

function renderCoverageChips(selector, items, matchedItems, missingVariant) {
  const container = document.querySelector(selector);
  replaceChildren(container);

  if (!items.length) {
    container.append(createElement("span", "chip empty", "None"));
    return;
  }

  const matchedSet = new Set(matchedItems);
  for (const item of items) {
    const variant = matchedSet.has(item) ? "matched" : missingVariant;
    container.append(createElement("span", `chip ${variant}`, item));
  }
}

function renderScoreBreakdown(breakdown) {
  const container = document.querySelector("#scoreBreakdown");
  replaceChildren(container);

  const items = [
    ["Must-have", `${breakdown.must_have_score}/70`],
    ["Nice-to-have", `${breakdown.nice_to_have_score}/15`],
    ["Evidence", `${breakdown.evidence_score}/10`],
    ["Adjacent", `${breakdown.adjacent_skill_score}/5`],
    ["Cap", breakdown.score_cap],
    ["Confidence", breakdown.confidence],
  ];

  for (const [label, value] of items) {
    const card = createElement("article", "score-breakdown-item");
    card.append(createElement("span", "", label), createElement("strong", "", value));
    container.append(card);
  }
}

function renderChips(selector, items, variant) {
  const container = document.querySelector(selector);
  replaceChildren(container);

  if (!items.length) {
    const chip = createElement("span", `chip empty`, "None");
    container.append(chip);
    return;
  }

  for (const item of items) {
    container.append(createElement("span", `chip ${variant}`, item));
  }
}

function renderPlainList(selector, items) {
  const container = document.querySelector(selector);
  replaceChildren(container);

  for (const item of items) {
    container.append(createElement("li", "", item));
  }
}

function renderCvRecommendations(items) {
  const container = document.querySelector("#cvRecommendations");
  replaceChildren(container);

  for (const item of items) {
    const card = createElement("article", "recommendation-card");
    const topLine = createElement("div", "card-topline");
    topLine.append(
      createElement("strong", "", item.title),
      createElement("span", `priority ${item.priority}`, item.priority),
    );

    card.append(
      topLine,
      createElement("div", "category", item.category.replaceAll("_", " ")),
      createElement("p", "", item.explanation),
      createElement("p", "", item.suggested_change),
    );

    if (item.example_bullet) {
      card.append(createElement("p", "example-bullet", item.example_bullet));
    }

    container.append(card);
  }
}

function renderWorkflowActions(items) {
  const container = document.querySelector("#workflowActions");
  replaceChildren(container);

  for (const item of items) {
    const card = createElement("article", "workflow-card");
    card.append(createElement("strong", "", item.title), createElement("p", "", item.description));
    container.append(card);
  }
}

function createElement(tagName, className = "", text = "") {
  const element = document.createElement(tagName);
  if (className) {
    element.className = className;
  }
  if (text !== "") {
    element.textContent = text;
  }
  return element;
}

function replaceChildren(element) {
  element.replaceChildren();
}

function setText(selector, value) {
  document.querySelector(selector).textContent = value;
}

function setStatus(status, message) {
  statusDot.className = `status-dot ${status === "checking" ? "" : status}`;
  statusText.textContent = message;
}

function setBusy(isBusy) {
  submitButton.disabled = isBusy;
  submitButton.textContent = isBusy ? "Analyzing..." : "Analyze CV";
}

function formatStatus(status) {
  return STATUS_LABELS[status] || status;
}

function readFileAsBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.addEventListener("load", () => {
      resolve(arrayBufferToBase64(reader.result));
    });
    reader.addEventListener("error", () => {
      reject(new Error("CV file could not be read"));
    });
    reader.readAsArrayBuffer(file);
  });
}

function arrayBufferToBase64(buffer) {
  const bytes = new Uint8Array(buffer);
  const chunkSize = 32768;
  let binary = "";

  for (let index = 0; index < bytes.length; index += chunkSize) {
    const chunk = bytes.subarray(index, index + chunkSize);
    binary += String.fromCharCode(...chunk);
  }

  return btoa(binary);
}

function readApiError(payload) {
  if (Array.isArray(payload.detail)) {
    return payload.detail.map((item) => item.msg).join(", ");
  }
  return payload.detail || "API request failed";
}

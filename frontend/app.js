const SAMPLE = {
  candidate_name: "Ada Lovelace",
  job_title: "Junior AI Backend Developer",
  company_name: "Example GmbH",
  cv_text:
    "I built Python APIs with FastAPI, PostgreSQL, Docker, REST APIs, Git and testing for backend projects.",
  job_description:
    "We need a junior developer with Python, FastAPI, PostgreSQL, Docker, REST APIs, Git, LLM experience, RAG, AWS and CI/CD.",
};

const DEFAULT_API_BASE_URL = "http://127.0.0.1:8001";

const form = document.querySelector("#analysisForm");
const sampleButton = document.querySelector("#sampleButton");
const healthButton = document.querySelector("#healthButton");
const submitButton = document.querySelector("#submitButton");
const apiBaseUrlInput = document.querySelector("#apiBaseUrl");
const statusDot = document.querySelector("#statusDot");
const statusText = document.querySelector("#statusText");
const emptyState = document.querySelector("#emptyState");
const resultContent = document.querySelector("#resultContent");

apiBaseUrlInput.value = localStorage.getItem("apiBaseUrl") || DEFAULT_API_BASE_URL;
fillSample();

sampleButton.addEventListener("click", fillSample);
healthButton.addEventListener("click", () => checkHealth());
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
  } catch {
    setStatus("offline", "API offline");
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
  setText("#aiStatus", `AI recommendations: ${result.ai_recommendation_status}`);
  setText("#explanation", result.explanation);
  setText("#coverLetter", result.cover_letter_draft);

  renderChips("#matchedSkills", result.matched_skills, "matched");
  renderChips("#missingSkills", result.missing_skills, "missing");
  renderChips("#extraSkills", result.extra_candidate_skills, "extra");
  renderPlainList("#recommendations", result.recommendations);
  renderCvRecommendations(result.cv_recommendations);
  renderWorkflowActions(result.workflow_actions);
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

function readApiError(payload) {
  if (Array.isArray(payload.detail)) {
    return payload.detail.map((item) => item.msg).join(", ");
  }
  return payload.detail || "API request failed";
}

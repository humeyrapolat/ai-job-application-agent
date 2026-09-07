const SAMPLE = {
  candidate_name: "Sample Candidate",
  job_title: "Agentic AI Engineer",
  company_name: "Sample Company",
  cv_text:
    "I built AI backend projects with Python, FastAPI, PostgreSQL, Docker, REST APIs, Git, testing, LangChain, RAG, vector databases, workflow automation, and OpenAI API integrations. I developed prototypes, automated API workflows, and documented technical findings for stakeholders.",
  job_description:
    "Requirements: Python, APIs, automation, Large Language Models, AI agents, and hands-on prototype development. Nice to have: LangChain, AutoGen, CrewAI, guardrails, RAG, and CI/CD. English fluent is required. Hybrid role in Berlin. Bachelor's degree in computer science, data science, artificial intelligence, or a related field.",
};

const DEFAULT_API_BASE_URL = "http://127.0.0.1:8001";
const MAX_CV_FILE_BYTES = 5 * 1024 * 1024;
const PDF_JS_WORKER_SRC =
  "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js";
const STATUS_LABELS = {
  demo: "browser demo",
  deterministic: "local draft",
  fallback: "safety fallback",
  generated: "AI generated",
  not_requested: "not requested",
  unavailable: "backend unavailable",
};
const SKILL_ALIASES = {
  ai: ["ai", "ai/ml", "artificial intelligence", "machine learning", "ml", "openai"],
  python: ["python", "py"],
  fastapi: ["fastapi", "fast api"],
  django: ["django"],
  flask: ["flask"],
  postgresql: ["postgresql", "postgres", "psql"],
  mysql: ["mysql"],
  sqlite: ["sqlite"],
  mongodb: ["mongodb", "mongo"],
  redis: ["redis"],
  docker: ["docker", "container", "containers"],
  kubernetes: ["kubernetes", "k8s"],
  "rest api": [
    "rest api",
    "rest apis",
    "rest endpoint",
    "rest endpoints",
    "restful",
    "api development",
    "apis",
  ],
  graphql: ["graphql"],
  neo4j: ["neo4j", "graph database", "graph databases"],
  git: ["git", "github", "gitlab"],
  "ci/cd": ["ci/cd", "github actions", "gitlab ci", "continuous integration"],
  testing: ["pytest", "unit test", "unit tests", "integration test", "testing"],
  nlp: ["nlp", "natural language processing"],
  "openai api": ["openai", "openai api", "gpt", "chatgpt"],
  llm: [
    "llm",
    "large language model",
    "large language models",
    "language model",
    "language models",
    "openai api",
    "gpt",
    "chatgpt",
  ],
  "ai agents": [
    "agentic ai",
    "ai agent",
    "ai agents",
    "agent system",
    "agent systems",
    "agent framework",
    "agent frameworks",
  ],
  automation: [
    "automation",
    "automating",
    "automated workflow",
    "automated workflows",
    "workflow automation",
  ],
  autogen: ["autogen", "auto gen"],
  crewai: ["crewai", "crew ai"],
  guardrails: ["guardrails", "nemo guardrails", "nemoguardrails"],
  openclaw: ["openclaw", "open claw"],
  rag: ["rag", "retrieval augmented generation", "vector search"],
  "vector database": ["vector database", "vector databases", "vector db", "embeddings"],
  langchain: ["langchain"],
  langgraph: ["langgraph"],
  n8n: ["n8n"],
  "power automate": ["power automate"],
  azure: ["azure", "microsoft azure"],
  aws: ["aws", "amazon web services"],
  linux: ["linux"],
  javascript: ["javascript", "js"],
  typescript: ["typescript", "ts"],
  react: ["react", "reactjs"],
};
const MUST_HAVE_TERMS = [
  "required",
  "requirement",
  "requirements",
  "must",
  "need",
  "needs",
  "looking for",
  "you bring",
  "you have",
  "proficiency",
  "strong knowledge",
  "hands-on",
  "mandatory",
  "essential",
];
const NICE_TO_HAVE_TERMS = [
  "nice to have",
  "nice-to-have",
  "preferred",
  "plus",
  "bonus",
  "desirable",
  "advantage",
  "ideally",
  "optional",
];
const LANGUAGE_ALIASES = {
  English: ["english"],
  German: ["german"],
  Turkish: ["turkish"],
  French: ["french"],
  Spanish: ["spanish"],
};
const LANGUAGE_LEVEL_ORDER = {
  a1: 1,
  a2: 2,
  b1: 3,
  b2: 4,
  c1: 5,
  c2: 6,
};
const LOCATION_ALIASES = {
  Remote: ["remote"],
  Hybrid: ["hybrid"],
  "On-site": ["on-site", "onsite", "on site"],
  Germany: ["germany"],
  Berlin: ["berlin"],
  Munich: ["munich"],
  Hamburg: ["hamburg"],
  Cologne: ["cologne"],
  Frankfurt: ["frankfurt"],
  Dusseldorf: ["dusseldorf"],
  Stuttgart: ["stuttgart"],
};
const DEGREE_PATTERNS = [
  [/(\bbachelor'?s?\b|\bbsc\b)/i, "Bachelor's degree"],
  [/(\bmaster'?s?\b|\bmsc\b)/i, "Master's degree"],
  [
    /\b(computer science|informatics|software engineering|data science|artificial intelligence)\b/i,
    "Computer science or related field",
  ],
  [/\b(university degree|academic degree|degree)\b/i, "University degree"],
];

const form = document.querySelector("#analysisForm");
const sampleButton = document.querySelector("#sampleButton");
const submitButton = document.querySelector("#submitButton");
const apiBaseUrlInput = document.querySelector("#apiBaseUrl");
const cvFileInput = document.querySelector("#cvFile");
const cvFileStatus = document.querySelector("#cvFileStatus");
const uploadZone = document.querySelector(".upload-zone");
const statusDot = document.querySelector("#statusDot");
const statusText = document.querySelector("#statusText");
const emptyState = document.querySelector("#emptyState");
const resultContent = document.querySelector("#resultContent");

let serviceAvailable = false;

configurePdfJs();
apiBaseUrlInput.value = localStorage.getItem("apiBaseUrl") || DEFAULT_API_BASE_URL;

sampleButton.addEventListener("click", fillSample);
cvFileInput.addEventListener("change", () => handleCvFileChange());
apiBaseUrlInput.addEventListener("change", () => {
  localStorage.setItem("apiBaseUrl", cleanApiBaseUrl());
  checkHealth();
});
checkHealth();

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  setBusy(true);
  setStatus("checking", "Analyzing...");

  let payload;
  try {
    payload = readPayload();
  } catch (error) {
    setStatus("offline", error.message || "Complete the scan inputs");
    setBusy(false);
    return;
  }

  try {
    const result = await analyzeWithBackend(payload);
    renderResult(result);
    setStatus("online", "Service ready");
  } catch (error) {
    renderResult(buildBrowserDemoResult(payload));
    setStatus("demo", "Demo result");
  } finally {
    setBusy(false);
  }
});

async function checkHealth() {
  setStatus("checking", "Checking service");
  try {
    localStorage.setItem("apiBaseUrl", cleanApiBaseUrl());
    const response = await fetch(`${cleanApiBaseUrl()}/health`);
    if (!response.ok) {
      throw new Error("Service health check failed");
    }
    serviceAvailable = true;
    setStatus("online", "Service ready");
  } catch (error) {
    serviceAvailable = false;
    setStatus("demo", "Demo ready");
  }
}

async function handleCvFileChange() {
  const file = cvFileInput.files[0];
  if (!file) {
    form.elements.cv_text.value = "";
    cvFileStatus.textContent = "Upload one PDF CV";
    uploadZone.classList.remove("is-ready");
    return;
  }

  if (!isPdfFile(file)) {
    cvFileInput.value = "";
    form.elements.cv_text.value = "";
    cvFileStatus.textContent = "PDF only";
    uploadZone.classList.remove("is-ready");
    setStatus("offline", "Please upload a PDF CV");
    return;
  }

  if (file.size > MAX_CV_FILE_BYTES) {
    cvFileStatus.textContent = "File is over 5 MB";
    setStatus("offline", "CV file is too large");
    return;
  }

  setStatus("checking", "Reading CV...");
  cvFileStatus.textContent = "Reading file...";

  try {
    const text = await extractCvText(file);
    form.elements.cv_text.value = text;
    autofillCandidateName(text, file.name);
    cvFileStatus.textContent = `${file.name} ready`;
    uploadZone.classList.add("is-ready");
    setStatus(serviceAvailable ? "online" : "demo", "CV ready");
  } catch (error) {
    form.elements.cv_text.value = "";
    uploadZone.classList.remove("is-ready");
    cvFileStatus.textContent = error.message || "CV file could not be read";
    setStatus("offline", error.message || "CV file could not be read");
  }
}

async function extractCvText(file) {
  try {
    return await extractPdfTextInBrowser(file);
  } catch (browserError) {
    if (!serviceAvailable) {
      throw new Error("This PDF could not be read in demo mode. Try the sample demo.");
    }
  }

  return extractPdfTextWithBackend(file);
}

async function extractPdfTextInBrowser(file) {
  if (!window.pdfjsLib) {
    throw new Error("Browser PDF reader is unavailable");
  }

  const arrayBuffer = await file.arrayBuffer();
  const loadingTask = window.pdfjsLib.getDocument({ data: arrayBuffer });
  const document = await loadingTask.promise;
  const pages = [];

  for (let pageNumber = 1; pageNumber <= document.numPages; pageNumber += 1) {
    const page = await document.getPage(pageNumber);
    const content = await page.getTextContent();
    const pageText = content.items.map((item) => item.str || "").join(" ");
    pages.push(pageText);
  }

  const text = cleanExtractedText(pages.join("\n"));
  if (text.length < 20) {
    throw new Error("The CV file did not contain enough readable text to analyze.");
  }

  return text;
}

async function extractPdfTextWithBackend(file) {
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

  return payload.text;
}

async function analyzeWithBackend(payload) {
  localStorage.setItem("apiBaseUrl", cleanApiBaseUrl());
  const response = await fetch(`${cleanApiBaseUrl()}/applications/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const result = await response.json();
  if (!response.ok) {
    throw new Error(readApiError(result));
  }

  serviceAvailable = true;
  return result;
}

function fillSample() {
  for (const [name, value] of Object.entries(SAMPLE)) {
    form.elements[name].value = value;
  }
  cvFileInput.value = "";
  cvFileStatus.textContent = "Sample CV loaded";
  uploadZone.classList.add("is-ready");
  setStatus(serviceAvailable ? "online" : "demo", "Sample ready");
}

function autofillCandidateName(cvText, filename = "") {
  if (form.elements.candidate_name.value.trim()) {
    return;
  }

  const candidateName = guessCandidateName(cvText) || guessCandidateNameFromFileName(filename);
  if (candidateName) {
    form.elements.candidate_name.value = candidateName;
  }
}

function guessCandidateName(cvText) {
  const lines = cvText
    .split(/\r?\n/)
    .map((line) => line.replace(/\s+/g, " ").trim())
    .filter(Boolean)
    .slice(0, 18);

  for (const line of lines) {
    const candidateName = normalizeNameLine(line);
    if (looksLikePersonName(candidateName)) {
      return candidateName;
    }
  }

  return "";
}

function guessCandidateNameFromFileName(filename) {
  const cleaned = filename
    .normalize("NFC")
    .replace(/\.[^.]+$/g, "")
    .replace(/[_-]+/g, " ")
    .replace(/\b(cv|resume|lebenslauf|final|upload|max\d+mb)\b/gi, " ")
    .replace(/\s+/g, " ")
    .trim();

  return looksLikePersonName(cleaned) ? cleaned : "";
}

function normalizeNameLine(line) {
  return line.replace(/[|,:;]+$/g, "").trim();
}

function looksLikePersonName(line) {
  const lower = line.toLowerCase();
  const blockedWords = [
    "address",
    "contact",
    "curriculum",
    "deutsch",
    "education",
    "email",
    "english",
    "experience",
    "github",
    "linkedin",
    "location",
    "portfolio",
    "profile",
    "resume",
    "skills",
    "summary",
    "telefon",
    "phone",
    "vitae",
  ];

  if (
    line.length < 3 ||
    line.length > 60 ||
    /[@:/\\0-9]/.test(line) ||
    blockedWords.some((word) => lower.includes(word))
  ) {
    return false;
  }

  const words = line.split(" ");
  if (words.length < 2 || words.length > 5) {
    return false;
  }

  return words.every((word) => /^[\p{L}][\p{L}'’.-]{1,}$/u.test(word));
}

function readPayload() {
  const cvText = form.elements.cv_text.value.trim();
  if (cvText.length < 20) {
    throw new Error("Upload a readable PDF CV before running the ATS scan");
  }

  return {
    candidate_name: form.elements.candidate_name.value.trim(),
    job_title: form.elements.job_title.value.trim(),
    company_name: form.elements.company_name.value.trim(),
    cv_text: cvText,
    job_description: form.elements.job_description.value.trim(),
    use_ai_recommendations: form.elements.use_ai_recommendations.checked,
  };
}

function buildBrowserDemoResult(payload) {
  const cvSkills = extractSkills(payload.cv_text);
  const jobText = `${payload.job_title}\n${payload.job_description}`;
  const jobSkills = extractSkills(jobText);
  const requirementAnalysis = analyzeJobRequirements({
    jobTitle: payload.job_title,
    jobDescription: payload.job_description,
    cvSkills,
  });
  const matchedSkills = sortItems(intersection(cvSkills, jobSkills));
  const missingSkills = sortItems(difference(jobSkills, cvSkills));
  const extraCandidateSkills = sortItems(difference(cvSkills, jobSkills));
  const scoreBreakdown = calculateScoreBreakdown({
    requirementAnalysis,
    matchedSkills: new Set(matchedSkills),
    extraCandidateSkills: new Set(extraCandidateSkills),
    cvText: payload.cv_text,
  });
  const matchScore = Math.min(
    scoreBreakdown.score_cap,
    scoreBreakdown.hard_requirement_score +
      scoreBreakdown.technical_score +
      scoreBreakdown.preferred_score +
      scoreBreakdown.evidence_score +
      scoreBreakdown.adjacent_skill_score,
  );

  return {
    application_id: "Demo",
    candidate_name: payload.candidate_name,
    job_title: payload.job_title,
    company_name: payload.company_name,
    match_score: matchScore,
    seniority_signal: requirementAnalysis.seniority,
    matched_skills: matchedSkills,
    missing_skills: missingSkills,
    extra_candidate_skills: extraCandidateSkills,
    requirement_analysis: requirementAnalysis,
    score_breakdown: scoreBreakdown,
    recommendations: buildRecommendations({
      matchScore,
      missingSkills,
      extraCandidateSkills,
      requirementAnalysis,
      scoreBreakdown,
    }),
    cv_recommendations: buildCvRecommendations({
      jobTitle: payload.job_title,
      matchScore,
      matchedSkills,
      missingSkills,
      cvText: payload.cv_text,
    }),
    ai_recommendation_status: "demo",
    cover_letter_draft: buildCoverLetter({
      candidateName: payload.candidate_name,
      jobTitle: payload.job_title,
      companyName: payload.company_name,
      matchScore,
      matchedSkills,
      missingSkills,
      extraCandidateSkills,
    }),
    cover_letter_status: "deterministic",
    workflow_actions: buildWorkflowActions({ matchScore, missingSkills }),
    explanation: explainScore({
      matchScore,
      requirementAnalysis,
      scoreBreakdown,
    }),
  };
}

function analyzeJobRequirements({ jobTitle, jobDescription, cvSkills }) {
  const jobText = `${jobTitle}\n${jobDescription}`;
  const jobSkills = extractSkills(jobText);
  const [mustHaveSkills, niceToHaveSkills] = classifyJobSkills(jobDescription, jobSkills);
  const matchedMustHaveSkills = sortItems(intersection(mustHaveSkills, cvSkills));
  const missingMustHaveSkills = sortItems(difference(mustHaveSkills, cvSkills));
  const matchedNiceToHaveSkills = sortItems(intersection(niceToHaveSkills, cvSkills));
  const missingNiceToHaveSkills = sortItems(difference(niceToHaveSkills, cvSkills));

  return {
    must_have_skills: sortItems(mustHaveSkills),
    nice_to_have_skills: sortItems(niceToHaveSkills),
    matched_must_have_skills: matchedMustHaveSkills,
    missing_must_have_skills: missingMustHaveSkills,
    matched_nice_to_have_skills: matchedNiceToHaveSkills,
    missing_nice_to_have_skills: missingNiceToHaveSkills,
    language_requirements: extractLanguageRequirements(jobText),
    location_requirements: extractLocationRequirements(jobText),
    degree_requirements: extractDegreeRequirements(jobText),
    seniority: inferSeniority(jobTitle, jobDescription),
  };
}

function classifyJobSkills(jobDescription, jobSkills) {
  const mustHaveSkills = new Set();
  const niceToHaveSkills = new Set();

  for (const fragment of splitRequirementFragments(jobDescription)) {
    const fragmentSkills = intersection(extractSkills(fragment), jobSkills);
    if (!fragmentSkills.size) {
      continue;
    }

    if (containsAny(fragment, NICE_TO_HAVE_TERMS)) {
      addAll(niceToHaveSkills, fragmentSkills);
    } else {
      addAll(mustHaveSkills, fragmentSkills);
    }
  }

  addAll(mustHaveSkills, difference(jobSkills, union(mustHaveSkills, niceToHaveSkills)));
  return [mustHaveSkills, difference(niceToHaveSkills, mustHaveSkills)];
}

function calculateScoreBreakdown({
  requirementAnalysis,
  matchedSkills,
  extraCandidateSkills,
  cvText,
}) {
  const detectedSkillCount =
    requirementAnalysis.must_have_skills.length + requirementAnalysis.nice_to_have_skills.length;
  const hardRequirementScore = hardRequirementScoreFor(requirementAnalysis, cvText);
  const confidence = scoreConfidence({
    detectedSkillCount,
    hardRequirementCount: hardRequirementCount(requirementAnalysis),
  });

  return {
    hard_requirement_score: hardRequirementScore,
    technical_score: technicalScore(requirementAnalysis),
    preferred_score: preferredScore(requirementAnalysis),
    evidence_score: evidenceScore(cvText, matchedSkills),
    adjacent_skill_score: adjacentSkillScore({ requirementAnalysis, extraCandidateSkills }),
    score_cap: scoreCapForRequirementAnalysis({
      requirementAnalysis,
      hardRequirementScore,
      confidence,
    }),
    confidence,
  };
}

function hardRequirementScoreFor(requirementAnalysis, cvText) {
  const checks = hardRequirementChecks(requirementAnalysis, cvText);
  if (!checks.length) {
    return 20;
  }

  return coverageScore({
    matchedCount: checks.filter(Boolean).length,
    totalCount: checks.length,
    maxScore: 20,
  });
}

function hardRequirementChecks(requirementAnalysis, cvText) {
  return [
    ...requirementAnalysis.language_requirements.map((requirement) =>
      matchesLanguageRequirement(requirement, cvText),
    ),
    ...requirementAnalysis.location_requirements.map((requirement) =>
      matchesLocationRequirement(requirement, cvText),
    ),
    ...requirementAnalysis.degree_requirements.map((requirement) =>
      matchesDegreeRequirement(requirement, cvText),
    ),
  ];
}

function hardRequirementCount(requirementAnalysis) {
  return (
    requirementAnalysis.language_requirements.length +
    requirementAnalysis.location_requirements.length +
    requirementAnalysis.degree_requirements.length
  );
}

function technicalScore(requirementAnalysis) {
  const mustHaveCount = requirementAnalysis.must_have_skills.length;
  if (!mustHaveCount) {
    return coverageScore({
      matchedCount: requirementAnalysis.matched_nice_to_have_skills.length,
      totalCount: requirementAnalysis.nice_to_have_skills.length,
      maxScore: 28,
    });
  }

  return coverageScore({
    matchedCount: requirementAnalysis.matched_must_have_skills.length,
    totalCount: mustHaveCount,
    maxScore: technicalScoreCeiling(mustHaveCount),
  });
}

function technicalScoreCeiling(mustHaveCount) {
  if (mustHaveCount <= 2) {
    return 28;
  }
  if (mustHaveCount === 3) {
    return 36;
  }
  return 45;
}

function preferredScore(requirementAnalysis) {
  const niceToHaveCount = requirementAnalysis.nice_to_have_skills.length;
  if (!niceToHaveCount) {
    return 15;
  }

  return coverageScore({
    matchedCount: requirementAnalysis.matched_nice_to_have_skills.length,
    totalCount: niceToHaveCount,
    maxScore: 15,
  });
}

function evidenceScore(cvText, matchedSkills) {
  if (!matchedSkills.size) {
    return 0;
  }

  let score = 0;
  if (mentionsExperience(cvText)) {
    score += 5;
  }
  if (mentionsImpact(cvText)) {
    score += 5;
  }
  if (matchedSkills.size >= 3) {
    score += 5;
  } else {
    score += 2;
  }

  return score;
}

function adjacentSkillScore({ requirementAnalysis, extraCandidateSkills }) {
  if (!requirementAnalysis.matched_must_have_skills.length) {
    return 0;
  }

  let maxAdjacentScore = 5;
  if (requirementAnalysis.must_have_skills.length <= 2) {
    maxAdjacentScore = 3;
  }
  if (requirementAnalysis.missing_must_have_skills.length) {
    maxAdjacentScore = 2;
  }

  return Math.min(extraCandidateSkills.size, maxAdjacentScore);
}

function scoreCapForRequirementAnalysis({ requirementAnalysis, hardRequirementScore, confidence }) {
  const skillCount =
    requirementAnalysis.must_have_skills.length + requirementAnalysis.nice_to_have_skills.length;
  const caps = [100];

  if (skillCount === 0) {
    caps.push(50);
  } else if (confidence === "low") {
    caps.push(72);
  } else if (confidence === "medium") {
    caps.push(skillCount <= 4 ? 92 : 95);
  }

  if (hardRequirementScore < 20) {
    caps.push(78);
  }

  if (requirementAnalysis.missing_must_have_skills.length) {
    caps.push(82);
  }

  return Math.min(...caps);
}

function scoreConfidence({ detectedSkillCount, hardRequirementCount: requirementCount }) {
  const measurableSignalCount = detectedSkillCount + requirementCount;
  if (measurableSignalCount <= 2) {
    return "low";
  }
  if (measurableSignalCount <= 5) {
    return "medium";
  }
  return "high";
}

function buildRecommendations({
  matchScore,
  missingSkills,
  extraCandidateSkills,
  requirementAnalysis,
  scoreBreakdown,
}) {
  const recommendations = [];

  if (matchScore >= 80) {
    recommendations.push("Apply after tailoring the CV summary to this role.");
  } else if (matchScore >= 65) {
    recommendations.push("Apply, but improve the CV bullets around the missing skills.");
  } else {
    recommendations.push("Consider learning the top missing skills before applying.");
  }

  if (scoreBreakdown.hard_requirement_score < 20) {
    recommendations.push(
      "Verify hard requirements such as language, degree, location, or seniority before applying.",
    );
  }

  if (missingSkills.length) {
    recommendations.push(`Add project evidence for: ${missingSkills.slice(0, 3).join(", ")}.`);
  }

  if (scoreBreakdown.confidence === "low") {
    recommendations.push(
      "Treat this score as directional because the job description exposed only a small number of measurable requirements.",
    );
  }

  if (requirementAnalysis.missing_must_have_skills.length) {
    recommendations.push(
      `Prioritize must-have gaps first: ${requirementAnalysis.missing_must_have_skills
        .slice(0, 3)
        .join(", ")}.`,
    );
  }

  if (extraCandidateSkills.length) {
    recommendations.push(
      `Mention related strengths if relevant: ${extraCandidateSkills.slice(0, 3).join(", ")}.`,
    );
  }

  return recommendations;
}

function buildCvRecommendations({ jobTitle, matchScore, matchedSkills, missingSkills, cvText }) {
  const recommendations = [];

  if (missingSkills.length) {
    recommendations.push({
      category: "keyword_optimization",
      priority: matchScore < 65 ? "high" : "medium",
      title: "Add evidence for missing role keywords",
      explanation: "The job description mentions skills that are not clearly supported by the CV.",
      suggested_change: `If you have real evidence, add a project bullet for: ${missingSkills
        .slice(0, 3)
        .join(", ")}.`,
      example_bullet: null,
    });
  }

  if (matchedSkills.length) {
    recommendations.push({
      category: "project_evidence",
      priority: "medium",
      title: "Move the strongest matching skills closer to the top",
      explanation: "Recruiters often scan the profile summary and first project bullets first.",
      suggested_change: `Mention the most relevant matched skills near the profile summary or first project for the ${jobTitle} role.`,
      example_bullet: `Developed a practical project with ${matchedSkills
        .slice(0, 4)
        .join(", ")}, focusing on reliable implementation and clear delivery.`,
    });
  }

  if (!mentionsImpact(cvText)) {
    recommendations.push({
      category: "impact_framing",
      priority: "medium",
      title: "Rewrite technical bullets with clearer impact",
      explanation:
        "The CV lists technical skills, but stronger bullets should show what was built, improved, automated, or measured.",
      suggested_change: "Use action-and-result bullets instead of only listing technologies.",
      example_bullet:
        "Built an AI workflow prototype with measurable scope, clear API boundaries, and documented implementation decisions.",
    });
  }

  if (matchScore < 65) {
    recommendations.push({
      category: "application_decision",
      priority: "high",
      title: "Strengthen the CV before applying",
      explanation: "The score is below the recommended threshold for a strong application.",
      suggested_change: "Improve the CV around the top missing skills before sending it.",
      example_bullet: null,
    });
  } else if (matchScore >= 80) {
    recommendations.push({
      category: "application_decision",
      priority: "low",
      title: "Tailor the summary before applying",
      explanation: "The CV already matches many role requirements.",
      suggested_change:
        "Adjust the profile summary and first project bullet to mirror the role's strongest keywords.",
      example_bullet: null,
    });
  }

  return recommendations;
}

function buildCoverLetter({
  candidateName,
  jobTitle,
  companyName,
  matchScore,
  matchedSkills,
  missingSkills,
  extraCandidateSkills,
}) {
  const strengths = formatHumanSkillList(matchedSkills.slice(0, 5)) || "AI and backend projects";
  const adjacentStrengths = formatHumanSkillList(extraCandidateSkills.slice(0, 4));
  const readinessSentence = buildReadinessSentence({ matchScore, missingSkills });
  const adjacentSentence = adjacentStrengths
    ? ` I can also bring adjacent experience in ${adjacentStrengths}, where relevant.`
    : "";

  return (
    `Dear ${companyName} team,\n\n` +
    `I am applying for the ${jobTitle} role because it aligns with my hands-on interest in ${strengths}.\n\n` +
    `My recent work includes practical project experience with ${strengths}. This background would help me contribute to implementation, clear API workflows, and reliable delivery for ${companyName}.${adjacentSentence}\n\n` +
    `${readinessSentence}\n\n` +
    `Thank you for considering my application. I would be glad to discuss how my AI automation and backend experience can support the ${companyName} team.\n\n` +
    `Best regards,\n${candidateName}`
  );
}

function buildReadinessSentence({ matchScore, missingSkills }) {
  if (missingSkills.length) {
    return `For the areas around ${formatHumanSkillList(
      missingSkills.slice(0, 3),
    )}, I would connect focused learning with concrete project evidence before presenting them as core strengths.`;
  }

  if (matchScore >= 80) {
    return "Because the core requirements are well aligned with my current profile, I would tailor the first project bullets to the role's priorities.";
  }

  return "The current overlap gives me a practical starting point, and I would strengthen the role-specific evidence before submitting the final application.";
}

function buildWorkflowActions({ matchScore, missingSkills }) {
  const actions = [
    {
      kind: "status_update",
      title: "Create application tracker entry",
      description: "Store this analysis result in the application tracking board.",
      payload: {},
    },
    {
      kind: "email_draft",
      title: "Prepare cover letter email",
      description: "Create a draft email that the candidate can review before sending.",
      payload: {},
    },
  ];

  if (matchScore < 70 || missingSkills.length) {
    actions.push({
      kind: "learning_plan",
      title: "Create focused improvement plan",
      description: "Prioritize the most important missing skills before applying.",
      payload: {},
    });
  }

  return actions;
}

function explainScore({ matchScore, requirementAnalysis, scoreBreakdown }) {
  let explanation =
    `The ATS compatibility score is ${matchScore}/100 using recruiter-weighted signals: ` +
    "hard requirements, required technical skills, preferred skills, CV evidence, and adjacent strengths. " +
    `Required technical coverage is ${requirementAnalysis.matched_must_have_skills.length}/` +
    `${requirementAnalysis.must_have_skills.length} and preferred coverage is ` +
    `${requirementAnalysis.matched_nice_to_have_skills.length}/` +
    `${requirementAnalysis.nice_to_have_skills.length}.`;

  if (scoreBreakdown.score_cap < 100) {
    explanation += ` Confidence is ${scoreBreakdown.confidence}, so the score is capped at ${scoreBreakdown.score_cap} instead of treated as a perfect fit.`;
  }

  return explanation;
}

function extractSkills(text) {
  const normalized = normalizeSkillText(text);
  const found = new Set();

  for (const [skill, aliases] of Object.entries(SKILL_ALIASES)) {
    if (aliases.some((alias) => containsAlias(normalized, alias))) {
      found.add(skill);
    }
  }

  return found;
}

function extractLanguageRequirements(text) {
  const requirements = [];

  for (const fragment of splitRequirementFragments(text)) {
    for (const [language, aliases] of Object.entries(LANGUAGE_ALIASES)) {
      if (aliases.some((alias) => languageAliasMatches(fragment, alias))) {
        requirements.push(formatLanguageRequirement(language, fragment));
      }
    }
  }

  return uniqueSorted(requirements);
}

function formatLanguageRequirement(language, fragment) {
  const levelMatch = fragment.match(
    /\b(business fluent|professional|fluent|native|a1|a2|b1|b2|c1|c2)\b/i,
  );
  if (!levelMatch) {
    return language;
  }

  const level = levelMatch[1].toLowerCase();
  return `${language} ${level.length === 2 ? level.toUpperCase() : level}`;
}

function extractLocationRequirements(text) {
  const lowered = text.toLowerCase();
  const locations = Object.entries(LOCATION_ALIASES)
    .filter(([, aliases]) => aliases.some((alias) => lowered.includes(alias)))
    .map(([location]) => location);

  return uniqueSorted(locations);
}

function extractDegreeRequirements(text) {
  return uniqueSorted(
    DEGREE_PATTERNS.filter(([pattern]) => pattern.test(text)).map(([, label]) => label),
  );
}

function inferSeniority(jobTitle, jobDescription = "") {
  const loweredTitle = jobTitle.toLowerCase();
  const loweredText = `${jobTitle}\n${jobDescription}`.toLowerCase();
  const studentTerms = ["working student", "werkstudent", "internship", "intern", "trainee"];

  if (studentTerms.some((term) => loweredTitle.includes(term))) {
    return "student";
  }
  if (["junior", "entry level", "graduate"].some((term) => loweredTitle.includes(term))) {
    return "junior";
  }
  if (["senior", "lead", "principal", "staff"].some((term) => loweredTitle.includes(term))) {
    return "senior";
  }

  if (studentTerms.some((term) => loweredText.includes(term))) {
    return "student";
  }
  if (["junior", "entry level", "graduate"].some((term) => loweredText.includes(term))) {
    return "junior";
  }
  if (["senior", "lead", "principal", "staff"].some((term) => loweredText.includes(term))) {
    return "senior";
  }
  if (["mid", "professional", "2+ years", "3+ years"].some((term) => loweredText.includes(term))) {
    return "mid";
  }
  return "unknown";
}

function matchesLanguageRequirement(requirement, cvText) {
  const [language, ...parts] = requirement.toLowerCase().split(" ");
  if (!containsTerm(cvText, language)) {
    return false;
  }

  const requiredLevel = parts.find((part) => LANGUAGE_LEVEL_ORDER[part]);
  if (!requiredLevel) {
    return true;
  }

  const cvLevel = findLanguageLevel(cvText, language);
  return Boolean(cvLevel) && LANGUAGE_LEVEL_ORDER[cvLevel] >= LANGUAGE_LEVEL_ORDER[requiredLevel];
}

function findLanguageLevel(text, language) {
  const match = text.match(new RegExp(`(?<![a-z0-9])${escapeRegExp(language)}(?![a-z0-9]).{0,32}`, "i"));
  if (!match) {
    return "";
  }

  const levelMatch = match[0].match(/\b(a1|a2|b1|b2|c1|c2|native|fluent|professional)\b/i);
  if (!levelMatch) {
    return "";
  }

  return normalizeLanguageLevel(levelMatch[1]);
}

function normalizeLanguageLevel(level) {
  const normalized = level.toLowerCase();
  if (normalized === "native") {
    return "c2";
  }
  if (normalized === "fluent" || normalized === "professional") {
    return "c1";
  }
  return normalized;
}

function matchesLocationRequirement(requirement, cvText) {
  const loweredRequirement = requirement.toLowerCase();
  if (["remote", "hybrid", "on-site"].includes(loweredRequirement)) {
    return true;
  }

  return containsTerm(cvText, loweredRequirement);
}

function matchesDegreeRequirement(requirement, cvText) {
  const loweredRequirement = requirement.toLowerCase();
  const loweredCv = cvText.toLowerCase();

  if (loweredRequirement.includes("bachelor")) {
    return ["bachelor", "master", "degree"].some((term) => loweredCv.includes(term));
  }
  if (loweredRequirement.includes("master")) {
    return loweredCv.includes("master");
  }
  if (loweredRequirement.includes("computer science")) {
    return [
      "computer science",
      "informatics",
      "software engineering",
      "data science",
      "artificial intelligence",
    ].some((term) => loweredCv.includes(term));
  }
  if (loweredRequirement.includes("degree")) {
    return ["bachelor", "master", "degree", "university"].some((term) =>
      loweredCv.includes(term),
    );
  }

  return containsTerm(cvText, loweredRequirement);
}

function coverageScore({ matchedCount, totalCount, maxScore }) {
  if (!totalCount) {
    return 0;
  }
  return Math.round((matchedCount / totalCount) * maxScore);
}

function mentionsExperience(text) {
  const lowered = text.toLowerCase();
  return ["experience", "project", "built", "developed", "implemented", "prototype"].some((term) =>
    lowered.includes(term),
  );
}

function mentionsImpact(text) {
  const lowered = text.toLowerCase();
  return [
    "improved",
    "reduced",
    "increased",
    "automated",
    "optimized",
    "measured",
    "deployed",
    "%",
  ].some((term) => lowered.includes(term));
}

function splitRequirementFragments(text) {
  return text
    .split(/[\n.;•]+/)
    .map((fragment) => fragment.trim())
    .filter(Boolean);
}

function containsAny(text, terms) {
  const lowered = text.toLowerCase();
  return terms.some((term) => lowered.includes(term));
}

function normalizeSkillText(text) {
  return text.toLowerCase().replace(/[^a-z0-9+#./ -]+/g, " ");
}

function containsAlias(text, alias) {
  return new RegExp(`(?<![a-z0-9])${escapeRegExp(alias.toLowerCase())}(?![a-z0-9])`).test(text);
}

function languageAliasMatches(fragment, alias) {
  return new RegExp(`(?<![a-z0-9])${escapeRegExp(alias)}(?![a-z0-9])`, "i").test(fragment);
}

function containsTerm(text, term) {
  return new RegExp(`(?<![a-z0-9])${escapeRegExp(term.toLowerCase())}(?![a-z0-9])`).test(
    text.toLowerCase(),
  );
}

function cleanApiBaseUrl() {
  return apiBaseUrlInput.value.trim().replace(/\/+$/, "") || DEFAULT_API_BASE_URL;
}

function renderResult(result) {
  emptyState.classList.add("hidden");
  resultContent.classList.remove("hidden");

  setText("#resultId", result.application_id === "Demo" ? "Demo result" : `Analysis #${result.application_id}`);
  setText("#scoreValue", result.match_score);
  document.querySelector("#scoreBar").style.width = `${Math.max(0, result.match_score)}%`;
  setText("#seniorityValue", result.seniority_signal);
  setText("#aiStatus", `Recommendations: ${formatStatus(result.ai_recommendation_status)}`);
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
    ["Hard reqs", `${breakdown.hard_requirement_score}/20`],
    ["Required skills", `${breakdown.technical_score}/45`],
    ["Preferred", `${breakdown.preferred_score}/15`],
    ["Evidence", `${breakdown.evidence_score}/15`],
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

function configurePdfJs() {
  if (window.pdfjsLib?.GlobalWorkerOptions) {
    window.pdfjsLib.GlobalWorkerOptions.workerSrc = PDF_JS_WORKER_SRC;
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
  submitButton.textContent = isBusy ? "Running ATS scan..." : "Run ATS scan";
}

function formatStatus(status) {
  return STATUS_LABELS[status] || status;
}

function isPdfFile(file) {
  return file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf");
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
  return payload.detail || "Service request failed";
}

function cleanExtractedText(text) {
  return text
    .split(/\r?\n/)
    .map((line) => line.replace(/\s+/g, " ").trim())
    .filter(Boolean)
    .join("\n")
    .trim();
}

function intersection(firstSet, secondSet) {
  return new Set([...firstSet].filter((item) => secondSet.has(item)));
}

function difference(firstSet, secondSet) {
  return new Set([...firstSet].filter((item) => !secondSet.has(item)));
}

function union(firstSet, secondSet) {
  return new Set([...firstSet, ...secondSet]);
}

function addAll(targetSet, sourceSet) {
  for (const item of sourceSet) {
    targetSet.add(item);
  }
}

function uniqueSorted(items) {
  return sortItems(new Set(items));
}

function sortItems(items) {
  return [...items].sort((first, second) => first.localeCompare(second));
}

function formatHumanList(items) {
  if (!items.length) {
    return "";
  }
  if (items.length === 1) {
    return items[0];
  }
  if (items.length === 2) {
    return `${items[0]} and ${items[1]}`;
  }
  return `${items.slice(0, -1).join(", ")}, and ${items.at(-1)}`;
}

function formatHumanSkillList(skills) {
  return formatHumanList(skills.map((skill) => formatSkillLabel(skill)));
}

function formatSkillLabel(skill) {
  const displayNames = {
    ai: "AI",
    "ai agents": "AI agents",
    autogen: "AutoGen",
    automation: "automation",
    aws: "AWS",
    azure: "Azure",
    "ci/cd": "CI/CD",
    crewai: "CrewAI",
    docker: "Docker",
    fastapi: "FastAPI",
    git: "Git",
    guardrails: "guardrails",
    javascript: "JavaScript",
    langchain: "LangChain",
    langgraph: "LangGraph",
    llm: "LLM",
    neo4j: "Neo4j",
    nlp: "NLP",
    "openai api": "OpenAI API",
    openclaw: "OpenClaw",
    postgresql: "PostgreSQL",
    python: "Python",
    rag: "RAG",
    react: "React",
    "rest api": "REST APIs",
    sqlite: "SQLite",
    testing: "testing",
    typescript: "TypeScript",
    "vector database": "vector databases",
  };
  return displayNames[skill] || skill;
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

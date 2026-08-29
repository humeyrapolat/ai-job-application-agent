import re

from app.domain.schemas import JobRequirementAnalysis
from app.services.skills import extract_skills

MUST_HAVE_TERMS = (
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
)

NICE_TO_HAVE_TERMS = (
    "nice to have",
    "nice-to-have",
    "preferred",
    "plus",
    "bonus",
    "desirable",
    "advantage",
    "ideally",
    "optional",
)

LANGUAGE_ALIASES = {
    "English": ("english",),
    "German": ("german", "deutsch"),
    "Turkish": ("turkish", "türkisch"),
    "French": ("french", "französisch"),
    "Spanish": ("spanish", "spanisch"),
}

LANGUAGE_LEVEL_PATTERN = re.compile(
    r"\b(business fluent|professional|fluent|native|a1|a2|b1|b2|c1|c2)\b",
    re.IGNORECASE,
)

LOCATION_ALIASES = {
    "Remote": ("remote", "home office", "home-office"),
    "Hybrid": ("hybrid",),
    "On-site": ("on-site", "onsite", "on site"),
    "Germany": ("germany", "deutschland"),
    "Berlin": ("berlin",),
    "Munich": ("munich", "münchen"),
    "Hamburg": ("hamburg",),
    "Cologne": ("cologne", "köln"),
    "Frankfurt": ("frankfurt",),
    "Dusseldorf": ("dusseldorf", "düsseldorf"),
    "Stuttgart": ("stuttgart",),
}

DEGREE_PATTERNS = (
    (re.compile(r"\bbachelor'?s?\b", re.IGNORECASE), "Bachelor's degree"),
    (re.compile(r"\bmaster'?s?\b", re.IGNORECASE), "Master's degree"),
    (
        re.compile(r"\b(computer science|informatics|software engineering)\b", re.IGNORECASE),
        "Computer science or related field",
    ),
    (
        re.compile(r"\b(university degree|academic degree|degree)\b", re.IGNORECASE),
        "University degree",
    ),
)


def analyze_job_requirements(
    *,
    job_title: str,
    job_description: str,
    cv_skills: set[str],
) -> JobRequirementAnalysis:
    job_text = f"{job_title}\n{job_description}"
    job_skills = extract_skills(job_text)
    must_have_skills, nice_to_have_skills = _classify_job_skills(job_description, job_skills)

    matched_must_have_skills = sorted(must_have_skills & cv_skills)
    missing_must_have_skills = sorted(must_have_skills - cv_skills)
    matched_nice_to_have_skills = sorted(nice_to_have_skills & cv_skills)
    missing_nice_to_have_skills = sorted(nice_to_have_skills - cv_skills)

    return JobRequirementAnalysis(
        must_have_skills=sorted(must_have_skills),
        nice_to_have_skills=sorted(nice_to_have_skills),
        matched_must_have_skills=matched_must_have_skills,
        missing_must_have_skills=missing_must_have_skills,
        matched_nice_to_have_skills=matched_nice_to_have_skills,
        missing_nice_to_have_skills=missing_nice_to_have_skills,
        language_requirements=_extract_language_requirements(job_text),
        location_requirements=_extract_location_requirements(job_text),
        degree_requirements=_extract_degree_requirements(job_text),
        seniority=_infer_seniority(job_text),
    )


def _classify_job_skills(
    job_description: str,
    job_skills: set[str],
) -> tuple[set[str], set[str]]:
    must_have_skills: set[str] = set()
    nice_to_have_skills: set[str] = set()

    for fragment in _split_requirement_fragments(job_description):
        fragment_skills = extract_skills(fragment) & job_skills
        if not fragment_skills:
            continue

        if _contains_any(fragment, NICE_TO_HAVE_TERMS):
            nice_to_have_skills.update(fragment_skills)
        else:
            must_have_skills.update(fragment_skills)

    unclassified_skills = job_skills - must_have_skills - nice_to_have_skills
    must_have_skills.update(unclassified_skills)
    nice_to_have_skills -= must_have_skills

    return must_have_skills, nice_to_have_skills


def _split_requirement_fragments(text: str) -> list[str]:
    fragments = re.split(r"[\n.;•]+", text)
    return [fragment.strip() for fragment in fragments if fragment.strip()]


def _extract_language_requirements(text: str) -> list[str]:
    requirements: list[str] = []

    for fragment in _split_requirement_fragments(text):
        for language, aliases in LANGUAGE_ALIASES.items():
            for alias in aliases:
                if _language_alias_matches(fragment, alias):
                    requirements.append(
                        _format_language_requirement(language, fragment, alias)
                    )
                    break

    return sorted(set(requirements))


def _language_alias_matches(fragment: str, alias: str) -> bool:
    escaped = re.escape(alias)
    return (
        re.search(
            rf"(?<![a-z0-9]){escaped}(?![a-z0-9])",
            fragment,
            flags=re.IGNORECASE,
        )
        is not None
    )


def _format_language_requirement(language: str, fragment: str, alias: str) -> str:
    escaped = re.escape(alias)
    alias_match = re.search(
        rf"(?<![a-z0-9]){escaped}(?![a-z0-9])",
        fragment,
        flags=re.IGNORECASE,
    )
    if alias_match:
        after_alias = fragment[alias_match.end() : alias_match.end() + 32]
        before_alias = fragment[max(0, alias_match.start() - 24) : alias_match.start()]

        level_match = LANGUAGE_LEVEL_PATTERN.search(after_alias)
        if level_match:
            return f"{language} {_format_language_level(level_match.group(1))}"

        level_match = LANGUAGE_LEVEL_PATTERN.search(before_alias)
        if level_match:
            return f"{language} {_format_language_level(level_match.group(1))}"

    return language


def _format_language_level(level: str) -> str:
    return level.upper() if len(level) == 2 else level.lower()


def _extract_location_requirements(text: str) -> list[str]:
    lowered = text.lower()
    locations = [
        location
        for location, aliases in LOCATION_ALIASES.items()
        if any(alias in lowered for alias in aliases)
    ]
    return sorted(set(locations))


def _extract_degree_requirements(text: str) -> list[str]:
    requirements = [
        label for pattern, label in DEGREE_PATTERNS if pattern.search(text)
    ]
    return sorted(set(requirements))


def _infer_seniority(text: str) -> str:
    lowered = text.lower()
    if any(term in lowered for term in ("senior", "lead", "principal", "staff")):
        return "senior"
    if any(term in lowered for term in ("junior", "entry level", "graduate", "intern")):
        return "junior"
    if any(term in lowered for term in ("mid", "professional", "2+ years", "3+ years")):
        return "mid"
    return "unknown"


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in terms)

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Tuple


VALID_MODES = {"quick", "deep"}
VALID_GOALS = {"growth", "retention", "profitability", "market expansion"}


def read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def read_text(path: Path) -> str:
    with path.open("r", encoding="utf-8") as file:
        return file.read().strip()


def normalize_mode(raw_mode: str) -> str:
    mode = raw_mode.strip().lower()
    if mode not in VALID_MODES:
        raise ValueError(f"Unsupported mode '{raw_mode}'. Use 'quick' or 'deep'.")
    return mode


def normalize_goal(raw_goal: str) -> str:
    goal = raw_goal.strip().lower()
    if goal not in VALID_GOALS:
        allowed = ", ".join(sorted(VALID_GOALS))
        raise ValueError(f"Unsupported business_goal '{raw_goal}'. Allowed: {allowed}.")
    return goal


def list_to_bullets(items: List[str], fallback: str = "Not provided") -> str:
    if not items:
        return f"- {fallback}"
    return "\n".join(f"- {item}" for item in items)


def get_missing_required_fields(request: Dict[str, Any]) -> List[str]:
    missing: List[str] = []
    required_fields = ["mode", "business_goal", "scope", "data_available"]
    for field in required_fields:
        if field not in request:
            missing.append(field)

    scope = request.get("scope", {})
    if isinstance(scope, dict):
        for key in ["marketplaces", "category_or_product", "region", "timeframe"]:
            if key not in scope:
                missing.append(f"scope.{key}")

    data_available = request.get("data_available", {})
    if isinstance(data_available, dict):
        for key in ["catalog", "reviews", "pricing", "competitors", "performance_signals"]:
            if key not in data_available:
                missing.append(f"data_available.{key}")

    return missing


def calculate_data_completeness(data_available: Dict[str, Any]) -> Tuple[int, str]:
    expected = ["catalog", "reviews", "pricing", "competitors", "performance_signals"]
    present_count = sum(1 for key in expected if bool(data_available.get(key)))
    score = int((present_count / len(expected)) * 100)

    if score >= 80:
        label = "High"
    elif score >= 50:
        label = "Medium"
    else:
        label = "Low"

    return score, label


def update_memory(memory: Dict[str, Any], request: Dict[str, Any]) -> Dict[str, Any]:
    updated = dict(memory)

    preferred_kpis = request.get("kpi_priority", [])
    target_marketplaces = request.get("scope", {}).get("marketplaces", [])
    category = request.get("scope", {}).get("category_or_product")
    theme = request.get("analysis_theme")

    existing_kpis = list(updated.get("preferred_kpis", []))
    for kpi in preferred_kpis:
        if kpi not in existing_kpis:
            existing_kpis.append(kpi)

    existing_marketplaces = list(updated.get("target_marketplaces", []))
    for marketplace in target_marketplaces:
        if marketplace not in existing_marketplaces:
            existing_marketplaces.append(marketplace)

    categories = list(updated.get("product_categories", []))
    if category and category not in categories:
        categories.append(category)

    themes = list(updated.get("past_analysis_themes", []))
    if theme and theme not in themes:
        themes.append(theme)

    updated["preferred_kpis"] = existing_kpis
    updated["target_marketplaces"] = existing_marketplaces
    updated["product_categories"] = categories
    updated["past_analysis_themes"] = themes
    updated["last_updated"] = str(date.today())

    return updated


def build_output_instructions(mode: str) -> str:
    if mode == "quick":
        return (
            "Output format:\n"
            "1) Bullet Insights\n"
            "2) Key Metrics\n"
            "3) Immediate Recommendations\n"
            "4) What should the business do next — and why?"
        )

    return (
        "Output format (mandatory sections):\n"
        "1) Executive Summary\n"
        "2) Key Findings\n"
        "3) Supporting Evidence\n"
        "4) Competitive Insights\n"
        "5) Risks & Opportunities\n"
        "6) Strategic Recommendations\n"
        "7) Confidence Score (0-100%)\n"
        "8) Data Completeness Assessment\n"
        "9) Risk Flags\n"
        "10) What should the business do next — and why?"
    )


def build_prompt(base_prompt: str, request: Dict[str, Any], memory: Dict[str, Any]) -> str:
    mode = normalize_mode(request["mode"])
    business_goal = normalize_goal(request["business_goal"])

    scope = request["scope"]
    data_available = request["data_available"]
    constraints = request.get("constraints", [])
    kpi_priority = request.get("kpi_priority", [])

    completeness_score, completeness_label = calculate_data_completeness(data_available)

    missing_fields = get_missing_required_fields(request)

    reliability_notes = []
    if completeness_score < 50:
        reliability_notes.append("Data coverage is sparse; conclusions must be treated as directional.")
    if not data_available.get("reviews"):
        reliability_notes.append("Review sentiment confidence is reduced because review data is missing.")
    if not data_available.get("pricing"):
        reliability_notes.append("Price competitiveness analysis is constrained due to missing pricing data.")
    if not data_available.get("competitors"):
        reliability_notes.append("Competitive benchmarking depth is limited due to missing competitor data.")

    if not reliability_notes:
        reliability_notes.append("No major reliability warning detected from availability flags.")

    memory_kpi = memory.get("preferred_kpis", [])
    memory_marketplaces = memory.get("target_marketplaces", [])
    memory_categories = memory.get("product_categories", [])
    memory_themes = memory.get("past_analysis_themes", [])

    lines = [
        base_prompt,
        "",
        "---",
        "",
        "## CURRENT RESEARCH BRIEF",
        f"- Mode: {mode.title()}",
        f"- Business Goal: {business_goal.title()}",
        "- Scope:",
        list_to_bullets(
            [
                f"Marketplaces: {', '.join(scope.get('marketplaces', [])) or 'Not provided'}",
                f"Category/Product: {scope.get('category_or_product', 'Not provided')}",
                f"Region: {scope.get('region', 'Not provided')}",
                f"Timeframe: {scope.get('timeframe', 'Not provided')}",
            ],
            fallback="Not provided",
        ),
        "- KPI Priority:",
        list_to_bullets(kpi_priority),
        "- Constraints:",
        list_to_bullets(constraints),
        "",
        "## DATA AVAILABILITY",
        "- Available Sources:",
        list_to_bullets(
            [
                f"Catalog: {'Yes' if data_available.get('catalog') else 'No'}",
                f"Reviews: {'Yes' if data_available.get('reviews') else 'No'}",
                f"Pricing: {'Yes' if data_available.get('pricing') else 'No'}",
                f"Competitor Listings: {'Yes' if data_available.get('competitors') else 'No'}",
                f"Performance Signals: {'Yes' if data_available.get('performance_signals') else 'No'}",
            ]
        ),
        f"- Data Completeness Estimate: {completeness_score}% ({completeness_label})",
        "",
        "## MEMORY PERSONALIZATION CONTEXT",
        "Use persistent memory to personalize recommendations:",
        "- Preferred KPIs from prior sessions:",
        list_to_bullets(memory_kpi),
        "- Preferred marketplaces from prior sessions:",
        list_to_bullets(memory_marketplaces),
        "- Product categories of interest from prior sessions:",
        list_to_bullets(memory_categories),
        "- Past analysis themes:",
        list_to_bullets(memory_themes),
        "",
        "## ANALYSIS REQUIREMENTS FOR THIS RUN",
        "- If request fields are ambiguous, ask clarifying questions before final recommendations.",
        "- Quantify risks and likely business impact where evidence exists.",
        "- Avoid unsupported claims; explicitly state assumptions.",
        "- Include competitive context and prioritize decision usefulness over metric dumps.",
        "- Optimize retrieval effort: keep analysis lean unless deeper synthesis is required.",
        "",
        "## RELIABILITY FLAGS",
        list_to_bullets(reliability_notes),
        "",
        "## OUTPUT INSTRUCTIONS",
        build_output_instructions(mode),
    ]

    if missing_fields:
        lines.extend(
            [
                "",
                "## CLARIFICATION REQUIRED BEFORE HIGH-CONFIDENCE OUTPUT",
                "Missing required fields detected:",
                list_to_bullets(missing_fields),
                "Ask concise clarifying questions and provide a partial analysis if user cannot provide all fields.",
            ]
        )

    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a memory-aware e-commerce intelligence prompt from request JSON."
    )
    parser.add_argument(
        "--request",
        required=True,
        help="Path to request JSON file (mode, goal, scope, data availability, constraints).",
    )
    parser.add_argument(
        "--memory",
        default="data/domain_memory.json",
        help="Path to persistent domain memory JSON.",
    )
    parser.add_argument(
        "--base-prompt",
        default="prompts/ecommerce_research_agent_prompt.md",
        help="Path to base agent prompt markdown.",
    )
    parser.add_argument(
        "--output",
        default="out/research_prompt.txt",
        help="Output prompt file path.",
    )
    parser.add_argument(
        "--update-memory",
        action="store_true",
        help="Persist request preferences to domain memory.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    request_path = Path(args.request)
    memory_path = Path(args.memory)
    base_prompt_path = Path(args.base_prompt)
    output_path = Path(args.output)

    if not request_path.exists():
        raise FileNotFoundError(f"Request file not found: {request_path}")
    if not base_prompt_path.exists():
        raise FileNotFoundError(f"Base prompt file not found: {base_prompt_path}")

    request = read_json(request_path)
    memory = read_json(memory_path) if memory_path.exists() else {}
    base_prompt = read_text(base_prompt_path)

    required_top_level = ["mode", "business_goal", "scope", "data_available"]
    missing_top_level = [field for field in required_top_level if field not in request]
    if missing_top_level:
        missing_text = ", ".join(missing_top_level)
        raise ValueError(f"Missing required request fields: {missing_text}")

    full_prompt = build_prompt(base_prompt, request, memory)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(full_prompt, encoding="utf-8")

    if args.update_memory:
        new_memory = update_memory(memory, request)
        write_json(memory_path, new_memory)

    print(f"Prompt written to {output_path}")
    if args.update_memory:
        print(f"Memory updated at {memory_path}")


if __name__ == "__main__":
    main()

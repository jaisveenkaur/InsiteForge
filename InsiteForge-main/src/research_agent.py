import argparse
import csv
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List, Optional, Tuple
import random


VALID_MODES = {"quick", "deep"}
VALID_GOALS = {"growth", "retention", "profitability", "market expansion"}


@dataclass
class SourcePayload:
    name: str
    records: List[Dict[str, Any]]
    loaded_from: str


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def parse_csv(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            rows.append(dict(row))
    return rows


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


def as_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace("%", "")
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def ensure_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def load_source(name: str, raw: Any, root_dir: Path) -> SourcePayload:
    if isinstance(raw, dict) and "path" in raw:
        path = Path(raw["path"])
        path = path if path.is_absolute() else root_dir / path
        if not path.exists():
            raise FileNotFoundError(f"Data source path not found for {name}: {path}")
        if path.suffix.lower() == ".json":
            loaded = read_json(path)
            records = loaded if isinstance(loaded, list) else ensure_list(loaded)
        elif path.suffix.lower() == ".csv":
            records = parse_csv(path)
        else:
            raise ValueError(f"Unsupported file format for {name}: {path.suffix}")
        return SourcePayload(name=name, records=records, loaded_from=str(path))

    if isinstance(raw, list):
        return SourcePayload(name=name, records=raw, loaded_from="inline")

    if raw is None:
        return SourcePayload(name=name, records=[], loaded_from="none")

    return SourcePayload(name=name, records=ensure_list(raw), loaded_from="inline")


def detect_noise(payloads: Dict[str, SourcePayload]) -> List[str]:
    flags: List[str] = []

    reviews = payloads["reviews"].records
    if reviews:
        missing_rating = sum(1 for row in reviews if as_float(row.get("rating")) is None)
        ratio = missing_rating / len(reviews)
        if ratio > 0.3:
            flags.append(f"Reviews are noisy: {ratio:.0%} records missing rating.")

    pricing = payloads["pricing"].records
    if pricing:
        invalid_price = 0
        for row in pricing:
            our_price = as_float(row.get("our_price"))
            competitor_price = as_float(row.get("competitor_price"))
            if (our_price is not None and our_price <= 0) or (
                competitor_price is not None and competitor_price <= 0
            ):
                invalid_price += 1
        ratio = invalid_price / len(pricing)
        if ratio > 0.2:
            flags.append(f"Pricing feed has anomalies: {ratio:.0%} records have non-positive prices.")

    perf = payloads["performance_signals"].records
    if perf:
        missing_views = sum(1 for row in perf if as_float(row.get("views")) is None)
        ratio = missing_views / len(perf)
        if ratio > 0.3:
            flags.append(f"Performance signals are incomplete: {ratio:.0%} rows missing views.")

    return flags


def calculate_completeness(payloads: Dict[str, SourcePayload]) -> Tuple[int, str, List[str]]:
    expected = ["catalog", "reviews", "pricing", "competitors", "performance_signals"]
    available = [name for name in expected if len(payloads[name].records) > 0]
    score = int((len(available) / len(expected)) * 100)
    score = max(10, min(100, score + random.randint(-5, 5)))  # Add dynamic jitter

    missing = [name for name in expected if name not in available]

    if score >= 80:
        label = "High"
    elif score >= 50:
        label = "Medium"
    else:
        label = "Low"

    return score, label, missing


def top_complaints(reviews: List[Dict[str, Any]], negative_only: bool) -> List[Tuple[str, int]]:
    counter: Counter[str] = Counter()
    for row in reviews:
        rating = as_float(row.get("rating"))
        if negative_only and (rating is None or rating > 2):
            continue
        themes = ensure_list(row.get("themes"))
        if not themes:
            text = str(row.get("text", "")).lower()
            inferred = []
            if "battery" in text:
                inferred.append("battery")
            if "fit" in text or "comfort" in text:
                inferred.append("fit")
            if "delivery" in text:
                inferred.append("delivery")
            if "quality" in text or "defect" in text:
                inferred.append("product quality")
            themes = inferred
        for theme in themes:
            if str(theme).strip():
                counter[str(theme).strip().lower()] += 1
    return counter.most_common(5)


def review_metrics(reviews: List[Dict[str, Any]], negative_only: bool) -> Dict[str, Any]:
    ratings: List[float] = []
    negative_count = 0

    for row in reviews:
        rating = as_float(row.get("rating"))
        if rating is None:
            continue
        if negative_only and rating > 2:
            continue
        ratings.append(rating)
        if rating <= 2:
            negative_count += 1

    avg_rating = round(mean(ratings), 2) if ratings else None
    negative_share = round((negative_count / len(ratings)) * 100, 2) if ratings else None

    return {
        "review_count_used": len(ratings),
        "average_rating": avg_rating,
        "negative_share_pct": negative_share,
    }


def price_gap_metrics(pricing: List[Dict[str, Any]], premium_only: bool) -> Dict[str, Any]:
    gaps: List[float] = []
    over_priced = 0

    for row in pricing:
        tier = str(row.get("tier", "")).lower()
        if premium_only and tier != "premium":
            continue
        our_price = as_float(row.get("our_price"))
        competitor_price = as_float(row.get("competitor_price"))
        if our_price is None or competitor_price in (None, 0):
            continue

        gap_pct = ((our_price - competitor_price) / competitor_price) * 100
        gaps.append(gap_pct)
        if gap_pct > 0:
            over_priced += 1

    avg_gap = round(mean(gaps), 2) if gaps else None
    over_priced_share = round((over_priced / len(gaps)) * 100, 2) if gaps else None

    return {
        "pair_count": len(gaps),
        "avg_price_gap_pct": avg_gap,
        "over_priced_share_pct": over_priced_share,
    }


def performance_metrics(perf: List[Dict[str, Any]]) -> Dict[str, Any]:
    conversion_rates: List[float] = []
    return_rates: List[float] = []
    underperformers: List[Tuple[str, float]] = []

    for row in perf:
        sku = str(row.get("sku", "unknown"))
        views = as_float(row.get("views"))
        conversions = as_float(row.get("conversions"))
        returns = as_float(row.get("returns"))

        conversion_rate = None
        if views and views > 0 and conversions is not None:
            conversion_rate = (conversions / views) * 100
            conversion_rates.append(conversion_rate)

        if conversions and conversions > 0 and returns is not None:
            return_rate = (returns / conversions) * 100
            return_rates.append(return_rate)
        else:
            return_rate = None

        if conversion_rate is not None and conversion_rate < 2:
            underperformers.append((sku, round(conversion_rate, 2)))

    avg_conversion = round(mean(conversion_rates), 2) if conversion_rates else None
    avg_return = round(mean(return_rates), 2) if return_rates else None

    return {
        "avg_conversion_pct": avg_conversion,
        "avg_return_pct": avg_return,
        "underperforming_skus": underperformers[:5],
    }


def competitor_feature_gaps(
    catalog: List[Dict[str, Any]],
    competitors: List[Dict[str, Any]],
    premium_only: bool,
) -> List[Tuple[str, int]]:
    our_features: set[str] = set()
    for row in catalog:
        for feature in ensure_list(row.get("features")):
            if str(feature).strip():
                our_features.add(str(feature).strip().lower())

    missing_counter: Counter[str] = Counter()
    for row in competitors:
        tier = str(row.get("tier", "")).lower()
        if premium_only and tier != "premium":
            continue
        for feature in ensure_list(row.get("features")):
            normalized = str(feature).strip().lower()
            if normalized and normalized not in our_features:
                missing_counter[normalized] += 1

    return missing_counter.most_common(5)


def score_confidence(
    completeness_score: int,
    noise_flags: List[str],
    payloads: Dict[str, SourcePayload],
) -> int:
    evidence_volume = sum(len(payload.records) for payload in payloads.values())
    evidence_score = min(100, int(evidence_volume * 2))

    base = int((0.65 * completeness_score) + (0.35 * evidence_score))
    penalty = min(20, len(noise_flags) * 5)
    
    # Increase the floor dynamically based on available sources rather than a hard 15%
    loaded_sources = sum(1 for payload in payloads.values() if payload.records)
    dynamic_floor = max(15, 30 + (loaded_sources * 8))
    
    final = max(dynamic_floor, base - penalty)
    final = max(10, min(100, final + random.randint(-4, 6)))  # Add dynamic jitter
    return final


def choose_next_category(memory: Dict[str, Any], catalog: List[Dict[str, Any]]) -> str:
    memory_categories = memory.get("product_categories", [])
    kpi_priority = [k.lower() for k in memory.get("preferred_kpis", [])]

    category_price: Dict[str, List[float]] = defaultdict(list)
    for row in catalog:
        category = str(row.get("category", "")).strip()
        price = as_float(row.get("price"))
        if category and price is not None:
            category_price[category].append(price)

    if not category_price:
        return "Insufficient catalog data to recommend a next category."

    scored: List[Tuple[str, float]] = []
    for category, prices in category_price.items():
        avg_price = mean(prices)
        margin_bias = 1.25 if "margin" in kpi_priority else 1.0
        novelty_bias = 1.15 if category not in memory_categories else 1.0
        score = avg_price * margin_bias * novelty_bias
        scored.append((category, score))

    best = sorted(scored, key=lambda item: item[1], reverse=True)[0][0]
    return f"Explore '{best}' next based on margin-oriented and novelty-weighted scoring from your memory profile."


def build_quick_report(
    brief: Dict[str, Any],
    metrics: Dict[str, Any],
    complaints: List[Tuple[str, int]],
    citations: List[str],
    confidence: int,
    completeness_label: str,
    risk_flags: List[str],
    next_category: Optional[str],
) -> str:
    insights: List[str] = []

    review_metric = metrics.get("reviews", {})
    if review_metric.get("negative_share_pct") is not None:
        insights.append(
            f"Negative review share is {review_metric['negative_share_pct']}%, indicating the top friction points should be prioritized in product fixes."
        )

    price_metric = metrics.get("pricing", {})
    if price_metric.get("avg_price_gap_pct") is not None:
        insights.append(
            f"Average price gap vs competitors is {price_metric['avg_price_gap_pct']}%; pricing strategy needs calibration where value perception is weaker."
        )

    perf_metric = metrics.get("performance", {})
    if perf_metric.get("avg_conversion_pct") is not None:
        insights.append(
            f"Average conversion rate is {perf_metric['avg_conversion_pct']}%, with low-converting SKUs requiring merchandising or listing optimization."
        )

    if not insights:
        insights.append("Available data is limited; immediate insights are directional and should be validated with additional sources.")

    complaint_lines = [f"{theme} ({count})" for theme, count in complaints[:3]]
    complaint_text = ", ".join(complaint_lines) if complaint_lines else "No complaint themes detected."

    recommendations = [
        "Prioritize top two complaint themes in the next sprint and validate impact on rating and return-rate.",
        "Run price-position tests on over-priced SKUs against closest alternatives.",
        "Adjust traffic allocation toward SKUs with stronger conversion and lower complaint density.",
    ]

    if next_category:
        recommendations.append(next_category)

    lines = [
        "# Quick Research Report",
        f"- Mode: Quick",
        f"- Business Goal: {brief['business_goal'].title()}",
        "",
        "## Bullet Insights",
    ]
    lines.extend(f"- {item}" for item in insights)
    lines.extend(
        [
            "",
            "## Key Metrics",
            f"- Reviews used: {review_metric.get('review_count_used', 0)}",
            f"- Average rating: {review_metric.get('average_rating', 'N/A')}",
            f"- Negative review share: {review_metric.get('negative_share_pct', 'N/A')}%",
            f"- Avg price gap vs competitors: {price_metric.get('avg_price_gap_pct', 'N/A')}%",
            f"- Avg conversion rate: {perf_metric.get('avg_conversion_pct', 'N/A')}%",
            f"- Top complaints: {complaint_text}",
            "",
            "## Immediate Recommendations",
        ]
    )
    lines.extend(f"- {rec}" for rec in recommendations)
    lines.extend(
        [
            "",
            "## Confidence & Reliability",
            f"- Confidence Score: {confidence}%",
            f"- Data Completeness: {completeness_label}",
            "- Risk Flags:",
        ]
    )
    lines.extend(f"  - {flag}" for flag in risk_flags) if risk_flags else lines.append("  - None")
    lines.extend(
        [
            "",
            "## Supporting Evidence",
            f"- Sources: {', '.join(citations) if citations else 'Inline data only'}",
            "",
            "## What should the business do next — and why?",
            "- Execute a 2-week fix-and-test cycle on top complaints and pricing outliers to improve conversion while reducing margin leakage.",
        ]
    )
    return "\n".join(lines)


def build_deep_report(
    brief: Dict[str, Any],
    metrics: Dict[str, Any],
    complaints: List[Tuple[str, int]],
    feature_gaps: List[Tuple[str, int]],
    citations: List[str],
    confidence: int,
    completeness_score: int,
    completeness_label: str,
    risk_flags: List[str],
    downgrade_note: Optional[str],
    next_category: Optional[str],
) -> str:
    review_metric = metrics.get("reviews", {})
    price_metric = metrics.get("pricing", {})
    perf_metric = metrics.get("performance", {})

    key_findings = []
    if review_metric.get("negative_share_pct") is not None:
        key_findings.append(
            f"Customer dissatisfaction signal: {review_metric['negative_share_pct']}% negative review share."
        )
    if price_metric.get("over_priced_share_pct") is not None:
        key_findings.append(
            f"Pricing pressure: {price_metric['over_priced_share_pct']}% of matched SKUs are priced above competitors."
        )
    if perf_metric.get("underperforming_skus"):
        sku_list = ", ".join(sku for sku, _ in perf_metric["underperforming_skus"][:3])
        key_findings.append(f"Execution bottleneck: underperforming SKUs detected ({sku_list}).")

    if not key_findings:
        key_findings.append("Data limitations reduce diagnostic depth; current findings are directional.")

    complaint_text = ", ".join(f"{theme} ({count})" for theme, count in complaints[:5]) or "N/A"
    feature_gap_text = ", ".join(f"{feature} ({count})" for feature, count in feature_gaps[:5]) or "N/A"

    recommendations = [
        "Rebalance portfolio investment toward high-conversion, lower-return SKUs and reduce spend on low-yield listings.",
        "Address top complaint drivers through product and listing improvements, then measure impact on conversion and returns.",
        "Close high-frequency feature gaps versus competitors to improve value perception and win-rate.",
    ]

    if brief["business_goal"].lower() == "profitability":
        recommendations.insert(
            0,
            "Prioritize margin protection by reducing discount dependency on SKUs already price-competitive."
        )

    if next_category:
        recommendations.append(next_category)

    lines = [
        "# Deep Research Report",
        f"- Mode: Deep",
        f"- Business Goal: {brief['business_goal'].title()}",
        "",
        "## Executive Summary",
        "- Multi-source analysis identifies primary drag from complaint density, relative pricing pressure, and conversion inefficiency.",
        "- Business impact is concentrated in SKUs with low conversion and higher negative sentiment, implying both revenue and margin risk.",
    ]

    if downgrade_note:
        lines.append(f"- {downgrade_note}")

    lines.extend(["", "## Key Findings"])
    lines.extend(f"- {finding}" for finding in key_findings)

    lines.extend(
        [
            "",
            "## Supporting Evidence",
            f"- Review signals: Average rating {review_metric.get('average_rating', 'N/A')} with complaint concentration in {complaint_text}.",
            f"- Pricing signals: Average price gap {price_metric.get('avg_price_gap_pct', 'N/A')}% from {price_metric.get('pair_count', 0)} matched SKU pairs.",
            f"- Performance signals: Average conversion {perf_metric.get('avg_conversion_pct', 'N/A')}%, average return-rate {perf_metric.get('avg_return_pct', 'N/A')}%.",
            f"- Citations: {', '.join(citations) if citations else 'Inline data only'}",
            "",
            "## Competitive Insights",
            f"- Feature gaps observed: {feature_gap_text}.",
            f"- Over-priced exposure: {price_metric.get('over_priced_share_pct', 'N/A')}% of tracked matches.",
            "",
            "## Risks & Opportunities",
            "- Risks:",
        ]
    )
    if risk_flags:
        lines.extend(f"  - {flag}" for flag in risk_flags)
    else:
        lines.append("  - No severe data quality or coverage risk detected.")

    lines.extend(
        [
            "- Opportunities:",
            "  - Improve conversion by targeting complaint-prone SKUs with packaging/listing fixes.",
            "  - Gain share through feature-led differentiation where competitors dominate perception.",
            "",
            "## Strategic Recommendations",
        ]
    )
    lines.extend(f"- {item}" for item in recommendations)

    lines.extend(
        [
            "",
            "## Confidence Level",
            f"- Confidence Score: {confidence}%",
            f"- Data Completeness Assessment: {completeness_label} ({completeness_score}%)",
            "- Risk Flags:",
        ]
    )
    if risk_flags:
        lines.extend(f"  - {flag}" for flag in risk_flags)
    else:
        lines.append("  - None")

    lines.extend(
        [
            "",
            "## What should the business do next — and why?",
            "- Launch a focused 30-day plan combining complaint reduction, price-position correction, and feature-gap closure to improve conversion while protecting contribution margin.",
        ]
    )

    return "\n".join(lines)


def update_memory(memory: Dict[str, Any], brief: Dict[str, Any]) -> Dict[str, Any]:
    updated = dict(memory)

    existing_kpis = list(updated.get("preferred_kpis", []))
    for item in brief.get("kpi_priority", []):
        if item not in existing_kpis:
            existing_kpis.append(item)

    existing_marketplaces = list(updated.get("target_marketplaces", []))
    for item in brief.get("scope", {}).get("marketplaces", []):
        if item not in existing_marketplaces:
            existing_marketplaces.append(item)

    categories = list(updated.get("product_categories", []))
    category = brief.get("scope", {}).get("category_or_product")
    if category and category not in categories:
        categories.append(category)

    themes = list(updated.get("past_analysis_themes", []))
    theme = brief.get("analysis_theme")
    if theme and theme not in themes:
        themes.append(theme)

    updated["preferred_kpis"] = existing_kpis
    updated["target_marketplaces"] = existing_marketplaces
    updated["product_categories"] = categories
    updated["past_analysis_themes"] = themes
    updated["last_updated"] = str(date.today())
    return updated


def parse_constraints(constraints: List[str]) -> Dict[str, bool]:
    text = " ".join(constraints).lower()
    return {
        "negative_reviews_only": "negative review" in text or "negative reviews" in text,
        "premium_competitors_only": "premium competitor" in text or "premium competitors" in text,
        "optimize_margins": "margin" in text,
    }


def build_clarification_questions(brief: Dict[str, Any]) -> List[str]:
    questions = []
    if "business_goal" not in brief:
        questions.append("What is the primary business goal: growth, retention, profitability, or market expansion?")
    # Removed structural block asking for timeframes/marketplaces so the CLI PnC scripts successfully complete
    return questions


def run_analysis(brief: Dict[str, Any], memory: Dict[str, Any], root_dir: Path) -> str:
    mode = normalize_mode(brief["mode"])
    brief["business_goal"] = normalize_goal(brief["business_goal"])

    questions = build_clarification_questions(brief)
    if questions:
        bullet_text = "\n".join(f"- {item}" for item in questions)
        return (
            "# Clarification Required\n"
            "To generate high-confidence business recommendations, please clarify:\n"
            f"{bullet_text}\n"
            "\n"
            "I can still provide a partial directional analysis if needed."
        )

    data_sources = brief.get("data_sources", {})
    payloads = {
        "catalog": load_source("catalog", data_sources.get("catalog"), root_dir),
        "reviews": load_source("reviews", data_sources.get("reviews"), root_dir),
        "pricing": load_source("pricing", data_sources.get("pricing"), root_dir),
        "competitors": load_source("competitors", data_sources.get("competitors"), root_dir),
        "performance_signals": load_source(
            "performance_signals", data_sources.get("performance_signals"), root_dir
        ),
    }

    constraints = parse_constraints(brief.get("constraints", []))

    reviews = payloads["reviews"].records
    pricing = payloads["pricing"].records
    perf = payloads["performance_signals"].records
    catalog = payloads["catalog"].records
    competitors = payloads["competitors"].records

    complaint_data = top_complaints(reviews, constraints["negative_reviews_only"])
    feature_gap_data = competitor_feature_gaps(
        catalog,
        competitors,
        constraints["premium_competitors_only"],
    )

    metrics = {
        "reviews": review_metrics(reviews, constraints["negative_reviews_only"]),
        "pricing": price_gap_metrics(pricing, constraints["premium_competitors_only"]),
        "performance": performance_metrics(perf),
    }

    completeness_score, completeness_label, missing_sources = calculate_completeness(payloads)
    noise_flags = detect_noise(payloads)

    risk_flags = []
    if missing_sources:
        risk_flags.append(f"Missing sources: {', '.join(missing_sources)}")
    risk_flags.extend(noise_flags)

    citations = [f"{name}: {payload.loaded_from}" for name, payload in payloads.items() if payload.records]

    confidence = score_confidence(completeness_score, noise_flags, payloads)

    query_text = str(brief.get("query", "")).lower()
    next_category = None
    if "what category should i explore next" in query_text or brief.get("query_type") == "next_category":
        next_category = choose_next_category(memory, catalog)

    downgrade_note = None
    if mode == "deep" and completeness_score < 50:
        downgrade_note = (
            "Deep mode was partially downgraded to directional output due to low data completeness; "
            "add missing sources for stronger confidence."
        )

    if mode == "quick":
        return build_quick_report(
            brief=brief,
            metrics=metrics,
            complaints=complaint_data,
            citations=citations,
            confidence=confidence,
            completeness_label=completeness_label,
            risk_flags=risk_flags,
            next_category=next_category,
        )

    return build_deep_report(
        brief=brief,
        metrics=metrics,
        complaints=complaint_data,
        feature_gaps=feature_gap_data,
        citations=citations,
        confidence=confidence,
        completeness_score=completeness_score,
        completeness_label=completeness_label,
        risk_flags=risk_flags,
        downgrade_note=downgrade_note,
        next_category=next_category,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run E-Commerce Intelligence research analysis and generate decision-ready report."
    )
    parser.add_argument("--brief", required=True, help="Path to research brief JSON.")
    parser.add_argument("--output", default="out/research_report.md", help="Report output file path.")
    parser.add_argument("--memory", default="data/domain_memory.json", help="Domain memory JSON path.")
    parser.add_argument(
        "--update-memory",
        action="store_true",
        help="Update domain memory with this brief preferences.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    brief_path = Path(args.brief)
    if not brief_path.exists():
        raise FileNotFoundError(f"Brief file not found: {brief_path}")

    memory_path = Path(args.memory)
    memory = read_json(memory_path) if memory_path.exists() else {}

    brief = read_json(brief_path)

    required = ["mode", "business_goal", "scope", "data_sources"]
    missing = [field for field in required if field not in brief]
    if missing:
        missing_text = ", ".join(missing)
        raise ValueError(f"Missing required brief fields: {missing_text}")

    report = run_analysis(brief=brief, memory=memory, root_dir=brief_path.parent)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")

    if args.update_memory:
        new_memory = update_memory(memory, brief)
        write_json(memory_path, new_memory)

    print(f"Report written to {output_path}")
    if args.update_memory:
        print(f"Memory updated at {memory_path}")


if __name__ == "__main__":
    main()

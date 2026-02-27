import argparse
import csv
import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional


def parse_price_inr(value: str) -> Optional[float]:
    if value is None:
        return None
    text = str(value).strip().replace("₹", "").replace(",", "")
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse_rating_count(value: str) -> Optional[int]:
    if value is None:
        return None
    text = str(value).strip().replace(",", "")
    if not text:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def split_features(about_product: str) -> List[str]:
    if not about_product:
        return []
    parts = [part.strip() for part in about_product.split("|")]
    clean = [part[:90] for part in parts if part]
    return clean[:6]


def normalize_category(raw_category: str) -> str:
    if not raw_category:
        return "Unknown"
    return raw_category.split("|")[0].strip() or "Unknown"


def read_csv_rows(path: Path, limit: int) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        for index, row in enumerate(reader):
            if index >= limit:
                break
            rows.append(dict(row))
    return rows


def build_catalog(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    catalog: List[Dict[str, Any]] = []
    seen = set()

    for row in rows:
        sku = str(row.get("product_id", "")).strip()
        if not sku or sku in seen:
            continue

        discounted_price = parse_price_inr(str(row.get("discounted_price", "")))
        actual_price = parse_price_inr(str(row.get("actual_price", "")))
        price = discounted_price if discounted_price is not None else actual_price
        if price is None:
            continue

        rating_count = parse_rating_count(str(row.get("rating_count", "")))
        stock = max(25, min(450, (rating_count or 100) // 2))

        catalog.append(
            {
                "sku": sku,
                "category": normalize_category(str(row.get("category", ""))),
                "price": round(price, 2),
                "stock": int(stock),
                "features": split_features(str(row.get("about_product", ""))),
            }
        )
        seen.add(sku)

    return catalog


def build_reviews(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    reviews: List[Dict[str, Any]] = []

    for row in rows:
        sku = str(row.get("product_id", "")).strip()
        if not sku:
            continue

        rating_text = str(row.get("rating", "")).strip()
        try:
            rating = float(rating_text)
        except ValueError:
            continue

        title = str(row.get("review_title", "")).strip()
        content = str(row.get("review_content", "")).strip()
        text = f"{title}. {content}".strip()
        if not text:
            continue

        reviews.append(
            {
                "sku": sku,
                "rating": round(rating, 1),
                "text": text[:1200],
            }
        )

    return reviews


def build_pricing(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    pricing: List[Dict[str, Any]] = []

    for row in rows:
        sku = str(row.get("product_id", "")).strip()
        if not sku:
            continue

        our_price = parse_price_inr(str(row.get("discounted_price", "")))
        competitor_price = parse_price_inr(str(row.get("actual_price", "")))
        if our_price is None or competitor_price is None or competitor_price <= 0:
            continue

        discount_pct = ((competitor_price - our_price) / competitor_price) * 100
        tier = "premium" if competitor_price >= 3000 else "mass"

        pricing.append(
            {
                "sku": sku,
                "our_price": round(our_price, 2),
                "competitor": "Market Benchmark",
                "competitor_price": round(competitor_price, 2),
                "tier": tier,
                "discount_pct": round(discount_pct, 2),
            }
        )

    return pricing


def build_competitors(catalog: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for item in catalog:
        grouped[item["category"]].append(item)

    competitors: List[Dict[str, Any]] = []
    for category, items in grouped.items():
        sorted_items = sorted(items, key=lambda item: item["price"], reverse=True)
        for idx, item in enumerate(sorted_items[: min(50, len(sorted_items))]):
            competitors.append(
                {
                    "competitor": f"Competitor {category[:18]} {idx + 1}",
                    "sku": f"CMP-{item['sku'][:8]}-{idx + 1}",
                    "tier": "premium" if item["price"] >= 3000 else "mass",
                    "features": item.get("features", [])[:4],
                }
            )

    return competitors


def build_performance(catalog: List[Dict[str, Any]], reviews: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    random.seed(42)
    rating_by_sku: Dict[str, List[float]] = defaultdict(list)

    for review in reviews:
        sku = review["sku"]
        rating_by_sku[sku].append(float(review.get("rating", 0)))

    perf: List[Dict[str, Any]] = []
    for item in catalog:
        sku = item["sku"]
        stock = float(item.get("stock", 100))
        price = float(item.get("price", 1000))
        ratings = rating_by_sku.get(sku, [])
        avg_rating = sum(ratings) / len(ratings) if ratings else 3.8

        views = int(max(250, stock * random.randint(18, 45)))
        conversion_base = 1.2 + (avg_rating - 3.5) * 0.8
        conversion_pct = min(6.5, max(0.7, conversion_base))
        conversions = int(max(8, (views * conversion_pct) / 100))
        return_rate_pct = max(2.0, 16.0 - avg_rating * 2.4)
        returns = int(max(1, (conversions * return_rate_pct) / 100))

        perf.append(
            {
                "sku": sku,
                "views": views,
                "conversions": conversions,
                "returns": returns,
                "estimated_from": "catalog+reviews",
            }
        )

    return perf


def write_json(path: Path, data: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare agent-ready datasets from raw CSV files.")
    parser.add_argument(
        "--raw",
        default="datasets/raw/amazon.csv",
        help="Raw product review CSV path (default: datasets/raw/amazon.csv).",
    )
    parser.add_argument(
        "--out-dir",
        default="datasets/processed",
        help="Output directory for processed JSON files.",
    )
    parser.add_argument(
        "--limit",
        default=5000,
        type=int,
        help="Maximum rows to process from raw CSV.",
    )
    args = parser.parse_args()

    root = Path.cwd()
    raw_path = Path(args.raw)
    raw_path = raw_path if raw_path.is_absolute() else root / raw_path

    if not raw_path.exists():
        raise FileNotFoundError(f"Raw CSV not found: {raw_path}")

    out_dir = Path(args.out_dir)
    out_dir = out_dir if out_dir.is_absolute() else root / out_dir

    rows = read_csv_rows(raw_path, args.limit)
    if not rows:
        raise ValueError("No rows found in raw CSV.")

    catalog = build_catalog(rows)
    reviews = build_reviews(rows)
    pricing = build_pricing(rows)
    competitors = build_competitors(catalog)
    performance = build_performance(catalog, reviews)

    write_json(out_dir / "catalog.json", catalog)
    write_json(out_dir / "reviews.json", reviews)
    write_json(out_dir / "pricing.json", pricing)
    write_json(out_dir / "competitors.json", competitors)
    write_json(out_dir / "performance_signals.json", performance)

    summary = {
        "raw_source": str(raw_path),
        "rows_read": len(rows),
        "catalog_records": len(catalog),
        "review_records": len(reviews),
        "pricing_records": len(pricing),
        "competitor_records": len(competitors),
        "performance_records": len(performance),
        "notes": [
            "competitors and performance_signals are derived for analysis compatibility.",
            "replace derived files with true marketplace feeds for production-grade accuracy.",
        ],
    }

    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"Processed datasets written to: {out_dir}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

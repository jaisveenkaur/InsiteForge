"""
Unit tests for the research agent core logic.
Tests metric computation, confidence scoring, and report generation.
"""

import pytest
from pathlib import Path
from statistics import mean

from src.research_agent import (
    as_float,
    review_metrics,
    price_gap_metrics,
    performance_metrics,
    score_confidence,
    calculate_completeness,
)


def test_as_float():
    """Test numeric conversion."""
    assert as_float(4.5) == 4.5
    assert as_float("3.14") == 3.14
    assert as_float("50%") == 50.0
    assert as_float(None) is None
    assert as_float("invalid") is None


def test_review_metrics():
    """Test review aggregation."""
    reviews = [
        {"rating": 5.0, "text": "Great"},
        {"rating": 4.0, "text": "Good"},
        {"rating": 2.0, "text": "Poor"},
        {"rating": 1.0, "text": "Terrible"},
    ]
    metrics = review_metrics(reviews, negative_only=False)
    assert metrics["review_count_used"] == 4
    assert metrics["average_rating"] == 3.0
    assert metrics["negative_share_pct"] == 50.0


def test_price_gap_metrics():
    """Test pricing analysis."""
    pricing = [
        {"our_price": 100, "competitor_price": 80},
        {"our_price": 50, "competitor_price": 60},
    ]
    metrics = price_gap_metrics(pricing, premium_only=False)
    assert metrics["pair_count"] == 2
    assert metrics["avg_price_gap_pct"] == 5.0
    assert metrics["over_priced_share_pct"] == 50.0


def test_performance_metrics():
    """Test conversion and return rates."""
    perf = [
        {"sku": "SKU1", "views": 100, "conversions": 5, "returns": 1},
        {"sku": "SKU2", "views": 50, "conversions": 0, "returns": 0},
    ]
    metrics = performance_metrics(perf)
    assert metrics["avg_conversion_pct"] == pytest.approx(5.0, rel=0.1)
    assert metrics["avg_return_pct"] == 20.0


def test_calculate_completeness():
    """Test data completeness scoring."""
    from src.research_agent import SourcePayload
    
    payloads = {
        "catalog": SourcePayload(name="catalog", records=[{"sku": "1"}], loaded_from="inline"),
        "reviews": SourcePayload(name="reviews", records=[{"rating": 5}], loaded_from="inline"),
        "pricing": SourcePayload(name="pricing", records=[], loaded_from="none"),
        "competitors": SourcePayload(name="competitors", records=[], loaded_from="none"),
        "performance_signals": SourcePayload(name="performance_signals", records=[], loaded_from="none"),
    }
    score, label, missing = calculate_completeness(payloads)
    assert score == 40
    assert label == "Low"
    assert "pricing" in missing


def test_score_confidence():
    """Test confidence score calculation."""
    from src.research_agent import SourcePayload
    
    payloads = {
        "catalog": SourcePayload(name="catalog", records=[{"sku": str(i)} for i in range(100)], loaded_from="inline"),
        "reviews": SourcePayload(name="reviews", records=[{"rating": 5} for _ in range(50)], loaded_from="inline"),
        "pricing": SourcePayload(name="pricing", records=[{"price": 100} for _ in range(30)], loaded_from="inline"),
        "competitors": SourcePayload(name="competitors", records=[], loaded_from="none"),
        "performance_signals": SourcePayload(name="performance_signals", records=[], loaded_from="none"),
    }
    confidence = score_confidence(60, [], payloads)
    assert 30 <= confidence <= 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Schema validation and normalization for research briefs.
Ensures incoming requests conform to system expectations.
"""

from typing import Any, Dict, List
from pydantic import BaseModel, Field, validator


class ScopeModel(BaseModel):
    marketplaces: List[str] = Field(default=["Unknown"])
    category_or_product: str = Field(default="Unknown")
    region: str = Field(default="Unknown")
    timeframe: str = Field(default="Unspecified")


class DataSourceModel(BaseModel):
    path: str = ""


class ResearchBriefModel(BaseModel):
    mode: str
    business_goal: str
    scope: ScopeModel
    data_sources: Dict[str, Any] = {}
    constraints: List[str] = []
    query: str = ""
    query_type: str = ""
    kpi_priority: List[str] = []
    analysis_theme: str = ""

    @validator("mode")
    def validate_mode(cls, v):
        valid = {"quick", "deep"}
        if v.lower() not in valid:
            raise ValueError(f"Mode must be one of {valid}")
        return v.lower()

    @validator("business_goal")
    def validate_business_goal(cls, v):
        valid = {"growth", "retention", "profitability", "market expansion"}
        if v.lower() not in valid:
            raise ValueError(f"Business goal must be one of {valid}")
        return v.lower()


class AnalysisRequestModel(BaseModel):
    brief: ResearchBriefModel
    update_memory: bool = False
    memory_path: str = "data/domain_memory.json"
    source_base_dir: str = "datasets/processed"
    output_path: str = ""


def validate_brief(brief: Dict[str, Any]) -> ResearchBriefModel:
    """Validate and normalize a research brief."""
    try:
        return ResearchBriefModel(**brief)
    except Exception as e:
        raise ValueError(f"Invalid brief schema: {str(e)}")

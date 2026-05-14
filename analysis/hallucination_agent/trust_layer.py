# analysis/hallucination_agent/trust_layer.py

"""
Aggregate HallucinationItem list → TrustLayer summary for frontend.
"""
from analysis.models.analysis_models import HallucinationResult, HallucinationItem
from typing import List

def build_trust_layer(items: List[HallucinationItem], filename: str = None) -> HallucinationResult:
    return HallucinationResult(
        valid_count=sum(1 for i in items if i.status == "valid"),
        deprecated_count=sum(1 for i in items if i.status == "deprecated"),
        hallucinated_count=sum(1 for i in items if i.status == "hallucinated"),
        items=items,
        file_analyzed=filename,
    )

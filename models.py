from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, field_validator


class Component(BaseModel):
    reference: str = Field(..., description="Schematic designator, e.g. R1, C2, U1")
    part_name: str = Field(..., description="Human-readable part name")
    value: str = Field(..., description="Component value with units, e.g. 10kΩ, 100nF")
    quantity: int = Field(..., ge=1)
    notes: Optional[str] = Field(None, description="Tolerance, rating, substitution hints")

    @field_validator("reference")
    @classmethod
    def reference_nonempty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Component reference must not be empty")
        return v


class BOM(BaseModel):
    components: list[Component] = Field(default_factory=list)
    is_complete: bool = Field(True)
    completeness_note: Optional[str] = Field(None)

    @property
    def total_components(self) -> int:
        return sum(c.quantity for c in self.components)


class CircuitSpec(BaseModel):
    name: str = Field(..., description="Spec name, e.g. Frequency, Duty Cycle")
    value: str = Field(..., description="Spec value with units, e.g. 1 kHz, 50%")
    relevance: Optional[str] = Field(None, description="How this spec relates to user requirements")


class Circuit(BaseModel):
    name: str
    description: str = Field(..., description="2-4 sentence plain-English description")
    circuit_type: str = Field(..., description="astable|monostable|bistable|schmitt-trigger|pwm|other")
    key_specs: list[CircuitSpec] = Field(default_factory=list)
    match_explanation: str = Field(..., description="How this circuit matches the user's requirements")
    bom: BOM = Field(default_factory=BOM)
    source_url: str
    source_title: str
    additional_urls: list[str] = Field(default_factory=list)
    search_query_used: str = Field("", description="Debug metadata — not shown in PDF")


class SearchResult(BaseModel):
    url: str
    title: str
    raw_content: str
    fetch_method: str = Field("unknown", description="tavily | serpapi+scrape | direct_scrape")

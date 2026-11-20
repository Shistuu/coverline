from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import Status


class SubmissionIn(BaseModel):
    business_name: str = Field(min_length=1, max_length=200)
    state: str = Field(min_length=2, max_length=2)
    annual_revenue: int = Field(gt=0)
    seats: int = Field(ge=0)
    liquor_pct: int = Field(ge=0, le=100)
    years_in_business: int = Field(ge=0)
    prior_claims: int = Field(ge=0)

    @field_validator("state")
    @classmethod
    def upper_state(cls, v: str) -> str:
        return v.upper()


class DecisionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    actor: str
    outcome: str
    rule: str
    reason: str
    created_at: datetime


class SubmissionOut(SubmissionIn):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: Status
    premium_cents: int | None
    created_at: datetime
    decisions: list[DecisionOut]


class UnderwriterAction(BaseModel):
    underwriter: str = Field(min_length=1, max_length=100)
    action: Literal["approve", "decline"]
    note: str = Field(min_length=1)
    # Lets the underwriter change the engine's price when approving. Leave empty to keep it.
    premium_cents: int | None = Field(default=None, gt=0)

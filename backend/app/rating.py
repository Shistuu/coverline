"""Rating engine for restaurant general liability.

Pure functions only: no database and no I/O. That keeps every pricing and
eligibility decision easy to test and easy to explain.

The numbers below are made up for a demo. They are not real insurance rates.
"""

from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from typing import Literal

from app.schemas import SubmissionIn

Outcome = Literal["quote", "refer", "decline"]

SUPPORTED_STATES = {"NY", "NJ", "CT", "PA", "OH", "IL", "TX", "FL", "CA"}

BASE_RATE_PER_1K_REVENUE = Decimal("2.50")
MINIMUM_PREMIUM = Decimal("750.00")


@dataclass(frozen=True)
class RuleHit:
    rule: str
    outcome: Outcome
    reason: str


@dataclass
class RatingResult:
    outcome: Outcome
    premium_cents: int | None
    hits: list[RuleHit] = field(default_factory=list)


def eligibility(s: SubmissionIn) -> list[RuleHit]:
    """Return every rule that fires. A decline beats a refer, and a refer beats a quote."""
    hits: list[RuleHit] = []

    if s.state not in SUPPORTED_STATES:
        hits.append(RuleHit("state_not_supported", "decline", f"We don't write in {s.state} yet."))
    if s.liquor_pct > 50:
        hits.append(
            RuleHit("liquor_over_50", "decline", f"Alcohol is {s.liquor_pct}% of sales (limit 50%).")
        )
    if s.prior_claims >= 4:
        hits.append(
            RuleHit("too_many_claims", "decline", f"{s.prior_claims} claims in 3 years (limit 3).")
        )

    if s.years_in_business < 2:
        hits.append(
            RuleHit("new_business", "refer", f"Only {s.years_in_business} year(s) in business.")
        )
    if s.annual_revenue > 5_000_000:
        hits.append(RuleHit("large_risk", "refer", "Revenue over $5M needs an underwriter."))
    if 30 < s.liquor_pct <= 50:
        hits.append(
            RuleHit("liquor_30_to_50", "refer", f"Alcohol is {s.liquor_pct}% of sales.")
        )

    # TODO(you): add a rule of your own, e.g. seats per $100K revenue looks off -> refer.
    return hits


def premium(s: SubmissionIn) -> Decimal:
    """Base rate on revenue, times a factor for alcohol and one for loss history."""
    base = Decimal(s.annual_revenue) / 1000 * BASE_RATE_PER_1K_REVENUE
    liquor_factor = 1 + Decimal(s.liquor_pct) / 100
    claims_factor = 1 + Decimal("0.15") * s.prior_claims
    # TODO(you): add a state factor (e.g. NY and CA cost more than OH).
    return max(base * liquor_factor * claims_factor, MINIMUM_PREMIUM)


def rate(s: SubmissionIn) -> RatingResult:
    hits = eligibility(s)
    outcomes = {h.outcome for h in hits}

    if "decline" in outcomes:
        return RatingResult("decline", None, hits)

    cents = int((premium(s) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    if "refer" in outcomes:
        # Price it anyway so the underwriter has a starting number.
        return RatingResult("refer", cents, hits)

    hits.append(RuleHit("auto_quote", "quote", "Passed every eligibility rule."))
    return RatingResult("quote", cents, hits)

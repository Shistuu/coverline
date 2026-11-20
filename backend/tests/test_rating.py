from app.rating import rate
from app.schemas import SubmissionIn


def make(**overrides) -> SubmissionIn:
    base = dict(
        business_name="Joe's Pizza",
        state="NY",
        annual_revenue=1_000_000,
        seats=40,
        liquor_pct=10,
        years_in_business=5,
        prior_claims=0,
    )
    base.update(overrides)
    return SubmissionIn(**base)


def rules(result) -> set[str]:
    return {h.rule for h in result.hits}


def test_clean_restaurant_gets_quoted():
    r = rate(make())
    assert r.outcome == "quote"
    # 1,000,000 / 1000 * 2.50 = 2500; * 1.10 liquor = 2750
    assert r.premium_cents == 275_000


def test_minimum_premium_applies():
    r = rate(make(annual_revenue=50_000, liquor_pct=0))
    assert r.premium_cents == 75_000


def test_claims_raise_the_price():
    clean = rate(make()).premium_cents
    with_claims = rate(make(prior_claims=2)).premium_cents
    assert with_claims > clean


def test_heavy_liquor_is_declined():
    r = rate(make(liquor_pct=60))
    assert r.outcome == "decline"
    assert r.premium_cents is None
    assert "liquor_over_50" in rules(r)


def test_unsupported_state_is_declined():
    r = rate(make(state="WY"))
    assert r.outcome == "decline"


def test_new_business_is_referred_with_a_price():
    r = rate(make(years_in_business=1))
    assert r.outcome == "refer"
    assert r.premium_cents is not None
    assert "new_business" in rules(r)


def test_decline_wins_over_refer_and_all_hits_are_kept():
    r = rate(make(liquor_pct=60, years_in_business=0))
    assert r.outcome == "decline"
    assert {"liquor_over_50", "new_business"} <= rules(r)

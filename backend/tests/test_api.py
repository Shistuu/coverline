"""API tests against an in-memory SQLite database (fast, no Postgres needed).

TODO(you): add a Postgres-backed run in CI (GitHub Actions service container).
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app

GOOD = dict(
    business_name="Joe's Pizza",
    state="ny",
    annual_revenue=1_000_000,
    seats=40,
    liquor_pct=10,
    years_in_business=5,
    prior_claims=0,
)


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, expire_on_commit=False)

    def override():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_quote_then_bind(client):
    r = client.post("/submissions", json=GOOD)
    assert r.status_code == 201
    sub = r.json()
    assert sub["status"] == "quoted"
    assert sub["state"] == "NY"
    assert sub["decisions"][0]["rule"] == "auto_quote"

    r = client.post(f"/submissions/{sub['id']}/bind")
    assert r.json()["status"] == "bound"
    assert [d["rule"] for d in r.json()["decisions"]] == ["auto_quote", "bind"]


def test_referral_goes_to_queue_and_underwriter_approves(client):
    sub = client.post("/submissions", json={**GOOD, "years_in_business": 1}).json()
    assert sub["status"] == "referred"

    queue = client.get("/submissions", params={"status": "referred"}).json()
    assert [s["id"] for s in queue] == [sub["id"]]

    r = client.post(
        f"/submissions/{sub['id']}/review",
        json={"underwriter": "Dana", "action": "approve", "note": "Owner ran a restaurant for 10 years.", "premium_cents": 300_000},
    )
    body = r.json()
    assert body["status"] == "quoted"
    assert body["premium_cents"] == 300_000
    assert body["decisions"][-1]["actor"] == "Dana"


def test_cannot_bind_a_referral(client):
    sub = client.post("/submissions", json={**GOOD, "years_in_business": 1}).json()
    assert client.post(f"/submissions/{sub['id']}/bind").status_code == 409


def test_cannot_review_a_quoted_submission(client):
    sub = client.post("/submissions", json=GOOD).json()
    r = client.post(
        f"/submissions/{sub['id']}/review",
        json={"underwriter": "Dana", "action": "decline", "note": "x"},
    )
    assert r.status_code == 409


def test_bad_input_is_rejected(client):
    assert client.post("/submissions", json={**GOOD, "liquor_pct": 150}).status_code == 422


def test_missing_submission_is_404(client):
    assert client.get("/submissions/999").status_code == 404

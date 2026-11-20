# Coverline

A small quote-and-bind tool for restaurant insurance.

A broker submits a restaurant's details. A rules-based rating engine either quotes it, declines it, or refers it to an underwriter. The underwriter reviews the referral, can change the price, and approves or declines it with a note. The broker binds the quote. Every step is written to an append-only decision log with the rule that triggered it.

The rates are made up. This is a demo, not real insurance pricing.

## Stack
- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic, PostgreSQL 16
- **Frontend:** React, TypeScript, Vite
- **Tests:** pytest (rating rules plus API flows)

## Run locally

Postgres needs to be running with a `coverline` database.

```bash
cd backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload        # http://localhost:8000/docs
pytest
```

```bash
cd frontend
npm install
npm run dev                          # http://localhost:5173
```

Set `DATABASE_URL` if your Postgres isn't at `postgresql+psycopg://localhost:5432/coverline`. Set `VITE_API_URL` if the API isn't at `http://localhost:8000`.

With Docker, `docker compose up` starts Postgres and the API together.

## API
| Method | Path | What it does |
|---|---|---|
| POST | `/submissions` | Rate a new submission and store it with its decision log |
| GET | `/submissions?status=referred` | List submissions (the underwriter queue) |
| GET | `/submissions/{id}` | One submission with its log |
| POST | `/submissions/{id}/review` | Underwriter approves or declines a referral |
| POST | `/submissions/{id}/bind` | Broker binds a quoted submission |

## How rating works
`backend/app/rating.py` is pure Python with no database, so every rule is unit-tested.
- **Decline:** unsupported state, alcohol over 50% of sales, 4+ claims in 3 years
- **Refer:** under 2 years in business, revenue over $5M, alcohol between 30% and 50%
- **Premium:** $2.50 per $1K of revenue × (1 + alcohol share) × (1 + 0.15 × claims), minimum $750

A decline beats a refer, and a refer beats a quote. All rules that fired are kept, not just the winning one.

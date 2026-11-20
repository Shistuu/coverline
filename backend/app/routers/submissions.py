from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.models import Decision, Status, Submission
from app.rating import rate
from app.schemas import SubmissionIn, SubmissionOut, UnderwriterAction

router = APIRouter(prefix="/submissions", tags=["submissions"])

ENGINE_TO_STATUS = {"quote": Status.quoted, "refer": Status.referred, "decline": Status.declined}


def _get(db: Session, submission_id: int) -> Submission:
    sub = db.scalar(
        select(Submission)
        .where(Submission.id == submission_id)
        .options(selectinload(Submission.decisions))
    )
    if sub is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Submission not found")
    return sub


@router.post("", response_model=SubmissionOut, status_code=status.HTTP_201_CREATED)
def create_submission(body: SubmissionIn, db: Session = Depends(get_db)) -> Submission:
    result = rate(body)
    sub = Submission(
        **body.model_dump(),
        status=ENGINE_TO_STATUS[result.outcome],
        premium_cents=result.premium_cents,
    )
    sub.decisions = [
        Decision(actor="rating_engine", outcome=h.outcome, rule=h.rule, reason=h.reason)
        for h in result.hits
    ]
    db.add(sub)
    db.commit()
    return _get(db, sub.id)


@router.get("", response_model=list[SubmissionOut])
def list_submissions(status: Status | None = None, db: Session = Depends(get_db)) -> list[Submission]:
    q = select(Submission).options(selectinload(Submission.decisions)).order_by(Submission.id.desc())
    if status is not None:
        q = q.where(Submission.status == status)
    return list(db.scalars(q))


@router.get("/{submission_id}", response_model=SubmissionOut)
def get_submission(submission_id: int, db: Session = Depends(get_db)) -> Submission:
    return _get(db, submission_id)


@router.post("/{submission_id}/review", response_model=SubmissionOut)
def review(submission_id: int, body: UnderwriterAction, db: Session = Depends(get_db)) -> Submission:
    sub = _get(db, submission_id)
    if sub.status != Status.referred:
        raise HTTPException(status.HTTP_409_CONFLICT, f"Submission is {sub.status.value}, not referred")

    if body.action == "approve":
        sub.status = Status.quoted
        if body.premium_cents is not None:
            sub.premium_cents = body.premium_cents
    else:
        sub.status = Status.declined
        sub.premium_cents = None

    sub.decisions.append(
        Decision(actor=body.underwriter, outcome=body.action, rule="underwriter_review", reason=body.note)
    )
    db.commit()
    return _get(db, submission_id)


@router.post("/{submission_id}/bind", response_model=SubmissionOut)
def bind(submission_id: int, db: Session = Depends(get_db)) -> Submission:
    sub = _get(db, submission_id)
    if sub.status != Status.quoted:
        raise HTTPException(status.HTTP_409_CONFLICT, f"Only quoted submissions can be bound (this one is {sub.status.value})")
    sub.status = Status.bound
    sub.decisions.append(
        Decision(actor="broker", outcome="bound", rule="bind", reason="Broker bound the quote.")
    )
    db.commit()
    return _get(db, submission_id)

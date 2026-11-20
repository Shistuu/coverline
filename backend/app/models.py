import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Status(str, enum.Enum):
    quoted = "quoted"
    referred = "referred"
    declined = "declined"
    bound = "bound"


class Submission(Base):
    """A broker's request for coverage for one restaurant."""

    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    business_name: Mapped[str] = mapped_column(String(200))
    state: Mapped[str] = mapped_column(String(2))
    annual_revenue: Mapped[int] = mapped_column(Integer)  # whole dollars
    seats: Mapped[int] = mapped_column(Integer)
    liquor_pct: Mapped[int] = mapped_column(Integer)  # share of sales from alcohol, 0-100
    years_in_business: Mapped[int] = mapped_column(Integer)
    prior_claims: Mapped[int] = mapped_column(Integer)  # claims in the last 3 years

    status: Mapped[Status] = mapped_column(Enum(Status, name="submission_status"))
    premium_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    decisions: Mapped[list["Decision"]] = relationship(
        back_populates="submission", order_by="Decision.id", cascade="all, delete-orphan"
    )


class Decision(Base):
    """Append-only audit log: every rule that fired and every underwriter action."""

    __tablename__ = "decisions"

    id: Mapped[int] = mapped_column(primary_key=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("submissions.id"), index=True)
    actor: Mapped[str] = mapped_column(String(100))  # "rating_engine" or an underwriter's name
    outcome: Mapped[str] = mapped_column(String(20))
    rule: Mapped[str] = mapped_column(String(100))
    reason: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    submission: Mapped[Submission] = relationship(back_populates="decisions")

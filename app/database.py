from datetime import datetime, timezone
from pathlib import Path
from typing import Generator

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    relationship,
    sessionmaker,
)

from .config import get_settings


settings = get_settings()


# ---------------------------------------------------------
# Database path setup
# ---------------------------------------------------------

if settings.database_url.startswith("sqlite:///"):
    db_path = settings.database_url.replace("sqlite:///", "", 1)

    if not db_path.startswith("/"):
        Path(db_path).parent.mkdir(
            parents=True,
            exist_ok=True,
        )


# ---------------------------------------------------------
# SQLAlchemy engine
# ---------------------------------------------------------

engine = create_engine(
    settings.database_url,
    connect_args={
        "check_same_thread": False
    }
    if settings.database_url.startswith("sqlite")
    else {},
)


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


# ---------------------------------------------------------
# Base class
# ---------------------------------------------------------

class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------
# Utility
# ---------------------------------------------------------

def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------
# User model
# ---------------------------------------------------------

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    user_id: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    age: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    weight: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    goal: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    intensity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        nullable=False,
    )

    plans: Mapped[list["Plan"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="Plan.created_at",
    )


# ---------------------------------------------------------
# Plan model
# ---------------------------------------------------------

class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    original_plan: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    updated_plan: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    nutrition_tip: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    feedback: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    user: Mapped[User] = relationship(
        back_populates="plans",
    )


# ---------------------------------------------------------
# Initialize database
# ---------------------------------------------------------

def init_db() -> None:
    Base.metadata.create_all(
        bind=engine,
    )


# ---------------------------------------------------------
# Database dependency
# ---------------------------------------------------------

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


# ---------------------------------------------------------
# User operations
# ---------------------------------------------------------

def save_user(
    db: Session,
    *,
    user_id: str,
    name: str,
    age: int,
    weight: float,
    goal: str,
    intensity: str,
) -> User:

    user = (
        db.query(User)
        .filter(User.user_id == user_id)
        .first()
    )

    if user:

        user.name = name
        user.age = age
        user.weight = weight
        user.goal = goal
        user.intensity = intensity

    else:

        user = User(
            user_id=user_id,
            name=name,
            age=age,
            weight=weight,
            goal=goal,
            intensity=intensity,
        )

        db.add(user)

    db.commit()
    db.refresh(user)

    return user


def get_user(
    db: Session,
    user_id: str,
) -> User | None:

    return (
        db.query(User)
        .filter(User.user_id == user_id)
        .first()
    )


def get_all_users(
    db: Session,
) -> list[User]:

    return (
        db.query(User)
        .order_by(User.created_at.desc())
        .all()
    )


def delete_user(
    db: Session,
    user_id: str,
) -> bool:

    user = get_user(
        db,
        user_id,
    )

    if not user:
        return False

    db.delete(user)
    db.commit()

    return True


# ---------------------------------------------------------
# Plan operations
# ---------------------------------------------------------

def save_plan(
    db: Session,
    *,
    user: User,
    original_plan: str,
    nutrition_tip: str,
) -> Plan:

    plan = Plan(
        user_id=user.id,
        original_plan=original_plan,
        nutrition_tip=nutrition_tip,
    )

    db.add(plan)
    db.commit()
    db.refresh(plan)

    return plan


def get_latest_plan(
    db: Session,
    user: User,
) -> Plan | None:

    return (
        db.query(Plan)
        .filter(Plan.user_id == user.id)
        .order_by(Plan.created_at.desc())
        .first()
    )


def get_original_plan(
    db: Session,
    user_id: str,
) -> Plan | None:

    user = get_user(
        db,
        user_id,
    )

    if not user:
        return None

    return get_latest_plan(
        db,
        user,
    )


def update_plan(
    db: Session,
    plan: Plan,
    *,
    updated_plan: str,
    feedback: str,
    nutrition_tip: str | None = None,
) -> Plan:

    plan.updated_plan = updated_plan
    plan.feedback = feedback
    plan.updated_at = utcnow()

    if nutrition_tip:
        plan.nutrition_tip = nutrition_tip

    db.commit()
    db.refresh(plan)

    return plan
from typing import Literal

from pydantic import BaseModel, Field, field_validator


Goal = Literal[
    "weight loss",
    "muscle gain",
    "general wellness",
    "flexibility",
]


Intensity = Literal[
    "low",
    "medium",
    "high",
]


class UserInput(BaseModel):

    user_id: str = Field(
        min_length=2,
        max_length=50,
        pattern=r"^[A-Za-z0-9_-]+$",
    )

    name: str = Field(
        min_length=2,
        max_length=100,
    )

    age: int = Field(
        ge=13,
        le=100,
    )

    weight: float = Field(
        gt=20,
        le=400,
    )

    goal: Goal

    intensity: Intensity

    @field_validator("name")
    @classmethod
    def clean_name(
        cls,
        value: str,
    ) -> str:

        return " ".join(
            value.strip().split()
        )


class FeedbackRequest(BaseModel):

    user_id: str = Field(
        min_length=2,
        max_length=50,
    )

    feedback: str = Field(
        min_length=3,
        max_length=1000,
    )


class GenerateResponse(BaseModel):

    user: UserInput
    workout_plan: str
    nutrition_tip: str
    plan_id: int


class FeedbackResponse(BaseModel):

    user_id: str
    updated_plan: str
    nutrition_tip: str
    feedback: str
    plan_id: int
import os


# ---------------------------------------------------------
# Test environment
# ---------------------------------------------------------

os.environ["DATABASE_URL"] = (
    "sqlite:///./data/test_fitbuddy.db"
)

os.environ["GEMINI_API_KEY"] = "test-key"

os.environ["ADMIN_KEY"] = ""


# ---------------------------------------------------------
# Imports
# ---------------------------------------------------------

from fastapi.testclient import TestClient

from app.main import app

from app.database import (
    Base,
    engine,
)

from app.services import gemini_client


# ---------------------------------------------------------
# Reset test database
# ---------------------------------------------------------

Base.metadata.drop_all(
    bind=engine
)

Base.metadata.create_all(
    bind=engine
)


client = TestClient(app)


# ---------------------------------------------------------
# Fake Gemini response
# ---------------------------------------------------------

def fake_generate(
    *,
    model: str,
    prompt: str,
    max_output_tokens: int = 4000,
    temperature: float = 0.7,
) -> str:

    if (
        "nutrition" in prompt.lower()
        or "recovery" in prompt.lower()
    ):

        return (
            "Drink water regularly and include "
            "a balanced protein-rich food with meals."
        )

    return "\n".join(
        [
            (
                f"Day {i}: Full-body training\n"
                "- Warm-up: 5 minutes\n"
                "- Squats: 3 x 10\n"
                "- Cooldown: 5 minutes"
            )
            for i in range(1, 8)
        ]
    )


gemini_client.generate_text = fake_generate


# ---------------------------------------------------------
# Test health endpoint
# ---------------------------------------------------------

def test_health():

    response = client.get(
        "/health"
    )

    assert response.status_code == 200

    assert response.json()["status"] == "ok"


# ---------------------------------------------------------
# Test home page
# ---------------------------------------------------------

def test_home():

    response = client.get(
        "/"
    )

    assert response.status_code == 200

    assert "Build your plan" in response.text


# ---------------------------------------------------------
# Test API workout generation
# ---------------------------------------------------------

def test_api_workout(monkeypatch):

    monkeypatch.setattr(
        "app.routes.generate_workout_gemini",
        lambda user: fake_generate(
            model="x",
            prompt="workout",
        ),
    )

    monkeypatch.setattr(
        "app.routes.generate_nutrition_tip_with_flash",
        lambda user: fake_generate(
            model="x",
            prompt="nutrition recovery",
        ),
    )

    response = client.post(
        "/api/v1/workout",
        json={
            "user_id": "test001",
            "name": "Test User",
            "age": 25,
            "weight": 65,
            "goal": "muscle gain",
            "intensity": "medium",
        },
    )

    assert response.status_code == 200

    assert response.json()["plan_id"] > 0

    assert "Day 1" in (
        response.json()["workout_plan"]
    )


# ---------------------------------------------------------
# Test feedback
# ---------------------------------------------------------

def test_feedback(monkeypatch):

    monkeypatch.setattr(
        "app.routes.update_workout_plan",
        lambda **kwargs: (
            "Updated Day 1\n"
            "Updated Day 2"
        ),
    )

    response = client.post(
        "/api/v1/feedback",
        json={
            "user_id": "test001",
            "feedback": "Add more cardio",
        },
    )

    assert response.status_code == 200

    assert (
        "Updated Day 1"
        in response.json()["updated_plan"]
    )


# ---------------------------------------------------------
# Test missing user
# ---------------------------------------------------------

def test_unknown_feedback_user():

    response = client.post(
        "/api/v1/feedback",
        json={
            "user_id": "missing",
            "feedback": "Add rest",
        },
    )

    assert response.status_code == 404
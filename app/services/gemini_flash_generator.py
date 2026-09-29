from ..config import get_settings
from ..schemas import UserInput

from .gemini_client import generate_text


def generate_nutrition_tip_with_flash(
    user: UserInput,
) -> str:

    settings = get_settings()

    prompt = f"""
You are FitBuddy's nutrition and recovery assistant.

Give ONE concise, practical nutrition or recovery tip.

USER PROFILE
------------
Age: {user.age}
Weight: {user.weight} kg
Goal: {user.goal}
Workout intensity: {user.intensity}

RULES
-----

- Keep the answer to 2-4 sentences.
- Prioritize balanced meals.
- Mention hydration when useful.
- Mention protein or whole foods when relevant.
- Mention sleep/recovery when useful.
- Encourage sustainable habits.
- Avoid medical claims.
- Avoid dangerous dieting.
- Do not prescribe medical treatment.
- Do not provide a long meal plan.

Return only the tip.
"""

    return generate_text(
        model=settings.gemini_tip_model,
        prompt=prompt,
        max_output_tokens=500,
        temperature=0.5,
    )
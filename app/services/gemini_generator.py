from ..config import get_settings
from ..schemas import UserInput

from .gemini_client import generate_text


def generate_workout_gemini(
    user: UserInput,
) -> str:

    settings = get_settings()

    prompt = f"""
You are FitBuddy, an AI fitness planning assistant.

Create a practical and personalized 7-day workout plan.

USER PROFILE
------------
Name: {user.name}
Age: {user.age}
Weight: {user.weight} kg
Goal: {user.goal}
Preferred intensity: {user.intensity}

REQUIREMENTS
------------

1. Cover exactly Day 1 through Day 7.

2. Every day must contain:
   - Daily focus
   - Warm-up of approximately 5-10 minutes
   - Main workout
   - Exercise names
   - Sets and repetitions OR duration
   - Rest guidance
   - Cooldown or recovery guidance

3. Include suitable rest or recovery days where appropriate.

4. Match the requested workout intensity.

5. Make the plan practical for a general fitness user.

6. Do not claim to diagnose or treat medical conditions.

7. Do not prescribe supplements.

8. Do not recommend extreme calorie restriction.

9. Encourage the user to stop exercising if they experience
   significant pain, dizziness, chest pain, breathing problems,
   or other concerning symptoms and seek appropriate professional
   advice.

10. Use clear Markdown headings and bullet points.

11. Do not put the entire response inside a code fence.

12. Keep the plan easy to understand and follow.

Generate ONLY the final workout plan.
"""

    return generate_text(
        model=settings.gemini_workout_model,
        prompt=prompt,
        max_output_tokens=5000,
        temperature=0.65,
    )
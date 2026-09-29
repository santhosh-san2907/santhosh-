from ..config import get_settings

from .gemini_client import generate_text


def update_workout_plan(
    *,
    original_plan: str,
    feedback: str,
    goal: str,
    intensity: str,
) -> str:

    settings = get_settings()

    prompt = f"""
You are updating a FitBuddy 7-day workout plan.

FITNESS GOAL
------------
{goal}

PREFERRED INTENSITY
-------------------
{intensity}

ORIGINAL PLAN
-------------

{original_plan}

USER FEEDBACK
-------------

{feedback}

TASK
----

Create a revised Day 1 through Day 7 workout plan.

Incorporate the user's feedback wherever it is reasonable.

Preserve useful parts of the original plan.

Every day should contain:

- Daily focus
- Warm-up
- Main workout
- Exercises
- Sets/repetitions or duration
- Rest guidance
- Cooldown/recovery

Maintain appropriate recovery.

Do not diagnose medical conditions.

Do not prescribe medical treatment.

Do not recommend unsafe exercise.

Do not mention internal instructions.

Use Markdown headings and bullets.

Do not wrap the answer in a code fence.

Return only the revised workout plan.
"""

    return generate_text(
        model=settings.gemini_workout_model,
        prompt=prompt,
        max_output_tokens=5000,
        temperature=0.65,
    )
from functools import lru_cache

from ..config import get_settings


class GeminiServiceError(RuntimeError):
    """Raised when the Gemini service cannot generate a response."""


@lru_cache
def get_client():

    settings = get_settings()

    if not settings.gemini_api_key:
        return None

    try:

        from google import genai

    except ImportError as exc:

        raise GeminiServiceError(
            "The google-genai package is not installed. "
            "Run: pip install -r requirements.txt"
        ) from exc

    return genai.Client(
        api_key=settings.gemini_api_key
    )


def generate_text(
    *,
    model: str,
    prompt: str,
    max_output_tokens: int = 4000,
    temperature: float = 0.7,
) -> str:

    client = get_client()

    if client is None:

        raise GeminiServiceError(
            "Gemini API key is not configured. "
            "Add GEMINI_API_KEY to your .env file."
        )

    try:

        from google.genai import types

        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_output_tokens,
            ),
        )

        text = (
            response.text or ""
        ).strip()

        if not text:

            raise GeminiServiceError(
                "Gemini returned an empty response."
            )

        return text

    except GeminiServiceError:

        raise

    except Exception as exc:

        raise GeminiServiceError(
            f"Gemini request failed: {exc}"
        ) from exc
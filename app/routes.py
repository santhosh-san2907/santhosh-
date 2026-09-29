from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    Form,
    HTTPException,
    Request,
    status,
)

from fastapi.responses import (
    HTMLResponse,
    JSONResponse,
    RedirectResponse,
)

from fastapi.templating import Jinja2Templates

from sqlalchemy.orm import Session

from .config import get_settings

from .database import (
    delete_user,
    get_all_users,
    get_db,
    get_original_plan,
    save_plan,
    save_user,
    update_plan,
)

from .schemas import (
    FeedbackRequest,
    FeedbackResponse,
    GenerateResponse,
    UserInput,
)

from .services.gemini_client import GeminiServiceError

from .services.gemini_flash_generator import (
    generate_nutrition_tip_with_flash,
)

from .services.gemini_generator import (
    generate_workout_gemini,
)

from .services.updated_plan import (
    update_workout_plan,
)


router = APIRouter()


# ---------------------------------------------------------
# Templates
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

templates = Jinja2Templates(
    directory=str(
        BASE_DIR / "templates"
    )
)


settings = get_settings()


# ---------------------------------------------------------
# Error helper
# ---------------------------------------------------------

def render_error(
    request: Request,
    message: str,
    status_code: int = 400,
):

    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "request": request,
            "message": message,
        },
        status_code=status_code,
    )


# ---------------------------------------------------------
# Home page
# ---------------------------------------------------------

@router.get(
    "/",
    response_class=HTMLResponse,
    name="home",
)
def home(request: Request):

    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "request": request,
        },
    )


# ---------------------------------------------------------
# Generate workout - HTML
# ---------------------------------------------------------

@router.post(
    "/generate-workout",
    response_class=HTMLResponse,
    name="generate_workout",
)
def generate_workout(
    request: Request,

    user_id: str = Form(...),

    name: str = Form(...),

    age: int = Form(...),

    weight: float = Form(...),

    goal: str = Form(...),

    intensity: str = Form(...),

    db: Session = Depends(get_db),
):

    try:

        user_input = UserInput(
            user_id=user_id,
            name=name,
            age=age,
            weight=weight,
            goal=goal,
            intensity=intensity,
        )

        workout = generate_workout_gemini(
            user_input
        )

        tip = generate_nutrition_tip_with_flash(
            user_input
        )

        user = save_user(
            db,
            **user_input.model_dump(),
        )

        plan = save_plan(
            db,
            user=user,
            original_plan=workout,
            nutrition_tip=tip,
        )

        return templates.TemplateResponse(
            request,
            "result.html",
            {
                "request": request,
                "user": user,
                "plan": plan,
                "display_plan": workout,
                "message": None,
            },
        )

    except GeminiServiceError as exc:

        return render_error(
            request,
            str(exc),
            503,
        )

    except Exception as exc:

        return render_error(
            request,
            f"Could not generate the plan: {exc}",
            400,
        )


# ---------------------------------------------------------
# Submit feedback - HTML
# ---------------------------------------------------------

@router.post(
    "/submit-feedback",
    response_class=HTMLResponse,
    name="submit_feedback",
)
def submit_feedback(
    request: Request,

    user_id: str = Form(...),

    feedback: str = Form(...),

    db: Session = Depends(get_db),
):

    try:

        data = FeedbackRequest(
            user_id=user_id,
            feedback=feedback,
        )

        plan = get_original_plan(
            db,
            data.user_id,
        )

        if not plan:

            return render_error(
                request,
                "No plan was found for that User ID. "
                "Generate a plan first.",
                404,
            )

        user = plan.user

        revised = update_workout_plan(
            original_plan=(
                plan.updated_plan
                or plan.original_plan
            ),
            feedback=data.feedback,
            goal=user.goal,
            intensity=user.intensity,
        )

        updated = update_plan(
            db,
            plan,
            updated_plan=revised,
            feedback=data.feedback,
        )

        return templates.TemplateResponse(
            request,
            "result.html",
            {
                "request": request,
                "user": user,
                "plan": updated,
                "display_plan": revised,
                "message": (
                    "Your plan has been updated "
                    "using your feedback."
                ),
            },
        )

    except GeminiServiceError as exc:

        return render_error(
            request,
            str(exc),
            503,
        )

    except Exception as exc:

        return render_error(
            request,
            f"Could not update the plan: {exc}",
            400,
        )


# ---------------------------------------------------------
# Admin dashboard
# ---------------------------------------------------------

@router.get(
    "/view-all-users",
    response_class=HTMLResponse,
    name="view_all_users",
)
def view_all_users(
    request: Request,

    admin_key: str | None = None,

    db: Session = Depends(get_db),
):

    if (
        settings.admin_key
        and admin_key != settings.admin_key
    ):

        return render_error(
            request,
            "Admin access denied. "
            "Provide the configured admin key.",
            403,
        )

    users = get_all_users(db)

    return templates.TemplateResponse(
        request,
        "all_users.html",
        {
            "request": request,
            "users": users,
            "admin_key": admin_key or "",
        },
    )


# ---------------------------------------------------------
# Delete user
# ---------------------------------------------------------

@router.post(
    "/delete-user/{user_id}",
    name="delete_user_route",
)
def delete_user_route(
    user_id: str,

    admin_key: str | None = Form(None),

    db: Session = Depends(get_db),
):

    if (
        settings.admin_key
        and admin_key != settings.admin_key
    ):

        raise HTTPException(
            status_code=403,
            detail="Admin access denied",
        )

    deleted = delete_user(
        db,
        user_id,
    )

    if not deleted:

        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    redirect_url = "/view-all-users"

    if settings.admin_key:

        redirect_url += (
            f"?admin_key={settings.admin_key}"
        )

    return RedirectResponse(
        url=redirect_url,
        status_code=status.HTTP_303_SEE_OTHER,
    )


# ---------------------------------------------------------
# API - Generate workout
# ---------------------------------------------------------

@router.post(
    "/api/v1/workout",
    response_model=GenerateResponse,
)
def api_generate_workout(
    payload: UserInput,

    db: Session = Depends(get_db),
):

    try:

        workout = generate_workout_gemini(
            payload
        )

        tip = generate_nutrition_tip_with_flash(
            payload
        )

        user = save_user(
            db,
            **payload.model_dump(),
        )

        plan = save_plan(
            db,
            user=user,
            original_plan=workout,
            nutrition_tip=tip,
        )

        return GenerateResponse(
            user=payload,
            workout_plan=workout,
            nutrition_tip=tip,
            plan_id=plan.id,
        )

    except GeminiServiceError as exc:

        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc


# ---------------------------------------------------------
# API - Feedback
# ---------------------------------------------------------

@router.post(
    "/api/v1/feedback",
    response_model=FeedbackResponse,
)
def api_feedback(
    payload: FeedbackRequest,

    db: Session = Depends(get_db),
):

    plan = get_original_plan(
        db,
        payload.user_id,
    )

    if not plan:

        raise HTTPException(
            status_code=404,
            detail="No plan found for this User ID",
        )

    user = plan.user

    try:

        revised = update_workout_plan(
            original_plan=(
                plan.updated_plan
                or plan.original_plan
            ),
            feedback=payload.feedback,
            goal=user.goal,
            intensity=user.intensity,
        )

        updated = update_plan(
            db,
            plan,
            updated_plan=revised,
            feedback=payload.feedback,
        )

        return FeedbackResponse(
            user_id=user.user_id,
            updated_plan=(
                updated.updated_plan
                or revised
            ),
            nutrition_tip=updated.nutrition_tip,
            feedback=(
                updated.feedback
                or payload.feedback
            ),
            plan_id=updated.id,
        )

    except GeminiServiceError as exc:

        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc


# ---------------------------------------------------------
# API - Users
# ---------------------------------------------------------

@router.get(
    "/api/v1/users",
)
def api_users(
    db: Session = Depends(get_db),
):

    if settings.admin_key:

        raise HTTPException(
            status_code=401,
            detail=(
                "Use the HTML admin endpoint "
                "with the configured admin key."
            ),
        )

    users = get_all_users(db)

    return JSONResponse(
        [
            {
                "user_id": user.user_id,
                "name": user.name,
                "age": user.age,
                "weight": user.weight,
                "goal": user.goal,
                "intensity": user.intensity,

                "plans": [
                    {
                        "id": plan.id,
                        "original_plan": (
                            plan.original_plan
                        ),
                        "updated_plan": (
                            plan.updated_plan
                        ),
                        "feedback": plan.feedback,
                        "created_at": (
                            plan.created_at.isoformat()
                        ),
                        "updated_at": (
                            plan.updated_at.isoformat()
                            if plan.updated_at
                            else None
                        ),
                    }

                    for plan in user.plans
                ],
            }

            for user in users
        ]
    )
from fastapi import APIRouter

from app.services.prompt import get_prompt_list

router = APIRouter(prefix="/prompt", tags=["prompt"])


@router.get("/list")
async def prompt_list():
    return get_prompt_list()

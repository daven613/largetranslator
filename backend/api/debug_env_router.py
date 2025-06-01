from fastapi import APIRouter, Depends
import os

router = APIRouter(prefix="/debug", tags=["debug"])

@router.get("/env-vars")
async def get_env_vars():
    return {
        "SUPABASE_KEY_from_env": os.getenv("SUPABASE_KEY", "Not Found"),
        "SUPABASE_ANON_KEY_from_env": os.getenv("SUPABASE_ANON_KEY", "Not Found"),
    } 
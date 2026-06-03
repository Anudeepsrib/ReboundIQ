from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    # Demo only: accept any, return fake JWT (real: verify hash, issue jose)
    if "@" not in req.email:
        raise HTTPException(400, "Invalid email")
    return {
        "access_token": "demo-jwt-for-slice." + req.email.split("@")[0],
        "user": {"id": "demo-user", "email": req.email, "name": "Demo User"},
    }


@router.post("/register")
async def register(req: LoginRequest):
    return {"message": "Registered (demo). Use /login."}

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from auth.keycloak_client import verify_token, extract_user
from typing import Optional

security = HTTPBearer(auto_error=False)

async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> dict:
    # If Bearer token present — verify with Keycloak
    if credentials:
        try:
            payload = verify_token(credentials.credentials)
            return extract_user(payload)
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
    # Fallback — API key auth mode, return anonymous user
    api_key = request.headers.get("X-API-Key", "")
    if api_key:
        return {
            "id": f"apikey-{api_key[:8]}",
            "username": "api-user",
            "email": None,
            "roles": ["analyst"],
        }
    return {
        "id": "anonymous",
        "username": "anonymous",
        "email": None,
        "roles": [],
    }

def require_role(role: str):
    async def role_checker(user: dict = Depends(get_current_user)):
        if role not in user["roles"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' required",
            )
        return user
    return role_checker

require_admin = require_role("admin")
require_analyst = require_role("analyst")

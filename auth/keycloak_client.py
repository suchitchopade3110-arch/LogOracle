import os
import httpx
from jose import jwt, JWTError
from loguru import logger
from functools import lru_cache

KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://localhost:8080")
REALM = os.getenv("KEYCLOAK_REALM", "logoracle")
CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID", "logoracle-api")
JWKS_URL = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/certs"

@lru_cache(maxsize=1)
def get_jwks() -> dict:
    response = httpx.get(JWKS_URL)
    response.raise_for_status()
    return response.json()

def verify_token(token: str) -> dict:
    try:
        jwks = get_jwks()
        payload = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            audience=CLIENT_ID,
            options={"verify_aud": False}
        )
        return payload
    except JWTError as e:
        logger.warning("Token verification failed: {}", str(e))
        raise

def extract_roles(payload: dict) -> list[str]:
    realm_access = payload.get("realm_access", {})
    return realm_access.get("roles", [])

def extract_user(payload: dict) -> dict:
    return {
        "id": payload.get("sub"),
        "username": payload.get("preferred_username"),
        "email": payload.get("email"),
        "roles": extract_roles(payload),
    }

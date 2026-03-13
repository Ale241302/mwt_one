"""JWT verification for mwt-knowledge (Camino B — JWT sin DB lookup)."""
import os, jwt
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

SECRET_KEY = os.environ.get("SECRET_KEY", "changeme")
ALGORITHM  = "HS256"

bearer = HTTPBearer()


def decode_token(credentials: HTTPAuthorizationCredentials = Security(bearer)) -> dict:
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload


def require_permission_jwt(permission: str):
    """FastAPI dependency — verifica permiso desde el payload JWT sin DB."""
    def _check(payload: dict = Security(decode_token)):
        perms = payload.get("permissions", [])
        if permission not in perms:
            raise HTTPException(status_code=403, detail=f"Permission required: {permission}")
        return payload
    return _check

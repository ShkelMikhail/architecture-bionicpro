from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
import httpx
from typing import List
from datetime import datetime
import random
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

KEYCLOAK_REALM = "reports-realm"
KEYCLOAK_URL = "http://keycloak:8080"
ALGORITHM = "RS256"
ROLE_REQUIRED = "prothetic_user"

JWKS_URL = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/certs"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
app = FastAPI()

origins = [
    "http://localhost:3000",
    "http://frontend:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

cached_jwks = None

async def get_jwks():
    global cached_jwks
    if cached_jwks is None:
        async with httpx.AsyncClient() as client:
            response = await client.get(JWKS_URL)
            response.raise_for_status()
            cached_jwks = response.json()
    return cached_jwks


async def verify_token(token: str = Depends(oauth2_scheme)):
    jwks = await get_jwks()
    try:
        logger.info(f"Проверка токена: {token[:40]}...")

        unverified_header = jwt.get_unverified_header(token)
        logger.info(f"Заголовок токена (kid): {unverified_header.get('kid')}")

        key = next(
            (k for k in jwks["keys"] if k["kid"] == unverified_header["kid"]), None
        )
        if key is None:
            logger.warning("Не найден открытый ключ для подписи")
            raise HTTPException(status_code=401, detail="Public key not found")

        payload = jwt.decode(token, key, algorithms=[ALGORITHM], options={"verify_aud": False})
        logger.info(f"Payload токена: {payload}")

        roles = payload.get("realm_access", {}).get("roles", [])
        logger.info(f"Роли пользователя: {roles}")

        if ROLE_REQUIRED not in roles:
            logger.warning("Нет нужной роли: prothetic_user")
            raise HTTPException(status_code=403, detail="Insufficient role")

        return payload

    except JWTError as e:
        logger.error(f"Ошибка валидации токена: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")


def generate_reports():
    return [
        {
            "id": i,
            "title": f"Report #{i}",
            "value": round(random.uniform(100, 1000), 2),
            "timestamp": datetime.now().isoformat(),
        }
        for i in range(1, 6)
    ]


@app.get("/reports")
async def get_reports(user=Depends(verify_token)):
    return {"reports": generate_reports()}

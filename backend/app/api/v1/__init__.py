from fastapi import APIRouter

from app.api.v1 import auth, cloud_accounts, health

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(cloud_accounts.router)

from fastapi import APIRouter

from app.api.routes import accountability_router, auth_router, blocking_router, reporting_router

api_router = APIRouter()
api_router.include_router(auth_router, tags=["auth"])
api_router.include_router(blocking_router, tags=["blocking"])
api_router.include_router(accountability_router, tags=["accountability"])
api_router.include_router(reporting_router, tags=["reporting"])

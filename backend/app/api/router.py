from __future__ import annotations

from fastapi import APIRouter

from backend.app.api.routes import images, listing, negotiation, sessions


api_router = APIRouter()
api_router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
api_router.include_router(images.router, prefix="/sessions", tags=["images"])
api_router.include_router(listing.router, prefix="/sessions", tags=["listing"])
api_router.include_router(negotiation.router, prefix="/sessions", tags=["negotiation"])


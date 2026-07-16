from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from backend.app.agent.graph import ReSaleAgentGraph
from backend.app.models.schemas import ListingResponse, PlatformCopy, PriceResult, SimilarItem
from backend.app.repositories.session_repository import SessionRepository
from backend.app.services.export_service import ExportService


router = APIRouter()
repo = SessionRepository()
graph = ReSaleAgentGraph()


@router.post("/{session_id}/listing/generate", response_model=ListingResponse)
def generate_listing(session_id: str) -> ListingResponse:
    state = repo.get(session_id)
    graph.generate_listing(state)
    repo.save(state)
    return ListingResponse(
        session_id=session_id,
        price=PriceResult(
            listing_price=state["listing_price"],
            deal_price_min=state["deal_price_min"],
            deal_price_max=state["deal_price_max"],
            suggested_floor_price=state["suggested_floor_price"],
            price_confidence=state["price_confidence"],
            price_reasons=state["price_reasons"],
            price_breakdown=state["price_breakdown"],
        ),
        similar_items=[SimilarItem(**item) for item in state.get("similar_items", [])],
        title=state["title"],
        description=state["description"],
        keywords=state["keywords"],
        defect_statement=state["defect_statement"],
        photo_suggestions=state["photo_suggestions"],
        platform_copies=[PlatformCopy(**item) for item in state.get("platform_copies", [])],
        trace=state.get("trace", []),
    )


@router.get("/{session_id}/export", response_class=PlainTextResponse)
def export_markdown(session_id: str) -> str:
    state = repo.get(session_id)
    return ExportService().build_markdown(state)

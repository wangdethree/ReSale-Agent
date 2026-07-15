from __future__ import annotations

from fastapi import APIRouter

from backend.app.agent.nodes import handle_negotiation_node
from backend.app.models.schemas import NegotiationRequest, NegotiationResponse
from backend.app.repositories.session_repository import SessionRepository


router = APIRouter()
repo = SessionRepository()


@router.post("/{session_id}/negotiation/reply", response_model=NegotiationResponse)
def generate_negotiation_reply(session_id: str, payload: NegotiationRequest) -> NegotiationResponse:
    state = repo.get(session_id)
    handle_negotiation_node(state, payload.buyer_message, payload.user_floor_price)
    result = state["last_negotiation"]
    repo.record_negotiation(session_id, payload.buyer_message, result["buyer_intent"], result["suggested_reply"])
    repo.save(state)
    return NegotiationResponse(**result)


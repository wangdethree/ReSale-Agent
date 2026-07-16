from __future__ import annotations

from fastapi import APIRouter

from backend.app.agent.graph import ReSaleAgentGraph
from backend.app.agent.nodes import confirm_product_node
from backend.app.models.schemas import (
    AnswerRequest,
    ConfirmRequest,
    NextQuestionResponse,
    OutcomeSummaryResponse,
    SaleOutcomeRequest,
    SaleStateResponse,
    SessionCreate,
    SessionSummary,
)
from backend.app.repositories.session_repository import SessionRepository
from backend.app.services.outcome_service import OutcomeService
from backend.app.tools.field_checker import get_question_for_field


router = APIRouter()
repo = SessionRepository()
graph = ReSaleAgentGraph()


@router.post("", response_model=SaleStateResponse)
def create_session(payload: SessionCreate) -> SaleStateResponse:
    state = repo.create(payload.category)
    return SaleStateResponse(session_id=state["session_id"], current_step=state["current_step"], state=state)


@router.get("", response_model=list[SessionSummary])
def list_sessions() -> list[SessionSummary]:
    return [SessionSummary(**item) for item in repo.list_recent()]


@router.get("/outcomes/summary", response_model=OutcomeSummaryResponse)
def get_outcome_summary() -> OutcomeSummaryResponse:
    return OutcomeSummaryResponse(**repo.outcome_summary())


@router.get("/{session_id}", response_model=SaleStateResponse)
def get_session(session_id: str) -> SaleStateResponse:
    state = repo.get(session_id)
    return SaleStateResponse(session_id=session_id, current_step=state["current_step"], state=state)


@router.delete("/{session_id}", status_code=204)
def delete_session(session_id: str) -> None:
    repo.delete(session_id)


@router.post("/{session_id}/outcome", response_model=SaleStateResponse)
def record_sale_outcome(session_id: str, payload: SaleOutcomeRequest) -> SaleStateResponse:
    state = repo.get(session_id)
    OutcomeService().record(state, payload.final_sold_price, payload.sold_channel, payload.sale_notes)
    repo.save(state)
    return SaleStateResponse(session_id=session_id, current_step=state["current_step"], state=state)


@router.post("/{session_id}/confirm", response_model=SaleStateResponse)
def confirm_product(session_id: str, payload: ConfirmRequest) -> SaleStateResponse:
    state = repo.get(session_id)
    confirm_product_node(state, payload.product.model_dump())
    graph.prepare_next_question(state)
    repo.save(state)
    return SaleStateResponse(session_id=session_id, current_step=state["current_step"], state=state)


@router.get("/{session_id}/questions/next", response_model=NextQuestionResponse)
def next_question(session_id: str) -> NextQuestionResponse:
    state = repo.get(session_id)
    graph.prepare_next_question(state)
    repo.save(state)
    missing = state.get("missing_fields", [])
    if not missing:
        return NextQuestionResponse(completed=True, missing_fields=[])
    field = missing[0]
    return NextQuestionResponse(
        completed=False,
        field=field,
        question=state.get("current_question") or get_question_for_field(field),
        missing_fields=missing,
    )


@router.post("/{session_id}/answers", response_model=NextQuestionResponse)
def submit_answer(session_id: str, payload: AnswerRequest) -> NextQuestionResponse:
    state = repo.get(session_id)
    field = payload.field.strip()
    value = payload.answer
    if field in {
        "product_type",
        "brand",
        "model",
        "color",
        "visible_condition",
        "original_price",
        "purchase_date",
        "functional_status",
        "repair_history",
        "accessories",
        "additional_defects",
        "delivery_options",
        "set_status",
        "notes_status",
        "damage_status",
    }:
        state[field] = value
    else:
        state.setdefault("user_answers", {})[field] = value

    graph.prepare_next_question(state)
    repo.save(state)
    missing = state.get("missing_fields", [])
    if not missing:
        return NextQuestionResponse(completed=True, missing_fields=[])
    next_field = missing[0]
    return NextQuestionResponse(
        completed=False,
        field=next_field,
        question=state.get("current_question") or get_question_for_field(next_field),
        missing_fields=missing,
    )

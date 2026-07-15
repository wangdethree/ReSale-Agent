from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, UploadFile

from backend.app.agent.nodes import analyze_images_node
from backend.app.core.config import get_settings
from backend.app.core.exceptions import AppError
from backend.app.models.schemas import AnalyzeImageResponse, ProductConfirmation, UploadValidation
from backend.app.repositories.session_repository import SessionRepository


router = APIRouter()
repo = SessionRepository()


@router.post("/{session_id}/images/analyze", response_model=AnalyzeImageResponse)
async def analyze_images(session_id: str, files: list[UploadFile] = File(...)) -> AnalyzeImageResponse:
    settings = get_settings()
    if not files:
        raise AppError("请至少上传 1 张图片")
    if len(files) > settings.max_images:
        raise AppError(f"最多只能上传 {settings.max_images} 张图片")

    state = repo.get(session_id)
    saved_paths: list[str] = []
    upload_dir = settings.upload_dir / session_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    for file in files:
        suffix = UploadValidation.normalize_suffix(file.filename or "")
        if not suffix:
            raise AppError("图片格式仅支持 JPG、JPEG、PNG")
        if file.content_type not in UploadValidation.allowed_content_types:
            raise AppError("图片 MIME 类型不合法")

        content = await file.read()
        if len(content) > settings.max_image_bytes:
            raise AppError("单张图片不能超过 10 MB")

        safe_name = f"{uuid4().hex}{suffix}"
        target = upload_dir / safe_name
        target.write_bytes(content)
        saved_paths.append(str(target))

    analyze_images_node(state, saved_paths)
    repo.save(state)
    product = ProductConfirmation(
        category=state["category"],
        product_type=state.get("product_type"),
        brand=state.get("brand"),
        model=state.get("model"),
        color=state.get("color"),
        visible_condition=state.get("visible_condition"),
        visible_defects=state.get("visible_defects", []),
        vision_confidence=state.get("vision_confidence"),
    )
    return AnalyzeImageResponse(session_id=session_id, image_paths=saved_paths, product=product)


from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any


TOKEN_PATTERN = re.compile(r"[a-z0-9]+|[\u4e00-\u9fff]+", re.IGNORECASE)
STOP_TOKENS = {
    "jpg",
    "jpeg",
    "png",
    "image",
    "img",
    "photo",
    "upload",
    "uploads",
    "tmp",
}


def build_image_query_signature(image_paths: list[str] | None, visual_keywords: list[str] | None = None) -> dict[str, Any]:
    """构建本地图片线索签名，不依赖外部图片库或模型服务。"""

    paths = image_paths or []
    keywords = visual_keywords or []
    file_hashes: list[str] = []
    total_bytes = 0
    token_sources = [*keywords]

    for image_path in paths:
        path = Path(image_path)
        token_sources.append(path.name)
        try:
            content = path.read_bytes()
        except OSError:
            continue
        if not content:
            continue
        total_bytes += len(content)
        file_hashes.append(hashlib.sha1(content).hexdigest())

    combined_hash = hashlib.sha1("".join(file_hashes).encode("utf-8")).hexdigest() if file_hashes else ""
    return {
        "has_image": bool(paths),
        "image_count": len(paths),
        "byte_count": total_bytes,
        "content_hash": combined_hash,
        "tokens": _tokenize(" ".join(str(source) for source in token_sources if source)),
    }


def score_image_similarity(item: dict[str, Any], signature: dict[str, Any]) -> tuple[int, list[str]]:
    """给本地模拟商品计算图片线索相似度，分数只用于候选排序和解释。"""

    if not signature.get("has_image"):
        return 0, []

    item_text = " ".join(
        str(item.get(key) or "")
        for key in ["category", "product_type", "brand", "model", "condition_level", "description"]
    )
    item_tokens = _tokenize(item_text)
    matched_tokens = _matched_tokens(signature.get("tokens", []), item_tokens, item_text)
    token_score = min(72, len(matched_tokens) * 12)
    hash_score = _hash_affinity(signature.get("content_hash") or "", item_text) if signature.get("content_hash") else 0
    score = min(100, token_score + hash_score)

    reasons: list[str] = []
    if matched_tokens:
        reasons.append("图片/识别线索命中：" + "、".join(matched_tokens[:4]))
    if hash_score:
        reasons.append("本地图片文件签名用于同分排序")
    return score, reasons


def _tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    for match in TOKEN_PATTERN.findall(text.lower()):
        token = match.strip("_- ")
        if len(token) < 2 or token in STOP_TOKENS:
            continue
        tokens.append(token)
    return list(dict.fromkeys(tokens))


def _matched_tokens(query_tokens: list[str], item_tokens: list[str], item_text: str) -> list[str]:
    matched: list[str] = []
    compact_item = "".join(item_tokens)
    normalized_item_text = item_text.lower().replace(" ", "")
    for token in query_tokens:
        if token in item_tokens or token in compact_item or token in normalized_item_text:
            matched.append(token)
            continue
        if any(token in item_token or item_token in token for item_token in item_tokens if len(item_token) >= 3):
            matched.append(token)
    return list(dict.fromkeys(matched))


def _hash_affinity(content_hash: str, item_text: str) -> int:
    item_hash = hashlib.sha1(item_text.encode("utf-8")).hexdigest()
    same_positions = sum(1 for left, right in zip(content_hash[:12], item_hash[:12], strict=False) if left == right)
    return min(8, same_positions)

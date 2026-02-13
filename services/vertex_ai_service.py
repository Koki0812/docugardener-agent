"""Vertex AI Gemini service — text and multimodal comparison."""
from __future__ import annotations

import logging
from typing import Any

import vertexai
from vertexai.generative_models import GenerativeModel, Part, Image

from config.settings import GCP_PROJECT_ID, GCP_LOCATION, GEMINI_MODEL

logger = logging.getLogger(__name__)

_model: GenerativeModel | None = None


def _get_model() -> GenerativeModel:
    """Lazily initialise Vertex AI and return the Gemini model."""
    global _model
    if _model is None:
        vertexai.init(project=GCP_PROJECT_ID, location=GCP_LOCATION)
        _model = GenerativeModel(GEMINI_MODEL)
        logger.info("Initialized Gemini model: %s", GEMINI_MODEL)
    return _model


# ---------------------------------------------------------------------------
# Text comparison
# ---------------------------------------------------------------------------

def compare_text(new_doc_text: str, old_doc_text: str) -> dict[str, Any]:
    """Use Gemini to find semantic contradictions between *new_doc_text* and *old_doc_text*.

    Returns a dict with keys ``contradictions`` (list) and ``summary``.
    """
    model = _get_model()
    prompt = f"""あなたはドキュメント品質管理の専門家です。
以下の「新しいドキュメント」と「古いドキュメント」を比較し、
意味的な矛盾や不整合を全て特定してください。

各矛盾について以下の形式で出力してください:
- 矛盾の種類（事実の相違 / 手順の変更 / 用語の不一致 / その他）
- 古いドキュメントの該当箇所（引用）
- 新しいドキュメントの該当箇所（引用）
- 矛盾の説明
- 修正提案

---
【新しいドキュメント】
{new_doc_text[:8000]}

---
【古いドキュメント】
{old_doc_text[:8000]}
"""
    response = model.generate_content(prompt)
    return {
        "contradictions": response.text,
        "summary": f"Compared {len(new_doc_text)} chars (new) vs {len(old_doc_text)} chars (old)",
    }


# ---------------------------------------------------------------------------
# Image comparison (multimodal — key differentiator)
# ---------------------------------------------------------------------------

def compare_images(old_image_bytes: bytes, new_image_bytes: bytes) -> dict[str, Any]:
    """Use Gemini's multimodal capabilities to detect visual decay.

    Compares an old screenshot from a manual with a newer reference image.
    """
    model = _get_model()

    old_part = Part.from_data(data=old_image_bytes, mime_type="image/png")
    new_part = Part.from_data(data=new_image_bytes, mime_type="image/png")

    prompt = """あなたはUI/UXの専門家です。
以下の2つの画像を比較してください。

画像1: マニュアルに掲載されている古いスクリーンショット
画像2: 現在のUIの最新スクリーンショット

以下の観点で分析し、相違点を報告してください:
1. レイアウトの変更
2. ボタン・メニュー項目の追加/削除/名称変更
3. 色やデザインの変更
4. テキストの変更
5. その他の視覚的な差異

各相違点について:
- 変更箇所の説明
- 影響度（高/中/低）
- マニュアル更新の推奨事項
"""
    response = model.generate_content([prompt, old_part, new_part])
    return {
        "visual_decay": response.text,
        "summary": "Multimodal image comparison completed",
    }

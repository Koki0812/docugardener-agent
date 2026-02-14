"""Vertex AI Gemini service — text and multimodal comparison.

Optimized for Gemini 2.0 Flash:
- Native JSON output via response_mime_type
- Extended context window (1M+ tokens)
- Faster inference for real-time detection
- Multimodal image comparison
"""
from __future__ import annotations

import logging
import time
from typing import Any

import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig, Part, Image

from config.settings import GCP_PROJECT_ID, GCP_LOCATION, GEMINI_MODEL
from utils.retry import retry_with_backoff
from services.logging_service import log_api_call

logger = logging.getLogger(__name__)

_model: GenerativeModel | None = None

# Gemini 2.0 Flash generation config for structured JSON output
_json_config = GenerationConfig(
    response_mime_type="application/json",
    temperature=0.1,
    top_p=0.95,
    max_output_tokens=8192,
)

# Config for free-form text analysis (image comparison)
_text_config = GenerationConfig(
    temperature=0.2,
    top_p=0.95,
    max_output_tokens=4096,
)


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

def compare_text(new_doc_text: str, old_doc_text: str, feedback_context: str = "") -> dict[str, Any]:
    """Use Gemini to find semantic contradictions between *new_doc_text* and *old_doc_text*.

    Args:
        new_doc_text: Text of the newer document.
        old_doc_text: Text of the older document.
        feedback_context: Optional past reviewer feedback to improve accuracy.

    Returns a dict with keys ``contradictions`` (list of structured dicts) and ``summary``.
    """
    import json as _json

    model = _get_model()

    feedback_section = ""
    if feedback_context:
        feedback_section = f"""
【過去のレビューフィードバック（参考情報）】
以下は過去のレビュアーの判断です。同様のパターンを参考にしてください：
{feedback_context}

"""

    prompt = f"""あなたはドキュメント品質管理の専門家です。
以下の「新しいドキュメント」と「古いドキュメント」を比較し、
意味的な矛盾や不整合を全て特定してください。
{feedback_section}
結果を以下のJSON形式で出力してください（JSON以外のテキストは含めないでください）:
```json
[
  {{
    "category": "矛盾の種類（例: 手順の変更、用語の不一致、事実の相違、連絡先変更）",
    "severity": "critical / warning / info のいずれか",
    "message": "矛盾の説明（何が問題か）",
    "suggestion": "修正提案（どう直すべきか）",
    "old_text": "古いドキュメントの該当箇所（原文をそのまま引用）",
    "new_text": "新しいドキュメントの該当箇所、または修正後のテキスト（原文をそのまま引用）"
  }}
]
```

矛盾が見つからない場合は空配列 `[]` を返してください。

---
【新しいドキュメント】
{new_doc_text[:16000]}

---
【古いドキュメント】
{old_doc_text[:16000]}
"""
    # Use Gemini 2.0 Flash native JSON output
    start_time = time.time()
    try:
        response = model.generate_content(prompt, generation_config=_json_config)
        duration_ms = (time.time() - start_time) * 1000
        log_api_call("gemini", "compare_text", duration_ms, True)
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_api_call("gemini", "compare_text", duration_ms, False, str(e))
        raise
    raw_text = response.text

    # Try to parse structured JSON from Gemini response
    parsed_items: list[dict[str, Any]] = []
    try:
        # Strip markdown code fences if present
        clean = raw_text.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1] if "\n" in clean else clean[3:]
            if clean.endswith("```"):
                clean = clean[:-3]
            clean = clean.strip()
            if clean.startswith("json"):
                clean = clean[4:].strip()
        parsed = _json.loads(clean)
        if isinstance(parsed, list):
            parsed_items = parsed
        elif isinstance(parsed, dict) and "contradictions" in parsed:
            parsed_items = parsed["contradictions"]
    except (_json.JSONDecodeError, ValueError):
        logger.warning("Gemini returned non-JSON; storing as raw analysis text")
        # Fallback: wrap raw text in a single analysis entry
        parsed_items = [{"analysis": raw_text, "category": "AI分析", "message": raw_text[:200]}]

    return {
        "contradictions": parsed_items,
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
    start_time = time.time()
    try:
        response = model.generate_content(
            [prompt, old_part, new_part],
            generation_config=_text_config,
        )
        duration_ms = (time.time() - start_time) * 1000
        log_api_call("gemini", "compare_images", duration_ms, True)
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_api_call("gemini", "compare_images", duration_ms, False, str(e))
        raise
    return {
        "visual_decay": response.text,
        "summary": "Multimodal image comparison completed",
    }

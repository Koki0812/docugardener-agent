"""Vertex AI Agent Builder (Discovery Engine) search service."""
from __future__ import annotations

import logging
from typing import Any

from google.cloud import discoveryengine_v1 as discoveryengine

from config.settings import GCP_PROJECT_ID, GCP_LOCATION, SEARCH_ENGINE_ID

logger = logging.getLogger(__name__)


def search_related_docs(query: str, page_size: int = 5) -> list[dict[str, Any]]:
    """Search for related documents using Vertex AI Agent Builder.

    Returns a list of dicts with ``title``, ``snippet``, ``link``, and ``doc_id``.
    """
    client = discoveryengine.SearchServiceClient()

    serving_config = (
        f"projects/{GCP_PROJECT_ID}"
        f"/locations/{GCP_LOCATION}"
        f"/dataStores/{SEARCH_ENGINE_ID}"
        f"/servingConfigs/default_search"
    )

    request = discoveryengine.SearchRequest(
        serving_config=serving_config,
        query=query,
        page_size=page_size,
    )

    try:
        response = client.search(request)
    except Exception:
        logger.exception("Discovery Engine search failed for query: %s", query)
        return []

    results: list[dict[str, Any]] = []
    for result in response.results:
        doc_data = result.document.derived_struct_data
        results.append(
            {
                "title": doc_data.get("title", ""),
                "snippet": doc_data.get("snippets", [{}])[0].get("snippet", "")
                if doc_data.get("snippets")
                else "",
                "link": doc_data.get("link", ""),
                "doc_id": result.document.id,
            }
        )

    logger.info("Search returned %d results for query: %s", len(results), query)
    return results

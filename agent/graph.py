"""DocuGardener Agent — LangGraph StateGraph definition."""
from __future__ import annotations

from langgraph.graph import StateGraph, END

from agent.state import AgentState
from agent.nodes import (
    fetch_source,
    search_related,
    compare_text_node,
    compare_images_node,
    generate_suggestions,
)


def build_graph() -> StateGraph:
    """Build and compile the DocuGardener LangGraph pipeline.

    Pipeline:
        fetch_source → search_related → compare_text → compare_images → suggest → END
    """
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("fetch_source", fetch_source)
    graph.add_node("search_related", search_related)
    graph.add_node("compare_text", compare_text_node)
    graph.add_node("compare_images", compare_images_node)
    graph.add_node("suggest", generate_suggestions)

    # Define edges (linear pipeline for MVP)
    graph.set_entry_point("fetch_source")
    graph.add_edge("fetch_source", "search_related")
    graph.add_edge("search_related", "compare_text")
    graph.add_edge("compare_text", "compare_images")
    graph.add_edge("compare_images", "suggest")
    graph.add_edge("suggest", END)

    return graph.compile()


# Singleton compiled graph
agent_graph = build_graph()

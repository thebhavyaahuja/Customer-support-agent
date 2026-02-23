"""
graph.py - Builds and compiles the LangGraph StateGraph for the Customer Support Agent.

This is where the agentic workflow is defined:
  1. Classify the customer's issue (LLM call)
  2. Route to the correct handler based on classification
  3. Check if escalation is needed
  4. Either generate a response (LLM call) or escalate to human

Graph Structure:
    START
      │
      ▼
    classify_issue
      │
      ├── (delivery)  ──► handle_delivery  ──┐
      ├── (refund)    ──► handle_refund    ──┤
      ├── (technical) ──► handle_technical ──┤
      └── (general)   ──► handle_general   ──┘
                                              │
                                              ▼
                                        check_escalation
                                              │
                                    ┌─────────┴──────────┐
                                    ▼                    ▼
                             generate_response    escalate_to_human
                                    │                    │
                                    ▼                    ▼
                                   END                  END
"""

from typing import Literal
from langgraph.graph import StateGraph, START, END

from state import CustomerSupportState
from nodes import (
    classify_issue,
    handle_delivery,
    handle_refund,
    handle_technical,
    handle_general,
    check_escalation,
    generate_response,
    escalate_to_human,
)


# ===========================================================================
# Routing Functions (Conditional Edges)
# ===========================================================================

def route_by_issue_type(state: CustomerSupportState) -> Literal[
    "handle_delivery", "handle_refund", "handle_technical", "handle_general"
]:
    """
    Routes to the appropriate handler node based on the classified issue type.
    This is a CONDITIONAL EDGE — LangGraph calls this function to decide
    which node to execute next.
    """
    issue_type = state.get("issue_type", "general")

    routing_map = {
        "delivery": "handle_delivery",
        "refund": "handle_refund",
        "technical": "handle_technical",
        "general": "handle_general",
    }

    return routing_map.get(issue_type, "handle_general")


def route_escalation(state: CustomerSupportState) -> Literal[
    "generate_response", "escalate_to_human"
]:
    """
    Routes to either normal response generation or human escalation
    based on the escalation check result.
    """
    if state.get("escalate", False):
        return "escalate_to_human"
    return "generate_response"


# ===========================================================================
# Graph Construction
# ===========================================================================

def build_graph() -> StateGraph:
    """
    Constructs and compiles the full customer support agent graph.

    Returns:
        A compiled LangGraph that can be invoked with a CustomerSupportState.
    """

    # Initialize the graph with our state schema
    builder = StateGraph(CustomerSupportState)

    # --- Add all nodes ---
    builder.add_node("classify_issue", classify_issue)
    builder.add_node("handle_delivery", handle_delivery)
    builder.add_node("handle_refund", handle_refund)
    builder.add_node("handle_technical", handle_technical)
    builder.add_node("handle_general", handle_general)
    builder.add_node("check_escalation", check_escalation)
    builder.add_node("generate_response", generate_response)
    builder.add_node("escalate_to_human", escalate_to_human)

    # --- Add edges ---

    # Entry: START → classify_issue
    builder.add_edge(START, "classify_issue")

    # Conditional: classify_issue → one of the four handlers
    builder.add_conditional_edges(
        "classify_issue",
        route_by_issue_type,
        ["handle_delivery", "handle_refund", "handle_technical", "handle_general"],
    )

    # All handlers → check_escalation
    builder.add_edge("handle_delivery", "check_escalation")
    builder.add_edge("handle_refund", "check_escalation")
    builder.add_edge("handle_technical", "check_escalation")
    builder.add_edge("handle_general", "check_escalation")

    # Conditional: check_escalation → generate_response OR escalate_to_human
    builder.add_conditional_edges(
        "check_escalation",
        route_escalation,
        ["generate_response", "escalate_to_human"],
    )

    # Terminal edges
    builder.add_edge("generate_response", END)
    builder.add_edge("escalate_to_human", END)

    # --- Compile the graph ---
    graph = builder.compile()

    return graph


# Allow importing the compiled graph directly
graph = build_graph()

"""
state.py - Defines the shared state schema for the Customer Support Agent.

The state is a TypedDict that flows through every node in the LangGraph.
Each node reads from and writes to this shared state.
"""

from typing import TypedDict, Optional


class CustomerSupportState(TypedDict):
    """
    Shared state for the Customer Support Agent graph.

    Fields:
        customer_message (str): The raw customer input message.
        issue_type (str): Classified category - one of:
            'delivery', 'refund', 'technical', 'general'.
        confidence (float): LLM's confidence in the classification (0.0 - 1.0).
        handler_context (dict): Extra context gathered by the issue handler,
            e.g., order details, refund policy, KB articles.
        response (str): The final generated response to the customer.
        escalate (bool): Whether the issue should be escalated to a human agent.
        escalation_reason (str): Why the issue was escalated.
    """
    customer_message: str
    issue_type: str
    confidence: float
    handler_context: dict
    response: str
    escalate: bool
    escalation_reason: str

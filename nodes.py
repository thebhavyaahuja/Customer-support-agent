"""
nodes.py - All node functions for the Customer Support Agent graph.

Each node is a Python function that:
  1. Receives the current state (CustomerSupportState)
  2. Performs its specific task (classify, handle, respond, escalate)
  3. Returns a dict of state updates

Nodes use Google Gemini (gemini-2.5-flash) for LLM calls.
External service calls (order DB, refund system) are simulated.
"""

import json
import re
import time
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

from state import CustomerSupportState
from database import (
    query_order_by_id,
    query_refund_policy,
    query_refund_eligibility,
    query_kb_article,
    query_faqs,
    insert_support_ticket,
)


# ---------------------------------------------------------------------------
# Initialize the Gemini LLM (free-tier model)
# ---------------------------------------------------------------------------
# gemini-2.5-flash is Google's latest free-tier model available via AI Studio.
# Fallback chain: gemini-2.5-flash → gemma-3-27b-it → gemma-3-12b-it → gemma-3-4b-it

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.3,        # Low temperature for consistent classification
    max_output_tokens=4096,
)


def invoke_llm_with_retry(messages, max_retries=3, initial_delay=5):
    """
    Invoke the LLM with retry logic to handle rate limits (429 errors).
    Uses exponential backoff between retries.
    """
    for attempt in range(max_retries):
        try:
            return llm.invoke(messages)
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                delay = initial_delay * (2 ** attempt)
                print(f"    ⏳ Rate limited. Retrying in {delay}s... (attempt {attempt + 1}/{max_retries})")
                time.sleep(delay)
            else:
                raise  # Non-rate-limit errors should propagate immediately
    # Final attempt — let it raise if it fails
    return llm.invoke(messages)


# ===========================================================================
# NODE 1: CLASSIFY ISSUE
# ===========================================================================
def classify_issue(state: CustomerSupportState) -> dict:
    """
    Classifies the customer message into one of four categories:
      - delivery  : order tracking, shipping delays, missing packages
      - refund    : returns, refunds, exchanges, damaged products
      - technical : app crashes, login issues, payment errors, bugs
      - general   : business hours, store locations, FAQs, greetings

    Uses Gemini to analyze the message and return:
      - issue_type (str)
      - confidence (float between 0.0 and 1.0)
    """
    customer_message = state["customer_message"]

    classification_prompt = f"""You are a customer support issue classifier for an e-commerce company.

Analyze the following customer message and classify it into EXACTLY ONE of these categories:
- "delivery" : relates to order tracking, shipping, delivery delays, missing packages
- "refund"   : relates to returns, refunds, exchanges, damaged/defective products
- "technical": relates to website/app issues, login problems, payment errors, bugs
- "general"  : relates to business hours, policies, FAQs, greetings, or anything else

Respond ONLY with a valid JSON object (no markdown, no code fences):
{{"issue_type": "<category>", "confidence": <float between 0.0 and 1.0>}}

Customer message: "{customer_message}"
"""

    messages = [
        SystemMessage(content="You are a precise classification assistant. Output ONLY valid JSON."),
        HumanMessage(content=classification_prompt),
    ]

    response = invoke_llm_with_retry(messages)

    # Parse the JSON response from the LLM
    try:
        # Strip markdown code fences if the model wraps the JSON
        raw = response.content.strip()
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        result = json.loads(raw)
        issue_type = result.get("issue_type", "general").lower()
        confidence = float(result.get("confidence", 0.5))
    except (json.JSONDecodeError, ValueError, AttributeError):
        # Fallback if LLM output is malformed
        issue_type = "general"
        confidence = 0.3

    # Validate issue_type
    valid_types = {"delivery", "refund", "technical", "general"}
    if issue_type not in valid_types:
        issue_type = "general"
        confidence = 0.3

    return {
        "issue_type": issue_type,
        "confidence": confidence,
    }


# ===========================================================================
# NODE 2a: HANDLE DELIVERY
# ===========================================================================
def handle_delivery(state: CustomerSupportState) -> dict:
    """
    Looks up delivery/order information from the Orders database.
    In production, this would call: SELECT * FROM orders WHERE order_id = %s
    """
    customer_message = state["customer_message"]

    # Extract order number if present (e.g., #12345)
    order_match = re.search(r"#?(\d{4,})", customer_message)
    order_id = order_match.group(1) if order_match else "UNKNOWN"

    # --- Database Query: Orders Table ---
    db_result = query_order_by_id(order_id)
    order_data = db_result["data"]

    handler_context = {
        "handler": "delivery",
        "db_query": db_result["query"],
        "db_status": db_result["status"],
        "order_data": order_data,
        "instructions": (
            "Provide the customer with their order status, tracking number, "
            "and estimated delivery date. Be empathetic if there's a delay."
        ),
    }

    return {"handler_context": handler_context}


# ===========================================================================
# NODE 2b: HANDLE REFUND
# ===========================================================================
def handle_refund(state: CustomerSupportState) -> dict:
    """
    Checks refund eligibility and policy from the database.
    In production, this would query:
      - SELECT * FROM refund_policies WHERE policy_id = 'default'
      - SELECT * FROM refund_requests WHERE order_id = %s
    """
    customer_message = state["customer_message"]

    # --- Database Query 1: Refund Policy ---
    policy_result = query_refund_policy()
    policy_data = policy_result["data"]

    # --- Database Query 2: Check existing refund eligibility ---
    order_match = re.search(r"#?(\d{4,})", customer_message)
    order_id = order_match.group(1) if order_match else "67890"  # default for demo
    eligibility_result = query_refund_eligibility(order_id)

    handler_context = {
        "handler": "refund",
        "db_queries": [
            policy_result["query"],
            eligibility_result["query"],
        ],
        "refund_policy": policy_data,
        "refund_eligibility": eligibility_result["data"],
        "instructions": (
            "Explain the refund/return policy clearly. Guide the customer through "
            "the return process. Be understanding about their frustration."
        ),
    }

    return {"handler_context": handler_context}


# ===========================================================================
# NODE 2c: HANDLE TECHNICAL
# ===========================================================================
def handle_technical(state: CustomerSupportState) -> dict:
    """
    Queries the Knowledge Base database for relevant troubleshooting articles.
    In production, this would query:
      SELECT * FROM kb_articles WHERE tags @> ARRAY[...] ORDER BY resolution_rate DESC LIMIT 1
    """
    customer_message = state["customer_message"].lower()

    # Extract keywords from the customer message for DB search
    search_keywords = []
    keyword_map = {
        "crash": ["crash", "crashing"],
        "login": ["login", "password", "sign in", "locked out"],
        "payment": ["payment", "checkout", "card", "declined"],
        "general": ["error", "bug", "glitch", "not working"],
    }
    for tag_keywords in keyword_map.values():
        for kw in tag_keywords:
            if kw in customer_message:
                search_keywords.append(kw)

    if not search_keywords:
        search_keywords = ["error"]  # fallback

    # --- Database Query: Knowledge Base ---
    kb_result = query_kb_article(search_keywords)
    kb_article = kb_result["data"]

    handler_context = {
        "handler": "technical",
        "db_query": kb_result["query"],
        "db_status": kb_result["status"],
        "match_score": kb_result.get("match_score", 0),
        "kb_article": kb_article,
        "instructions": (
            "Walk the customer through the troubleshooting steps from the "
            "knowledge base article. Be patient and clear."
        ),
    }

    return {"handler_context": handler_context}


# ===========================================================================
# NODE 2d: HANDLE GENERAL
# ===========================================================================
def handle_general(state: CustomerSupportState) -> dict:
    """
    Queries the FAQ database for relevant answers.
    In production, this would query: SELECT * FROM faqs ORDER BY views DESC
    """
    # --- Database Query: FAQ Table ---
    faq_result = query_faqs()
    faq_data = faq_result["data"]

    handler_context = {
        "handler": "general",
        "db_query": faq_result["query"],
        "db_status": faq_result["status"],
        "rows_returned": faq_result["rows_returned"],
        "faq_data": faq_data,
        "instructions": (
            "Answer the customer's question using the FAQ data. "
            "Be friendly and helpful. If the question is a greeting, "
            "respond warmly and ask how you can help."
        ),
    }

    return {"handler_context": handler_context}


# ===========================================================================
# NODE 3: CHECK ESCALATION
# ===========================================================================
def check_escalation(state: CustomerSupportState) -> dict:
    """
    Decides whether to escalate the issue to a human agent.

    Escalation triggers:
      1. Low confidence in classification (< 0.5)
      2. Sensitive keywords indicating anger, legal threats, or urgency
      3. The customer explicitly asks for a human/manager
    """
    confidence = state.get("confidence", 1.0)
    customer_message = state["customer_message"].lower()

    escalate = False
    reasons = []

    # Trigger 1: Low classification confidence
    if confidence < 0.5:
        escalate = True
        reasons.append(f"Low classification confidence ({confidence:.2f})")

    # Trigger 2: Sensitive / high-priority keywords
    escalation_keywords = [
        "lawsuit", "sue", "legal", "lawyer", "attorney",
        "manager", "supervisor", "human agent", "real person",
        "unacceptable", "worst experience", "never again",
        "report", "complaint", "consumer forum", "bbb",
    ]
    found_keywords = [kw for kw in escalation_keywords if kw in customer_message]
    if found_keywords:
        escalate = True
        reasons.append(f"Sensitive keywords detected: {', '.join(found_keywords)}")

    escalation_reason = "; ".join(reasons) if reasons else ""

    return {
        "escalate": escalate,
        "escalation_reason": escalation_reason,
    }


# ===========================================================================
# NODE 4a: GENERATE RESPONSE (Normal path)
# ===========================================================================
def generate_response(state: CustomerSupportState) -> dict:
    """
    Uses Gemini to generate a polished, empathetic customer response
    based on the handler context and original message.
    """
    customer_message = state["customer_message"]
    issue_type = state["issue_type"]
    handler_context = state.get("handler_context", {})

    response_prompt = f"""You are a friendly and professional customer support agent for "ShopEase", 
an e-commerce company. Generate a helpful response to the customer.

CUSTOMER MESSAGE: "{customer_message}"

ISSUE TYPE: {issue_type}

CONTEXT FROM OUR SYSTEMS:
{json.dumps(handler_context, indent=2)}

INSTRUCTIONS:
- Be empathetic and professional
- Use the context/data provided to give specific, accurate information
- Keep the response concise but complete (3-5 sentences)
- If applicable, provide next steps
- Sign off as "ShopEase Support Team"
- Do NOT make up information not in the context
"""

    messages = [
        SystemMessage(content="You are a helpful e-commerce customer support agent."),
        HumanMessage(content=response_prompt),
    ]

    response = invoke_llm_with_retry(messages)

    return {"response": response.content.strip()}


# ===========================================================================
# NODE 4b: ESCALATE TO HUMAN (Escalation path)
# ===========================================================================
def escalate_to_human(state: CustomerSupportState) -> dict:
    """
    Generates an escalation response for the customer and prepares
    a summary for the human agent who will take over.
    """
    customer_message = state["customer_message"]
    issue_type = state.get("issue_type", "unknown")
    escalation_reason = state.get("escalation_reason", "Unspecified")
    handler_context = state.get("handler_context", {})

    # --- Database Insert: Create support ticket ---
    ticket_result = insert_support_ticket(
        customer_message=customer_message,
        issue_type=issue_type,
        escalation_reason=escalation_reason,
        handler_context=handler_context,
    )
    ticket = ticket_result["data"]

    # Generate a customer-facing escalation message
    escalation_response = (
        f"Thank you for reaching out to ShopEase. I understand your concern, "
        f"and I want to make sure you receive the best possible assistance.\n\n"
        f"I am connecting you with a senior support specialist who will be able "
        f"to help you further. Your case has been flagged as priority.\n\n"
        f"📋 **Your Case Summary:**\n"
        f"- Ticket ID: {ticket['ticket_id']}\n"
        f"- Issue Type: {issue_type.title()}\n"
        f"- Priority: {ticket['priority'].upper()}\n"
        f"- Escalation Reason: {escalation_reason}\n\n"
        f"A human agent will respond within 15 minutes during business hours "
        f"(Mon-Fri, 9 AM - 6 PM IST).\n\n"
        f"— ShopEase Support Team"
    )

    return {"response": escalation_response}

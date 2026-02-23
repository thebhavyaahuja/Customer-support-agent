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
    Simulates looking up delivery/order information.
    In a real system, this would call an Order Management API.
    """
    customer_message = state["customer_message"]

    # --- Simulated API call: Order Management System ---
    # Extract order number if present (e.g., #12345)
    order_match = re.search(r"#?(\d{4,})", customer_message)
    order_id = order_match.group(1) if order_match else "UNKNOWN"

    # Simulated order database response
    simulated_order_data = {
        "order_id": order_id,
        "status": "In Transit",
        "carrier": "FedEx",
        "tracking_number": "FX-9876543210",
        "estimated_delivery": "February 25, 2026",
        "last_location": "Distribution Center, Mumbai",
    }

    handler_context = {
        "handler": "delivery",
        "order_data": simulated_order_data,
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
    Simulates checking refund eligibility and policy.
    In a real system, this would call a Payment/Refund API.
    """
    # --- Simulated API call: Refund/Payment System ---
    simulated_refund_data = {
        "refund_policy": "Full refund within 30 days of purchase for unused items. "
                         "Damaged items are eligible for immediate replacement or refund.",
        "refund_processing_time": "5-7 business days",
        "refund_method": "Original payment method",
        "return_shipping": "Free return shipping label provided",
    }

    handler_context = {
        "handler": "refund",
        "refund_data": simulated_refund_data,
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
    Simulates a knowledge base lookup for technical issues.
    In a real system, this would query a KB/documentation API.
    """
    customer_message = state["customer_message"].lower()

    # --- Simulated API call: Knowledge Base ---
    # Simple keyword matching to simulate KB search results
    if "crash" in customer_message or "crashing" in customer_message:
        kb_article = {
            "title": "App Crashing - Troubleshooting Steps",
            "steps": [
                "1. Force close the app and reopen it",
                "2. Clear the app cache (Settings > Apps > Our App > Clear Cache)",
                "3. Update the app to the latest version from the App Store",
                "4. Restart your device",
                "5. If the issue persists, uninstall and reinstall the app",
            ],
        }
    elif "login" in customer_message or "password" in customer_message:
        kb_article = {
            "title": "Login Issues - Resolution Guide",
            "steps": [
                "1. Click 'Forgot Password' on the login page",
                "2. Enter your registered email address",
                "3. Check your inbox (and spam folder) for the reset link",
                "4. Create a new password (min 8 characters, 1 uppercase, 1 number)",
                "5. Try logging in with the new password",
            ],
        }
    elif "payment" in customer_message or "checkout" in customer_message:
        kb_article = {
            "title": "Payment / Checkout Issues",
            "steps": [
                "1. Verify your card details are entered correctly",
                "2. Ensure your card has sufficient balance",
                "3. Try a different payment method",
                "4. Disable any VPN or ad-blocker that might interfere",
                "5. Try using a different browser or the mobile app",
            ],
        }
    else:
        kb_article = {
            "title": "General Technical Troubleshooting",
            "steps": [
                "1. Clear your browser cache and cookies",
                "2. Try using a different browser",
                "3. Check your internet connection",
                "4. Disable browser extensions",
                "5. Contact our technical team if the issue persists",
            ],
        }

    handler_context = {
        "handler": "technical",
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
    Handles general queries: business hours, FAQs, greetings, etc.
    In a real system, this might query an FAQ database or CRM.
    """
    # --- Simulated FAQ database ---
    faq_data = {
        "business_hours": "Monday - Friday: 9:00 AM to 6:00 PM IST. "
                          "Saturday: 10:00 AM to 4:00 PM IST. Sunday: Closed.",
        "contact_email": "support@shopease.com",
        "contact_phone": "+91-1800-123-4567 (Toll Free)",
        "shipping_info": "Free shipping on orders above ₹499. "
                         "Standard delivery takes 3-5 business days.",
        "store_locations": "We are an online-only store with warehouses in "
                           "Mumbai, Delhi, and Bangalore.",
    }

    handler_context = {
        "handler": "general",
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

    # Generate a customer-facing escalation message
    escalation_response = (
        f"Thank you for reaching out to ShopEase. I understand your concern, "
        f"and I want to make sure you receive the best possible assistance.\n\n"
        f"I am connecting you with a senior support specialist who will be able "
        f"to help you further. Your case has been flagged as priority.\n\n"
        f"📋 **Your Case Summary:**\n"
        f"- Issue Type: {issue_type.title()}\n"
        f"- Escalation Reason: {escalation_reason}\n"
        f"- Reference ID: ESC-2026-{hash(customer_message) % 10000:04d}\n\n"
        f"A human agent will respond within 15 minutes during business hours "
        f"(Mon-Fri, 9 AM - 6 PM IST).\n\n"
        f"— ShopEase Support Team"
    )

    return {"response": escalation_response}

"""
test_agent.py - Runs pre-defined test scenarios through the Customer Support Agent.

Tests all 5 issue categories: delivery, refund, technical, general, and escalation.

Usage:
    python test_agent.py
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

if not os.getenv("GOOGLE_API_KEY"):
    print("ERROR: GOOGLE_API_KEY not found in .env")
    sys.exit(1)

from graph import graph


# ===========================================================================
# Test Messages - Different scenarios the agent should handle
# ===========================================================================
TEST_MESSAGES = [
    # Delivery issue
    "Where is my order #12345? It was supposed to arrive 3 days ago.",

    # Refund request
    "I received broken headphones. I want a full refund please.",

    # Technical issue
    "The app keeps crashing when I try to checkout. I've tried 3 times now.",

    # General query
    "What are your business hours? And do you have a physical store?",

    # Should trigger escalation (legal threat)
    "This is unacceptable! I'm going to sue you if I don't get my money back immediately. I want to speak to a manager!",
]


def run_agent(message: str) -> dict:
    initial_state = {
        "customer_message": message,
        "issue_type": "",
        "confidence": 0.0,
        "handler_context": {},
        "response": "",
        "escalate": False,
        "escalation_reason": "",
    }
    return graph.invoke(initial_state)


def print_result(index: int, message: str, result: dict):
    print(f"\n{'='*70}")
    print(f"  TEST CASE {index + 1}")
    print(f"{'='*70}")
    print(f"\n  📩 CUSTOMER MESSAGE:")
    print(f"     \"{message}\"")
    print(f"\n  🏷️  CLASSIFICATION:")
    print(f"     Issue Type  : {result.get('issue_type', 'N/A').upper()}")
    print(f"     Confidence  : {result.get('confidence', 0):.0%}")
    print(f"\n  🔄 ROUTING:")
    handler_ctx = result.get("handler_context", {})
    handler = handler_ctx.get("handler", "N/A")
    print(f"     Handled by  : {handler.title()} Handler")

    # --- Database Transparency Section ---
    db_query = handler_ctx.get("db_query") or handler_ctx.get("db_queries")
    if db_query:
        print(f"\n  🗄️  DATABASE QUERIES:")
        if isinstance(db_query, list):
            for i, q in enumerate(db_query, 1):
                print(f"     [{i}] {q}")
        else:
            print(f"     {db_query}")

    # Show key data retrieved from DB
    if "order_data" in handler_ctx:
        od = handler_ctx["order_data"]
        print(f"\n  📦 DATA RETRIEVED (Orders DB):")
        print(f"     Order ID    : {od.get('order_id', 'N/A')}")
        print(f"     Status      : {od.get('status', 'N/A')}")
        shipping = od.get("shipping", {})
        print(f"     Carrier     : {shipping.get('carrier', 'N/A')}")
        print(f"     Tracking #  : {shipping.get('tracking_number', 'N/A')}")
        print(f"     ETA         : {shipping.get('estimated_delivery', 'N/A')}")
    elif "refund_policy" in handler_ctx:
        rp = handler_ctx["refund_policy"]
        re_ = handler_ctx.get("refund_eligibility", {})
        print(f"\n  💳 DATA RETRIEVED (Refund DB):")
        print(f"     Policy      : {rp.get('policy_name', 'N/A')}")
        print(f"     Window      : {rp.get('return_window_days', 'N/A')} days")
        print(f"     Processing  : {rp.get('refund_processing_days', 'N/A')}")
        print(f"     Eligibility : {re_.get('status', 'N/A')}")
    elif "kb_article" in handler_ctx:
        kb = handler_ctx["kb_article"]
        print(f"\n  📖 DATA RETRIEVED (Knowledge Base DB):")
        print(f"     Article ID  : {kb.get('article_id', 'N/A')}")
        print(f"     Title       : {kb.get('title', 'N/A')}")
        print(f"     Match Score : {handler_ctx.get('match_score', 'N/A')}")
        print(f"     Resolution  : {kb.get('resolution_rate', 0):.0%}")
    elif "faq_data" in handler_ctx:
        faq_list = handler_ctx["faq_data"]
        print(f"\n  📋 DATA RETRIEVED (FAQ DB):")
        print(f"     Rows returned: {handler_ctx.get('rows_returned', len(faq_list))}")
        if isinstance(faq_list, list):
            for faq in faq_list[:3]:
                print(f"     • [{faq.get('faq_id','?')}] {faq.get('question','?')}")

    if result.get("escalate"):
        print(f"\n  ⚠️  ESCALATED TO HUMAN:")
        print(f"     Reason: {result.get('escalation_reason', 'N/A')}")

    print(f"\n  💬 AGENT RESPONSE:")
    response = result.get("response", "No response generated.")
    for line in response.split("\n"):
        print(f"     {line}")

    print(f"\n{'─'*70}")


def main():
    print("\n" + "╔" + "═"*68 + "╗")
    print("║" + " ShopEase AI — TEST SUITE ".center(68) + "║")
    print("║" + " Running 5 pre-defined test scenarios ".center(68) + "║")
    print("╚" + "═"*68 + "╝\n")

    for i, message in enumerate(TEST_MESSAGES):
        try:
            result = run_agent(message)
            print_result(i, message, result)
        except Exception as e:
            print(f"\n  TEST CASE {i + 1} — ERROR: {type(e).__name__}: {e}")
            print(f"{'─'*70}")

    print(f"\n{'╔' + '═'*68 + '╗'}")
    print(f"{'║' + ' All test cases completed! '.center(68) + '║'}")
    print(f"{'╚' + '═'*68 + '╝'}\n")


if __name__ == "__main__":
    main()

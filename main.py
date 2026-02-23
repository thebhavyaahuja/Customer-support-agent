"""
main.py - Interactive entry point for the E-Commerce Customer Support Agent.

Lets you type customer messages and get live responses from the agent.

Usage:
    1. Set your GOOGLE_API_KEY in the .env file
    2. pip install -r requirements.txt
    3. python main.py
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Validate API key is set
if not os.getenv("GOOGLE_API_KEY"):
    print("=" * 60)
    print("ERROR: GOOGLE_API_KEY not found!")
    print()
    print("Steps to fix:")
    print("  1. Go to https://aistudio.google.com/apikey")
    print("  2. Create a free API key")
    print("  3. Add it to the .env file:")
    print('     GOOGLE_API_KEY=your_key_here')
    print("=" * 60)
    sys.exit(1)

from graph import graph


def run_agent(message: str) -> dict:
    """
    Run the customer support agent graph with a single customer message.
    """
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


def print_result(result: dict):
    """Pretty-print the agent's result with full transparency."""
    print(f"\n  🏷️  Classification : {result.get('issue_type', 'N/A').upper()} "
          f"({result.get('confidence', 0):.0%} confidence)")

    handler_ctx = result.get("handler_context", {})
    handler = handler_ctx.get("handler", "N/A")
    print(f"  🔄 Routed to     : {handler.title()} Handler")

    # --- Database Transparency Section ---
    db_query = handler_ctx.get("db_query") or handler_ctx.get("db_queries")
    if db_query:
        print(f"\n  🗄️  Database Queries:")
        if isinstance(db_query, list):
            for i, q in enumerate(db_query, 1):
                print(f"     [{i}] {q}")
        else:
            print(f"     {db_query}")

    # Show key data retrieved from DB
    if "order_data" in handler_ctx:
        od = handler_ctx["order_data"]
        print(f"\n  📦 Data Retrieved (Orders DB):")
        print(f"     Order ID    : {od.get('order_id', 'N/A')}")
        print(f"     Status      : {od.get('status', 'N/A')}")
        shipping = od.get("shipping", {})
        print(f"     Carrier     : {shipping.get('carrier', 'N/A')}")
        print(f"     Tracking #  : {shipping.get('tracking_number', 'N/A')}")
        print(f"     ETA         : {shipping.get('estimated_delivery', 'N/A')}")
    elif "refund_policy" in handler_ctx:
        rp = handler_ctx["refund_policy"]
        re_ = handler_ctx.get("refund_eligibility", {})
        print(f"\n  💳 Data Retrieved (Refund DB):")
        print(f"     Policy      : {rp.get('policy_name', 'N/A')}")
        print(f"     Window      : {rp.get('return_window_days', 'N/A')} days")
        print(f"     Processing  : {rp.get('refund_processing_days', 'N/A')}")
        print(f"     Eligibility : {re_.get('status', 'N/A')}")
    elif "kb_article" in handler_ctx:
        kb = handler_ctx["kb_article"]
        print(f"\n  📖 Data Retrieved (Knowledge Base DB):")
        print(f"     Article ID  : {kb.get('article_id', 'N/A')}")
        print(f"     Title       : {kb.get('title', 'N/A')}")
        print(f"     Match Score : {handler_ctx.get('match_score', 'N/A')}")
        print(f"     Resolution  : {kb.get('resolution_rate', 0):.0%}")
    elif "faq_data" in handler_ctx:
        faq_list = handler_ctx["faq_data"]
        print(f"\n  📋 Data Retrieved (FAQ DB):")
        print(f"     Rows returned: {handler_ctx.get('rows_returned', len(faq_list))}")
        if isinstance(faq_list, list):
            for faq in faq_list[:3]:  # show top 3
                print(f"     • [{faq.get('faq_id','?')}] {faq.get('question','?')}")

    if result.get("escalate"):
        print(f"\n  ⚠️  Escalated     : {result.get('escalation_reason', 'N/A')}")

    print(f"\n  💬 Response:")
    print(f"  {'─'*60}")
    response = result.get("response", "No response generated.")
    for line in response.split("\n"):
        print(f"  {line}")
    print(f"  {'─'*60}")


def main():
    """Interactive loop — type messages, get agent responses."""
    print("\n" + "╔" + "═"*68 + "╗")
    print("║" + " ShopEase AI Customer Support Agent ".center(68) + "║")
    print("║" + " Powered by LangGraph + Google Gemini ".center(68) + "║")
    print("╚" + "═"*68 + "╝")
    print("\n  Type a customer message and press Enter.")
    print("  Type 'quit' or 'exit' to stop.\n")

    while True:
        try:
            message = input("  📩 You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n  Goodbye! 👋\n")
            break

        if not message:
            continue
        if message.lower() in ("quit", "exit", "q"):
            print("\n  Goodbye! 👋\n")
            break

        try:
            result = run_agent(message)
            print_result(result)
            print()
        except Exception as e:
            print(f"\n  ❌ Error: {type(e).__name__}: {e}\n")


if __name__ == "__main__":
    main()

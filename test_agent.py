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
    handler = result.get("handler_context", {}).get("handler", "N/A")
    print(f"     Handled by  : {handler.title()} Handler")

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

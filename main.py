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
    """Pretty-print the agent's result."""
    print(f"\n  🏷️  Classification : {result.get('issue_type', 'N/A').upper()} "
          f"({result.get('confidence', 0):.0%} confidence)")

    handler = result.get("handler_context", {}).get("handler", "N/A")
    print(f"  🔄 Routed to     : {handler.title()} Handler")

    if result.get("escalate"):
        print(f"  ⚠️  Escalated     : {result.get('escalation_reason', 'N/A')}")

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

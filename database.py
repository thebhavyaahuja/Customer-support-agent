"""
database.py - Simulated Database Layer for the Customer Support Agent.

Mimics what a real database (PostgreSQL / MongoDB) would return.
Each function represents a DB query and returns data in the same
format that an ORM (like SQLAlchemy) or a DB driver would return —
i.e., dictionaries with proper column names, data types, timestamps, and IDs.

In production, these would be replaced with actual DB calls:
    - PostgreSQL via SQLAlchemy / psycopg2
    - MongoDB via pymongo
    - Redis for caching / session data
"""

from datetime import datetime, timedelta
import random


# ===========================================================================
# SIMULATED DATABASE TABLES (in-memory dicts acting as DB rows)
# ===========================================================================

# --- Orders Table ---
# Simulates: SELECT * FROM orders WHERE order_id = ?
ORDERS_TABLE = {
    "12345": {
        "order_id": "12345",
        "customer_id": "CUST-0042",
        "customer_name": "Bhavya Ahuja",
        "customer_email": "bhavya@example.com",
        "order_date": "2026-02-18T10:30:00Z",
        "status": "in_transit",
        "total_amount": 2499.00,
        "currency": "INR",
        "items": [
            {"sku": "SKU-HD-001", "name": "Sony WH-1000XM5 Headphones", "qty": 1, "price": 2499.00}
        ],
        "shipping": {
            "carrier": "FedEx",
            "tracking_number": "FX-9876543210",
            "shipped_date": "2026-02-19T14:00:00Z",
            "estimated_delivery": "2026-02-25T18:00:00Z",
            "last_location": "Distribution Center, Mumbai",
            "last_updated": "2026-02-22T08:15:00Z",
        },
        "payment": {
            "method": "credit_card",
            "card_last_four": "4242",
            "transaction_id": "TXN-20260218-7891",
            "status": "captured",
        },
        "created_at": "2026-02-18T10:30:00Z",
        "updated_at": "2026-02-22T08:15:00Z",
    },
    "67890": {
        "order_id": "67890",
        "customer_id": "CUST-0042",
        "customer_name": "Bhavya Ahuja",
        "customer_email": "bhavya@example.com",
        "order_date": "2026-02-10T09:00:00Z",
        "status": "delivered",
        "total_amount": 1299.00,
        "currency": "INR",
        "items": [
            {"sku": "SKU-HP-003", "name": "boAt Rockerz 450 Headphones", "qty": 1, "price": 1299.00}
        ],
        "shipping": {
            "carrier": "BlueDart",
            "tracking_number": "BD-1122334455",
            "shipped_date": "2026-02-11T10:00:00Z",
            "estimated_delivery": "2026-02-14T18:00:00Z",
            "delivered_date": "2026-02-13T16:30:00Z",
            "last_location": "Delivered - Delhi",
            "last_updated": "2026-02-13T16:30:00Z",
        },
        "payment": {
            "method": "upi",
            "upi_id": "bhavya@paytm",
            "transaction_id": "TXN-20260210-4561",
            "status": "captured",
        },
        "created_at": "2026-02-10T09:00:00Z",
        "updated_at": "2026-02-13T16:30:00Z",
    },
}

# --- Customers Table ---
# Simulates: SELECT * FROM customers WHERE customer_id = ?
CUSTOMERS_TABLE = {
    "CUST-0042": {
        "customer_id": "CUST-0042",
        "name": "Bhavya Ahuja",
        "email": "bhavya@example.com",
        "phone": "+91-9876543210",
        "tier": "gold",
        "total_orders": 12,
        "account_created": "2025-06-15T00:00:00Z",
        "last_login": "2026-02-23T09:00:00Z",
    },
}

# --- Refund Policies Table ---
# Simulates: SELECT * FROM refund_policies WHERE policy_id = ?
REFUND_POLICIES_TABLE = {
    "default": {
        "policy_id": "POL-001",
        "policy_name": "Standard Return & Refund Policy",
        "return_window_days": 30,
        "conditions": [
            "Item must be unused and in original packaging",
            "Damaged/defective items eligible for immediate refund",
            "Electronics must be returned within 15 days",
            "Sale items are exchange-only (no cash refund)",
        ],
        "refund_processing_days": "5-7 business days",
        "refund_method": "Original payment method",
        "return_shipping": "Free return shipping label provided",
        "effective_date": "2025-01-01",
        "last_updated": "2026-01-15T00:00:00Z",
    },
}

# --- Refund Requests Table ---
# Simulates: SELECT * FROM refund_requests WHERE order_id = ?
REFUND_REQUESTS_TABLE = {
    "67890": {
        "refund_id": "REF-2026-0023",
        "order_id": "67890",
        "customer_id": "CUST-0042",
        "status": "eligible",
        "reason": "defective_product",
        "amount": 1299.00,
        "currency": "INR",
        "requested_at": None,  # Not yet requested
        "processed_at": None,
    },
}

# --- Knowledge Base Table ---
# Simulates: SELECT * FROM kb_articles WHERE category = ? AND tags @> ?
KB_ARTICLES_TABLE = {
    "app_crash": {
        "article_id": "KB-1001",
        "category": "technical",
        "title": "App Crashing - Troubleshooting Steps",
        "tags": ["crash", "crashing", "app", "freeze", "not responding"],
        "steps": [
            "1. Force close the app and reopen it",
            "2. Clear the app cache (Settings > Apps > ShopEase > Clear Cache)",
            "3. Update the app to the latest version from the App Store / Play Store",
            "4. Restart your device",
            "5. If the issue persists, uninstall and reinstall the app",
        ],
        "resolution_rate": 0.87,
        "last_updated": "2026-02-01T00:00:00Z",
    },
    "login_issue": {
        "article_id": "KB-1002",
        "category": "technical",
        "title": "Login Issues - Resolution Guide",
        "tags": ["login", "password", "sign in", "locked out", "forgot password"],
        "steps": [
            "1. Click 'Forgot Password' on the login page",
            "2. Enter your registered email address",
            "3. Check your inbox (and spam folder) for the reset link",
            "4. Create a new password (min 8 chars, 1 uppercase, 1 number)",
            "5. Try logging in with the new password",
        ],
        "resolution_rate": 0.92,
        "last_updated": "2026-01-20T00:00:00Z",
    },
    "payment_issue": {
        "article_id": "KB-1003",
        "category": "technical",
        "title": "Payment / Checkout Issues",
        "tags": ["payment", "checkout", "card", "declined", "transaction failed"],
        "steps": [
            "1. Verify your card details are entered correctly",
            "2. Ensure your card has sufficient balance",
            "3. Try a different payment method (UPI, Net Banking, COD)",
            "4. Disable any VPN or ad-blocker that might interfere",
            "5. Try using a different browser or the mobile app",
        ],
        "resolution_rate": 0.78,
        "last_updated": "2026-02-10T00:00:00Z",
    },
    "general_tech": {
        "article_id": "KB-1004",
        "category": "technical",
        "title": "General Technical Troubleshooting",
        "tags": ["browser", "error", "bug", "glitch", "not working"],
        "steps": [
            "1. Clear your browser cache and cookies",
            "2. Try using a different browser (Chrome, Firefox, Edge)",
            "3. Check your internet connection",
            "4. Disable browser extensions",
            "5. Contact our technical team if the issue persists",
        ],
        "resolution_rate": 0.65,
        "last_updated": "2026-01-05T00:00:00Z",
    },
}

# --- FAQ Table ---
# Simulates: SELECT * FROM faqs
FAQ_TABLE = {
    "business_hours": {
        "faq_id": "FAQ-001",
        "question": "What are your business/support hours?",
        "answer": "Monday-Friday: 9:00 AM to 6:00 PM IST. Saturday: 10:00 AM to 4:00 PM IST. Sunday: Closed.",
        "category": "general",
        "views": 4521,
    },
    "contact": {
        "faq_id": "FAQ-002",
        "question": "How can I contact customer support?",
        "answer": "Email: support@shopease.com | Phone: +91-1800-123-4567 (Toll Free) | Live Chat: available on our website during business hours.",
        "category": "general",
        "views": 3890,
    },
    "shipping": {
        "faq_id": "FAQ-003",
        "question": "What are the shipping charges and delivery times?",
        "answer": "Free shipping on orders above ₹499. Standard delivery: 3-5 business days. Express delivery: 1-2 business days (₹99 extra).",
        "category": "shipping",
        "views": 5120,
    },
    "stores": {
        "faq_id": "FAQ-004",
        "question": "Do you have physical stores?",
        "answer": "ShopEase is an online-only store. We operate warehouses in Mumbai, Delhi, and Bangalore for fast delivery across India.",
        "category": "general",
        "views": 2100,
    },
    "returns": {
        "faq_id": "FAQ-005",
        "question": "What is your return policy?",
        "answer": "We offer a 30-day return policy for unused items in original packaging. Damaged items can be returned immediately for a full refund or replacement.",
        "category": "returns",
        "views": 6780,
    },
}

# --- Escalation/Tickets Table ---
# Simulates: INSERT INTO support_tickets VALUES (...)
TICKETS_TABLE = {}


# ===========================================================================
# DATABASE QUERY FUNCTIONS
# These mimic the interface of a real DB access layer / repository pattern.
# Each returns a dict in the same format a DB driver / ORM would return.
# ===========================================================================

def query_order_by_id(order_id: str) -> dict:
    """
    Simulates: SELECT * FROM orders WHERE order_id = %s
    Returns a single order row or a 'not found' result.
    """
    order = ORDERS_TABLE.get(order_id)
    if order:
        return {
            "status": "found",
            "rows_returned": 1,
            "data": order,
            "query": f"SELECT * FROM orders WHERE order_id = '{order_id}'",
            "executed_at": datetime.utcnow().isoformat() + "Z",
        }
    else:
        # Generate a plausible default for unknown orders
        return {
            "status": "found",
            "rows_returned": 1,
            "data": {
                "order_id": order_id,
                "customer_id": "CUST-UNKNOWN",
                "order_date": (datetime.utcnow() - timedelta(days=random.randint(1, 10))).isoformat() + "Z",
                "status": random.choice(["in_transit", "processing", "shipped"]),
                "total_amount": round(random.uniform(499, 4999), 2),
                "currency": "INR",
                "items": [{"sku": "SKU-GEN-001", "name": "Product Item", "qty": 1}],
                "shipping": {
                    "carrier": random.choice(["FedEx", "BlueDart", "Delhivery", "DTDC"]),
                    "tracking_number": f"TRK-{random.randint(1000000, 9999999)}",
                    "estimated_delivery": (datetime.utcnow() + timedelta(days=random.randint(1, 5))).strftime("%Y-%m-%d"),
                    "last_location": random.choice(["Warehouse, Mumbai", "Hub, Delhi", "Sorting Facility, Bangalore"]),
                    "last_updated": datetime.utcnow().isoformat() + "Z",
                },
            },
            "query": f"SELECT * FROM orders WHERE order_id = '{order_id}'",
            "executed_at": datetime.utcnow().isoformat() + "Z",
        }


def query_refund_policy() -> dict:
    """
    Simulates: SELECT * FROM refund_policies WHERE policy_id = 'default'
    """
    policy = REFUND_POLICIES_TABLE["default"]
    return {
        "status": "found",
        "rows_returned": 1,
        "data": policy,
        "query": "SELECT * FROM refund_policies WHERE policy_id = 'default'",
        "executed_at": datetime.utcnow().isoformat() + "Z",
    }


def query_refund_eligibility(order_id: str) -> dict:
    """
    Simulates: SELECT * FROM refund_requests WHERE order_id = %s
    Also checks if the order is within the return window.
    """
    existing = REFUND_REQUESTS_TABLE.get(order_id)
    if existing:
        return {
            "status": "found",
            "rows_returned": 1,
            "data": existing,
            "query": f"SELECT * FROM refund_requests WHERE order_id = '{order_id}'",
            "executed_at": datetime.utcnow().isoformat() + "Z",
        }
    return {
        "status": "not_found",
        "rows_returned": 0,
        "data": {
            "order_id": order_id,
            "status": "eligible",
            "reason": "within_return_window",
            "note": "No prior refund request found. Customer is eligible to initiate one.",
        },
        "query": f"SELECT * FROM refund_requests WHERE order_id = '{order_id}'",
        "executed_at": datetime.utcnow().isoformat() + "Z",
    }


def query_kb_article(keywords: list) -> dict:
    """
    Simulates: SELECT * FROM kb_articles WHERE tags @> ARRAY[%s] ORDER BY resolution_rate DESC LIMIT 1
    Finds the best matching knowledge base article by tag overlap.
    """
    best_match = None
    best_score = 0

    for key, article in KB_ARTICLES_TABLE.items():
        score = sum(1 for kw in keywords if kw in article["tags"])
        if score > best_score:
            best_score = score
            best_match = article

    if best_match:
        return {
            "status": "found",
            "rows_returned": 1,
            "data": best_match,
            "match_score": best_score,
            "query": f"SELECT * FROM kb_articles WHERE tags @> ARRAY{keywords} ORDER BY resolution_rate DESC LIMIT 1",
            "executed_at": datetime.utcnow().isoformat() + "Z",
        }
    # Fallback to general troubleshooting
    return {
        "status": "found",
        "rows_returned": 1,
        "data": KB_ARTICLES_TABLE["general_tech"],
        "match_score": 0,
        "query": f"SELECT * FROM kb_articles WHERE category = 'technical' ORDER BY resolution_rate DESC LIMIT 1",
        "executed_at": datetime.utcnow().isoformat() + "Z",
    }


def query_faqs() -> dict:
    """
    Simulates: SELECT * FROM faqs ORDER BY views DESC
    Returns all FAQ entries.
    """
    faqs = list(FAQ_TABLE.values())
    return {
        "status": "found",
        "rows_returned": len(faqs),
        "data": faqs,
        "query": "SELECT * FROM faqs ORDER BY views DESC",
        "executed_at": datetime.utcnow().isoformat() + "Z",
    }


def insert_support_ticket(customer_message: str, issue_type: str,
                          escalation_reason: str, handler_context: dict) -> dict:
    """
    Simulates: INSERT INTO support_tickets (...) VALUES (...) RETURNING *
    Creates an escalation ticket and returns the inserted row.
    """
    ticket_id = f"TKT-2026-{random.randint(1000, 9999)}"
    ticket = {
        "ticket_id": ticket_id,
        "customer_message": customer_message,
        "issue_type": issue_type,
        "escalation_reason": escalation_reason,
        "priority": "high" if any(kw in customer_message.lower() for kw in ["sue", "legal", "lawyer"]) else "medium",
        "status": "open",
        "assigned_to": None,
        "handler_context": handler_context,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "updated_at": datetime.utcnow().isoformat() + "Z",
    }
    TICKETS_TABLE[ticket_id] = ticket

    return {
        "status": "inserted",
        "rows_affected": 1,
        "data": ticket,
        "query": f"INSERT INTO support_tickets (...) VALUES (...) RETURNING *",
        "executed_at": datetime.utcnow().isoformat() + "Z",
    }

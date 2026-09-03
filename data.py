"""In-memory canned data for Tarang Electronics — a fictional Indian
consumer-electronics retailer used to demonstrate integrating the
`weave` SDK (see README.md for the full six-step walkthrough).

Not a real business system: this is deliberately a fixed, restart-empty
dataset just realistic enough to demonstrate the external/internal
tool-visibility split and give the analytics endpoints something
non-trivial to aggregate over. Sourced from weave/'s own former
in-repo demo (`connectors/demo-acme-electronics`, since relocated here
per weave's PLAN.md Phase 3.9) and reworked with Indian pricing (INR),
an Indian product catalog, Indian customer/address data, and GST fields
on the internal-only order view — a realistic addition for an Indian
retailer's backend that the original demo didn't need.
"""

from datetime import date

ORDERS: dict[str, dict] = {
    "ORD-1001": {
        "order_id": "ORD-1001",
        "customer_id": "cust_priya",
        "sku": "SKU-AB-14",
        "status": "shipped",
        "eta": "2026-09-08",
        "placed_on": "2026-09-01",
        "total_inr": 98999.00,
        "supplier": "Nirmaan Components Pvt Ltd",
        "cost_basis_inr": 64500.00,
        "gstin": "27AAJCT1234M1ZQ",
        "hsn_code": "8471",
        "cgst_inr": 8909.91,
        "sgst_inr": 8909.91,
        "igst_inr": 0.00,
    },
    "ORD-1002": {
        "order_id": "ORD-1002",
        "customer_id": "cust_arjun",
        "sku": "SKU-BP-27",
        "status": "processing",
        "eta": "2026-09-12",
        "placed_on": "2026-09-02",
        "total_inr": 6499.00,
        "supplier": "Nirmaan Components Pvt Ltd",
        "cost_basis_inr": 3900.00,
        "gstin": "27AAJCT1234M1ZQ",
        "hsn_code": "8518",
        "cgst_inr": 0.00,
        "sgst_inr": 0.00,
        "igst_inr": 1169.82,
    },
    "ORD-1003": {
        "order_id": "ORD-1003",
        "customer_id": "cust_priya",
        "sku": "SKU-RH-9",
        "status": "delivered",
        "eta": "2026-08-28",
        "placed_on": "2026-08-20",
        "total_inr": 3999.00,
        "supplier": "Swarna Audio Works",
        "cost_basis_inr": 2100.00,
        "gstin": "27AAJCT1234M1ZQ",
        "hsn_code": "8518",
        "cgst_inr": 359.91,
        "sgst_inr": 359.91,
        "igst_inr": 0.00,
    },
    "ORD-1004": {
        "order_id": "ORD-1004",
        "customer_id": "cust_kavya",
        "sku": "SKU-AB-14",
        "status": "delivered",
        "eta": "2026-08-25",
        "placed_on": "2026-08-18",
        "total_inr": 98999.00,
        "supplier": "Nirmaan Components Pvt Ltd",
        "cost_basis_inr": 64500.00,
        "gstin": "27AAJCT1234M1ZQ",
        "hsn_code": "8471",
        "cgst_inr": 0.00,
        "sgst_inr": 0.00,
        "igst_inr": 17819.82,
    },
    "ORD-1005": {
        "order_id": "ORD-1005",
        "customer_id": "cust_arjun",
        "sku": "SKU-VM-32",
        "status": "cancelled",
        "eta": None,
        "placed_on": "2026-08-30",
        "total_inr": 24999.00,
        "supplier": "Swarna Audio Works",
        "cost_basis_inr": 15600.00,
        "gstin": "27AAJCT1234M1ZQ",
        "hsn_code": "8528",
        "cgst_inr": 2249.91,
        "sgst_inr": 2249.91,
        "igst_inr": 0.00,
    },
}

PRODUCTS: dict[str, dict] = {
    "SKU-AB-14": {"sku": "SKU-AB-14", "name": "Tarang AirBook 14\" Laptop", "price_inr": 98999.00, "category": "laptops"},
    "SKU-BP-27": {"sku": "SKU-BP-27", "name": "Tarang Buds Pro Earbuds", "price_inr": 6499.00, "category": "audio"},
    "SKU-RH-9": {"sku": "SKU-RH-9", "name": "Tarang Resonance Headphones", "price_inr": 3999.00, "category": "audio"},
    "SKU-VM-32": {"sku": "SKU-VM-32", "name": "Tarang Vista 32\" Monitor", "price_inr": 24999.00, "category": "displays"},
}

INVENTORY: dict[str, dict] = {
    "SKU-AB-14": {"sku": "SKU-AB-14", "on_hand": 14, "reorder_threshold": 10, "warehouse": "WH-PUNE"},
    "SKU-BP-27": {"sku": "SKU-BP-27", "on_hand": 3, "reorder_threshold": 15, "warehouse": "WH-PUNE"},
    "SKU-RH-9": {"sku": "SKU-RH-9", "on_hand": 42, "reorder_threshold": 20, "warehouse": "WH-BLR"},
    "SKU-VM-32": {"sku": "SKU-VM-32", "on_hand": 0, "reorder_threshold": 8, "warehouse": "WH-BLR"},
}

WARRANTIES: dict[str, dict] = {
    "ORD-1001": {"order_id": "ORD-1001", "warranty_status": "active", "expires_on": "2028-09-01"},
    "ORD-1002": {"order_id": "ORD-1002", "warranty_status": "active", "expires_on": "2028-09-02"},
    "ORD-1003": {"order_id": "ORD-1003", "warranty_status": "active", "expires_on": "2027-08-28"},
    "ORD-1004": {"order_id": "ORD-1004", "warranty_status": "active", "expires_on": "2028-08-25"},
    "ORD-1005": {"order_id": "ORD-1005", "warranty_status": "void", "expires_on": None},
}

CUSTOMERS: dict[str, dict] = {
    "cust_priya": {
        "customer_id": "cust_priya", "name": "Priya Sharma", "email": "priya.sharma@example.test",
        "phone": "+91-98200-11234", "address": "B-204, Sunrise Apartments, Kothrud, Pune, Maharashtra 411038",
        "since": "2025-03-14",
    },
    "cust_arjun": {
        "customer_id": "cust_arjun", "name": "Arjun Mehta", "email": "arjun.mehta@example.test",
        "phone": "+91-99870-45678", "address": "14, Green Park Extension, New Delhi, Delhi 110016",
        "since": "2025-11-02",
    },
    "cust_kavya": {
        "customer_id": "cust_kavya", "name": "Kavya Reddy", "email": "kavya.reddy@example.test",
        "phone": "+91-90080-99321", "address": "Flat 7B, Lakeview Residency, Jubilee Hills, Hyderabad, Telangana 500033",
        "since": "2026-01-20",
    },
}


def sales_report(period: str) -> dict:
    """Aggregates ORDERS into a revenue report. period is accepted but not
    actually used to filter this fixed dataset (there's only one month of
    demo data) — it's part of the tool's schema so the shape matches what
    a real analytics endpoint would take."""
    non_cancelled = [o for o in ORDERS.values() if o["status"] != "cancelled"]
    revenue = sum(o["total_inr"] for o in non_cancelled)
    cost = sum(o["cost_basis_inr"] for o in non_cancelled)
    by_sku: dict[str, int] = {}
    for o in non_cancelled:
        by_sku[o["sku"]] = by_sku.get(o["sku"], 0) + 1
    top_sku = max(by_sku, key=by_sku.get) if by_sku else None
    return {
        "period": period,
        "orders_count": len(non_cancelled),
        "cancelled_count": len(ORDERS) - len(non_cancelled),
        "revenue_inr": round(revenue, 2),
        "gross_margin_inr": round(revenue - cost, 2),
        "top_selling_sku": top_sku,
        "generated_on": date.today().isoformat(),
    }


def customer_report(period: str) -> dict:
    """Aggregates CUSTOMERS/ORDERS into a customer-activity report, same
    period-is-schema-only caveat as sales_report."""
    orders_per_customer: dict[str, int] = {}
    for o in ORDERS.values():
        orders_per_customer[o["customer_id"]] = orders_per_customer.get(o["customer_id"], 0) + 1
    returning = sum(1 for c in orders_per_customer.values() if c > 1)
    return {
        "period": period,
        "active_customers": len(orders_per_customer),
        "returning_customers": returning,
        "new_customers": len(orders_per_customer) - returning,
        "generated_on": date.today().isoformat(),
    }

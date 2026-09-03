import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient

from api import app

client = TestClient(app)


def test_order_status_found():
    resp = client.get("/orders/ORD-1001/status")
    assert resp.status_code == 200
    body = resp.json()
    assert body == {"order_id": "ORD-1001", "status": "shipped", "eta": "2026-09-08"}


def test_order_status_never_leaks_supplier_cost_or_gst():
    resp = client.get("/orders/ORD-1001/status")
    body = resp.json()
    for field in ("supplier", "cost_basis_inr", "gstin", "hsn_code", "cgst_inr", "sgst_inr", "igst_inr"):
        assert field not in body


def test_order_status_not_found():
    resp = client.get("/orders/NOPE/status")
    assert resp.status_code == 404


def test_product_found():
    resp = client.get("/products/SKU-AB-14")
    assert resp.status_code == 200
    assert resp.json()["name"] == 'Tarang AirBook 14" Laptop'


def test_product_not_found():
    resp = client.get("/products/NOPE")
    assert resp.status_code == 404


def test_warranty_found():
    resp = client.get("/warranty/ORD-1001")
    assert resp.status_code == 200
    assert resp.json()["warranty_status"] == "active"


def test_internal_customer_has_pii():
    resp = client.get("/internal/customers/cust_priya")
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == "priya.sharma@example.test"
    assert "phone" in body and "address" in body


def test_internal_customer_not_found():
    resp = client.get("/internal/customers/nope")
    assert resp.status_code == 404


def test_internal_order_includes_supplier_cost_and_gst():
    resp = client.get("/internal/orders/ORD-1001")
    assert resp.status_code == 200
    body = resp.json()
    assert body["supplier"] == "Nirmaan Components Pvt Ltd"
    assert body["cost_basis_inr"] == 64500.00
    assert body["gstin"] == "27AAJCT1234M1ZQ"
    assert body["hsn_code"] == "8471"
    assert body["cgst_inr"] == 8909.91
    assert body["sgst_inr"] == 8909.91


def test_internal_inventory_list():
    resp = client.get("/internal/inventory")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 4
    assert any(i["sku"] == "SKU-VM-32" and i["on_hand"] == 0 for i in items)


def test_internal_inventory_item_not_found():
    resp = client.get("/internal/inventory/NOPE")
    assert resp.status_code == 404


def test_sales_analytics_excludes_cancelled_orders():
    resp = client.get("/internal/analytics/sales?period=this_month")
    assert resp.status_code == 200
    body = resp.json()
    assert body["period"] == "this_month"
    assert body["orders_count"] == 4  # 5 orders minus 1 cancelled
    assert body["cancelled_count"] == 1
    assert body["revenue_inr"] > 0
    assert body["gross_margin_inr"] > 0


def test_sales_analytics_defaults_period():
    resp = client.get("/internal/analytics/sales")
    assert resp.json()["period"] == "current"


def test_customer_analytics_counts_returning_customers():
    resp = client.get("/internal/analytics/customers?period=this_month")
    assert resp.status_code == 200
    body = resp.json()
    # cust_priya: ORD-1001, ORD-1003 (2 orders). cust_arjun: ORD-1002,
    # ORD-1005 (2 orders, one cancelled but still counted as activity).
    # cust_kavya: ORD-1004 (1 order).
    assert body["active_customers"] == 3
    assert body["returning_customers"] == 2
    assert body["new_customers"] == 1

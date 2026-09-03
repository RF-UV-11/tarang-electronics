"""Tarang Electronics — a fictional Indian consumer-electronics
retailer's real public-facing API, standing in for "a business that
already runs its own systems and wants Weave to reason over them
without building an MCP server." Every route here is a genuine HTTP
endpoint a real business could run; onboard.py is what turns a subset
of them into Weave tools via the weave SDK's add_tool(), with
visibility/category exactly as a real integrator would set them.

This project is one of two independent, external reference projects
for weave/'s PLAN.md Phase 3.9 — it lives entirely outside the weave/
repo, exactly as a real tenant's integration would, and installs the
`weave` SDK the same way a real integrator would pre-release (see
initialize.sh). See README.md for the full six-step onboarding story.

Deliberate design choice for the visibility split: sensitive fields
(supplier, cost basis, GST breakdown, customer PII) live only on
internal-only routes, never as extra fields on an external route's
response — the safest way to prevent a customer-facing bot from ever
seeing them at all, one level earlier than a guardrail would need to
catch it.
"""

from fastapi import FastAPI, HTTPException

from data import CUSTOMERS, INVENTORY, ORDERS, PRODUCTS, WARRANTIES, customer_report, sales_report

app = FastAPI(title="Tarang Electronics API", description="Indian consumer-electronics retailer — weave SDK reference integration")

# --------------------------------------------------------------------
# External / customer-facing routes — safe to register as visibility=
# "external" tools. No supplier, cost, GST, or PII fields anywhere below.
# --------------------------------------------------------------------


@app.get("/orders/{order_id}/status")
def get_order_status(order_id: str):
    order = ORDERS.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail=f"no such order {order_id}")
    return {"order_id": order["order_id"], "status": order["status"], "eta": order["eta"]}


@app.get("/products/{sku}")
def get_product(sku: str):
    product = PRODUCTS.get(sku)
    if not product:
        raise HTTPException(status_code=404, detail=f"no such product {sku}")
    return product


@app.get("/warranty/{order_id}")
def get_warranty(order_id: str):
    warranty = WARRANTIES.get(order_id)
    if not warranty:
        raise HTTPException(status_code=404, detail=f"no warranty record for order {order_id}")
    return warranty


# --------------------------------------------------------------------
# Internal-only routes — visibility="internal" tools. Staff bot profiles
# can use these; a customer-facing external profile never sees them, at
# the tool-assembly stage, not via a guardrail catching it after the fact.
# --------------------------------------------------------------------


@app.get("/internal/customers/{customer_id}")
def get_customer(customer_id: str):
    customer = CUSTOMERS.get(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail=f"no such customer {customer_id}")
    return customer


@app.get("/internal/orders/{order_id}")
def get_order_internal(order_id: str):
    """Same order, full detail — including supplier, cost basis, and the
    GST breakdown (GSTIN, HSN code, CGST/SGST/IGST), fields the external
    /orders/{id}/status route never exposes."""
    order = ORDERS.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail=f"no such order {order_id}")
    return order


@app.get("/internal/inventory")
def list_inventory():
    return {"items": list(INVENTORY.values())}


@app.get("/internal/inventory/{sku}")
def get_inventory_item(sku: str):
    item = INVENTORY.get(sku)
    if not item:
        raise HTTPException(status_code=404, detail=f"no inventory record for {sku}")
    return item


@app.get("/internal/analytics/sales")
def get_sales_analytics(period: str = "current"):
    return sales_report(period)


@app.get("/internal/analytics/customers")
def get_customer_analytics(period: str = "current"):
    return customer_report(period)


if __name__ == "__main__":
    import os

    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("DEMO_PORT", "9101")))

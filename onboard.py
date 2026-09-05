"""onboard.py — the actual tutorial for integrating `weave` into an
existing business. Read this file top to bottom to learn how to wire
your own systems into Weave; each STEP below narrates one stage of the
real onboarding sequence a business goes through, in the order they'd
actually do it. This is not a toy — every RPC/SDK call here is exactly
what a real integrator would run, just against a fictional business
(Tarang Electronics, an Indian consumer-electronics retailer) and a
fictional dataset (data.py/api.py).

Prerequisites (see README.md for the full walkthrough):
  1. weave/'s own stack is running: `core` (CORE_ADDR, default
     localhost:9090) reachable, with Mongo/Redis/Qdrant behind it.
  2. This project's own API is running (DEMO_API_URL, default
     http://localhost:9101) — that's api.py, started by initialize.sh.
  3. The `weave` SDK is installed from weave/'s packages/weave-sdk (see
     initialize.sh / pyproject.toml) — this project never vendors or
     copies weave's code, it depends on it like any external consumer
     would.

Usage:
    ./.venv/Scripts/python.exe onboard.py

Idempotency: none — re-running creates a second tenant with a fresh
random suffix each time. This is an onboarding walkthrough, not a
migration; delete the tenant via core if you need to start over.
"""

import asyncio
import os
import secrets

import weave

CORE_ADDR = os.environ.get("CORE_ADDR", "localhost:9090")
DEMO_API_URL = os.environ.get("DEMO_API_URL", "http://localhost:9101")
OWNER_EMAIL = os.environ.get("DEMO_OWNER_EMAIL", "owner@tarang-electronics.test")
OWNER_PASSWORD = os.environ.get("DEMO_OWNER_PASSWORD", "hunter2hunter2")


async def _step1_sign_up() -> str:
    """STEP 1 — Sign up: CreateTenant + Register (an owner account), via
    `weave.sign_up()` — core's real public bootstrap RPCs, unauthenticated
    by design for exactly this reason (there's no token to present before
    a tenant/user exists at all), not a special-cased dev shortcut. Every
    real integration starts here, exactly like this — and, like every
    other call in this file, needs nothing beyond the `weave` package
    itself (no direct core-proto/gRPC-stub access of its own)."""
    print("STEP 1: signing up — CreateTenant + Register(owner)")
    tenant_id = await weave.sign_up(
        display_name=f"Tarang Electronics ({secrets.token_hex(3)})",
        email=OWNER_EMAIL,
        password=OWNER_PASSWORD,
        core_addr=CORE_ADDR,
    )
    print(f"   -> tenant_id={tenant_id}")
    return tenant_id


async def main() -> None:
    tenant_id = await _step1_sign_up()

    print("STEP 2: authenticating — weave.connect_async() (Login -> JWT)")
    client = await weave.connect_async(
        tenant_id=tenant_id, email=OWNER_EMAIL, password=OWNER_PASSWORD, core_addr=CORE_ADDR
    )
    try:
        print()
        print("STEP 3: describing the business's systems — weave.connect() + add_tool()")
        print("        (each tool's visibility/category is a deliberate decision, not left default)")

        # --- External tools: safe for a customer-facing bot -----------
        await client.add_tool(
            name="track_order",
            description=(
                "Look up the shipping status and estimated delivery date for a customer's order, "
                "given the order ID (e.g. ORD-1001)."
            ),
            endpoint=f"{DEMO_API_URL}/orders/{{order_id}}/status",
            method="GET",
            params_schema={
                "type": "object",
                "properties": {"order_id": {"type": "string", "description": "The order ID, e.g. ORD-1001."}},
                "required": ["order_id"],
            },
            visibility="external",
            category="general",
        )
        await client.add_tool(
            name="get_product_info",
            description="Look up a product's name, price (INR), and category by its SKU (e.g. SKU-AB-14).",
            endpoint=f"{DEMO_API_URL}/products/{{sku}}",
            method="GET",
            params_schema={
                "type": "object",
                "properties": {"sku": {"type": "string", "description": "The product SKU, e.g. SKU-AB-14."}},
                "required": ["sku"],
            },
            visibility="external",
            category="general",
        )
        await client.add_tool(
            name="check_warranty",
            description="Check whether an order's warranty is active or void, and its expiry date, given the order ID.",
            endpoint=f"{DEMO_API_URL}/warranty/{{order_id}}",
            method="GET",
            params_schema={
                "type": "object",
                "properties": {"order_id": {"type": "string", "description": "The order ID, e.g. ORD-1001."}},
                "required": ["order_id"],
            },
            visibility="external",
            category="general",
        )

        # --- Internal-only tools: staff bots only ----------------------
        await client.add_tool(
            name="get_customer_details",
            description=(
                "Look up a customer's full contact details (name, email, phone, address) by customer ID. "
                "Contains PII — internal/staff use only."
            ),
            endpoint=f"{DEMO_API_URL}/internal/customers/{{customer_id}}",
            method="GET",
            params_schema={
                "type": "object",
                "properties": {"customer_id": {"type": "string", "description": "The customer ID, e.g. cust_priya."}},
                "required": ["customer_id"],
            },
            visibility="internal",
            category="general",
        )
        await client.add_tool(
            name="get_order_internal_details",
            description=(
                "Look up full internal details for an order, including supplier, cost basis, and GST breakdown "
                "(GSTIN, HSN code, CGST/SGST/IGST) — internal/staff use only, never expose these figures to a customer."
            ),
            endpoint=f"{DEMO_API_URL}/internal/orders/{{order_id}}",
            method="GET",
            params_schema={
                "type": "object",
                "properties": {"order_id": {"type": "string", "description": "The order ID, e.g. ORD-1001."}},
                "required": ["order_id"],
            },
            visibility="internal",
            category="general",
        )
        await client.add_tool(
            name="check_inventory",
            description="List current stock levels and reorder thresholds for every product SKU. Internal/staff use only.",
            endpoint=f"{DEMO_API_URL}/internal/inventory",
            method="GET",
            visibility="internal",
            category="general",
        )
        await client.add_tool(
            name="get_sales_report",
            description=(
                "Get an aggregate sales report: revenue (INR), order counts, gross margin, and the top-selling "
                "product for a given period. Internal/staff use only."
            ),
            endpoint=f"{DEMO_API_URL}/internal/analytics/sales",
            method="GET",
            params_schema={
                "type": "object",
                "properties": {"period": {"type": "string", "description": "Reporting period, e.g. 'this_month'."}},
            },
            visibility="internal",
            category="analytics",
        )
        await client.add_tool(
            name="get_customer_activity_report",
            description=(
                "Get an aggregate customer-activity report: how many active, new, and returning customers "
                "there were in a given period. Internal/staff use only."
            ),
            endpoint=f"{DEMO_API_URL}/internal/analytics/customers",
            method="GET",
            params_schema={
                "type": "object",
                "properties": {"period": {"type": "string", "description": "Reporting period, e.g. 'this_month'."}},
            },
            visibility="internal",
            category="analytics",
        )
        print("   -> registered 8 tools (3 external, 5 internal)")

        print()
        print("STEP 4: shaping the bots — create_bot_profile() per audience")
        external_profile = await client.create_bot_profile(
            name="external",
            persona="personas/external.md",
            channels=["web-widget"],
            roles_allowed=["customer"],
            visibility="external",
            guardrails=[
                "Never disclose supplier names.",
                "Never disclose cost basis, margins, GST figures, or internal pricing.",
                "Never disclose another customer's contact details.",
            ],
            web_search_enabled=True,
        )
        internal_profile = await client.create_bot_profile(
            name="internal",
            persona="personas/internal.md",
            channels=["slack"],
            roles_allowed=["staff", "admin", "owner"],
            visibility="internal",
            web_search_enabled=False,
        )
        print(f"   -> external profile: {external_profile.id} (channel web-widget, guardrails on)")
        print(f"   -> internal profile: {internal_profile.id} (channel slack, sees all 8 tools)")

        print()
        print("STEP 5: connect a channel — the step this walkthrough stops short of.")
        print("        A real deployment embeds web/'s chat widget on tarang-electronics.example")
        print("        pointed at the external profile's web-widget channel, and/or wires a Slack")
        print("        app pointed at the internal profile's slack channel. See README.md.")
        print()
        print("STEP 6: go live — once a channel is connected, end users (Tarang's own customers")
        print("        or staff) interact through it. Until then, weave/'s own orchestrator/dev_cli.py")
        print("        exercises the exact same ChatStream RPC a real channel integration would call")
        print("        (see README.md for the exact command against this tenant).")
        print()
        print(f"tenant_id={tenant_id}")
        print(f"owner_email={OWNER_EMAIL}")
        print(f"owner_password={OWNER_PASSWORD}")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())

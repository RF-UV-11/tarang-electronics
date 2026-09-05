# Tarang Electronics

A fictional Indian consumer-electronics retailer ("Tarang" = "wave" in
Hindi — a nod to the platform this project integrates with), used as a
**reference project for integrating the [`weave`](../weave) SDK**. This
repo is entirely independent of `weave/` — its own git history, its own
dependencies — exactly the shape a real Weave tenant's integration takes:
a business's own code, in a business's own codebase, never inside the
platform repo itself.

Read this file (and `onboard.py`, `api.py`) to learn exactly how to wire
an existing business's systems into Weave. Nothing here is a toy stand-in
for "real code" — `api.py` is a genuine FastAPI service with the kind of
public/internal route split any online retailer would already have, and
`onboard.py` calls the exact same SDK/RPC surface a real integrator would.

## The six-step onboarding flow

Every business connecting to Weave goes through the same sequence.
`onboard.py` narrates each step explicitly as it runs; here's what each
one means and where the code for it lives.

1. **Sign up** — `CreateTenant` + `Register` an owner account, via a
   single `weave.sign_up()` call. These are `core`'s real public
   bootstrap RPCs, unauthenticated by design (there's no token to present
   before a tenant/user exists at all). See `onboard.py`'s `_step1_sign_up`.
2. **Authenticate** — `Login` to get a JWT, exactly as any caller (the SDK,
   `weave/web`, or a hand-rolled integration) would.
3. **Describe the business's systems** — `weave.connect()` then repeated
   `add_tool()` calls, one per existing HTTP endpoint Tarang wants Weave
   to reason over. Each call makes a deliberate `visibility`
   (`external`/`internal`) and `category` (`general`/`analytics`)
   decision — see the comments in `onboard.py` for why each of the 8
   tools here got the value it did. (A business with a much larger API —
   dozens to hundreds of routes — doesn't have to hand-write one
   `add_tool()` call per endpoint: `client.add_tools_from_openapi()`
   registers a deliberate subset of an existing OpenAPI spec in one call.
   Tarang's own API is small enough that hand-written calls are clearer
   to read as a tutorial, so `onboard.py` doesn't use it, but see
   `weave/docs/architecture/ARCHITECTURE.md` §3 for how it works.) A tool
   can also be marked `auth_mode="user_token"` for an endpoint that must
   be scoped to the specific signed-in customer asking (e.g. a
   `get_my_order_history` a real electronics retailer might expose) —
   none of Tarang's 8 tools need this (all 8 answer the same regardless
   of *who's* asking), so `onboard.py` leaves every tool at the default
   `auth_mode="none"`, but see `ARCHITECTURE.md` §3 for the full
   mechanism.
4. **Shape the bots** — `create_bot_profile()` once per distinct audience.
   Tarang has two: `external` (customers, on the `web-widget` channel,
   with guardrails against leaking supplier/cost/GST figures or another
   customer's PII) and `internal` (staff, on `slack`, sees everything).
   Each profile can also set its own `persona` (the literal system-prompt
   text for that bot — see `weave`'s `create_bot_profile()` docstring)
   and choose which LLM backend generates its answers via
   `llm_provider`/`llm_model` (defaults to orchestrator's local Ollama
   model if left unset); this project's `onboard.py` doesn't set either,
   relying on those defaults, but a real integrator often would.
5. **Connect a channel** — the step this reference project intentionally
   stops short of automating, since it's specific to how *you* reach your
   users: embed `weave/web`'s chat widget on your own site pointed at the
   external profile's `web-widget` channel, and/or wire a Slack app
   pointed at the internal profile's `slack` channel. Nothing today
   listens on either channel for this fictional tenant — `onboard.py`
   prints this explicitly rather than silently skipping it.
6. **Go live** — once a channel exists, real end users interact through
   it. Until then, verify the exact same `ChatStream` RPC a real channel
   would call using `weave`'s own dev harness (see **Verifying** below).

## Layout

- `data.py` — canned in-memory data: orders, products, inventory,
  warranties, customers. Indian pricing (INR), Indian customer/address
  data, and GST fields (GSTIN, HSN code, CGST/SGST/IGST) on the
  internal-only order view.
- `api.py` — the FastAPI service. 3 external routes (order status,
  product info, warranty), 5 internal-only routes (customer PII, full
  order detail incl. GST/cost, inventory, sales analytics,
  customer-activity analytics).
- `onboard.py` — runs the six-step flow above against a real running
  Weave `core`.
- `tests/test_api.py` — asserts the external/internal field split holds
  (e.g. the external order-status route never leaks `supplier`/GST
  fields) alongside ordinary endpoint correctness.

## Running it

Requires a sibling `weave/` checkout (this project depends on
`weave/packages/weave-sdk` as a path dependency — see `initialize.sh` —
the same way a real integrator would pre-release; swap for `pip install
weave-sdk` once it's published, with zero other code changes) and
weave's own stack already running (`core` + Mongo/Redis/Qdrant, plus
`mcp-gateway` — see `weave/PLAN.md` and `weave/infra/`). The `weave` SDK
is self-contained (bundles its own generated gRPC stubs — see
`weave/packages/weave-sdk/weave/_core_client.py`), so this is the only
package this project needs from `weave/` — no separate
`weave/packages/shared-clients` install step.

```bash
./initialize.sh              # venv, deps, proto codegen, starts api.py on :9101
```

In a second shell, once the API is up:

```bash
./.venv/Scripts/python.exe onboard.py
```

This prints `tenant_id`/`owner_email`/`owner_password` at the end —
save them for verification.

### Tests

```bash
./.venv/Scripts/python.exe -m pytest
```

### Verifying (step 6)

Using `weave/orchestrator`'s own dev harness against the tenant
`onboard.py` just created. The owner account `onboard.py` registers has
role `owner`, which the `external` profile's `roles_allowed` (customer
only) correctly rejects — verify against the `internal` profile's
`slack` channel instead:

```bash
cd ../weave/orchestrator
./.venv/Scripts/python.exe dev_cli.py \
  --tenant-id <tenant_id> --email owner@tarang-electronics.test --password hunter2hunter2 \
  --channel slack "What's the status of order ORD-1001?"
```

This exercises the exact `ChatStream` RPC a real channel integration
would call — dynamic tool discovery and (for a real `customer`-role
caller against the `external` profile's `web-widget` channel) the
external visibility filter and guardrails all apply exactly as they
would for a real customer.

## Config

| Env var | Default | Meaning |
|---|---|---|
| `DEMO_PORT` | `9101` | Port `api.py` listens on |
| `WEAVE_REPO` | `../weave` | Path to the sibling `weave/` checkout |
| `CORE_ADDR` | `localhost:9090` | `core`'s gRPC address |
| `DEMO_API_URL` | `http://localhost:9101` | Where `onboard.py` registers tools against |
| `DEMO_OWNER_EMAIL` / `DEMO_OWNER_PASSWORD` | `owner@tarang-electronics.test` / `hunter2hunter2` | Owner account created in step 1 |

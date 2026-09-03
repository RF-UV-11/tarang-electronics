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

1. **Sign up** — `CreateTenant` + `Register` an owner account. These are
   `core`'s real public bootstrap RPCs, unauthenticated by design (there's
   no token to present before a tenant/user exists at all). See
   `onboard.py`'s `_step1_sign_up_and_step2_authenticate`.
2. **Authenticate** — `Login` to get a JWT, exactly as any caller (the SDK,
   `weave/web`, or a hand-rolled integration) would.
3. **Describe the business's systems** — `weave.connect()` then repeated
   `add_tool()` calls, one per existing HTTP endpoint Tarang wants Weave
   to reason over. Each call makes a deliberate `visibility`
   (`external`/`internal`) and `category` (`general`/`analytics`)
   decision — see the comments in `onboard.py` for why each of the 8
   tools here got the value it did.
4. **Shape the bots** — `create_bot_profile()` once per distinct audience.
   Tarang has two: `external` (customers, on the `web-widget` channel,
   with guardrails against leaking supplier/cost/GST figures or another
   customer's PII) and `internal` (staff, on `slack`, sees everything).
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
`weave/packages/weave-sdk` and `weave/packages/shared-clients` as a
path dependency — see `initialize.sh` — the same way a real integrator
would pre-release; swap for `pip install weave-sdk` once it's published,
with zero other code changes) and weave's own stack already running
(`core` + Mongo/Redis/Qdrant, plus `mcp-gateway` — see `weave/PLAN.md`
and `weave/infra/`).

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
`onboard.py` just created:

```bash
cd ../weave/orchestrator
./.venv/Scripts/python.exe dev_cli.py \
  --tenant-id <tenant_id> --email owner@tarang-electronics.test --password hunter2hunter2 \
  --channel web-widget "What's the status of order ORD-1001?"
```

This exercises the exact `ChatStream` RPC a real `web-widget` channel
integration would call — dynamic tool discovery, the external
visibility filter, and guardrails all apply exactly as they would for a
real customer.

## Config

| Env var | Default | Meaning |
|---|---|---|
| `DEMO_PORT` | `9101` | Port `api.py` listens on |
| `WEAVE_REPO` | `../weave` | Path to the sibling `weave/` checkout |
| `CORE_ADDR` | `localhost:9090` | `core`'s gRPC address |
| `DEMO_API_URL` | `http://localhost:9101` | Where `onboard.py` registers tools against |
| `DEMO_OWNER_EMAIL` / `DEMO_OWNER_PASSWORD` | `owner@tarang-electronics.test` / `hunter2hunter2` | Owner account created in step 1 |

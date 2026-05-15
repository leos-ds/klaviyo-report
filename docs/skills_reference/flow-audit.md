---
name: klaviyo-flow-audit
description: Run a deep flow performance audit on the connected Klaviyo account — pulls real metrics, compares to industry benchmarks, drills down to per-message level, and outputs a prioritized punch list with concrete fixes. Use when the user says "audit flows", "audit klaviyo", "flow performance check", "udělej audit flow", "co je špatně s flowy", "performance audit pro [client]", or anything similar. Do not skip the per-message drilldown — it's how you find the actual root cause.
---

# Klaviyo Flow Audit

Pulls live performance data and produces a real audit, not a metadata summary. Encodes industry benchmarks for ecommerce flow types and flags every flow that deviates significantly.

## Industry benchmarks (food/beverage e-commerce, 2025)

Use these as the baseline. If the client is in a different vertical, note that and adjust expectations 5-10 percentage points.

| Flow type | Open rate (good) | CTR (good) | Conv rate (good) | Notes |
|---|---|---|---|---|
| Welcome | 35%+ | 5%+ | 4%+ | Highest engagement of any flow |
| Cart abandonment | 40%+ | 6%+ | 3%+ | Highly engaged audience — already in cart |
| Checkout abandonment | 45%+ | 8%+ | 4%+ | Extremely engaged — was on checkout page |
| Browse abandonment | 35%+ | 4%+ | 1.5%+ | Lower intent than cart |
| Post-purchase | 40%+ | 6%+ | 1%+ | Already converted; conversion = repeat order or cross-sell |
| Winback | 20%+ | 2.5%+ | 1%+ | Dormant audience |
| Sunset | 5%+ | 0.5%+ | 0.1%+ | Intentionally low — purpose is to identify dormant |

If a flow is more than 30% below the "good" threshold, flag as red. Within 30% but below threshold, flag as yellow.

## Workflow

### Step 1 — Find the conversion metric

Call `klaviyo_get_metrics` filtered to integration Shopify (or relevant ecommerce platform). Find the metric named "Placed Order" — note its ID. If not present, fall back to any conversion-style metric and note the substitution.

### Step 2 — Pull flow list

Call `klaviyo_get_flows` with `pageSize: 50`, fields `["name", "status", "trigger_type", "created", "updated"]`. Capture all live flow IDs.

### Step 3 — Pull performance for all live flows

Call `klaviyo_get_flow_report` once with all live flow IDs:

- `conversionMetricId`: from step 1
- `timeframe`: `{ key: "last_90_days" }` (default; use 30 or 365 days if the user specifies)
- `filters`: send_channel equals email + flow_id contains-any [list of live flow IDs]
- `groupBy`: `["flow_id", "flow_name", "send_channel"]`
- `statistics`: `["recipients", "delivered", "opens_unique", "open_rate", "clicks_unique", "click_rate", "click_to_open_rate", "conversion_uniques", "conversion_rate", "unsubscribe_rate", "bounce_rate"]`
- `valueStatistics`: `["conversion_value", "revenue_per_recipient", "average_order_value"]`

Use the `flow_aggregation` array for flow-level rollups.

### Step 4 — Categorize and grade

For each flow, infer category from its name (welcome, cart, checkout, post-purchase, browse, sunset, winback) and look up the matching benchmark. Compute grade for open rate, CTR, conversion rate: green (above good), yellow (between warn and good), red (below warn).

### Step 5 — Drilldown on red flows

For every flow flagged red on open rate or conversion rate, call `klaviyo_get_flow_report` again with `groupBy: ["flow_id", "flow_message_id", "flow_message_name", "send_channel"]` filtered to that single flow. This shows per-message performance — usually one specific email in the sequence is dragging the average down.

### Step 6 — Generate the audit document

Write `<client>_audit.md` to the outputs folder with:

**Executive summary** (3-5 sentences). Lead with the worst problem and the highest-revenue opportunity.

**Performance table** with columns: Flow, Recipients, Open rate (with benchmark delta), CTR, Conv rate, RPR, Total revenue, Grade.

**Red flag findings** — for each red-flagged flow, list:
- The actual numbers
- Suspected root cause hypotheses (subject lines, send timing, deliverability, attribution gap, weak CTA, segment problem)
- Specific fix to test next

**Per-message drilldown findings** — surface which specific emails in red flows are the worst offenders.

**Punch list (P1/P2/P3)** with effort estimates.

**90-day plan** with weekly milestones.

### Step 7 — Cross-reference dashboard

Tell the user the same data is now visible in the `digismoothie-klaviyo-agency` artifact with click-to-drill capability. The audit doc is the report; the dashboard is the live monitor.

## Common diagnoses for low cart/checkout abandonment open rates

- **Subject line problems:** generic "You left something in your cart" instead of product-specific or urgency-based
- **Send timing:** delay too long (>2h for first send) or too short (<15min, gets caught in dedupe)
- **Deliverability:** check inbox provider mix — Czech email lists often have 30%+ on seznam.cz, where DKIM/DMARC misconfiguration tanks deliverability
- **Trigger filters:** flow excludes engaged segment by mistake (e.g. "exclude profiles with placed order in last 1 day" running too aggressively)
- **From address:** generic "noreply@" suppresses opens; switch to a person or branded address
- **Pre-header / preview text:** missing or duplicate of subject line

## Critical rules

- Never report numbers without pulling them. If you cannot pull data, say so explicitly — do not speculate.
- Always include the actual benchmark thresholds in the report so the reader can sanity-check the grade.
- Per-message drilldown is mandatory for red flags. The flow-level number is an average; the fix is at the message level.
- Do not auto-fix anything. Audit only proposes; humans approve and ship.

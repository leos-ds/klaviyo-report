---
name: klaviyo-client-onboarding
description: Onboard a new Digismoothie client to a dedicated Cowork chat — verifies Klaviyo connection, extracts brand voice from past campaigns, runs flow audit, and produces a starter document set in the workspace. Use whenever the user says "onboard new client", "start setup for [client]", "set up Klaviyo for [client]", "kickoff [client] account", "připravit účet [klient]", or any first-touch client setup phrase. Run once at the start of a per-client chat.
---

# Klaviyo Client Onboarding

End-to-end onboarding workflow for a new Digismoothie Klaviyo client. Produces three artifacts in the user's workspace: a brand voice profile, a flow audit, and a 90-day plan.

## Prerequisites

This skill expects the chat to already have the Klaviyo MCP connected to the target client account. Confirm by calling `klaviyo_get_account_details` before doing anything else. If the connector is connected to a different account, stop and surface that to the user — do not proceed.

## Workflow

### Step 1 — Verify connection

Call `klaviyo_get_account_details` and report the connected account: organization name, sender email, currency, timezone, industry. Ask the user to confirm this is the intended client. If not, halt and tell the user how to switch the Klaviyo connector to the correct account.

### Step 2 — Pull baseline data

Pull all of these in parallel where possible:

- `klaviyo_get_campaigns` with `channel: "email"`, filter `status equals Sent`, fields `["name", "status", "send_time", "created_at"]` — for naming patterns, cadence, topical themes
- `klaviyo_get_flows` with `pageSize: 50`, fields `["name", "status", "trigger_type", "created", "updated"]` — for flow inventory
- `klaviyo_get_metrics` filtered to integration `Shopify` (or whatever ecommerce platform is connected) — to find the conversion metric ID for `Placed Order`

If the campaigns response is large (>50K chars), spawn a subagent to parse it. Do NOT load the full response into your context.

### Step 3 — Brand voice profile

Write `<client>_brand_voice.md` to the outputs folder following the structure in `references/brand_voice_template.md`. Extract from campaign metadata:

- Account snapshot (from `klaviyo_get_account_details`)
- Naming conventions observed in campaign names
- Recurring topics and angles (seasonal hooks, product launches, social proof, recipes)
- Series cadence (launch → reminder → last-call patterns)
- Open questions for the client team to confirm (tykání/vykání, color palette from brand assets, sender name variants, no-go list)

Mark anything you cannot determine from metadata as "TBD — extract from individual campaign bodies in next pass."

### Step 4 — Flow audit

Trigger the `klaviyo-flow-audit` skill in this same session. It produces `<client>_audit.md` with real performance data, benchmark comparison, and prioritized punch list.

### Step 5 — 90-day plan

Append a 90-day plan section to the audit file with weekly milestones based on the gaps found:

- Weeks 1-2: Finish any draft flows that are P1.
- Weeks 3-4: Launch the highest-impact missing flow.
- Weeks 5-6: Standardize naming and run a brand voice deep-dive on 5 campaign bodies.
- Weeks 7-8: A/B test the worst-performing live flow.
- Weeks 9-10: Add the next missing flow.
- Weeks 11-12: Q+1 campaign calendar.

### Step 6 — Summary

Tell the user what was created with computer:// links to each file. Recommend they open the agency dashboard artifact (`digismoothie-klaviyo-agency`) to see the live performance flags for this client.

## Critical rules

- Never paste Klaviyo API keys into chat output, files, or tool arguments. The connector handles auth.
- Always confirm the connected account before running any data pulls — the Klaviyo connector is per-chat and the user may have switched accounts.
- Keep all client deliverables in Czech if the account locale or sender suggests Czech. Default to the language used in the existing campaign names.
- Do not auto-post to Slack as part of onboarding. Per Digismoothie direction, all reporting is centralized in the agency dashboard, not per-client Slack channels.

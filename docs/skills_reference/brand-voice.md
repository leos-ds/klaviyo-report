---
name: klaviyo-brand-voice-extract
description: Deep brand voice extraction from a client's actual sent campaign content (subject lines, body, CTAs). Use when the user says "extract brand voice", "deep brand voice", "analyze campaigns content", "rozbor kampaní", "přečti kampaně", or wants to enrich an existing brand voice profile beyond metadata. Pulls full campaign messages — not just names — to identify tonality, vocabulary, sentence structure, and CTA patterns. Slow but thorough; intended as a one-off enrichment step after onboarding.
---

# Klaviyo Brand Voice Deep Extract

The `klaviyo-client-onboarding` skill produces a brand voice profile from campaign metadata only. This skill goes deeper: it pulls actual campaign content (subjects, preview text, body) and analyzes the language patterns at scale.

## When to run

- After `klaviyo-client-onboarding` finished and the brand voice profile has many "TBD" placeholders
- When the team wants to onboard a new copywriter and needs a comprehensive style guide
- Before a major campaign push where consistency matters

## Workflow

### Step 1 — Pick a representative sample

Call `klaviyo_get_campaigns` with `channel: email`, filter `status equals Sent`. Pick the 10-20 most recent campaigns by `send_time`. Skew toward variety — include launches, reminders, plain-text variants, and seasonal campaigns.

If the response is too large to load, use a subagent to filter it down to the 20 most recent IDs and persist that list to a temporary file.

### Step 2 — Pull full content per campaign

For each selected campaign, call `klaviyo_get_campaign` with the campaign's ID and include `campaignMessageFields` covering subject, preview_text, from_email, from_label, body. Capture:

- Subject line
- Preview text
- From label (sender name variants?)
- Body content (HTML — strip to text for analysis)

### Step 3 — Analyze

For the collected content, identify:

**Subject line patterns:**
- Average length in characters
- Use of personalization tokens
- Emoji frequency and which emoji
- Question vs statement vs imperative ratio
- Common opening words
- Urgency triggers ("Poslední šance", "Dnes končí")

**Preview text patterns:**
- Length, relationship to subject (extension vs duplicate vs unrelated)
- Whether preview text is set at all (gap signal)

**Body patterns:**
- Greeting style (Ahoj / Dobrý den / no greeting)
- Person address (tykání 2sg vs vykání 2pl) — count instances
- Sentence length distribution
- Common phrases that recur (could be brand catchphrases)
- CTA wording — list every CTA verb used and frequency
- Sign-off style
- Use of formatting (bold, italic, emoji in body, lists)

**Vocabulary:**
- 30 most distinctive nouns/verbs (filter common stopwords)
- Industry-specific terms
- Trademark words the brand owns

### Step 4 — Update brand voice profile

Find `<client>_brand_voice.md` in the workspace. Replace the "TBD" placeholders with concrete extracted patterns. Mark any patterns that show inconsistency (e.g. tykání and vykání both appearing) as "INCONSISTENT — needs team decision."

Add a new section "Subject line cookbook" with 5-10 templates extracted from the highest-performing campaigns (cross-reference `klaviyo_get_campaign_report` for opens to identify performers).

### Step 5 — No-go list

Identify words, phrases, or formatting choices that NEVER appear in the brand's content. These become the no-go list. Examples: hard-sell language, English fallback, certain emoji families, exclamation point spam.

### Step 6 — Output

Update the brand voice file in place. Tell the user what changed and which sections still need human input (color palette, formal stylistic decisions).

## Critical rules

- Pull each campaign's content directly — do not synthesize patterns from names alone (that's the onboarding skill's job).
- Strip HTML to text for analysis. If `mammoth` or similar library is unavailable, use simple regex to remove tags and decode entities.
- Quote actual examples verbatim in the analysis. "Brand uses friendly tone" is useless; "Brand uses 'Ahoj milí zákazníci' as standard greeting" is actionable.
- Flag inconsistencies, don't smooth them over. Inconsistency is itself a finding worth surfacing.
- Never invent CTAs or phrases. Every claim about the brand voice must trace back to a real campaign with a quoted example.

# DNS authentication rules for Klaviyo senders

## SPF

A valid SPF record is a TXT record on the apex domain starting with `v=spf1`.

For Klaviyo to send authenticated mail on behalf of the domain, the record must include one of:
- `include:_spf.klaviyo.com`
- `include:sendgrid.net` (if the account uses Klaviyo's SendGrid relay — older accounts)

**Common errors:**
- Multiple SPF records on the same domain (RFC violation; combine into one)
- Record exceeds 10 DNS lookups (use `+` mechanisms count); fix with SPF flattening
- Ends with `~all` (soft-fail) instead of `-all` (hard-fail) — `~all` is OK during ramp-up, `-all` is the production target after validation

## DKIM

Klaviyo signs messages with two selectors by default:
- `klaviyo1._domainkey.<domain>` — first key
- `klaviyo2._domainkey.<domain>` — second (rotation) key

Both must resolve to a TXT record beginning `v=DKIM1; k=rsa; p=...` with a non-empty public key.

If a Klaviyo account was re-onboarded or migrated, selectors may use `km1` / `km2` instead. Check both pairs before declaring DKIM missing.

**Common errors:**
- Only one of the two selectors resolves → key rotation broken; deliverability degrades over time
- TXT record contains `p=` empty value → key revoked; Klaviyo can't sign
- TXT record is split across multiple strings without proper concatenation → some resolvers fail

## DMARC

A valid DMARC record is a TXT on `_dmarc.<domain>` starting with `v=DMARC1`.

Required tags:
- `p=` — policy: `none` (monitor only), `quarantine` (spam folder), `reject` (bounce)
- `rua=` — aggregate reporting URI (mailto:dmarc@example.com); omit and you fly blind

Recommended tags:
- `pct=` — percentage of mail to apply policy to (start at 10, ramp up)
- `adkim=` and `aspf=` — alignment mode: `s` (strict, exact match) or `r` (relaxed, allow subdomains)
- `sp=` — subdomain policy

**Progression for a new domain:**
1. Install `v=DMARC1; p=none; rua=mailto:dmarc-reports@<domain>;` — 2 weeks of monitoring
2. Verify all sending sources in the rua reports are authenticated
3. Move to `p=quarantine; pct=10;` — 2 weeks
4. Ramp `pct` to 50, then 100
5. After clean reports at `p=quarantine pct=100`, move to `p=reject`

**Common errors:**
- `p=reject` set immediately on a domain with unauthenticated legitimate mail → all that mail bounces
- No `rua` → no visibility into what's failing
- Multiple DMARC records on the same `_dmarc` host → all ignored

## Quick decision tree

After running the dig commands, classify the domain:

- **GREEN**: SPF includes Klaviyo with `-all` or `~all`, both DKIM selectors resolve, DMARC has `p=quarantine` or `p=reject` with `rua=`
- **YELLOW**: One element missing or weak (e.g. DMARC `p=none` with `rua=`, SPF present but missing Klaviyo include even though Klaviyo sends, only one DKIM selector live)
- **RED**: SPF missing, or both DKIM selectors missing, or DMARC absent entirely

A RED status is the most likely root cause when seznam.cz / email.cz open rates are <10 %.

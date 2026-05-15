# Industry benchmarks reference (2025)

Sources: Klaviyo Industry Benchmark Report 2025, Omnisend Email Marketing Benchmarks 2025, Mailchimp Email Marketing Benchmarks 2025.

## Email open rates by industry (averages, all email)

| Industry | Open rate | CTR |
|---|---|---|
| Food & Beverage | 24-30% | 2-3% |
| Fashion & Apparel | 22-28% | 1.5-2.5% |
| Health & Beauty | 26-32% | 2-3% |
| Home & Garden | 24-30% | 2-3% |
| Pet | 28-34% | 2.5-3.5% |
| Electronics | 20-26% | 1.5-2.5% |
| Sports & Outdoor | 25-31% | 2-3% |

Flow-specific benchmarks should always be 10-20 percentage points above the all-email industry average for the same vertical, because flow recipients are pre-qualified by intent.

## Flow conversion rate ranges

| Flow type | Below avg | Average | Above avg |
|---|---|---|---|
| Welcome | <2% | 2-4% | 4%+ |
| Cart abandon | <1% | 1-3% | 3%+ |
| Checkout abandon | <2% | 2-4% | 4%+ |
| Browse abandon | <0.5% | 0.5-1.5% | 1.5%+ |
| Post-purchase (cross-sell) | <0.3% | 0.3-1% | 1%+ |
| Winback | <0.5% | 0.5-1% | 1%+ |
| Sunset | <0.05% | 0.05-0.1% | 0.1%+ |

## Revenue per recipient (RPR) heuristics

For ecommerce stores with AOV between 500-1500 CZK:

| Flow type | RPR target |
|---|---|
| Welcome | 30+ Kč |
| Cart abandon | 25+ Kč |
| Checkout abandon | 50+ Kč |
| Post-purchase | 5+ Kč |
| Browse abandon | 10+ Kč |
| Winback | 5+ Kč |
| Sunset | 0.50+ Kč |

If a flow is 3x or more below the RPR target, the flow has either an attribution gap or a content/offer problem — investigate.

## Czech market deliverability notes

- **seznam.cz** is often 25-40% of a Czech list. Sender authentication must include DKIM, DMARC (p=quarantine or p=reject), and SPF. Misconfigured authentication causes seznam.cz to silently drop or bulk-folder messages.
- **email.cz / atlas.cz / centrum.cz** share the same backend — same auth requirements.
- **gmail.com** is most forgiving but reacts to engagement. Flows with low open rates compound: gmail starts bulk-foldering, which further suppresses opens.
- **post.cz** has stricter spam filters; avoid promotional language in subject lines.

If a flow's open rate is anomalously low and the campaign program looks healthy, suspect deliverability and ask the user to check their authentication setup in Klaviyo (Account > Domains).

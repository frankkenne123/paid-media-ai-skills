---
name: account_auditor
description: "Ad Account Auditor — use when conducting a full audit of a Meta or Google Ads account (new client onboarding, quarterly review, problem diagnosis, or before a strategy change). Performs a structured deep-dive across account structure, targeting, creative, tracking, and performance history. Outputs a prioritized action list of what to fix, what to keep, and what to kill. Works with meta-ads-api, google-ads-api, ga4-integration, and shopify-integration."
user-invocable: true
---

# Ad Account Auditor

Complete structured audit of a Meta or Google Ads account. Use this for new client onboarding, quarterly reviews, diagnosing poor performance, or before making major strategy changes.

**Output:** A prioritized action plan — what to fix, what to keep, what to kill — with specific recommendations.

---

## AUDIT WORKFLOW

### Phase 1: Account Context (10 min)

Collect:
- Business type (DTC, SaaS, local, lead gen, etc.)
- Monthly ad budget
- Target ROAS / CPA / CPL
- Average Order Value (for eCommerce)
- Customer LTV (if known)
- Main offer + any current promotions
- Competitive landscape (top 3 competitors)
- Historical best-performing creative/campaign (ask the client)

---

### Phase 2: Account Structure Audit

**Meta:**
- Count of campaigns, ad sets, ads (total and active)
- Campaign objectives used — are they aligned with actual business goals?
- Budget distribution — top 3 campaigns by % of spend
- Any campaigns with <5 ads (under-tested)
- Any campaigns with >30 ads (over-fragmented, dilutes learning)

**Google Ads:**
- Campaign types (Search, Shopping, PMax, Display, YouTube) — appropriate mix?
- Ad group count per campaign — <3 = too broad, >20 = over-fragmented
- Keyword match types: broad/phrase/exact balance
- Search Impression Share by campaign
- Lost IS (budget) — how much money is being left on the table?

**Red flags:**
- Single-campaign account (no structure at all) — high risk
- 20+ campaigns with most <$100/month spend — fragmented, can't optimize
- No conversion-optimized campaign (all traffic or awareness) — no revenue signal

---

### Phase 3: Targeting Audit

**Meta:**
- Audiences in use: custom, lookalike, interest, broad
- Any interest stacks with 10+ interests (probably not focused)
- Lookalike percentages used (1%, 2%, 5%, 10%)
- Exclusions: are existing customers excluded from prospecting?
- Geo targeting: is it too broad (worldwide) or too narrow (single zip)?
- Age range: too narrow may limit scale; too broad may be inefficient

**Google Ads:**
- Keyword research depth — are long-tail keywords being used?
- Negative keywords: are there any? Enough?
- Search terms report — any obvious wasted spend (irrelevant queries converting clicks but not sales)?
- Audiences layered on Search — any remarketing lists observation?
- Location targeting (check "Presence or Interest" vs "Presence only")
- Device bid adjustments (mobile vs desktop)

**Red flags:**
- No exclusions for existing customers (wasting prospecting budget)
- No negative keywords on Search (wasting spend on irrelevant queries)
- Single audience used everywhere (no segmentation)
- Targeting includes clearly off-ICP countries/ages

---

### Phase 4: Creative Audit

**Meta:**
- Number of active ads
- Creative formats in use: single image, carousel, video, reels
- Top-performing creative (last 30d by ROAS) — what format and hook?
- Bottom-performing creative — still active? Should be paused.
- Creative age: any ads running >60 days? (probable fatigue)
- Hook rate (3-sec video view rate): top vs average
- CTR spread: are outliers being identified?
- UGC vs produced content ratio

**Google Ads:**
- Responsive Search Ad strength ratings (Good / Excellent?)
- Headlines and descriptions variety per ad group (aim for 15 headlines, 4 descriptions)
- Ad extensions coverage: sitelinks, callouts, structured snippets, price extensions
- Image assets for PMax / Shopping: enough high-quality product images?

**Red flags:**
- <5 active ads per ad set/ad group — not enough creative diversity
- No video in Meta account (missing highest-performing format for 2026)
- RSA strength "Poor" — Google penalizes in auctions
- No ad extensions enabled — leaves CTR improvement on the table
- 0 UGC creative — social proof is missing

---

### Phase 5: Tracking & Attribution Audit

**This is the biggest source of false ROAS numbers. Prioritize heavily.**

Check via `attribution-auditor` skill:
- Meta Pixel firing on all critical events (ViewContent, AddToCart, InitiateCheckout, Purchase)?
- Meta Conversions API (CAPI) deployed? (iOS 14+ losing 30%+ signal without it)
- Google Ads conversion tag firing on purchase?
- GA4 events aligned with Google Ads conversions?
- UTMs consistent across all ads? (Use `shopify-integration` to verify Shopify orders have UTM data)
- Google Merchant Center feed health (for Shopping)?
- iOS signal quality — Meta's "Events Quality Rating" in Events Manager

**Red flags:**
- Multiple conversion events double-counting
- Purchase pixel not firing on thank-you page
- No CAPI deployment (just client-side pixel)
- GA4 revenue ≠ Shopify revenue (>20% gap = tracking problem)
- No UTMs on ads = zero attribution in Shopify/GA4

---

### Phase 6: Performance History

Pull via `performance-analyst`:
- Last 30 days: spend, revenue, ROAS, trend direction
- Last 90 days: month-over-month comparison
- Best-ever month vs current month: what changed?
- Seasonality patterns (if 12+ months of data)
- Correlation between creative refreshes and performance spikes

**Red flags:**
- Steady decline for 60+ days with no creative refresh (fatigue)
- Performance dropped off a cliff at a specific date — find what changed (iOS update, creative swap, audience change)
- Revenue reported >GA4 reported >Shopify actual — tracking inflation

---

### Phase 7: Output — Audit Report

Deliver a structured report:

```
# Ad Account Audit — [Client Name]
## [Platform: Meta / Google Ads]
## Audit Date: [Date]

---

## Overall Grade: [A / B / C / D / F]

**Why:** [2-3 sentence summary]

---

## 🔴 CRITICAL FIXES (do this week)
1. [Issue] — [Specific fix] — Impact: [Dollar or % gain]
2. [Issue] — [Specific fix] — Impact: [Dollar or % gain]

## 🟡 IMPROVEMENTS (do this month)
1. [Issue] — [Fix] — Impact: [Estimated gain]
2. [Issue] — [Fix] — Impact: [Estimated gain]

## 🟢 KEEP DOING
- [Thing that's working well]

## 💀 KILL
- [Campaign / Ad Set / Ad to pause immediately] — reason

## 🧪 TEST NEXT
1. [Experiment idea based on findings]
2. [Experiment idea]

## 📊 EXPECTED OUTCOME (if all changes implemented)
- ROAS improvement: [X%]
- Spend efficiency: [% reduction in wasted spend]
- 90-day revenue impact: [$X estimate]
```

---

## AUDIT SCORE RUBRIC

| Dimension | A (90-100) | B (80-89) | C (70-79) | D (60-69) | F (<60) |
|-----------|-----------|-----------|-----------|-----------|---------|
| **Structure** | Clean, logical, funnel-aligned | Mostly good, minor issues | OK but some messy areas | Fragmented or overly simple | Chaos, no strategy |
| **Targeting** | Clear ICP, layered, smart exclusions | Good but could tighten | Basic targeting works | Broad, no segmentation | No strategy, wasting spend |
| **Creative** | Fresh, diverse, winning hooks ID'd | Strong variety | Adequate, some old | Limited variety, stale | Dead creative still running |
| **Tracking** | CAPI + pixel + GA4 aligned | Good pixel, GA4 setup | Client-side pixel only | Missing events | Broken tracking |
| **Performance** | Exceeding targets consistently | Meeting targets | Hitting floor | Below target | Unprofitable |

**Overall grade** = weighted average (Tracking = 2x weight — if tracking is broken, nothing else matters).

---

## NOTES
- Always audit tracking FIRST — false ROAS hides real problems
- Never make >3 structural changes at once — can't attribute what worked
- For new clients, do this audit before week 1 — it sets the plan for first 90 days
- Follow up 30 days after implementing changes — measure impact

---
name: attribution_auditor
description: "Attribution Auditor — use when auditing tracking health, diagnosing ROAS discrepancies, checking pixel firing, validating UTMs, or investigating why platform-reported revenue doesn't match Shopify. This is the most important skill for new client onboarding — if tracking is broken, every other metric is wrong. Works with meta-ads-api, ga4-integration, and shopify-integration."
user-invocable: true
---

# Attribution Auditor

Diagnose and fix tracking, attribution, and conversion measurement across the paid media stack. The single highest-leverage skill in paid media — because if tracking is broken, every optimization decision is based on false data.

---

## THE ATTRIBUTION REALITY

Three systems report different numbers for the same activity:

| System | What It Sees | When It's Wrong |
|--------|--------------|-----------------|
| **Meta Pixel + CAPI** | Clicks + conversions attributed to Meta ads | iOS 14+ losses, view-through over-counting, duplicate events |
| **Google Ads Conversions** | Clicks + conversions attributed to Google | Cross-device, GCLID drops, consent mode |
| **GA4** | All website sessions + events (with consent) | Consent-mode data loss, sampling, event setup errors |
| **Shopify** | Every actual order, the source of truth | Attribution only if UTMs are on the landing URL |

**Your job as auditor:** Find the gaps and diagnose why they exist.

**Target health:** Meta + Google reported revenue should be within 15–20% of Shopify revenue for the same customers. Larger gaps = tracking problems.

---

## AUDIT WORKFLOW

### Phase 1: Pixel & Tag Health Check

#### Meta Pixel
Use [Meta Events Manager](https://business.facebook.com/events_manager) to check:

**Standard events firing correctly?**
- `PageView` — fires on every page
- `ViewContent` — fires on product pages
- `AddToCart` — fires when item added
- `InitiateCheckout` — fires on checkout start
- `Purchase` — fires on thank-you page (this is the critical one)

**Event Match Quality (EMQ) score:** Should be 6+/10. Lower = missing parameters (email, phone, fbc, fbp).

**CAPI (Conversions API) deployed?**
- No CAPI = losing 30%+ of iOS conversion signal
- Check if events are marked "Pixel + Server" (good) or "Pixel only" (bad)
- CAPI is table-stakes in 2026 — if a client doesn't have it, that's finding #1

**Duplicate events?**
- Use "Overview" tab in Events Manager → look for spikes
- Same event firing twice from pixel + Shopify integration = inflated conversion count

#### Google Ads Conversion Tag

In [Google Ads → Tools → Conversions](https://ads.google.com):
- Each conversion action should show "Recording conversions" status
- Last conversion received timestamp should be recent (within hours)
- Verify tag firing with Google Tag Assistant

**Common breaks:**
- Conversion tag on wrong page (not the thank-you page)
- GA4 and Google Ads conversions double-counting
- Enhanced conversions not enabled (major 2026 signal source)

#### GA4 Events

In GA4 → Admin → Events:
- `purchase` event firing with revenue?
- `add_to_cart`, `begin_checkout`, `view_item` firing?
- Any anomalous drops in event count?

Use GA4 DebugView for real-time testing.

---

### Phase 2: UTM Tracking Audit

**Critical check:** Open the client's active Meta ads (via Ad Library or Ads Manager). Click the first ad's landing URL.

Does the URL have UTMs?
- ✅ Good: `store.com/product?utm_source=facebook&utm_medium=cpc&utm_campaign=fall-2026`
- ❌ Bad: `store.com/product`

Without UTMs:
- Shopify can't attribute the order to paid media
- GA4 shows "direct" or "referral" traffic instead of `facebook / cpc`
- You can't reconcile platform ROAS vs real revenue

**Meta UTM convention:**
```
?utm_source=facebook&utm_medium=cpc&utm_campaign={{campaign.name}}&utm_content={{ad.name}}&utm_term={{adset.name}}
```

**Google Ads:**
- Auto-tagging should be ON (adds GCLID automatically)
- No manual UTMs needed if auto-tagging is on

**Verify in Shopify:** Use `shopify-integration` skill to pull recent orders. Check `landing_site` field — does it contain `utm_source=facebook`?
- If yes for >80% of Meta-attributed orders → UTMs working
- If no → UTMs missing on the actual ads

---

### Phase 3: Cross-System Reconciliation

Pull the same 30-day window from all three systems:

```
## Revenue Reconciliation — [Client Name]
## Period: [Date Range]

| System | Revenue Reported | Orders | AOV |
|--------|------------------|--------|-----|
| Meta (platform) | $X | Y | $Z |
| Google Ads (platform) | $X | Y | $Z |
| GA4 (filtered to utm_medium=cpc) | $X | Y | $Z |
| Shopify (filtered to utm_source=facebook or google) | $X | Y | $Z |

**Meta-reported vs Shopify:** [% gap]
**Google-reported vs Shopify:** [% gap]
**GA4 vs Shopify:** [% gap]
```

**Interpret the gaps:**

| Gap | Likely Cause |
|-----|--------------|
| Meta reports 30%+ MORE than Shopify | View-through attribution, pixel double-firing, or iOS over-claiming |
| Meta reports 30%+ LESS than Shopify | Pixel/CAPI issues, audience signal loss |
| GA4 reports LESS than Shopify | Consent mode loss, event setup errors, sampling |
| GA4 reports MORE than Shopify | Event firing on non-purchase pages (setup error) |
| Google reports MORE than Shopify | GCLID / attribution window issues, double-counting with GA4 |

---

### Phase 4: iOS Signal Quality (Meta-Specific)

For Meta specifically, check **Events Quality Rating** in Events Manager:
- **Poor:** Losing massive iOS signal — CAPI urgently needed
- **Good:** CAPI is deployed and sending matching hashed customer data
- **Great:** CAPI + Advanced Matching parameters (email, phone) with high match rates

**Aggregated Event Measurement (AEM):**
- Each domain verified in Business Settings?
- 8 conversion events prioritized (Meta limit per domain post-iOS 14)?
- Purchase is priority #1 (should be obvious, but check)

---

### Phase 5: Landing Page Load & Tag Health

For each major landing page:
1. Load page, open browser DevTools
2. Check Network tab for pixel/tag requests:
   - `connect.facebook.net/en_US/fbevents.js` (Meta pixel)
   - `googletagmanager.com/gtag/js` (Google Tag)
   - `www.google-analytics.com/g/collect` (GA4)
3. Run through full purchase flow — verify events fire at each step

**Page speed check:**
- If page load >5 seconds, tags may not fire reliably
- Mobile speed matters most — test on 4G throttling

---

## AUDIT REPORT OUTPUT

```
# Attribution & Tracking Audit — [Client Name]
## Audit Date: [Date]

---

## OVERALL GRADE: [A / B / C / D / F]

[1-2 sentence summary of tracking health]

---

## 🔴 CRITICAL FIXES (blocking accurate data)

1. **[Issue]** — [Specific fix] — Impact: "Without this, Meta ROAS is overstated by ~25%"
2. **[Issue]** — [Fix] — Impact: ...

## 🟡 IMPROVEMENTS (signal quality gains)

1. **[Issue]** — [Fix] — Impact: "Will improve Meta EMQ from 5 to 7+"
2. **[Issue]** — [Fix]

## 🟢 WORKING WELL
- [What's configured correctly]

---

## RECONCILIATION TABLE
[Revenue comparison across systems — copy from Phase 3]

**Verdict:** [Attribution is / is not trustworthy for optimization decisions]

---

## EVENT QUALITY SCORES
- Meta EMQ: [X]/10
- CAPI: [Deployed / Not deployed]
- GA4 Events: [X] configured, [Y] firing cleanly
- Google Ads Conversions: [Enhanced on/off]

---

## UTM COMPLIANCE
- % of Meta ads with UTMs: [X%]
- % of recent Shopify orders with UTM attribution: [X%]
- Auto-tagging on Google Ads: [Yes/No]

---

## IMPLEMENTATION PRIORITY
1. [Fix 1] — Owner: [Dev / Agency] — Timeline: [Week]
2. [Fix 2] — Owner: ...
```

---

## WORKFLOW RULES

1. **Run this audit FIRST for any new client** — before running any performance analysis. Bad data = bad decisions.
2. **Re-audit quarterly** — tracking breaks over time. Devs push changes, platforms update, things drift.
3. **When ROAS changes significantly** — before assuming it's a campaign issue, check if tracking changed.
4. **After platform updates** — iOS releases, Meta tool updates, Google changes often break tracking silently.

---

## COMMON FINDINGS (ranked by frequency)

1. **No CAPI** — 60% of new clients. Deploy this first for Meta clients.
2. **Missing or inconsistent UTMs** — 40% of clients. Standardize immediately.
3. **Double-counting conversions** — GA4 + Pixel firing purchase twice. 25%.
4. **Purchase pixel on wrong page** — 20%. Usually cart page instead of thank-you page.
5. **No Enhanced Conversions on Google** — 50%. Easy fix, major signal boost.
6. **Auto-tagging off on Google** — 15%. Flip the switch, wait 24 hours.
7. **GA4 not configured for eCommerce events** — 30%. Need `purchase` event with `value` and `items`.

---

## NOTES
- For deeper pixel/tag debugging, Meta Pixel Helper and Google Tag Assistant browser extensions are essential
- CAPI implementation usually requires dev work (Gateway, Stape, or direct API) — scope accordingly
- Never touch the client's GTM container without explicit approval — one bad change can break everything
- For Shopify clients, Shopify's native Facebook/Google apps handle most pixel setup automatically but CAPI still needs to be deployed

---
name: shopify_integration
description: "Shopify Admin API Integration — use when pulling eCommerce revenue data, analyzing customer LTV, checking ad attribution against actual purchases, identifying top products, or reconciling platform-reported ROAS with real Shopify revenue. Requires SHOPIFY_SHOP_URL and SHOPIFY_ADMIN_API_TOKEN in .env. Critical for validating paid media performance against source-of-truth revenue."
user-invocable: true
---

# Shopify Admin API Integration

Pull actual eCommerce revenue data from Shopify to validate paid media performance. Meta and Google both report conversions — but Shopify is the source of truth. Use this skill to reconcile platform-reported ROAS with real revenue, analyze customer LTV, and identify high-LTV cohorts for lookalike audience building.

---

## SETUP

Add to your `.env` (one set per client Shopify store):
```
SHOPIFY_SHOP_URL=your-store.myshopify.com
SHOPIFY_ADMIN_API_TOKEN=shpat_your_admin_api_token
SHOPIFY_API_VERSION=2024-10
```

**Where to get these:**
1. Shopify Admin → Settings → Apps and sales channels → Develop apps → Create app
2. Configure Admin API scopes: `read_orders`, `read_customers`, `read_products`, `read_analytics`, `read_draft_orders`
3. Install the app → copy the Admin API access token (starts with `shpat_`)

**API Base:** `https://{shop}.myshopify.com/admin/api/2024-10`

All calls:
```
X-Shopify-Access-Token: YOUR_ADMIN_API_TOKEN
```

---

## CORE OPERATIONS

### 1. Get orders in a date range
```bash
curl "https://YOUR_SHOP.myshopify.com/admin/api/2024-10/orders.json?status=any&created_at_min=2026-01-01T00:00:00-05:00&created_at_max=2026-01-08T00:00:00-05:00&limit=250" \
  -H "X-Shopify-Access-Token: YOUR_TOKEN"
```

Key fields: `id`, `total_price`, `subtotal_price`, `customer.id`, `line_items`, `source_name`, `landing_site`, `referring_site`, `note_attributes`

### 2. Get orders by UTM (paid attribution)
Shopify stores UTMs in `note_attributes` or `landing_site`. Filter orders where `landing_site` contains `utm_source=facebook` or `utm_source=google`:

```bash
# Then filter in-code after fetching orders
# Look for utm_source=facebook, utm_source=google, utm_medium=cpc, etc.
```

### 3. Customer data
```bash
curl "https://YOUR_SHOP.myshopify.com/admin/api/2024-10/customers/CUSTOMER_ID.json" \
  -H "X-Shopify-Access-Token: YOUR_TOKEN"
```

Key fields: `orders_count`, `total_spent`, `created_at`, `last_order_id`

### 4. Get all products
```bash
curl "https://YOUR_SHOP.myshopify.com/admin/api/2024-10/products.json?limit=250" \
  -H "X-Shopify-Access-Token: YOUR_TOKEN"
```

### 5. Analytics: Sales by source
```bash
curl "https://YOUR_SHOP.myshopify.com/admin/api/2024-10/reports.json" \
  -H "X-Shopify-Access-Token: YOUR_TOKEN"
```
> Reports API is Shopify Plus only. For most stores, query orders + aggregate in code.

---

## KEY USE CASES FOR PAID MEDIA

### 1. Reconcile Platform ROAS vs Real ROAS

**Problem:** Meta says ROAS is 4.0x, but actual Shopify revenue for Meta-attributed orders is only 2.8x.

**Process:**
1. Get all Shopify orders for the last 30 days
2. Filter orders where `landing_site` contains `utm_source=facebook` (or `utm_source=fb`)
3. Sum `total_price` for those orders = **Real Meta revenue**
4. Pull Meta ad spend last 30 days via `meta_ads_api` skill
5. **Real ROAS = Real Meta revenue / Meta ad spend**
6. Compare to Meta's reported ROAS — any gap >20% indicates attribution issues (pixel, iOS, view-through counting)

Do the same for Google: filter `utm_source=google` + `utm_medium=cpc`.

### 2. Customer LTV Analysis

**Goal:** Find high-LTV cohorts to build better lookalike audiences.

**Process:**
1. Pull all customers
2. Sort by `total_spent`
3. Top 10% = seed audience for lookalikes
4. Export emails → upload to Meta Custom Audience → build Lookalike
5. Use `meta_ads_api` skill to create the custom audience from this list

### 3. Top-Selling Products (feed prioritization for PMax / Shopping)

1. Aggregate `line_items` across orders last 90 days
2. Sum quantity and revenue per `product_id`
3. Top 10 products by revenue = priority for Shopping campaigns and PMax asset groups
4. Bottom 50% of products = candidates to exclude from feed (low velocity = wasted crawl budget)

### 4. First-Order vs Repeat Customer Analysis

Split orders into:
- **First-time buyers:** Customer's `orders_count` was 1 at time of order
- **Repeat buyers:** `orders_count` > 1

**Key insight:** Paid media optimizes for first purchase. If repeat revenue is 50%+ of total, the real blended CAC payback is faster than it looks on platform data.

### 5. Subscription / Recurring Revenue Breakdown
If using Recharge, Bold, or similar — filter `source_name` or `tags` to separate subscriptions from one-time orders. Use for LTV calculations.

---

## UTM TRACKING CONVENTION (IMPORTANT)

For Shopify attribution to work, every paid ad's URL must include UTMs. Standard convention:

**Meta:**
```
?utm_source=facebook&utm_medium=cpc&utm_campaign={{campaign.name}}&utm_content={{ad.name}}
```

**Google Ads:**
```
?utm_source=google&utm_medium=cpc&utm_campaign={campaignid}&utm_content={adgroupid}
```
(Use auto-tagging for Google — GCLID handles it automatically if configured)

Without UTMs, Shopify attribution breaks and you can't reconcile platform ROAS vs real revenue.

---

## RATE LIMITS

Shopify Admin API: **2 requests/second for Basic plan** (bucket of 40, refills at 2/sec).

For large order pulls (>1000 orders), use **cursor-based pagination**:
```bash
curl "https://YOUR_SHOP.myshopify.com/admin/api/2024-10/orders.json?limit=250&status=any" \
  -H "X-Shopify-Access-Token: YOUR_TOKEN" -I
```
Check `Link` header for `rel="next"` and follow pagination.

---

## WORKFLOW RULES

1. **Never modify orders or customers** via this skill — read-only operations only
2. **Respect rate limits** — back off when you hit them, don't retry immediately
3. **UTMs are everything** — if a client's ads aren't UTM-tagged, attribution is broken. Flag this as a top priority fix.
4. **Cross-reference** — always compare Shopify revenue vs platform-reported revenue to catch attribution drift

---

## COMMON DIAGNOSIS PROMPTS

- **"What's our actual Meta ROAS?"** → Orders last 30d filtered by utm_source=facebook, sum total_price, divide by Meta spend
- **"Who are our best customers?"** → Top customers by total_spent, last 90 days
- **"Which products should we feature in PMax?"** → Top 10 products by revenue last 90 days
- **"Is our attribution working?"** → Compare utm_source breakdown in Shopify vs platform-reported conversions

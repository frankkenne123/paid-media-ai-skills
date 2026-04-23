---
name: google_ads_api
description: "Google Ads API Integration — use when managing Google Ads campaigns (Search, Shopping, Performance Max, YouTube), pulling performance insights, creating/editing campaigns/ad groups/ads, managing keywords, adjusting bids, or any direct Google Ads operation. Requires OAuth credentials in .env. Handles MCC (manager account) hierarchies for agency setups."
user-invocable: true
---

# Google Ads API Integration

Direct API integration with Google Ads for campaign management, insights, keyword management, and bid adjustments. Supports MCC (Manager) accounts for agencies managing multiple clients.

---

## SETUP

Add to your `.env`:
```
GOOGLE_ADS_DEVELOPER_TOKEN=your_developer_token
GOOGLE_ADS_CLIENT_ID=your_oauth_client_id
GOOGLE_ADS_CLIENT_SECRET=your_oauth_client_secret
GOOGLE_ADS_REFRESH_TOKEN=your_oauth_refresh_token
GOOGLE_ADS_LOGIN_CUSTOMER_ID=your_mcc_account_id  # e.g., 1234567890 (no dashes)
```

**Where to get these:**
1. Developer token: [Google Ads API Center](https://ads.google.com/aw/apicenter) (apply for Standard Access for production)
2. OAuth: Create project in [Google Cloud Console](https://console.cloud.google.com) → enable Google Ads API → OAuth 2.0 client
3. Refresh token: Run OAuth flow once to get refresh token (it doesn't expire)
4. MCC Customer ID: Your manager account number without dashes

**API:** Use the official [google-ads-python](https://github.com/googleads/google-ads-python) library — it handles auth + versioning.

---

## ACCOUNT HIERARCHY (MCC)

```
MCC Manager Account
├── Client Account 1 (customer_id: 1234567890)
│   └── Campaigns → Ad Groups → Ads + Keywords
├── Client Account 2 (customer_id: 9876543210)
│   └── Campaigns → Ad Groups → Ads + Keywords
```

Always specify which client account (`customer_id`) you're operating on.

---

## CAMPAIGN TYPES (how to identify them)

| Type | When to Use | Campaign Subtype |
|------|-------------|------------------|
| **Search** | Keyword-intent traffic | `SEARCH` |
| **Performance Max** | Goal-based, all channels | `PERFORMANCE_MAX` |
| **Shopping** | eCommerce product feeds | `SHOPPING` (Standard or PMax Shopping) |
| **Display** | Visual placement network | `DISPLAY` |
| **Video** | YouTube ads | `VIDEO` |
| **Demand Gen** | YouTube + Discover + Gmail | `DEMAND_GEN` |

For eCommerce clients, default recommendation: **PMax for product feed + Search for branded keywords**.

---

## CORE OPERATIONS (Python SDK examples)

### 1. List all accessible client accounts under MCC
```python
from google.ads.googleads.client import GoogleAdsClient

client = GoogleAdsClient.load_from_env()
customer_service = client.get_service("CustomerService")
accessible = customer_service.list_accessible_customers()
for resource_name in accessible.resource_names:
    print(resource_name)  # "customers/1234567890"
```

### 2. Get account-level insights (last 7 days)
```python
ga_service = client.get_service("GoogleAdsService")
query = """
    SELECT
        customer.id,
        customer.descriptive_name,
        metrics.cost_micros,
        metrics.impressions,
        metrics.clicks,
        metrics.ctr,
        metrics.average_cpc,
        metrics.conversions,
        metrics.conversions_value
    FROM customer
    WHERE segments.date DURING LAST_7_DAYS
"""
response = ga_service.search(customer_id="1234567890", query=query)
for row in response:
    print(row)
```
> **Cost is in micros** (1,000,000 micros = $1). Divide by 1,000,000.

### 3. List campaigns with performance
```python
query = """
    SELECT
        campaign.id,
        campaign.name,
        campaign.status,
        campaign.advertising_channel_type,
        metrics.cost_micros,
        metrics.conversions,
        metrics.conversions_value,
        metrics.ctr,
        metrics.average_cpc
    FROM campaign
    WHERE segments.date DURING LAST_30_DAYS
    ORDER BY metrics.cost_micros DESC
"""
```

### 4. Pause / Enable a campaign
```python
campaign_service = client.get_service("CampaignService")
operation = client.get_type("CampaignOperation")
campaign = operation.update
campaign.resource_name = f"customers/1234567890/campaigns/CAMPAIGN_ID"
campaign.status = client.enums.CampaignStatusEnum.PAUSED  # or ENABLED
client.copy_from(operation.update_mask, client.get_type("FieldMask")(paths=["status"]))
campaign_service.mutate_campaigns(customer_id="1234567890", operations=[operation])
```

### 5. Update daily budget
```python
budget_service = client.get_service("CampaignBudgetService")
operation = client.get_type("CampaignBudgetOperation")
budget = operation.update
budget.resource_name = f"customers/1234567890/campaignBudgets/BUDGET_ID"
budget.amount_micros = 50_000_000  # $50/day
client.copy_from(operation.update_mask, client.get_type("FieldMask")(paths=["amount_micros"]))
budget_service.mutate_campaign_budgets(customer_id="1234567890", operations=[operation])
```

### 6. Search Terms Report (find wasted spend)
```python
query = """
    SELECT
        search_term_view.search_term,
        metrics.cost_micros,
        metrics.clicks,
        metrics.conversions
    FROM search_term_view
    WHERE segments.date DURING LAST_30_DAYS
    ORDER BY metrics.cost_micros DESC
    LIMIT 100
"""
```
Run this for every Search campaign monthly — flag high-spend, zero-conversion search terms for negative keyword addition.

### 7. Ad Group Performance
```python
query = """
    SELECT
        ad_group.id,
        ad_group.name,
        ad_group.status,
        metrics.cost_micros,
        metrics.conversions,
        metrics.ctr
    FROM ad_group
    WHERE segments.date DURING LAST_14_DAYS
"""
```

### 8. Performance Max Asset Group Performance
```python
query = """
    SELECT
        asset_group.id,
        asset_group.name,
        asset_group_listing_group_filter.path,
        metrics.cost_micros,
        metrics.conversions_value
    FROM asset_group
    WHERE campaign.advertising_channel_type = 'PERFORMANCE_MAX'
    AND segments.date DURING LAST_30_DAYS
"""
```

---

## KEY METRICS (Google Ads field names)

| Metric | GAQL Field | Conversion |
|--------|-----------|------------|
| Cost | `metrics.cost_micros` | Divide by 1,000,000 for dollars |
| Impressions | `metrics.impressions` | Raw count |
| Clicks | `metrics.clicks` | Raw count |
| CTR | `metrics.ctr` | Decimal (0.03 = 3%) |
| CPC | `metrics.average_cpc` | Micros — divide by 1,000,000 |
| Conversions | `metrics.conversions` | Raw count |
| Conversion Value | `metrics.conversions_value` | Dollars |
| ROAS | `metrics.conversions_value / metrics.cost_micros * 1_000_000` | Calculated |
| Search Impression Share | `metrics.search_impression_share` | % of eligible impressions won |
| Search Lost IS (budget) | `metrics.search_budget_lost_impression_share` | % lost due to low budget |

---

## WORKFLOW RULES

1. **NEVER auto-activate campaigns** — always create paused, require approval
2. **Budget changes >20%** require confirmation
3. **Specify `customer_id` explicitly** for every operation — don't rely on defaults
4. **Rate limits** — Google Ads API has per-hour quotas. Use batch operations when possible.
5. **Attribution** — Default is last-click. Use data-driven attribution where available.
6. **Cost values** — always in micros in GAQL responses. Multiply budgets by 1,000,000 when setting.

---

## COMMON DIAGNOSIS PROMPTS

- **"How is [Client] Google doing last 7 days?"** → Account insights with LAST_7_DAYS, calculate ROAS = conv_value / cost
- **"What campaigns should we cut?"** → Campaign report last 14 days, flag spend >$500 with ROAS <1.5x
- **"Find wasted spend"** → Search terms report, flag high-cost zero-conversion terms as negative keyword candidates
- **"Is our PMax healthy?"** → Asset group report + campaign listing group performance
- **"What's our Search Impression Share?"** → Campaign report with `search_impression_share` and `search_budget_lost_impression_share`

---

## NOTES
- Use the [google-ads-python SDK](https://github.com/googleads/google-ads-python) — it handles auth, versioning, retries
- GAQL (Google Ads Query Language) is SQL-like — you write queries, API returns structured data
- Reports have up to 24-hour delay — don't rely on "today" data before end of day
- For MCC-wide reporting, run the same query against each customer_id and aggregate

---
name: ga4_integration
description: "Google Analytics 4 Integration — use when pulling website traffic data, conversion tracking, funnel analysis, traffic source breakdowns, landing page performance, or any GA4 reporting. Essential for understanding what paid media traffic actually does on the site. Requires GA4 service account credentials in .env."
user-invocable: true
---

# Google Analytics 4 Integration

Pull website behavior data from GA4 to understand what paid media traffic is actually doing on the site. Bridges the gap between "they clicked the ad" (platform data) and "they did something valuable" (GA4 / Shopify data).

---

## SETUP

Add to your `.env`:
```
GA4_PROPERTY_ID=properties/123456789
GA4_SERVICE_ACCOUNT_KEY_PATH=/path/to/ga4-service-account.json
```

**Where to get these:**
1. Create a service account in [Google Cloud Console](https://console.cloud.google.com) → IAM → Service Accounts
2. Generate a JSON key → save to a secure location
3. In GA4 Admin → Property Access Management → add the service account email as Viewer
4. Get the property ID from GA4 Admin → Property Settings (format: `properties/123456789`)

**SDK:** Use [google-analytics-data](https://pypi.org/project/google-analytics-data/) — `pip install google-analytics-data`

---

## CORE OPERATIONS

### 1. Traffic by Source/Medium last 7 days
```python
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, RunReportRequest

client = BetaAnalyticsDataClient()
request = RunReportRequest(
    property="properties/123456789",
    dimensions=[Dimension(name="sessionSource"), Dimension(name="sessionMedium")],
    metrics=[
        Metric(name="sessions"),
        Metric(name="engagedSessions"),
        Metric(name="conversions"),
        Metric(name="totalRevenue"),
    ],
    date_ranges=[DateRange(start_date="7daysAgo", end_date="today")],
)
response = client.run_report(request)
for row in response.rows:
    print(row)
```

### 2. Landing page performance
```python
request = RunReportRequest(
    property="properties/123456789",
    dimensions=[Dimension(name="landingPage")],
    metrics=[
        Metric(name="sessions"),
        Metric(name="engagementRate"),
        Metric(name="conversions"),
        Metric(name="totalRevenue"),
    ],
    date_ranges=[DateRange(start_date="30daysAgo", end_date="today")],
    order_bys=[{"metric": {"metric_name": "sessions"}, "desc": True}],
    limit=50,
)
```

### 3. Paid media attribution (sessions from utm_source=facebook or google)
```python
request = RunReportRequest(
    property="properties/123456789",
    dimensions=[
        Dimension(name="sessionSource"),
        Dimension(name="sessionMedium"),
        Dimension(name="sessionCampaignName"),
    ],
    metrics=[
        Metric(name="sessions"),
        Metric(name="conversions"),
        Metric(name="totalRevenue"),
        Metric(name="averagePurchaseRevenue"),
    ],
    dimension_filter={
        "filter": {
            "field_name": "sessionMedium",
            "string_filter": {"match_type": "EXACT", "value": "cpc"}
        }
    },
    date_ranges=[DateRange(start_date="30daysAgo", end_date="today")],
)
```

### 4. Event tracking (custom conversion events)
```python
request = RunReportRequest(
    property="properties/123456789",
    dimensions=[Dimension(name="eventName")],
    metrics=[
        Metric(name="eventCount"),
        Metric(name="totalUsers"),
    ],
    date_ranges=[DateRange(start_date="7daysAgo", end_date="today")],
    order_bys=[{"metric": {"metric_name": "eventCount"}, "desc": True}],
)
```

### 5. Funnel / Path Exploration
Use the [Funnel Report API](https://developers.google.com/analytics/devguides/reporting/data/v1/advanced#funnels) for multi-step conversion analysis — view_item → add_to_cart → begin_checkout → purchase.

### 6. Device breakdown
```python
dimensions=[Dimension(name="deviceCategory")]  # mobile, desktop, tablet
```

---

## KEY METRICS

| Metric | Field | Meaning |
|--------|-------|---------|
| Sessions | `sessions` | Visit count |
| Engaged Sessions | `engagedSessions` | Sessions with >10 sec OR conversion OR 2+ pageviews |
| Engagement Rate | `engagementRate` | Engaged / total sessions |
| Conversions | `conversions` | Goal events fired |
| Revenue | `totalRevenue` | Total order value from GA4 events |
| Bounce Rate | `bounceRate` | Non-engaged sessions % |
| Pages/Session | `screenPageViewsPerSession` | Avg pages viewed |
| Avg Session Duration | `averageSessionDuration` | In seconds |

---

## KEY DIMENSIONS

| Dimension | Values |
|-----------|--------|
| `sessionSource` | google, facebook, direct, organic, etc. |
| `sessionMedium` | cpc, organic, referral, email, etc. |
| `sessionCampaignName` | UTM campaign name |
| `landingPage` | First page of the session |
| `deviceCategory` | mobile, desktop, tablet |
| `country` | Country from IP |
| `eventName` | Custom event name (purchase, add_to_cart, etc.) |

---

## KEY USE CASES FOR PAID MEDIA

### 1. Landing Page Performance for Paid Traffic

**Goal:** Find which landing pages convert best for paid traffic.

Query: Landing pages last 30 days, filter medium=cpc, sort by engagement rate and conversions.

If CTR on ads is high but engagement on landing page is low → landing page is the problem, not the ad.

### 2. Bounce Rate by Campaign

Cross-reference campaign name with bounce rate. High bounce (>70%) on a campaign = audience mismatch or broken landing page.

### 3. Device Performance

Compare mobile vs desktop conversion rates. If mobile is 80% of traffic but 30% of revenue, mobile UX needs fixing before scaling ad spend.

### 4. GA4 vs Platform Discrepancies

**Classic problem:** Meta reports 100 purchases, GA4 reports 65, Shopify reports 70.

This means:
- Meta pixel is over-counting (view-through attribution or double-firing)
- GA4 might be under-counting (missing events or consent issues)
- Shopify is the source of truth for actual revenue

Flag whenever Meta-reported purchases are >30% higher than GA4 for the same window.

### 5. New vs Returning User Performance for Paid Traffic

```python
dimensions=[Dimension(name="newVsReturning")]
```

If paid media is converting >80% returning users, you're reaching existing customers (retargeting), not acquiring new ones. Re-balance toward prospecting.

---

## COMMON DIAGNOSIS PROMPTS

- **"What's our top-performing landing page for Meta?"** → Filter sessionSource=facebook, sort landing pages by conversions
- **"Why is our ROAS dropping?"** → Check engagement rate by landing page + device breakdown over time
- **"Are we getting quality traffic from [Campaign]?"** → Filter by sessionCampaignName, check engagementRate and conversions
- **"Pixel vs GA4 discrepancy?"** → Pull GA4 purchases for a date range, compare against Meta/Google reported purchases
- **"Is our site mobile-ready?"** → Device breakdown — compare mobile vs desktop conversion rate

---

## NOTES
- GA4 reports have ~24-48 hour data processing delay for full accuracy
- GA4 samples data when queries are complex — use smaller date ranges for high-volume sites
- Custom events must be set up in GA4 first (this skill queries existing events, doesn't create them)
- Consent Mode v2 may reduce reported data — this is normal in EU traffic

---
name: performance_analyst
description: "Ad Performance Analyst — use when the user asks about ad performance, campaign data, spend, ROAS, conversions, impressions, clicks, or any advertising metrics for Google Ads or Meta (Facebook/Instagram) Ads. Reads pre-fetched JSON data files from the ad-data/ directory in your workspace."
user-invocable: true
---

# Ad Performance Analyst

Analyze Google Ads and Meta (Facebook/Instagram) ad performance for all managed client accounts. Data is pre-fetched and stored as JSON files in your workspace's `ad-data/` directory.

---

## SETUP

This skill reads pre-fetched ad data files — it does not call ad platform APIs directly. You need a data-fetching script that pulls from Google Ads API and Meta Marketing API and saves results as JSON.

**Data files location:** `ad-data/` directory in your workspace

**Required files:**
```
ad-data/google-ads-summary-yesterday.json
ad-data/google-ads-summary-last_7_days.json
ad-data/google-ads-summary-last_30_days.json
ad-data/google-ads-campaigns-yesterday.json
ad-data/google-ads-campaigns-last_7_days.json
ad-data/google-ads-campaigns-last_30_days.json
ad-data/meta-ads-summary-yesterday.json
ad-data/meta-ads-summary-last_7d.json
ad-data/meta-ads-summary-last_30d.json
ad-data/meta-ads-campaigns-yesterday.json
ad-data/meta-ads-campaigns-last_7d.json
ad-data/meta-ads-campaigns-last_30d.json
```

Each file contains a `fetched_at` timestamp showing when data was pulled.

---

## GOOGLE ADS DATA FORMAT

### Summary files (`google-ads-summary-*.json`)
```json
{
  "fetched_at": "2026-01-01T10:00:00Z",
  "date_range": "LAST_7_DAYS",
  "accounts": [
    {
      "customer_id": "YOUR_CUSTOMER_ID",
      "account_name": "Client Name",
      "spend": 5000.00,
      "impressions": 400000,
      "clicks": 8000,
      "conversions": 100.0,
      "conversion_value": 15000.00,
      "roas": 3.00,
      "cpc": 0.63
    }
  ]
}
```

### Campaign files (`google-ads-campaigns-*.json`)
```json
{
  "campaigns": [
    {
      "customer_id": "YOUR_CUSTOMER_ID",
      "account_name": "Client Name",
      "campaign": "Campaign Name",
      "status": "ENABLED",
      "type": "PERFORMANCE_MAX",
      "spend": 2500.00,
      "impressions": 200000,
      "clicks": 5000,
      "conversions": 80.0,
      "conversion_value": 12000.00,
      "roas": 4.80
    }
  ]
}
```

---

## META ADS DATA FORMAT

### Summary files (`meta-ads-summary-*.json`)
```json
{
  "fetched_at": "2026-01-01T10:00:00Z",
  "date_preset": "last_7d",
  "accounts": [
    {
      "account_id": "act_YOUR_ACCOUNT_ID",
      "account_name": "Client Name",
      "status": "ACTIVE",
      "spend": 3200.00,
      "impressions": 150000,
      "clicks": 4500,
      "ctr": 3.0,
      "cpc": 0.71,
      "purchases": 45,
      "revenue": 9800.00,
      "roas": 3.06
    }
  ]
}
```

---

## HOW TO RESPOND

When asked about ad performance:

1. **Read the appropriate JSON file** from `ad-data/` based on the time range requested
2. **Default to last 7 days** if no time range specified
3. **Present data in clean tables** with spend, clicks, conversions, ROAS
4. **Calculate totals** across accounts when showing summaries
5. **Compare periods** when asked (e.g., read both yesterday and last_7d files)
6. **Flag anomalies:** ROAS below 2.0, sudden spend spikes, zero-conversion campaigns

### Formatting Standards
- Dollar amounts: `$5,373.13` (always `$` + commas)
- ROAS: `3.40x` (2 decimal places)
- Percentages: `3.0%`
- Sort by descending spend by default
- Always show `fetched_at` timestamp for data freshness

---

## EXAMPLE PROMPTS

- "How are our Google Ads doing?" → Read `google-ads-summary-last_7_days.json`
- "Show me campaign breakdown for [Client]" → Read campaigns file, filter by account
- "What's our total spend this month?" → Read both platform summary last_30d files, sum all spend
- "Compare yesterday vs last week" → Read yesterday and last_7_days files side by side
- "Any campaigns with ROAS below 2x?" → Read campaigns file, flag low performers

---

## ANOMALY FLAGS

Always proactively flag:
- ROAS below 2.0x (for eCommerce — adjust threshold for your clients)
- Spend up or down >30% vs prior period
- CTR dropping >20% week-over-week
- Zero conversions on a campaign that had conversions last period
- Campaigns in error or unexpectedly paused state

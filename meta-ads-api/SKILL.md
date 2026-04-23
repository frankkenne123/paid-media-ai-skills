---
name: meta_ads_api
description: "Meta Marketing API Integration — use when managing Meta (Facebook/Instagram) ad campaigns, pulling insights, creating/editing ad sets, launching ads, building custom/lookalike audiences, uploading creative, checking account health, or any direct Meta Ads operation. Requires META_ACCESS_TOKEN and META_AD_ACCOUNT_ID in .env. Handles the full campaign lifecycle via the Marketing API."
user-invocable: true
---

# Meta Marketing API Integration

Direct API integration with Meta (Facebook/Instagram) Ads for full campaign management, insights, audience building, and creative upload.

---

## SETUP

Add to your `.env`:
```
META_ACCESS_TOKEN=your_long_lived_access_token
META_AD_ACCOUNT_ID=act_your_ad_account_id
META_APP_ID=your_facebook_app_id
META_APP_SECRET=your_facebook_app_secret
META_API_VERSION=v20.0
```

**Where to get these:**
1. Create a Meta for Developers app at [developers.facebook.com](https://developers.facebook.com)
2. Add Marketing API product → generate access token with `ads_management` + `ads_read` + `business_management` permissions
3. Use the long-lived token exchange to get a 60-day token (or a System User token for production)
4. Ad Account ID is in Business Manager → Ad Accounts (prefix with `act_`)

**API Base:** `https://graph.facebook.com/v20.0`

All calls: `?access_token=YOUR_META_ACCESS_TOKEN`

---

## CAMPAIGN HIERARCHY

```
Ad Account
└── Campaign (objective, budget)
    └── Ad Set (audience, placement, schedule, optimization goal)
        └── Ad (creative, headline, body, CTA)
```

Always think in this hierarchy. When a user says "run a new ad," you need: campaign (or reuse existing) → ad set → ad.

---

## CORE OPERATIONS

### 1. Get Account Insights
```bash
curl -G "https://graph.facebook.com/v20.0/act_YOUR_ACCOUNT_ID/insights" \
  -d "access_token=YOUR_META_ACCESS_TOKEN" \
  -d "date_preset=last_7d" \
  -d "fields=spend,impressions,clicks,ctr,cpc,cpm,actions,action_values,purchase_roas" \
  -d "level=account"
```

### 2. List Campaigns
```bash
curl -G "https://graph.facebook.com/v20.0/act_YOUR_ACCOUNT_ID/campaigns" \
  -d "access_token=YOUR_META_ACCESS_TOKEN" \
  -d "fields=id,name,status,objective,daily_budget,lifetime_budget,created_time" \
  -d "limit=100"
```

### 3. Create a Campaign
```bash
curl -X POST "https://graph.facebook.com/v20.0/act_YOUR_ACCOUNT_ID/campaigns" \
  -d "access_token=YOUR_META_ACCESS_TOKEN" \
  -d "name=Client Name - Campaign Name - MM.DD.YY" \
  -d "objective=OUTCOME_SALES" \
  -d "status=PAUSED" \
  -d "special_ad_categories=[]"
```
> **ALWAYS create campaigns in PAUSED status.** Require human approval before activating.

**Common objectives:**
- `OUTCOME_SALES` — Purchase optimization (eCommerce default)
- `OUTCOME_LEADS` — Lead generation
- `OUTCOME_TRAFFIC` — Link clicks / landing page views
- `OUTCOME_AWARENESS` — Reach / brand awareness
- `OUTCOME_ENGAGEMENT` — Post engagement

### 4. Create an Ad Set
```bash
curl -X POST "https://graph.facebook.com/v20.0/act_YOUR_ACCOUNT_ID/adsets" \
  -d "access_token=YOUR_META_ACCESS_TOKEN" \
  -d "name=Ad Set Name" \
  -d "campaign_id=CAMPAIGN_ID" \
  -d "daily_budget=5000" \
  -d "billing_event=IMPRESSIONS" \
  -d "optimization_goal=OFFSITE_CONVERSIONS" \
  -d 'targeting={"geo_locations":{"countries":["US"]},"age_min":25,"age_max":55}' \
  -d "status=PAUSED"
```
> Budget values are in cents (`5000` = $50/day)

### 5. Get Ad Set Insights (campaign performance breakdown)
```bash
curl -G "https://graph.facebook.com/v20.0/act_YOUR_ACCOUNT_ID/insights" \
  -d "access_token=YOUR_META_ACCESS_TOKEN" \
  -d "date_preset=last_7d" \
  -d "level=adset" \
  -d "fields=adset_id,adset_name,spend,impressions,clicks,ctr,cpc,actions,action_values" \
  -d "limit=500"
```

### 6. Get Ad-Level Insights (creative performance)
```bash
curl -G "https://graph.facebook.com/v20.0/act_YOUR_ACCOUNT_ID/insights" \
  -d "access_token=YOUR_META_ACCESS_TOKEN" \
  -d "date_preset=last_30d" \
  -d "level=ad" \
  -d "fields=ad_id,ad_name,spend,impressions,ctr,video_play_actions,actions,purchase_roas" \
  -d "limit=500"
```

### 7. Update Status (pause / activate campaigns, ad sets, ads)
```bash
curl -X POST "https://graph.facebook.com/v20.0/CAMPAIGN_OR_ADSET_OR_AD_ID" \
  -d "access_token=YOUR_META_ACCESS_TOKEN" \
  -d "status=ACTIVE"   # or PAUSED
```

### 8. Update Budget
```bash
curl -X POST "https://graph.facebook.com/v20.0/ADSET_ID" \
  -d "access_token=YOUR_META_ACCESS_TOKEN" \
  -d "daily_budget=10000"
```

### 9. Create Custom Audience (from customer list)
```bash
curl -X POST "https://graph.facebook.com/v20.0/act_YOUR_ACCOUNT_ID/customaudiences" \
  -d "access_token=YOUR_META_ACCESS_TOKEN" \
  -d "name=Purchasers Last 180d" \
  -d "subtype=CUSTOM" \
  -d "customer_file_source=USER_PROVIDED_ONLY" \
  -d "description=Recent buyers for retargeting"
```

### 10. Create Lookalike Audience
```bash
curl -X POST "https://graph.facebook.com/v20.0/act_YOUR_ACCOUNT_ID/customaudiences" \
  -d "access_token=YOUR_META_ACCESS_TOKEN" \
  -d "name=LAL 1% US — Purchasers 180d" \
  -d "subtype=LOOKALIKE" \
  -d 'lookalike_spec={"type":"custom_ratio","country":"US","ratio":0.01,"origin_audience_id":"SOURCE_AUDIENCE_ID"}'
```

---

## KEY METRICS TO PULL

| Metric | Meta Field | Meaning |
|--------|-----------|---------|
| Spend | `spend` | Dollars spent |
| Impressions | `impressions` | Times ad was shown |
| Clicks | `clicks` | Link + button clicks |
| CTR | `ctr` | Click-through rate % |
| CPC | `cpc` | Cost per click |
| CPM | `cpm` | Cost per 1000 impressions |
| Purchases | `actions` → `purchase` | Purchase count |
| Revenue | `action_values` → `purchase` | Purchase value in $ |
| ROAS | `purchase_roas` | Return on ad spend |
| Hook Rate | `video_play_actions` / impressions | 3-sec video view rate |

For `actions` and `action_values`, the response is an array — filter by `action_type=purchase` (or other conversion events).

---

## WORKFLOW RULES

1. **NEVER auto-activate campaigns, ad sets, or ads** — always create in PAUSED status, require human approval before launch
2. **Budget changes >20%** require confirmation before sending
3. **Paused campaigns** — never resume without explicit instruction
4. **Error handling** — Meta returns rate limit errors (code 80000) — back off and retry with exponential delay
5. **Dollar values** — budget fields are in **cents** (5000 = $50). Insights return dollars as strings.
6. **Token refresh** — long-lived tokens expire after 60 days. Use System User tokens for production automation.

---

## COMMON DIAGNOSIS PROMPTS

- **"How is [Client] Meta doing last 7 days?"** → Account insights with `date_preset=last_7d`, show ROAS, spend, CPM, CTR
- **"Which ad sets should we scale?"** → Ad set insights last 14 days, filter ROAS >3.0x and spend >$500
- **"Which creative is winning?"** → Ad-level insights last 30 days, sort by purchase_roas DESC
- **"Is our pacing on track?"** → Account insights today + daily_budget — calculate spend % of daily budget by hour
- **"Audit this account"** → Combine: campaigns, ad sets, ads, recent insights — report structure + performance

---

## NOTES
- Always use `act_` prefix for ad account IDs
- Meta insights have an ~3 hour delay — don't rely on "today" data before 10am
- Attribution defaults: 7-day click + 1-day view. Specify `action_attribution_windows` for custom
- Conversion API (CAPI) is separate — this skill handles Marketing API only

---
name: meta_ads_campaign_builder
description: "Meta Ads campaign-build playbook — end-to-end recipe for creating fully-editable Meta (Facebook/Instagram) ad campaigns programmatically: campaign + ad set + creative + ad. Covers the gotchas that block production builds (dev-mode app blocker, CBO vs ABO, Advantage+ age constraints, naming conventions, and rebuilding legacy dark-post ads to editable single-image-with-website-destination ads). Use this whenever you're building Meta campaigns from scratch, troubleshooting an `Ads creative post was created by an app that is in development mode` error, or migrating dark-post ads to fully-editable creatives. Companion to meta-ads-api (which covers individual API calls)."
user-invocable: true
---

# Meta Ads Campaign Builder Playbook

End-to-end recipe for creating production Meta Ads campaigns via the Marketing API. This is the playbook complement to the `meta-ads-api` reference skill — that one tells you which endpoint to call; this one tells you what gotchas block real-world builds and how to handle them.

---

## SETUP

```
META_ACCESS_TOKEN=long_lived_user_or_system_user_token
META_AD_ACCOUNT_ID=act_xxxxxxxxxxxxx
META_API_VERSION=v22.0
```

**Token requirements:**
- Scopes: `ads_management`, `ads_read`, `business_management`, `pages_manage_posts`, `pages_read_engagement`, `pages_show_list`
- For production-mode use: the Meta app behind the token must be in **Live mode** (App Review approved) for `ads_management`. Otherwise, the dev-mode block (error subcode `1885183`) will reject `object_story_spec.link_data` creative creation. See "Dev-mode block" section below.

---

## CAMPAIGN HIERARCHY (Always Build In This Order)

```
Ad Account
  └── Campaign        — objective, special_ad_categories, optionally CBO budget
      └── Ad Set      — targeting, optimization_goal, billing_event, optionally ABO budget
          └── Creative — image_hash + link_data (or object_story_id for legacy dark posts)
              └── Ad  — links creative to ad set, status PAUSED for review
```

**Always create in PAUSED status.** The operator activates manually after Ads Manager review. This is non-negotiable — it's the safety net against runaway spend on a typo'd budget or wrong audience.

---

## THE 5-STEP BUILD

### Step 1 — Resolve campaign budget mode (CBO vs ABO) BEFORE creating ad sets

Before posting an ad set, GET the parent campaign:

```bash
curl -s "https://graph.facebook.com/v22.0/CAMPAIGN_ID?fields=daily_budget,lifetime_budget&access_token=$TOKEN"
```

- If `daily_budget` OR `lifetime_budget` is set → campaign uses **CBO**. **OMIT** `daily_budget` from the ad set POST. Meta distributes the campaign budget across ad sets automatically.
- If neither is set → campaign uses **ABO**. Pass `daily_budget` (in cents) at the ad set level.

**Symptom of mismatch:** `error_subcode: 1885621` "Can't Set Ad Set and Campaign Budget — You can only set an ad set budget or a campaign budget."

### Step 2 — Create the ad set with valid Advantage+ targeting

When `targeting_automation.advantage_audience: 1` is enabled, the targeting block has strict constraints:

```json
{
  "age_min": 18,
  "age_max": 65,
  "age_range": [35, 65],
  "geo_locations": {"countries": ["US"], "location_types": ["home", "recent"]},
  "targeting_automation": {"advantage_audience": 1}
}
```

- `age_min` **MUST** be 18 (Meta's legal minimum for Advantage+ expansion).
- The desired audience age range goes in `age_range: [low, high]`. That's the *preferred* hint Advantage+ honors while still being allowed to expand outside it.
- Setting `age_min: 35` directly with Advantage+ on returns `error_subcode: 1870188` "Minimum age is above threshold".

```bash
curl -s -X POST "https://graph.facebook.com/v22.0/$ACT/adsets" \
  -d "access_token=$TOKEN" \
  -d "name=Broad targeting (35-65+) - AI" \
  -d "campaign_id=CAMPAIGN_ID" \
  -d "billing_event=IMPRESSIONS" \
  -d "optimization_goal=OFFSITE_CONVERSIONS" \
  -d 'targeting={"age_min":18,"age_max":65,"age_range":[35,65],"geo_locations":{"countries":["US"]},"targeting_automation":{"advantage_audience":1}}' \
  -d 'promoted_object={"pixel_id":"PIXEL_ID","custom_event_type":"PURCHASE"}' \
  -d "status=PAUSED" \
  -d "start_time=2026-05-08T14:00:00Z"
```

### Step 3 — Upload the creative image

```bash
curl -s -X POST "https://graph.facebook.com/v22.0/$ACT/adimages?access_token=$TOKEN" \
  -F "filename=@/path/to/creative.png"
```

Response: `{"images": {"creative.png": {"hash": "abc123..."}}}`. Capture the `hash` for step 4.

### Step 4 — Create the ad creative (the editable, production-correct way)

Use `object_story_spec.link_data` for full editability. This is the path that produces a single-image ad with a website destination, where URL, headline (`name`), body copy (`message`), and CTA are all editable in Ads Manager UI:

```bash
SPEC='{"page_id":"PAGE_ID","link_data":{"image_hash":"HASH","link":"https://landing.com","name":"Headline","message":"Body copy","call_to_action":{"type":"SHOP_NOW","value":{"link":"https://landing.com"}}}}'

curl -s -X POST "https://graph.facebook.com/v22.0/$ACT/adcreatives" \
  -d "access_token=$TOKEN" \
  -d "name=Campaign Creative — slug" \
  -d "object_story_spec=$SPEC"
```

If body copy or headline aren't ready yet, pass empty strings (`"message": "", "name": ""`) — the operator fills them in per-ad in Ads Manager.

### Step 5 — Create the ad (PAUSED)

```bash
curl -s -X POST "https://graph.facebook.com/v22.0/$ACT/ads" \
  -d "access_token=$TOKEN" \
  -d "name=Ad name (descriptive — see naming rule below)" \
  -d "adset_id=ADSET_ID" \
  -d "creative={\"creative_id\":\"CREATIVE_ID\"}" \
  -d "status=PAUSED"
```

---

## THE DEV-MODE BLOCK (and the dark-post workaround)

If the Meta app behind your token is in **Development mode**, step 4 above will fail with:

```json
{
  "error_subcode": 1885183,
  "error_user_title": "Ads creative post was created by an app that is in development mode",
  "error_user_msg": "Ads creative post was created by an app that is in development mode. It must be in public to create this ad."
}
```

This blocks every variant of `object_story_spec` creative creation: `link_data`, `photo_data`, `asset_feed_spec`, etc.

### Permanent fix (recommended)

Move the app to Live mode and submit App Review for `ads_management`:

1. Open `https://developers.facebook.com/apps/{APP_ID}/app-review/permissions/`
2. Click "Request Advanced Access" for each of: `ads_management`, `ads_read`, `business_management`, `pages_manage_posts`
3. For each: paste a use-case description, step-by-step user flow, and a 4-5 minute screencast (unlisted YouTube is fine)
4. Submit. Approval typically lands in 1-3 weeks.
5. Toggle App Mode → Live in `/settings/basic/`.

### Temporary workaround (dark posts via `object_story_id`)

For builds while waiting for App Review:

1. Upload the image as an **unpublished page photo** (uses `pages_manage_posts` scope — NOT blocked by dev mode):
   ```bash
   curl -s -X POST "https://graph.facebook.com/v22.0/PAGE_ID/photos" \
     -F "source=@/path/to/image.png" \
     -F "published=false" \
     -F "access_token=$PAGE_TOKEN"
   ```
   Capture the `page_story_id` (format: `PAGEID_POSTID`).

2. Create the creative referencing the unpublished post via `object_story_id`:
   ```bash
   curl -s -X POST "https://graph.facebook.com/v22.0/$ACT/adcreatives" \
     -d "access_token=$TOKEN" \
     -d "name=Dark Post Creative" \
     -d "object_story_id=PAGEID_POSTID" \
     -d 'call_to_action={"type":"SHOP_NOW","value":{"link":"https://landing.com"}}'
   ```

**Limitations of the dark-post workaround:**
- Body copy is NOT editable in Ads Manager UI (it's the page post's `message` field).
- API PATCH on the page post is also blocked by dev mode (same `permission for this endpoint` error).
- URL / CTA / headline ARE editable in Ads Manager.

When the app eventually goes Live, **delete and rebuild** dark-post ads via the direct path to restore full editability — Meta keeps the legacy lock on posts created during dev mode.

---

## NAMING CONVENTIONS

When the operator says **"name both ad sets the same way"** or **"both like that"** — name them **identically with no format-differentiator suffix** (no "Grp 5", "- Feed", "- Story"). Differentiate at the **ad** level instead. The operator works at the ad-set level for budget/targeting and the ad level for creative variants — duplicate ad set names are intentional and fine.

When the operator says **"put today's date so I know"** — append `YYYY-MM-DD` to BOTH the ad set name AND each ad name:

| Asset | Name pattern |
|---|---|
| Ad set | `Broad targeting (35-65+) - AI - 2026-05-06` |
| Ad | `AI-v2 - Feed 11 - 2026-05-06` |

The date suffix lets the operator visually scan Ads Manager and spot the new build instantly.

---

## REBUILDING LEGACY DARK-POST ADS TO EDITABLE

Once the app is Live, dark-post ads created in dev mode keep their legacy body-copy lock. To restore full editability, delete and rebuild via the direct path:

```python
# Pseudo-flow
for old_ad_id in legacy_dark_post_ids:
    DELETE /v22.0/{old_ad_id}

for image, ad_set in product:
    image_hash = upload_image(image)
    creative_id = POST /act_X/adcreatives with object_story_spec.link_data  # the editable path
    new_ad_id = POST /act_X/ads with creative_id, status=PAUSED
```

Same images, same ad sets (rename/keep), same URL — but the new ads are fully editable in Ads Manager.

---

## COMMON PITFALLS

| Symptom | Cause | Fix |
|---|---|---|
| `error_subcode: 1885183` "app is in development mode" | App in dev mode | Submit App Review, or use dark-post workaround |
| `error_subcode: 1885621` "Can't Set Ad Set and Campaign Budget" | Trying to set ad-set budget on a CBO campaign | Omit `daily_budget` at ad set level |
| `error_subcode: 1870188` "Minimum age is above threshold" | `age_min > 18` with Advantage+ on | Use `age_min: 18` + `age_range: [low, high]` |
| `error_subcode: 4834011` "is_adset_budget_sharing_enabled required" | Missing required field at campaign creation | Add `is_adset_budget_sharing_enabled: false` to campaign POST |
| Body copy greyed out in Ads Manager UI for an ad | Ad uses `object_story_id` (dark post) | Delete and rebuild via `link_data` (requires Live mode) |
| `Pixel must be on the page` | Pixel not installed on landing URL | Verify Pixel Helper extension shows fire on landing page |
| `Bidding strategy not allowed for this objective` | `LOWEST_COST_WITHOUT_CAP` on OUTCOME_AWARENESS | Switch to LIFETIME_BUDGET or change objective |

---

## WHEN TO USE THIS SKILL

- Building a new Meta campaign from scratch (campaign + ad set + ads in one flow)
- Diagnosing a build that's failing with one of the error subcodes above
- Migrating legacy dark-post ads to fully-editable creatives after App Review approval
- Setting up multi-format builds (1:1 Feed + 9:16 Story) with shared targeting

**Pair with `meta-ads-api`** for individual API call reference (insights, audiences, single ad updates). This skill is the recipe; that one is the reference manual.

# creative-specialist · tools

Runnable scripts that pair with `../SKILL.md`. Together they let an AI agent build, audit, and document Meta ad campaigns end-to-end.

## What's here

| File | Purpose |
|---|---|
| `build_meta_campaign_full.py` | **Meta:** one-command builder — campaign → ad set → upload image → adcreative → ad. Supports `--reuse-adset <ID>` to add additional creative variants to an existing ad set (one-variable testing). All PAUSED until approved. |
| `build_google_search_campaign.py` | **Google Ads — Search:** Responsive Search Ad builder — budget → campaign → ad group → RSA (3-15 headlines × 2-4 descriptions) → keywords with match-type syntax. |
| `build_google_pmax_campaign.py` | **Google Ads — Performance Max:** asset-group builder — uploads 5+ images, 1+ logos, headlines/descriptions, links YouTube videos. PMax is asset-driven, no manual targeting. |
| `build_tiktok_campaign.py` | **TikTok:** in-feed video ad builder — upload video → campaign → ad group → ad. Uses `PLACEMENT_TYPE_AUTOMATIC` (TikTok's Advantage+ equivalent). |
| `activate_paused_resources.py` | **All platforms:** activate PAUSED resources after the user approves. Cascades campaign → ad sets/groups → ads. Confirmation prompt by default; `--yes` to skip; `--dry-run` to preview. Meta supports `--ad-id` for activating a single variant. |
| `discover_client_brief.py` | Pulls everything Meta knows about a client (Pages, Pixels, IG, currently-running ad copy) + scrapes their homepage for brand voice signals. Outputs `client-briefs/<slug>.md`. |
| `analyze_account_creatives.py` | Pulls every active Meta ad with copy + creative URL + 30-day performance into a markdown worksheet for framework analysis. |
| `META_CAMPAIGN_PLAYBOOK.md` | The 5-step recipe an agent follows to build a Meta campaign. |
| `client-briefs/_TEMPLATE.md` | Per-client brief template — populated by discovery, refined over time. |
| `accounts.example.json` | Example config for batch discovery: `{"act_XXXXXXXX": "slug"}`. Copy to `accounts.json` and fill in. |

## Setup

```bash
pip install requests python-dotenv google-ads
```

Configure `.env` (in this folder or any parent) per the platforms you'll use:

```ini
# Meta
META_ACCESS_TOKEN=...               # scopes: ads_management, ads_read, business_management,
                                    #         pages_show_list, pages_manage_posts, pages_read_engagement
                                    # System User token recommended (never expires)

# Google Ads
GOOGLE_ADS_DEVELOPER_TOKEN=...
GOOGLE_ADS_CLIENT_ID=...
GOOGLE_ADS_CLIENT_SECRET=...
GOOGLE_ADS_REFRESH_TOKEN=...
GOOGLE_ADS_LOGIN_CUSTOMER_ID=...    # MCC ID (no dashes)

# TikTok
TIKTOK_ACCESS_TOKEN=...             # long-lived from TikTok for Business
TIKTOK_ADVERTISER_ID=...
TIKTOK_IDENTITY_ID=...              # CUSTOMIZED_USER or AUTHORIZED_BC_ACCOUNT
TIKTOK_PIXEL_ID=...                 # required for CONVERSIONS objective
```

## Workflow

```bash
# 1. Discover everything Meta + the website know about your clients
cp accounts.example.json accounts.json   # then edit accounts.json
python3 discover_client_brief.py --all --accounts-file accounts.json
# → writes client-briefs/<slug>.md for each

# 2. Audit what's running on a client (Meta)
python3 analyze_account_creatives.py --account act_XXXXXXXX --output /tmp/audit.md
# Open /tmp/audit.md, fill in the framework analysis (per SKILL.md §1, §3, §5)

# 3. Build a new campaign — Meta
python3 build_meta_campaign_full.py \
  --account act_XXXXXXXX --client "Acme Co" \
  --campaign-name "Spring ACQ" --daily-budget 50 \
  --landing-url "https://..." \
  --headline "..." --primary-text "..." --description "..." \
  --cta SHOP_NOW \
  --image /tmp/acme_creative.png \
  --page-id <PAGE_ID> --pixel-id <PIXEL_ID> \
  --countries US

# 3b. Build on Google Search instead (text-only, RSA)
python3 build_google_search_campaign.py \
  --customer XXXXXXXXXX --client "Acme Co" \
  --campaign-name "Brand Search" --daily-budget 50 \
  --final-url "https://..." \
  --headlines "Headline 1" "Headline 2" "Headline 3" "Headline 4" "Headline 5" \
  --descriptions "Desc 1" "Desc 2" \
  --keywords "broad keyword" '"phrase match"' "[exact match]" \
  --countries US

# 3c. Build on TikTok (video-first)
python3 build_tiktok_campaign.py \
  --client "Acme Co" --campaign-name "Spring ACQ" --daily-budget 50 \
  --landing-url "https://..." \
  --ad-text "..." --cta SHOP_NOW \
  --video /tmp/acme_video.mp4 \
  --countries US

# All builders create resources PAUSED. Activate via the platform UI or by
# updating status to ENABLED/ACTIVE on the respective campaign.
```

All builders support `--dry-run` to print mutations without sending.

## Privacy

The shipped `.gitignore` excludes:
- `accounts.json` — your real account list
- `client-briefs/*.md` (except `_TEMPLATE.md`) — they contain Pixel and Page IDs
- `audits/` — they contain spend and revenue numbers
- `.env` — your API token

Don't disable. Don't commit any of these.

## Defaults you should know

- **All campaigns / ad sets / ads are created PAUSED.** Activation is a separate explicit step.
- **Default targeting is Advantage+ broad.** Override with `--manual-targeting`.
- **Default bid strategy is `LOWEST_COST_WITHOUT_CAP`.**
- **Default optimization goal is `OFFSITE_CONVERSIONS` → PURCHASE event** (assumes a Pixel with PURCHASE on the landing page).

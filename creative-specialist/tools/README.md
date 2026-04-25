# creative-specialist · tools

Runnable scripts that pair with `../SKILL.md`. Together they let an AI agent build, audit, and document Meta ad campaigns end-to-end.

## What's here

| File | Purpose |
|---|---|
| `build_meta_campaign_full.py` | One-command campaign builder: campaign → ad set → upload image → adcreative → ad. All PAUSED until the user approves. |
| `discover_client_brief.py` | Pulls everything Meta knows about a client (Pages, Pixels, IG, currently-running ad copy) + scrapes their homepage for brand voice signals. Outputs `client-briefs/<slug>.md`. |
| `analyze_account_creatives.py` | Pulls every active ad with copy + creative URL + 30-day performance into a markdown worksheet for framework analysis. |
| `META_CAMPAIGN_PLAYBOOK.md` | The 5-step recipe an agent follows to build a campaign. |
| `client-briefs/_TEMPLATE.md` | Per-client brief template — populated by discovery, refined by the user over time. |
| `accounts.example.json` | Example config for batch discovery: `{"act_XXXXXXXX": "slug"}`. Copy to `accounts.json` and fill in. |

## Setup

```bash
pip install requests python-dotenv

# .env in this folder (or any parent)
echo "META_ACCESS_TOKEN=your_token_here" > .env
```

Token needs scopes: `ads_management`, `ads_read`, `business_management`, `pages_show_list`, `pages_manage_posts`, `pages_read_engagement`. A System User token is best (never expires).

## Workflow

```bash
# 1. Discover everything Meta + the website know about your clients
cp accounts.example.json accounts.json   # then edit accounts.json
python3 discover_client_brief.py --all --accounts-file accounts.json
# → writes client-briefs/<slug>.md for each

# 2. Audit what's running on a client
python3 analyze_account_creatives.py --account act_XXXXXXXX --output /tmp/audit.md
# Open /tmp/audit.md, fill in the framework analysis (per SKILL.md §1, §3, §5)

# 3. Build a new campaign (after the user approves the copy + image)
python3 build_meta_campaign_full.py \
  --account act_XXXXXXXX --client "Acme Co" \
  --campaign-name "Spring ACQ" --daily-budget 50 \
  --landing-url "https://..." \
  --headline "..." --primary-text "..." --description "..." \
  --cta SHOP_NOW \
  --image /tmp/acme_creative.png \
  --page-id <PAGE_ID> --pixel-id <PIXEL_ID> \
  --countries US
# All resources land PAUSED. Activate with:
#   curl -X POST .../v20.0/<CAMPAIGN_ID> -d "status=ACTIVE" -d "access_token=$META_ACCESS_TOKEN"
```

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

# Meta Campaign Build Playbook

End-to-end recipe for building a Meta campaign **including new ad copy and new creatives**, from scratch, in one session. Pairs with the `creative-specialist` skill.

---

## Prerequisites

- `META_ACCESS_TOKEN` in `.env` with scopes: `ads_management`, `ads_read`, `business_management`, `pages_show_list`, `pages_manage_posts`, `pages_read_engagement`. A System User token is best (never expires); a Long-lived User token works for ~60 days.
- For each client: their Ad Account ID, Facebook Page ID, Meta Pixel ID, landing page URL. The `discover_client_brief.py` tool auto-discovers most of this.
- An image-generation tool (this playbook assumes a `generate_image()` capability on your agent — e.g. fal.ai Nano Banana Pro, Replicate, Midjourney via API, etc.).

---

## Inputs (ALWAYS read `client-briefs/<slug>.md` FIRST)

Per-client briefs live at `client-briefs/<slug>.md`. They get auto-populated by `discover_client_brief.py` from the Meta API + the brand's website. **Read the brief before asking the user anything.** Most of what you'd ask is already in there.

What auto-discovery gives you:
- Ad Account, Currency, Timezone, Business Manager
- Connected Facebook Pages (with IDs)
- Connected Pixels (with IDs + last-fired times)
- Linked Instagram accounts
- Homepage URL + page title + meta description (= a starting take on brand voice)
- Currently-running ad copy (their actual voice in market — best raw material for matching tone)

What the user still has to fill in (don't guess, ask):
- Standing offer (free shipping, % off, etc.)
- Target ROAS / acceptable CPC / CPM
- Brand voice refinements (banned words, hooks that work, hooks to avoid)
- Visual style refinements (color palette, lifestyle vs flat-lay vs UGC)
- Per-campaign: budget, landing URL (if not the standing one), specific angle/hook for this push

To **regenerate** a brief (e.g. after a new ad account is added, or to refresh active-ad samples):
```bash
python3 discover_client_brief.py --account act_XXXXXXXX --slug <slug>
# or all at once (requires accounts.json — see accounts.example.json)
python3 discover_client_brief.py --all --accounts-file accounts.json
```

If the user asks for a campaign on a client whose brief is missing, run discovery FIRST, then read the brief, then start the build.

---

## The 5-step build

### Step 1 — Draft the copy

Write 2-3 variants of:
- **Headline** (≤40 chars renders cleanly)
- **Primary text** (first 125 chars must land before "...See more")
- **Description** (sub-headline below CTA)
- Pick a CTA: `SHOP_NOW`, `LEARN_MORE`, `SIGN_UP`, `GET_OFFER`, etc.

Show the user the variants. Pick one (or let them pick). **Don't move to Step 2 until copy is approved.**

Match the brand voice from the brief — see `creative-specialist/SKILL.md` §1 for hook frameworks (PAS, Before-After-Bridge, AIDA, Problem-Solution, Social-Proof Lead, Scarcity, Curiosity).

### Step 2 — Generate the creative

Use your image-generation tool. For Meta feed/Reels, default size is **1080×1080 (1:1)** for feed, **1080×1920 (9:16)** for Stories/Reels.

Prompt structure: subject → setting → lighting → style → camera/lens → quality. See `creative-specialist/SKILL.md` §3 for category-specific prompt templates.

**Example (jewelry/streetwear):**
```
Bold streetwear flat lay of a chunky gold cuban link chain on dark concrete,
urban backdrop with neon purple accent light, hip-hop editorial photography,
shot on Canon R5 with 85mm lens, ultra-detailed 8K commercial product shot,
luxury jewelry aesthetic
```

Show the image to the user. If they want changes, regenerate. **Save the final image locally** — most generators return a URL, but you need a file on disk for the next step. Save to `/tmp/<client>_creative_<timestamp>.png`.

### Step 3 — Build the campaign (one command)

```bash
python3 build_meta_campaign_full.py \
  --account act_XXXXXXXX \
  --client "Acme Co" \
  --campaign-name "Spring ACQ" \
  --daily-budget 50 \
  --landing-url "https://acme.example.com/collections/new" \
  --headline "Hand-Crafted Statement Pieces" \
  --primary-text "Discover the bold designs trusted by 2M+ customers — free shipping over \$50." \
  --description "Limited drop. Ships today." \
  --cta SHOP_NOW \
  --image /tmp/acme_creative_0101_1015.png \
  --page-id <FACEBOOK_PAGE_ID> \
  --pixel-id <META_PIXEL_ID> \
  --countries US
```

**Default targeting is Advantage+ broad** — no flag needed. Only use `--manual-targeting --age-min X --age-max Y` when explicitly told to override.
**To preview API calls without firing them:** add `--dry-run`.

The script does this in order:
1. Creates campaign (PAUSED)
2. Creates ad set with Pixel + PURCHASE optimization (PAUSED)
3. Uploads your image to Meta → gets `image_hash`
4. Creates ad creative with copy + image + CTA + Page
5. Creates the ad and links creative to ad set (PAUSED)

Output: campaign ID, ad set ID, creative ID, ad ID. Everything paused.

### Step 4 — Show the user and wait for approval

Post the IDs + a screenshot of the ad preview. Wait for explicit approval. **Never auto-activate.**

### Step 5 — Activate when approved

```bash
curl -X POST "https://graph.facebook.com/v20.0/<CAMPAIGN_ID>" \
  -d "access_token=$META_ACCESS_TOKEN" \
  -d "status=ACTIVE"
# Repeat for the ad set and ad if Meta hasn't activated them automatically.
```

Or activate everything in one loop — see the `meta-ads-api` skill, "Update Status."

---

## Variations / Add-ons

- **Multiple creatives in one ad set (carousel-style A/B):** Run Step 3 multiple times with different `--image` and `--headline` against the SAME ad set. The script doesn't support `--reuse-adset` yet; build it inline if needed.
- **Lookalike audience:** Use the `meta-ads-api` skill's "Create Lookalike Audience" recipe before running the build script, then reference the audience ID in custom targeting.
- **Existing creative reuse:** Pull `GET /act_X/adcreatives` and pass an existing `creative_id` directly — no image upload needed. The full-build script doesn't support this yet; build it inline.

---

## Common pitfalls

- **"Bidding strategy not allowed for this objective"** — Some bid strategies require LIFETIME budget instead of DAILY. Default `LOWEST_COST_WITHOUT_CAP` works for everything except OUTCOME_AWARENESS — don't switch unless you know why.
- **"Page ID is required"** — Every ad MUST link to a Page. If the client doesn't have a Page, you can't run ads. Flag it and stop.
- **"Pixel must be on the page"** — `promoted_object` requires the pixel be installed on the landing page. If it isn't, conversions won't track.
- **Image dimensions wrong** — Meta auto-crops if dimensions don't match placement. For mixed feed + Stories, generate two images (1:1 and 9:16) instead of relying on auto-crop.
- **Token expired** — If `GET /me` fails, regenerate the token. Best long-term: a System User token (Business Manager → Users → System Users → Generate New Token → never expires).

---

## Privacy

Keep `.env`, `accounts.json`, `client-briefs/*.md`, and audit outputs out of any commit, log, or web post. The `.gitignore` shipped with this folder already excludes them — don't disable.

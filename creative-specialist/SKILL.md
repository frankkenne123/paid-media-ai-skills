---
name: creative-specialist
description: "Creative Specialist — use when writing ad copy, generating ad creatives (images), planning creative tests, or diagnosing creative fatigue for paid social campaigns. Concrete frameworks, prompt templates, testing thresholds. Pairs with build_meta_campaign_full.py and the client briefs in client-briefs/."
user-invocable: true
---

# Creative Specialist

Practical playbook for writing ad copy and generating creatives that actually run. No frameworks for their own sake — every section here exists because it changes a decision you'd otherwise have to wing.

> **Pre-flight (always):** Open `client-briefs/<slug>.md` for the client. Read their currently-running ad copy, homepage tagline, target ROAS, and standing offer. Match that voice — don't invent one. If the brief is missing or stale: `python3 discover_client_brief.py --account act_X --slug <slug>` first.

---

## 1. Hook frameworks (pick one per ad — don't blend them)

A "hook" is the first 1-2 sentences of primary text. It has to stop the scroll. Every framework below has the same job — different angles for different audiences.

### PAS — Problem / Agitate / Solve
Best for: pain-point products (wellness, fitness, productivity), lead gen.
```
P: [State the problem the audience already feels]
A: [Make it visceral — the cost of ignoring it]
S: [Your product as the relief]
```
**Example (wellness/CBD brand):**
> Most CBD oils are 10x weaker than the label claims. After months of "no effect" you assume it doesn't work for you — when really, you've been taking water. The nano-emulsified formula absorbs 17x faster, so you actually feel it.

### Before / After / Bridge
Best for: transformation products (fitness, beauty, finance, jewelry as identity).
```
Before: [Where they are now — be specific, not generic]
After:  [Where they want to be]
Bridge: [Your product is the path]
```
**Example (recovery/training facility):**
> Three months ago she got up from a chair creaking. Today she's back to lifting heavy and recovering fast. The difference: cold therapy + compression + sauna, three times a week.

### AIDA — Attention / Interest / Desire / Action
Best for: broad reach, brand-awareness layered with a CTA.
```
A: [Pattern interrupt — claim, stat, contrarian take]
I: [Why it matters to them specifically]
D: [The benefit/proof]
A: [What to do now]
```

### Problem / Solution (no agitation)
Best for: brands that don't want to feel "salesy" — premium, clinical, calm.
```
[State the problem matter-of-factly]
[State the solution matter-of-factly]
[One line of proof]
```
**Example (premium jewelry/streetwear brand):**
> Most chains tarnish in 6 months. Ours don't — every piece is real 14k gold, backed by a lifetime warranty. 20 years and counting.

### Social proof lead
Best for: established brands with reviews/numbers, second-iteration ads after a winner is found.
```
[Specific number/name — "2M customers", a real customer's first name, "Forbes"]
[What they got from it]
[Soft CTA]
```
**Example (jewelry/streetwear brand):**
> 2M+ customers. 4.8 stars. The same real gold the brand has been making for 20 years — now in the new Spring drop.

### Scarcity / Urgency
Best for: drops, sales, limited inventory. **Use sparingly** — Meta penalizes obvious clickbait, and audiences burn out fast on fake countdowns.
```
[Real constraint — limited stock, timed offer, seasonal]
[Why it matters]
[Time-bound CTA]
```

### Curiosity / Pattern interrupt
Best for: cold audiences who don't know the brand.
```
[Counterintuitive claim or question that breaks the scroll]
[Resolution — your product]
[CTA]
```
**Example:**
> If your CBD doesn't kick in within 15 minutes, you're wasting your money. Here's why nano-emulsified CBD works differently →

---

## 2. Copy structure for Meta ads (the 4 fields)

Every Meta ad has four copy fields. Here's how to think about each:

| Field | Char limit (rendered) | Job |
|---|---|---|
| **Primary text** | 125 visible before "...See more" | The hook + benefit. Use a hook framework above. |
| **Headline** | 27-40 visible (varies by placement) | The single biggest reason to click. Often a benefit statement. |
| **Description** | 30 visible (mobile feed only) | Reinforce or extend the headline. Often the offer. Frequently optional. |
| **CTA button** | Fixed Meta enum | Action verb. `SHOP_NOW` for ecom, `LEARN_MORE` for content/services, `SIGN_UP` / `GET_OFFER` for lead gen. |

### Templates by objective

**DTC ecommerce — OUTCOME_SALES, default for most clients:**
```
Primary text:  [Hook — 1-2 lines from frameworks above]
               [3-4 benefit bullets, single line each]
               [Soft CTA — "Shop the [collection name] now"]

Headline:      [Benefit + product type — "Real Gold, Lifetime Guaranteed"]
Description:   [Offer — "Free shipping over $50" or "20% off first order"]
CTA:           SHOP_NOW
```

**Lead gen — OUTCOME_LEADS:**
```
Primary text:  [PAS hook]
               [What they get when they sign up]
               [Time/effort cost — "Takes 30 seconds"]

Headline:      [The lead magnet name]
Description:   [Who it's for]
CTA:           SIGN_UP / GET_OFFER / DOWNLOAD
```

**Services / consulting / B2B — OUTCOME_LEADS or OUTCOME_TRAFFIC:**
```
Primary text:  [Specific outcome client got — name + before/after detail]
               [How — 2-3 sentence summary]
               [Open-loop — "If you want the same..."]

Headline:      [Service name + region/niche]
Description:   [Trust signal — years in business / number served]
CTA:           LEARN_MORE / BOOK_TRAVEL / CONTACT_US
```

### Copy rules
- **Primary text:** Don't waste the first 125 chars. The hook has to land before "See more."
- **No fake urgency.** "Last chance" / "today only" when it's not real → Meta lowers your delivery quality score and audiences smell it.
- **Match the brand brief's voice exactly.** If their currently-running ads say "drip" and "iced-out," yours should too. If they say "nano-emulsified" and "wellness," yours should too. **Don't homogenize different brands into one voice.**
- **Banned-word check:** Read the brief's "banned words" list before publishing. If empty, ask the user once and add to the brief.

---

## 3. Image generation prompt templates (Nano Banana Pro via fal.ai)

The image goes in `--image` of `build_meta_campaign_full.py`. Generate it first via the `generate_image` tool, save to `/tmp/<client>_creative_<timestamp>.png`, then run the build script.

### Prompt structure (always)
```
[Subject in foreground] + [Setting/environment] + [Lighting] + [Style/aesthetic] + [Camera/lens] + [Quality modifiers]
```
The order matters — subject first, modifiers last. Putting style before subject confuses the model.

### Templates by category

**Jewelry / streetwear / accessories:**
```
[Specific product — e.g. "chunky 14k gold cuban link chain"] on [surface — "dark concrete" / "marble slab" / "black velvet"], [accent lighting — "neon purple rim light from 45deg" / "warm golden hour through window"], [aesthetic — "hip-hop editorial" / "luxury minimalist"], shot on Canon R5 with [85mm portrait / 100mm macro] lens, ultra-detailed 8K commercial product photography, [mood — "bold and authentic" / "premium and quiet"]
```
**Concrete example:**
```
Chunky 14k gold cuban link chain coiled on dark concrete, neon purple rim light from 45deg with deep shadow on the right, hip-hop editorial aesthetic, shot on Canon R5 with 100mm macro lens, ultra-detailed 8K commercial product photography, bold and authentic mood
```

**Supplements / wellness / CBD:**
```
[Product bottle/dropper] on [natural surface — "raw linen" / "white marble" / "warm wood"], [botanicals nearby — "dried lavender sprigs" / "fresh sage" / "eucalyptus"], soft natural [morning / afternoon] window light from [left/right], clean wellness editorial style, shot on Sony A7R with 50mm lens, shallow depth of field, photorealistic, calm and clinical mood, neutral palette with [accent color from brand]
```

**Fitness / training / recovery:**
```
[Subject — "athletic woman in mid-30s" / "older man, fit, gray hair"] [action — "doing cold plunge" / "using compression boots" / "post-sauna with towel"], [setting — "modern recovery facility" / "minimalist gym"], [lighting — "natural skylight" / "warm tungsten ambient"], documentary lifestyle photography, candid not posed, shot on Sony A7IV with 35mm lens, [color grade — "muted warm" / "clean cool"], authentic UGC feel, no stock-photo cliches
```

**Beauty / skincare / fashion editorial:**
```
[Product or model with product] in [setting — "minimalist bathroom" / "neutral studio" / "soft pink backdrop"], [lighting — "soft beauty dish from front-left" / "natural diffused window light"], editorial beauty photography, shot on Hasselblad H6D with 80mm lens, skin texture preserved, [color palette from brand], aspirational but real, [mood]
```

### Dimensions cheat sheet (set when generating, or crop after)
| Placement | Dimensions | Notes |
|---|---|---|
| Feed (FB/IG) | **1080×1080 (1:1)** | Default for most builds |
| Stories / Reels | **1080×1920 (9:16)** | Generate separately, don't upscale |
| Marketplace | 1200×628 (1.91:1) | Rare — only if specifically asked |

For mixed feed + Stories campaigns: generate **two** images. Don't try to letterbox a 1:1 into a 9:16 — Stories will look bad.

### What to avoid in prompts
- **No "AI-generated" tells:** Avoid "render," "3D," "CGI," "digital art." Add "photorealistic," "shot on [camera]," "natural lighting."
- **No stock-photo cliches:** "happy diverse family," "businesswoman smiling at laptop," "minimalist lifestyle." Be specific.
- **No banned categories:** Meta rejects ads showing before/after weight loss, alcohol with explicit drinking, gambling with cash, sexually suggestive imagery, "perfect bodies." Generate in this style and the campaign will fail review.
- **Don't include text in the image** unless required — Meta's text-overlay rules are strict, and the headline goes in the copy field anyway. Exception: logo or product label is fine.

### Generating multiple variants for testing
For one ad set, generate **3 image variants on the same hook**, varying ONE element at a time:
1. Background — concrete vs. marble vs. fabric
2. Lighting — golden hour vs. neon vs. natural
3. Subject framing — flat lay vs. on model vs. macro detail

Build 3 ads in the same ad set (one per image) using the same copy. Let Meta auto-rotate. After 7 days at $50+/day spend, the winner will be obvious in ad-level insights.

---

## 4. Creative testing protocol

### The one-variable rule
Test ONE element at a time. Otherwise you can't tell what won.

| What you're testing | Hold constant | Vary |
|---|---|---|
| Hook | Same image, headline, CTA, audience | Primary text first 1-2 lines |
| Image | Same copy, headline, CTA, audience | Image only |
| Headline | Same primary text, image, CTA, audience | Headline only |
| Audience | Same ad, copy, image, CTA | Targeting only |

### Sample size and time
**Minimum to call a winner:**
- $50/day budget → 7-day test minimum, $350 total spend
- $100/day budget → 5-day test minimum, $500 total spend
- $250+/day budget → 3-day test minimum, $750 total spend

Below that, you're reading noise. Don't kill an ad after 24 hours unless it has zero impressions (delivery problem) or actual policy issues.

### When to declare a winner
- **Statistically meaningful gap:** winner's CPA is ≥30% lower than runner-up, OR winner's ROAS is ≥40% higher
- **Sustained for 3+ days** (not one-day spike)
- **Spend on each variant >= $200** (avoids small-sample illusion)

If gap is smaller, keep both and let Meta budget-allocate. Don't force a winner that isn't there.

---

## 5. Creative fatigue — concrete thresholds

A creative is "fatigued" when its performance has degraded materially. Watch these numbers per ad (not per ad set):

| Signal | Healthy | Warning (refresh soon) | Critical (kill or replace) |
|---|---|---|---|
| **CTR (link)** | Stable or rising | Down >25% from peak | Down >40% from peak |
| **CPM** | Stable | Up >20% from launch | Up >35% from launch |
| **Frequency** | <2.0 (week) | 2.5-3.5 | >4.0 |
| **CPA / CPC** | Stable | Up >25% | Up >50% |
| **ROAS** | At/above target | <80% of target | <60% of target |

**Rule of thumb:** if 2+ signals are in "warning" or any 1 is "critical," refresh.

### Lifespan by spend tier (when to expect fatigue)
| Daily spend | Typical creative lifespan | Refresh cadence |
|---|---|---|
| <$50/day | 30-60 days | Monthly |
| $50-200/day | 14-30 days | Every 2-3 weeks |
| $200-1000/day | 7-14 days | Weekly |
| >$1000/day | 3-7 days | Twice a week |

Higher spend = bigger audience saturated faster = more frequent refresh needed.

### What "refresh" means
1. **New image, same copy** — cheapest, fastest. Test first.
2. **New copy, same image** — try if image is still novel
3. **New hook framework + new image** — full refresh. Use when both are tired.
4. **New audience** — last resort. Only if Advantage+ has clearly saturated and CPMs are still rising.

---

## 6. Workflow — putting it together for a build

When the user says "build a campaign for [client]":

1. **Read the brief.** `client-briefs/<slug>.md`. Note voice, currently-running copy, offer.
2. **Pick a hook framework.** Match what the brief says works. If the brand's existing top performers favor (e.g.) Social Proof Lead + Problem-Solution, ride that voice; don't invent.
3. **Draft 2-3 copy variants.** Vary one element (hook lead vs. another). Show the user in Discord, get pick.
4. **Generate the image(s).** Use the category template. Generate 1080×1080 unless the user says Stories. Save to `/tmp/`.
5. **Run the build script.**
   ```bash
   python3 build_meta_campaign_full.py \
     --account <act_id> --client "<Client>" --campaign-name "<name>" \
     --daily-budget <$> --landing-url <url> \
     --headline "<H>" --primary-text "<P>" --description "<D>" --cta SHOP_NOW \
     --image /tmp/<file>.png \
     --page-id <from brief> --pixel-id <from brief>
   ```
   Default is Advantage+. Don't pass `--manual-targeting` unless the user tells you to.
6. **Show the user** the IDs and a preview screenshot. **Wait for explicit approval.**
7. **Activate** when the user says go (curl POST status=ACTIVE).
8. **Monitor** at 24/72/168 hours. Apply the testing thresholds (Section 4).
9. **Log to Obsidian** when the test finishes — what won, why, what you'd do next time.

---

## 7. Common mistakes to avoid

- **Inventing a brand voice.** The brief has the actual voice. Don't homogenize different brands into one tone.
- **Testing 4 things at once.** You'll learn nothing. One variable per test.
- **Killing ads after 24 hours.** Below sample-size threshold = noise.
- **Restarting the same ad on a new image.** Meta resets the learning phase. Better: new ad in same ad set.
- **Generating images with text in them.** Headline goes in the copy field. Only logos/product labels in the image.
- **Activating without the user's approval.** Hard rule. Build PAUSED, show the user, wait.
- **Forgetting to save the brief.** When the user gives you offer/ROAS/voice info, write it to `client-briefs/<slug>.md` immediately. Don't make them repeat themselves next session.

---

## 8. Auditing existing creatives (apply these frameworks to live ads)

When the user asks "audit [client] creatives" or "what's working / what should we kill," run:

```bash
python3 tools/analyze_account_creatives.py --account act_XXXXXXXX --output /tmp/<client>-audit.md
# Add --include-paused to also audit paused ads (useful for spotting past winners)
```

The script pulls every active ad with: copy fields, creative URL, ad set + campaign, and **30-day spend / revenue / CTR / CPM / frequency / ROAS**. It auto-flags critical fatigue signals (frequency ≥4.0, ROAS <1.0 on >$100 spend, CTR <0.8% on >5k impressions). Output is markdown — open it and fill in the analysis.

### What to fill in (per ad)

For each ad, classify and recommend:

1. **Hook framework** — Match the primary text's first 1-2 lines to one of: PAS, Before-After-Bridge, AIDA, Problem-Solution, Social-Proof Lead, Scarcity, Curiosity, or "no clear framework." This isn't always clean — pick the dominant pattern.
2. **Image style** — Studio product / UGC-feel / lifestyle-with-people / flat lay / before-after / text-overlay graphic.
3. **Recommendation** — `keep` (performing, fresh) / `refresh` (working but tired — new image or new copy) / `kill` (losing money, no path to fix).

### What to fill in (account-wide summary at the bottom)

After per-ad work, write the rollup:
- **Hook framework distribution** — count of ads per framework. Reveals what the brand has been leaning on.
- **What's working (keep + scale)** — winners by ROAS, with the framework + image style noted so we can repeat the pattern.
- **What's fatigued (refresh)** — ads with warning/critical fatigue flags but still worth refreshing.
- **What's losing money (kill)** — anything with sustained ROAS <1.0 on meaningful spend.
- **Gaps** — frameworks NOT being tested. If 80% of ads are Social-Proof Lead, recommend testing PAS or Before-After-Bridge to find new angles.
- **Recommended next 3 builds** — specific hook + image style combinations to test, derived from the gaps.

### Audit cadence
- **Weekly** for clients spending >$1k/day (creatives fatigue fast)
- **Bi-weekly** for $200-1000/day
- **Monthly** for <$200/day
- **On-demand** anytime the user asks or before launching a refresh batch

### Save the audit
Write the completed audit to `audits/<client>-<YYYY-MM-DD>.md` in this workspace. Reference the previous audit when running the next one — note what changed, what got killed, what got launched.

---

## 9. Quick reference: tools you actually use

| What you need | How |
|---|---|
| Generate an image | `generate_image(prompt="...")` (Nano Banana Pro via fal.ai) |
| Save image to disk | Pipe URL to `requests.get(...).content`, write to `/tmp/<client>_<stamp>.png` |
| Build full campaign | `python3 build_meta_campaign_full.py ...` (workspace root) |
| Audit existing creatives | `python3 analyze_account_creatives.py --account act_X --output ...` |
| Discover client context | `python3 discover_client_brief.py --account act_X --slug <slug>` |
| Pull live performance | `python3 meta_ads_data.py campaigns --account act_X --preset last_7d` |
| Lookup what's connected | `client-briefs/<slug>.md` — read first, ask the user only for what's missing |

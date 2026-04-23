---
name: creative_testing
description: "Creative Testing Engine — use when designing, launching, or analyzing structured creative A/B tests for Meta and Google ads. Handles test hypothesis design, variant planning (hook/format/angle/offer), statistical significance checking, and winner promotion to a living creative playbook. Works with performance-analyst and creative-specialist."
user-invocable: true
---

# Creative Testing Engine

Structured methodology for testing ad creative with statistical rigor. Prevents "creative vibes" decisions by enforcing one-variable-at-a-time testing and real data thresholds before calling winners.

---

## CORE PRINCIPLE: TEST ONE VARIABLE AT A TIME

The #1 mistake in creative testing is changing multiple things at once. If Variant A has a new hook AND new format AND new offer and it wins, you don't know which change mattered.

**Testing discipline:**
- One variable per test (hook, format, offer, or angle)
- Same audience across variants
- Same campaign structure, same budget allocation
- Minimum 7 days runtime (to smooth day-of-week variance)
- Statistical significance check before declaring a winner

---

## THE 4 VARIABLES TO TEST

### 1. HOOK (first 3 seconds / headline)
The opener that decides whether someone stops scrolling or keeps going.

**Hook formats to test:**
- Question hook: "Are you tired of [pain point]?"
- Statement hook: "This is why [product] sold out 3 times."
- Curiosity hook: "I didn't believe this worked until..."
- Stat hook: "85% of customers reorder within 30 days."
- Contrarian hook: "Everyone tells you to [X]. That's why it doesn't work."
- UGC hook: "Real customer unboxing [product]" (raw format)
- POV hook: "POV: You finally found [thing]"

**Metric to measure:** 3-second video view rate (hook rate) or CTR

### 2. FORMAT
How the message is delivered visually.

**Formats to test:**
- Single image vs carousel
- Static vs video
- Short video (6-15 sec) vs long video (30-60 sec)
- UGC style vs produced
- Text-heavy graphic vs product-focused
- Product demo vs lifestyle
- Before/after vs results-focused

**Metric to measure:** CTR, engagement rate, video completion rate

### 3. OFFER / ANGLE
The core promise or angle of attack.

**Angles to test:**
- Feature angle (what it does)
- Benefit angle (what you get)
- Social proof angle (what others say)
- Risk reversal angle (guarantee, free trial)
- Scarcity angle (limited time/quantity)
- Urgency angle (sale ends soon)
- Problem-agitation-solution angle

**Metric to measure:** Conversion rate, ROAS

### 4. CTA
What action you're asking for.

**CTAs to test:**
- "Shop Now" vs "Learn More"
- "Get Yours" vs "Buy Now"
- "See Results" vs "Try Free"
- Specific ("Get the 20% discount") vs generic ("Shop Now")

**Metric to measure:** CTR, CVR

---

## TEST DESIGN WORKFLOW

### Step 1: Define the Test
```
Test Name: Hook Test — Question vs Statement (Product Name)
Hypothesis: Question hooks will get 20%+ higher CTR than statement hooks for cold prospecting audiences
Variable: Hook format
Constants: Same audience (LAL 1% purchasers), same format (15-sec UGC video), same offer (15% off), same CTA ("Shop Now")
Variants:
  A: "Are you still using [old way]? Here's why [product] is different."
  B: "[Product] is the only [category] that [unique promise]."
Primary metric: CTR
Secondary metrics: Hook rate, CVR, ROAS
Minimum runtime: 7 days
Minimum data: 10,000 impressions per variant OR 50 conversions per variant
```

### Step 2: Launch
Use `meta-ads-api` or `google-ads-api` to create both variants:
- Same campaign objective
- Same ad set / ad group
- Same audience
- Same schedule and budget
- Each variant as separate ad (Meta creates its own A/B test structure, or use Meta's built-in A/B test tool)

### Step 3: Monitor
Do **NOT** check results daily. Creative tests need runtime — day-1 data lies.

Minimum check-in cadence:
- **Day 7:** First real look
- **Day 14:** Statistical significance check
- **Day 21:** Hard call — winner or kill

### Step 4: Score the Winner

Use `growth-engine` skill for statistical analysis, OR apply these rules:

**Declaration criteria (all must be true):**
- Primary metric difference > 15% lift
- Minimum data threshold hit (10K impressions OR 50 conversions per variant)
- Effect is consistent across days 4-14 (not just first 3 days)
- Secondary metrics don't contradict (e.g., high CTR but no conversions = not a winner)

**If inconclusive after 21 days:**
- Effect is real but small → not worth scaling unless other gains
- OR variants are essentially the same → use either, move on
- OR audience is too small/variable → retest with different audience

### Step 5: Promote to Playbook
Winning hooks/formats/angles get added to the **Creative Playbook** (use `growth-engine` skill to track).

Future creative briefs reference the playbook. No one re-tests what's already proven — unless we're suspicious of fatigue.

---

## CREATIVE VOLUME TARGETS

Healthy accounts have consistent creative velocity. Rough targets by spend level:

| Monthly Spend | Creative Velocity |
|---------------|------------------|
| <$5K/month | 4–6 new creatives/month |
| $5K–$25K/month | 10–15 new creatives/month |
| $25K–$100K/month | 20–30 new creatives/month |
| $100K+/month | 40+ new creatives/month |

Without this velocity, you're not testing enough to stay ahead of fatigue.

---

## TEST PRIORITIZATION MATRIX

When you have 10 test ideas but budget for 3 — which to run first?

| Test | Impact (1-10) | Confidence (1-10) | Ease (1-10) | Score |
|------|---------------|-------------------|-------------|-------|
| Hook A/B | 8 | 9 | 9 | 648 |
| New offer | 10 | 5 | 3 | 150 |
| Format change | 6 | 7 | 6 | 252 |

Score = Impact × Confidence × Ease. Run the highest score first.

---

## COMMON MISTAKES TO AVOID

1. **Testing multiple variables** — Meta's "Dynamic Creative" is fine for scale, but for LEARNING what works you need isolated variables
2. **Killing tests too early** — Day 3 "winners" often flip by day 14
3. **Testing tiny differences** — "Shop Now" vs "Buy Now" usually isn't worth the test slots; test bigger swings
4. **Not tracking the playbook** — winning patterns forgotten within a month = you're retesting things you already solved
5. **Same audience for all tests** — cold vs warm audiences respond to different creative. Test on the audience you intend to scale to.

---

## TEST LOGGING TEMPLATE

Every completed test should be logged:

```
## Test Log: [Test Name]
**Run dates:** [Start] → [End]
**Account:** [Client]
**Audience:** [Name]
**Spend:** $[total across variants]
**Hypothesis:** [what we expected]
**Winner:** [A / B / Inconclusive]
**Primary metric result:**
  - Variant A: [value]
  - Variant B: [value]
  - Lift: [%]
  - Statistical significance: [Yes/No, p-value]
**Secondary metric results:** [list]
**Learnings:** [1-2 sentences about what this teaches us]
**Playbook update:** [what gets added to the living playbook]
**Next test queued:** [what to test next]
```

---

## NOTES
- This skill handles test design and winner analysis, not creative production — use `creative-specialist` for that
- For statistical analysis of larger experiments → use `growth-engine` skill
- For writing the actual ad copy → use `content-ops` for quality scoring
- Meta's built-in A/B Test tool works well for single-variable Meta tests
- Google Ads RSA "Ad Strength" is not an A/B test — it's Google's optimization algorithm. Run explicit tests separately.

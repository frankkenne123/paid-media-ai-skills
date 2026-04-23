---
name: media_buyer
description: "Media Buyer — use when making scaling, cutting, or bid strategy decisions for Meta and Google ad campaigns. Handles daily budget pacing checks, kill/scale rules, bid strategy recommendations, day-parting analysis, and end-of-day optimization routines. This is the 'what do we do next?' skill — it reads performance data and gives specific, rule-based tactical decisions. Works best combined with performance-analyst, meta-ads-api, and google-ads-api."
user-invocable: true
---

# Media Buyer — Scaling, Cutting, and Bid Decisions

Rule-based tactical decision-making for live ad accounts. Reads performance data and outputs specific actions: what to scale, what to cut, what bids to adjust, and what to fix.

**Philosophy:** Media buying is 80% applying consistent rules and 20% strategic judgment. This skill handles the 80% so you can focus on the 20%.

---

## DAILY ROUTINE (MORNING CHECK — 9 AM)

Run this every morning for each live account:

### 1. Yesterday's Performance Snapshot
Pull from `performance-analyst`: yesterday spend, revenue, ROAS per campaign.

**Flags:**
- 🔴 **Spend >120% of daily budget** — check for pacing anomaly or audience exhaustion
- 🔴 **ROAS <1.5x on campaigns spending >$500** — review immediately
- 🟡 **CTR dropped >25% vs 7-day average** — creative fatigue warning
- 🟢 **ROAS >2x target AND spend underpacing** — scale candidate

### 2. Pacing Check
If today is day N of month, and the account should spend $X/month:
- Expected cumulative spend by now = (N / days_in_month) × $X
- Actual cumulative spend vs expected

**Decision:**
- Over-pacing by >15% → reduce daily budgets 10–20%
- Under-pacing by >15% → increase daily budgets on proven winners only
- On pace ±15% → no changes, continue monitoring

### 3. Kill / Scale List
Output today's action list:

```
## DAILY ACTION LIST — [DATE]

### SCALE (increase budget 20–30%)
- Campaign: [Name] | ROAS: 4.2x (target 3x) | Spend: $450/day | NEW BUDGET: $550

### CUT (pause immediately)
- Campaign: [Name] | ROAS: 0.8x over 7 days | Spend: $250/day wasted
- Ad Set: [Name] | Frequency 5.2 + CTR dropped 40% | Fatigued

### FIX (needs attention)
- Campaign: [Name] | Pixel events dropped 50% | Check tracking

### TEST (next creative/audience queue)
- Launch new creative variant for [Campaign] — current best ROAS leader
```

---

## SCALING RULES

### The 20/20/3 Scaling Rule (Meta)

**Scale a Meta ad set if ALL are true:**
- ROAS is 20%+ above target for 3+ consecutive days
- Spend is consistently 20%+ under daily budget (meaning room to grow)
- Frequency is under 3.0 (audience not saturated)

**How much to scale:**
- First scale: +20% daily budget
- Wait 3 days, evaluate
- If ROAS holds, scale +30% next time
- Never scale >50% in a single move — triggers re-learning phase

### The 50% Day Scaling Rule (Google Ads)

For Google Search/Shopping/PMax:
- If campaign is hitting target ROAS/CPA and spend <50% of available impression share, increase budget 30–50%
- Monitor Search Impression Share: if >70% already, budget increases have diminishing returns — test new ad groups/keywords instead

### Horizontal Scaling (Audience / Creative)

Instead of scaling budget on a proven winner, **duplicate the ad set** with:
- Different audience (expand lookalike % or try new interest)
- Same creative (confirm creative is the winner, not audience)
- OR same audience with fresh creative (confirm audience is winner)

This preserves the learning phase and gives 2× the data.

---

## KILL RULES

### Immediate Pause (no exceptions)
- Campaign spend >$500 in 7 days with <0.5x ROAS
- Ad set frequency >5.0 with declining CTR (fully fatigued)
- Policy violation or account warning
- Landing page broken / 404 / slow (>8 sec load)

### Review Before Pausing (talk to client first)
- ROAS 0.8–1.5x on spend <$500 — might still be in learning phase
- Low ROAS but high add-to-cart rate — attribution issue or checkout problem, not ad problem
- Branded search underperforming — might be stolen by aggregators; investigate before cutting

### Never Pause These
- Branded Google Search (defensive — protect your brand from competitors bidding)
- Retargeting/DPA campaigns (even low ROAS captures late-funnel buyers)
- Evergreen best-seller Shopping feed (reliable profit driver)

---

## BID STRATEGY DECISION TREE

### Meta
| Situation | Recommended Bid Strategy |
|-----------|--------------------------|
| New campaign, unknown performance | Highest Volume (lowest cost) |
| Proven product, known CPA target | Cost Cap at target CPA |
| Scaling aggressively, tolerate higher CPA | Bid Cap slightly above target |
| Protecting margin | Minimum ROAS (set ROAS goal) |

### Google Ads
| Situation | Bid Strategy |
|-----------|--------------|
| New Search campaign | Maximize Conversions (let AI learn) |
| After 30 conversions collected | Target CPA or Target ROAS |
| Shopping / PMax | Maximize Conversion Value + Target ROAS |
| Top-of-funnel video | Target CPV or CPM |

---

## DAY-PARTING RULES

**When to recommend day-parting (restricting ad delivery by hour):**
- Account has 30+ days of hourly data
- Clear pattern: certain hours have <50% of daytime ROAS for 14+ days
- Spend outside best hours is significant (>20% of daily)

**When NOT to day-part:**
- Account has <30 days of data (you'll miss opportunity hours)
- Low total daily spend (<$100) — not enough volume to judge
- Already using Target ROAS bidding (algorithm handles this)

---

## BUDGET ALLOCATION RULES

For accounts with multiple campaigns:

**70/20/10 Rule (default):**
- 70% to proven winners (ROAS >target for 30+ days)
- 20% to scaling tests (ROAS 80–100% of target, being optimized)
- 10% to new creative/audience tests (pure experiment)

Never go 100% on winners — your creative WILL fatigue, and you'll have nothing in the pipeline.

---

## CREATIVE REFRESH TRIGGERS

Rotate creative when ANY two conditions hit:
- Frequency >3.5 AND CTR down 25% from launch
- CPM up >40% from launch (audience saturation)
- Campaign has spent >$5000 lifetime
- 14+ days since creative launch and spend is slowing

Use `creative-testing` skill for next-variant planning.

---

## ALERT CONDITIONS (FLAG TO HUMAN)

Flag these for immediate client conversation:
- ROAS dropped >40% week-over-week on a top-3 spender
- Pixel/conversion events dropped >30% in 24 hours
- Account suspended or disapproved ads
- Unusual spend spike (>200% of average daily)
- Competitive ad activity detected in ad library (competitor launched large campaign)

---

## WEEKLY REPORTING OUTPUT

End of each week, generate:
```
## Weekly Media Buying Report — [Client Name] — Week of [DATE]

**Spend this week:** $X (vs $Y target — Z% variance)
**Revenue this week:** $X
**Blended ROAS:** X.Xx

### Top Performers
- [Campaign]: Xx ROAS, $X spent — RECOMMENDATION: Scale 25%

### Bottom Performers
- [Campaign]: Xx ROAS, $X spent — RECOMMENDATION: Pause and refresh creative

### Creative Fatigue Alerts
- [Ad]: Frequency 4.2, CTR -30% — CUEING new variant

### Week-Ahead Plan
- Scale: [list]
- Cut: [list]
- Test: [list]
- Fix: [list]
```

---

## NOTES
- Rules are starting points — adjust thresholds per client based on their margin, LTV, and risk tolerance
- NEVER auto-execute scale/cut decisions — output recommendations for human approval
- When in doubt, check `performance-analyst` data before making recommendations
- For creative production and testing → use `creative-specialist` and `creative-testing` skills

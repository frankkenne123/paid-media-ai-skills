---
name: client_reporter
description: "Client Reporter — use when generating weekly or monthly performance reports for paid media clients. Aggregates data from Meta, Google, GA4, and Shopify into clear executive summaries with traffic-light health status, wins, losses, and recommended actions. Designed to be read by busy founders/CMOs in under 5 minutes — not a data dump, but a decision doc."
user-invocable: true
---

# Client Reporter

Generate clear, action-oriented weekly and monthly performance reports for paid media clients. Designed to be read in under 5 minutes by founders and CMOs who want answers, not spreadsheets.

**Philosophy:** Clients don't want to see every metric — they want to know: Are we on track? What's winning? What's broken? What's next?

---

## REPORT PRINCIPLES

1. **Lead with the headline** — one sentence that captures the week: "Strong week — spend up, ROAS steady at 3.2x, on pace for $85K revenue month."
2. **Traffic lights** — 🟢🟡🔴 at the top of each section so client can skim
3. **Insight, not data** — don't say "spend was $6,000." Say "spend up 12% w/w, all on winning campaigns."
4. **Next actions stated** — every report ends with "what we're doing next."
5. **Under 5 minutes to read** — no 12-page decks. 1-page summary + appendix for details.

---

## WEEKLY REPORT TEMPLATE

```
# [Client Name] — Weekly Paid Media Report
## Week of [Start Date] → [End Date]

---

## 🎯 HEADLINE
[One sentence summary of the week]

---

## 📊 THE NUMBERS [🟢/🟡/🔴]

| Metric | This Week | Last Week | Change |
|--------|-----------|-----------|--------|
| Spend | $X | $Y | +/- Z% |
| Revenue | $X | $Y | +/- Z% |
| ROAS | X.Xx | X.Xx | +/- Z% |
| Orders | X | Y | +/- Z% |
| AOV | $X | $Y | +/- Z% |

**Target ROAS:** [X.Xx] — **Status:** [🟢 On target / 🟡 Close / 🔴 Below]

---

## 🔥 WINS THIS WEEK
- [Specific win with numbers]: e.g., "Scaled [Campaign] 30% — ROAS held at 4.2x, generated $8K additional revenue"
- [Win]: e.g., "New UGC creative launched, already at 3.8x ROAS vs account avg 3.1x"

---

## ⚠️ CHALLENGES
- [Issue with context]: e.g., "Prospecting campaigns dropped to 1.8x ROAS — likely creative fatigue on top ad, refreshing next week"
- [Issue]: e.g., "Shopify revenue 15% lower than Meta-reported — investigating pixel"

---

## 🧪 WHAT WE TESTED
- [Test name]: Result — [Winner / Running / Inconclusive]
- [Test name]: Result

---

## 📋 WHAT WE'RE DOING NEXT WEEK
1. [Specific action]: e.g., "Launch 3 new UGC creatives in [Campaign]"
2. [Action]: e.g., "Audit Google Shopping feed — 40% of SKUs underperforming"
3. [Action]: e.g., "Test Target ROAS bidding on [Campaign] — currently on Max Conv"

---

## 📎 APPENDIX (optional — details available on request)
- Campaign-by-campaign breakdown
- Creative performance details
- Ad set / ad group drill-down
- Full attribution comparison (Meta vs GA4 vs Shopify)
```

---

## MONTHLY REPORT TEMPLATE

Monthly reports are slightly longer — they include trends, MoM comparison, and strategic recommendations.

```
# [Client Name] — Monthly Paid Media Report
## [Month Year]

---

## 🎯 EXECUTIVE SUMMARY
[3-4 sentences: overall performance, biggest win, biggest challenge, strategic direction]

---

## 📊 MONTH IN NUMBERS [🟢/🟡/🔴]

| Metric | This Month | Last Month | 3-Mo Avg | Target |
|--------|-----------|------------|----------|--------|
| Spend | $X | $Y | $Z | $T |
| Revenue | $X | $Y | $Z | $T |
| ROAS | X.Xx | X.Xx | X.Xx | X.Xx |
| New Customers | X | Y | Z | T |
| Returning Customer Rate | X% | Y% | Z% | - |

---

## 📈 TREND CHART
[ASCII chart or description: spend and revenue over 90 days]

---

## 🏆 TOP 3 MOVES THAT WORKED
1. [Specific decision] → [Outcome with numbers]
2. [Decision] → [Outcome]
3. [Decision] → [Outcome]

## 🔍 TOP 3 ISSUES IDENTIFIED
1. [Problem] → [How we're fixing it]
2. [Problem] → [How we're fixing it]
3. [Problem] → [How we're fixing it]

---

## 🧪 CREATIVE LEARNINGS THIS MONTH

**Winning Hook Themes:**
- [Theme]: Avg ROAS X.Xx
- [Theme]: Avg ROAS X.Xx

**Winning Formats:**
- UGC video > produced video (40% better ROAS)
- Short (<15 sec) > long video

**Playbook Updates:**
- [New rule added to creative playbook]

---

## 🎯 NEXT MONTH — STRATEGIC FOCUS

1. [Big bet for next month]
2. [Second priority]
3. [Third priority]

### Budget Recommendation
- Current monthly: $X
- Proposed next month: $Y [+/- Z%]
- Rationale: [why this allocation]

---

## 📎 APPENDIX
[Full campaign breakdown, creative library, attribution audit]
```

---

## HEALTH SCORING RUBRIC

Assign a status to each major metric for the traffic lights:

### ROAS Status
- 🟢 **Green:** ROAS ≥ target for 4+ weeks consistently
- 🟡 **Yellow:** ROAS within 20% of target, mixed performance
- 🔴 **Red:** ROAS <80% of target for 2+ weeks

### Spend Pacing
- 🟢 **Green:** On pace (±10% of target spend)
- 🟡 **Yellow:** Under-pacing or over-pacing 10-20%
- 🔴 **Red:** >20% variance with no plan to fix

### Creative Health
- 🟢 **Green:** Fresh creative added each week, no fatigue signals
- 🟡 **Yellow:** 1–2 ads showing fatigue, new creative queued
- 🔴 **Red:** Multiple ads fatigued, no new creative in pipeline

### Attribution Health
- 🟢 **Green:** Meta/GA4/Shopify within 15% of each other
- 🟡 **Yellow:** 15–30% gap, investigating
- 🔴 **Red:** >30% gap — tracking likely broken

---

## WORKFLOW: GENERATING A REPORT

### Step 1: Pull Data
Use these skills in sequence:
1. `performance-analyst` — Aggregate Meta + Google data
2. `meta-ads-api` — Specific campaign/ad-level breakdowns
3. `google-ads-api` — Specific campaign data
4. `shopify-integration` — Actual revenue and order data
5. `ga4-integration` — Landing page / attribution check

### Step 2: Identify Headline
Ask: "What's the single most important thing the client should know about this week/month?"

That's the headline. Not "spend was $6,000." Instead: "Strong week — best ROAS month-to-date, driven by new UGC creative."

### Step 3: Traffic-Light Each Section
Assign status using rubric above. Be honest — if ROAS is red, say it's red. Clients respect honesty more than spin.

### Step 4: Write Wins and Challenges
- 2–4 wins with specific numbers
- 2–4 challenges with what you're doing about each

### Step 5: Write "What's Next"
Always end with 3-5 specific actions for the coming week/month. Not vague goals ("improve performance") — specific actions ("launch 3 new UGC creatives in Campaign A").

### Step 6: Keep the Appendix Optional
Don't force clients to scroll through 10 pages of tables. Offer appendix data on request.

---

## TONE RULES

- **Active voice** — "We scaled X" not "X was scaled"
- **Specific over vague** — "ROAS up 12%" not "performance improved"
- **Own the losses** — "I paused this creative too early" beats "creative didn't perform as expected"
- **Next-step oriented** — every problem mentioned should have a "what we're doing about it"
- **No jargon for jargon's sake** — if you have to say "CPM," explain why it matters

---

## NOTES
- Weekly reports go out Monday or Tuesday — clients want them at the start of the week
- Monthly reports go out by day 3 of the new month
- If numbers are bad, send the report EARLIER, not later. Bad news should arrive fast with a plan.
- For clients who read nothing — send a 3-sentence Slack/Loom summary: "Week was green. ROAS 3.4x. Scaling Campaign A, refreshing creative on Campaign B."

---
name: growth_engine
description: "Autonomous marketing experiment engine — use when running A/B tests on ad creative, email subject lines, landing pages, outreach copy, or any marketing variable. Tracks experiments with real statistical rigor (bootstrap CI + Mann-Whitney U), auto-promotes winners to a living playbook, and generates weekly scorecards. Use for your own agency marketing AND for client campaigns. Triggers on: 'run experiment', 'A/B test', 'test this', 'what's performing', 'weekly scorecard', 'what should we test next', 'growth playbook', 'experiment results'."
user-invocable: true
---

# Growth Engine — Autonomous Experiment Tracker

Track marketing experiments with real statistical rigor. Hypothesize, measure, score, promote winners to a living playbook, and suggest what to test next.

Inspired by Andrej Karpathy's autoresearch pattern applied to marketing. Adapted from Eric Siu's ai-marketing-skills growth-engine.

---

## WHEN TO USE

Use this skill when:
- Creating or managing A/B or multivariate experiments for any marketing channel
- Logging experiment data points after content is published or campaigns run
- Scoring experiments to determine statistical winners
- Checking the playbook for proven best practices before creating new content
- Generating weekly scorecards across all channels
- Monitoring campaign pacing and health

**Do NOT use for:**
- One-off content creation (use the playbook output as input, but don't run the engine)
- Non-experiment analytics (use `performance_analyst` skill)
- Campaign setup in external platforms (this tracks experiments, doesn't configure them)

---

## STARTING AN EXPERIMENT

Tell me:
1. **What are you testing?** (the variable — e.g., "subject line style", "ad hook format", "CTA text")
2. **What's the hypothesis?** (e.g., "question hooks get higher open rates than statement hooks")
3. **What are the variants?** (e.g., A = question hook, B = statement hook, C = curiosity gap)
4. **What metric are you measuring?** (open rate, CTR, reply rate, ROAS, CVR, etc.)
5. **Which channel?** (email, LinkedIn, Meta ads, Google ads, landing page, etc.)

---

## EXPERIMENT WORKFLOW

```
1. HYPOTHESIZE  → Define variable, variants, metric, success threshold
2. PUBLISH      → Log which variant went live and when
3. COLLECT      → Log data points as results come in
4. SCORE        → Statistical analysis when minimum data collected
5. DECIDE       → Keep (winner → playbook) or Discard
6. SUGGEST      → What to test next based on learnings
```

---

## STATISTICAL RIGOR

**Minimum data requirements:**
- High-volume channels (email, ads): 10+ data points per variant before scoring
- Low-volume channels (LinkedIn, SEO, blog): 30+ data points per variant

**Winner criteria:** p-value < 0.05 AND at least 15% lift over control

**Status flow:** `running` → `trending` (p < 0.10) → `keep` or `discard`

Always report confidence intervals, not just point estimates. "Variant A is winning with 95% confidence" is meaningful. "Variant A looks better" is not.

---

## THE LIVING PLAYBOOK

Winners auto-promote to your marketing playbook. The playbook is the source of truth for "what works."

**Always check the playbook before writing new copy or creative briefs.**

Organize by channel:
- `email` — subject line rules, first sentence patterns, CTA formats, send time
- `linkedin` — connection request formats, message sequence structure
- `meta_ads` — hook formats, creative types, offer angles, copy length
- `google_ads` — headline patterns, description rules, extension types
- `landing_pages` — above-fold copy, CTA placement, social proof positioning

---

## WEEKLY SCORECARD FORMAT

Generate every Monday:

```
## Growth Scorecard — Week of [DATE]

### This Week's Wins
- [Experiment]: [Variant] won with [X]% lift → added to playbook

### Active Experiments
| Experiment | Channel | Status | Data Points | Trending |
|------------|---------|--------|-------------|---------|
| [name] | [channel] | running | X/10 | [yes/no] |

### Playbook Updates This Week
- [New rule added based on recent winner]

### Suggested Next Tests
1. [Test idea based on what we've learned]
2. [Test idea]

### Pacing Alerts
- [Any campaigns off-track vs. targets]
```

---

## PACING ALERTS

Flag when:
- A campaign is spending but not hitting KPI targets (ROAS, CPL, open rate)
- Metrics drop >20% week-over-week
- An experiment has been running 3+ weeks with no statistical conclusion (may need more data or the effect is too small to matter)

---

## CONFIGURATION

Set these for your business context:

| Variable | Description | Default |
|----------|-------------|---------|
| Channels | What channels you're running experiments on | `email, linkedin, meta_ads, google_ads` |
| Win threshold | Minimum lift % to declare a winner | 15% |
| P-value threshold | Statistical significance | 0.05 |
| High-volume minimum | Samples needed for fast channels | 10/variant |
| Low-volume minimum | Samples needed for slow channels | 30/variant |

---

## NOTES
- This tracks experiments — it does not set up campaigns in external platforms
- Experiments need to run their full cycle — don't call winners on day 2
- One variable per experiment — don't test the hook AND the CTA at the same time
- Source: Adapted from Eric Siu's ai-marketing-skills growth-engine (github.com/ericosiu/ai-marketing-skills)

---
name: content_ops
description: "Expert panel content scoring — use when you need to score, evaluate, or improve any content before it goes out. Auto-assembles a panel of 7–10 domain experts, scores recursively until it hits 90+, and delivers the final version with full scoring history. Use for: ad copy, cold emails, LinkedIn posts, proposals, client reports, landing page copy, case studies, or any content that needs a quality gate. Triggers on: 'expert panel this', 'score this', 'quality check', 'rate these variants', 'which version is better', 'panel review', 'is this good enough', 'score my copy'."
user-invocable: true
---

# Content Ops — Expert Panel

General-purpose content scoring and improvement engine. Auto-assembles the right experts for whatever you're evaluating, scores it honestly, and iterates until it hits 90+.

**Target: 90/100. Non-negotiable. Max 3 rounds.**

Inspired by Eric Siu's ai-marketing-skills content-ops (github.com/ericosiu/ai-marketing-skills).

---

## STEP 1: INTAKE

Provide:
1. **The content** — paste it, share a file, or describe it
2. **Content type** — cold email, ad copy, LinkedIn post, proposal, report, landing page, etc.
3. **Audience** — who will read this? (prospects, clients, general public)
4. **Variants** (if A/B) — I'll score each and pick the winner

If context is obvious, I'll proceed without asking.

---

## STEP 2: EXPERT PANEL ASSEMBLY

I auto-assemble 7–10 experts based on content type and audience.

**Always included:**
- **AI Writing Detector** (24-pattern human-writing scan — weighted 1.5x, non-negotiable)
- **Brand Voice** (does this match your established voice and tone?)

**Added by content type:**

| Content Type | Experts Added |
|---|---|
| Cold email / outreach | Deliverability Expert, Cold Email Copywriter, Persuasion Psychologist, Buyer Persona ("would I reply?") |
| Ad copy (Meta/Google) | Performance Creative Expert, Hook Specialist, CTA Optimizer, Target Customer POV |
| LinkedIn post | B2B Social Media Expert, Thought Leadership Strategist, Engagement Optimizer |
| Proposal / pitch | Sales Strategist, Client Psychology Expert, Value & Pricing Expert |
| Client report | Data Storytelling Expert, Executive Communication Expert |
| Landing page | CRO Specialist, UX Copywriter, Conversion Psychologist |
| Case study | Narrative Expert, Social Proof Optimizer, SEO Specialist |

---

## STEP 3: SCORING ROUNDS

Each round produces:

```
## Round [N] — Score: [AVG]/100

| Expert | Score | Key Feedback |
|--------|-------|--------------|
| [Name] | [0-100] | [One-line rationale] |
| ...    | ...   | ...          |

**Aggregate:** [weighted average — AI detector at 1.5x]
**Top 3 weaknesses:** [ranked list]
**Changes made:** [specific edits addressing each weakness]
```

Then the revised content below.

**Rules:**
- Scores are brutally honest — no padding to reach 90
- AI Detector is weighted 1.5x in the aggregate
- If aggregate < 90: fix top 3 weaknesses, run next round
- If aggregate ≥ 90: done — deliver final version
- After 3 rounds at <90: deliver best version with honest score + note on what's holding it back
- **All rounds are shown in output** — the iteration history is proof of quality

---

## STEP 4: OUTPUT FORMAT

```
## Result: [SCORE]/100 — [PASS ✅ | NEEDS WORK ⚠️]

[Final content here]

**Iterations:** [N] rounds
**Panel:** [Expert names]
```

If scoring variants (A/B/C):
```
## Winner: Variant [X] — [SCORE]/100

[Winning content]

### Runner-up scores
- Variant A: 87/100
- Variant B: 91/100 ← Winner
- Variant C: 82/100
```

---

## STEP 5: LEARN FROM REJECTIONS

If you reject content that scored 90+ (overrides the panel):
1. I'll ask why (or infer from context)
2. I'll add a new rejection pattern to memory
3. Future scoring will automatically dock points for that pattern

The panel gets smarter over time — it learns what you actually approve.

---

## QUICK EXAMPLES

**"Score my cold email"** → paste it, get 90+ version back
**"Which subject line is better?"** → paste A/B, get winner with reasoning
**"Is this proposal ready to send?"** → paste it, get honest answer
**"Expert panel this ad copy"** → paste copy + what it's promoting, get scored and improved version

---

## NOTES
- This is a quality gate — bring your draft, it makes it better
- For generating content from scratch → use `creative_specialist` skill
- For full cold email campaign strategy → use `outbound_engine` skill (calls this skill internally for sequence scoring)

# Paid Media AI Skills

**Open-source AI agent skills for paid media teams and VPs of Paid Media.**

A complete stack for managing Meta, Google, and Shopify data — from direct API integrations to strategic decision-making. Built to run real client campaigns: account audits, scaling decisions, creative testing, client reporting, and attribution diagnostics.

Drop any skill into your Claude Code project or OpenClaw agent and it works.

---

## Skills

### 🔌 Platform Integrations
| Skill | What It Does |
|---|---|
| [meta-ads-api](./meta-ads-api/) | Meta Marketing API — campaigns, ad sets, ads, audiences, insights |
| [google-ads-api](./google-ads-api/) | Google Ads API — Search, Shopping, PMax, YouTube, Display |
| [shopify-integration](./shopify-integration/) | Shopify Admin API — revenue, orders, customers, LTV, attribution |
| [ga4-integration](./ga4-integration/) | Google Analytics 4 — traffic sources, landing pages, events, funnels |

### 📊 Analysis
| Skill | What It Does |
|---|---|
| [performance-analyst](./performance-analyst/) | Ad performance analysis across Google Ads and Meta Ads |
| [attribution-auditor](./attribution-auditor/) | Pixel health, UTM audit, Meta/Google/GA4/Shopify reconciliation |
| [competitive-intel](./competitive-intel/) | Meta Ad Library monitoring, competitor creative analysis |

### 🎯 Strategy & Execution
| Skill | What It Does |
|---|---|
| [media-buyer](./media-buyer/) | Scaling, cutting, and bid strategy decisions with rule-based logic |
| [account-auditor](./account-auditor/) | Full ad account audit — structure, targeting, creative, tracking |
| [creative-specialist](./creative-specialist/) | Ad creative strategy, testing frameworks, fatigue detection |
| [creative-testing](./creative-testing/) | Structured creative A/B testing — hook, format, offer, CTA |
| [cro-specialist](./cro-specialist/) | Landing page optimization for paid traffic |

### 📝 Reporting & Ops
| Skill | What It Does |
|---|---|
| [client-reporter](./client-reporter/) | Weekly and monthly performance reports with insights and actions |
| [growth-engine](./growth-engine/) | Experiment tracker with statistical rigor — promotes winners to a living playbook |
| [content-ops](./content-ops/) | Expert panel scoring — ad copy, subject lines, hooks to 90+ quality |

---

## How It Works

Every skill is a `SKILL.md` file. Your AI agent reads it and knows how to use the APIs and tools.

**Claude Code:**
```bash
git clone https://github.com/YOUR_USERNAME/paid-media-ai-skills.git
cp paid-media-ai-skills/meta-ads-api/SKILL.md .claude/skills/meta-ads-api.md
```

**OpenClaw:**
```bash
cp -r paid-media-ai-skills/meta-ads-api/ ~/.openclaw/workspace/skills/
```

Then ask your agent: *"How is [Client] Meta doing last 7 days?"* — it reads the skill and knows how to pull insights from the Meta Marketing API.

---

## Setup

Each skill that connects to an external API reads credentials from `.env`. Copy the example and fill in only what you need:

```bash
cp .env.example .env
```

You don't need every API key — only fill in credentials for the skills you use.

---

## The Skills Work Together

These aren't 15 isolated skills — they're designed as a stack:

```
                    ┌─────────────────────────────────────┐
                    │   meta-ads-api   google-ads-api     │
                    │   shopify-integration  ga4-integ.   │
                    └────────────────┬────────────────────┘
                                     │
                    ┌────────────────▼────────────────────┐
                    │   performance-analyst               │
                    │   attribution-auditor               │
                    │   competitive-intel                 │
                    └────────────────┬────────────────────┘
                                     │
                    ┌────────────────▼────────────────────┐
                    │   account-auditor                   │
                    │   media-buyer                       │
                    │   creative-specialist / testing     │
                    │   cro-specialist                    │
                    └────────────────┬────────────────────┘
                                     │
                    ┌────────────────▼────────────────────┐
                    │   client-reporter                   │
                    │   growth-engine                     │
                    │   content-ops                       │
                    └─────────────────────────────────────┘
```

**Example workflow — New Client Onboarding:**

1. `attribution-auditor` — first, make sure tracking is healthy (most clients have broken tracking)
2. `account-auditor` — full audit of Meta and Google accounts
3. `performance-analyst` — baseline the historical performance
4. `competitive-intel` — see what the category is doing
5. `media-buyer` — make first scaling/cutting decisions
6. `creative-testing` — queue the first structured tests
7. `client-reporter` — weekly report framework

---

## What Makes These Different

**Built for the real job of a VP of Paid Media.** Most AI marketing content is generic — "write an ad," "analyze this data." These skills are the actual workflows: weekly account routines, monthly client reports, attribution diagnostics, structured creative testing, full ad account audits.

**API-first.** Where other skills describe what to do, these connect directly to the APIs (Meta Marketing, Google Ads, Shopify Admin, GA4 Data API). Your agent doesn't just tell you what to do — it does it.

**Rule-based decisions.** The `media-buyer` skill has specific scaling rules (20/20/3, 50% Day), kill rules (kill if ROAS <0.5x on $500+ spend), and bid strategy decision trees. No hand-waving — concrete logic.

**Attribution-obsessed.** 4 of the 15 skills are about tracking and attribution because in 2026, the biggest lever in paid media isn't the creative — it's knowing what's actually working.

---

## Stack

Built to work with:
- **[Claude Code](https://claude.ai/code)** — Anthropic's AI coding agent
- **[OpenClaw](https://github.com/openclaw)** — Multi-agent framework
- Any agent that reads `SKILL.md` files

---

## Related

Looking for broader agency skills (CRM, cold email, domains, finance ops)? Check out the companion repo: [**agency-ai-skills**](https://github.com/frankkenne123/agency-ai-skills).

---

## Contributing

Found an improvement or built a new skill? PRs welcome.

1. Fork the repo
2. Create your skill folder with `SKILL.md`
3. Strip any credentials, client names, or personal data before committing
4. Open a PR with a short description

---

## License

MIT — use these however you want.

---

*Built by [Lion Media](https://lionmediaad.com) — a performance marketing agency for eCommerce brands.*

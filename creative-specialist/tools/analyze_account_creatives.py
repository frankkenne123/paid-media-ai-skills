#!/usr/bin/env python3
"""
Pull every active (and optionally recent-paused) ad from a Meta ad account along
with its copy, creative URL, and 30-day performance, in a format ready for
framework analysis. Output is markdown — your agent reads it, applies the
hook-framework taxonomy + fatigue thresholds from creative-specialist/SKILL.md,
and writes the audit recommendations.

Usage:
  python3 analyze_account_creatives.py --account act_XXXXXXXX
  python3 analyze_account_creatives.py --account act_XXXXXXXX --include-paused
  python3 analyze_account_creatives.py --account act_XXXXXXXX --output /tmp/<client>-audit.md
"""

import argparse, json, os, sys
from collections import defaultdict
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()
API = "https://graph.facebook.com/v20.0"
TOKEN = os.getenv("META_ACCESS_TOKEN")


def gget(path, **params):
    params["access_token"] = TOKEN
    try:
        r = requests.get(f"{API}{path}", params=params, timeout=30)
        return r.json()
    except Exception as e:
        return {"error": {"message": str(e)}}


def gget_paginated(path, **params):
    """Follow paging.next until exhausted (capped at 5 pages)."""
    params["access_token"] = TOKEN
    out, url = [], f"{API}{path}"
    for _ in range(5):
        r = requests.get(url, params=params, timeout=30).json()
        out.extend(r.get("data", []))
        nxt = (r.get("paging") or {}).get("next")
        if not nxt:
            break
        url, params = nxt, {}
    return out


def fetch_ads(account_id, include_paused):
    fields = (
        "id,name,status,effective_status,created_time,updated_time,"
        "adset_id,adset{name,daily_budget,lifetime_budget,targeting},"
        "campaign_id,campaign{name,objective},"
        "creative{id,name,object_story_spec{link_data{link,message,name,description,call_to_action,image_hash}},image_url,thumbnail_url}"
    )
    params = {"fields": fields, "limit": 50}
    if not include_paused:
        params["effective_status"] = '["ACTIVE"]'
    return gget_paginated(f"/{account_id}/ads", **params)


def fetch_insights(account_id):
    """Pull 30-day insights at the AD level keyed by ad_id."""
    fields = ("ad_id,ad_name,spend,impressions,clicks,ctr,cpc,cpm,frequency,"
              "actions,action_values,purchase_roas")
    rows = gget_paginated(
        f"/{account_id}/insights",
        date_preset="last_30d",
        level="ad",
        fields=fields,
        limit=200,
    )
    by_ad = {}
    for r in rows:
        ad_id = r.get("ad_id")
        if not ad_id:
            continue
        purchases = 0
        revenue = 0.0
        for a in r.get("actions") or []:
            if a.get("action_type") == "purchase":
                try: purchases = int(float(a.get("value", 0)))
                except Exception: purchases = 0
        for a in r.get("action_values") or []:
            if a.get("action_type") == "purchase":
                try: revenue = float(a.get("value", 0))
                except Exception: revenue = 0.0
        roas_list = r.get("purchase_roas") or []
        roas = float(roas_list[0]["value"]) if roas_list else 0.0
        by_ad[ad_id] = {
            "spend": float(r.get("spend") or 0),
            "impressions": int(r.get("impressions") or 0),
            "clicks": int(r.get("clicks") or 0),
            "ctr": float(r.get("ctr") or 0),
            "cpc": float(r.get("cpc") or 0),
            "cpm": float(r.get("cpm") or 0),
            "frequency": float(r.get("frequency") or 0),
            "purchases": purchases,
            "revenue": revenue,
            "roas": roas,
        }
    return by_ad


def fatigue_signals(ins):
    """Apply §5 thresholds — flag warning/critical signals.
    We don't have peak-CTR history here so we can't compute drop-from-peak;
    we use absolute thresholds + frequency + spend-vs-revenue as proxies."""
    flags = []
    if not ins:
        return ["no spend in last 30d (paused or never delivered)"]
    if ins["frequency"] >= 4.0:
        flags.append(f"⛔ frequency {ins['frequency']:.1f} (critical: ≥4.0)")
    elif ins["frequency"] >= 2.5:
        flags.append(f"⚠️ frequency {ins['frequency']:.1f} (warning: 2.5-3.5)")
    if ins["roas"] and ins["roas"] < 1.0 and ins["spend"] > 100:
        flags.append(f"⛔ ROAS {ins['roas']:.2f} on ${ins['spend']:.0f} spend (losing money)")
    elif ins["ctr"] < 0.8 and ins["impressions"] > 5000:
        flags.append(f"⚠️ CTR {ins['ctr']:.2f}% (low — typical Meta DTC is 1-3%)")
    if not flags:
        flags.append("✅ no critical signals")
    return flags


def compose_report(account_id, ads, insights):
    lines = []
    acct = gget(f"/{account_id}", fields="name,currency")
    name = acct.get("name", account_id)
    lines += [
        f"# Creative Audit — {name} (`{account_id}`)",
        "",
        f"_Generated {__import__('datetime').date.today().isoformat()}. 30-day performance window._",
        "",
        f"**Total ads pulled:** {len(ads)}",
    ]
    total_spend = sum(insights.get(a["id"], {}).get("spend", 0) for a in ads)
    total_revenue = sum(insights.get(a["id"], {}).get("revenue", 0) for a in ads)
    blended = (total_revenue / total_spend) if total_spend else 0
    lines += [
        f"**Aggregate 30-day spend:** ${total_spend:,.0f}",
        f"**Aggregate 30-day revenue:** ${total_revenue:,.0f}",
        f"**Blended ROAS:** {blended:.2f}x",
        "",
        "---",
        "",
        "## Per-ad detail",
        "",
        "_For each ad below, identify the **hook framework** "
        "(PAS / Before-After-Bridge / AIDA / Problem-Solution / Social Proof Lead / "
        "Scarcity / Curiosity), classify the **image style**, apply the **fatigue thresholds**, "
        "and recommend keep / refresh / kill. See `skills/creative-specialist/SKILL.md` §1, §3, §5._",
        "",
    ]

    # group by campaign for readability
    by_campaign = defaultdict(list)
    for ad in ads:
        camp = (ad.get("campaign") or {}).get("name") or ad.get("campaign_id") or "(unknown campaign)"
        by_campaign[camp].append(ad)

    for camp, camp_ads in sorted(by_campaign.items()):
        lines += [f"### Campaign: {camp}", ""]
        for ad in camp_ads:
            ins = insights.get(ad["id"], {})
            creative = ad.get("creative") or {}
            spec = ((creative.get("object_story_spec") or {}).get("link_data") or {})
            cta = (spec.get("call_to_action") or {}).get("type") or "—"

            lines += [
                f"#### `{ad['id']}` — {ad['name']}",
                f"- **Status:** {ad.get('effective_status', '—')} · **Ad Set:** {(ad.get('adset') or {}).get('name', '—')}",
            ]
            if spec.get("link"):
                lines.append(f"- **Landing URL:** {spec['link']}")
            if spec.get("name"):
                lines.append(f"- **Headline:** _{spec['name']}_")
            if spec.get("description"):
                lines.append(f"- **Description:** {spec['description']}")
            lines.append(f"- **CTA:** `{cta}`")
            if msg := spec.get("message"):
                lines.append("- **Primary text:**")
                preview = msg if len(msg) <= 600 else msg[:600] + "…"
                for ln in preview.split("\n"):
                    if ln.strip():
                        lines.append(f"  > {ln}")
            else:
                lines.append("- **Primary text:** _(not link_data — possibly video ad or post; check creative ID directly)_")

            if ins:
                lines.append(
                    f"- **30d:** spend ${ins['spend']:,.0f} · "
                    f"impr {ins['impressions']:,} · "
                    f"CTR {ins['ctr']:.2f}% · "
                    f"CPM ${ins['cpm']:.2f} · "
                    f"freq {ins['frequency']:.2f} · "
                    f"purchases {ins['purchases']} · "
                    f"revenue ${ins['revenue']:,.0f} · "
                    f"ROAS **{ins['roas']:.2f}x**"
                )
            else:
                lines.append("- **30d:** _no impressions in window_")
            for f in fatigue_signals(ins):
                lines.append(f"- {f}")

            if creative.get("thumbnail_url"):
                lines.append(f"- **Image:** {creative['thumbnail_url']}")

            lines += [
                "",
                "**Analysis:**",
                "- Hook framework: _____",
                "- Image style: _____",
                "- Recommendation: ☐ keep · ☐ refresh ☐ kill — because _____",
                "",
            ]
        lines.append("")

    lines += [
        "---",
        "",
        "## Audit summary (fill in after per-ad analysis)",
        "",
        "**Hook framework distribution:**",
        "- PAS: __ ads · Before-After-Bridge: __ · AIDA: __ · Problem-Solution: __ · Social-Proof Lead: __ · Scarcity: __ · Curiosity: __ · No clear framework: __",
        "",
        "**What's working (keep + scale):**",
        "- ",
        "",
        "**What's fatigued (refresh):**",
        "- ",
        "",
        "**What's losing money (kill):**",
        "- ",
        "",
        "**Gaps in current creative (frameworks NOT being tested):**",
        "- ",
        "",
        "**Recommended next 3 builds:**",
        "1. ",
        "2. ",
        "3. ",
        "",
    ]
    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--account", required=True)
    p.add_argument("--include-paused", action="store_true",
                   help="Include paused ads (default: active only)")
    p.add_argument("--output", help="Save markdown to this path. Default: print to stdout.")
    args = p.parse_args()

    if not TOKEN:
        print("❌ META_ACCESS_TOKEN missing in .env", file=sys.stderr)
        sys.exit(1)

    print(f"→ pulling ads for {args.account}", file=sys.stderr)
    ads = fetch_ads(args.account, args.include_paused)
    print(f"  found {len(ads)} ads", file=sys.stderr)
    print(f"→ pulling 30-day insights", file=sys.stderr)
    insights = fetch_insights(args.account)
    print(f"  insights for {len(insights)} ads with delivery", file=sys.stderr)
    md = compose_report(args.account, ads, insights)
    if args.output:
        Path(args.output).write_text(md)
        print(f"✓ {args.output}", file=sys.stderr)
    else:
        print(md)


if __name__ == "__main__":
    main()

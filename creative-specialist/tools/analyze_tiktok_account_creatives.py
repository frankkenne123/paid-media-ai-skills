#!/usr/bin/env python3
"""
Pull every active TikTok ad with copy, video reference, and performance,
formatted as a markdown audit worksheet for framework analysis.

Mirrors analyze_account_creatives.py (Meta) and analyze_google_account_creatives.py
(Google) — same hook framework taxonomy + fatigue thresholds, applied to TikTok.

Usage:
  python3 analyze_tiktok_account_creatives.py
  python3 analyze_tiktok_account_creatives.py --advertiser-id 7401234567890123 \
    --output /tmp/<client>-tiktok-audit.md
  python3 analyze_tiktok_account_creatives.py --include-paused --range last_14d

Date ranges: last_3d | last_7d | last_14d | last_30d | this_month | last_month

Required .env keys:
  TIKTOK_ACCESS_TOKEN
  TIKTOK_ADVERTISER_ID  (or pass --advertiser-id)
"""

import argparse, datetime as dt, json, os, sys
from collections import defaultdict
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()
API = "https://business-api.tiktok.com/open_api/v1.3"
TOKEN = os.getenv("TIKTOK_ACCESS_TOKEN")


def headers():
    return {"Access-Token": TOKEN, "Content-Type": "application/json"}


def call(path, params=None, method="GET"):
    url = f"{API}{path}"
    if method == "GET":
        r = requests.get(url, headers=headers(), params=params, timeout=60)
    else:
        r = requests.post(url, headers=headers(), json=params, timeout=60)
    if r.status_code != 200:
        sys.exit(f"❌ HTTP {r.status_code} on {method} {path}\n{r.text}")
    body = r.json()
    if body.get("code") != 0:
        sys.exit(f"❌ TikTok API error on {path}: code={body.get('code')} msg={body.get('message')}\n"
                 f"{json.dumps(body, indent=2)}")
    return body.get("data") or {}


def list_ads(advertiser_id, include_paused):
    """Pull every ad with copy + creative refs."""
    out = []
    page = 1
    filtering = {"primary_status": "STATUS_DELIVERY_OK"} if not include_paused else {}
    while True:
        data = call("/ad/get/", params={
            "advertiser_id": advertiser_id,
            "page": page,
            "page_size": 50,
            "filtering": json.dumps(filtering),
            "fields": json.dumps([
                "ad_id", "ad_name", "campaign_id", "campaign_name",
                "adgroup_id", "adgroup_name",
                "ad_text", "video_id", "image_ids",
                "call_to_action", "landing_page_url",
                "operation_status", "ad_format",
                "create_time", "modify_time",
            ]),
        })
        ads = data.get("list", [])
        out.extend(ads)
        info = data.get("page_info", {})
        if info.get("page", page) >= info.get("total_page", 1):
            break
        page += 1
        if page > 20:  # safety
            break
    return out


def get_metrics(advertiser_id, ad_ids, date_range):
    """Pull 30-day (or chosen window) metrics keyed by ad_id."""
    if not ad_ids:
        return {}

    # TikTok report API
    metrics = [
        "spend", "impressions", "clicks", "ctr", "cpc", "cpm",
        "conversion", "conversion_rate", "cost_per_conversion",
        "video_play_actions", "video_watched_2s", "video_watched_6s",
        "video_views_p25", "video_views_p50", "video_views_p75", "video_views_p100",
    ]
    by_ad = {}
    # batch ad_ids in groups of 100
    for chunk_start in range(0, len(ad_ids), 100):
        chunk = ad_ids[chunk_start:chunk_start + 100]
        data = call("/report/integrated/get/", params={
            "advertiser_id": advertiser_id,
            "report_type": "BASIC",
            "data_level": "AUCTION_AD",
            "dimensions": json.dumps(["ad_id"]),
            "metrics": json.dumps(metrics),
            "filtering": json.dumps([
                {"field_name": "ad_ids", "filter_type": "IN", "filter_value": json.dumps(chunk)}
            ]),
            "date_range": date_range if date_range not in (
                "last_3d", "last_7d", "last_14d", "last_30d", "this_month", "last_month"
            ) else None,
            "data_range": date_range if date_range in (
                "last_3d", "last_7d", "last_14d", "last_30d", "this_month", "last_month"
            ) else None,
            "page_size": 1000,
        })
        for row in data.get("list", []):
            ad_id = (row.get("dimensions") or {}).get("ad_id")
            if ad_id:
                by_ad[ad_id] = row.get("metrics", {})
    return by_ad


def fatigue_signals(m):
    flags = []
    spend = float(m.get("spend") or 0)
    if not spend:
        flags.append("no spend in window (paused or new)")
        return flags
    impressions = int(float(m.get("impressions") or 0))
    ctr = float(m.get("ctr") or 0)  # already a percentage in TikTok API (0-100)
    conversions = int(float(m.get("conversion") or 0))
    cpa = float(m.get("cost_per_conversion") or 0)
    p100 = int(float(m.get("video_views_p100") or 0))
    completion_rate = (p100 / impressions * 100) if impressions else 0

    if conversions == 0 and spend > 100:
        flags.append(f"⛔ 0 conversions on ${spend:.0f} spend — kill or audit landing page")
    if ctr < 0.5 and impressions > 5000:
        flags.append(f"⚠️ CTR {ctr:.2f}% (TikTok benchmark is 1-2% — <0.5% = bad creative match)")
    if completion_rate < 5 and impressions > 5000:
        flags.append(f"⚠️ video completion {completion_rate:.1f}% (creative isn't holding attention past first 3s)")
    if cpa > 0 and cpa > 100:
        flags.append(f"⚠️ CPA ${cpa:.0f} (high — check landing-page conversion rate)")
    if not flags:
        flags.append("✅ no critical signals")
    return flags


def compose(advertiser_id, date_range, ads, metrics_by_ad):
    today = dt.date.today().isoformat()
    lines = [
        f"# TikTok Creative Audit — advertiser `{advertiser_id}`",
        "",
        f"_Generated {today}. Window: {date_range}._",
        "",
        f"**Total ads pulled:** {len(ads)}",
    ]

    total_spend = sum(float((metrics_by_ad.get(a["ad_id"]) or {}).get("spend") or 0) for a in ads)
    total_conversions = sum(int(float((metrics_by_ad.get(a["ad_id"]) or {}).get("conversion") or 0)) for a in ads)
    blended_cpa = (total_spend / total_conversions) if total_conversions else 0
    lines += [
        f"**Aggregate spend ({date_range}):**       ${total_spend:,.0f}",
        f"**Aggregate conversions:**              {total_conversions}",
        f"**Blended CPA:**                        ${blended_cpa:.0f}",
        "",
        "_For each ad below, classify the **hook framework** (PAS / Before-After-Bridge / "
        "AIDA / Problem-Solution / Social Proof Lead / Scarcity / Curiosity), apply the "
        "**fatigue thresholds**, and recommend keep / refresh / kill. See "
        "`creative-specialist/SKILL.md` §1, §4, §5._",
        "",
        "---",
        "",
        "## Per-ad detail",
        "",
    ]

    by_campaign = defaultdict(list)
    for ad in ads:
        by_campaign[ad.get("campaign_name") or ad.get("campaign_id") or "(unknown)"].append(ad)

    for camp, camp_ads in sorted(by_campaign.items()):
        lines += [f"### Campaign: {camp}", ""]
        for ad in camp_ads:
            ad_id = ad["ad_id"]
            m = metrics_by_ad.get(ad_id) or {}
            lines += [
                f"#### `{ad_id}` — {ad.get('ad_name') or 'unnamed'}",
                f"- **Status:** {ad.get('operation_status', '—')} · "
                f"**Ad Group:** {ad.get('adgroup_name', '—')} · "
                f"**Format:** {ad.get('ad_format', '—')}",
            ]
            if ad.get("landing_page_url"):
                lines.append(f"- **Landing URL:** {ad['landing_page_url']}")
            cta = ad.get("call_to_action")
            if cta:
                lines.append(f"- **CTA:** `{cta}`")
            if ad.get("video_id"):
                lines.append(f"- **Video ID:** `{ad['video_id']}`")
            if ad.get("ad_text"):
                lines.append("- **Ad text:**")
                for ln in ad["ad_text"].split("\n"):
                    if ln.strip():
                        lines.append(f"  > {ln}")

            if m:
                spend = float(m.get("spend") or 0)
                impressions = int(float(m.get("impressions") or 0))
                clicks = int(float(m.get("clicks") or 0))
                ctr = float(m.get("ctr") or 0)
                cpc = float(m.get("cpc") or 0)
                cpm = float(m.get("cpm") or 0)
                conv = int(float(m.get("conversion") or 0))
                cpa = float(m.get("cost_per_conversion") or 0)
                p2s = int(float(m.get("video_watched_2s") or 0))
                p100 = int(float(m.get("video_views_p100") or 0))
                hook_rate = (p2s / impressions * 100) if impressions else 0
                completion = (p100 / impressions * 100) if impressions else 0
                lines.append(
                    f"- **{date_range}:** spend ${spend:,.0f} · "
                    f"impr {impressions:,} · clicks {clicks:,} · "
                    f"CTR {ctr:.2f}% · CPC ${cpc:.2f} · CPM ${cpm:.2f} · "
                    f"conv {conv} · CPA ${cpa:.0f} · "
                    f"hook(2s) {hook_rate:.1f}% · completion {completion:.1f}%"
                )
            else:
                lines.append("- **No metrics in window** (no delivery yet)")

            for f in fatigue_signals(m):
                lines.append(f"- {f}")

            lines += [
                "",
                "**Analysis:**",
                "- Hook framework (per SKILL.md §1): _____",
                "- Video opening (first 3s holds attention?): _____",
                "- Recommendation: ☐ keep · ☐ refresh ☐ kill — because _____",
                "",
            ]

    lines += [
        "---",
        "",
        "## Audit summary (fill in after per-ad analysis)",
        "",
        "**Hook framework distribution:**",
        "- PAS: __ · BAB: __ · AIDA: __ · Problem-Solution: __ · Social-Proof Lead: __ · Scarcity: __ · Curiosity: __ · No clear: __",
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
        "**Hook-rate winners (>20% 2s view rate) worth modeling:**",
        "- ",
        "",
        "**Completion-rate floor — anything <5% should be killed:**",
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
    p = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                description=__doc__)
    p.add_argument("--advertiser-id", default=os.getenv("TIKTOK_ADVERTISER_ID"))
    p.add_argument("--include-paused", action="store_true")
    p.add_argument("--range", default="last_30d", dest="date_range",
                   choices=["last_3d", "last_7d", "last_14d", "last_30d",
                            "this_month", "last_month"])
    p.add_argument("--output", help="Save markdown to this path. Default: stdout.")
    args = p.parse_args()

    if not TOKEN:
        sys.exit("❌ TIKTOK_ACCESS_TOKEN missing in .env")
    if not args.advertiser_id:
        sys.exit("❌ Pass --advertiser-id or set TIKTOK_ADVERTISER_ID in .env")

    print(f"→ pulling ads for advertiser {args.advertiser_id}", file=sys.stderr)
    ads = list_ads(args.advertiser_id, args.include_paused)
    print(f"  found {len(ads)} ads", file=sys.stderr)

    print(f"→ pulling {args.date_range} metrics", file=sys.stderr)
    metrics_by_ad = get_metrics(args.advertiser_id, [a["ad_id"] for a in ads], args.date_range)
    print(f"  metrics for {len(metrics_by_ad)} ads with delivery", file=sys.stderr)

    md = compose(args.advertiser_id, args.date_range, ads, metrics_by_ad)
    if args.output:
        Path(args.output).write_text(md)
        print(f"✓ {args.output}", file=sys.stderr)
    else:
        print(md)


if __name__ == "__main__":
    main()

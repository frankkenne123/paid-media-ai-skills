#!/usr/bin/env python3
"""
Pull every active ad from a Google Ads account along with copy, performance,
and (for PMax) asset breakdown — formatted as a markdown audit worksheet for
framework analysis.

Output mirrors analyze_account_creatives.py (Meta) but handles both:
  - Search: Responsive Search Ads (headlines × descriptions, keyword-level performance)
  - PMax:    Asset groups + headline/description/image/video assets

Usage:
  python3 analyze_google_account_creatives.py --customer XXXXXXXXXX
  python3 analyze_google_account_creatives.py --customer XXXXXXXXXX \
    --output /tmp/<client>-google-audit.md
  python3 analyze_google_account_creatives.py --customer XXXXXXXXXX --range LAST_30_DAYS

Date ranges:
  YESTERDAY | LAST_7_DAYS | LAST_14_DAYS | LAST_30_DAYS | THIS_MONTH | LAST_MONTH
"""

import argparse, datetime as dt, os, sys
from collections import defaultdict
from pathlib import Path

# Use venv if present
_venv = Path(__file__).resolve().parent / "venv" / "lib" / "python3.10" / "site-packages"
if _venv.exists():
    sys.path.insert(0, str(_venv))

from dotenv import load_dotenv
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

load_dotenv()


def build_client():
    creds = {
        "developer_token": os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN"),
        "client_id": os.getenv("GOOGLE_ADS_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_ADS_CLIENT_SECRET"),
        "refresh_token": os.getenv("GOOGLE_ADS_REFRESH_TOKEN"),
        "login_customer_id": os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID"),
        "use_proto_plus": True,
    }
    missing = [k for k, v in creds.items() if not v and k != "use_proto_plus"]
    if missing:
        sys.exit(f"❌ Missing in .env: {', '.join(missing)}")
    return GoogleAdsClient.load_from_dict(creds)


def search(ga_service, customer_id, query):
    return list(ga_service.search(customer_id=customer_id, query=query))


def m_to_dollars(micros):
    return (micros or 0) / 1_000_000


def fmt_money(micros):
    return f"${m_to_dollars(micros):,.0f}"


def fatigue_signals(metrics):
    """Same thresholds as the Meta audit — applied to Google."""
    flags = []
    spend = m_to_dollars(metrics.get("spend_micros", 0))
    if not spend:
        flags.append("no spend in window (paused or new)")
        return flags
    ctr = metrics.get("ctr", 0) * 100
    impressions = metrics.get("impressions", 0)
    conversions = metrics.get("conversions", 0)
    conversion_value = metrics.get("conversion_value", 0)
    roas = (conversion_value / spend) if spend else 0
    if roas and roas < 1.0 and spend > 100:
        flags.append(f"⛔ ROAS {roas:.2f} on ${spend:.0f} spend (losing money)")
    if conversions == 0 and spend > 100:
        flags.append(f"⛔ 0 conversions on ${spend:.0f} spend (kill or audit landing page)")
    if ctr < 1.0 and impressions > 5000:
        flags.append(f"⚠️ CTR {ctr:.2f}% (Google search benchmark is 3-5%; <1% = bad keyword/copy match)")
    if not flags:
        flags.append("✅ no critical signals")
    return flags


def build_search_section(ga_service, customer_id, date_range):
    """Pull all RSAs + their performance for SEARCH campaigns in this customer."""
    q = f"""
        SELECT
            campaign.id, campaign.name, campaign.status, campaign.advertising_channel_type,
            ad_group.id, ad_group.name, ad_group.status,
            ad_group_ad.ad.id, ad_group_ad.ad.name, ad_group_ad.status,
            ad_group_ad.ad.type,
            ad_group_ad.ad.responsive_search_ad.headlines,
            ad_group_ad.ad.responsive_search_ad.descriptions,
            ad_group_ad.ad.final_urls,
            metrics.cost_micros, metrics.impressions, metrics.clicks, metrics.ctr,
            metrics.average_cpc, metrics.conversions, metrics.conversions_value
        FROM ad_group_ad
        WHERE
            campaign.advertising_channel_type = 'SEARCH'
            AND ad_group_ad.status = 'ENABLED'
            AND ad_group_ad.ad.type = 'RESPONSIVE_SEARCH_AD'
            AND metrics.impressions > 0
            AND segments.date DURING {date_range}
    """
    rows = search(ga_service, customer_id, q)

    by_campaign = defaultdict(list)
    for r in rows:
        camp = r.campaign.name
        rsa = r.ad_group_ad.ad.responsive_search_ad
        by_campaign[camp].append({
            "ad_id": r.ad_group_ad.ad.id,
            "ad_name": r.ad_group_ad.ad.name or f"ad-{r.ad_group_ad.ad.id}",
            "ad_group": r.ad_group.name,
            "headlines": [h.text for h in rsa.headlines],
            "descriptions": [d.text for d in rsa.descriptions],
            "final_urls": list(r.ad_group_ad.ad.final_urls),
            "metrics": {
                "spend_micros": r.metrics.cost_micros,
                "impressions": r.metrics.impressions,
                "clicks": r.metrics.clicks,
                "ctr": r.metrics.ctr,
                "avg_cpc_micros": r.metrics.average_cpc,
                "conversions": r.metrics.conversions,
                "conversion_value": r.metrics.conversions_value,
            },
        })
    return by_campaign


def build_pmax_section(ga_service, customer_id, date_range):
    """Pull asset groups + their key text/image/video assets for PMax."""
    # First: campaigns + asset groups + 30d performance
    q = f"""
        SELECT
            campaign.id, campaign.name, campaign.status,
            asset_group.id, asset_group.name, asset_group.status,
            metrics.cost_micros, metrics.impressions, metrics.clicks, metrics.ctr,
            metrics.conversions, metrics.conversions_value
        FROM asset_group
        WHERE
            campaign.advertising_channel_type = 'PERFORMANCE_MAX'
            AND segments.date DURING {date_range}
    """
    rows = search(ga_service, customer_id, q)

    by_campaign = defaultdict(list)
    for r in rows:
        by_campaign[r.campaign.name].append({
            "campaign_id": r.campaign.id,
            "ag_id": r.asset_group.id,
            "ag_name": r.asset_group.name,
            "ag_status": r.asset_group.status.name,
            "metrics": {
                "spend_micros": r.metrics.cost_micros,
                "impressions": r.metrics.impressions,
                "clicks": r.metrics.clicks,
                "ctr": r.metrics.ctr,
                "conversions": r.metrics.conversions,
                "conversion_value": r.metrics.conversions_value,
            },
        })

    # Second pass: pull text/video/image assets per asset group (no per-asset perf — that
    # query is more involved; we just enumerate what's in the group so the agent can
    # see if it's under-resourced)
    asset_q = """
        SELECT
            asset_group.id, asset_group.name,
            asset_group_asset.field_type,
            asset.text_asset.text,
            asset.youtube_video_asset.youtube_video_id,
            asset.image_asset.full_size.url
        FROM asset_group_asset
        WHERE asset_group_asset.status != 'REMOVED'
    """
    asset_rows = search(ga_service, customer_id, asset_q)
    assets_by_ag = defaultdict(lambda: defaultdict(list))
    for r in asset_rows:
        ft = r.asset_group_asset.field_type.name
        text = r.asset.text_asset.text
        yt_id = r.asset.youtube_video_asset.youtube_video_id
        img_url = r.asset.image_asset.full_size.url
        assets_by_ag[r.asset_group.id][ft].append({
            "text": text or None,
            "youtube_video_id": yt_id or None,
            "image_url": img_url or None,
        })

    return by_campaign, assets_by_ag


def build_keywords_section(ga_service, customer_id, date_range):
    """Pull keyword-level performance — useful context for what's converting."""
    q = f"""
        SELECT
            campaign.name, ad_group.name,
            ad_group_criterion.keyword.text, ad_group_criterion.keyword.match_type,
            metrics.cost_micros, metrics.clicks, metrics.conversions, metrics.conversions_value
        FROM keyword_view
        WHERE
            ad_group_criterion.status = 'ENABLED'
            AND segments.date DURING {date_range}
        ORDER BY metrics.cost_micros DESC
        LIMIT 30
    """
    rows = search(ga_service, customer_id, q)
    return [{
        "campaign": r.campaign.name,
        "ad_group": r.ad_group.name,
        "keyword": r.ad_group_criterion.keyword.text,
        "match_type": r.ad_group_criterion.keyword.match_type.name,
        "spend": m_to_dollars(r.metrics.cost_micros),
        "clicks": r.metrics.clicks,
        "conversions": r.metrics.conversions,
        "revenue": r.metrics.conversions_value,
    } for r in rows]


def compose(customer_id, date_range, search_data, pmax_campaigns, pmax_assets, keywords):
    today = dt.date.today().isoformat()
    lines = [
        f"# Google Ads Creative Audit — `{customer_id}`",
        "",
        f"_Generated {today}. Window: {date_range}._",
        "",
        "_For each ad below, classify the **hook framework** "
        "(PAS / Before-After-Bridge / AIDA / Problem-Solution / Social Proof Lead / "
        "Scarcity / Curiosity), apply **fatigue thresholds**, and recommend "
        "keep / refresh / kill. See `creative-specialist/SKILL.md` §1, §4, §5._",
        "",
        "---",
        "",
    ]

    # Aggregate totals across both channels
    total_spend = 0.0
    total_revenue = 0.0
    total_conversions = 0.0
    for ads in search_data.values():
        for ad in ads:
            m = ad["metrics"]
            total_spend += m_to_dollars(m["spend_micros"])
            total_revenue += m["conversion_value"]
            total_conversions += m["conversions"]
    for ags in pmax_campaigns.values():
        for ag in ags:
            m = ag["metrics"]
            total_spend += m_to_dollars(m["spend_micros"])
            total_revenue += m["conversion_value"]
            total_conversions += m["conversions"]
    blended_roas = (total_revenue / total_spend) if total_spend else 0
    lines += [
        f"**Aggregate spend ({date_range}):**       ${total_spend:,.0f}",
        f"**Aggregate revenue:**                  ${total_revenue:,.0f}",
        f"**Aggregate conversions:**              {total_conversions:.1f}",
        f"**Blended ROAS:**                       {blended_roas:.2f}x",
        "",
        "---",
        "",
    ]

    # ─── SEARCH ──────────────────────────────────────────────────────────
    if search_data:
        lines += ["## Search — Responsive Search Ads", ""]
        for camp, ads in sorted(search_data.items()):
            lines += [f"### Campaign: {camp}", ""]
            for ad in ads:
                m = ad["metrics"]
                spend = m_to_dollars(m["spend_micros"])
                ctr = m["ctr"] * 100
                cpc = m_to_dollars(m["avg_cpc_micros"])
                roas = (m["conversion_value"] / spend) if spend else 0
                lines += [
                    f"#### Ad `{ad['ad_id']}` — {ad['ad_name']}",
                    f"- **Ad Group:** {ad['ad_group']}",
                    f"- **Final URLs:** {', '.join(ad['final_urls']) or '—'}",
                    f"- **Headlines** ({len(ad['headlines'])}):",
                ]
                for h in ad["headlines"]:
                    lines.append(f"  - _{h}_")
                lines.append(f"- **Descriptions** ({len(ad['descriptions'])}):")
                for d in ad["descriptions"]:
                    lines.append(f"  - {d}")
                lines.append(
                    f"- **{date_range}:** spend ${spend:,.0f} · "
                    f"impr {m['impressions']:,} · clicks {m['clicks']:,} · "
                    f"CTR {ctr:.2f}% · CPC ${cpc:.2f} · "
                    f"conv {m['conversions']:.1f} · revenue ${m['conversion_value']:,.0f} · "
                    f"ROAS **{roas:.2f}x**"
                )
                for f in fatigue_signals(m):
                    lines.append(f"- {f}")
                lines += [
                    "",
                    "**Analysis:**",
                    "- Hook framework (per SKILL.md §1): _____",
                    "- Recommendation: ☐ keep · ☐ refresh ☐ kill — because _____",
                    "",
                ]
    else:
        lines += ["## Search", "", "_(no active Search ads in window)_", ""]

    # ─── PMAX ────────────────────────────────────────────────────────────
    if pmax_campaigns:
        lines += ["---", "", "## Performance Max", ""]
        for camp, ags in sorted(pmax_campaigns.items()):
            lines += [f"### Campaign: {camp}", ""]
            for ag in ags:
                m = ag["metrics"]
                spend = m_to_dollars(m["spend_micros"])
                ctr = m["ctr"] * 100
                roas = (m["conversion_value"] / spend) if spend else 0
                ag_assets = pmax_assets.get(ag["ag_id"], {})
                lines += [
                    f"#### Asset Group `{ag['ag_id']}` — {ag['ag_name']} ({ag['ag_status']})",
                    f"- **{date_range}:** spend ${spend:,.0f} · "
                    f"impr {m['impressions']:,} · CTR {ctr:.2f}% · "
                    f"conv {m['conversions']:.1f} · revenue ${m['conversion_value']:,.0f} · "
                    f"ROAS **{roas:.2f}x**",
                ]
                for f in fatigue_signals(m):
                    lines.append(f"- {f}")
                # Asset breakdown
                lines.append("- **Assets:**")
                for field, items in sorted(ag_assets.items()):
                    lines.append(f"  - `{field}`: {len(items)}")
                # Show top text assets if any
                for field in ("HEADLINE", "LONG_HEADLINE", "DESCRIPTION", "BUSINESS_NAME"):
                    items = ag_assets.get(field, [])
                    if items:
                        lines.append(f"  - **{field} samples:**")
                        for item in items[:3]:
                            if item["text"]:
                                lines.append(f"    - _{item['text']}_")
                lines += [
                    "",
                    "**Analysis:**",
                    "- Asset coverage check: ✅/❌ 5+ marketing images · ✅/❌ 1+ logo · ✅/❌ 5+ headlines · ✅/❌ 5+ descriptions · ✅/❌ 1+ video",
                    "- Hook framework dominant in headlines (per SKILL.md §1): _____",
                    "- Recommendation: ☐ scale ☐ refresh assets ☐ pause — because _____",
                    "",
                ]
    else:
        lines += ["---", "", "## Performance Max", "", "_(no active PMax campaigns in window)_", ""]

    # ─── KEYWORDS ─────────────────────────────────────────────────────────
    if keywords:
        lines += ["---", "", "## Top 30 keywords by spend", "",
                  "| Keyword | Match | Campaign / Ad Group | Spend | Clicks | Conv | Revenue |",
                  "|---|---|---|---:|---:|---:|---:|"]
        for kw in keywords:
            lines.append(
                f"| `{kw['keyword']}` | {kw['match_type']} | "
                f"{kw['campaign']} / {kw['ad_group']} | "
                f"${kw['spend']:,.0f} | {kw['clicks']:,} | "
                f"{kw['conversions']:.1f} | ${kw['revenue']:,.0f} |"
            )
        lines.append("")

    # ─── ROLLUP ─────────────────────────────────────────────────────────
    lines += [
        "---",
        "",
        "## Audit summary (fill in after per-ad/asset-group analysis)",
        "",
        "**Hook framework distribution across Search RSAs:**",
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
        "**PMax asset gaps to fix:**",
        "- ",
        "",
        "**Top wasted-spend keywords (negative-keyword candidates):**",
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
    p.add_argument("--customer", required=True, help="Customer ID without dashes")
    p.add_argument("--range", default="LAST_30_DAYS",
                   choices=["YESTERDAY", "LAST_7_DAYS", "LAST_14_DAYS",
                            "LAST_30_DAYS", "THIS_MONTH", "LAST_MONTH"],
                   dest="date_range")
    p.add_argument("--output", help="Save markdown to this path. Default: stdout.")
    args = p.parse_args()

    client = build_client()
    customer_id = args.customer.replace("-", "")
    ga_service = client.get_service("GoogleAdsService")

    print(f"→ pulling Search RSAs for customer {customer_id} ({args.date_range})", file=sys.stderr)
    try:
        search_data = build_search_section(ga_service, customer_id, args.date_range)
    except GoogleAdsException as e:
        print(f"⚠️  Search query failed: {e}", file=sys.stderr)
        search_data = {}

    print(f"→ pulling PMax asset groups", file=sys.stderr)
    try:
        pmax_campaigns, pmax_assets = build_pmax_section(ga_service, customer_id, args.date_range)
    except GoogleAdsException as e:
        print(f"⚠️  PMax query failed: {e}", file=sys.stderr)
        pmax_campaigns, pmax_assets = {}, {}

    print(f"→ pulling top keywords", file=sys.stderr)
    try:
        keywords = build_keywords_section(ga_service, customer_id, args.date_range)
    except GoogleAdsException as e:
        print(f"⚠️  keyword query failed: {e}", file=sys.stderr)
        keywords = []

    md = compose(customer_id, args.date_range, search_data, pmax_campaigns, pmax_assets, keywords)
    if args.output:
        Path(args.output).write_text(md)
        print(f"✓ {args.output}", file=sys.stderr)
    else:
        print(md)


if __name__ == "__main__":
    main()

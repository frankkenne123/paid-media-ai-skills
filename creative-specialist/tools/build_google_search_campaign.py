#!/usr/bin/env python3
"""
Build a full Google Ads Search campaign end-to-end:
  budget → campaign → ad group → responsive search ad → keywords.

All in PAUSED state. The user approves before activating.

Usage:
  python3 build_google_search_campaign.py \
    --customer XXXXXXXXXX \
    --client "Acme Co" \
    --campaign-name "Brand - Spring 2026" \
    --daily-budget 50 \
    --final-url "https://acme.example.com/landing" \
    --headlines "Real 14k Gold Chains" "Lifetime Warranty" "Free Shipping Over \$50" \
                "Hand-Crafted Jewelry" "20+ Years of Quality" "Shop the New Drop" \
                "Trusted by 2M+ Customers" "Premium Cuban Links" \
    --descriptions "Hand-crafted 14k gold chains backed by a lifetime warranty. Free shipping over \$50." \
                   "Trusted by over 2 million customers — premium streetwear jewelry since 2003." \
                   "Real gold, not plated. Every piece guaranteed for life." \
                   "Discover the new Spring drop — limited stock, ships today." \
    --keywords "14k gold chain" "cuban link chain" "+real +gold +jewelry" "[gold cuban link]" \
    --countries US \
    --bidding-strategy MAXIMIZE_CONVERSIONS

Default bidding is MAXIMIZE_CONVERSIONS. Override with --bidding-strategy MANUAL_CPC,
TARGET_CPA, MAXIMIZE_CLICKS, or TARGET_ROAS (TARGET_CPA needs --target-cpa-dollars,
TARGET_ROAS needs --target-roas).

Keyword match types (prefix the keyword text):
  "exact"        — broad match (no quotes/brackets/plus)
  "+modified +broad" — broad-match with required terms (use + per word)
  '"phrase match"'   — phrase match (wrap in double quotes)
  "[exact match]"    — exact match (wrap in square brackets)

Use --dry-run to print the API mutations without sending.
"""

import argparse, datetime as dt, json, os, sys
from pathlib import Path

# Use the workspace venv if it exists (matches google_ads_data.py)
_venv = Path(__file__).resolve().parent / "venv" / "lib" / "python3.10" / "site-packages"
if _venv.exists():
    sys.path.insert(0, str(_venv))

from dotenv import load_dotenv
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

load_dotenv()

CTA_HELP = (
    "Bidding: MAXIMIZE_CONVERSIONS (default), MANUAL_CPC, MAXIMIZE_CLICKS, "
    "TARGET_CPA (with --target-cpa-dollars), TARGET_ROAS (with --target-roas)"
)


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


def parse_keyword(text):
    """Detect match type from keyword string. Returns (match_type, clean_text)."""
    t = text.strip()
    if t.startswith("[") and t.endswith("]"):
        return "EXACT", t[1:-1].strip()
    if t.startswith('"') and t.endswith('"'):
        return "PHRASE", t[1:-1].strip()
    return "BROAD", t


def fail_on_ads_exception(client, e, where):
    msgs = []
    for err in e.failure.errors:
        msgs.append(f"  - {err.message} (at {[f.field_name for f in err.location.field_path_elements]})")
    print(f"❌ Google Ads API error during {where}:\n" + "\n".join(msgs))
    sys.exit(1)


def main():
    p = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                description=__doc__)
    # Required
    p.add_argument("--customer", required=True, help="Customer ID without dashes, e.g. XXXXXXXXXX")
    p.add_argument("--client", required=True, help="Client name (used in campaign labeling)")
    p.add_argument("--campaign-name", required=True)
    p.add_argument("--daily-budget", type=float, required=True, help="In dollars (e.g. 50 = $50/day)")
    p.add_argument("--final-url", required=True)
    p.add_argument("--headlines", nargs="+", required=True,
                   help="3-15 headlines, each ≤30 chars")
    p.add_argument("--descriptions", nargs="+", required=True,
                   help="2-4 descriptions, each ≤90 chars")
    p.add_argument("--keywords", nargs="+", required=True,
                   help='Keywords with match-type syntax: bare=broad, "phrase"=phrase, [exact]=exact')
    # Optional
    p.add_argument("--countries", default="US",
                   help="Comma-separated country codes (US,CA,GB...) — default US")
    p.add_argument("--bidding-strategy", default="MAXIMIZE_CONVERSIONS",
                   choices=["MAXIMIZE_CONVERSIONS", "MANUAL_CPC", "MAXIMIZE_CLICKS",
                            "TARGET_CPA", "TARGET_ROAS"])
    p.add_argument("--target-cpa-dollars", type=float, help="Required when --bidding-strategy=TARGET_CPA")
    p.add_argument("--target-roas", type=float, help="Required when --bidding-strategy=TARGET_ROAS (e.g. 3.0 for 300%%)")
    p.add_argument("--default-cpc", type=float, default=1.50, help="Default CPC bid in dollars (manual + ad-group level for safety)")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    # Validate
    if not (3 <= len(args.headlines) <= 15):
        sys.exit(f"❌ --headlines must be 3-15 (got {len(args.headlines)})")
    if not (2 <= len(args.descriptions) <= 4):
        sys.exit(f"❌ --descriptions must be 2-4 (got {len(args.descriptions)})")
    too_long = [h for h in args.headlines if len(h) > 30]
    if too_long:
        sys.exit(f"❌ headlines >30 chars: {too_long}")
    too_long = [d for d in args.descriptions if len(d) > 90]
    if too_long:
        sys.exit(f"❌ descriptions >90 chars: {too_long}")
    if args.bidding_strategy == "TARGET_CPA" and not args.target_cpa_dollars:
        sys.exit("❌ --bidding-strategy TARGET_CPA requires --target-cpa-dollars")
    if args.bidding_strategy == "TARGET_ROAS" and not args.target_roas:
        sys.exit("❌ --bidding-strategy TARGET_ROAS requires --target-roas")

    stamp = dt.datetime.now().strftime("%m%d_%H%M")
    full_name = f"{args.client} — {args.campaign_name} — {stamp}"

    print(f"🏗️  Building Google Search campaign: {full_name}")
    print(f"    Customer: {args.customer}")
    print(f"    Budget:   ${args.daily_budget}/day")
    print(f"    Bidding:  {args.bidding_strategy}")
    print(f"    Status:   PAUSED (you must activate manually after approval)\n")

    client = build_client()
    customer_id = args.customer.replace("-", "")

    if args.dry_run:
        print("🔍 DRY RUN — no mutations will be sent.\n")
        print(f"Would create:")
        print(f"  CampaignBudget: '{full_name} Budget' @ ${args.daily_budget}/day (SHARED=False)")
        print(f"  Campaign:       '{full_name}' SEARCH, status=PAUSED, bidding={args.bidding_strategy}")
        print(f"  GeoCriterion:   countries={args.countries}")
        print(f"  AdGroup:        '{full_name} - Ad Group 1', status=PAUSED, max-cpc=${args.default_cpc}")
        print(f"  RSA:            {len(args.headlines)} headlines, {len(args.descriptions)} descriptions, status=PAUSED")
        print(f"                  final_url={args.final_url}")
        print(f"  Keywords ({len(args.keywords)}):")
        for k in args.keywords:
            mt, txt = parse_keyword(k)
            print(f"                  [{mt}] {txt}")
        return

    try:
        # 1. Budget
        budget_svc = client.get_service("CampaignBudgetService")
        budget_op = client.get_type("CampaignBudgetOperation")
        budget = budget_op.create
        budget.name = f"{full_name} Budget"
        budget.amount_micros = int(args.daily_budget * 1_000_000)
        budget.delivery_method = client.enums.BudgetDeliveryMethodEnum.STANDARD
        budget.explicitly_shared = False
        resp = budget_svc.mutate_campaign_budgets(customer_id=customer_id, operations=[budget_op])
        budget_resource = resp.results[0].resource_name
        print(f"✅ Budget:    {budget_resource}")

        # 2. Campaign
        camp_svc = client.get_service("CampaignService")
        camp_op = client.get_type("CampaignOperation")
        camp = camp_op.create
        camp.name = full_name
        camp.advertising_channel_type = client.enums.AdvertisingChannelTypeEnum.SEARCH
        camp.status = client.enums.CampaignStatusEnum.PAUSED
        camp.campaign_budget = budget_resource
        # Network settings: search + partners + content (display) — Search-only is most common
        camp.network_settings.target_google_search = True
        camp.network_settings.target_search_network = True
        camp.network_settings.target_content_network = False
        camp.network_settings.target_partner_search_network = False
        # Bidding
        bs = args.bidding_strategy
        if bs == "MAXIMIZE_CONVERSIONS":
            camp.maximize_conversions.CopyFrom(client.get_type("MaximizeConversions"))
        elif bs == "MAXIMIZE_CLICKS":
            camp.target_spend.CopyFrom(client.get_type("TargetSpend"))
        elif bs == "MANUAL_CPC":
            camp.manual_cpc.enhanced_cpc_enabled = True
        elif bs == "TARGET_CPA":
            camp.maximize_conversions.target_cpa_micros = int(args.target_cpa_dollars * 1_000_000)
        elif bs == "TARGET_ROAS":
            camp.maximize_conversion_value.target_roas = args.target_roas
        # Start tomorrow to avoid mid-day partial-day spend skew
        camp.start_date = (dt.date.today() + dt.timedelta(days=1)).strftime("%Y%m%d")
        resp = camp_svc.mutate_campaigns(customer_id=customer_id, operations=[camp_op])
        camp_resource = resp.results[0].resource_name
        camp_id = camp_resource.split("/")[-1]
        print(f"✅ Campaign:  {camp_resource}")

        # 3. Geo targeting (country-level)
        geo_svc = client.get_service("CampaignCriterionService")
        const_svc = client.get_service("GeoTargetConstantService")
        geo_ops = []
        for code in [c.strip().upper() for c in args.countries.split(",")]:
            sugg = const_svc.suggest_geo_target_constants(
                locale="en",
                country_code=code,
            )
            if not sugg.geo_target_constant_suggestions:
                print(f"⚠️  no geo target found for '{code}', skipping")
                continue
            geo_const = sugg.geo_target_constant_suggestions[0].geo_target_constant
            op = client.get_type("CampaignCriterionOperation")
            crit = op.create
            crit.campaign = camp_resource
            crit.location.geo_target_constant = geo_const.resource_name
            geo_ops.append(op)
        if geo_ops:
            geo_svc.mutate_campaign_criteria(customer_id=customer_id, operations=geo_ops)
        print(f"✅ Geo:       {args.countries}")

        # 4. Ad group
        ag_svc = client.get_service("AdGroupService")
        ag_op = client.get_type("AdGroupOperation")
        ag = ag_op.create
        ag.name = f"{full_name} - Ad Group 1"
        ag.campaign = camp_resource
        ag.type_ = client.enums.AdGroupTypeEnum.SEARCH_STANDARD
        ag.status = client.enums.AdGroupStatusEnum.PAUSED
        ag.cpc_bid_micros = int(args.default_cpc * 1_000_000)
        resp = ag_svc.mutate_ad_groups(customer_id=customer_id, operations=[ag_op])
        ag_resource = resp.results[0].resource_name
        print(f"✅ Ad Group:  {ag_resource}")

        # 5. RSA
        ad_svc = client.get_service("AdGroupAdService")
        ad_op = client.get_type("AdGroupAdOperation")
        ad = ad_op.create
        ad.ad_group = ag_resource
        ad.status = client.enums.AdGroupAdStatusEnum.PAUSED
        ad.ad.final_urls.append(args.final_url)
        for h in args.headlines:
            asset = client.get_type("AdTextAsset")
            asset.text = h
            ad.ad.responsive_search_ad.headlines.append(asset)
        for d in args.descriptions:
            asset = client.get_type("AdTextAsset")
            asset.text = d
            ad.ad.responsive_search_ad.descriptions.append(asset)
        resp = ad_svc.mutate_ad_group_ads(customer_id=customer_id, operations=[ad_op])
        ad_resource = resp.results[0].resource_name
        print(f"✅ RSA Ad:    {ad_resource}")

        # 6. Keywords
        kw_svc = client.get_service("AdGroupCriterionService")
        kw_ops = []
        for kw in args.keywords:
            mt, txt = parse_keyword(kw)
            op = client.get_type("AdGroupCriterionOperation")
            crit = op.create
            crit.ad_group = ag_resource
            crit.status = client.enums.AdGroupCriterionStatusEnum.PAUSED
            crit.keyword.text = txt
            crit.keyword.match_type = getattr(client.enums.KeywordMatchTypeEnum, mt)
            kw_ops.append(op)
        if kw_ops:
            resp = kw_svc.mutate_ad_group_criteria(customer_id=customer_id, operations=kw_ops)
            print(f"✅ Keywords:  {len(resp.results)} added")

    except GoogleAdsException as e:
        fail_on_ads_exception(client, e, "campaign build")

    print("\n🎉 Built. All resources are PAUSED.")
    print(f"    Campaign:  {camp_resource} (id={camp_id})")
    print(f"    Ad Group:  {ag_resource}")
    print(f"    RSA Ad:    {ad_resource}")
    print("\nNext: Show the user a preview in Google Ads UI.")
    print("After approval, activate via the UI or by mutating campaign.status=ENABLED.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Build a full Google Ads Performance Max campaign end-to-end:
  budget → campaign (PMAX) → asset group → upload assets (images/logos/video) → headlines → descriptions

All in PAUSED state. The user approves before activating.

Usage:
  python3 build_google_pmax_campaign.py \
    --customer XXXXXXXXXX \
    --client "Acme Co" \
    --campaign-name "PMax - Spring 2026" \
    --daily-budget 100 \
    --final-url "https://acme.example.com/landing" \
    --business-name "Acme Co" \
    --headlines "Real 14k Gold Chains" "Lifetime Warranty" "Free Shipping Over \$50" \
                "Hand-Crafted Jewelry" "20+ Years of Quality" \
    --long-headlines "Hand-crafted 14k gold chains backed by a lifetime warranty" \
                     "Trusted by 2M+ customers — premium streetwear jewelry since 2003" \
    --descriptions "Hand-crafted real 14k gold chains. Free shipping over \$50." \
                   "Backed by a lifetime warranty. Trusted by over 2M customers." \
                   "Real gold, not plated. Premium streetwear jewelry since 2003." \
    --marketing-images /tmp/img1.png /tmp/img2.png /tmp/img3.png /tmp/img4.png /tmp/img5.png \
    --logo-images /tmp/logo.png \
    --videos /tmp/hero.mp4 \
    --countries US \
    --bidding-strategy MAXIMIZE_CONVERSION_VALUE \
    --target-roas 3.0

PMax requires a LOT of assets. Required minimums per Google:
  - 5+ marketing images (1200×628 landscape recommended; supports 1:1, 4:5, 1.91:1)
  - 1+ logos (1:1 minimum 128×128, 4:1 horizontal optional)
  - 5 short headlines (≤30 chars each)
  - 1+ long headlines (≤90 chars)
  - 5 descriptions (≤90 chars; 1 must be ≤60)
  - Business name (≤25 chars)
  - 0+ videos (HIGHLY recommended — without video, Google auto-generates a slideshow that looks bad)

Bidding:
  --bidding-strategy MAXIMIZE_CONVERSIONS    (default for new accounts)
  --bidding-strategy MAXIMIZE_CONVERSION_VALUE --target-roas 3.0  (recommended once you have conversion history)
  --bidding-strategy TARGET_CPA --target-cpa-dollars 25

Use --dry-run to print mutations without sending.
"""

import argparse, datetime as dt, hashlib, json, os, sys
from pathlib import Path

# Use the workspace venv if it exists
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


def upload_image_asset(client, customer_id, image_path, name, image_type):
    """Upload an image to Google Ads as an asset. Returns asset resource name."""
    if not Path(image_path).exists():
        sys.exit(f"❌ image not found: {image_path}")
    svc = client.get_service("AssetService")
    op = client.get_type("AssetOperation")
    asset = op.create
    asset.name = name
    asset.type_ = client.enums.AssetTypeEnum.IMAGE
    with open(image_path, "rb") as f:
        asset.image_asset.data = f.read()
    # image_type hints PMax which slot to use (MARKETING_IMAGE / LOGO / SQUARE_MARKETING_IMAGE etc)
    resp = svc.mutate_assets(customer_id=customer_id, operations=[op])
    return resp.results[0].resource_name


def upload_text_asset(client, customer_id, text):
    svc = client.get_service("AssetService")
    op = client.get_type("AssetOperation")
    asset = op.create
    asset.type_ = client.enums.AssetTypeEnum.TEXT
    asset.text_asset.text = text
    resp = svc.mutate_assets(customer_id=customer_id, operations=[op])
    return resp.results[0].resource_name


def upload_video_asset(client, customer_id, video_path):
    """Google Ads can't accept raw video uploads via API — videos must be on YouTube.
    This function expects video_path to be a YouTube URL or YouTube video ID, not a local file."""
    yt_id = video_path
    if "youtube.com" in video_path or "youtu.be" in video_path:
        # Extract ID from URL
        if "v=" in video_path:
            yt_id = video_path.split("v=")[1].split("&")[0]
        elif "youtu.be/" in video_path:
            yt_id = video_path.split("youtu.be/")[1].split("?")[0]
    elif "/" in video_path or video_path.endswith((".mp4", ".mov", ".webm")):
        sys.exit(f"❌ Google Ads PMax requires videos to be uploaded to YouTube first. "
                 f"Got local path '{video_path}' — upload to YouTube and pass the URL or 11-char video ID instead.")

    svc = client.get_service("AssetService")
    op = client.get_type("AssetOperation")
    asset = op.create
    asset.name = f"Video {yt_id}"
    asset.type_ = client.enums.AssetTypeEnum.YOUTUBE_VIDEO
    asset.youtube_video_asset.youtube_video_id = yt_id
    resp = svc.mutate_assets(customer_id=customer_id, operations=[op])
    return resp.results[0].resource_name


def link_asset_to_group(client, customer_id, asset_resource, asset_group_resource, field_type):
    svc = client.get_service("AssetGroupAssetService")
    op = client.get_type("AssetGroupAssetOperation")
    link = op.create
    link.asset = asset_resource
    link.asset_group = asset_group_resource
    link.field_type = getattr(client.enums.AssetFieldTypeEnum, field_type)
    return op


def fail_on_ads_exception(e, where):
    msgs = []
    for err in e.failure.errors:
        path = ".".join(f.field_name for f in err.location.field_path_elements)
        msgs.append(f"  - {err.message} (at {path})")
    print(f"❌ Google Ads API error during {where}:\n" + "\n".join(msgs))
    sys.exit(1)


def main():
    p = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                description=__doc__)
    p.add_argument("--customer", required=True)
    p.add_argument("--client", required=True)
    p.add_argument("--campaign-name", required=True)
    p.add_argument("--daily-budget", type=float, required=True)
    p.add_argument("--final-url", required=True)
    p.add_argument("--business-name", required=True, help="≤25 chars — appears as the brand line in PMax")
    p.add_argument("--headlines", nargs="+", required=True,
                   help="At least 5 headlines, each ≤30 chars")
    p.add_argument("--long-headlines", nargs="+", required=True,
                   help="At least 1 long headline, each ≤90 chars")
    p.add_argument("--descriptions", nargs="+", required=True,
                   help="At least 5 descriptions, each ≤90 chars (1 must be ≤60)")
    p.add_argument("--marketing-images", nargs="+", required=True,
                   help="Paths to 5+ local images for MARKETING_IMAGE slot (1200×628 recommended)")
    p.add_argument("--square-images", nargs="*", default=[],
                   help="Optional 1:1 images for SQUARE_MARKETING_IMAGE slot")
    p.add_argument("--portrait-images", nargs="*", default=[],
                   help="Optional 4:5 images for PORTRAIT_MARKETING_IMAGE slot")
    p.add_argument("--logo-images", nargs="+", required=True,
                   help="At least 1 logo (1:1 minimum 128×128)")
    p.add_argument("--landscape-logos", nargs="*", default=[],
                   help="Optional 4:1 horizontal logos")
    p.add_argument("--videos", nargs="*", default=[],
                   help="YouTube URLs or 11-char video IDs (Google Ads can't accept local video uploads)")
    p.add_argument("--countries", default="US")
    p.add_argument("--bidding-strategy", default="MAXIMIZE_CONVERSIONS",
                   choices=["MAXIMIZE_CONVERSIONS", "MAXIMIZE_CONVERSION_VALUE", "TARGET_CPA", "TARGET_ROAS"])
    p.add_argument("--target-cpa-dollars", type=float)
    p.add_argument("--target-roas", type=float)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    # Validate
    if len(args.headlines) < 5:
        sys.exit(f"❌ Need at least 5 headlines (got {len(args.headlines)})")
    too_long = [h for h in args.headlines if len(h) > 30]
    if too_long:
        sys.exit(f"❌ headlines >30 chars: {too_long}")
    too_long = [h for h in args.long_headlines if len(h) > 90]
    if too_long:
        sys.exit(f"❌ long-headlines >90 chars: {too_long}")
    if len(args.descriptions) < 5:
        sys.exit(f"❌ Need at least 5 descriptions (got {len(args.descriptions)})")
    too_long = [d for d in args.descriptions if len(d) > 90]
    if too_long:
        sys.exit(f"❌ descriptions >90 chars: {too_long}")
    if not any(len(d) <= 60 for d in args.descriptions):
        sys.exit("❌ At least 1 description must be ≤60 chars (PMax requires a short variant)")
    if len(args.business_name) > 25:
        sys.exit(f"❌ business-name >25 chars: {args.business_name!r}")
    if len(args.marketing_images) < 5:
        sys.exit(f"❌ Need at least 5 --marketing-images (got {len(args.marketing_images)})")
    if not args.logo_images:
        sys.exit("❌ Need at least 1 --logo-images")
    if not args.videos:
        print("⚠️  No --videos provided. PMax will auto-generate slideshow videos (lower performance).")
        print("    Strongly recommend uploading at least 1 video to YouTube and passing the URL.\n")
    if args.bidding_strategy == "TARGET_CPA" and not args.target_cpa_dollars:
        sys.exit("❌ TARGET_CPA requires --target-cpa-dollars")
    if args.bidding_strategy == "TARGET_ROAS" and not args.target_roas:
        sys.exit("❌ TARGET_ROAS requires --target-roas")

    stamp = dt.datetime.now().strftime("%m%d_%H%M")
    full_name = f"{args.client} — {args.campaign_name} — {stamp}"

    print(f"🏗️  Building Google Performance Max campaign: {full_name}")
    print(f"    Customer:  {args.customer}")
    print(f"    Budget:    ${args.daily_budget}/day")
    print(f"    Bidding:   {args.bidding_strategy}")
    print(f"    Assets:    {len(args.marketing_images)} marketing + "
          f"{len(args.square_images)} square + "
          f"{len(args.portrait_images)} portrait + "
          f"{len(args.logo_images)} logo + "
          f"{len(args.landscape_logos)} landscape-logo + "
          f"{len(args.videos)} video")
    print(f"    Status:    PAUSED (activate manually after approval)\n")

    if args.dry_run:
        print("🔍 DRY RUN — no mutations will be sent.\n")
        print(f"Would upload {sum(len(x) for x in [args.marketing_images, args.square_images, args.portrait_images, args.logo_images, args.landscape_logos])} images, "
              f"{len(args.videos)} videos, "
              f"{len(args.headlines) + len(args.long_headlines) + len(args.descriptions) + 1} text assets, "
              f"create campaign + asset group + listing-group root, link assets to fields.")
        return

    client = build_client()
    customer_id = args.customer.replace("-", "")

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
        print(f"✅ Budget:        {budget_resource}")

        # 2. Campaign (Performance Max)
        camp_svc = client.get_service("CampaignService")
        camp_op = client.get_type("CampaignOperation")
        camp = camp_op.create
        camp.name = full_name
        camp.advertising_channel_type = client.enums.AdvertisingChannelTypeEnum.PERFORMANCE_MAX
        camp.status = client.enums.CampaignStatusEnum.PAUSED
        camp.campaign_budget = budget_resource
        bs = args.bidding_strategy
        if bs == "MAXIMIZE_CONVERSIONS":
            camp.maximize_conversions.CopyFrom(client.get_type("MaximizeConversions"))
        elif bs == "MAXIMIZE_CONVERSION_VALUE":
            mcv = client.get_type("MaximizeConversionValue")
            if args.target_roas:
                mcv.target_roas = args.target_roas
            camp.maximize_conversion_value.CopyFrom(mcv)
        elif bs == "TARGET_CPA":
            mc = client.get_type("MaximizeConversions")
            mc.target_cpa_micros = int(args.target_cpa_dollars * 1_000_000)
            camp.maximize_conversions.CopyFrom(mc)
        elif bs == "TARGET_ROAS":
            mcv = client.get_type("MaximizeConversionValue")
            mcv.target_roas = args.target_roas
            camp.maximize_conversion_value.CopyFrom(mcv)
        # PMax-specific: enable URL expansion + final URL suffix toggles
        camp.url_expansion_opt_out = False
        camp.start_date = (dt.date.today() + dt.timedelta(days=1)).strftime("%Y%m%d")
        resp = camp_svc.mutate_campaigns(customer_id=customer_id, operations=[camp_op])
        camp_resource = resp.results[0].resource_name
        camp_id = camp_resource.split("/")[-1]
        print(f"✅ Campaign:      {camp_resource}")

        # 3. Geo targeting
        geo_svc = client.get_service("CampaignCriterionService")
        const_svc = client.get_service("GeoTargetConstantService")
        geo_ops = []
        for code in [c.strip().upper() for c in args.countries.split(",")]:
            sugg = const_svc.suggest_geo_target_constants(locale="en", country_code=code)
            if not sugg.geo_target_constant_suggestions:
                continue
            geo_const = sugg.geo_target_constant_suggestions[0].geo_target_constant
            op = client.get_type("CampaignCriterionOperation")
            crit = op.create
            crit.campaign = camp_resource
            crit.location.geo_target_constant = geo_const.resource_name
            geo_ops.append(op)
        if geo_ops:
            geo_svc.mutate_campaign_criteria(customer_id=customer_id, operations=geo_ops)
        print(f"✅ Geo:           {args.countries}")

        # 4. Asset group
        ag_svc = client.get_service("AssetGroupService")
        ag_op = client.get_type("AssetGroupOperation")
        ag = ag_op.create
        ag.name = f"{full_name} - Asset Group 1"
        ag.campaign = camp_resource
        ag.final_urls.append(args.final_url)
        ag.status = client.enums.AssetGroupStatusEnum.PAUSED
        resp = ag_svc.mutate_asset_groups(customer_id=customer_id, operations=[ag_op])
        ag_resource = resp.results[0].resource_name
        print(f"✅ Asset Group:   {ag_resource}")

        # 5. Upload assets + link to asset group
        link_ops = []

        # Business name
        bn_resource = upload_text_asset(client, customer_id, args.business_name)
        link_ops.append(link_asset_to_group(client, customer_id, bn_resource, ag_resource, "BUSINESS_NAME"))
        print(f"✅ Business name: {bn_resource}")

        # Text assets
        for h in args.headlines:
            r = upload_text_asset(client, customer_id, h)
            link_ops.append(link_asset_to_group(client, customer_id, r, ag_resource, "HEADLINE"))
        for h in args.long_headlines:
            r = upload_text_asset(client, customer_id, h)
            link_ops.append(link_asset_to_group(client, customer_id, r, ag_resource, "LONG_HEADLINE"))
        for d in args.descriptions:
            r = upload_text_asset(client, customer_id, d)
            link_ops.append(link_asset_to_group(client, customer_id, r, ag_resource, "DESCRIPTION"))
        print(f"✅ Text assets:   {len(args.headlines)} headline + "
              f"{len(args.long_headlines)} long + "
              f"{len(args.descriptions)} description")

        # Image assets
        def upload_and_link_images(paths, field_type, prefix):
            for i, path in enumerate(paths):
                r = upload_image_asset(client, customer_id, path,
                                       name=f"{full_name} {prefix} {i+1}",
                                       image_type=field_type)
                link_ops.append(link_asset_to_group(client, customer_id, r, ag_resource, field_type))
        upload_and_link_images(args.marketing_images, "MARKETING_IMAGE", "marketing")
        upload_and_link_images(args.square_images, "SQUARE_MARKETING_IMAGE", "square")
        upload_and_link_images(args.portrait_images, "PORTRAIT_MARKETING_IMAGE", "portrait")
        upload_and_link_images(args.logo_images, "LOGO", "logo")
        upload_and_link_images(args.landscape_logos, "LANDSCAPE_LOGO", "landscape-logo")
        print(f"✅ Image assets:  {len(args.marketing_images)} marketing + "
              f"{len(args.square_images)} square + "
              f"{len(args.portrait_images)} portrait + "
              f"{len(args.logo_images)} logo + "
              f"{len(args.landscape_logos)} landscape-logo")

        # Video assets
        for v in args.videos:
            r = upload_video_asset(client, customer_id, v)
            link_ops.append(link_asset_to_group(client, customer_id, r, ag_resource, "YOUTUBE_VIDEO"))
        if args.videos:
            print(f"✅ Videos:        {len(args.videos)} (YouTube)")

        # Send all asset-group-asset links in one batch
        link_svc = client.get_service("AssetGroupAssetService")
        link_svc.mutate_asset_group_assets(customer_id=customer_id, operations=link_ops)

        # 6. Asset Group Listing Group root (required for PMax even without Merchant Center feed)
        lg_svc = client.get_service("AssetGroupListingGroupFilterService")
        lg_op = client.get_type("AssetGroupListingGroupFilterOperation")
        lg = lg_op.create
        lg.asset_group = ag_resource
        lg.type_ = client.enums.ListingGroupFilterTypeEnum.UNIT_INCLUDED
        lg.listing_source = client.enums.ListingGroupFilterListingSourceEnum.SHOPPING
        try:
            lg_svc.mutate_asset_group_listing_group_filters(customer_id=customer_id, operations=[lg_op])
            print(f"✅ Listing root:  created (Shopping)")
        except GoogleAdsException:
            # Some accounts without Merchant Center won't accept this — that's OK for non-shopping PMax
            print(f"⚠️  Skipped listing-group root (no Merchant Center / non-shopping PMax)")

    except GoogleAdsException as e:
        fail_on_ads_exception(e, "PMax build")

    print("\n🎉 Built. All resources are PAUSED.")
    print(f"    Campaign:     {camp_resource} (id={camp_id})")
    print(f"    Asset Group:  {ag_resource}")
    print("\nNext: Show the user a preview in Google Ads UI.")
    print("After approval, activate by setting campaign + asset_group status to ENABLED.")


if __name__ == "__main__":
    main()

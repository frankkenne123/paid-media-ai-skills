#!/usr/bin/env python3
"""
Build a full Meta campaign end-to-end: campaign → ad set → upload image → adcreative → ad.

All in PAUSED state. the user approves before activating.

Usage:
  python3 build_meta_campaign_full.py \
    --account act_XXXXXXXX \
    --client "Acme Co" \
    --campaign-name "AI - Spring Acquisition" \
    --daily-budget 50 \
    --landing-url https://acme.example.com/collections/new \
    --headline "Hand-Crafted Statement Pieces" \
    --primary-text "Discover the bold designs trusted by 2M+ customers..." \
    --description "Free shipping over $50" \
    --cta SHOP_NOW \
    --image /path/to/creative.png \
    --page-id <PIXEL_ID>_PAGE \
    --pixel-id <PIXEL_ID> \
    --age-min 25 --age-max 55 --countries US

Use --advantage-plus to skip manual targeting and let Meta optimize.
Use --dry-run to print the API calls that would fire without making them.

The image MUST already be saved locally — generate it first with generate_image()
and write it to /tmp/, then pass the path here.
"""

import argparse, datetime as dt, json, os, sys
from pathlib import Path
import requests
from dotenv import load_dotenv

load_dotenv()
API = "https://graph.facebook.com/v20.0"
TOKEN = os.getenv("META_ACCESS_TOKEN")

CTA_TYPES = {"SHOP_NOW", "LEARN_MORE", "SIGN_UP", "BOOK_TRAVEL", "DOWNLOAD",
             "GET_OFFER", "CONTACT_US", "SUBSCRIBE", "APPLY_NOW", "GET_QUOTE"}


def fail(msg, resp=None):
    print(f"❌ {msg}")
    if resp is not None:
        try: print(json.dumps(resp.json(), indent=2))
        except Exception: print(resp.text)
    sys.exit(1)


def post(path, params, dry):
    if dry:
        print(f"DRY POST {API}{path}")
        print(json.dumps({k: (v if k != "access_token" else "<redacted>") for k, v in params.items()}, indent=2))
        return {"id": "DRY_RUN_ID"}
    r = requests.post(f"{API}{path}", data=params, timeout=60)
    if r.status_code != 200:
        fail(f"POST {path} failed ({r.status_code})", r)
    return r.json()


def upload_image(account_id, image_path, dry):
    """Upload local image to Meta — returns the hash."""
    if not Path(image_path).exists():
        fail(f"Image not found: {image_path}")
    if dry:
        print(f"DRY upload image {image_path} → /act_X/adimages")
        return "DRY_HASH"
    with open(image_path, "rb") as fh:
        r = requests.post(
            f"{API}/{account_id}/adimages",
            data={"access_token": TOKEN},
            files={"filename": fh},
            timeout=120,
        )
    if r.status_code != 200:
        fail("image upload failed", r)
    images = r.json().get("images", {})
    h = next(iter(images.values()), {}).get("hash")
    if not h:
        fail("upload succeeded but no hash returned", r)
    return h


def main():
    p = argparse.ArgumentParser()
    # Required
    p.add_argument("--account", required=True, help="Ad account ID with act_ prefix")
    p.add_argument("--client", required=True, help="Client name (used in campaign labeling)")
    p.add_argument("--campaign-name", required=True)
    p.add_argument("--daily-budget", type=float, default=None,
                   help="In dollars (e.g. 50 = $50/day). Required unless --reuse-adset is set.")
    p.add_argument("--landing-url", required=True)
    p.add_argument("--headline", required=True, help="Short — max 40 chars renders cleanly")
    p.add_argument("--primary-text", required=True, help="Body — keep under 125 chars for full visibility")
    p.add_argument("--cta", required=True, choices=sorted(CTA_TYPES))
    p.add_argument("--image", required=True, help="Path to local image file (PNG/JPG)")
    p.add_argument("--page-id", required=True, help="Facebook Page ID (required for every ad)")
    p.add_argument("--pixel-id", required=True, help="Meta Pixel ID for conversion tracking")
    # Optional
    p.add_argument("--description", default="", help="Sub-headline below CTA")
    p.add_argument("--objective", default="OUTCOME_SALES",
                   choices=["OUTCOME_SALES", "OUTCOME_LEADS", "OUTCOME_TRAFFIC",
                            "OUTCOME_AWARENESS", "OUTCOME_ENGAGEMENT"])
    p.add_argument("--manual-targeting", action="store_true",
                   help="Override the user's standing rule (Advantage+ broad). Only use when explicitly told to.")
    p.add_argument("--age-min", type=int, default=25, help="Only used with --manual-targeting")
    p.add_argument("--age-max", type=int, default=55, help="Only used with --manual-targeting")
    p.add_argument("--countries", default="US", help="Comma-separated country codes")
    p.add_argument("--instagram-account-id", default=None,
                   help="Optional — if provided, ad runs on IG too")
    p.add_argument("--reuse-adset", default=None, metavar="ADSET_ID",
                   help="Skip campaign + ad-set creation; add a new ad to this existing ad set. "
                        "Use this to test 3 creative variants on the same hook in one ad set: "
                        "run the script 3 times with --reuse-adset <ID>, varying --image (and "
                        "optionally --headline / --primary-text). All ads land PAUSED.")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    if not TOKEN and not args.dry_run:
        fail("META_ACCESS_TOKEN missing in .env")

    if not args.reuse_adset and args.daily_budget is None:
        fail("--daily-budget is required when not using --reuse-adset")

    stamp = dt.datetime.now().strftime("%m%d_%H%M")
    full_name = f"{args.client} — {args.campaign_name} — {stamp}"
    print(f"🏗️  Building: {full_name}")
    print(f"    Account: {args.account}")
    if args.reuse_adset:
        print(f"    Mode:    VARIANT — adding new ad to existing ad set {args.reuse_adset}")
    else:
        print(f"    Budget:  ${args.daily_budget}/day")
    print(f"    Status:  PAUSED (you must activate manually after the user approves)\n")

    if args.reuse_adset:
        # Variant mode — skip campaign + adset creation, reuse the existing ad set
        adset_id = args.reuse_adset
        campaign_id = None
        print(f"➡️  Reusing Ad Set: {adset_id} (skipping campaign + adset creation)")
    else:
        # 1. Campaign
        camp = post(f"/{args.account}/campaigns", {
            "name": full_name,
            "objective": args.objective,
            "status": "PAUSED",
            "special_ad_categories": "[]",
            "buying_type": "AUCTION",
            "access_token": TOKEN,
        }, args.dry_run)
        campaign_id = camp["id"]
        print(f"✅ Campaign:  {campaign_id}")

        # 2. Ad set — default is Advantage+ broad per the user's standing rule
        targeting = {
            "geo_locations": {"countries": [c.strip() for c in args.countries.split(",")]},
        }
        if args.manual_targeting:
            targeting["age_min"] = args.age_min
            targeting["age_max"] = args.age_max
        else:
            targeting["targeting_automation"] = {"advantage_audience": 1}

        adset_params = {
            "name": f"{args.client} — Ad Set — {stamp}",
            "campaign_id": campaign_id,
            "daily_budget": int(args.daily_budget * 100),
            "billing_event": "IMPRESSIONS",
            "optimization_goal": "OFFSITE_CONVERSIONS",
            "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
            "targeting": json.dumps(targeting),
            "status": "PAUSED",
            "promoted_object": json.dumps({"pixel_id": args.pixel_id, "custom_event_type": "PURCHASE"}),
            "start_time": (dt.datetime.utcnow() + dt.timedelta(hours=1)).isoformat() + "Z",
            "access_token": TOKEN,
        }
        adset = post(f"/{args.account}/adsets", adset_params, args.dry_run)
        adset_id = adset["id"]
        print(f"✅ Ad Set:    {adset_id}")

    # 3. Image upload
    image_hash = upload_image(args.account, args.image, args.dry_run)
    print(f"✅ Image:     {image_hash}")

    # 4. Ad creative
    link_data = {
        "link": args.landing_url,
        "message": args.primary_text,
        "name": args.headline,
        "image_hash": image_hash,
        "call_to_action": {"type": args.cta, "value": {"link": args.landing_url}},
    }
    if args.description:
        link_data["description"] = args.description

    object_story_spec = {"page_id": args.page_id, "link_data": link_data}
    if args.instagram_account_id:
        object_story_spec["instagram_actor_id"] = args.instagram_account_id

    creative = post(f"/{args.account}/adcreatives", {
        "name": f"{args.client} — Creative — {stamp}",
        "object_story_spec": json.dumps(object_story_spec),
        "access_token": TOKEN,
    }, args.dry_run)
    creative_id = creative["id"]
    print(f"✅ Creative:  {creative_id}")

    # 5. Ad
    ad = post(f"/{args.account}/ads", {
        "name": f"{args.client} — Ad — {stamp}",
        "adset_id": adset_id,
        "creative": json.dumps({"creative_id": creative_id}),
        "status": "PAUSED",
        "access_token": TOKEN,
    }, args.dry_run)
    ad_id = ad["id"]
    print(f"✅ Ad:        {ad_id}\n")

    print("🎉 Built. All resources are PAUSED.")
    if campaign_id:
        print(f"    Campaign:  {campaign_id}")
    print(f"    Ad Set:    {adset_id}")
    print(f"    Creative:  {creative_id}")
    print(f"    Ad:        {ad_id}")
    if args.reuse_adset:
        print("\nNext: Show the user in Discord. After approval, activate the ad alone via:")
        print(f"  curl -X POST '{API}/{ad_id}' -d 'access_token=$META_ACCESS_TOKEN' -d 'status=ACTIVE'")
    else:
        print("\nNext: Show the user in Discord. After approval, activate via:")
        print(f"  curl -X POST '{API}/{campaign_id}' -d 'access_token=$META_ACCESS_TOKEN' -d 'status=ACTIVE'")


if __name__ == "__main__":
    main()

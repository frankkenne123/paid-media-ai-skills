#!/usr/bin/env python3
"""
Build a full TikTok Ads campaign end-to-end:
  upload video → campaign → ad group → ad.

All in PAUSED state. The user approves before activating.

Usage:
  python3 build_tiktok_campaign.py \
    --campaign-name "Spring ACQ" \
    --client "Acme Co" \
    --daily-budget 50 \
    --landing-url "https://acme.example.com/landing" \
    --ad-text "Real 14k gold chains, lifetime warranty. Shop the new drop →" \
    --cta SHOP_NOW \
    --video /tmp/acme_video.mp4 \
    --countries US

Optional:
  --advertiser-id <ID>       Override TIKTOK_ADVERTISER_ID from .env
  --identity-id <ID>         Override TIKTOK_IDENTITY_ID from .env (the TikTok
                             account or custom identity that ads run from)
  --identity-type CUSTOMIZED_USER | AUTHORIZED_BC_ACCOUNT | TT_USER  (default CUSTOMIZED_USER)
  --pixel-id <ID>            Required for CONVERSIONS objective (default uses TIKTOK_PIXEL_ID)
  --objective TRAFFIC | CONVERSIONS | REACH | VIDEO_VIEWS  (default CONVERSIONS)
  --age-groups               e.g. "AGE_18_24,AGE_25_34" — default unset (broad)
  --gender MALE | FEMALE     default unset (broad)
  --cover-image PATH         Upload a custom cover frame (otherwise TikTok auto-picks)
  --dry-run                  Print mutations without sending

The video file MUST already be saved locally (TikTok ads are video-first; static
image ads have very limited reach). If you don't have a video generator wired
up, point --video at a manually-produced .mp4 file.

Required .env keys:
  TIKTOK_ACCESS_TOKEN     — long-lived access token from TikTok for Business
  TIKTOK_ADVERTISER_ID    — advertiser account ID
  TIKTOK_IDENTITY_ID      — identity (custom user or BC-authorized account) the ads run from
  TIKTOK_PIXEL_ID         — pixel for CONVERSIONS objective (optional otherwise)
"""

import argparse, datetime as dt, hashlib, json, os, sys
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()
API = "https://business-api.tiktok.com/open_api/v1.3"
TOKEN = os.getenv("TIKTOK_ACCESS_TOKEN")

CTA_TYPES = {
    "SHOP_NOW", "LEARN_MORE", "SIGN_UP", "DOWNLOAD",
    "APPLY_NOW", "GET_QUOTE", "ORDER_NOW", "SUBSCRIBE",
    "VIEW_NOW", "BOOK_NOW", "INSTALL_NOW", "WATCH_NOW",
}


def headers():
    return {"Access-Token": TOKEN, "Content-Type": "application/json"}


def call(method, path, payload=None, files=None, dry=False):
    url = f"{API}{path}"
    if dry:
        print(f"DRY {method} {path}")
        if payload:
            print(json.dumps(payload, indent=2))
        return {"data": {"id": "DRY_RUN_ID", "video_id": "DRY_RUN_VIDEO"}}
    if files:
        # multipart — strip Content-Type so requests sets the boundary
        h = {"Access-Token": TOKEN}
        r = requests.request(method, url, headers=h, data=payload, files=files, timeout=180)
    else:
        r = requests.request(method, url, headers=headers(),
                             json=payload if method in ("POST", "PUT") else None,
                             params=payload if method == "GET" else None,
                             timeout=60)
    if r.status_code != 200:
        print(f"❌ HTTP {r.status_code} on {method} {path}")
        print(r.text)
        sys.exit(1)
    body = r.json()
    if body.get("code") != 0:
        print(f"❌ TikTok API error on {method} {path}: code={body.get('code')} msg={body.get('message')}")
        print(json.dumps(body, indent=2))
        sys.exit(1)
    return body


def file_md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def upload_video(advertiser_id, video_path, dry):
    if dry:
        print(f"DRY upload video {video_path} → /file/video/ad/upload/")
        return "DRY_VIDEO_ID"
    if not Path(video_path).exists():
        sys.exit(f"❌ video not found: {video_path}")
    with open(video_path, "rb") as f:
        files = {"video_file": (Path(video_path).name, f, "video/mp4")}
        data = {
            "advertiser_id": advertiser_id,
            "upload_type": "UPLOAD_BY_FILE",
            "video_signature": file_md5(video_path),
        }
        body = call("POST", "/file/video/ad/upload/", payload=data, files=files)
    vids = body.get("data", [])
    if isinstance(vids, list) and vids:
        return vids[0].get("video_id")
    return body.get("data", {}).get("video_id")


def upload_cover(advertiser_id, image_path, dry):
    if not image_path:
        return None
    if dry:
        print(f"DRY upload cover {image_path} → /file/image/ad/upload/")
        return "DRY_IMAGE_ID"
    if not Path(image_path).exists():
        sys.exit(f"❌ cover image not found: {image_path}")
    with open(image_path, "rb") as f:
        files = {"image_file": (Path(image_path).name, f, "image/png")}
        data = {
            "advertiser_id": advertiser_id,
            "upload_type": "UPLOAD_BY_FILE",
            "image_signature": file_md5(image_path),
        }
        body = call("POST", "/file/image/ad/upload/", payload=data, files=files)
    imgs = body.get("data", {})
    return imgs.get("image_id") if isinstance(imgs, dict) else None


def main():
    p = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                description=__doc__)
    p.add_argument("--client", required=True)
    p.add_argument("--campaign-name", required=True)
    p.add_argument("--daily-budget", type=float, required=True, help="In dollars (e.g. 50 = $50/day)")
    p.add_argument("--landing-url", required=True)
    p.add_argument("--ad-text", required=True, help="Ad caption — keep under 100 chars for full visibility")
    p.add_argument("--cta", required=True, choices=sorted(CTA_TYPES))
    p.add_argument("--video", required=True, help="Path to local .mp4 video file")
    p.add_argument("--cover-image", help="Path to local cover image (otherwise auto)")
    p.add_argument("--countries", default="US", help="Comma-separated country codes (US,CA,GB...)")
    p.add_argument("--objective", default="CONVERSIONS",
                   choices=["TRAFFIC", "CONVERSIONS", "REACH", "VIDEO_VIEWS"])
    p.add_argument("--age-groups", default="",
                   help='Comma-separated, e.g. "AGE_25_34,AGE_35_44". Empty = broad')
    p.add_argument("--gender", choices=["MALE", "FEMALE"], help="Empty = broad")
    p.add_argument("--advertiser-id", default=os.getenv("TIKTOK_ADVERTISER_ID"))
    p.add_argument("--identity-id", default=os.getenv("TIKTOK_IDENTITY_ID"))
    p.add_argument("--identity-type", default="CUSTOMIZED_USER",
                   choices=["CUSTOMIZED_USER", "AUTHORIZED_BC_ACCOUNT", "TT_USER"])
    p.add_argument("--pixel-id", default=os.getenv("TIKTOK_PIXEL_ID"))
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    if not args.dry_run:
        missing = []
        if not TOKEN: missing.append("TIKTOK_ACCESS_TOKEN")
        if not args.advertiser_id: missing.append("TIKTOK_ADVERTISER_ID")
        if not args.identity_id: missing.append("TIKTOK_IDENTITY_ID")
        if args.objective == "CONVERSIONS" and not args.pixel_id:
            missing.append("TIKTOK_PIXEL_ID (required for CONVERSIONS)")
        if missing:
            sys.exit(f"❌ Missing required values (set in .env or pass via flags): {', '.join(missing)}")

    advertiser_id = args.advertiser_id
    stamp = dt.datetime.now().strftime("%m%d_%H%M")
    full_name = f"{args.client} — {args.campaign_name} — {stamp}"

    print(f"🏗️  Building TikTok campaign: {full_name}")
    print(f"    Advertiser: {advertiser_id}")
    print(f"    Budget:     ${args.daily_budget}/day")
    print(f"    Objective:  {args.objective}")
    print(f"    Status:     PAUSED (activate manually after approval)\n")

    # 1. Upload video
    video_id = upload_video(advertiser_id, args.video, args.dry_run)
    print(f"✅ Video:     {video_id}")

    # 2. Optional cover
    image_id = upload_cover(advertiser_id, args.cover_image, args.dry_run)
    if image_id:
        print(f"✅ Cover:     {image_id}")

    # 3. Campaign
    campaign_payload = {
        "advertiser_id": advertiser_id,
        "campaign_name": full_name,
        "objective_type": args.objective,
        "budget_mode": "BUDGET_MODE_DAY",
        "budget": args.daily_budget,
        "operation_status": "DISABLE",   # PAUSED equivalent
    }
    camp_resp = call("POST", "/campaign/create/", campaign_payload, dry=args.dry_run)
    campaign_id = camp_resp.get("data", {}).get("campaign_id") or "DRY_RUN_ID"
    print(f"✅ Campaign:  {campaign_id}")

    # 4. Ad group
    countries = [c.strip() for c in args.countries.split(",")]
    adgroup_payload = {
        "advertiser_id": advertiser_id,
        "campaign_id": campaign_id,
        "adgroup_name": f"{full_name} — Ad Group",
        "placement_type": "PLACEMENT_TYPE_AUTOMATIC",   # equivalent to Meta Advantage+ broad
        "location_ids": [],   # populated below
        "budget_mode": "BUDGET_MODE_DAY",
        "budget": args.daily_budget,
        "schedule_type": "SCHEDULE_FROM_NOW",
        "schedule_start_time": (dt.datetime.utcnow() + dt.timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S"),
        "billing_event": "OCPM" if args.objective == "CONVERSIONS" else "CPM",
        "bid_type": "BID_TYPE_NO_BID",   # tCPA / lowest-cost equivalent
        "operation_status": "DISABLE",
        "identity_id": args.identity_id,
        "identity_type": args.identity_type,
        "creative_material_mode": "CUSTOM",
    }
    if args.objective == "CONVERSIONS":
        adgroup_payload["optimization_goal"] = "CONVERT"
        adgroup_payload["pixel_id"] = args.pixel_id
        adgroup_payload["optimization_event"] = "ON_WEB_ORDER"
    elif args.objective == "TRAFFIC":
        adgroup_payload["optimization_goal"] = "CLICK"
    elif args.objective == "REACH":
        adgroup_payload["optimization_goal"] = "REACH"
    elif args.objective == "VIDEO_VIEWS":
        adgroup_payload["optimization_goal"] = "VIDEO_VIEW"

    # Geo: TikTok wants integer location_ids — quick lookup helper
    if not args.dry_run and countries:
        loc_resp = call("GET", "/tool/region/", {"advertiser_id": advertiser_id})
        all_locs = loc_resp.get("data", {}).get("regions", []) if isinstance(loc_resp.get("data"), dict) else []
        country_lookup = {r.get("region_code"): r.get("location_id") for r in all_locs if r.get("level") == "COUNTRY"}
        ids = [country_lookup[c] for c in countries if c in country_lookup]
        if ids:
            adgroup_payload["location_ids"] = ids
        else:
            print(f"⚠️  could not resolve country codes {countries} to location_ids — leaving empty (broad)")
    if args.age_groups:
        adgroup_payload["age_groups"] = [a.strip() for a in args.age_groups.split(",")]
    if args.gender:
        adgroup_payload["gender"] = args.gender

    ag_resp = call("POST", "/adgroup/create/", adgroup_payload, dry=args.dry_run)
    adgroup_id = ag_resp.get("data", {}).get("adgroup_id") or "DRY_RUN_ID"
    print(f"✅ Ad Group:  {adgroup_id}")

    # 5. Ad
    creative = {
        "ad_format": "SINGLE_VIDEO",
        "ad_name": f"{full_name} — Ad",
        "ad_text": args.ad_text,
        "video_id": video_id,
        "call_to_action": args.cta,
        "landing_page_url": args.landing_url,
        "identity_id": args.identity_id,
        "identity_type": args.identity_type,
    }
    if image_id:
        creative["image_ids"] = [image_id]

    ad_payload = {
        "advertiser_id": advertiser_id,
        "adgroup_id": adgroup_id,
        "creatives": [creative],
        "operation_status": "DISABLE",
    }
    ad_resp = call("POST", "/ad/create/", ad_payload, dry=args.dry_run)
    ad_id = ad_resp.get("data", {}).get("ad_ids", ["DRY_RUN_ID"])
    if isinstance(ad_id, list):
        ad_id = ad_id[0]
    print(f"✅ Ad:        {ad_id}\n")

    print("🎉 Built. All resources are PAUSED.")
    print(f"    Campaign:  {campaign_id}")
    print(f"    Ad Group:  {adgroup_id}")
    print(f"    Ad:        {ad_id}")
    print("\nNext: Show the user a preview in TikTok Ads Manager.")
    print("After approval, activate by updating operation_status to ENABLE.")


if __name__ == "__main__":
    main()

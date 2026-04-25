#!/usr/bin/env python3
"""
Activate PAUSED Meta or Google Ads resources after the user has approved them.

Cascades activation: campaign ACTIVE → all ad sets/groups ACTIVE → all ads ACTIVE.
Always asks for explicit confirmation before sending.

Usage:
  # Meta — activate a single campaign and everything under it
  python3 activate_paused_resources.py --platform meta --campaign-id <CAMPAIGN_ID>

  # Meta — activate JUST a specific ad (e.g. a creative variant added with --reuse-adset)
  python3 activate_paused_resources.py --platform meta --ad-id <AD_ID>

  # Google — activate a Search or PMax campaign and everything under it
  python3 activate_paused_resources.py --platform google --customer XXXXXXXXXX --campaign-id <CAMPAIGN_ID>

  # Skip the confirmation prompt (use only if you've already shown the user the preview)
  python3 activate_paused_resources.py --platform meta --campaign-id <ID> --yes

  # See what would happen without sending mutations
  python3 activate_paused_resources.py --platform meta --campaign-id <ID> --dry-run
"""

import argparse, json, os, sys
from pathlib import Path

# Use the workspace venv if it exists
_venv = Path(__file__).resolve().parent / "venv" / "lib" / "python3.10" / "site-packages"
if _venv.exists():
    sys.path.insert(0, str(_venv))

import requests
from dotenv import load_dotenv

load_dotenv()
META_API = "https://graph.facebook.com/v20.0"
META_TOKEN = os.getenv("META_ACCESS_TOKEN")


# ─── Meta ─────────────────────────────────────────────────────────────────────
def meta_get(path, **params):
    params["access_token"] = META_TOKEN
    r = requests.get(f"{META_API}{path}", params=params, timeout=30)
    if r.status_code != 200:
        sys.exit(f"❌ Meta GET {path} failed: {r.status_code} {r.text}")
    return r.json()


def meta_post(path, **params):
    params["access_token"] = META_TOKEN
    r = requests.post(f"{META_API}{path}", data=params, timeout=30)
    if r.status_code != 200:
        sys.exit(f"❌ Meta POST {path} failed: {r.status_code} {r.text}")
    return r.json()


def meta_describe_campaign(campaign_id):
    """Pull the campaign + all ad sets + all ads under it."""
    camp = meta_get(f"/{campaign_id}", fields="id,name,status,objective,daily_budget,lifetime_budget")
    adsets = meta_get(f"/{campaign_id}/adsets",
                      fields="id,name,status,daily_budget", limit=200).get("data", [])
    ads_by_adset = {}
    for adset in adsets:
        ads = meta_get(f"/{adset['id']}/ads",
                       fields="id,name,status", limit=200).get("data", [])
        ads_by_adset[adset["id"]] = ads
    return camp, adsets, ads_by_adset


def meta_describe_ad(ad_id):
    ad = meta_get(f"/{ad_id}", fields="id,name,status,adset_id,campaign_id")
    return ad


def meta_activate(resource_id, dry):
    if dry:
        print(f"  DRY POST /{resource_id} status=ACTIVE")
        return
    meta_post(f"/{resource_id}", status="ACTIVE")


def activate_meta_campaign(campaign_id, dry, skip_confirm):
    print(f"📋 Pulling campaign tree for {campaign_id}…")
    camp, adsets, ads_by_adset = meta_describe_campaign(campaign_id)

    print(f"\nCampaign: {camp['name']} ({campaign_id}) — currently {camp['status']}")
    paused_adsets = [a for a in adsets if a["status"] == "PAUSED"]
    paused_ads = [(adset["id"], ad) for adset in adsets for ad in ads_by_adset[adset["id"]] if ad["status"] == "PAUSED"]

    print(f"  → {len(paused_adsets)}/{len(adsets)} ad sets PAUSED")
    for a in paused_adsets:
        print(f"     ad set: {a['name']} ({a['id']}) — daily ${int(a.get('daily_budget') or 0)/100:.0f}")
    print(f"  → {len(paused_ads)}/{sum(len(v) for v in ads_by_adset.values())} ads PAUSED")
    for adset_id, ad in paused_ads:
        print(f"     ad: {ad['name']} ({ad['id']})")

    if camp["status"] == "ACTIVE" and not paused_adsets and not paused_ads:
        print("\n✅ Already fully active. Nothing to do.")
        return

    if not skip_confirm:
        print()
        ans = input("Activate campaign + all paused ad sets + all paused ads? [yes/N] ")
        if ans.strip().lower() not in ("y", "yes"):
            print("Aborted.")
            sys.exit(0)

    print()
    if camp["status"] == "PAUSED":
        meta_activate(camp["id"], dry)
        print(f"✅ Campaign  ACTIVE: {camp['id']}")
    for a in paused_adsets:
        meta_activate(a["id"], dry)
        print(f"✅ Ad Set    ACTIVE: {a['id']} ({a['name']})")
    for adset_id, ad in paused_ads:
        meta_activate(ad["id"], dry)
        print(f"✅ Ad        ACTIVE: {ad['id']} ({ad['name']})")
    print("\n🚀 Done.")


def activate_meta_ad(ad_id, dry, skip_confirm):
    print(f"📋 Looking up ad {ad_id}…")
    ad = meta_describe_ad(ad_id)

    print(f"\nAd: {ad['name']} ({ad_id}) — currently {ad['status']}")
    print(f"  ad_set_id={ad.get('adset_id')}  campaign_id={ad.get('campaign_id')}")

    if ad["status"] == "ACTIVE":
        print("✅ Already active. Nothing to do.")
        return
    if ad["status"] != "PAUSED":
        print(f"⚠️  Ad is in status '{ad['status']}', not PAUSED. Activate anyway?")
        if not skip_confirm:
            ans = input("  Activate anyway? [yes/N] ")
            if ans.strip().lower() not in ("y", "yes"):
                sys.exit(0)

    if not skip_confirm:
        ans = input(f"\nActivate ad {ad_id}? [yes/N] ")
        if ans.strip().lower() not in ("y", "yes"):
            print("Aborted.")
            sys.exit(0)

    meta_activate(ad_id, dry)
    print(f"\n✅ Ad ACTIVE: {ad_id}")
    print("Note: parent ad set / campaign must already be ACTIVE for delivery to start.")


# ─── Google Ads ───────────────────────────────────────────────────────────────
def build_google_client():
    from google.ads.googleads.client import GoogleAdsClient
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


def activate_google_campaign(customer_id, campaign_id, dry, skip_confirm):
    customer_id = customer_id.replace("-", "")
    client = build_google_client()
    ga_service = client.get_service("GoogleAdsService")

    # Detect channel type — PMax has asset_groups, Search has ad_groups+ads
    q = f"""
        SELECT campaign.id, campaign.name, campaign.status, campaign.advertising_channel_type
        FROM campaign WHERE campaign.id = {campaign_id}
    """
    rows = list(ga_service.search(customer_id=customer_id, query=q))
    if not rows:
        sys.exit(f"❌ Campaign {campaign_id} not found in customer {customer_id}")
    camp = rows[0].campaign
    channel = camp.advertising_channel_type.name
    print(f"\nCampaign: {camp.name} ({campaign_id}) — {camp.status.name}, channel={channel}")

    # Collect children
    if channel == "PERFORMANCE_MAX":
        q2 = f"""
            SELECT asset_group.id, asset_group.name, asset_group.status
            FROM asset_group WHERE asset_group.campaign = 'customers/{customer_id}/campaigns/{campaign_id}'
        """
        children = [(r.asset_group.id, r.asset_group.name, r.asset_group.status, "asset_group")
                    for r in ga_service.search(customer_id=customer_id, query=q2)]
    else:
        q2 = f"""
            SELECT ad_group.id, ad_group.name, ad_group.status
            FROM ad_group WHERE ad_group.campaign = 'customers/{customer_id}/campaigns/{campaign_id}'
        """
        ad_groups = [(r.ad_group.id, r.ad_group.name, r.ad_group.status, "ad_group")
                     for r in ga_service.search(customer_id=customer_id, query=q2)]
        ads = []
        for ag_id, _, _, _ in ad_groups:
            q3 = f"""
                SELECT ad_group_ad.ad.id, ad_group_ad.ad.name, ad_group_ad.status, ad_group_ad.resource_name
                FROM ad_group_ad WHERE ad_group.id = {ag_id}
            """
            ads.extend(
                (r.ad_group_ad.ad.id, r.ad_group_ad.ad.name or f"ad-{r.ad_group_ad.ad.id}",
                 r.ad_group_ad.status, "ad_group_ad", r.ad_group_ad.resource_name)
                for r in ga_service.search(customer_id=customer_id, query=q3)
            )
        children = ad_groups + [(a[0], a[1], a[2], a[3]) for a in ads]

    paused_kids = [c for c in children if c[2].name == "PAUSED"]
    print(f"  → {len(paused_kids)}/{len(children)} children PAUSED")
    for child in paused_kids:
        print(f"     {child[3]}: {child[1]} ({child[0]})")

    if camp.status.name == "ENABLED" and not paused_kids:
        print("\n✅ Already fully enabled. Nothing to do.")
        return

    if not skip_confirm:
        ans = input("\nEnable campaign + all paused children? [yes/N] ")
        if ans.strip().lower() not in ("y", "yes"):
            print("Aborted.")
            sys.exit(0)

    if dry:
        print("\n🔍 DRY RUN — no mutations sent.")
        return

    # Activate campaign
    if camp.status.name == "PAUSED":
        camp_svc = client.get_service("CampaignService")
        op = client.get_type("CampaignOperation")
        op.update.resource_name = f"customers/{customer_id}/campaigns/{campaign_id}"
        op.update.status = client.enums.CampaignStatusEnum.ENABLED
        client.copy_from(op.update_mask, client.get_type("FieldMask")(paths=["status"]))
        camp_svc.mutate_campaigns(customer_id=customer_id, operations=[op])
        print(f"\n✅ Campaign  ENABLED: {campaign_id}")

    # Activate children
    if channel == "PERFORMANCE_MAX":
        ag_svc = client.get_service("AssetGroupService")
        ops = []
        for child_id, name, status, _ in paused_kids:
            op = client.get_type("AssetGroupOperation")
            op.update.resource_name = f"customers/{customer_id}/assetGroups/{child_id}"
            op.update.status = client.enums.AssetGroupStatusEnum.ENABLED
            client.copy_from(op.update_mask, client.get_type("FieldMask")(paths=["status"]))
            ops.append(op)
        if ops:
            ag_svc.mutate_asset_groups(customer_id=customer_id, operations=ops)
            for c in paused_kids:
                print(f"✅ Asset Group ENABLED: {c[0]} ({c[1]})")
    else:
        ag_svc = client.get_service("AdGroupService")
        ad_svc = client.get_service("AdGroupAdService")
        ag_ops, ad_ops = [], []
        for child in paused_kids:
            child_id, name, status, kind = child[0], child[1], child[2], child[3]
            if kind == "ad_group":
                op = client.get_type("AdGroupOperation")
                op.update.resource_name = f"customers/{customer_id}/adGroups/{child_id}"
                op.update.status = client.enums.AdGroupStatusEnum.ENABLED
                client.copy_from(op.update_mask, client.get_type("FieldMask")(paths=["status"]))
                ag_ops.append((op, child_id, name))
            elif kind == "ad_group_ad":
                op = client.get_type("AdGroupAdOperation")
                op.update.resource_name = child[4] if len(child) > 4 else f"customers/{customer_id}/adGroupAds/{child_id}"
                op.update.status = client.enums.AdGroupAdStatusEnum.ENABLED
                client.copy_from(op.update_mask, client.get_type("FieldMask")(paths=["status"]))
                ad_ops.append((op, child_id, name))
        if ag_ops:
            ag_svc.mutate_ad_groups(customer_id=customer_id, operations=[o[0] for o in ag_ops])
            for _, cid, n in ag_ops:
                print(f"✅ Ad Group ENABLED: {cid} ({n})")
        if ad_ops:
            ad_svc.mutate_ad_group_ads(customer_id=customer_id, operations=[o[0] for o in ad_ops])
            for _, cid, n in ad_ops:
                print(f"✅ Ad ENABLED: {cid} ({n})")

    print("\n🚀 Done.")


# ─── CLI ──────────────────────────────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                description=__doc__)
    p.add_argument("--platform", required=True, choices=["meta", "google"])
    p.add_argument("--campaign-id", help="Activate campaign + cascade to children")
    p.add_argument("--ad-id", help="(Meta only) Activate just one ad")
    p.add_argument("--customer", help="(Google only) Customer ID without dashes")
    p.add_argument("--yes", action="store_true", help="Skip confirmation prompt")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    if args.platform == "meta":
        if not META_TOKEN and not args.dry_run:
            sys.exit("❌ META_ACCESS_TOKEN missing in .env")
        if args.ad_id:
            activate_meta_ad(args.ad_id, args.dry_run, args.yes)
        elif args.campaign_id:
            activate_meta_campaign(args.campaign_id, args.dry_run, args.yes)
        else:
            sys.exit("❌ Pass --campaign-id or --ad-id for meta")
    elif args.platform == "google":
        if not args.customer:
            sys.exit("❌ Google requires --customer")
        if not args.campaign_id:
            sys.exit("❌ Google requires --campaign-id")
        activate_google_campaign(args.customer, args.campaign_id, args.dry_run, args.yes)


if __name__ == "__main__":
    main()

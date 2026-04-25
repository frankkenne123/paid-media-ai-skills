#!/usr/bin/env python3
"""
Auto-discover everything Meta knows about a client and what their website says,
then write it to client-briefs/<slug>.md as a starting brief.

Usage:
  # Single account
  python3 discover_client_brief.py --account act_XXXXXXXX --slug acme-co

  # Batch via config file (see accounts.example.json)
  python3 discover_client_brief.py --all --accounts-file accounts.json

The config file is a simple JSON map of ad account ID → filename slug:
  { "act_XXXXXXXX": "acme-co", "act_YYYYYYYY": "another-brand" }

Briefs land in ./client-briefs/<slug>.md. Keep that folder out of any public
repo — it contains pixel IDs, page IDs, and other identifiers you may not
want shared.
"""

import argparse, json, os, re, sys
from html import unescape
from pathlib import Path
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv

load_dotenv()

API = "https://graph.facebook.com/v20.0"
TOKEN = os.getenv("META_ACCESS_TOKEN")
BRIEFS = Path(__file__).resolve().parent / "client-briefs"


def load_accounts(path):
    """Load the {account_id: slug} map from a JSON config file."""
    p = Path(path)
    if not p.exists():
        sys.exit(f"❌ accounts file not found: {path}")
    try:
        data = json.loads(p.read_text())
    except Exception as e:
        sys.exit(f"❌ couldn't parse {path}: {e}")
    if not isinstance(data, dict) or not data:
        sys.exit(f"❌ {path} must be a non-empty JSON object: {{\"act_X\": \"slug\"}}")
    return data


def gget(path, **params):
    params["access_token"] = TOKEN
    try:
        r = requests.get(f"{API}{path}", params=params, timeout=30)
        return r.json()
    except Exception as e:
        return {"error": {"message": str(e)}}


def account(act_id):
    return gget(f"/{act_id}", fields="name,currency,timezone_name,business,account_status")


def pages(act_id):
    out = gget(f"/{act_id}/promote_pages", fields="id,name,website,link,about,category", limit=25)
    return out.get("data", [])


def first_page_website(page_list):
    """Find a Page-level website URL when ads aren't running yet."""
    for pg in page_list:
        for k in ("website", "link"):
            v = pg.get(k)
            if v and v.startswith("http") and "facebook.com" not in v:
                return v
    return None


def pixels(act_id):
    out = gget(f"/{act_id}/adspixels", fields="id,name,last_fired_time", limit=10)
    return out.get("data", [])


def instagram(act_id, page_ids):
    """IG isn't exposed at the account level — try via the connected page."""
    igs = []
    for pid in page_ids:
        r = gget(f"/{pid}", fields="instagram_business_account{id,username,followers_count}")
        ig = r.get("instagram_business_account")
        if ig:
            igs.append({"page_id": pid, **ig})
    return igs


def active_ads(act_id, limit=8):
    out = gget(
        f"/{act_id}/ads",
        fields="name,creative{object_story_spec{link_data{link,message,name,description,call_to_action}}}",
        effective_status='["ACTIVE"]',
        limit=limit,
    )
    return out.get("data", [])


# ── Website extraction ─────────────────────────────────────────────────────
META_TAGS = re.compile(r'<meta[^>]+>', re.I)
TAG_RE   = re.compile(r'<[^>]+>')
H1_RE    = re.compile(r'<h1[^>]*>(.*?)</h1>', re.I | re.S)
TITLE_RE = re.compile(r'<title[^>]*>(.*?)</title>', re.I | re.S)


def attr(tag, name):
    m = re.search(rf'{name}\s*=\s*"([^"]*)"', tag, re.I)
    return m.group(1) if m else None


def fetch_brand_signals(url):
    """Pull title, meta description, og description, h1s from the homepage."""
    if not url:
        return {}
    try:
        r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0 LionMediaBot"})
        if r.status_code != 200:
            return {"error": f"HTTP {r.status_code}"}
        html = r.text
    except Exception as e:
        return {"error": str(e)}

    out = {"url": url}
    if m := TITLE_RE.search(html):
        out["title"] = unescape(TAG_RE.sub("", m.group(1))).strip()[:200]
    for tag in META_TAGS.findall(html):
        name = (attr(tag, "name") or attr(tag, "property") or "").lower()
        content = attr(tag, "content")
        if not content:
            continue
        if name == "description":
            out.setdefault("meta_description", unescape(content).strip()[:300])
        if name == "og:description":
            out.setdefault("og_description", unescape(content).strip()[:300])
        if name == "og:site_name":
            out.setdefault("site_name", unescape(content).strip()[:80])
    h1s = [unescape(TAG_RE.sub("", h)).strip() for h in H1_RE.findall(html)]
    h1s = [h for h in h1s if 5 <= len(h) <= 200][:5]
    if h1s:
        out["h1"] = h1s
    return out


# ── Brief composition ─────────────────────────────────────────────────────
def compose(act_id, slug):
    a = account(act_id)
    if "error" in a:
        return f"# {slug}\n\n❌ Account error: {a['error'].get('message')}\n"

    p = pages(act_id)
    px = pixels(act_id)
    ig = instagram(act_id, [pg["id"] for pg in p])
    ads = active_ads(act_id)

    # Find a representative landing URL
    landing_urls = []
    sample_copy = []
    for ad in ads:
        ld = ((ad.get("creative") or {}).get("object_story_spec") or {}).get("link_data") or {}
        if (l := ld.get("link")):
            landing_urls.append(l)
        if (m := ld.get("message")):
            sample_copy.append({"ad": ad.get("name"), "message": m, "headline": ld.get("name")})
    primary_url = landing_urls[0] if landing_urls else None
    domain = urlparse(primary_url).netloc if primary_url else None
    homepage = f"https://{domain}" if domain else None
    if not homepage:
        homepage = first_page_website(p)  # fall back to Facebook Page's own website link
    site = fetch_brand_signals(homepage) if homepage else {}

    status_label = {1: "ACTIVE", 2: "DISABLED", 3: "UNSETTLED", 7: "PENDING_RISK_REVIEW",
                    101: "CLOSED", 102: "ANY_CLOSED", 201: "ANY_ACTIVE"}.get(a.get("account_status"), str(a.get("account_status")))

    lines = [
        f"# {a.get('name', slug)} — Brand Brief",
        "",
        f"_Auto-discovered on {__import__('datetime').date.today().isoformat()}._",
        f"_Read this every time you build a campaign for this client._",
        "",
        "## Identity",
        "",
        f"- **Ad Account:** `{act_id}` — {a.get('name')} ({status_label})",
        f"- **Currency:** {a.get('currency')} · **Timezone:** {a.get('timezone_name')}",
    ]
    if biz := a.get("business"):
        lines.append(f"- **Business Manager:** {biz.get('name')} (`{biz.get('id')}`)")

    lines += ["", "### Connected Facebook Pages"]
    if p:
        for pg in p:
            lines.append(f"- `{pg['id']}` — {pg['name']}")
    else:
        lines.append("- ⚠️ None — this account cannot run ads until a Page is connected.")

    lines += ["", "### Connected Pixels"]
    if px:
        for pix in px:
            lf = pix.get("last_fired_time", "never")
            lines.append(f"- `{pix['id']}` — {pix['name']} · last fired: {lf}")
    else:
        lines.append("- ⚠️ None — conversion optimization will not work.")

    lines += ["", "### Instagram"]
    if ig:
        for i in ig:
            lines.append(f"- `{i['id']}` — @{i.get('username','?')} ({i.get('followers_count','?')} followers, page `{i['page_id']}`)")
    else:
        lines.append("- (none linked at the page level)")

    lines += ["", "## Website signals", ""]
    if homepage:
        lines.append(f"- **Homepage:** {homepage}")
        if site.get("title"):
            lines.append(f"- **Title tag:** {site['title']}")
        if site.get("site_name"):
            lines.append(f"- **og:site_name:** {site['site_name']}")
        if site.get("meta_description"):
            lines.append(f"- **Meta description:** {site['meta_description']}")
        elif site.get("og_description"):
            lines.append(f"- **og:description:** {site['og_description']}")
        if site.get("h1"):
            lines.append("- **H1 tags from homepage:**")
            for h in site["h1"]:
                lines.append(f"  - {h}")
        if site.get("error"):
            lines.append(f"- ⚠️ Couldn't fetch homepage: {site['error']}")
    else:
        lines.append("- (no landing URL found in active ads — ask the user for the website)")

    lines += ["", "## Currently-running ad copy (their actual voice in market)", ""]
    if sample_copy:
        for s in sample_copy[:5]:
            head = (s.get("headline") or "").strip()
            msg = (s.get("message") or "").strip()
            lines.append(f"**{s['ad']}**")
            if head:
                lines.append(f"- Headline: _{head}_")
            if msg:
                # truncate to keep brief readable
                msg_preview = msg if len(msg) <= 400 else msg[:400] + "…"
                lines.append("- Body:")
                for ln in msg_preview.split("\n"):
                    if ln.strip():
                        lines.append(f"  > {ln}")
            lines.append("")
    else:
        lines.append("- (no active ads found — account is paused or new)")

    lines += [
        "## Defaults (assumed unless the user overrides)",
        "",
        "- **Targeting:** Advantage+ broad (project default). Override with `--manual-targeting` only when explicitly told to.",
        "- **Bid strategy:** `LOWEST_COST_WITHOUT_CAP`",
        "- **Optimization goal:** `OFFSITE_CONVERSIONS` → PURCHASE event",
        "- **Status on creation:** PAUSED — never auto-activate.",
        "",
        "## TODO — fill in",
        "",
        "- **Standing offer:** _(e.g. free shipping over $50, 20% off first order)_",
        "- **Standing landing pages:** _(if different from active ads above)_",
        "- **Target ROAS:** _(e.g. 3.0x)_",
        "- **Acceptable CPC / CPM:** _(e.g. $1.50 / $25)_",
        "- **Brand voice notes:** _(banned words, hooks that work, hooks to avoid — feel free to refine the auto-discovered voice above)_",
        "- **Visual style notes:** _(aesthetic, color palette, lifestyle vs flat-lay vs UGC preference)_",
        "- **Audience exceptions:** _(only override Advantage+ if there's a real reason — list it here if so)_",
        "",
        "## Privacy",
        "",
        "Don't paste account IDs, Pixel IDs, or token strings into Obsidian / external surfaces. Reference clients by name only.",
        "",
    ]
    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--account", help="Single ad account, e.g. act_XXXXXXXX")
    p.add_argument("--slug", help="Filename slug for output (e.g. acme-co)")
    p.add_argument("--all", action="store_true",
                   help="Discover every account in --accounts-file")
    p.add_argument("--accounts-file", default="accounts.json",
                   help="Path to JSON map of {act_X: slug}. See accounts.example.json. Default: accounts.json")
    args = p.parse_args()

    if not TOKEN:
        print("❌ META_ACCESS_TOKEN missing in .env")
        sys.exit(1)

    BRIEFS.mkdir(parents=True, exist_ok=True)

    targets = []
    if args.all:
        accounts = load_accounts(args.accounts_file)
        targets = list(accounts.items())
    elif args.account:
        slug = args.slug or args.account.replace("act_", "act-")
        targets = [(args.account, slug)]
    else:
        p.error("Pass --account ... or --all (with --accounts-file)")

    for act_id, slug in targets:
        print(f"→ {act_id} ({slug})")
        out = compose(act_id, slug)
        path = BRIEFS / f"{slug}.md"
        path.write_text(out)
        print(f"   ✓ {path}")


if __name__ == "__main__":
    main()

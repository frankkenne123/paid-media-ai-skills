#!/usr/bin/env python3
"""
Upload a local video to YouTube and return the video ID — for use with
build_google_pmax_campaign.py --videos.

Subcommands:
  setup   — One-time OAuth flow to authorize the app for your YouTube channel.
            Walks you through Google's consent screen, saves the refresh token
            to .env as YOUTUBE_REFRESH_TOKEN.

  upload  — Upload a local .mp4 (or .mov, .webm) to YouTube. Defaults to
            "unlisted" privacy — the video isn't public-searchable but is
            usable as an asset in Google Ads PMax campaigns.

Usage:
  # First time only:
  python3 youtube_upload.py setup

  # Upload (returns video ID + URL):
  python3 youtube_upload.py upload --file /tmp/acme_video.mp4 \
    --title "Acme — Spring 2026 Hero" \
    --description "PMax asset" \
    --tags "ad,spring,2026"

  # Pass directly to PMax build:
  VID=$(python3 youtube_upload.py upload --file /tmp/v.mp4 --title "..." --quiet)
  python3 build_google_pmax_campaign.py ... --videos $VID

Privacy options:
  --privacy unlisted (default) — link-only, fine for ads
  --privacy private  — only you can see; works for ads but harder to preview
  --privacy public   — fully public on the channel
"""

import argparse, json, os, sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# YouTube + Ads can share the same Google Cloud OAuth client.
# We reuse GOOGLE_ADS_CLIENT_ID / GOOGLE_ADS_CLIENT_SECRET if YOUTUBE_CLIENT_ID isn't set,
# but YouTube needs its own refresh token (different scope).
CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID") or os.getenv("GOOGLE_ADS_CLIENT_ID")
CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET") or os.getenv("GOOGLE_ADS_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("YOUTUBE_REFRESH_TOKEN")
SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/youtube.readonly"]
OAUTH_PORT = 8090   # different from Ads helper to avoid clobbering


def cmd_setup(args):
    """Walk through OAuth and write YOUTUBE_REFRESH_TOKEN to .env."""
    import http.server, urllib.parse, urllib.request, webbrowser, threading

    if not CLIENT_ID or not CLIENT_SECRET:
        sys.exit("❌ Need YOUTUBE_CLIENT_ID/YOUTUBE_CLIENT_SECRET (or fall back to "
                 "GOOGLE_ADS_CLIENT_ID/SECRET) in .env. Create them at "
                 "https://console.cloud.google.com/apis/credentials (OAuth client, "
                 "Web app, redirect=http://localhost:8090).")

    auth_code = {"value": None}
    done = threading.Event()

    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a): pass
        def do_GET(self):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if "code" in q:
                auth_code["value"] = q["code"][0]
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(b"<h1>YouTube authorized.</h1><p>You can close this tab.</p>")
            elif "error" in q:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(f"Error: {q.get('error',['?'])[0]}".encode())
            done.set()

    redirect_uri = f"http://localhost:{OAUTH_PORT}"
    auth_url = ("https://accounts.google.com/o/oauth2/auth?"
                + urllib.parse.urlencode({
                    "client_id": CLIENT_ID,
                    "redirect_uri": redirect_uri,
                    "scope": " ".join(SCOPES),
                    "response_type": "code",
                    "access_type": "offline",
                    "prompt": "consent",
                }))

    print("🔐 Opening browser for YouTube authorization…")
    print(f"   If it doesn't open, paste this URL: {auth_url}\n")
    server = http.server.HTTPServer(("localhost", OAUTH_PORT), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    webbrowser.open(auth_url)
    if not done.wait(timeout=300):
        sys.exit("❌ Timed out waiting for authorization.")
    server.shutdown()

    if not auth_code["value"]:
        sys.exit("❌ No authorization code received.")

    print("🔄 Exchanging code for refresh token…")
    token_resp = urllib.request.urlopen(
        "https://oauth2.googleapis.com/token",
        data=urllib.parse.urlencode({
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "code": auth_code["value"],
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }).encode(),
    )
    tokens = json.loads(token_resp.read())
    refresh = tokens.get("refresh_token")
    if not refresh:
        sys.exit(f"❌ No refresh_token in response: {tokens}")

    print(f"✅ Got refresh token (length: {len(refresh)})")

    # Append to .env if not already present
    env_path = Path(__file__).resolve().parent / ".env"
    existing = env_path.read_text() if env_path.exists() else ""
    if "YOUTUBE_REFRESH_TOKEN=" in existing:
        print("⚠️  YOUTUBE_REFRESH_TOKEN already exists in .env — manually replace it:")
        print(f"   YOUTUBE_REFRESH_TOKEN={refresh}")
    else:
        with env_path.open("a") as f:
            if existing and not existing.endswith("\n"):
                f.write("\n")
            f.write(f"YOUTUBE_REFRESH_TOKEN={refresh}\n")
        print(f"✅ Saved to {env_path}")
    print("\nDone. You can now run:")
    print("  python3 youtube_upload.py upload --file /path/to/video.mp4 --title \"...\"")


def cmd_upload(args):
    """Upload a video to YouTube and return its ID."""
    if not REFRESH_TOKEN:
        sys.exit("❌ YOUTUBE_REFRESH_TOKEN missing in .env. Run: "
                 "python3 youtube_upload.py setup")
    if not CLIENT_ID or not CLIENT_SECRET:
        sys.exit("❌ Missing YOUTUBE_CLIENT_ID/SECRET (or GOOGLE_ADS_CLIENT_ID/SECRET fallback)")

    if not Path(args.file).exists():
        sys.exit(f"❌ File not found: {args.file}")

    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from googleapiclient.errors import HttpError

    creds = Credentials(
        token=None,
        refresh_token=REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        scopes=SCOPES,
    )
    yt = build("youtube", "v3", credentials=creds, cache_discovery=False)

    body = {
        "snippet": {
            "title": args.title,
            "description": args.description or "",
            "tags": [t.strip() for t in args.tags.split(",")] if args.tags else [],
            "categoryId": args.category_id,
        },
        "status": {
            "privacyStatus": args.privacy,
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(args.file, chunksize=-1, resumable=True, mimetype="video/*")

    if not args.quiet:
        print(f"⏫ Uploading {args.file} → YouTube (privacy={args.privacy})…")

    try:
        req = yt.videos().insert(part="snippet,status", body=body, media_body=media)
        response = None
        while response is None:
            status, response = req.next_chunk()
            if status and not args.quiet:
                print(f"   {int(status.progress() * 100)}% uploaded…")
        video_id = response["id"]
    except HttpError as e:
        sys.exit(f"❌ YouTube upload failed: {e}")

    url = f"https://youtu.be/{video_id}"
    if args.quiet:
        print(video_id)
    else:
        print(f"\n✅ Uploaded.")
        print(f"   Video ID: {video_id}")
        print(f"   URL:      {url}")
        print(f"\nUse with PMax: --videos {video_id}")


def main():
    p = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)

    s_setup = sub.add_parser("setup", help="One-time OAuth authorization")
    s_setup.set_defaults(func=cmd_setup)

    s_up = sub.add_parser("upload", help="Upload a local video file")
    s_up.add_argument("--file", required=True, help="Path to local .mp4/.mov/.webm")
    s_up.add_argument("--title", required=True, help="Video title (≤100 chars)")
    s_up.add_argument("--description", default="", help="Video description")
    s_up.add_argument("--tags", default="", help="Comma-separated tags")
    s_up.add_argument("--privacy", default="unlisted",
                      choices=["public", "unlisted", "private"],
                      help="Default: unlisted (link-only, fine for PMax)")
    s_up.add_argument("--category-id", default="22",
                      help="YouTube category ID (default 22 = People & Blogs; 24 = Entertainment)")
    s_up.add_argument("--quiet", action="store_true",
                      help="Print only the video ID — for shell substitution")
    s_up.set_defaults(func=cmd_upload)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

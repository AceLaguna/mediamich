#!/usr/bin/env python3
"""Monthly link checker for the Michigan Media Hub.
Reads outlets.json, tests every website URL, and writes broken_links.md.
Exits 0 always; the workflow decides whether to open an issue."""
import json, sys, concurrent.futures, urllib.request, urllib.error, ssl

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE  # many small-town news sites have imperfect certs
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; MichiganMediaHub-LinkChecker/1.0)"}

def check(outlet):
    url = outlet.get("website", "")
    if not url.startswith("http"):
        return outlet, "no URL"
    req = urllib.request.Request(url, headers=HEADERS, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=25, context=CTX) as resp:
            code = resp.getcode()
            return outlet, None if code < 400 else f"HTTP {code}"
    except urllib.error.HTTPError as e:
        # 403/429 usually means a bot-blocker, not a dead site — don't flag
        if e.code in (403, 429, 406):
            return outlet, None
        return outlet, f"HTTP {e.code}"
    except Exception as e:
        return outlet, type(e).__name__

def main():
    with open("outlets.json") as f:
        data = json.load(f)
    outlets = [o for o in data["outlets"] if o.get("status", "active") == "active"]
    broken = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex:
        for outlet, err in ex.map(check, outlets):
            if err:
                broken.append((outlet, err))
                print(f"  BROKEN  {outlet['name']}: {err}")
    with open("broken_links.md", "w") as f:
        if not broken:
            f.write("All links OK.\n")
        else:
            f.write(f"# Broken links — {len(broken)} of {len(outlets)} checked\n\n")
            f.write("| Outlet | Category | URL | Error |\n|---|---|---|---|\n")
            for o, err in broken:
                f.write(f"| {o['name']} | {o['category']} | {o['website']} | {err} |\n")
    print(f"\nChecked {len(outlets)} URLs — {len(broken)} problems. Report: broken_links.md")

if __name__ == "__main__":
    main()

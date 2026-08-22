#!/usr/bin/env python3
"""
SpiderFoot OSINT Search – companion to Sherlock
Runs a SpiderFoot scan on a username or email address.

Requirements:
    pip install spiderfoot        # installs sf.py CLI
  OR
    git clone https://github.com/smicallef/spiderfoot
    cd spiderfoot && pip install -r requirements.txt

Usage:
    python spiderfoot_search.py <username>
    python spiderfoot_search.py <username> --email user@example.com
    python spiderfoot_search.py <username> --web          # open SpiderFoot web UI
"""

import argparse
import json
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

SPIDERFOOT_URL = "http://localhost:5001"

# Modules focused on username / identity OSINT
USERNAME_MODULES = [
    "sfp_github",
    "sfp_instagram",
    "sfp_twitter",
    "sfp_reddit",
    "sfp_tiktok",
    "sfp_linkedin",
    "sfp_keybase",
    "sfp_pastebin",
    "sfp_haveibeenpwned",
    "sfp_dehashed",
    "sfp_whoisxmlapi",
    "sfp_gravatar",
    "sfp_socialprofiles",
    "sfp_accounts",
]


def _api(path, data=None):
    url = SPIDERFOOT_URL + path
    body = urllib.parse.urlencode(data).encode() if data else None
    req = urllib.request.Request(url, data=body)
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())


def _sf_running():
    try:
        urllib.request.urlopen(SPIDERFOOT_URL + "/", timeout=3)
        return True
    except Exception:
        return False


def _start_sf_server():
    sf = shutil.which("sf.py") or shutil.which("sf")
    if sf is None:
        # Try common clone location
        import os
        candidate = os.path.expanduser("~/spiderfoot/sf.py")
        if os.path.exists(candidate):
            sf = candidate
    if sf is None:
        print("SpiderFoot not found. Install it with:")
        print("    pip install spiderfoot")
        print("or:")
        print("    git clone https://github.com/smicallef/spiderfoot")
        print("    cd spiderfoot && pip install -r requirements.txt")
        sys.exit(1)
    print(f"Starting SpiderFoot server ({sf}) …")
    subprocess.Popen(
        [sys.executable, sf, "-l", "127.0.0.1:5001"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(20):
        time.sleep(1)
        if _sf_running():
            return
    print("SpiderFoot server did not start in time.")
    sys.exit(1)


def run_scan(target, target_type, modules):
    scan_id = _api("/startscan", {
        "scanname": f"sherlock_{target}",
        "scantarget": target,
        "targettype": target_type,
        "modulelist": ",".join(modules),
        "typelist": "",
    })["id"]
    print(f"Scan started (id={scan_id}). Waiting for results …")

    while True:
        time.sleep(5)
        status = _api(f"/scanstatus/{scan_id}")
        state = status.get("status", "")
        print(f"  [{state}]", end="\r", flush=True)
        if state in ("FINISHED", "ABORTED", "ERROR-FAILED"):
            break

    print()
    results = _api(f"/scaneventresults/{scan_id}")
    return scan_id, results


def print_results(results):
    if not results:
        print("No results found.")
        return

    by_type = {}
    for row in results:
        t = row.get("type", "Unknown")
        by_type.setdefault(t, []).append(row.get("data", ""))

    found = 0
    for t, items in sorted(by_type.items()):
        unique = sorted(set(items))
        print(f"\n=== {t} ({len(unique)}) ===")
        for item in unique:
            print(f"  {item}")
            found += 1

    print(f"\nTotal data points: {found}")


def main():
    parser = argparse.ArgumentParser(description="SpiderFoot OSINT search")
    parser.add_argument("username", help="Username to search for")
    parser.add_argument("--email", help="Also scan this email address")
    parser.add_argument(
        "--web",
        action="store_true",
        help="Open SpiderFoot web UI in browser after scan",
    )
    parser.add_argument(
        "--modules",
        help="Comma-separated SpiderFoot modules (default: username set)",
    )
    args = parser.parse_args()

    modules = args.modules.split(",") if args.modules else USERNAME_MODULES

    if not _sf_running():
        _start_sf_server()

    targets = [(args.username, "USERNAME")]
    if args.email:
        targets.append((args.email, "EMAILADDR"))

    for target, target_type in targets:
        print(f"\n{'='*60}")
        print(f"Scanning {target_type}: {target}")
        print("=" * 60)
        scan_id, results = run_scan(target, target_type, modules)
        print_results(results)

        if args.web:
            import webbrowser
            webbrowser.open(f"{SPIDERFOOT_URL}/scaninfo?id={scan_id}")


if __name__ == "__main__":
    main()

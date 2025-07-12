#!/usr/bin/python3
"""

Author: JDunphy - 7/11/2025

Purpose: Given a block list with cloudflare, this will add/del/list ip's in that list.
         modifyBanList.py – Add, delete, or list IP entries in a Cloudflare custom list.

Operation: Create a block list (on CF -> Manage Account/Configurations/Lists)
           Setup a rule (On CF -> Pick Domain then Security/WAF/Custom rules) then
                      
Hint:
    To find your list id, edit the list and look at the URL. It will look like this:
    https://dash.cloudflare.com/<user id>/configurations/lists/<list id>

Populate the USER-SPECIFIC SETTINGS below.

USAGE EXAMPLES:
  # Add an IP with the default comment
  ./modifyBanList.py 203.0.113.4 add

  # Add an IP to a specific list
  ./modifyBanList.py 203.0.113.4 add --list-name bots

  # Delete an IP from the challenge list
  ./modifyBanList.py 203.0.113.4 del --list-name challenge

  # List current items in the 'block' list
  ./modifyBanList.py --list --list-name block
"""

import sys
import json
import ipaddress
import argparse
import requests
from typing import Dict, Any, Optional, List


# ──────────────────────────  USER-SPECIFIC SETTINGS  ────────────────────────── #
ACCOUNT_ID = 'somehexnumber'   # Your Cloudflare account ID
EMAIL = 'user@example.com'     # Your Cloudflare account email
API_KEY = 'somehexnumber'      # Your Cloudflare Global API Key (or API token if supported)

# example list types - if you have some that block and some that throw up challenges
LIST_IDS = {
    "default": "somehexnumber",    # default list
    "block": "",                   # hard block list
    "captcha": "",                 # CAPTCHA challenge list
    "challenge": "somehexnumber",  # JS challenge list
    "bots": "",       # soft bot list
}
# ────────────────────────────────────────────────────────────────────────────── #

VERSION = "1.2.1"


def get_api_endpoint(list_id: str) -> str:
    return f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/rules/lists/{list_id}/items"


def build_headers() -> Dict[str, str]:
    return {
        "X-Auth-Email": EMAIL,
        "X-Auth-Key": API_KEY,
        "Content-Type": "application/json",
    }


def print_usage():
    print("""\
USAGE EXAMPLES:

  # Show help
  ./modifyBanList.py --help

  # Add an IP to the default list
  ./modifyBanList.py 198.51.100.77 add

  # Add an IP to the 'captcha' list
  ./modifyBanList.py 198.51.100.77 add --list-name captcha

  # Add with custom comment
  ./modifyBanList.py 198.51.100.77 add --list-name block --comment "spam scan"

  # Delete an IP
  ./modifyBanList.py 198.51.100.77 del --list-name captcha

  # View everything in the 'bots' list
  ./modifyBanList.py --list --list-name bots
""")


def api_get(list_id: str) -> Dict[str, Any]:
    r = requests.get(get_api_endpoint(list_id), headers=build_headers())
    if r.ok:
        return r.json()
    sys.exit(f"[ERROR] Unable to fetch list: {r.status_code}\n{r.text}")


def api_post(list_id: str, payload: Any) -> requests.Response:
    return requests.post(get_api_endpoint(list_id), headers=build_headers(), data=json.dumps(payload))


def api_delete(list_id: str, payload: Any) -> requests.Response:
    return requests.delete(get_api_endpoint(list_id), headers=build_headers(), data=json.dumps(payload))


def ipv6_to_slash64(addr: str) -> str:
    ip6 = ipaddress.IPv6Address(addr)
    net = ipaddress.IPv6Network(f"{ip6}/64", strict=False)
    return str(net.compressed)

def pretty_print_list(result: List[Dict[str, Any]]) -> None:
    if not result:
        print("(list is empty)")
        return
    print(f"{'IP OR RANGE':39}  {'ID':32}  COMMENT")
    print("-" * 90)
    for item in result:
        comment = item.get("comment", "")
        print(f"{item['ip']:<39}  {item['id']:<32}  {comment}")


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Cloudflare custom IP list manager")
    parser.add_argument("ip", nargs="?", help="IP address (IPv4 or IPv6)")
    parser.add_argument("action", nargs="?", choices=("add", "del"), help="Action to perform")
    parser.add_argument("--comment", "-c", default="added by fail2ban", help="Comment for 'add' action")
    parser.add_argument("--list", action="store_true", help="Show the current list contents and exit")
    parser.add_argument("--list-name", "-n", default="default", help="Name of the list to act on")
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    parser.add_argument("--usage", action="store_true", help="Show usage examples and exit")
    args = parser.parse_args(argv)

    if args.usage:
        print_usage()
        sys.exit(0)

    if args.list_name not in LIST_IDS:
        print(f"[ERROR] Unknown list-name '{args.list_name}'. Must be one of: {', '.join(LIST_IDS.keys())}")
        sys.exit(1)

    list_id = LIST_IDS[args.list_name]

    # ── LIST MODE ────────────────────────────
    if args.list:
        pretty_print_list(api_get(list_id)["result"])
        return

    # ── ADD / DELETE MODE ────────────────────
    if not args.ip or not args.action:
        parser.error("ip and action are required unless --list is used")

    try:
        ip_to_use = ipv6_to_slash64(args.ip)
    except ipaddress.AddressValueError:
        ip_to_use = args.ip  # IPv4 or already valid range

    existing = api_get(list_id)["result"]

    if args.action == "del":

        #cloudflare adds /64 on insertion so we need to match that for del
        try:
            ip_obj = ipaddress.ip_address(args.ip)
            if ip_obj.version == 6:
                ip_to_use = ipv6_to_slash64(args.ip)
            else:
                ip_to_use = args.ip
        except ValueError:
            ip_to_use = args.ip  # fallback for malformed or already-CIDR

        item_id = next((i["id"] for i in existing if i["ip"] == ip_to_use), None)
        if not item_id:
            print(f"[INFO] {ip_to_use} not in list – nothing to do.")
            return
        resp = api_delete(list_id, {"items": [{"id": item_id}]})
        if resp.ok:
            print(f"[OK] Removed {ip_to_use}")
        else:
            print(f"[ERROR] Deletion failed: {resp.status_code}\n{resp.text}")
        return

    if any(i["ip"] == ip_to_use for i in existing):
        print(f"[INFO] {ip_to_use} already present – skipping add.")
        return

    payload = [{"ip": ip_to_use, "comment": args.comment}]
    resp = api_post(list_id, payload)
    if resp.ok:
        print(f"[OK] Added {ip_to_use} to list '{args.list_name}' (comment: {args.comment})")
    else:
        print(f"[ERROR] Add failed: {resp.status_code}\n{resp.text}")


if __name__ == "__main__":
    main()


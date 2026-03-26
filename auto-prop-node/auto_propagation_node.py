#!/usr/bin/env python3
#
# auto_propagation_node.py — Automatic LXMF Propagation Node Selector
#
# Queries the local MeshChat API for all known LXMF propagation node
# announces, selects the best one by hop count, updates MeshChat's
# preferred propagation node, and sends an LXMF status message to a
# configured address.
#
# Intended to run hourly via systemd timer (see auto-propnode.timer).
# Sends a status report every run whether or not the node changed.
#
# Configuration: edit the two constants below before deploying.

import json, base64, sys, urllib.request, urllib.error
from datetime import datetime

try:
    import msgpack
except ImportError:
    print("msgpack not found - install it into your venv first"); sys.exit(1)

# -------------------------------------------------------------------
# CONFIGURATION — edit these before deploying
# -------------------------------------------------------------------

# URL of your local MeshChat instance
MESHCHAT_URL = "http://localhost:8000"

# Minimum hops to consider — set to 2 to exclude local nodes at 1 hop
MIN_HOPS = 2

# Your LXMF address hash — status messages will be sent here
# Find it in MeshChat under Settings > Identity, or:
#   curl -s http://localhost:8000/api/v1/config | python3 -c \
#     "import sys,json; print(json.load(sys.stdin)['config']['lxmf_address_hash'])"
MY_LXMF_ADDRESS = "YOUR_LXMF_ADDRESS_HASH_HERE"

# -------------------------------------------------------------------


def get(path):
    return json.loads(urllib.request.urlopen(MESHCHAT_URL + path).read())


def patch(path, data):
    req = urllib.request.Request(
        MESHCHAT_URL + path,
        data=json.dumps(data).encode(),
        headers={"Content-Type": "application/json"},
        method="PATCH"
    )
    return json.loads(urllib.request.urlopen(req).read())


def send_lxmf(message):
    payload = {
        "lxmf_message": {
            "destination_hash": MY_LXMF_ADDRESS,
            "content": message,
        }
    }
    req = urllib.request.Request(
        MESHCHAT_URL + "/api/v1/lxmf-messages/send",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        urllib.request.urlopen(req)
    except Exception as e:
        print("Failed to send LXMF notification: " + str(e))


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("[" + ts + "] " + msg)


ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

announces = get("/api/v1/announces").get("announces", [])
pnodes = [a for a in announces if a.get("aspect") == "lxmf.propagation"]
current = get("/api/v1/config")["config"]["lxmf_preferred_propagation_node_destination_hash"]

candidates = []
for a in pnodes:
    hops = a.get("hops") or 99
    if hops < MIN_HOPS:
        continue
    try:
        decoded = msgpack.unpackb(base64.b64decode(a["app_data"]))
        if decoded[2]:  # node reports itself as enabled
            candidates.append({
                "hash": a["destination_hash"],
                "hops": hops,
                "updated": a.get("updated_at", ""),
            })
    except Exception:
        pass

if not candidates:
    msg = (
        "[PropNode] " + ts + "\n"
        "No enabled propagation nodes found.\n"
        "Current node unchanged: " + str(current) + "\n"
        "Total nodes in DB: " + str(len(pnodes))
    )
    log(msg)
    send_lxmf(msg)
    sys.exit(0)

candidates.sort(key=lambda x: (x["hops"], x["updated"]), reverse=False)
best = candidates[0]

if best["hash"] == current:
    msg = (
        "[PropNode] " + ts + "\n"
        "Current node is still the best, no change made.\n"
        "Node: " + best["hash"] + "\n"
        "Hops: " + str(best["hops"]) + "\n"
        "Enabled candidates available: " + str(len(candidates))
    )
    log(msg)
    send_lxmf(msg)
    sys.exit(0)

patch("/api/v1/config", {"lxmf_preferred_propagation_node_destination_hash": best["hash"]})
msg = (
    "[PropNode] " + ts + "\n"
    "Propagation node switched.\n"
    "New: " + best["hash"] + "\n"
    "Hops: " + str(best["hops"]) + "\n"
    "Was: " + str(current) + "\n"
    "Enabled candidates available: " + str(len(candidates))
)
log(msg)
send_lxmf(msg)

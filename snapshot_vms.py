#!/usr/bin/env python3

import openstack
import os
import json
import time
from datetime import datetime
from pathlib import Path

# --- CONFIGURATION ---
AUTH_ARGS = {
    "auth_url": "$KEYSTONEURL",
    "project_name": "$PROJECT_NAME",
    "username": "$USERNAME",
    "password": "$API_KEY",
    "user_domain_name": "$DOMAIN",
    "project_domain_name": "$DOMAIN"
}

SNAPSHOT_PREFIX = "auto-snap"
SNAPSHOT_RETENTION = 5  # number of snapshots to retain per instance
STAGGER_SECONDS = 20  # Time to wait between each VM snapshot (in seconds)

# Use local directory for snapshot state
SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR / ".snapshot_data"
DATA_FILE = DATA_DIR / "instances.json"

# Ensure data directory exists
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Create state dir if it doesn't exist
DATA_FILE.parent.mkdir(parents=True, exist_ok=True)

def connect():
    return openstack.connect(**AUTH_ARGS)

def load_previous_instance_ids():
    if not os.path.exists(DATA_FILE):
        return set()
    try:
        with open(DATA_FILE) as f:
            data = f.read().strip()
            if not data:
                return set()  # empty file
            return set(json.loads(data))
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Could not load instance IDs from {DATA_FILE}: {e}")
        return set()

def save_instance_ids(instance_ids):
    with open(DATA_FILE, 'w') as f:
        json.dump(list(instance_ids), f)  # convert set to list here

def detect_changes(current_ids, previous_ids):
    added = list(set(current_ids) - set(previous_ids))
    removed = list(set(previous_ids) - set(current_ids))
    return added, removed

def create_snapshot(conn, instance):
    timestamp = datetime.utcnow().strftime('%Y%m%d-%H%M%S')
    snap_name = f"{SNAPSHOT_PREFIX}-{instance.name}-{timestamp}"
    print(f"Creating snapshot: {snap_name}")
    conn.compute.create_server_image(instance.id, snap_name)

def cleanup_old_snapshots(conn, instance):
    # Define the name prefix for this instance's snapshots
    instance_prefix = f"{SNAPSHOT_PREFIX}-{instance.name}-"

    # List images and filter by name pattern
    images = list(conn.image.images())
    matching = [
        img for img in images
        if img.name.startswith(instance_prefix)
        and img.owner_id == conn.current_project_id  # only your own snapshots
    ]

    # Sort by creation time, newest first
    matching.sort(key=lambda x: x.created_at, reverse=True)

    for img in matching[SNAPSHOT_RETENTION:]:
        print(f"Deleting old snapshot: {img.name}")
        try:
            conn.image.delete_image(img.id, ignore_missing=True)
        except Exception as e:
            print(f"Failed to delete snapshot {img.name}: {e}")

def main():
    conn = connect()
    previous_instances = load_previous_instance_ids()

    servers = list(conn.compute.servers())

    for i, srv in enumerate(servers):
        print(f"\n[+] Processing {srv.name} ({srv.id})")

        create_snapshot(conn, srv)
        cleanup_old_snapshots(conn, srv)

        # Stagger next snapshot
        if i < len(servers) - 1:  # don't wait after last VM
            print(f"Sleeping {STAGGER_SECONDS}s before next VM...")
            time.sleep(STAGGER_SECONDS)

    instance_ids = {srv.id for srv in servers}
    save_instance_ids(instance_ids)

if __name__ == "__main__":
    main()

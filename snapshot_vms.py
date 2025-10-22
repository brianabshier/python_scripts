#!/usr/bin/env python3
"""
OpenStack VM Snapshot Script using Application Credentials
----------------------------------------------------------
Creates snapshots of all instances in the project,
retains a fixed number per instance, and removes older ones.
Credentials are hardcoded in the script (Application Credential ID + Secret).
VMs can be excluded from snapshotting by creating and using:
  - .snapshot_data/exclude_ids.txt (one VM ID per line)
  - .snapshot_data/exclude_names.txt (one pattern per line, supports '*' wildcards)
"""

import json
import time
from datetime import datetime
from pathlib import Path
import fnmatch

from keystoneauth1 import session
from keystoneauth1.identity import v3
from openstack import connection

# --- CONFIGURATION ---
AUTH_URL = "$https://keystone.api.region3.cloud.com/v3"
APP_CRED_ID = "$APPLICATION_CRED_ID"
APP_CRED_SECRET = "$APPLICATION_CRED_SECRET"

SNAPSHOT_PREFIX = "auto-snap"
SNAPSHOT_RETENTION = 5      # number of snapshots to retain per instance
STAGGER_SECONDS = 20        # delay between snapshots (seconds)

# Local storage for instance tracking
SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR / ".snapshot_data"
DATA_FILE = DATA_DIR / "instances.json"
EXCLUDE_IDS_FILE = DATA_DIR / "exclude_ids.txt"
EXCLUDE_NAMES_FILE = DATA_DIR / "exclude_names.txt"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# --- HELPER FUNCTIONS ---
def connect():
    """Create OpenStack connection using hardcoded Application Credential."""
    auth = v3.ApplicationCredential(
        auth_url=AUTH_URL,
        application_credential_id=APP_CRED_ID,
        application_credential_secret=APP_CRED_SECRET,
    )
    sess = session.Session(auth=auth)
    return connection.Connection(session=sess)


def load_previous_instance_ids():
    if not DATA_FILE.exists():
        return set()
    try:
        with open(DATA_FILE) as f:
            data = f.read().strip()
            return set(json.loads(data)) if data else set()
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Could not load instance IDs from {DATA_FILE}: {e}")
        return set()


def save_instance_ids(instance_ids):
    with open(DATA_FILE, "w") as f:
        json.dump(list(instance_ids), f)


def load_exclude_ids():
    """Return a set of VM IDs to exclude from snapshotting."""
    if not EXCLUDE_IDS_FILE.exists():
        return set()
    with open(EXCLUDE_IDS_FILE) as f:
        return {line.strip() for line in f if line.strip()}


def load_exclude_name_patterns():
    """Return a list of name patterns to exclude (supports '*' wildcards)."""
    if not EXCLUDE_NAMES_FILE.exists():
        return []
    with open(EXCLUDE_NAMES_FILE) as f:
        return [line.strip() for line in f if line.strip()]


def is_excluded(vm_id, vm_name, exclude_ids, exclude_name_patterns):
    """Return True if a VM should be skipped based on ID or name pattern (case-insensitive)."""
    if vm_id in exclude_ids:
        return True
    vm_name_lower = vm_name.lower()
    for pattern in exclude_name_patterns:
        if fnmatch.fnmatch(vm_name_lower, pattern.lower()):
            return True
    return False


def create_snapshot(conn, instance):
    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    snap_name = f"{SNAPSHOT_PREFIX}-{instance.name}-{timestamp}"
    print(f"[{datetime.utcnow().isoformat()}] Creating snapshot: {snap_name}")
    conn.compute.create_server_image(instance.id, snap_name)


def cleanup_old_snapshots(conn, instance):
    instance_prefix = f"{SNAPSHOT_PREFIX}-{instance.name}-"
    images = list(conn.image.images())

    matching = [
        img for img in images
        if img.name.startswith(instance_prefix)
        and img.owner_id == conn.current_project_id
    ]

    matching.sort(key=lambda x: x.created_at, reverse=True)

    for img in matching[SNAPSHOT_RETENTION:]:
        print(f"[{datetime.utcnow().isoformat()}] Deleting old snapshot: {img.name}")
        try:
            conn.image.delete_image(img.id, ignore_missing=True)
        except Exception as e:
            print(f"Failed to delete snapshot {img.name}: {e}")


# --- MAIN LOGIC ---
def main():
    conn = connect()
    previous_instances = load_previous_instance_ids()
    exclude_ids = load_exclude_ids()
    exclude_name_patterns = load_exclude_name_patterns()

    print(f"[{datetime.utcnow().isoformat()}] Fetching list of instances...")
    servers = list(conn.compute.servers())

    for i, srv in enumerate(servers):
        if is_excluded(srv.id, srv.name, exclude_ids, exclude_name_patterns):
            print(f"[{datetime.utcnow().isoformat()}] Skipping excluded VM: {srv.name} ({srv.id})")
            continue

        print(f"\n[{datetime.utcnow().isoformat()}] Processing {srv.name} ({srv.id})")
        create_snapshot(conn, srv)
        cleanup_old_snapshots(conn, srv)

        if i < len(servers) - 1:
            print(f"Sleeping {STAGGER_SECONDS}s before next VM...")
            time.sleep(STAGGER_SECONDS)

    instance_ids = {srv.id for srv in servers}
    save_instance_ids(instance_ids)

    print(f"[{datetime.utcnow().isoformat()}] All snapshots completed successfully.")


if __name__ == "__main__":
    main()

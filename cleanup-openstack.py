#!/usr/bin/env python3
"""
Dependency-aware OpenStack project cleanup.

Deletes, in roughly this order:
- Load balancers
- Servers / instances
- Floating IPs
- Volume snapshots
- Volumes
- Non-default security groups
- Routers
- Non-router ports
- Subnets
- Networks

Preserves:
- SSH keypairs (never touched)
- Security group named "default"
- Network named "PUBLICNET"
- Any subnet attached to PUBLICNET

Notes:
- Dry-run by default
- Use --execute to actually delete resources
- Requires confirmation of the target project unless --yes is supplied
- Uses the OpenStack CLI already configured in your environment
- Does not rely on volume --force
- Detects whether your CLI supports volume delete --cascade or --purge
- Network cleanup is done in the order:
    router interfaces -> router gateway -> router delete -> other ports -> subnets -> networks

Examples:
    python3 cleanup_openstack_project.py
    python3 cleanup_openstack_project.py --execute
    python3 cleanup_openstack_project.py --execute --yes
    python3 cleanup_openstack_project.py --execute --network-passes 3
"""

import argparse
import ast
import json
import os
import re
import shutil
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional, Sequence, Set


class OSCommandError(RuntimeError):
    pass


UUID_PATTERN = re.compile(
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)


def run_cmd(
    cmd: Sequence[str],
    expect_json: bool = False,
    allow_fail: bool = False,
    retries: int = 0,
    retry_delay: int = 3,
) -> Any:
    last_err = None

    for attempt in range(retries + 1):
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        if proc.returncode == 0:
            stdout = proc.stdout.strip()
            if expect_json:
                if not stdout:
                    return []
                try:
                    return json.loads(stdout)
                except json.JSONDecodeError as exc:
                    raise OSCommandError(
                        f"Failed to parse JSON from command: {' '.join(cmd)}\n"
                        f"STDOUT:\n{proc.stdout}\n"
                        f"STDERR:\n{proc.stderr}"
                    ) from exc
            return stdout

        last_err = OSCommandError(
            f"Command failed ({proc.returncode}): {' '.join(cmd)}\n"
            f"STDERR:\n{proc.stderr.strip()}\n"
            f"STDOUT:\n{proc.stdout.strip()}"
        )

        if attempt < retries:
            time.sleep(retry_delay)

    if allow_fail:
        print(f"[WARN] {last_err}", file=sys.stderr)
        return None

    raise last_err


def which_or_die(binary: str) -> None:
    if shutil.which(binary) is None:
        print(f"ERROR: Required binary not found in PATH: {binary}", file=sys.stderr)
        sys.exit(2)


def verify_auth() -> None:
    try:
        run_cmd(["openstack", "token", "issue", "-f", "json"], expect_json=True)
    except Exception as exc:
        print(
            "ERROR: OpenStack CLI authentication failed. "
            "Make sure your credentials are loaded.",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc


def get_token_info() -> Dict[str, Any]:
    result = run_cmd(["openstack", "token", "issue", "-f", "json"], expect_json=True)
    if not isinstance(result, dict):
        raise OSCommandError("Unexpected response from openstack token issue")
    return result


def os_list(resource: List[str], extra_args: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    extra_args = extra_args or []
    cmd = ["openstack", *resource, "list", *extra_args, "-f", "json"]
    return run_cmd(cmd, expect_json=True)


def os_show(resource: List[str], object_id: str, allow_fail: bool = False) -> Optional[Dict[str, Any]]:
    cmd = ["openstack", *resource, "show", object_id, "-f", "json"]
    result = run_cmd(cmd, expect_json=True, allow_fail=allow_fail)
    if result is None:
        return None
    return result


def value_get(obj: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        if key in obj:
            return obj[key]
    return default


def normalize_status(value: Any) -> str:
    return str(value or "").strip().lower()


def os_delete(
    resource: List[str],
    object_id: str,
    extra_args: Optional[List[str]] = None,
    execute: bool = False,
    allow_fail: bool = True,
    label: Optional[str] = None,
) -> bool:
    extra_args = extra_args or []
    cmd = ["openstack", *resource, "delete", *extra_args, object_id]

    if execute:
        print(f"[DELETE] {' '.join(cmd)}" + (f"  # {label}" if label else ""))
        result = run_cmd(cmd, allow_fail=allow_fail, retries=1)
        return result is not None

    print(f"[DRY-RUN] {' '.join(cmd)}" + (f"  # {label}" if label else ""))
    return True


def os_unset(
    resource: List[str],
    object_id: str,
    args: List[str],
    execute: bool = False,
    allow_fail: bool = True,
) -> bool:
    cmd = ["openstack", *resource, "unset", *args, object_id]

    if execute:
        print(f"[UPDATE] {' '.join(cmd)}")
        result = run_cmd(cmd, allow_fail=allow_fail, retries=1)
        return result is not None

    print(f"[DRY-RUN] {' '.join(cmd)}")
    return True


def list_ports_long() -> List[Dict[str, Any]]:
    return os_list(["port"], extra_args=["--long"])


def list_routers_long() -> List[Dict[str, Any]]:
    return os_list(["router"], extra_args=["--long"])


def list_ports_for_router(router_id: str) -> List[Dict[str, Any]]:
    ports = []

    try:
        ports = os_list(["port"], extra_args=["--router", router_id, "--long"])
    except Exception:
        pass

    if ports:
        return ports

    router_ports = []
    for port in list_ports_long():
        device_id = value_get(port, "Device ID", "device_id")
        if device_id == router_id:
            router_ports.append(port)

    return router_ports


def get_current_project_info() -> Dict[str, Any]:
    token_info = get_token_info()
    project_id = str(
        value_get(
            token_info,
            "project_id",
            "project",
            "Project",
            default="",
        )
        or ""
    )

    project_name = str(
        value_get(
            token_info,
            "project_name",
            "project",
            "Project",
            default="",
        )
        or ""
    )
    user_name = str(value_get(token_info, "user_name", "user", "User", default="") or "")
    if not user_name:
        user_name = os.environ.get("OS_USERNAME", "").strip()
    region_name = os.environ.get("OS_REGION_NAME", "").strip()
    project_tags: List[str] = []

    project_details = os_show(["project"], project_id, allow_fail=True) if project_id else None
    if project_details:
        project_name = str(
            value_get(project_details, "name", "Name", default=project_name or project_id) or project_name
        )
        raw_tags = value_get(project_details, "tags", "Tags", default=[])
        if isinstance(raw_tags, list):
            project_tags = [str(tag) for tag in raw_tags if str(tag).strip()]
        elif isinstance(raw_tags, str) and raw_tags.strip():
            project_tags = [tag.strip() for tag in raw_tags.split(",") if tag.strip()]

    return {
        "project_id": project_id or "unknown",
        "project_name": project_name or "unknown",
        "user_name": user_name or "unknown",
        "region_name": region_name or "unknown",
        "project_tags": project_tags,
    }


def confirm_target_project(skip_confirmation: bool) -> None:
    info = get_current_project_info()

    print("\n== Target project confirmation ==")
    print(f"Project Name: {info['project_name']}")
    print(f"Project ID: {info['project_id']}")
    print(f"Authenticated user: {info['user_name']}")
    print(f"Region: {info['region_name']}")
    if info["project_tags"]:
        print(f"Project tags: {', '.join(info['project_tags'])}")
    else:
        print("Project tags: none")

    if skip_confirmation:
        print("Confirmation bypassed with --yes.")
        return

    if not sys.stdin.isatty():
        print(
            "ERROR: Confirmation required, but no interactive terminal is available. "
            "Re-run with --yes if this target project is correct.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    response = input("Type 'yes' to continue with this project: ").strip().lower()
    if response != "yes":
        print("Aborted before making any changes.")
        raise SystemExit(1)


def get_publicnet_id() -> Optional[str]:
    nets = os_list(["network"])
    for net in nets:
        name = value_get(net, "Name", "name")
        net_id = value_get(net, "ID", "id")
        if name == "PUBLICNET":
            return net_id
    return None


def get_publicnet_subnet_ids(publicnet_id: Optional[str]) -> Set[str]:
    keep: Set[str] = set()
    if not publicnet_id:
        return keep

    subnets = os_list(["subnet"])
    for subnet in subnets:
        subnet_id = value_get(subnet, "ID", "id")
        network_id = value_get(subnet, "Network", "network_id")
        if network_id == publicnet_id:
            keep.add(subnet_id)

    return keep


def get_volume_delete_mode() -> str:
    help_text = run_cmd(["openstack", "volume", "delete", "-h"], allow_fail=True)
    help_text = help_text or ""

    if "--cascade" in help_text:
        return "cascade"
    if "--purge" in help_text:
        return "purge"
    return "plain"


def extract_subnet_ids(fixed_ips_field: Any) -> List[str]:
    subnet_ids: List[str] = []

    if isinstance(fixed_ips_field, list):
        for item in fixed_ips_field:
            if isinstance(item, dict) and item.get("subnet_id"):
                subnet_ids.append(item["subnet_id"])
        return list(dict.fromkeys(subnet_ids))

    if isinstance(fixed_ips_field, dict):
        subnet_id = fixed_ips_field.get("subnet_id")
        return [subnet_id] if subnet_id else []

    text = str(fixed_ips_field).strip()
    if not text:
        return []

    if text.startswith(("[", "{")):
        try:
            parsed = ast.literal_eval(text)
        except (ValueError, SyntaxError):
            parsed = None
        if isinstance(parsed, list):
            for item in parsed:
                if isinstance(item, dict) and item.get("subnet_id"):
                    subnet_ids.append(item["subnet_id"])
        elif isinstance(parsed, dict) and parsed.get("subnet_id"):
            subnet_ids.append(parsed["subnet_id"])

    if subnet_ids:
        return list(dict.fromkeys(subnet_ids))

    subnet_ids.extend(
        match.group(1)
        for match in re.finditer(r"subnet_id\s*[:=]\s*['\"]?([0-9a-f-]+)", text, flags=re.IGNORECASE)
    )

    return list(dict.fromkeys(subnet_ids))


def wait_for_no_servers(timeout: int = 900, interval: int = 10) -> None:
    print("Waiting for servers to disappear...")
    deadline = time.time() + timeout

    while time.time() < deadline:
        servers = os_list(["server"])
        if not servers:
            print("All servers removed.")
            return
        print(f"Still present: {len(servers)} server(s)")
        time.sleep(interval)

    print("[WARN] Timed out waiting for all servers to delete.", file=sys.stderr)


def delete_load_balancers(execute: bool) -> None:
    print("\n== Load balancers ==")

    lbs = os_list(["loadbalancer"])
    if not lbs:
        print("No load balancers found.")
        return

    for lb in lbs:
        lb_id = value_get(lb, "id", "ID")
        lb_name = value_get(lb, "name", "Name", default=lb_id)

        cmd = ["openstack", "loadbalancer", "delete", "--cascade", "--wait", lb_id]
        if execute:
            print(f"[DELETE] {' '.join(cmd)}  # {lb_name}")
            run_cmd(cmd, allow_fail=True, retries=2, retry_delay=5)
        else:
            print(f"[DRY-RUN] {' '.join(cmd)}  # {lb_name}")


def delete_servers(execute: bool) -> None:
    print("\n== Servers ==")

    servers = os_list(["server"])
    if not servers:
        print("No servers found.")
        return

    for srv in servers:
        srv_id = value_get(srv, "ID", "id")
        srv_name = value_get(srv, "Name", "name", default=srv_id)

        cmd = ["openstack", "server", "delete", srv_id]
        if execute:
            print(f"[DELETE] {' '.join(cmd)}  # {srv_name}")
            run_cmd(cmd, allow_fail=True, retries=1)
        else:
            print(f"[DRY-RUN] {' '.join(cmd)}  # {srv_name}")

    if execute:
        wait_for_no_servers()


def delete_floating_ips(execute: bool) -> None:
    print("\n== Floating IPs ==")

    fips = os_list(["floating", "ip"])
    if not fips:
        print("No floating IPs found.")
        return

    for fip in fips:
        fip_id = value_get(fip, "ID", "id")
        fip_ip = value_get(fip, "Floating IP Address", "floating_ip_address", default=fip_id)

        os_delete(["floating", "ip"], fip_id, execute=execute, allow_fail=True, label=str(fip_ip))


def delete_volume_snapshots(execute: bool) -> None:
    print("\n== Volume snapshots ==")

    snaps = os_list(["volume", "snapshot"])
    if not snaps:
        print("No volume snapshots found.")
        return

    for snap in snaps:
        snap_id = value_get(snap, "ID", "id")
        snap_name = value_get(snap, "Name", "name", default=snap_id)
        status = normalize_status(value_get(snap, "Status", "status"))

        if status in {"deleting", "error_deleting"}:
            print(f"[SKIP] snapshot already in transitional state: {snap_name} ({status})")
            continue

        cmd = ["openstack", "volume", "snapshot", "delete", snap_id]
        if execute:
            print(f"[DELETE] {' '.join(cmd)}  # {snap_name}")
            run_cmd(cmd, allow_fail=True, retries=1)
        else:
            print(f"[DRY-RUN] {' '.join(cmd)}  # {snap_name}")


def delete_volumes(execute: bool) -> None:
    print("\n== Volumes ==")

    vols = os_list(["volume"])
    if not vols:
        print("No volumes found.")
        return

    mode = get_volume_delete_mode()
    print(f"Volume delete mode detected: {mode}")

    for vol in vols:
        vol_id = value_get(vol, "ID", "id")
        vol_name = value_get(vol, "Name", "name", default=vol_id)
        status = normalize_status(value_get(vol, "Status", "status"))
        attached = value_get(vol, "Attached to", "attached_to", default="")

        if attached and str(attached).strip() not in {"", "[]", "None", "null"}:
            print(f"[SKIP] volume still attached: {vol_name} ({attached})")
            continue

        if status in {"deleting"}:
            print(f"[SKIP] volume already deleting: {vol_name}")
            continue

        if mode == "cascade":
            primary_cmd = ["openstack", "volume", "delete", "--cascade", vol_id]
        elif mode == "purge":
            primary_cmd = ["openstack", "volume", "delete", "--purge", vol_id]
        else:
            primary_cmd = ["openstack", "volume", "delete", vol_id]

        fallback_cmd = ["openstack", "volume", "delete", vol_id]

        if execute:
            print(f"[DELETE] {' '.join(primary_cmd)}  # {vol_name}")
            result = run_cmd(primary_cmd, allow_fail=True, retries=1)

            if result is None and primary_cmd != fallback_cmd:
                print(f"[DELETE] {' '.join(fallback_cmd)}  # fallback for {vol_name}")
                run_cmd(fallback_cmd, allow_fail=True, retries=1)
        else:
            print(f"[DRY-RUN] {' '.join(primary_cmd)}  # {vol_name}")
            if primary_cmd != fallback_cmd:
                print(f"[DRY-RUN] {' '.join(fallback_cmd)}  # fallback")


def delete_nondefault_security_groups(execute: bool) -> None:
    print("\n== Security groups ==")

    sgs = os_list(["security", "group"])
    targets = []

    for sg in sgs:
        sg_name = value_get(sg, "Name", "name")
        sg_id = value_get(sg, "ID", "id")
        if sg_name == "default":
            continue
        targets.append((sg_id, sg_name))

    if not targets:
        print("No non-default security groups found.")
        return

    for sg_id, sg_name in targets:
        os_delete(
            ["security", "group"],
            sg_id,
            execute=execute,
            allow_fail=True,
            label=str(sg_name),
        )


def list_router_ports(router_id: str) -> List[Dict[str, Any]]:
    return list_ports_for_router(router_id)


def extract_port_ids(text: str) -> List[str]:
    return list(dict.fromkeys(UUID_PATTERN.findall(text or "")))


def detach_router_port(router_id: str, port_id: str, execute: bool) -> bool:
    port = os_show(["port"], port_id, allow_fail=True)
    if not port:
        print(f"[WARN] Unable to inspect attached port {port_id}", file=sys.stderr)
        return False

    fixed_ips = value_get(port, "fixed_ips", "Fixed IP Addresses", default=[])
    subnet_ids = extract_subnet_ids(fixed_ips)

    if subnet_ids:
        detached = False
        for subnet_id in subnet_ids:
            cmd = ["openstack", "router", "remove", "subnet", router_id, subnet_id]
            if execute:
                print(f"[UPDATE] {' '.join(cmd)}")
                result = run_cmd(cmd, allow_fail=True, retries=1)
                detached = result is not None or detached
            else:
                print(f"[DRY-RUN] {' '.join(cmd)}")
                detached = True
        return detached

    cmd = ["openstack", "router", "remove", "port", router_id, port_id]
    if execute:
        print(f"[UPDATE] {' '.join(cmd)}")
        return run_cmd(cmd, allow_fail=True, retries=1) is not None

    print(f"[DRY-RUN] {' '.join(cmd)}")
    return True


def run_delete_router(router_id: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["openstack", "router", "delete", router_id],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def remove_router_subnets(router_id: str, execute: bool) -> None:
    ports = list_router_ports(router_id)
    detached_any = False

    for port in ports:
        device_owner = value_get(port, "Device Owner", "device_owner", default="") or ""
        port_id = value_get(port, "ID", "id")
        fixed_ips = value_get(port, "Fixed IP Addresses", "fixed_ips", default=[])

        if device_owner not in {
            "network:router_interface",
            "network:ha_router_replicated_interface",
        }:
            continue

        subnet_ids = extract_subnet_ids(fixed_ips)

        if subnet_ids:
            for subnet_id in subnet_ids:
                cmd = ["openstack", "router", "remove", "subnet", router_id, subnet_id]
                if execute:
                    print(f"[UPDATE] {' '.join(cmd)}")
                    run_cmd(cmd, allow_fail=True, retries=1)
                else:
                    print(f"[DRY-RUN] {' '.join(cmd)}")
                detached_any = True
        elif port_id:
            cmd = ["openstack", "router", "remove", "port", router_id, port_id]
            if execute:
                print(f"[UPDATE] {' '.join(cmd)}")
                run_cmd(cmd, allow_fail=True, retries=1)
            else:
                print(f"[DRY-RUN] {' '.join(cmd)}")
            detached_any = True

    if not detached_any:
        print("  no router interface ports found")


def remove_router_gateway(router_id: str, execute: bool) -> None:
    cmd = ["openstack", "router", "unset", "--external-gateway", router_id]
    if execute:
        print(f"[UPDATE] {' '.join(cmd)}")
        run_cmd(cmd, allow_fail=True, retries=1)
    else:
        print(f"[DRY-RUN] {' '.join(cmd)}")


def delete_routers(execute: bool) -> None:
    print("\n== Routers ==")

    routers = list_routers_long()
    if not routers:
        print("No routers found.")
        return

    for router in routers:
        router_id = value_get(router, "ID", "id")
        router_name = value_get(router, "Name", "name", default=router_id)

        print(f"-- clearing router {router_name} ({router_id})")
        remove_router_gateway(router_id, execute=execute)
        remove_router_subnets(router_id, execute=execute)

        cmd = ["openstack", "router", "delete", router_id]
        if execute:
            print(f"[DELETE] {' '.join(cmd)}")
            proc = run_delete_router(router_id)
            if proc.returncode == 0:
                continue

            err = OSCommandError(
                f"Command failed ({proc.returncode}): {' '.join(cmd)}\n"
                f"STDERR:\n{proc.stderr.strip()}\n"
                f"STDOUT:\n{proc.stdout.strip()}"
            )
            print(f"[WARN] {err}", file=sys.stderr)

            attached_port_ids = extract_port_ids(proc.stderr)
            if not attached_port_ids:
                continue

            print(
                "  retrying router cleanup after detaching attached ports: "
                + ", ".join(attached_port_ids)
            )
            detached_any = False
            for port_id in attached_port_ids:
                detached_any = detach_router_port(router_id, port_id, execute=True) or detached_any

            if detached_any:
                print(f"[DELETE] {' '.join(cmd)}  # retry")
                run_cmd(cmd, allow_fail=True, retries=1)
        else:
            print(f"[DRY-RUN] {' '.join(cmd)}")


def delete_non_router_ports(execute: bool, keep_network_ids: Set[str]) -> None:
    print("\n== Leftover non-router ports ==")

    ports = list_ports_long()
    if not ports:
        print("No ports found.")
        return

    for port in ports:
        port_id = value_get(port, "ID", "id")
        network_id = value_get(port, "Network", "network_id")
        device_owner = value_get(port, "Device Owner", "device_owner", default="") or ""
        name = value_get(port, "Name", "name", default=port_id)

        if network_id in keep_network_ids:
            continue

        if device_owner in {
            "network:router_interface",
            "network:router_gateway",
            "network:ha_router_replicated_interface",
        }:
            print(f"[SKIP] router-owned port: {port_id} ({device_owner})")
            continue

        cmd = ["openstack", "port", "delete", port_id]
        if execute:
            print(f"[DELETE] {' '.join(cmd)}")
            run_cmd(cmd, allow_fail=True, retries=1)
        else:
            print(f"[DRY-RUN] {' '.join(cmd)}")
        print(f"  target: {name} ({device_owner})")


def delete_subnets(execute: bool, keep_subnet_ids: Set[str]) -> None:
    print("\n== Subnets ==")

    subnets = os_list(["subnet"])
    targets = []

    for subnet in subnets:
        subnet_id = value_get(subnet, "ID", "id")
        subnet_name = value_get(subnet, "Name", "name", default=subnet_id)

        if subnet_id in keep_subnet_ids:
            continue

        targets.append((subnet_id, subnet_name))

    if not targets:
        print("No subnets eligible for deletion.")
        return

    for subnet_id, subnet_name in targets:
        cmd = ["openstack", "subnet", "delete", subnet_id]
        if execute:
            print(f"[DELETE] {' '.join(cmd)}  # {subnet_name}")
            run_cmd(cmd, allow_fail=True, retries=1)
        else:
            print(f"[DRY-RUN] {' '.join(cmd)}  # {subnet_name}")


def delete_networks(execute: bool, keep_network_ids: Set[str]) -> None:
    print("\n== Networks ==")

    nets = os_list(["network"])
    targets = []

    for net in nets:
        net_id = value_get(net, "ID", "id")
        net_name = value_get(net, "Name", "name", default=net_id)

        if net_id in keep_network_ids or net_name == "PUBLICNET":
            continue

        targets.append((net_id, net_name))

    if not targets:
        print("No networks eligible for deletion.")
        return

    for net_id, net_name in targets:
        cmd = ["openstack", "network", "delete", net_id]
        if execute:
            print(f"[DELETE] {' '.join(cmd)}  # {net_name}")
            run_cmd(cmd, allow_fail=True, retries=1)
        else:
            print(f"[DRY-RUN] {' '.join(cmd)}  # {net_name}")


def cleanup_network_stack(
    execute: bool,
    keep_network_ids: Set[str],
    keep_subnet_ids: Set[str],
    passes: int = 2,
) -> None:
    for pass_num in range(1, passes + 1):
        print(f"\n==== Network cleanup pass {pass_num}/{passes} ====")
        delete_routers(execute)
        delete_non_router_ports(execute, keep_network_ids=keep_network_ids)
        delete_subnets(execute, keep_subnet_ids=keep_subnet_ids)
        delete_networks(execute, keep_network_ids=keep_network_ids)


def main() -> None:
    parser = argparse.ArgumentParser(description="Dependency-aware OpenStack project cleanup.")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually perform deletions. Without this flag, the script only prints what it would do.",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip the interactive target-project confirmation prompt.",
    )
    parser.add_argument(
        "--network-passes",
        type=int,
        default=2,
        help="Number of router/port/subnet/network cleanup passes to run (default: 2).",
    )
    args = parser.parse_args()

    which_or_die("openstack")
    verify_auth()
    confirm_target_project(skip_confirmation=args.yes)

    publicnet_id = get_publicnet_id()
    keep_network_ids: Set[str] = set()
    keep_subnet_ids: Set[str] = set()

    if publicnet_id:
        keep_network_ids.add(publicnet_id)
        keep_subnet_ids = get_publicnet_subnet_ids(publicnet_id)
        print(f"Preserving PUBLICNET network: {publicnet_id}")
        if keep_subnet_ids:
            print(f"Preserving PUBLICNET subnets: {', '.join(sorted(keep_subnet_ids))}")
    else:
        print("PUBLICNET not found. No network will be preserved by that name.")

    print("\nMode:", "EXECUTE" if args.execute else "DRY-RUN")

    delete_load_balancers(args.execute)
    delete_servers(args.execute)
    delete_floating_ips(args.execute)
    delete_volume_snapshots(args.execute)
    delete_volumes(args.execute)
    delete_nondefault_security_groups(args.execute)

    cleanup_network_stack(
        execute=args.execute,
        keep_network_ids=keep_network_ids,
        keep_subnet_ids=keep_subnet_ids,
        passes=max(1, args.network_passes),
    )

    print("\nCleanup pass complete.")
    if not args.execute:
        print("This was a dry-run. Re-run with --execute to actually delete resources.")


if __name__ == "__main__":
    main()

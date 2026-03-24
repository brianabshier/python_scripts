OVERVIEW

This script performs a dependency-aware cleanup of an OpenStack project using the OpenStack CLI. It deletes most resources in the correct order to avoid common dependency conflicts. The goal is to automate what is otherwise a manual and error-prone cleanup process.

• What It Deletes

Load balancers (Octavia)
Servers / instances
Floating IPs
Volume snapshots
Volumes
Non-default security groups
Routers (including interfaces and gateways)
Non-router ports
Subnets
Networks

• What It Preserves

SSH keypairs (not touched at all)
Security group named: default
Network named: PUBLICNET
Any subnet attached to PUBLICNET
Requirements
Python 3
OpenStack CLI (openstack) installed
Valid OpenStack credentials sourced in your shell
(e.g. source openrc)

• USAGE

Dry run (safe, no changes made):

`python3 cleanup_openstack_project.py`

Execute actual deletion:

`python3 cleanup_openstack_project.py --execute`

Increase network cleanup passes (useful for stubborn environments):

`python3 cleanup_openstack_project.py --execute --network-passes 3`

No irreversible actions occur unless --execute is used

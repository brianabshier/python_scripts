import requests
import json
from datetime import datetime, timedelta
import csv

# Prompt user for account information
username = input("Enter your Rackspace username: ")
api_key = input("Enter your Rackspace API key: ")
account_id = input("Enter your Rackspace account ID: ")

# Ask user whether to generate a cost optimization report
run_cost_report = input("Generate Cost Optimization Report? (Y/N): ").strip().lower() == 'y'
export_to_file = input("Export report to CSV file? (Y/N): ").strip().lower() == 'y'

# Prompt user to enter regions to scan
valid_regions = ['dfw', 'iad', 'ord', 'hkg', 'syd', 'lon']
region_input = input(f"Enter comma-separated Rackspace regions to scan (default: {', '.join(valid_regions)}): ").strip()

if region_input:
    selected_regions = [r.strip().lower() for r in region_input.split(',') if r.strip()]
    invalid = [r for r in selected_regions if r not in valid_regions]
    if invalid:
        print(f"Warning: Invalid region(s) entered: {', '.join(invalid)}. They will be skipped.")
    regions = [r for r in selected_regions if r in valid_regions]
else:
    regions = list(valid_regions)


# Authenticate and get token for each region
auth_url = 'https://identity.api.rackspacecloud.com/v2.0/tokens'
auth_payload = {
    'auth': {
        'RAX-KSKEY:apiKeyCredentials': {
            'username': username,
            'apiKey': api_key
        }
    }
}

tokens = {}

print("Authenticating across regions...")
for region in regions:
    response = requests.post(auth_url, json=auth_payload)
    if response.status_code == 200:
        tokens[region] = response.json()['access']['token']['id']
        print(f"  Authenticated for region {region.upper()}")
    else:
        print(f'  Authentication failed for region {region.upper()}:', response.status_code)

# Helper function to parse Rackspace timestamps
def parse_rackspace_date(date_str):
    return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")

# Helper function to fetch all paginated results from Rackspace API
def fetch_all_pages(url, headers, key_name, params=None):
    if params is None:
        params = {}
    all_items = []
    while True:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            print(f"  Failed to fetch data from {url} with params {params}, status: {response.status_code}")
            break
        data = response.json()
        items = data.get(key_name, [])
        all_items.extend(items)
        # Check for pagination marker/next page
        # Rackspace pagination uses 'next' links or marker param:
        # We check if 'next' exists in the response or if 'marker' param is needed
        # Some APIs use 'links' with rel 'next' or 'marker' for paging

        # This is a generic approach:
        links = data.get('links', [])
        next_url = None
        for link in links:
            if link.get('rel') == 'next':
                next_url = link.get('href')
                break
        if next_url:
            url = next_url
            params = {}  # Already included in next_url
        else:
            # Check if marker param needed
            if len(items) == 0:
                break
            last_id = items[-1].get('id')
            if not last_id:
                break
            # If no 'next' link, try marker param
            if 'marker' in params and params['marker'] == last_id:
                break  # Avoid infinite loop if marker doesn't advance
            params['marker'] = last_id
    return all_items

# Collect issues for cost report
cost_issues = {
    'unattached_volumes': [],
    'shutoff_or_error_servers': [],
    'zero_node_load_balancers': [],
    'error_databases': [],
    'old_images': []
}

print("\nStarting data collection...")
# Process each region
for region, token in tokens.items():
    print(f"\nProcessing region: {region.upper()} ...")
    headers = {'X-Auth-Token': token}

    # CLOUD SERVERS
    servers_url = f'https://{region}.servers.api.rackspacecloud.com/v2/{account_id}/servers/detail'
    servers_response = requests.get(servers_url, headers=headers)
    if servers_response.status_code == 200:
        servers = servers_response.json().get('servers', [])
        print(f"  Retrieved {len(servers)} servers")
        for server in servers:
            if run_cost_report and server['status'].lower() in ('error', 'shutoff'):
                cost_issues['shutoff_or_error_servers'].append({"region": region, **server})
    else:
        print(f"  Failed to retrieve servers: {servers_response.status_code}")

    # CLOUD BLOCK STORAGE
    blockstorage_url = f'https://{region}.blockstorage.api.rackspacecloud.com/v1/{account_id}/volumes/detail'
    blockstorage_response = requests.get(blockstorage_url, headers=headers)
    if blockstorage_response.status_code == 200:
        volumes = blockstorage_response.json().get('volumes', [])
        print(f"  Retrieved {len(volumes)} block storage volumes")
        for volume in volumes:
            if run_cost_report and volume['status'].lower() == 'available':
                cost_issues['unattached_volumes'].append({"region": region, **volume})
    else:
        print(f"  Failed to retrieve block storage volumes: {blockstorage_response.status_code}")

    # LOAD BALANCERS
    loadbalancers_url = f'https://{region}.loadbalancers.api.rackspacecloud.com/v1.0/{account_id}/loadbalancers'
    lb_response = requests.get(loadbalancers_url, headers=headers)
    if lb_response.status_code == 200:
        lbs = lb_response.json().get('loadBalancers', [])
        print(f"  Retrieved {len(lbs)} load balancers")
        for lb in lbs:
            if run_cost_report and lb.get('nodeCount', 0) == 0:
                cost_issues['zero_node_load_balancers'].append({"region": region, **lb})
    else:
        print(f"  Failed to retrieve load balancers: {lb_response.status_code}")

    # CLOUD DATABASES - Use pagination
    db_url = f'https://{region}.databases.api.rackspacecloud.com/v1.0/{account_id}/instances'
    dbs = fetch_all_pages(db_url, headers, 'instances')
    print(f"  Retrieved {len(dbs)} cloud databases (paginated)")
    for db in dbs:
        if run_cost_report and db['status'].lower() == 'error':
            cost_issues['error_databases'].append({"region": region, **db})

    # IMAGES
    images_url = f'https://{region}.images.api.rackspacecloud.com/v2/{account_id}/images'
    img_response = requests.get(images_url, headers=headers)
    if img_response.status_code == 200:
        imgs = img_response.json().get('images', [])
        print(f"  Retrieved {len(imgs)} images")
        one_year_ago = datetime.utcnow() - timedelta(days=365)
        for img in imgs:
            created_str = img.get('created_at') or img.get('created')
            if created_str:
                created = parse_rackspace_date(created_str)
                if run_cost_report and created < one_year_ago:
                    cost_issues['old_images'].append({"region": region, **img})
            else:
                print(f"  Warning: No creation date found for image {img.get('id')}")
    else:
        print(f"  Failed to retrieve images: {img_response.status_code}")

    # Summary per region
    print(f"  Summary for {region.upper()}:")
    print(f"    Unattached Volumes: {len([v for v in cost_issues['unattached_volumes'] if v['region'] == region])}")
    print(f"    Servers in Error/Shutoff: {len([s for s in cost_issues['shutoff_or_error_servers'] if s['region'] == region])}")
    print(f"    Load Balancers with 0 Nodes: {len([lb for lb in cost_issues['zero_node_load_balancers'] if lb['region'] == region])}")
    print(f"    Databases in Error: {len([db for db in cost_issues['error_databases'] if db['region'] == region])}")
    print(f"    Old Saved Images: {len([img for img in cost_issues['old_images'] if img['region'] == region])}")

# Output the cost optimization report
if run_cost_report:
    print("\nCOST OPTIMIZATION REPORT")
    print("========================")

    print(f"Unattached Volumes (Available Status): {len(cost_issues['unattached_volumes'])}")
    for v in cost_issues['unattached_volumes']:
        print(f"- {v['region'].upper()} Volume: {v.get('display_name', v.get('id'))}")

    print(f"\nServers in Error/Shutoff State: {len(cost_issues['shutoff_or_error_servers'])}")
    for s in cost_issues['shutoff_or_error_servers']:
        print(f"- {s['region'].upper()} Server: {s.get('name', s['id'])} ({s['status']})")

    print(f"\nLoad Balancers with 0 Nodes: {len(cost_issues['zero_node_load_balancers'])}")
    for lb in cost_issues['zero_node_load_balancers']:
        print(f"- {lb['region'].upper()} Load Balancer: {lb.get('name', lb['id'])}")

    print(f"\nCloud Databases in Error State: {len(cost_issues['error_databases'])}")
    for db in cost_issues['error_databases']:
        print(f"- {db['region'].upper()} Database: {db.get('name', db.get('id'))} ({db['status']})")
        
print(f"\nSaved Images Older Than 365 Days: {len(cost_issues['old_images'])}")
for img in cost_issues['old_images']:
    print(f"- {img['region'].upper()} Image: {img.get('name', img.get('id'))}")

if export_to_file:
    filename = f"rackspace_cost_optimization_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    print(f"\nExporting report to {filename}...")

    # Flatten and write to CSV
    with open(filename, mode='w', newline='') as csvfile:
        fieldnames = ['Category', 'Region', 'ID', 'Name', 'Status', 'Additional Info']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        def write_items(category, items, name_key='name'):
            for item in items:
                writer.writerow({
                    'Category': category,
                    'Region': item.get('region'),
                    'ID': item.get('id', ''),
                    'Name': item.get(name_key, ''),
                    'Status': item.get('status', ''),
                    'Additional Info': json.dumps(item)
                })

        write_items('Unattached Volume', cost_issues['unattached_volumes'], 'display_name')
        write_items('Server Error/Shutoff', cost_issues['shutoff_or_error_servers'], 'name')
        write_items('Load Balancer 0 Nodes', cost_issues['zero_node_load_balancers'], 'name')
        write_items('Database Error', cost_issues['error_databases'], 'name')
        write_items('Old Image', cost_issues['old_images'], 'name')

    print("Export complete.")

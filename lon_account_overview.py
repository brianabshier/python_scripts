import requests
import json

# Prompt user for account information
username = input("Enter your Rackspace username: ")
api_key = input("Enter your Rackspace API key: ")
account_id = input("Enter your Rackspace account ID: ")

# Define regions
regions = ['lon']

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

for region in regions:
    response = requests.post(auth_url, json=auth_payload)
    if response.status_code == 200:
        tokens[region] = response.json()['access']['token']['id']
    else:
        print(f'Authentication failed for region {region}:', response.status_code)
        continue

# Fetch Cloud Servers information for each region
for region, token in tokens.items():
    # Fetch Cloud Servers information
    servers_url = f'https://{region}.servers.api.rackspacecloud.com/v2/{account_id}/servers/detail'
    headers = {'X-Auth-Token': token}
    servers_response = requests.get(servers_url, headers=headers)

    if servers_response.status_code == 200:
        servers_data = servers_response.json()
        
        # Process and display Cloud Servers information
        print(f"\nCLOUD SERVERS IN {region.upper()}:")
        for server in servers_data['servers']:
            print("- Name:", server['name'])
            try:
                print("  Public IPs:", server['addresses']['public'])
            except KeyError:
                print("  Public IPs: NOT FOUND")
            try:
                print("  Private IPs:", server['addresses']['private'])
            except KeyError:
                print("  Private IPs: NOT FOUND")
            print("  ID:", server['id'])
            print("  Status:", server['status'])
            print("  Flavor ID:", server['flavor']['id'])
            try:
                print("  Image ID:", server['image']['id'])
            except (KeyError, TypeError):
                print("  Image ID: NOT FOUND")
            print("  Created:", server['created'])
            try:
                print("  Image Schedule:", server['RAX-SI:image_schedule'])
            except KeyError:
                print("  Image Schedule: NO BACKUP IMAGE SCHEDULED")
            print("  Hypervisor ID:", server['hostId'])
            print()
    else:
        print(f'Failed to fetch Cloud Servers data for region {region}:', servers_response.status_code)

    # Fetch Cloud Block Storage information
    blockstorage_url = f'https://{region}.blockstorage.api.rackspacecloud.com/v1/{account_id}/volumes/detail'
    blockstorage_response = requests.get(blockstorage_url, headers=headers)

    if blockstorage_response.status_code == 200:
        blockstorage_data = blockstorage_response.json()
        
        # Process and display Cloud Block Storage information
        print(f"\nCLOUD BLOCK STORAGE IN {region.upper()}:")
        for volume in blockstorage_data['volumes']:
            print("- Name:", volume['display_name'])
            print("  ID:", volume['id'])
            print("  Status:", volume['status'])
            print("  Size:", volume['size'])
            print("  Attached to:", volume.get('attachments', []))  # List of attachments if any
            print()
    else:
        print(f'Failed to fetch Cloud Block Storage data for region {region}:', blockstorage_response.status_code)

    # Fetch Cloud Load Balancers information
    loadbalancers_url = f'https://{region}.loadbalancers.api.rackspacecloud.com/v1.0/{account_id}/loadbalancers'
    loadbalancers_response = requests.get(loadbalancers_url, headers=headers)

    if loadbalancers_response.status_code == 200:
        loadbalancers_data = loadbalancers_response.json()
        
        # Process and display Cloud Load Balancers information
        print(f"\nCLOUD LOAD BALANCERS IN {region.upper()}:")
        for lb in loadbalancers_data['loadBalancers']:
            print("- Name:", lb['name'])
            print("  ID:", lb['id'])
            print("  Status:", lb['status'])
            print("  Created:", lb['created'])
            print("  Protocol:", lb['protocol'])
            print("  Node Count:", lb['nodeCount'])
            print()
    else:
        print(f'Failed to fetch Cloud Load Balancers data for region {region}:', loadbalancers_response.status_code)
        
    # Fetch Cloud Databases information
    databases_url = f'https://{region}.databases.api.rackspacecloud.com/v1.0/{account_id}/instances'
    databases_response = requests.get(databases_url, headers=headers)

    if databases_response.status_code == 200:
        databases_data = databases_response.json()
        
        # Process and display Cloud Databases information
        print(f"\nCLOUD DATABASES IN {region.upper()}:")
        for db in databases_data['instances']:
            print("- Name:", db['name'])
            print("  ID:", db['id'])
            print("  Status:", db['status'])
            print("  Datastore:", db['datastore']['type'])
            print("  Datastore Version:", db['datastore']['version'])
            print("  Volume:", db['volume']['size'])
            print("  Backup Schedule:", db['schedule']['enabled'])
            try:
                print("  HA Group ID:", db['ha_id'])
            except (KeyError, TypeError):
                print("  HA Group ID: NOT PART OF HA GROUP")
            print()
    else:
        print(f'Failed to fetch Cloud Databases data for region {region}:', databases_response.status_code)
        
    # Fetch HA Cloud Databases information
    ha_databases_url = f'https://{region}.databases.api.rackspacecloud.com/v1.0/{account_id}/ha'
    ha_databases_response = requests.get(ha_databases_url, headers=headers)

    if ha_databases_response.status_code == 200:
        ha_databases_data = ha_databases_response.json()
    
        # Process and display HA Cloud Databases information
        print(f"\nHA GROUPS IN {region.upper()}:")
        for ha_db in ha_databases_data['ha_instances']:
            print("- Name:", ha_db['name'])
            print("  ID:", ha_db['id'])
            print("  Status:", ha_db['state'])
            print("  Datastore:", ha_db['datastore']['type'])
            print()
    else:
        print(f'Failed to fetch High Availability Cloud Databases data for region {region}:', ha_databases_response.status_code)

# Fetch DNS Information (run once at the end)
dns_url = f'https://dns.api.rackspacecloud.com/v1.0/{account_id}/domains'
dns_response = requests.get(dns_url, headers=headers)

if dns_response.status_code == 200:
    dns_data = dns_response.json()

    # Process and display DNS information
    print(f"\nDNS ZONES IN ACCOUNT:")
    for dns in dns_data['domains']:
        print("- Name:", dns['name'])
        print("  ID:", dns['id'])
        print("  Email Address:", dns['emailAddress'])
        print("  Created:", dns['created'])
        print("  Updated:", dns['updated'])
        print()
else:
    print(f'Failed to fetch DNS data for account.', dns_response.status_code)

# Define regions
regions = ['lon']

for region in regions:
    # Fetch Cloud Backup information for the current region
    backup_agents_url = f'https://{region}.backup.api.rackspacecloud.com/v1.0/{account_id}/user/agents'
    backup_agents_response = requests.get(backup_agents_url, headers=headers)

    if backup_agents_response.status_code == 200:
        backup_agents_data_str = backup_agents_response.text
        
        try:
            backup_agents_data = json.loads(backup_agents_data_str)
            
            # Check if the response data is empty
            if not backup_agents_data:
                print(f"No Cloud Backup systems found in {region.upper()}.")
            else:
                # Process and display Cloud Backup information
                print(f"\nCLOUD BACKUP SYSTEMS IN {region.upper()}:")
                for agents in backup_agents_data:
                    print("- Machine Name:", agents.get('MachineName', 'NOT FOUND'))
                    print("  Agent ID:", agents.get('MachineAgentId', 'NOT FOUND'))
                    print("  Status:", agents.get('status', 'NOT FOUND'))
                    print("  Backup Container:", agents.get('BackupContainer', 'NOT FOUND'))
                    print("  Encrypted:", agents.get('IsEncrypted', 'NOT FOUND'))
                    print("  Datacenter:", agents.get('Datacenter', 'NOT FOUND'))
                    print()
        except json.JSONDecodeError as e:
            print(f'Failed to decode JSON response for region {region}:', e)
    else:
        print(f'Failed to fetch Cloud Backup data for region {region}:', backup_agents_response.status_code)

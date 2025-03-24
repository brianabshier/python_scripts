import requests
import json
from datetime import datetime

def authenticate(username, api_key, region='DFW'):
    url = "https://identity.api.rackspacecloud.com/v2.0/tokens"
    headers = {'Content-Type': 'application/json'}
    data = {
        "auth": {
            "RAX-KSKEY:apiKeyCredentials": {
                "username": username,
                "apiKey": api_key
            }
        }
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    token = response.json()['access']['token']['id']
    tenant_id = response.json()['access']['token']['tenant']['id']
    return token, tenant_id

def get_load_balancer_usage(token, tenant_id, lb_id, start_date, end_date, region='DFW'):
    url = f"https://{region}.loadbalancers.api.rackspacecloud.com/v1.0/{tenant_id}/loadbalancers/{lb_id}/usage?startTime={start_date}&endTime={end_date}"
    headers = {'X-Auth-Token': token, 'Accept': 'application/json'}
    all_records = []
    
    while url:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        all_records.extend(data.get("loadBalancerUsageRecords", []))
        
        next_link = next((link["link"]["href"] for link in data.get("links", []) if link["link"]["rel"] == "next"), None)
        url = next_link if next_link else None
    
    return all_records

def aggregate_usage(records):
    total_incoming_transfer = sum(record["incomingTransfer"] for record in records)
    total_outgoing_transfer = sum(record["outgoingTransfer"] for record in records)
    total_incoming_transfer_ssl = sum(record["incomingTransferSsl"] for record in records)
    total_outgoing_transfer_ssl = sum(record["outgoingTransferSsl"] for record in records)
    total_num_polls = sum(record["numPolls"] for record in records)
    total_connections = sum(record["averageNumConnections"] for record in records) / len(records) if records else 0
    total_connections_ssl = sum(record["averageNumConnectionsSsl"] for record in records) / len(records) if records else 0
    
    return {
        "totalIncomingTransfer": total_incoming_transfer,
        "totalOutgoingTransfer": total_outgoing_transfer,
        "totalIncomingTransferSsl": total_incoming_transfer_ssl,
        "totalOutgoingTransferSsl": total_outgoing_transfer_ssl,
        "totalNumPolls": total_num_polls,
        "averageNumConnections": total_connections,
        "averageNumConnectionsSsl": total_connections_ssl
    }

def main():
    username = input("Enter Rackspace username: ")
    api_key = input("Enter Rackspace API key: ")
    region = input("Enter region (default 'DFW'): ") or 'DFW'
    lb_id = input("Enter Load Balancer ID: ")
    start_date = input("Enter start date (YYYY-MM-DD): ")
    end_date = input("Enter end date (YYYY-MM-DD): ")
    
    try:
        token, tenant_id = authenticate(username, api_key, region)
        records = get_load_balancer_usage(token, tenant_id, lb_id, start_date, end_date, region)
        aggregated_data = aggregate_usage(records)
        print(json.dumps(aggregated_data, indent=4))
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()


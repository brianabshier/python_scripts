import requests
import json

def authenticate(account_type):
    """Authenticate with Rackspace and return the token, tenant ID, and region."""
    print(f"\nEnter credentials for the {account_type} account:")
    username = input("Username: ")
    api_key = input("API key: ")
    region = input("Region where volume exists: ")
    auth_url = "https://identity.api.rackspacecloud.com/v2.0/tokens"

    headers = {"Content-Type": "application/json"}
    data = {
        "auth": {
            "RAX-KSKEY:apiKeyCredentials": {
                "username": username,
                "apiKey": api_key
            }
        }
    }

    response = requests.post(auth_url, headers=headers, data=json.dumps(data))
    response.raise_for_status()

    auth_data = response.json()["access"]
    token = auth_data["token"]["id"]
    tenant_id = auth_data["token"].get("tenant")

    return token, tenant_id["id"], region

def create_transfer(source_token, tenant_id, volume_id, region):
    """Create a transfer request for the specified volume."""
    url = f"https://{region}.blockstorage.api.rackspacecloud.com/v1/{tenant_id}/os-volume-transfer"
    headers = {
        "X-Auth-Token": source_token,
        "Content-Type": "application/json"
    }
    data = {
        "transfer": {
            "name": "VolumeTransfer",
            "volume_id": volume_id
        }
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))
    response.raise_for_status()

    return response.json()["transfer"]

def accept_transfer(destination_token, tenant_id, transfer_id, auth_key, region):
    """Accept a transfer using the transfer ID and authentication key."""
    url = f"https://{region}.blockstorage.api.rackspacecloud.com/v1/{tenant_id}/os-volume-transfer/{transfer_id}/accept"
    headers = {
        "X-Auth-Token": destination_token,
        "Content-Type": "application/json"
    }
    data = {
        "accept": {
            "auth_key": auth_key
        }
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))
    response.raise_for_status()

    return response.json()

def main():
    try:
        volume_id = input("Enter the ID of the volume to transfer: ")

        print("\nAuthenticating source account...")
        source_token, source_tenant_id, region = authenticate("source")

        print("\nAuthenticating destination account...")
        destination_token, destination_tenant_id, _ = authenticate("destination")

        print("\nCreating volume transfer...")
        transfer = create_transfer(source_token, source_tenant_id, volume_id, region)
        transfer_id = transfer["id"]
        auth_key = transfer["auth_key"]

        print(f"Transfer created. Transfer ID: {transfer_id}, Auth Key: {auth_key}")

        print("\nAccepting volume transfer...")
        accept_transfer(destination_token, destination_tenant_id, transfer_id, auth_key, region)

        print("\nVolume transfer completed successfully.")

    except requests.exceptions.HTTPError as e:
        print(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()


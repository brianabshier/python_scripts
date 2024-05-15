Rackspace Overview Script

This script fetches various information about a Rackspace cloud account using the Rackspace API. It prompts the user to input their Rackspace username, API key, and account ID. Then, it authenticates with the Rackspace API and retrieves data for the following services in each supported region:

Cloud Servers
Cloud Block Storage
Cloud Load Balancers
Cloud Databases
High Availability Cloud Databases
DNS Zones
Cloud Backup

The script iterates over predefined regions ('dfw', 'iad', 'ord', 'hkg', 'syd'), fetching data for each one and printing it to the console. Additionally, it handles cases where certain data may not be available or the API request fails.

Usage:

1) Run the script: python3 account_overview.py
2) Enter your Rackspace username, API key, and account ID when prompted.
3) The script will fetch and display information for each region's cloud services.

Requirements:
- Python 3.x
- requests library (install via pip install requests if not already installed)

Notes:
Ensure you have a Rackspace OSPC account and your user has the necessary permissions to access the required services via the API.
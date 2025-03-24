Rackspace Cloud Load Balancer Usage Aggregator

Overview:
This script authenticates with the Rackspace API using a username and API key, retrieves historical usage data for a specified Cloud Load Balancer, and aggregates the results. The script supports pagination and calculates total and average usage metrics.

Features:
- Authenticates with Rackspace Identity API to obtain an access token.
- Retrieves usage data for a Cloud Load Balancer within a user-specified date range.
- Handles API pagination to gather all records.
- Aggregates total and average usage metrics, including:
  - Incoming and outgoing transfer (regular and SSL).
  - Number of polling events.
  - Average number of connections (regular and SSL).

Prerequisites:
- Python 3.x
- requests module (install with 'pip install requests')

Usage:
1. Run the script:
   python script.py
2. Enter the required information when prompted:
   - Rackspace username
   - API key
   - Region (default: 'DFW')
   - Load Balancer ID
   - Start date (YYYY-MM-DD)
   - End date (YYYY-MM-DD)
3. The script will authenticate, fetch usage data, and display aggregated results in JSON format.

Example Output:
{
    "totalIncomingTransfer": 34029,
    "totalOutgoingTransfer": 12000,
    "totalIncomingTransferSsl": 5000,
    "totalOutgoingTransferSsl": 3000,
    "totalNumPolls": 120,
    "averageNumConnections": 2.5,
    "averageNumConnectionsSsl": 0.0
}

Notes:
- Ensure your Rackspace credentials are correct.
- The script defaults to the 'DFW' region if none is specified.
- The API may enforce rate limits; handle accordingly if necessary.

License:
This script is provided as-is without warranty or support.

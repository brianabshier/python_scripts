Rackspace Cloud Account Optimization Script
===================================

This script connects to the Rackspace Public Cloud API and scans your cloud infrastructure across specified regions to identify cost optimization opportunities, such as:

- Unattached Cloud Block Storage volumes
- Cloud Servers in shutoff or error states
- Load Balancers with zero nodes
- Cloud Databases in an error state
- Saved Images older than 365 days

Requirements
------------
- Python 3.6 or newer
- Internet access to Rackspace Public Cloud API
- Rackspace account with username, API key, and account ID

Usage
-----
1. Run the script:
   python rackspace_cost_optimization.py

2. Enter the following when prompted:
   - Rackspace username
   - Rackspace API key
   - Rackspace account ID
   - Whether to generate the cost optimization report (Y/N)
   - Whether to export the report to a CSV file (Y/N)
   - Comma-separated list of regions to scan (e.g., dfw,iad,lon)
     (Press Enter to use the default list: dfw, iad, ord, hkg, syd, lon)

3. The script will authenticate to each region and display progress messages as it scans services.

4. If requested, the report will be saved as a CSV file in the current directory.

Output
------
- Console output summarizing optimization issues by region and category.
- Optional CSV file with detailed data for further analysis.

Notes
-----
- The script includes built-in support for paginated API results.
- Authentication is performed independently for each region.
- This tool is intended for read-only auditing and does not make any changes to your infrastructure.

License
-------
MIT License – use freely at your own risk.

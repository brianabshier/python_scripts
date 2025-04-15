Python File Utilities

This repository contains some Python scripts for manipulating text files.

1. DNS Zone Splitter:
- Splits a file with multiple DNS zone configurations into individual zone files.
- Usage: `python dns_zone_splitter.py input_file.txt`

2. Text File Splitter:
- Splits a large text file into smaller files with a specified number of lines.
- Usage: `python text_file_splitter.py`

3. Compare
- Compares the contents of two text files line by line and prints out the matching lines as well as the lines that are unique to each file.
- Usage: `python compare.py`

4. Account Overview
- This script fetches various information about a Rackspace cloud account using the Rackspace API. It allows the user to authenticate with the Rackspace API and retrieves data for a number of services in each supported region.
- Usage: `python account_overview.py`
- NOTE: If you are interracting with a UK account which utilizes the LON region, use the `lon_account_overview.py` script.

5. LB Node Check
- This python3 script checks a specific Rackspace Cloud Load Balancer and if it finds a node in an 'OFFLINE' status will send an email to the configured address using the configured SMTP setup.
- Usage: `python3 lb_node_check.py`

6. CORs Adder
- This python2 script uses pyrax and variables set by the user within the file to add CORS headers as metadata to a Cloud Files container.
- Usage: `python cf_cors.py`

7. Cloud Files Log Parser
- There are two python3 scripts called logparser.py and logparser_geo.py that allow a user to parse through their Rackspace Cloud Files CDN/Access logs and obtain information on the log files such as most frequently requested files, respnse codes, source IPs, etc.
- The logparser_geo.py file incudes geolocation lookups to match a continent on the top 10 identified IPs in the logs
- The parser will look inside a directory for any log.gz files, extract them, and parse them.
- The scripts do not involve the fetching/downloading of any log files - this must be done separately.
- Review the README_logparser.txt file for more information on dependencies and requirements.
- Usage: `python3 logparser.py /$DIR/$DIR`

8. Load Balancer Historical Data Puller
- This script authenticates with the Rackspace API using a username and API key, retrieves historical usage data for a specified Cloud Load Balancer, and aggregates the results. The script supports pagination and calculates total and average usage metrics.
- Usage: `python3 lb_historical.py`

9. Volume Transfer
- This script authenticates with both the source Rackspace Account and the destination Rackspace Account and transfers a Cloud Block Storage Volume from the source to the destination.
- Usage: `python3 volume_transfer.py`

Author: Brian Abshier

License: MIT License

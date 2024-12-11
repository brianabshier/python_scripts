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

Author: Brian Abshier

License: MIT License

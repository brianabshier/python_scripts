CHECK ENDPOINTS SCRIPT
======================

Description:
------------
This Python script checks a specified text-based file for the presence of any known endpoints (e.g., URLs or domain names). It scans the file line-by-line and reports any matches.

Endpoints checked by default:
- api.mosso.com
- auth.api.rackspacecloud.com
- lon.auth.api.rackspacecloud.com
- hkg.identity.api.rackspacecloud.com
- identity.prod.ord1.cidm.rackspace.net
- identity.prod.lon3.cidm.rackspace.net
- identity.prod.syd2.cidm.rackspace.net
- rackidentity.api.rackspacecloud.com
- lon.rackidentity.api.rackspacecloud.com

Usage:
------

Option 1: Provide the file path as a command-line argument
-----------------------------------------------------------
Example:
    python check_endpoints.py path/to/yourfile.txt

Option 2: Run the script and input the file path when prompted
---------------------------------------------------------------
Example:
    python check_endpoints.py
    (Then type the path to the file when asked)

Output:
-------
- If any of the endpoints are found in the file, the script will print the line number and contents.
- If no endpoints are found, it will notify you accordingly.
- If the file doesn't exist or is unreadable, an error message will be shown.

Requirements:
-------------
- Python 3.x
- The file being scanned should be a readable text-based file (e.g., .py, .js, .txt)

Notes:
------
- The list of endpoints can be modified directly in the script.
- This script only scans a single file at a time.

Author:
-------
Brian Abshier

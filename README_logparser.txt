Log Parser Script

This repository contains two versions of a log parser script for analyzing web server logs (in `.log.gz` format). The parser provides insights into various statistics, such as the most frequent IP addresses, files requested, response codes, and overall request counts. The geolocation version also provides continent information for the top IP addresses.

Requirements

The following Python packages are required to run both versions of the log parser:

- `ipwhois` (for geolocation lookups in `logparser_geo.py`)
- `argparse` (for parsing command-line arguments)
- `gzip` (for handling `.gz` files)
- `re` (for regular expression matching)
- `collections` (for counting IPs, files, and response codes)

To install the required packages, run:

pip install ipwhois

Versions

logparser.py (No Geolocation)

This version parses `.log.gz` files and generates the following statistics:

- Total number of requests
- Number of requests per file
- Number of requests per response code
- Top 5 most frequent IP addresses and the files they requested

How to use:

1. Save the script as `logparser.py`.
2. Run the script with the directory containing your `.log.gz` log files as an argument:

   python logparser.py /path/to/log/directory

Output Example:

Processing: /path/to/logs/access1.log.gz
Processing: /path/to/logs/access2.log.gz
Total requests: 350

Total response codes:
  200: 270 requests
  404: 50 requests
  500: 30 requests

Top IPs with the most requests:
192.168.1.1: 50 requests
192.168.1.2: 45 requests

Top requested files:
/path/to/file1.jpg: 100 requests
  Response codes:
    200: 90 requests
    404: 10 requests

/path/to/file2.png: 80 requests
  Response codes:
    200: 75 requests
    500: 5 requests
...

logparser_geo.py (With Geolocation)

This version parses `.log.gz` files, generates the same statistics as `logparser.py`, and adds geolocation information for the top 10 most frequent IP addresses.

- Total number of requests
- Number of requests per file
- Number of requests per response code
- Top 10 most frequent IP addresses with their continent information
- Top requested files with response codes

How to use:

1. Save the script as `logparser_geo.py`.
2. Run the script with the directory containing your `.log.gz` log files as an argument:

   python logparser_geo.py /path/to/log/directory

Output Example:

Processing: /path/to/logs/access1.log.gz
Processing: /path/to/logs/access2.log.gz
Total requests: 350

Total response codes:
  200: 270 requests
  404: 50 requests
  500: 30 requests

Top IPs with the most requests:
192.168.1.1: 50 requests (Continent: NA)
192.168.1.2: 45 requests (Continent: NA)

Top requested files:
/path/to/file1.jpg: 100 requests
  Response codes:
    200: 90 requests
    404: 10 requests

/path/to/file2.png: 80 requests
  Response codes:
    200: 75 requests
    500: 5 requests
...

Features

- **Parsing `.log.gz` files**: Both versions of the script handle `.log.gz` compressed log files.
- **Geolocation (optional)**: `logparser_geo.py` performs geolocation lookup for the top 10 IPs to determine their continent (using `ipwhois`).
- **UTF-8 Decoding**: The script safely handles logs with potential encoding issues using `errors='ignore'`.

Notes

- The geolocation feature requires an internet connection and uses the `ipwhois` library to perform lookups, which may take some time depending on the number of IPs.
- For large log files or many logs, the script may take some time to process due to the geolocation lookups.

License

This script is free to use under the [MIT License](https://opensource.org/licenses/MIT).
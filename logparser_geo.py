import os
import gzip
import re
import argparse
from collections import Counter, defaultdict
from ipwhois import IPWhois

# Regular expression pattern for log format
log_format = r'(?P<ip>\S+) - - \[(?P<datetime>[^\]]+)\] "(?P<method>\S+) (?P<url>\S+) (?P<http_version>\S+)" (?P<response_code>\S+) (?P<bytes_sent>\S+) "(?P<referrer>\S+)" "(?P<user_agent>.+)"'

# Function to get continent by IP using ipwhois
def get_continent_by_ip(ip):
    try:
        ipwhois = IPWhois(ip)
        result = ipwhois.lookup_rdap()
        continent = result.get('asn_country_code', 'Unknown')
        return continent
    except Exception as e:
        print(f"Error fetching geolocation for {ip}: {e}")
        return 'Unknown'

# Function to parse individual log files
def parse_log_file(file_path):
    ip_counter = Counter()
    file_counter = Counter()
    response_code_counter = defaultdict(Counter)

    total_requests = 0
    total_response_codes = defaultdict(int)

    with gzip.open(file_path, 'rt', errors='ignore') as f:  # Open with error handling
        for line in f:
            match = re.match(log_format, line)
            if match:
                ip = match.group('ip')
                url = match.group('url')
                response_code = match.group('response_code')

                ip_counter[ip] += 1
                file_counter[url] += 1
                response_code_counter[url][response_code] += 1

                total_requests += 1
                total_response_codes[response_code] += 1

    return ip_counter, file_counter, response_code_counter, total_requests, total_response_codes

# Function to parse all log files in a directory
def parse_logs_in_directory(directory):
    ip_counter = Counter()
    file_counter = Counter()
    response_code_counter = defaultdict(Counter)

    total_requests = 0
    total_response_codes = defaultdict(int)

    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".log.gz"):
                file_path = os.path.join(root, file)
                print(f"Processing: {file_path}")
                ip_count, file_count, response_code_count, file_total_requests, file_total_response_codes = parse_log_file(file_path)

                ip_counter.update(ip_count)
                file_counter.update(file_count)
                for file, codes in response_code_count.items():
                    response_code_counter[file].update(codes)
                total_requests += file_total_requests
                for code, count in file_total_response_codes.items():
                    total_response_codes[code] += count

    return ip_counter, file_counter, response_code_counter, total_requests, total_response_codes

# Function to perform geolocation on the top N IPs
def geolocate_top_ips(ip_counter, top_n=10):
    top_ips = ip_counter.most_common(top_n)
    ip_geolocation = {}

    for ip, _ in top_ips:
        continent = get_continent_by_ip(ip)
        ip_geolocation[ip] = continent

    return ip_geolocation

# Function to print parsed statistics
def print_stats(ip_counter, file_counter, response_code_counter, total_requests, total_response_codes, ip_geolocation):
    print(f"Total requests: {total_requests}")
    print("\nTotal response codes:")
    for code, count in total_response_codes.items():
        print(f"  {code}: {count} requests")

    print("\nTop IPs with the most requests:")
    for ip, count in ip_counter.most_common(5):
        continent = ip_geolocation.get(ip, 'Unknown')
        print(f"  {ip}: {count} requests (Continent: {continent})")

    print("\nTop requested files:")
    for url, count in file_counter.most_common(5):
        print(f"  {url}: {count} requests")
        print(f"    Response codes:")
        for code, count in response_code_counter[url].items():
            print(f"      {code}: {count} requests")

def main():
    parser = argparse.ArgumentParser(description="Parse log files and generate statistics.")
    parser.add_argument("directory", help="Directory containing .log.gz files")
    args = parser.parse_args()

    ip_counter, file_counter, response_code_counter, total_requests, total_response_codes = parse_logs_in_directory(args.directory)

    # Perform geolocation on the top 10 IPs
    ip_geolocation = geolocate_top_ips(ip_counter, top_n=10)

    print_stats(ip_counter, file_counter, response_code_counter, total_requests, total_response_codes, ip_geolocation)

if __name__ == "__main__":
    main()


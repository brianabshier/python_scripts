import os
import re
import gzip
import argparse
from collections import Counter, defaultdict

# Log line format: '195.124.109.192 - - [18/10/2024:05:20:17 +0000] "GET /path/to/file HTTP/1.1" 403 699 "-" "Mozilla/5.0"'
log_format = r'(?P<ip>\d+\.\d+\.\d+\.\d+) - - \[\d{2}/\d{2}/\d{4}:\d{2}:\d{2}:\d{2} \+\d{4}\] "(?P<method>\S+) (?P<url>\S+) HTTP/1.1" (?P<response_code>\d+) \d+ "-" "(?P<user_agent>[^"]+)"'

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

def parse_logs_in_directory(directory):
    ip_counter = Counter()
    file_counter = Counter()
    response_code_counter = defaultdict(Counter)
    
    total_requests = 0
    total_response_codes = defaultdict(int)

    # Walk through the directory and process all .log.gz files
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.log.gz'):
                file_path = os.path.join(root, file)
                print(f"Processing: {file_path}")
                ip_count, file_count, response_code_count, file_total_requests, file_total_response_codes = parse_log_file(file_path)

                ip_counter.update(ip_count)
                file_counter.update(file_count)
                for url, counts in response_code_count.items():
                    response_code_counter[url].update(counts)

                total_requests += file_total_requests
                for code, count in file_total_response_codes.items():
                    total_response_codes[code] += count

    return ip_counter, file_counter, response_code_counter, total_requests, total_response_codes

def main():
    parser = argparse.ArgumentParser(description="Parse all .log.gz files in a directory to find the most requested IPs, files, response codes, and totals.")
    parser.add_argument('directory', type=str, help="Path to the directory containing the .log.gz files")
    
    args = parser.parse_args()

    ip_count, file_count, response_code_count, total_requests, total_response_codes = parse_logs_in_directory(args.directory)

    # Print total requests
    print(f"Total requests: {total_requests}\n")

    # Print total response codes
    print("Total response codes:")
    for code, count in total_response_codes.items():
        print(f"  {code}: {count} requests")

    # Print top 5 IPs with the most requests
    print("\nTop 5 IPs with the most requests:")
    for ip, count in ip_count.most_common(5):
        print(f'{ip}: {count} requests')

    # Print top 5 files requested
    print("\nTop 5 files requested:")
    for url, count in file_count.most_common(5):
        print(f'{url}: {count} requests')

        # Print response code breakdown for each file
        print("  Response codes:")
        for code, code_count in response_code_count[url].items():
            print(f"    {code}: {code_count} requests")

if __name__ == "__main__":
    main()


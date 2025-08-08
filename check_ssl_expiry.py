#!/usr/bin/env python3
import ssl
import socket
import sys
from datetime import datetime
from urllib.parse import urlparse

DAYS_WARNING = 30

def get_ssl_expiry_date(hostname, port=443):
    context = ssl.create_default_context()
    with socket.create_connection((hostname, port), timeout=5) as sock:
        with context.wrap_socket(sock, server_hostname=hostname) as ssock:
            cert = ssock.getpeercert()
            expiry_str = cert['notAfter']
            expiry_date = datetime.strptime(expiry_str, '%b %d %H:%M:%S %Y %Z')
            return expiry_date

def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <endpoint_file>")
        sys.exit(1)

    endpoint_file = sys.argv[1]
    hosts_checked = set()

    with open(endpoint_file) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            parsed = urlparse(line)
            hostname = parsed.hostname
            if not hostname:
                print(f"Skipping invalid URL: {line}")
                continue

            if hostname in hosts_checked:
                continue
            hosts_checked.add(hostname)

            try:
                expiry = get_ssl_expiry_date(hostname)
                days_left = (expiry - datetime.utcnow()).days
                status = "OK"
                if days_left <= DAYS_WARNING:
                    status = f"⚠️  EXPIRING in {days_left} days!"
                print(f"{hostname} — expires {expiry} UTC — {status}")
            except Exception as e:
                print(f"Error checking {hostname}: {e}")

if __name__ == "__main__":
    main()


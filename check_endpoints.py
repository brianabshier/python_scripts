import os
import sys

# Endpoints to search for
endpoints = [
	"api.mosso.com",
	"auth.api.rackspacecloud.com",
	"lon.auth.api.rackspacecloud.com",
	"hkg.identity.api.rackspacecloud.com",
	"identity.prod.ord1.cidm.rackspace.net",
	"identity.prod.lon3.cidm.rackspace.net",
	"identity.prod.syd2.cidm.rackspace.net",
	"rackidentity.api.rackspacecloud.com",
	"lon.rackidentity.api.rackspacecloud.com"
]

def search_file_for_endpoints(file_path, endpoints):
    if not os.path.isfile(file_path):
        print(f"[!] File not found: {file_path}")
        return

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    found = False
    for i, line in enumerate(lines, start=1):
        for endpoint in endpoints:
            if endpoint in line:
                print(f"[+] Found '{endpoint}' in {file_path} at line {i}: {line.strip()}")
                found = True
    if not found:
        print(f"[-] No endpoints found in {file_path}.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = input("Enter the path to the file you want to check: ").strip()

    search_file_for_endpoints(file_path, endpoints)

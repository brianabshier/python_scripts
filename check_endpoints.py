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

# Optional: restrict search to specific file extensions (set to None to allow all)
allowed_extensions = ['.py', '.js', '.txt', '.html', '.css', '.json', '.sh']

def search_file(file_path, endpoints):
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"[!] Could not read {file_path}: {e}")
        return

    matches_found = False

    for i, line in enumerate(lines, start=1):
        for endpoint in endpoints:
            if endpoint in line:
                if not matches_found:
                    print(f"\n[+] Matches found in: {file_path}")
                    matches_found = True
                print(f"  Line {i}: {line.strip()}")

def search_directory(dir_path, endpoints):
    for root, _, files in os.walk(dir_path):
        for filename in files:
            file_path = os.path.join(root, filename)
            if allowed_extensions is None or any(file_path.endswith(ext) for ext in allowed_extensions):
                search_file(file_path, endpoints)

def main():
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        path = input("Enter the path to a file or directory to scan: ").strip()

    if not os.path.exists(path):
        print(f"[!] Path does not exist: {path}")
        return

    if os.path.isfile(path):
        search_file(path, endpoints)
    elif os.path.isdir(path):
        search_directory(path, endpoints)
    else:
        print(f"[!] Not a valid file or directory: {path}")

if __name__ == "__main__":
    main()

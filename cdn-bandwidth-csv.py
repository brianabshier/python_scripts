import json
import csv
import sys
from pathlib import Path

BYTES_IN_GIB = 1024 ** 3

def main(filename):
    path = Path(filename)

    if not path.exists():
        print(f"File not found: {filename}")
        sys.exit(1)

    with open(path, "r") as f:
        data = json.load(f)

    domain = data.get("domain", "")
    bandwidth = data.get("bandwidthOut", {})

    daily_rows = []
    region_totals = {}

    for region, region_data in bandwidth.items():
        region_total_bytes = 0

        for entry in region_data[0]:
            bytes_used = entry["count"]
            region_total_bytes += bytes_used

            daily_rows.append({
                "domain": domain,
                "date": entry["timestamp"][:10],
                "region": region,
                "bytes": bytes_used,
                "GiB": round(bytes_used / BYTES_IN_GIB, 2)
            })

        region_totals[region] = region_total_bytes

    # Write daily CSV
    daily_csv = path.with_name(f"{path.stem}_daily.csv")
    with open(daily_csv, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["domain", "date", "region", "bytes", "GiB"]
        )
        writer.writeheader()
        writer.writerows(daily_rows)

    # Write region totals CSV
    totals_csv = path.with_name(f"{path.stem}_region_totals.csv")
    with open(totals_csv, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["domain", "region", "total_bytes", "total_GiB"]
        )
        writer.writeheader()

        for region, total_bytes in region_totals.items():
            writer.writerow({
                "domain": domain,
                "region": region,
                "total_bytes": total_bytes,
                "total_GiB": round(total_bytes / BYTES_IN_GIB, 2)
            })

    print(f"Created:")
    print(f"  {daily_csv}")
    print(f"  {totals_csv}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python bandwidth_to_csv.py <json_file>")
        sys.exit(1)

    main(sys.argv[1])


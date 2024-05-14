import re
import os

def split_dns_zones(input_file):
    # Read the input file
    with open(input_file, 'r') as f:
        data = f.read()

    # Split the data into individual DNS zones based on the pattern
    zones = re.split(r';Configuration for DNS Zone ', data)[1:]

    # Create a directory to store the individual zone files
    output_dir = 'dns_zones'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Write each zone to a separate file
    for idx, zone in enumerate(zones):
        # Extract domain name from the zone
        domain_name = re.search(r'^([\w.-]+)', zone, re.MULTILINE).group(1)
        # Write the zone to a file
        output_file = os.path.join(output_dir, f'{domain_name}.zone')
        with open(output_file, 'w') as f:
            f.write(zone)

        print(f'Zone {idx+1}: {domain_name} written to {output_file}')

# Usage: python script_name.py input_file.txt
if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python script_name.py input_file.txt")
    else:
        input_file = sys.argv[1]
        split_dns_zones(input_file)


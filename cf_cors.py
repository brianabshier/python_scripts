import pyrax

# Configuration Variables (Modify these as needed)
USERNAME = "YOUR_USERNAME"
API_KEY = "YOUR_API_KEY"
REGION = "DFW"  # Set to your desired region, e.g., "DFW", "ORD", etc.
CONTAINER_NAME = "your-container-name"

# Authenticates with Rackspace
pyrax.set_setting("identity_type", "rackspace")
pyrax.set_credentials(USERNAME, API_KEY)

# Sets the region
pyrax.set_setting("region", REGION)

# Gets the Cloud Files client
cf = pyrax.cloudfiles

# Fetches the container
container = cf.get_container(CONTAINER_NAME)

# Sets CORS headers
cors_headers = {
    "X-Container-Meta-Access-Control-Allow-Origin": "*",  # Allows all origins
    "X-Container-Meta-Access-Control-Allow-Methods": "GET, POST, OPTIONS",  # Allowed HTTP methods
    "X-Container-Meta-Access-Control-Allow-Headers": "Content-Type, Authorization",  # Allowed headers
}

# Updates container metadata
for key, value in cors_headers.items():
    container.set_metadata({key: value})

print("CORS headers set for container '{}' in region '{}'.".format(CONTAINER_NAME, REGION))

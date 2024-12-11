import requests
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# This uses python3

# Replace these with your actual Rackspace credentials and email details
username = '$RACKSPACE_USERNAME'
api_key = '$RACKSPACE_APIKEY'
ddi = '$ACCOUNT_NUMBER'          # Your DDI (data center identifier)
lb_id = '$LOADBALANCER_ID'      # Your Load Balancer ID

# Email configuration
sender_email = "$SENDING_EMAIL"  # Sender's email address (replace with your actual email)
recipient_email = "$RECIPIENT_EMAIL"       # Recipient's email address
email_subject = "Alert: Node is OFFLINE"   # Subject of the email

# URL for the Rackspace Identity API to obtain a token
identity_url = 'https://identity.api.rackspacecloud.com/v2.0/tokens'

# Function to authenticate and get the token
def get_auth_token(username, api_key):
    # Prepare authentication payload
    payload = {
        "auth": {
            "RAX-KSKEY:apiKeyCredentials": {
                "username": username,
                "apiKey": api_key
            }
        }
    }

    # Make the request to get the token
    response = requests.post(identity_url, json=payload)
    
    if response.status_code == 200:
        # Extract token from the response
        data = response.json()
        token = data['access']['token']['id']
        return token
    else:
        print(f"Error: Failed to authenticate. Status code: {response.status_code}")
        return None

# Function to send email
def send_email(subject, body):
    try:
        # Set up the SMTP server
        server = smtplib.SMTP('smtp.gmail.com', 587)  # Use your SMTP server here, example is the default SMTP server for gmail.
        server.starttls()  # Secure the connection
        server.login(sender_email, "$MAIIL_PASSWORD")  # Sender's email login credentials (use app password if 2FA enabled)
        
        # Craft the email
        message = MIMEMultipart()
        message['From'] = sender_email
        message['To'] = recipient_email
        message['Subject'] = subject
        message.attach(MIMEText(body, 'plain'))
        
        # Send the email
        server.sendmail(sender_email, recipient_email, message.as_string())
        server.quit()  # Close the connection

        print("Email sent successfully.")

    except Exception as e:
        print(f"Error sending email: {e}")

# Function to check load balancer node status
def check_load_balancer_status(token, ddi, lb_id):
    # API URL for the load balancer details
    lb_url = f'https://$REGION.loadbalancers.api.rackspacecloud.com/v1.0/$ACCOUNT_NUMBER/loadbalancers/{lb_id}'

    # Set the authentication header using the token
    headers = {
        'X-Auth-Token': token,
        'Content-Type': 'application/json'
    }

    # Make the request to get the load balancer details
    print(f"Sending request to: {lb_url}")  # Debugging line
    response = requests.get(lb_url, headers=headers)

    if response.status_code == 200:
        print("Received LBaaS status successfully.")  # Debugging line
        data = response.json()

        # Debugging: print the full JSON structure to ensure we're accessing it correctly
        print("Full response data: ", json.dumps(data, indent=4))

        # Access the 'nodes' list
        nodes = data.get('loadBalancer', {}).get('nodes', [])
        if not nodes:
            print("No nodes found in the load balancer details.")
        else:
            # Check for any nodes that are OFFLINE
            for node in nodes:
                print(f"Node {node['id']} at {node['address']} has status: {node['status']}")
                if node['status'] == 'OFFLINE':
                    # If a node is OFFLINE, send an email alert
                    email_body = f"Node {node['id']} at {node['address']} is OFFLINE.\n\nDetails:\n{json.dumps(node, indent=4)}"
                    send_email(email_subject, email_body)
                    print(f"Warning: Node {node['id']} at {node['address']} is OFFLINE.")
                else:
                    print(f"Node {node['id']} at {node['address']} is {node['status']}.")
    else:
        print(f"Error: Failed to retrieve load balancer details. Status code: {response.status_code}")
        print(f"Response: {response.text}")  # Display full response for debugging

# Main script execution
token = get_auth_token(username, api_key)
if token:
    print(f"Authentication successful. Token: {token[:10]}...")  # Print part of the token for security
    check_load_balancer_status(token, ddi, lb_id)
else:
    print("Authentication failed. Please check your credentials.")

import asyncio
import os
import json
from netbox_device_details import netbox_device_details

# Set environment variables if not already set
os.environ["NETBOX_URL"] = "https://idoh2793.cloud.netboxapp.com/graphql/"
os.environ["NETBOX_TOKEN"] = "ff9a399c5a10baa25652f1df3765cdf9db360399"

# Test function to call 'netbox_device_details' with parameters
async def test_netbox_device_details():
    # Example assistant request
    assistant_request = {
        'device_name_regex': 'cisco*',  # Regex to match device names starting with 'AUS'
        'fields': ['name', 'interfaces', 'location', 'invalid_field']  # Fields to request, including an invalid one
    }
    
    # Call the original function and get the response
    response = await netbox_device_details(assistant_request)
    
    # Print the response in a readable format
    print(json.dumps(response, indent=4))

# Run the test function
if __name__ == "__main__":
    asyncio.run(test_netbox_device_details())

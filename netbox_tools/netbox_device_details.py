import requests
import os
import json
from typing import List, Dict, Any

class NetboxGraphQLClient:
    def __init__(self, url, token):
        self.url = url
        self.headers = {
            "Authorization": f"Token {token}",
            "Content-Type": "application/json",
        }

    def execute_query(self, query: str, variables: Dict[str, Any] = None) -> Dict[str, Any]:
        payload = {
            "query": query,
            "variables": variables or {}
        }
        response = requests.post(self.url, json=payload, headers=self.headers)
        
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise

        return response.json()

    def get_device_details(self, device_name_contains):
        query = """
        query Device($nameContains: String!) {
          device_list(filters: {
            name: {contains: $nameContains}
          }) {
            name
            primary_ip4 {
              display
            }
            primary_ip6 {
              display
            }
            oob_ip {
              address
            }
            device_type {
              model
              manufacturer {
                name
              }
            }
            role {
              name
            }
            location {
              name			
              site {
                name
                racks {
                  name
                  starting_unit
                }
              }
            }
            consoleports {
              name
            }
            interfaces {
              tagged_vlans {
                name
              }
              untagged_vlan {
                name
              }
              name
              type
              lag {
                name
              }
              mtu
              mode
              cable {
                label
                terminations {
                  display
                }
                display
              }
              ip_addresses {
                display
              }
            }
          }
        }
        """
        variables = {"nameContains": device_name_contains}
        return self.execute_query(query, variables)

async def netbox_device_details(arguments):
    netbox_url = os.getenv("NETBOX_URL")
    netbox_token = os.getenv("NETBOX_TOKEN")
    client = NetboxGraphQLClient(netbox_url, netbox_token)
    
    device_name_contains = arguments.get("device_name_contains")
    
    if not device_name_contains:
        return {"error": "'device_name_contains' is a required parameter."}
    
    try:
        result = client.get_device_details(device_name_contains)
        response = {"data": {}}
        
        if 'errors' in result:
            response['error'] = result['errors'][0]['message']
        elif 'data' in result:
            devices = result['data'].get('device_list', [])
            if not devices:
                response['error'] = f"No device found matching contains: {device_name_contains}"
            else:
                response['data'] = {"devices": devices}
        else:
            response['error'] = "Unexpected response structure."
        
        return response
    
    except Exception as e:
        return {"error": str(e)}

# Example usage
async def handle_assistant_request(assistant_request):
    result = await netbox_device_details(assistant_request)
    return result

# You can test the function like this:
# assistant_request = {
#     'device_name_contains': 'cisco'
# }
# import asyncio
# response = asyncio.run(handle_assistant_request(assistant_request))
# print(response)
import requests
import json
import os
from typing import List, Dict, Any

class NetboxGraphQLClient:
    def __init__(self, url: str, token: str):
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

    def get_interfaces(self, interface_regex):
        query = """
        query interface_list($interfaceRegex: String!) {
            interface_list(filters: {name: {regex: $interfaceRegex}}) {
                device {
                    name
                }
                cable {
                    display
                    label
                    status
                }
                connected_endpoints {
                    __typename
                }
                type
                tags {
                    name
                }
                speed
                duplex
                child_interfaces {
                    name
                }
                wwn
                mac_address
                tagged_vlans {
                    name
                }
                untagged_vlan {
                    name
                }
                mtu
                enabled
                mgmt_only
                mode
                bridge {
                    name
                }
                lag {
                    name
                }
                description
                parent {
                    name
                }
                display
                ip_addresses {
                    address
                    role
                    status
                    tenant {
                        name
                    }
                    dns_name
                    description
                    assigned_object {
                        __typename
                    }
                    vrf {
                        name
                    }
                }
            }
        }
        """
        variables = {"interfaceRegex": interface_regex}
        result = self.execute_query(query, variables)
        
        return result

async def netbox_interfaces(arguments):
    netbox_url = os.getenv("NETBOX_URL")
    netbox_token = os.getenv("NETBOX_TOKEN")
    client = NetboxGraphQLClient(netbox_url, netbox_token)
    
    interface_regex = arguments.get("interface_regex")
    
    if not interface_regex:
        return {"error": "'interface_regex' is a required parameter."}
    
    try:
        result = client.get_interfaces(interface_regex)
        response = {}
        
        if 'errors' in result:
            response['error'] = result['errors'][0]['message']
        elif 'data' in result:
            interfaces = result['data'].get('interface_list')
            if not interfaces:
                response['error'] = f"No interfaces found matching regex: {interface_regex}."
            else:
                response['data'] = {"interfaces": interfaces}
        
        return response
    
    except Exception as e:
        return {"error": str(e)}

# Example usage
async def handle_assistant_request(assistant_request: Dict[str, Any]) -> Dict[str, Any]:
    result = await netbox_interfaces(assistant_request)
    return result

# You can test the function like this:
# assistant_request = {
#     'interface_regex': 'ethernet1/0',
# }
# import asyncio
# response = asyncio.run(handle_assistant_request(assistant_request))
# print(json.dumps(response, indent=2))
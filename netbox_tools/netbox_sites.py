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

    def get_site_details(self, site_name: str) -> Dict[str, Any]:
        query = """
        query Sites($name: String!) {
            site_list(filters: {name: {regex: $name}}) {
                status
                comments
                contacts {
                    contact {
                        name
                        link
                        phone
                    }
                }
                locations {
                    site {
                        name
                    }
                    name
                    facility    
                    devices {
                        name
                        description
                        rack {
                            name
                        }
                    }
                    tenant {
                        name
                    }    
                }
                status
                facility
                time_zone
                physical_address
                description
                region {
                    name
                }
                group {
                    name
                }
                tenant {
                    name
                }
            }
        }
        """
        variables = {"name": f"{site_name}.*"}
        result = self.execute_query(query, variables)
        
        return result

async def netbox_sites(arguments: Dict[str, Any]) -> Dict[str, Any]:
    netbox_url = os.getenv("NETBOX_URL")
    netbox_token = os.getenv("NETBOX_TOKEN")
    client = NetboxGraphQLClient(netbox_url, netbox_token)
    
    site_name = arguments.get("site_name")
    
    if not site_name:
        return {"error": "'site_name' is a required parameter."}
    
    try:
        result = client.get_site_details(site_name)
        response = {}
        
        if 'errors' in result:
            response['error'] = result['errors'][0]['message']
        elif 'data' in result:
            site_data = result['data'].get('site_list')
            if not site_data:
                response['error'] = f"No sites found matching the name: {site_name}."
            else:
                response['data'] = {"sites": site_data}
        
        return response
    
    except Exception as e:
        return {"error": str(e)}

# Example usage
async def handle_assistant_request(assistant_request: Dict[str, Any]) -> Dict[str, Any]:
    result = await netbox_sites(assistant_request)
    return result

# You can test the function like this:
# assistant_request = {
#     'site_name': 'Mel'
# }
# import asyncio
# response = asyncio.run(handle_assistant_request(assistant_request))
# print(response)
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

    def search_roles(self, name_contains):
        query = """
        query SearchRoles($nameContains: String!) {
          device_role_list(filters: {
            name: {i_contains: $nameContains},
          }) {
            display
            description
            devices {
              status
              name
              role {
                name
              }
              id
              location {
                name
              }
              site {
                name
              }
              rack {
                name       
              }
            }
          }
        }
        """
        variables = {"nameContains": name_contains}
        return self.execute_query(query, variables)

    def get_all_roles(self):
        query = """
        query RolesListAll {
          device_role_list {
            display
            description
          }
        }
        """
        return self.execute_query(query)

async def netbox_search_roles(arguments):
    netbox_url = os.getenv("NETBOX_URL")
    netbox_token = os.getenv("NETBOX_TOKEN")
    client = NetboxGraphQLClient(netbox_url, netbox_token)
    
    role_name_contains = arguments.get("role_name_contains")
    
    if not role_name_contains:
        return {"error": "'role_name_contains' is a required parameter for searching roles."}
    
    try:
        result = client.search_roles(role_name_contains)
        response = {"data": {}}
        
        if 'errors' in result:
            response['error'] = result['errors'][0]['message']
        elif 'data' in result:
            device_roles = result['data'].get('device_role_list', [])
            if not device_roles:
                response['message'] = f"No device roles found matching: '{role_name_contains}'"
            else:
                response['data'] = {"device_roles": device_roles}
                response['message'] = f"{len(device_roles)} device role(s) found matching: '{role_name_contains}'"
        else:
            response['error'] = "Unexpected response structure."
        
        return response
    
    except Exception as e:
        return {"error": str(e)}

async def netbox_get_all_roles():
    netbox_url = os.getenv("NETBOX_URL")
    netbox_token = os.getenv("NETBOX_TOKEN")
    client = NetboxGraphQLClient(netbox_url, netbox_token)
    
    try:
        result = client.get_all_roles()
        response = {"data": {}}
        
        if 'errors' in result:
            response['error'] = result['errors'][0]['message']
        elif 'data' in result:
            device_roles = result['data'].get('device_role_list', [])
            if not device_roles:
                response['message'] = "No device roles found."
            else:
                response['data'] = {"device_roles": device_roles}
                response['message'] = f"{len(device_roles)} device role(s) found."
        else:
            response['error'] = "Unexpected response structure."
        
        return response
    
    except Exception as e:
        return {"error": str(e)}

# Example usage
async def handle_assistant_request(assistant_request):
    if assistant_request.get('action') == 'search_roles':
        result = await netbox_search_roles(assistant_request)
    elif assistant_request.get('action') == 'get_all_roles':
        result = await netbox_get_all_roles()
    else:
        result = {"error": "Invalid action specified. Use 'search_roles' or 'get_all_roles'."}
    return result

# You can test the functions like this:
# import asyncio

# Search roles
# assistant_request = {
#     'action': 'search_roles',
#     'role_name_contains': 'WAN'
# }
# response = asyncio.run(handle_assistant_request(assistant_request))
# print(json.dumps(response, indent=2))

# Get all roles
# assistant_request = {
#     'action': 'get_all_roles'
# }
# response = asyncio.run(handle_assistant_request(assistant_request))
# print(json.dumps(response, indent=2))
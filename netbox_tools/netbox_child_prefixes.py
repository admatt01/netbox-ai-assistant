import requests
import os

class NetboxGraphQLClient:
    def __init__(self, url, token):
        self.url = url
        self.headers = {
            "Authorization": f"Token {token}",
            "Content-Type": "application/json",
        }

    def execute_query(self, query, variables=None):
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

    def get_child_prefixes(self, parent_prefix):
        query = """
        query getChildPrefixes($parentPrefix: String!) {
          prefix_list(filters: {
            within: $parentPrefix
          }) {
            description
            status
            role {
              name
            }
            prefix
            vrf {
              name
            }
            site {
              name
            }
            vlan {
              name
              tenant {
                name
              }
            }
          }
        }
        """
        variables = {"parentPrefix": parent_prefix}
        return self.execute_query(query, variables)

async def netbox_child_prefixes(arguments):
    netbox_url = os.getenv("NETBOX_URL")
    netbox_token = os.getenv("NETBOX_TOKEN")
    client = NetboxGraphQLClient(netbox_url, netbox_token)
    
    parent_prefix = arguments.get("parent_prefix")
    
    if not parent_prefix:
        return {"error": "'parent_prefix' is a required parameter."}
    
    try:
        result = client.get_child_prefixes(parent_prefix)
        response = {"data": {}}
        
        if 'errors' in result:
            response['error'] = result['errors'][0]['message']
        elif 'data' in result:
            prefixes = result['data'].get('prefix_list', [])
            if not prefixes:
                response['error'] = f"No prefixes found within: {parent_prefix}"
            else:
                response['data'] = {"prefixes": prefixes}
        else:
            response['error'] = "Unexpected response structure."
        
        return response
    
    except Exception as e:
        return {"error": str(e)}

# Example usage
async def handle_assistant_request(assistant_request):
    result = await netbox_child_prefixes(assistant_request)
    return result

# You can test the function like this:
# assistant_request = {
#     'parent_prefix': '192.168.0.0/22'
# }
# import asyncio
# response = asyncio.run(handle_assistant_request(assistant_request))
# print(response)
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

    def get_prefix_details(self, prefix_regex):
        query = """
        query prefixes($prefixRegex: String!) {
          prefix_list(filters: {
            prefix: {regex: $prefixRegex}
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
            _children
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
        variables = {"prefixRegex": prefix_regex}
        return self.execute_query(query, variables)

async def netbox_prefixes(arguments):
    netbox_url = os.getenv("NETBOX_URL")
    netbox_token = os.getenv("NETBOX_TOKEN")
    client = NetboxGraphQLClient(netbox_url, netbox_token)
    
    prefix_regex = arguments.get("prefix_regex")
    
    if not prefix_regex:
        return {"error": "'prefix_regex' is a required parameter."}
    
    try:
        result = client.get_prefix_details(prefix_regex)
        response = {"data": {}}
        
        if 'errors' in result:
            response['error'] = result['errors'][0]['message']
        elif 'data' in result:
            prefixes = result['data'].get('prefix_list', [])
            if not prefixes:
                response['error'] = f"No prefixes found matching regex: {prefix_regex}"
            else:
                response['data'] = {"prefixes": prefixes}
        else:
            response['error'] = "Unexpected response structure."
        
        return response
    
    except Exception as e:
        return {"error": str(e)}

# Example usage
async def handle_assistant_request(assistant_request):
    result = await netbox_prefixes(assistant_request)
    return result

# You can test the function like this:
# assistant_request = {
#     'prefix_regex': '^192.168.2.64/30$'
# }
# import asyncio
# response = asyncio.run(handle_assistant_request(assistant_request))
# print(response)
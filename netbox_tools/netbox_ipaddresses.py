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

    def get_ipaddresses(self, ipaddress_regex=None, dns_name_regex=None):
        query = """
        query IPaddresses($ipaddressRegex: String, $dnsNameRegex: String) {
            ip_address_list(filters: {
                address: {regex: $ipaddressRegex}
                dns_name: {regex: $dnsNameRegex}
            }) {
                id
                status
                tenant {
                    name
                }
                display
                description
                nat_inside {
                    description
                    address
                }
                nat_outside {
                    description
                    address
                }
                vrf {
                    name
                    interfaces {
                        ip_addresses {
                            address
                        }
                        device {
                            name
                        }
                    }
                }
                dns_name
                role
                services {
                    name
                    protocol
                    ports
                    description
                }
            }
        }
        """
        variables = {
            "ipaddressRegex": ipaddress_regex,
            "dnsNameRegex": dns_name_regex
        }
        result = self.execute_query(query, variables)
        
        return result

async def netbox_ipaddresses(arguments):
    netbox_url = os.getenv("NETBOX_URL")
    netbox_token = os.getenv("NETBOX_TOKEN")
    client = NetboxGraphQLClient(netbox_url, netbox_token)
    
    ipaddress_regex = arguments.get("ipaddress_regex", "")
    dns_name_regex = arguments.get("dns_name_regex", "")
    filter_logic = arguments.get("filter_logic", "and").lower()

    if not ipaddress_regex and not dns_name_regex:
        return {"error": "At least one of 'ipaddress_regex' or 'dns_name_regex' must be non-empty."}
    
    if filter_logic not in ["and", "or"]:
        return {"error": "Invalid filter_logic. Must be 'and' or 'or'."}

    try:
        # Initialize the result lists
        ipaddress_results = []
        dns_name_results = []

        # If 'and' logic, perform one query with both filters
        if filter_logic == "and":
            result = client.get_ipaddresses(ipaddress_regex, dns_name_regex)
            if 'errors' in result:
                return {"error": result['errors'][0]['message']}
            ipaddress_results = result['data'].get('ip_address_list', [])
        else:
            # If 'or' logic, perform two queries and combine results
            if ipaddress_regex:
                ip_result = client.get_ipaddresses(ipaddress_regex, None)
                if 'errors' in ip_result:
                    return {"error": ip_result['errors'][0]['message']}
                ipaddress_results = ip_result['data'].get('ip_address_list', [])

            if dns_name_regex:
                dns_result = client.get_ipaddresses(None, dns_name_regex)
                if 'errors' in dns_result:
                    return {"error": dns_result['errors'][0]['message']}
                dns_name_results = dns_result['data'].get('ip_address_list', [])

            # Combine both results and remove duplicates
            combined_results = {item['id']: item for item in ipaddress_results + dns_name_results}
            ipaddress_results = list(combined_results.values())

        # Prepare the response
        if not ipaddress_results:
            return {"error": "No IP addresses found matching the provided criteria."}
        return {"data": {"ip addresses": ipaddress_results}}

    except Exception as e:
        return {"error": str(e)}

# Example usage
async def handle_assistant_request(assistant_request: Dict[str, Any]) -> Dict[str, Any]:
    result = await netbox_ipaddresses(assistant_request)
    return result

# You can test the function like this:
# assistant_request = {
#     'ipaddress_regex': '^192.168.*',
#     'dns_name_regex': 'nlams.*',
#     'filter_logic': 'or'
# }
# import asyncio
# response = asyncio.run(handle_assistant_request(assistant_request))
# print(json.dumps(response, indent=2))

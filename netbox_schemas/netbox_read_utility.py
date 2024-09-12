import requests
import json

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
        
        print(f"Request URL: {self.url}")
        print(f"Request Headers: {self.headers}")
        print(f"Request Payload: {json.dumps(payload, indent=2)}")
        print(f"Response Status Code: {response.status_code}")
        
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error: {e}")
            print(f"Response Content: {response.text}")
            raise

        return response.json()

    def get_available_queries(self):
        query = """
        query AvailableQueries {
          __schema {
            queryType {
              fields {
                name
                description
                args {
                  name
                  description
                  type {
                    name
                    kind
                    ofType {
                      name
                      kind
                    }
                  }
                }
              }
            }
          }
        }
        """
        result = self.execute_query(query)
        return result['data']['__schema']['queryType']['fields']

    def generate_query_function(self, query_name, args, fields):
        arg_list = ", ".join([f"${arg['name']}: {arg['type']}" for arg in args])
        arg_params = ", ".join([f"{arg['name']}: ${arg['name']}" for arg in args])
        
        query = f"""
        query {query_name}({arg_list}) {{
          {query_name}({arg_params}) {{
            {fields}
          }}
        }}
        """
        
        def query_function(**kwargs):
            return self.execute_query(query, kwargs)
        
        return query_function

# Example usage
if __name__ == "__main__":
    netbox_url = "https://idoh2793.cloud.netboxapp.com/graphql/" 
    netbox_token = "ff9a399c5a10baa25652f1df3765cdf9db360399" 
    client = NetboxGraphQLClient(netbox_url, netbox_token)

    try:
        # Get and print available queries
        available_queries = client.get_available_queries()
        print("Available Queries:")
        for query in available_queries:
            print(f"- {query['name']}: {query['description']}")
            for arg in query['args']:
                arg_type = arg['type']['ofType']['name'] if arg['type']['ofType'] else arg['type']['name']
                print(f"  - Argument: {arg['name']} ({arg_type})")
        print("\n")

        # Find the 'device' query
        device_query = next((q for q in available_queries if q['name'] == 'device'), None)

        if device_query:
            # Extract argument types
            args = [{'name': arg['name'], 'type': arg['type']['ofType']['name'] + '!' if arg['type']['ofType'] else arg['type']['name']} 
                    for arg in device_query['args']]

            # Define the fields for your specific device query
            device_fields = """
            _name
            oob_ip {
              address
            }
            role {
              name
            }
            device_type {
              description
              display
              manufacturer {
                name
              }
            }
            """

            # Generate the query function
            get_device = client.generate_query_function('device', args, device_fields)
            
            # Use the generated function
            result = get_device(id=141)  # Using the device ID from your example, as an integer
            print("Device Query Result:")
            print(json.dumps(result, indent=2))
        else:
            print("Device query not found in available queries.")

    except Exception as e:
        print(f"An error occurred: {e}")
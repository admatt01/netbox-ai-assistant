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
        
        try:
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error: {e}")
            print(f"Response Content: {response.text}")
            raise

    def build_query(self, query_structure):
        query_lines = []
        variables = {}

        def build_field(name, value, indent=""):
            if isinstance(value, dict):
                args = []
                sub_fields = []
                for sub_name, sub_value in value.items():
                    if (sub_name == "__args"):
                        for arg_name, arg_value in sub_value.items():
                            var_name = f"{name}_{arg_name}".replace(".", "_")
                            variables[var_name] = arg_value
                            args.append(f"{arg_name}: ${var_name}")
                    else:
                        sub_fields.extend(build_field(sub_name, sub_value, indent + "  "))
                
                arg_string = f"({', '.join(args)})" if args else ""
                field_string = f"{indent}{name}{arg_string}"
                if sub_fields:
                    return [f"{field_string} {{"] + sub_fields + [f"{indent}}}"]
                else:
                    return [field_string]
            else:
                return [f"{indent}{name}"]

        for top_level_name, top_level_value in query_structure.items():
            query_lines.extend(build_field(top_level_name, top_level_value))

        # Correctly map Python types to GraphQL types
        type_map = {
            int: "Int",
            str: "String",
            bool: "Boolean",
            float: "Float",
        }

        var_declarations = ", ".join(f"${name}: {type_map[type(value)]}!" for name, value in variables.items())
        query_string = f"query ({var_declarations}) {{\n" + "\n".join(query_lines) + "\n}"
        return query_string, variables


    def execute_advanced_query(self, query_structure):
        query, variables = self.build_query(query_structure)
        print("Generated Query:")
        print(query)
        print("\nVariables:")
        print(json.dumps(variables, indent=2))
        return self.execute_query(query, variables)

# Example usage
if __name__ == "__main__":
    netbox_url = "https://idoh2793.cloud.netboxapp.com/graphql/" 
    netbox_token = "ff9a399c5a10baa25652f1df3765cdf9db360399"
    client = NetboxGraphQLClient(netbox_url, netbox_token)

    # Example query structure based on your working query
    query_structure = {
        "device": {
            "__args": {"id": 241},
            "_name": {},
            "oob_ip": {
                "address": {}
            },
            "role": {
                "name": {}
            },
            "location": {
                "name": {},
                "site": {
                    "_name": {}
                }
            }
        }
    }

    try:
        result = client.execute_advanced_query(query_structure)
        print("\nQuery Result:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"An error occurred: {e}")
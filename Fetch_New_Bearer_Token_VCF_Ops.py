"""
Copyright (c) 2025 Alonso Trejo Mora
"""
import requests
import os   # Not a Pip dependency. Built into Python.
import json # Not a Pip dependency. Built into Python.


# Use your Refresh Token to obtain a temporary Bearer Token
# source: https://developer.vmware.com/apis/vrealize-operations/vrealize-operations-cloud-api/latest/
def Fetch_New_Bearer_Token():
    current_dir = os.getcwd()
    ops_api_auth_file_path = os.path.join(current_dir, 'vcf-monitoring-loginData.json')

    with open(ops_api_auth_file_path, 'r') as file:
        jsonContent = json.load(file)

    ops_url = jsonContent['operationsHost']
    requestUrl = f"https://{ops_url}/suite-api"
    extension = "/api/auth/token/acquire"
    headers = { 'Accept': 'application/json',
                'Content-Type': 'application/json'}
    data = json.dumps(jsonContent['loginData'])

    response = requests.post(requestUrl+extension, headers=headers, data=data, verify=False)
    print(response.status_code)
    if response.status_code != 200:
        print(f'ERROR: Status code {response.status_code}')
        exit(1)

    jsonResponse = response.json()

    accessToken = jsonResponse['token']

    # Update the Bearer Token file with the new Bearer Token.
    access_token_path_from_root = os.getcwd() + "/vcf-monitoring-accessToken.txt"

    with open(access_token_path_from_root, 'w') as f:
        f.truncate(0)
        f.write(accessToken)

if __name__ == '__main__':
    Fetch_New_Bearer_Token()

# https://<vcf-ops-fqdn>/suite-api/doc/swagger-ui.html

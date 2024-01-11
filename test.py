import requests
import json
import sys, time

tenant_id = "03d63788-8162-4380-bc13-c4efc557596a"
client_id = "2f3b7c9f-66c8-47f5-8192-449fafe0e21e"
client_secret = "dQ_8Q~pnjUDwYv_dl4v9eIOO~OxiVD8QO7daZaNZ"

token_url = f'https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token'
headers = {'Content-Type': 'application/x-www-form-urlencoded'}

data = {
    'grant_type': 'client_credentials',
    'client_id': client_id,
    'client_secret': client_secret,
    'scope': 'https://graph.microsoft.com/.default'
}

response = requests.post(token_url, headers=headers, data=data)
access_token = response.json()['access_token']

graph_api_endpoint = 'https://graph.microsoft.com/v1.0/'

################################ Get all users in batches #####################################
users_response = requests.get(graph_api_endpoint + 'users', headers={
    'Authorization': 'Bearer ' + access_token,
    "Content-Type": "application/json"
})

print("Checking all users...")

if users_response.status_code == 200:
    # Initialize parameters for pagination
    users_data = []
    url = graph_api_endpoint + 'users'
    batch_num = 1 

    while True:
        users_batch_response = requests.get(url, headers={
            'Authorization': 'Bearer ' + access_token,
            "Content-Type": "application/json"
        })
        if users_batch_response.status_code != 200:
            print(f"Failed to retrieve users. Status code: {users_batch_response.status_code}")
            break
        
        print(f"Requesting batch {batch_num}...")  # Print batch number
        users_batch = users_batch_response.json().get('value', [])
        users_data.extend(users_batch)
        
        next_link = users_batch_response.json().get('@odata.nextLink')
        if not next_link:
            break
        url = next_link  # Move to the next page
        batch_num += 1
        
################################ Filter conditional users #####################################
    licensed_users = []
    conditional_users = []



    for user in users_data:
        user_id = user['id']
        license_details_response = requests.get(graph_api_endpoint + f"users/{user_id}/licenseDetails", headers={
            'Authorization': 'Bearer ' + access_token,
            "Content-Type": "application/json"
        })

        plan = license_details_response.json().get('value')

        print(plan)
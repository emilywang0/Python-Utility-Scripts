#!/usr/bin/env python3
# Author: ewang@atimi.com
# Automates the process of finding and upgrading conditional users in Microsoft365

import requests
import json

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
        
        # Check if the user has a license
        plan = license_details_response.json().get('value')
        if plan:
            licensed_users.append(user)  # Add user to licensed list
            for item in plan:
                servicePlan = item.get('servicePlans', [])
                for plan in servicePlan:
                    service_plan_name = plan.get('servicePlanName', [])
                    provisioning_status = plan.get('provisioningStatus', [])
        
                    if 'SHAREPOINTSTANDARD' in service_plan_name and provisioning_status == 'Disabled':
                            conditional_users.append(user)  # Add user to conditional list if SharePoint plan is disabled
                            print('Conditional user added...')

    # Display conditional users
    def print_list():
        id_num = 1 
        if conditional_users:
            print("\nConditional users:")
            for user in conditional_users:
                print(f"{id_num}) {user['displayName']} - {user['mail']}")
                id_num += 1
        else:
            print("No conditional users found.")

    # # Display licensed users
            
    # if licensed_users:
    #     print("Licensed users:")
    #     for user in licensed_users:
    #         print(user)
    # else:
    #     print("No licensed users found.")
            
    print_list()

else:
    print(f"Failed to retrieve users. Status code: {users_response.status_code}")

################################ Upgrade License #####################################

# Helper function to upgrade license
def upgrade_user(user, type):
    user_id = user['id']
    license_details_response = requests.get(graph_api_endpoint + f"users/{user_id}/licenseDetails", headers={
            'Authorization': 'Bearer ' + access_token,
            "Content-Type": "application/json"
    })

    license = license_details_response.json().get('value')
    item = license[0]
    servicePlan = item.get('servicePlans', [])

    disabledPlans = []
    # Upgrade to Basic license
    if (type == "basic"):
        for plan in servicePlan: 
            if plan["servicePlanName"] in ["YAMMER_ENTERPRISE", "PROJECT_O365_P1", "MICROSOFTBOOKINGS"]:
                disabledPlans.append(plan["servicePlanId"])
        
        data = {
            "addLicenses": [
                {
                "disabledPlans": disabledPlans,
                "skuId": "3b555118-da6a-4418-894f-7df1e2096870" # Business Essentials/Basic License
                }
            ],
            "removeLicenses": []
        }

    # Upgrade to Standard license
    if (type == "standard"):
        # YAMMER_ENTERPRISE, PROJECT_0365_P2, DYN365BC_MS_INVOICING, O365_SB_Relationship_Management
        disabledPlans = ["7547a3fe-08ee-4ccb-b430-5077c5041653", "31b4e2fc-4cd6-4e7d-9c1b-41407303bd66",
                         "39b5c996-467e-4e60-bd62-46066f572726", "5bfe124c-bbdc-4494-8835-f1297d457d79"]
        
        data = {
            "addLicenses": [
                {
                "disabledPlans": disabledPlans,
                "skuId": "f245ecc8-75af-4f8e-b61f-27d8114de5f3" # Business Premium/Standard License
                }
            ],
            "removeLicenses": ["3b555118-da6a-4418-894f-7df1e2096870"]
        }

    remove_response = requests.post(graph_api_endpoint + f"users/{user_id}/assignLicense", json=data, headers={
        'Authorization': 'Bearer ' + access_token,
        "Content-Type": "application/json"
    })
    
    # Check remove_response status and handle accordingly
    if remove_response.status_code == 200:
        print(f"Upgrade for user {user['displayName']} successful.")
        conditional_users.remove(user)
    else:
        print(f"Upgrade for user {user['displayName']} failed. Status code: {remove_response.status_code}, Response: {remove_response.text}")
    

# Command-line prompts for actions
while True:
    user_input = input('Type "upgrade [Number] basic", "upgrade [Number] standard", or "quit": ')

    if user_input.lower() == "quit":
        print("Exiting the application.")
        break

    if user_input.lower().startswith("upgrade"):
        parts = user_input.split(" ")
        if len(parts) == 3 and parts[2] in ["basic", "standard"]:
            try:
                user_number = int(parts[1]) - 1  # Adjust to zero-based index
                user_to_upgrade = conditional_users[user_number]

                upgrade_type = parts[2]
                print(f"Upgrading {user_to_upgrade['displayName']} to {upgrade_type}...")
                
                # Call a function that handles the upgrade based on upgrade_type
                upgrade_user(user_to_upgrade, upgrade_type)
                
                print_list()
            except (ValueError, IndexError):
                print("Invalid user number. Please type a valid number.")
        else:
            print('Invalid input format. Please type "upgrade [Number] basic" or "upgrade [Number] standard".')
    else:
        print('Invalid command. Type "upgrade [Number] basic", "upgrade [Number] standard" or "quit" to exit.')
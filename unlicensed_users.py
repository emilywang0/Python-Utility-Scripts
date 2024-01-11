#!/Library/Frameworks/Python.framework/Versions/3.12/bin/python3
# ....

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
        
# users_response = requests.get(graph_api_endpoint + 'users', headers={
#     'Authorization': 'Bearer ' + access_token,
#     "Content-Type": "application/json"
# })

# if users_response.status_code == 200:
#     users_data = users_response.json().get('value', [])

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
    if conditional_users:
        print("\nConditional users:")
        for user in conditional_users:
            print(user['displayName'])
    else:
        print("No conditional users found.")
    # # Display licensed users
            
    # if licensed_users:
    #     print("Licensed users:")
    #     for user in licensed_users:
    #         print(user)
    # else:
    #     print("No licensed users found.")
            


else:
    print(f"Failed to retrieve users. Status code: {users_response.status_code}")

################################ Upgrade License #####################################

# Helper function to upgrade license
def upgrade_user(user):
    user_id = user['id']
    license_details_response = requests.get(graph_api_endpoint + f"users/{user_id}/licenseDetails", headers={
            'Authorization': 'Bearer ' + access_token,
            "Content-Type": "application/json"
    })

    license = license_details_response.json().get('value')
    for item in license:
        servicePlan = item.get('servicePlans', [])
        # Get all previously disabled plans
        disabled_plans = [plan["servicePlanId"] for plan in servicePlan if "Disabled" in plan["provisioningStatus"]]
    
        # Plans to be enabled (add all previously disabled plans)
        enabled_plans = [{"skuId": plan, "disabledPlans": []} for plan in disabled_plans]
        
        # Plans to be disabled
        disabled_plans_to_disable = [plan["servicePlanId"] for plan in servicePlan if plan["servicePlanName"] in ["YAMMER_ENTERPRISE", "PROJECT_O365_P3", "MICROSOFTBOOKINGS"]]
        
        data = {
            "addLicenses": enabled_plans,
            "removeLicenses": [
                {
                    "disabledPlans": disabled_plans_to_disable,
                }
            ]   
        }

        remove_response = requests.post(graph_api_endpoint + f"users/{user_id}/assignLicense", json=data, headers={
            'Authorization': 'Bearer ' + access_token,
            "Content-Type": "application/json"
        })
        
        # Check remove_response status and handle accordingly
        if remove_response.status_code == 200:
            print(f"Upgrade for user {user['displayName']} successful.")
            conditional_users.remove(user_to_upgrade)
        else:
            print(f"Upgrade for user {user['displayName']} failed. Status code: {remove_response.status_code}, Response: {remove_response.text}")
        


while True:
    user_input = input('Type "upgrade [Full Name]" or "quit": ')
    
    if user_input.lower().startswith("upgrade"):
        parts = user_input.split(" ", 1)
        if len(parts) == 2:
            user_to_upgrade = parts[1].strip()

            # Search within conditional_users for the user based on displayName
            found_user = None
            for user in conditional_users:
                if user.get('displayName') == user_to_upgrade:
                    found_user = user
                    break
                
            if found_user:
                print(f"Upgrading {user_to_upgrade}...")
                # Perform upgrade action here (e.g., remove from conditional users list, perform upgrade process, etc.)
                upgrade_user(found_user)
            else:
                print(f"{user_to_upgrade} is not a conditional user. Check spelling and capitalization of full name")
        else:
            print("Invalid input format. Please type 'upgrade [Full Name]'.")

    elif user_input.lower() == "quit":
        print("Exiting the application.")
        break

    else:
        print('Invalid command. Type "upgrade [Full Name]" or "quit" to exit.')
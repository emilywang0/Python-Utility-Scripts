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

################################ Move all of user file to the archive folder #####################################

# Set the ID of the user whose OneDrive you want to query
user_name = sys.argv[1]

# Set the path of the folder you want to get the ID for
url = graph_api_endpoint + f'users/{user_name}'
response = requests.get(url, headers={
    'Authorization': 'Bearer ' + access_token,
    "Content-Type": "application/json"
})

user_id = response.json()['id']
display_name = response.json()['displayName']
print(user_id)

# ## Create a new folder in archive with user display name

destination_drive_id = "b!cog1bg9pDkOZbc6539Ex2glN-GjsTT1HrYU5qtCnfns98A0KClYBSZslP_ZfNVUd"
item_id = "01GAL4ODN6Y2GOVW7725BZO354PWSELRRZ"

post_url = graph_api_endpoint + f'drives/{destination_drive_id}/items/{item_id}/children'
request_body = {
    "name": display_name,
    "folder": {},
    "@microsoft.graph.conflictBehavior": "rename"
}
response = requests.post(post_url, headers={
    'Authorization': 'Bearer ' + access_token,
    "Content-Type": "application/json"
}, json=request_body)

file_id = response.json()['id']
print(f"Create a file with {file_id} in the archive folder")

# ## Construct the Graph API URL to get the folder metadata

user_source = graph_api_endpoint + f'users/{user_id}/drive/root/children'
response = requests.get(user_source, headers={
    'Authorization': 'Bearer ' + access_token,
    "Content-Type": "application/json"
})

for file in response.json()["value"]:
    data = {
        "parentReference": {
            "id": f"{file_id}",
            "driveId": f"{destination_drive_id}"
        },
    }

    # print(data)
    # print(graph_api_endpoint + f"drives/{file['parentReference']['driveId']}/items/{file['id']}/copy")

    response = requests.post(graph_api_endpoint + f"drives/{file['parentReference']['driveId']}/items/{file['id']}/copy",json=data ,headers={
        'Authorization': 'Bearer ' + access_token,
        "Content-Type": "application/json"
    })

    if (response.status_code == 202):
        print(response)
    else:
        print(json.dumps(response.json(), indent=4))


################################ Convert User to Shared Mailbox #####################################

## Try to convert user to shared mail box by generating power shell script and run it

## Get User manager

import subprocess, os

response = requests.get(graph_api_endpoint + f"users/{user_id}/manager", headers={
    'Authorization': 'Bearer ' + access_token,
    "Content-Type": "application/json"
})


if (response.status_code == 202):
    ## The user has manager
    manager_email = response.json()["mail"] 

    with open("powershell_script_generated.ps1", "w") as f:
        f.write("param($Name, $Manager)\n")
        f.write("Connect-ExchangeOnline\n")
        f.write("Set-Mailbox -Identity $Name -Type Shared\n")
        f.write("Add-MailboxPermission -Identity $Name -User sysadmin -AccessRights FullAccess, ReadPermission -InheritanceType All\n")
        f.write("Add-MailboxPermission -Identity $Name -User $Manager -AccessRights FullAccess, ReadPermission -InheritanceType All\n")
        f.write("Set-Mailbox -Identity $Name -HiddenFromAddressListsEnabled $true\n")

    subprocess.run(["pwsh", "powershell_script_generated.ps1", "-Name", user_name, "-Manager", manager_email])
    os.remove("powershell_script_generated.ps1")

else:
    with open("powershell_script_generated.ps1", "w") as f:
        f.write("param($Name, $Manager)\n")
        f.write("Connect-ExchangeOnline\n")
        f.write("Set-Mailbox -Identity $Name -Type Shared\n")
        f.write("Add-MailboxPermission -Identity $Name -User sysadmin -AccessRights FullAccess, ReadPermission -InheritanceType All\n")
        f.write("Set-Mailbox -Identity $Name -HiddenFromAddressListsEnabled $true\n")

    subprocess.run(["pwsh", "powershell_script_generated.ps1", "-Name", user_name])
    os.remove("powershell_script_generated.ps1")

################################ REMOVE USER LICENSES #####################################


response = requests.get(graph_api_endpoint + f"users/{user_id}/licenseDetails", headers={
    'Authorization': 'Bearer ' + access_token,
    "Content-Type": "application/json"
})

license_remove = []

for plan in response.json()["value"]:
    print("remove plan " + plan["skuPartNumber"])
    license_remove.append(plan["skuId"])

data = {
    "addLicenses": [],
    "removeLicenses": license_remove
}

remove_reponse = requests.post(graph_api_endpoint + f"users/{user_id}/assignLicense", json=data ,headers={
    'Authorization': 'Bearer ' + access_token,
    "Content-Type": "application/json"
})
################################ REMOVE USER GROUPS #####################################

response = requests.get(graph_api_endpoint + f"users/{user_id}/memberOf", headers={
    'Authorization': 'Bearer ' + access_token,
    "Content-Type": "application/json"
})

## Use jumpcloud api to remove user from the group??

remove_group = []
exeption_group = ["Atimi Quality Assurance", "Atimi Product Design", 
                  "Project Management", "Finance", "Atimi Remote Staff", 
                  "Atimi Administration", "Atimi Development", "Contractors India",
                  "Contractors Canada", "Manager", "Staff India", "Staff Canada", "Senior Managers", "Atimi Canada", "Atimi India"
                  ]

distribution_group_or_mail_enabled_group = []

for group in response.json()['value']:

    if group["@odata.type"] == "#microsoft.graph.directoryRole":
        continue
    else:
        if (group["displayName"] not in exeption_group)  and (group["securityEnabled"] != True):
            print("Prepare to remove user from group {}".format(group["displayName"]))
            group_id = group["id"]

            response = requests.delete(graph_api_endpoint + f"groups/{group_id}/members/{user_id}/$ref",headers={
                'Authorization': 'Bearer ' + access_token,
                "Content-Type": "application/json"
            })
            if (response.status_code >= 400):
                print("Can not remove the current user from group {}".format(group["displayName"]))
                print(json.dumps(response.json(), indent= 4))

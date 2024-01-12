### Before running the script:
- Please install python to your computer using this documentation here: https://www.python.org/downloads/
- Once you have python installed, please open the terminal and run (depending on how you install your python, the name might be pip or pip3):
```
python3 install -r requirement.txt 
```

---

### How to use the m365_license_upgrade.py script to automate the process of finding and upgrading conditional users: 
Conditional users should only have limited apps enabled, most notably with SharePoint turned off. However, once they are hired full-time, they should have either a Microsoft Basic license or Microsoft Standard license and be upgraded to have almost all apps enabled. This script automates the process of finding conditional users and upgrading their license plans.

1. Make sure you have downloaded python and the requirement.txt file 
2. Run on the Terminal: 
```
./m365_license_upgrade.py
```
You can also try the following command if the previous is running into problems:
```
python3 m365_license_upgrade.py
```
3. Follow the command line prompts. You can upgrade one conditional user at a time.

---

### How to use the off_boarding.py script to automate the process of off boarding a user from Atimi

- To use the script, you need to install python (Please follow the documentation in here https://www.python.org/downloads/) and powershell (pwsh) if you are on intended to using it on a Mac. To install powershell on Mac, you can follow the documentation provided by Microsoft here: https://learn.microsoft.com/en-us/powershell/scripting/install/installing-powershell-on-macos?view=powershell-7.3. Once you install the Powershell make sure you have Exchange Online PowerShell module install properly on your machine.

- To run the script, open the terminal line and type python off_boarding.py user_name@atimi.com. This script should make a new folder in archive folder with user's display name. Copy the entire user folder to that folder. Convert user to a shared mail box and if user's manager is recorded in Micorsoft, it will add manager and sysadmin permission to that shared mailbox. Then it will remove all the user license and remove them from all the existing group they have (except mail enabled group or distribution list and some group that is managed by power automate group distribution)

- At the start of the python script, there is 3 variables that is hard coded with value which is the parameter you will need to run the script.
```
tenant_id = "YOUR TENANT ID"
client_id = "YOUR CLIENT ID"
client_secret = "YOUR SECRET"
```

- You can access get these parameter by going to https://portal.azure.com/#home, then choose App registrations. You can see the tenant id and the client id in the overview tab. If you want to get the secret, please go to certificates and secret. Please be aware that you can not see the full secret for all the old secret, and you have to generate a new secret once you lose access to your old secret. 

- Secret can also be expired. Please be aware of this once you run the script. Generally, a secret should only last for 6 months.

- When remove user from groups, only remove user from group that is not managed by JumpCloud (M365 and group that are security group)
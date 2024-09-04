import pandas as pd
import pbipy
import requests
from azure.identity import ClientSecretCredential
import json

# Authetification using a Service Principal 
tenant_id = ''
client_id = ''
client_secret = '' # Better use Azure Key Vault or any other Vault alternative

# Enter the workspace name
workspace_name = 'dev-test-gj'

# Enter the Microsoft Entra ID security group
group_name = 'Enter your security group name'

"""
Create a function to get the object ID from Microsoft Entra ID group using Microsoft Graph
The aplication (Service Principal) needs the Group.Read.All permission
"""
# Function to create the access token
def get_access_token(tenant_id, client_id, client_secret):
    url = f'https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    body = {
        'client_id': client_id,
        'scope': 'https://graph.microsoft.com/.default',
        'client_secret': client_secret,
        'grant_type': 'client_credentials'
    }
    response = requests.post(url, headers=headers, data=body)
    response_data = response.json()

    # Check if the response contains 'access_token'
    if 'access_token' in response_data:
        return response_data['access_token']
    else:
        # Print the error details for debugging
        error_description = response_data.get('error_description', 'No error description provided.')
        error = response_data.get('error', 'No error code provided.')
        print(f"Error obtaining access token: {error} - {error_description}")
        return None

# Function to get all groups
def get_all_groups(access_token):
    url = "https://graph.microsoft.com/v1.0/groups"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    groups = []
    while url:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            groups.extend(data.get('value', []))
            url = data.get('@odata.nextLink')  # URL for the next page of groups, if any
        else:
            print(f"Failed to fetch groups: {response.status_code} - {response.text}")
            break
    return groups

# This function gets the group id based on the name
def get_group_id(group_name, access_token):
    url = f'https://graph.microsoft.com/v1.0/groups?$filter=displayName eq \'{group_name}\''
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(url, headers=headers)
    groups = response.json().get('value', [])
    if groups:
        return groups[0]['id']  # Assuming the first match is the desired group
    return None

# Call the function to get the access token
access_token = get_access_token(tenant_id, client_id, client_secret)

# Call the function to get the object id from the Microsoft entra id group
# The application must have the API permission for Group.Read.All as application and granted for the tenant
ad_pbi_id = get_group_id(ad_pbi, access_token)

# Power BI authetification
## Saving the Power BI REST API
pbi_api = 'https://analysis.windows.net/powerbi/api/.default'

# Generate the access token using the Service Principal for the Power BI REST API
auth = ClientSecretCredential(authority = 'https://login.microsoftonline.com/',
                                            tenant_id = tenant_id,
                                            client_id = client_id,
                                            client_secret = client_secret)
access_token = auth.get_token(pbi_api)
access_token = access_token.token

# Save the base URL to call the Power BI REST API
base_url = 'https://api.powerbi.com/v1.0/myorg/'
header = {'Authorization': f'Bearer {access_token}',
          'Content-Type': 'application/json'}

# Use the pbipy library as Python wrapper to use the Power BI API
pbi = pbipy.PowerBI(access_token)

# Get the methods from the Python class admin from pbipy
admin = pbi.admin()

def add_user_to_group(workspace, identifier, access_right, principal_type):
    try:
        # Attempt to add the user to the group
        response = pbi.group(workspace.id).add_user(identifier=identifier, access_right=access_right, principal_type=principal_type)
        print(f"User {identifier} added as {access_right} to {workspace.name}.")
    except Exception as e:
        # Handle exceptions that may occur if the user or group does not exist, or if the user is already in the group
        print(f"Failed to add user {identifier} to {workspace.name}: {str(e)}")

# Assuming ws_dev, ws_qual, and ws_prod are defined and valid workspace objects
try:
    add_user_to_group(ws_dev, ad_pbi_id, "Admin", "Group")
    add_user_to_group(ws_dev, ad_dvs_id, "Contributor", "Group")
    add_user_to_group(ws_dev, ad_opr_id, "Member", "Group")

    add_user_to_group(ws_qual, ad_pbi_id, "Admin", "Group")
    add_user_to_group(ws_qual, ad_dvs_id, "Contributor", "Group")
    add_user_to_group(ws_qual, ad_opr_id, "Member", "Group")

    add_user_to_group(ws_prod, ad_pbi_id, "Admin", "Group")
    add_user_to_group(ws_prod, ad_dvs_id, "Contributor", "Group")
    add_user_to_group(ws_prod, ad_opr_id, "Member", "Group")
except Exception as e:
    print(f"An error occurred: {str(e)}")


# Create a function to check if the workspace you want to create already exists. This function returns TRUE or FALSE
def check_workspace_exists(df, workspace_name):
    existing_name = set(df['name'].values)
    result = workspace_name in existing_name
    return result

# Get all workspaces in the tenant. Make sure to add your Service Principal in the Fabric Admin settings to read admin data
workspace_tenant = admin.groups()

# Extract 'id' and 'name' directly from each group object
data = [{'Group id': ws.id, 'name': ws.name} for ws in workspace_tenant]

# Create a pandas DataFrame from the extracted data
df_workspace = pd.DataFrame(data)

# Check if the workspace you want to create already exists calling the function "check_workspace_exists"
workspace_check_existence = check_workspace_exists(df_workspace, workspace_name)

# Create workspace only if it does not exist
if not workspace_check_existence:
    # Create DEV workspace
    workspace_dev = pbi.create_group(name = workspace_name)
    print(f"Workspace '{workspace_dev.name}' created.")
    # Create TEST workspace
    workspace_test = pbi.create_group(name = workspace_name.replace('dev', 'test'))
    print(f"Workspace '{workspace_test.name}' created.")
    # Create PROD workspace
    workspace_prod = pbi.create_group(name = workspace_name.replace('dev', 'prod'))
    print(f"Workspace '{workspace_prod.name}' created.")
else:
    print(f"A workspace with the name '{workspace_name}' already exists")
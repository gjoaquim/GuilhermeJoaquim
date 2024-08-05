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

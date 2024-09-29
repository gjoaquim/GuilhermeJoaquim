# This code creates a Fabric workspace, assign a Fabric capacity, add user and add a Entra ID security group to the worspace

# Specify the Terraform version and required providers
terraform {
    required_version = ">= 1.8, < 2.0"
    required_providers {
        fabric = {
            source = "microsoft/fabric"                 # Microsoft Fabric provider
            version = "0.1.0-beta.3"                    # Current version of the Fabric provider
        }
        azuread = {
            source = "hashicorp/azuread"                # Azure AD provider
            version = "~> 2.0"                          # Required version for Azure AD provider
        }
    }
}

# Configuration for the Microsoft Fabric provider
provider "fabric" {
    # Configuration for the provider
    client_id = "Enter your Client Id"              # Client ID for authenticating with Microsoft Fabric
    client_secret = "Enter your Secret Id"          # Client secret for authentication (please dont save your secret here. Use Vault or save as enviroment variable in your CI/CD)
    tenant_id = "Enter your Tenant Id"              # Tenant ID for your Microsoft Azure environment
}

# Configuration for the Azure AD provider
provider "azuread" {
    # Configuration for the provider    
    client_id = "Enter your Client Id"              # Client ID for authenticating with Microsoft Fabric
    client_secret = "Enter your Secret Id"          # Client secret for authentication (please dont save your secret here. Use Vault or save as enviroment variable in your CI/CD)
    tenant_id = "Enter your Tenant Id"              # Tenant ID for your Microsoft Azure environment
}

# Data source to retrieve an existing Entra ID group by its display name
data "azuread_group" "example_group" {
    display_name = "Enter the security group name"                  # The display name of the Entra ID group               
}

# Data source to retrieve an existing Azure AD user by their principal name
data "azuread_user" "example_user" {
    user_principal_name = "Enter the email address of the user"     # The principal name (email) of the Azure AD user
}

# Data source to retrieve an existing Fabric capacity by its display name
data "fabric_capacity" "capacity_example" {
   display_name = "Enter your Fabric capacity name"                 # The name of the Fabric capacity to retrieve
}

# Resource block to create a Microsoft Fabric workspace
resource "fabric_workspace" "workspace_example_capacity" {
    display_name = "Test Workspace using Terraform GJ"              # Name of the workspace
    description = "Test using Terraform"                            # Description for the workspace
    capacity_id = data.fabric_capacity.capacity_example.id          # Fabric capacity id
}

# Resource block to assign the Azure AD group as an Admin in the workspace
resource "fabric_workspace_role_assignment" "assign_security_group" {
    workspace_id = fabric_workspace.workspace_example_capacity.id   # Reference to the workspace ID
    principal_id = data.azuread_group.example_group.object_id       # ID of the Entra ID group
    principal_type = "Group"                                        # Specify that the principal type is a group
    role = "Admin"                                                  # Assign Admin role to the group
}

# Resource block to assign the Azure AD user as an Admin in the workspace
resource "fabric_workspace_role_assignment" "assign_user" {         
    workspace_id = fabric_workspace.workspace_example_capacity.id   # Reference to the workspace ID
    principal_id = data.azuread_user.example_user.object_id         # ID of the Entra ID group
    principal_type = "User"                                         # Specify that the principal type is a group   
    role = "Admin"                                                  # Assign Admin role to the group 
}
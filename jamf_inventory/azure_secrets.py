"""
Module Name: azure_secrets.py
Description: A class for getting secrets from azure key vault
Must be signed in to Azure CLI locally for this to work.
Author: John Naeder
Created: 2021-06-03
"""

from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential


class AzureSecrets:
    """
    Connects to Azure keyvault and then has a method to get a secret from a
    key name.
    """
    def __init__(self):
        self.key_vault = "https://sae-keys.vault.azure.net/"
        self.credential = DefaultAzureCredential(
            exclude_environment_credential=True,
            exclude_shared_token_cache_credential=True)
        self.client = SecretClient(self.key_vault, self.credential)

    def get_secret(self, secret_name: str) -> str:
        """
        Gets a secret from Azure Keyvault
        Args:
            secret_name: The name of the secret in the keyvault

        Returns:
            The value of the secret

        """
        return self.client.get_secret(secret_name).value

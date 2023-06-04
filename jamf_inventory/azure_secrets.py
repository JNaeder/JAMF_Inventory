from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential


class AzureSecrets:
    def __init__(self):
        self.key_vault = "https://sae-keys.vault.azure.net/"
        self.credential = DefaultAzureCredential(
            exclude_environment_credential=True,
            exclude_shared_token_cache_credential=True)
        self.client = SecretClient(self.key_vault, self.credential)

    def get_secret(self, secret_name: str) -> str:
        return self.client.get_secret(secret_name).value

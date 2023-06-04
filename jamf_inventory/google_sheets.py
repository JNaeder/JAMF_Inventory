"""
Module Name: google_sheets.py
Description: A class for writing to Google Sheets
Author: John Naeder
Created: 2021-06-01
"""

import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build

from azure_secrets import AzureSecrets

az = AzureSecrets()


class GoogleSheets:
    """
    Uses a service account to write data to worksheets in a Google Spreadsheet.
    Requires a google_credentials.json file to work.
    """

    def __init__(self):
        self.sheet_id = az.get_secret("GOOGLE-SHEET-URL")
        self.scopes = ['https://www.googleapis.com/auth/spreadsheets']
        self.user_info = {
            "client_email": az.get_secret("GOOGLE-CLIENT-EMAIL"),
            "token_uri": az.get_secret("GOOGLE-TOKEN-URI"),
            "private_key": az.get_secret("GOOGLE-PRIVATE-KEY")
        }
        self.creds = service_account.Credentials.from_service_account_info(
            self.user_info)
        # self.creds = service_account.Credentials.from_service_account_file(
        #     "../google_credentials.json", scopes=self.scopes)
        self.service = build('sheets', 'v4', credentials=self.creds)
        self.value_input_option = "USER_ENTERED"
        self.insert_data_option = "OVERWRITE"

    def clear_worksheet(self, sheet_name):
        request = self.service.spreadsheets().values().clear(
            spreadsheetId=self.sheet_id, range=sheet_name, body={})
        request.execute()

    @staticmethod
    def parse_dataframe(dataframe: pd.DataFrame):
        values = dataframe.values.tolist()
        header = dataframe.columns.tolist()
        output = [header, *values]
        return output

    def write_data_to_sheet(self, worksheet_name: str, data: list) -> None:
        self.clear_worksheet(worksheet_name)
        the_range = f"{worksheet_name}!A1:A"
        new_data = pd.DataFrame(data).astype(str)
        the_values = self.parse_dataframe(new_data)
        body = {
            "range": the_range,
            "values": the_values
        }
        request = self.service.spreadsheets().values().append(
            spreadsheetId=self.sheet_id, range=the_range,
            valueInputOption=self.value_input_option,
            insertDataOption=self.insert_data_option, body=body)
        request.execute()

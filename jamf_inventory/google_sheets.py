"""
Module Name: google_sheets.py
Description: A class for writing to Google Sheets
Author: John Naeder
Created: 2021-06-02
"""
import os
from dotenv import load_dotenv
import pandas as pd
# TODO: Think about not using gspread
import gspread as gs
from gspread_dataframe import set_with_dataframe

load_dotenv()


class GoogleSheets:
    def __init__(self):
        self.service_account = gs.service_account("../google_credentials.json")
        self.sheet_url = os.environ.get("GOOGLE_SHEET_URL")
        self.spreadsheet = self.service_account.open_by_key(self.sheet_url)

    def set_spreadsheet(self, sheet_url: str) -> None:
        self.service_account.open_by_key(sheet_url)

    def write_to_google_sheets(self, groups) -> None:
        """
        Writes each group container data to a Google Sheet via a DataFrame
        :return: None
        """
        print("\nWriting to Google Sheets")
        for items in groups.values():
            ws_id = items["ws_id"]
            container = items["container"]
            # TODO: This should get the worksheet by name, not ID
            ss = self.spreadsheet.get_worksheet_by_id(ws_id)
            ss.clear()
            set_with_dataframe(ss, pd.DataFrame(container))
        print("Done!")

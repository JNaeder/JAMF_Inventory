"""
Module Name: google_sheets.py
Description: A class for writing to Google Sheets
Author: John Naeder
Created: 2021-06-01
"""
import os

from dotenv import load_dotenv
import pandas as pd
import gspread as gs
from gspread_dataframe import set_with_dataframe

load_dotenv()


class GoogleSheets:
    """
    Uses a service account to write data to worksheets in a Google Spreadsheet.
    Requires a google_credentials.json file to work.
    """
    def __init__(self):
        self.service_account = gs.service_account("../google_credentials.json")
        self.sheet_url = os.environ.get("GOOGLE_SHEET_URL")
        self.spreadsheet = self.service_account.open_by_key(self.sheet_url)

    def write_data_to_google_sheet(self, sheet_name: str, data: list) -> None:
        """
        Takes a sheet name finds that worksheet, and then converts the 
        container data into a DataFrame and writes it to that sheet.
        
        Args:
            sheet_name: Name of the worksheet to write to.
            data: The data to write to worksheet
        """
        worksheet = self.spreadsheet.worksheet(sheet_name)
        worksheet.clear()
        set_with_dataframe(worksheet, pd.DataFrame(data))

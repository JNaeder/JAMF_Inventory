"""
Module Name: main
Description: This module contains the class that calls the JAMF API,
pareses the information, separates them into groups,
and writes that information to Google sheets.
Author: John Naeder
Created: 2023-06-01
"""

import os
from typing import Dict, List
import requests
from dotenv import load_dotenv
import pandas as pd
import gspread as gs
from gspread_dataframe import set_with_dataframe
from computer import Computer

load_dotenv()


class JamfAPI:
    """
    Main JAMF API class
    """

    def __init__(self):
        self.base_url = "https://saena.jamfcloud.com/"
        self.username = os.environ.get("JAMF_USERNAME")
        self.password = os.environ.get("JAMF_PASSWORD")
        self.sheet_url = os.environ.get("GOOGLE_SHEET_URL")
        self.session = requests.session()
        self.auth_token = self.get_auth_token()
        self.session.headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
        self.service_account = gs.service_account("./google_credentials.json")
        self.spreadsheet = self.service_account.open_by_key(self.sheet_url)
        self.amount = 1000
        self.size = 5
        self.current_page = 0

        self.groups = {
            "All Computers": {"ws_id": 0, "container": []},
            "NY Student": {"ws_id": 2007300303, "container": []},
            "MIA Student": {"ws_id": 108807186, "container": []},
            "NAS Student": {"ws_id": 1784935395, "container": []},
            "ATL Student": {"ws_id": 43197857, "container": []},
            "CHI Student": {"ws_id": 1825908811, "container": []},
            "General Staff": {"ws_id": 160467683, "container": []},
            "No Group": {"ws_id": 1822520265, "container": []},
        }

    def get_auth_token(self):
        url = self.base_url + "api/v1/auth/token"
        response = self.session.post(url, auth=(self.username, self.password))
        return response.json()["token"]

    def api_request(self) -> List[Dict]:
        """
        Get the data from the JAMF API, and return the results
        :param: None
        :return: Dictionary of the http response Dataa
        """
        print(".", end=("" if self.current_page % 40 != 0 else "\n"))
        url = self.base_url + ("/api/v1/computers-inventory"
                               "?section=GENERAL"
                               "&section=APPLICATIONS"
                               "&section=GROUP_MEMBERSHIPS"
                               "&section=HARDWARE"
                               "&section=OPERATING_SYSTEM"
                               "&section=STORAGE"
                               f"&page={self.current_page}"
                               f"&page-size={self.size}"
                               "&sort=general.name%3Aasc")
        response = self.session.get(url)
        if response.status_code != 200:
            print(f"Response code was {response.status_code}")
            return None
        self.amount = response.json()["totalCount"]
        data = response.json()["results"]
        return data

    def write_to_google_sheets(self):
        print("\nWriting to Google Sheets")
        for items in self.groups.values():
            ws_id = items["ws_id"]
            container = items["container"]
            ss = self.spreadsheet.get_worksheet_by_id(ws_id)
            ss.clear()
            set_with_dataframe(ss, pd.DataFrame(container))
        print("Done!")

    def get_computer_info(self):
        while (self.current_page * self.size) < self.amount:
            data = self.api_request()
            if data is None:
                self.current_page += 1
                continue
            for machine in data:
                computer = Computer(machine=machine)
                computer.write_to_group(self.groups)
            self.current_page += 1
        self.write_to_google_sheets()


if __name__ == "__main__":
    jamf = JamfAPI()
    jamf.get_computer_info()

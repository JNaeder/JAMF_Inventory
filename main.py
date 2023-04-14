import requests
from dotenv import load_dotenv
import os
import pandas as pd
import gspread as gs
from gspread_dataframe import set_with_dataframe
from datetime import datetime

load_dotenv()


class jamfAPI:
    def __init__(self):
        self.baseURL = "https://saena.jamfcloud.com/"
        self.username = os.environ.get("USERNAME")
        self.password = os.environ.get("PASSWORD")
        self.sheet_url = os.environ.get("SHEET_URL")
        self.worksheet_id = os.environ.get("WORKSHEET_ID")
        self.session = requests.session()
        self.auth_token = self.get_auth_token()
        self.session.headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
        self.data_frame = pd.DataFrame()
        self.service_account = gs.service_account("./google_credentials.json")
        self.spreadsheet = self.service_account.open_by_key(self.sheet_url)
        self.worksheet = self.spreadsheet.get_worksheet_by_id(1258656501)
        self.app_names = ["Pro Tools.app", "Ableton Live 11 Standard.app", "Logic Pro X.app"]

    def get_auth_token(self):
        url = self.baseURL + "api/v1/auth/token"
        response = self.session.post(url, auth=(self.username, self.password))
        return response.json()["token"]

    def get_computer_info(self):
        page = 0
        size = 50
        amount = 1000
        all_computers = []

        while (page * size) < amount:
            print(f"---Get page {page}---")
            url = self.baseURL + f"/api/v1/computers-inventory?section=GENERAL&section=APPLICATIONS&section=GROUP_MEMBERSHIPS&section=HARDWARE&section=OPERATING_SYSTEM&&section=STORAGE&page={page}&page-size={size}&sort=id%3Aasc"
            response = self.session.get(url)
            if response.status_code != 200:
                print(f"Response code was {response.status_code}")
                page += 1
                continue
            amount = response.json()["totalCount"]
            data = response.json()["results"]
            print(f"returned {len(data)} items")
            for computer in data:
                new_data = {}
                general_info = computer["general"]
                applications = computer["applications"]
                hardware = computer["hardware"]
                os = computer["operatingSystem"]
                groups = computer["groupMemberships"]

                new_data["Name"] = general_info["name"]
                new_data["OS"] = os["version"]
                new_data["Last_Contact"] = datetime.fromisoformat(general_info["lastContactTime"]).strftime("%m/%d/%Y")
                new_data["Model"] = hardware["modelIdentifier"]
                new_data["Serial"] = hardware["serialNumber"]
                new_data["CPU"] = hardware["processorType"]
                new_data["RAM"] = hardware["totalRamMegabytes"] // 1000

                storage = computer["storage"]["disks"]
                if storage:
                    drive = storage[0]["partitions"]
                    if drive:
                        new_data["HD Size"] = drive[0]["sizeMegabytes"] // 1000
                        new_data["HD_Free"] = drive[0]["availableMegabytes"] // 1000

                for app in applications:
                    if app["name"] in self.app_names:
                        new_data[app["name"]] = app["version"]
                all_computers.append(new_data)
            page += 1

        self.data_frame = pd.DataFrame(all_computers)
        set_with_dataframe(self.worksheet, self.data_frame)


if __name__ == "__main__":
    jamf = jamfAPI()
    jamf.get_computer_info()

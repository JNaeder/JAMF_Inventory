import requests
from dotenv import load_dotenv
import os
import pandas as pd
import gspread as gs
from gspread_dataframe import set_with_dataframe
from datetime import datetime, timezone

load_dotenv()


class jamfAPI:
    def __init__(self):
        self.baseURL = "https://saena.jamfcloud.com/"
        self.username = os.environ.get("JAMF_USERNAME")
        self.password = os.environ.get("JAMF_PASSWORD")
        self.sheet_url = os.environ.get("GOOGLE_SHEET_URL")
        self.session = requests.session()
        self.auth_token = self.get_auth_token()
        self.session.headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
        self.data_frame = pd.DataFrame()
        self.service_account = gs.service_account("./google_credentials.json")
        self.spreadsheet = self.service_account.open_by_key(self.sheet_url)
        self.all_computers = self.spreadsheet.get_worksheet_by_id(0)
        self.ny_students = self.spreadsheet.get_worksheet_by_id(1745485465)
        self.atl_students = self.spreadsheet.get_worksheet_by_id(2037246095)
        self.nas_students = self.spreadsheet.get_worksheet_by_id(60083025)
        self.mia_students = self.spreadsheet.get_worksheet_by_id(1777779477)
        self.chi_students = self.spreadsheet.get_worksheet_by_id(679638181)
        self.general_staff = self.spreadsheet.get_worksheet_by_id(1531308029)
        self.no_group = self.spreadsheet.get_worksheet_by_id(904518589)
        self.app_names = ["Pro Tools.app", "Ableton Live 11 Standard.app", "Logic Pro X.app", "8x8 Work.app",
                          "Slack.app", "FortiClient.app", "TeamViewer.app",
                          "Zoom.us.app", "UAD Meter & Control Panel.app", "Google Chrome.app"]
        self.group_names = ["NY Student", "MIA Student", "NAS Student", "ATL Student", "CHI Student", "General Staff"]

    def get_auth_token(self):
        url = self.baseURL + "api/v1/auth/token"
        response = self.session.post(url, auth=(self.username, self.password))
        return response.json()["token"]

    def get_computer_info(self):
        page = 0
        size = 5
        amount = 1000
        all_computers = []
        no_group = []
        ny_students = []
        mia_students = []
        nas_students = []
        atl_students = []
        chi_students = []
        general_staff = []

        the_groups = {
            "NY Student": ny_students,
            "MIA Student": mia_students,
            "NAS Student": nas_students,
            "ATL Student": atl_students,
            "CHI Student": chi_students,
            "General Staff": general_staff,
        }

        while (page * size) < amount:
            print(f"---Get page {page}---")
            url = self.baseURL + f"/api/v1/computers-inventory?section=GENERAL&section=APPLICATIONS&section=GROUP_MEMBERSHIPS&section=HARDWARE&section=OPERATING_SYSTEM&section=STORAGE&page={page}&page-size={size}&sort=general.name%3Aasc"
            response = self.session.get(url)
            if response.status_code != 200:
                print(f"Response code was {response.status_code}")
                page += 1
                continue
            amount = response.json()["totalCount"]
            data = response.json()["results"]
            print(f"returned {len(data)} items")
            for computer in data:
                has_group = False
                new_data = {}
                general_info = computer["general"]
                applications = computer["applications"]
                applications.sort(key=lambda x: x["name"])
                hardware = computer["hardware"]
                operatingSystem = computer["operatingSystem"]
                groups = computer["groupMemberships"]
                # application_names = [app["name"] for app in applications]

                new_data["Name"] = general_info["name"]
                new_data["Specs"] = ""
                new_data["Serial"] = hardware["serialNumber"]
                last_contact = datetime.fromisoformat(general_info["lastContactTime"])
                days_since_contact = (datetime.now(timezone.utc) - last_contact).days
                new_data["Last Contact"] = last_contact.strftime("%m/%d/%Y")
                new_data["Days Since Contact"] = days_since_contact
                new_data["OS"] = operatingSystem["version"]
                new_data["Model"] = hardware["modelIdentifier"]
                new_data["CPU"] = hardware["processorType"]
                new_data["RAM"] = hardware["totalRamMegabytes"] // 1000

                storage = computer["storage"]["disks"]
                total_space = 0
                available_space = 0
                if storage:
                    for drive in storage:
                        if drive["device"] == "disk0":
                            for partition in drive["partitions"]:
                                total_space += partition["sizeMegabytes"] // 1000
                                available_space += partition["availableMegabytes"] // 1000
                    new_data["Total Space"] = total_space
                    new_data["Available Space"] = available_space

                new_data["Apps"] = ""
                for app in applications:
                    if app["name"] in self.app_names:
                        app_name = app["name"].replace(".app", "")
                        new_data[app_name] = app["version"].split(" ")[0]

                for group in groups:
                    if group["groupName"] in self.group_names:
                        the_groups[group["groupName"]].append(new_data)
                        has_group = True

                if not has_group:
                    no_group.append(new_data)
                all_computers.append(new_data)
            page += 1

        print("Setting Dataframes")
        set_with_dataframe(self.all_computers, pd.DataFrame(all_computers))
        set_with_dataframe(self.ny_students, pd.DataFrame(ny_students))
        set_with_dataframe(self.atl_students, pd.DataFrame(atl_students))
        set_with_dataframe(self.mia_students, pd.DataFrame(mia_students))
        set_with_dataframe(self.nas_students, pd.DataFrame(nas_students))
        set_with_dataframe(self.chi_students, pd.DataFrame(chi_students))
        set_with_dataframe(self.general_staff, pd.DataFrame(general_staff))
        set_with_dataframe(self.no_group, pd.DataFrame(no_group))


if __name__ == "__main__":
    jamf = jamfAPI()
    jamf.get_computer_info()

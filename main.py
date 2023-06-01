"""
JAMF-INVENTORY
Author: John Naeder

"""

import requests
from dotenv import load_dotenv
import os
import pandas as pd
import gspread as gs
from gspread_dataframe import set_with_dataframe
from datetime import datetime, timezone
from typing import Dict

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
        self.data_frame = pd.DataFrame()
        self.service_account = gs.service_account("./google_credentials.json")
        self.spreadsheet = self.service_account.open_by_key(self.sheet_url)
        self.amount = 1000
        self.size = 5
        self.current_page = 0

        self.groups = {
            "All Computers": {"ws_id": 0, "container": []},
            "NY Student": {"ws_id": 1745485465, "container": []},
            "MIA Student": {"ws_id": 1777779477, "container": []},
            "NAS Student": {"ws_id": 60083025, "container": []},
            "ATL Student": {"ws_id": 2037246095, "container": []},
            "CHI Student": {"ws_id": 679638181, "container": []},
            "General Staff": {"ws_id": 1531308029, "container": []},
            "No Group": {"ws_id": 904518589, "container": []},
        }
        self.app_names = ["Pro Tools.app", "Ableton Live 10 Standard.app",
                          "Ableton Live 11 Standard.app",
                          "Logic Pro X.app", "8x8 Work.app",
                          "Slack.app", "FortiClient.app", "TeamViewer.app",
                          "Zoom.us.app", "UAD Meter & Control Panel.app",
                          "Google Chrome.app", "Install macOS Monterey.app"]

    def get_auth_token(self):
        url = self.base_url + "api/v1/auth/token"
        response = self.session.post(url, auth=(self.username, self.password))
        return response.json()["token"]

    def api_request(self) -> Dict:
        """
        Get the data from the JAMF API
        :return: Dictionary of the http response Dataa
        """
        print(".", end=("" if self.current_page % 40 != 0 else "\n"))
        url = self.base_url + f"/api/v1/computers-inventory" \
                              f"?section=GENERAL" \
                              f"&section=APPLICATIONS" \
                              f"&section=GROUP_MEMBERSHIPS" \
                              f"&section=HARDWARE" \
                              f"&section=OPERATING_SYSTEM" \
                              f"&section=STORAGE" \
                              f"&page={self.current_page}" \
                              f"&page-size={self.size}" \
                              f"&sort=general.name%3Aasc"
        response = self.session.get(url)
        if response.status_code != 200:
            print(f"Response code was {response.status_code}")
            return None
        self.amount = response.json()["totalCount"]
        return response.json()["results"]

    def get_computer_info(self):

        while (self.current_page * self.size) < self.amount:
            data = self.api_request()

            if data is None:
                self.current_page += 1
                continue

            for computer in data:
                # TODO: Do something with this
                has_group = False
                new_data = {}
                general_info = computer["general"]
                applications = computer["applications"]
                applications.sort(key=lambda x: x["name"])
                hardware = computer["hardware"]
                operating_system = computer["operatingSystem"]
                groups = computer["groupMemberships"]

                # TODO: Make this a function
                new_data["Name"] = general_info["name"]
                new_data["Specs"] = ""
                new_data["Serial"] = hardware["serialNumber"]
                new_data["Last IP"] = general_info["lastReportedIp"]
                jamf_binary = general_info["jamfBinaryVersion"]
                new_data["JAMF Binary"] = jamf_binary.split("-")[0] if jamf_binary else ""
                last_contact_time = general_info["lastContactTime"]
                last_contact = datetime.fromisoformat(last_contact_time) if last_contact_time else None
                days_since_contact = (datetime.now(timezone.utc) - last_contact).days if last_contact_time else 0
                new_data["Last Contact"] = last_contact.strftime("%m/%d/%Y") if last_contact_time else None
                new_data["Days Since Contact"] = days_since_contact
                new_data["OS"] = operating_system["version"]
                new_data["Model"] = hardware["modelIdentifier"]
                new_data["CPU"] = hardware["processorType"]
                new_data["RAM"] = hardware["totalRamMegabytes"] // 1000

                # TODO: Make this another function
                storage = computer["storage"]["disks"]
                total_space = 0
                available_space = 0
                if storage:
                    for drive in storage:
                        if drive["device"] == "disk0":
                            for partition in drive["partitions"]:
                                if partition["partitionType"] == "BOOT":
                                    total_space += partition["sizeMegabytes"] // 1000
                                    available_space += partition["availableMegabytes"] // 1000
                    new_data["Total Space"] = total_space
                    new_data["Available Space"] = available_space

                # TODO: Make this a function
                new_data["Apps"] = ""
                for app in applications:
                    if app["name"] in self.app_names:
                        app_name = app["name"].replace(".app", "")
                        new_data[app_name] = app["version"].split(" ")[0]

                # TODO: This too a function
                for group in groups:
                    if group["groupName"] in self.groups:
                        group_name = group["groupName"]
                        group_container = self.groups[group_name]["container"]
                        group_container.append(new_data)
                        has_group = True

                if not has_group:
                    self.groups["No Group"]["container"].append(new_data)
                self.groups["All Computers"]["container"].append(new_data)
            self.current_page += 1

        print("\nWriting to Google Sheets")
        for group_name, items in self.groups.items():
            ws_id = items["ws_id"]
            container = items["container"]
            ss = self.spreadsheet.get_worksheet_by_id(ws_id)
            ss.clear()
            set_with_dataframe(ss, pd.DataFrame(container))
        print("Done!")


if __name__ == "__main__":
    jamf = JamfAPI()
    jamf.get_computer_info()

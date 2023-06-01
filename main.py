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
from typing import Dict, List
from app_names import app_names

load_dotenv()


class Computer:
    def __init__(self, machine):
        self.machine: Dict = machine
        self.has_group: bool = False,
        self.new_data: Dict[str, str] = {}
        self.general_info = self.machine["general"]
        self.applications = self.machine["applications"]
        self.applications.sort(key=lambda x: x["name"])
        self.hardware = self.machine["hardware"]
        self.operating_system = self.machine["operatingSystem"]
        self.groups = self.machine["groupMemberships"]
        self.write_new_data()
        self.get_apps()

    def get_contact_time(self):
        last_contact_time = self.general_info["lastContactTime"]
        last_contact = datetime.fromisoformat(
            last_contact_time) if last_contact_time else None
        days_since_contact = (datetime.now(
            timezone.utc) - last_contact).days if last_contact_time \
            else 0
        return last_contact_time, last_contact, days_since_contact

    def get_hd_data(self) -> (int, int):
        """
        Parses through the disk info to return relevant disk space.
        :return: Tuple containing the total space and available space.
        """
        storage = self.machine["storage"]["disks"]
        total_space = 0
        available_space = 0
        if storage:
            for drive in storage:
                if drive["device"] == "disk0":
                    for partition in drive["partitions"]:
                        if partition["partitionType"] == "BOOT":
                            total_space += partition[
                                               "sizeMegabytes"] // 1000
                            available_space += partition[
                                                   "availableMegabytes"] // 1000
        return total_space, available_space

    def get_apps(self):
        self.new_data["Apps"] = ""
        for app in self.applications:
            if app["name"] in app_names:
                app_name = app["name"].replace(".app", "")
                self.new_data[app_name] = app["version"].split(" ")[0]

    def write_new_data(self):
        last_contact_time, \
            last_contact, \
            days_since_contact = self.get_contact_time()
        total_space, available_space = self.get_hd_data()

        self.new_data["Name"] = self.general_info["name"]
        self.new_data["Serial"] = self.hardware["serialNumber"]
        self.new_data["Days Since Contact"] = days_since_contact
        self.new_data["Specs"] = ""
        self.new_data["Last IP"] = self.general_info["lastReportedIp"]
        jamf_binary = self.general_info["jamfBinaryVersion"]
        self.new_data["JAMF Binary"] = jamf_binary.split("-")[
            0] if jamf_binary else ""
        self.new_data["Last Contact"] = last_contact.strftime(
            "%m/%d/%Y") if last_contact_time else None
        self.new_data["OS"] = self.operating_system["version"]
        self.new_data["Model"] = self.hardware["modelIdentifier"]
        self.new_data["CPU"] = self.hardware["processorType"]
        self.new_data["RAM"] = self.hardware["totalRamMegabytes"] // 1000
        self.new_data["Total Space"] = total_space
        self.new_data["Available Space"] = available_space

    def write_to_group(self, jamf_groups):
        for group in self.groups:
            if group["groupName"] in jamf_groups:
                group_name = group["groupName"]
                group_container = jamf_groups[group_name]["container"]
                group_container.append(self.new_data)
                self.has_group = True

        if not self.has_group:
            jamf_groups["No Group"]["container"].append(self.new_data)

        jamf_groups["All Computers"]["container"].append(self.new_data)


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

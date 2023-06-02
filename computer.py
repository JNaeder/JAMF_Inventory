"""
Module Name: computer.py
Description: A class for a computer. It is responsible for taking the raw
information from JAMF and parsing it into usable information for Google Sheets
Author: John Naeder
Created: 2023-06-01
"""
from typing import Dict, Any
from datetime import datetime, timezone
from app_names import app_names


class Computer:
    """
    Class for a single computer
    Takes in machine information from JAMF
    and parses it down for The Google Sheet
    """

    def __init__(self, machine):
        self.machine: Dict[str, Any] = machine
        self.has_group: bool = False
        self.new_data: Dict[str, str] = {}
        self.general_info = self.machine["general"]
        self.applications = self.machine["applications"]
        self.applications.sort(key=lambda x: x["name"])
        self.hardware = self.machine["hardware"]
        self.operating_system = self.machine["operatingSystem"]
        self.groups = self.machine["groupMemberships"]
        self.write_new_data()
        self.get_apps()

    def get_contact_time(self) -> (datetime, int):
        """
        Returns a tuple of last contact date, and the amount of days since
        last contact.
        :return: (datetime,  int)
        """
        last_contact_time = self.general_info["lastContactTime"]
        last_contact = datetime.fromisoformat(last_contact_time)\
            if last_contact_time else None
        days_since_contact = (datetime.now(timezone.utc) - last_contact).days\
            if last_contact_time else 0
        return last_contact, days_since_contact

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
        last_contact, days_since_contact = self.get_contact_time()
        total_space, available_space = self.get_hd_data()

        self.new_data["Name"] = self.general_info["name"]
        self.new_data["Serial"] = self.hardware["serialNumber"]
        self.new_data["Days Since Contact"] = days_since_contact
        self.new_data["Specs"] = ""
        self.new_data["Last IP"] = self.general_info["lastReportedIp"]
        jamf_binary = self.general_info["jamfBinaryVersion"]
        self.new_data["JAMF Binary"] = jamf_binary.split("-")[0]\
            if jamf_binary else ""
        self.new_data["Last Contact"] = last_contact.strftime("%m/%d/%Y")\
            if last_contact else None
        self.new_data["OS"] = self.operating_system["version"]
        self.new_data["Model"] = self.hardware["modelIdentifier"]
        self.new_data["CPU"] = self.hardware["processorType"]
        self.new_data["RAM"] = self.hardware["totalRamMegabytes"] // 1000
        self.new_data["Total Space"] = total_space
        self.new_data["Available Space"] = available_space

    # fixme: This should be in the JAMF API Class
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

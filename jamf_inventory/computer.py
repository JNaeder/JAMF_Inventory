"""
Module Name: computer.py
Description: A class for a computer. It is responsible for taking the raw
information from JAMF and parsing it into usable information for Google Sheets
Author: John Naeder
Created: 2023-06-01
"""
from typing import Dict, List, Any
from datetime import datetime, timezone

from app_names import app_names

ComputerData = Dict[str, Any]


class Computer:
    """
    Class for a single computer
    Takes in machine information from JAMF
    and parses it down for The Google Sheet
    """

    def __init__(self, machine: ComputerData):
        self.machine: Dict[str, Any] = machine
        self.has_group: bool = False
        self.parsed_data: Dict[str, str] = {}
        self.general_info: Dict[str, Any] = self.machine["general"]
        self.hardware: Dict[str, Any] = self.machine["hardware"]
        self.operating_system: Dict[str, Any] = self.machine["operatingSystem"]
        self.groups: List[Dict[str, Any]] = self.machine["groupMemberships"]
        self.write_new_data()
        self.get_apps()

    def get_parsed_data(self):
        """Returns the parsed data of the computer"""
        return self.parsed_data

    def get_has_group(self) -> bool:
        """Returns the status of the computer being in a group"""
        return self.has_group

    def set_has_group(self, status: bool) -> None:
        """Sets the has group status"""
        self.has_group = status

    def get_contact_time(self) -> (datetime, int):
        """
        Calculates the last contact date, and the amount of days since last
        contact.

        Returns:
            Tuple of the last contact time, and the amount of days.

        """
        last_contact_time = self.general_info["lastContactTime"]
        last_contact = datetime.fromisoformat(last_contact_time) \
            if last_contact_time else None
        days_since_contact = (datetime.now(timezone.utc) - last_contact).days \
            if last_contact_time else 0
        return last_contact, days_since_contact

    def get_hd_data(self) -> (int, int):
        """
        Parses through the computers data to get the amount of hard drive
        space on the machine.

        Returns:
            Tuple of total space and available space on the machine

        """
        storage = self.machine["storage"]["disks"]
        total_space = 0
        available_space = 0
        partitions = []

        if storage:
            for drive in storage:
                if drive["device"] == "disk0":
                    partitions = drive["partitions"]

            for partition in partitions:
                if partition["partitionType"] == "BOOT":
                    size_mb = partition["sizeMegabytes"]
                    available_mb = partition["availableMegabytes"]
                    total_space += size_mb // 1000
                    available_space += available_mb // 1000

        return total_space, available_space

    def get_apps(self) -> None:
        """
        Goes through the list of apps form app_names, and writes the version
        to the parsed data.

        Returns: None

        """
        applications = self.machine["applications"]
        applications.sort(key=lambda x: x["name"])

        self.parsed_data["Apps"] = ""
        for app in applications:
            if app["name"] in app_names:
                app_name = app["name"].replace(".app", "")
                self.parsed_data[app_name] = app["version"].split(" ")[0]

    def write_new_data(self) -> None:
        """
        Responsible for doing the heavy lifting as far as parsing data goes.

        Returns: None

        """
        last_contact, days_since_contact = self.get_contact_time()
        total_space, available_space = self.get_hd_data()

        self.parsed_data["Name"] = self.general_info["name"]
        self.parsed_data["Serial"] = self.hardware["serialNumber"]
        self.parsed_data["Days Since Contact"] = days_since_contact
        self.parsed_data["Specs"] = ""
        self.parsed_data["Last IP"] = self.general_info["lastReportedIp"]
        jamf_binary = self.general_info["jamfBinaryVersion"]
        self.parsed_data["JAMF Binary"] = jamf_binary.split("-")[0] \
            if jamf_binary else ""
        self.parsed_data["Last Contact"] = last_contact.strftime("%m/%d/%Y") \
            if last_contact else None
        self.parsed_data["OS"] = self.operating_system["version"]
        self.parsed_data["Model"] = self.hardware["modelIdentifier"]
        self.parsed_data["CPU"] = self.hardware["processorType"]
        self.parsed_data["RAM"] = self.hardware["totalRamMegabytes"] // 1000
        self.parsed_data["Total Space"] = total_space
        self.parsed_data["Available Space"] = available_space

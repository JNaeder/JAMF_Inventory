"""
Module Name: jamf_inventory.py

This module is responsible for main logic.
Imports JamfAPI, GoogleSheets and Computer classes.

Author: John Naeder
Created: 2021-06-01
"""

from jamf_api import JamfAPI
from google_sheets import GoogleSheets
from computer import Computer


class JamfInventory:
    """
    Main Jamf Inventory Class

    Used to run the main logic of this project. Imports other modules and
    runs them together to get all computer data from JAMF, parse it and
    export it to Google Sheets.
    """
    def __init__(self):
        self.page_size = 5
        self.groups = {
            "All Computers": [],
            "NY Student": [],
            "MIA Student": [],
            "NAS Student": [],
            "ATL Student": [],
            "CHI Student": [],
            "General Staff": [],
            "No Group": [],
        }

    def get_computer_data(self) -> None:
        """
        Calls the JAMF API and continuously calls the api_request
        method until all computer data has been written to groups.

        Returns: None
        """
        jamf_api = JamfAPI()
        total_count = 1000
        current_page = 0

        while (current_page * self.page_size) < total_count:
            print(".", end="" if current_page % 40 != 0 else "\n")
            data, count = jamf_api.api_request(current_page, self.page_size)
            current_page += 1

            if count:
                total_count = count
            if data is None:
                continue

            for machine in data:
                computer = Computer(machine=machine)
                self.write_to_groups(computer)

    def write_to_groups(self, computer: Computer) -> None:
        """
        Takes in a computer as input and writes the parsed out data to the
        appropriate groups.

        Args:
            computer: The Computer class whose data should be copied

        Returns: None

        """
        data = computer.get_parsed_data()

        for group in computer.groups:
            if group["groupName"] in self.groups:
                group_name = group["groupName"]
                group_container = self.groups[group_name]
                group_container.append(data)
                computer.set_has_group(True)

        if not computer.get_has_group():
            self.groups["No Group"].append(data)

        self.groups["All Computers"].append(data)

    def write_all_data_to_sheets(self) -> None:
        """
        Responsible for taking all the data from the groups,
        and writing them to the appropriate Google Sheet

        Returns: None

        """
        print("\nWriting to Google Sheets")
        for sheet_name, container in self.groups.items():
            google_sheets = GoogleSheets()
            google_sheets.write_data_to_google_sheet(sheet_name, container)

    def run_program(self) -> None:
        """
        Main logic. Gets all the data, and then writes all the data.

        Returns: None

        """
        print("Starting")
        self.get_computer_data()
        self.write_all_data_to_sheets()
        print("Done")


if __name__ == "__main__":
    JamfInventory().run_program()

"""
Module Name: jamf_inventory.py
This module is responsible for making API calls to the JAMF service and
parsing the data into a data structure.
Author: John Naeder
Created: 2021-06-02
"""

from jamf_api import JamfAPI
from google_sheets import GoogleSheets


class JamfInventory:
    def __init__(self):
        # TODO: Make this dictionary not have sheet IDs. Just lists
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

    def run_program(self):
        print("Starting")
        jamf_api = JamfAPI()
        google_sheets = GoogleSheets()
        jamf_api.make_all_requests(self.groups)
        google_sheets.write_to_google_sheets(self.groups)


if __name__ == "__main__":
    JamfInventory().run_program()

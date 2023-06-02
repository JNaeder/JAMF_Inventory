"""
Module Name: jamf_api.py
Description: A class for making API calls to the JAMF API
Author: John Naeder
Created: 2021-06-02
"""

import os
from typing import Dict, List
import requests
from dotenv import load_dotenv
from computer import Computer

load_dotenv()


class JamfAPI:
    """
    Responsible for making API calls to the JAMF API service
    """

    def __init__(self):
        self.base_url = "https://saena.jamfcloud.com/"
        self.username = os.environ.get("JAMF_USERNAME")
        self.password = os.environ.get("JAMF_PASSWORD")
        self.session = requests.session()
        self.auth_token = self.get_auth_token()
        self.session.headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }

    def get_auth_token(self) -> str:
        """
        Uses username and password to get an authentication token from the
        JAMF API.
        :return:str Authentication token
        """
        url = self.base_url + "api/v1/auth/token"
        response = self.session.post(url, auth=(self.username, self.password))
        return response.json()["token"]

    def api_request(self, current_page: int, size: int) -> List[Dict]:
        """
        Get the data from the JAMF API, and return the results
        :param: None
        :return: Dictionary of the http response Dataa
        """
        url = self.base_url + ("/api/v1/computers-inventory"
                               "?section=GENERAL"
                               "&section=APPLICATIONS"
                               "&section=GROUP_MEMBERSHIPS"
                               "&section=HARDWARE"
                               "&section=OPERATING_SYSTEM"
                               "&section=STORAGE"
                               f"&page={current_page}"
                               f"&page-size={size}"
                               "&sort=general.name%3Aasc")
        response = self.session.get(url)
        if response.status_code != 200:
            print(f"Response code was {response.status_code}")
            return None
        # amount = response.json()["totalCount"]
        data = response.json()["results"]
        return data

    def make_all_requests(self,
                          groups: Dict[str, list],
                          page_size: int = 5) -> None:
        current_page = 0
        amount = 1000

        # TODO: Think about how to manage "amount"
        while (current_page * page_size) < amount:
            print(".", end="" if current_page % 40 != 0 else "\n")
            data = self.api_request(current_page, page_size)
            current_page += 1
            if data is None:
                continue
            for machine in data:
                computer = Computer(machine=machine)
                # TODO: This should be in another class
                computer.write_to_group(groups)

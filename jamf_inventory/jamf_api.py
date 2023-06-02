"""
Module Name: jamf_api.py
Description: A class for making API calls to the JAMF API
Author: John Naeder
Created: 2021-06-01
"""

import os
from typing import Dict, Any

from requests import session
from dotenv import load_dotenv

load_dotenv()

ComputerData = Dict[str, Any]


class JamfAPI:
    """
    Responsible for making API calls to the JAMF API service
    """

    def __init__(self):
        self.base_url = "https://saena.jamfcloud.com/"
        self.username = os.environ.get("JAMF_USERNAME")
        self.password = os.environ.get("JAMF_PASSWORD")
        self.session = session()
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

    def api_request(self, current_page: int, size: int) -> [ComputerData, int]:
        """
        Make an HTTP request to the JAMF API, and return the response.
        :param: None
        :return: HTTP Response is successful, otherwise None
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
            return [None, None]
        total_count = response.json()["totalCount"]
        data = response.json()["results"]
        return [data, total_count]

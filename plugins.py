import os
import pandas as pd
import gspread as gs
from gspread_dataframe import set_with_dataframe
from dotenv import load_dotenv


load_dotenv()

sheet_url = os.environ.get("GOOGLE_SHEET_URL")

# Windows
# log_files = "G:/Shared Drives/NY Tech Drive/computer_logs"
# macOS
log_files = "/Volumes/GoogleDrive/Shared drives/NY Tech Drive/computer_logs"

all_files = os.listdir(log_files)

service_account = gs.service_account("./google_credentials.json")
spreadsheet = service_account.open_by_key(sheet_url)
worksheet = spreadsheet.get_worksheet_by_id(383527880)

output = []

for file in all_files:
    new_data = {}
    with open(f"{log_files}/{file}", "r") as the_file:
        for line in the_file:
            [plugin_name, plugin_version] = line.split(",")
            new_data[plugin_name] = plugin_version.strip()
    output.append(new_data)

df = pd.DataFrame(output)
worksheet.clear()
set_with_dataframe(worksheet, df)


# Wrapper for Google Sheet API

import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import json
secret = {}
with open('credentials.json') as f:
    secret = json.load(f)

# If modifying these scopes, delete the file token.pickle.
SCOPES = ["https://www.googleapis.com/auth/drive",
          "https://www.googleapis.com/auth/drive.file",
          "https://www.googleapis.com/auth/spreadsheets"]
# The ID and range of a sample spreadsheet.
TEMPLATE_SPREADSHEET_ID = secret['sheet']['spreadsheet_id']
TEMPLATE_SHEET_ID = secret['sheet']['sheet_id']

class Sheet:
    def __init__(self):
        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        self.service = build('sheets', 'v4', credentials=creds)

    def createNewSheetFromTemplate(self, title: str):
        newSheet = {
            'properties': {
                'title': title
            }
        }
        newSheet = self.service.newSheet().create(
            body=newSheet,
            fields='spreadsheetId'
        ).execute()
        copy_sheet_to_another_spreadsheet_request_body = {
            'destination_spreadsheet_id': newSheet.get('spreadsheetId')
        }
        self.service.spreadsheets().sheets().copyTo(
            spreadsheetId=TEMPLATE_SPREADSHEET_ID, 
            sheetId=TEMPLATE_SHEET_ID, 
            body=copy_sheet_to_another_spreadsheet_request_body
        ).execute()
        return newSheet
    
    def writeValues(self, range):



